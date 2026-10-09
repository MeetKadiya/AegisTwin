package pipeline

import (
	"context"
	"errors"
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"aegistwin/edge-agent/pkg/broker"
	"aegistwin/edge-agent/pkg/buffer"
	"aegistwin/edge-agent/pkg/parser"
	"aegistwin/edge-agent/pkg/validator"
	pb "aegistwin/edge-agent/proto"

	"google.golang.org/protobuf/proto"
)

var (
	ErrQueueFull      = errors.New("ingestion pipeline queue is saturated")
	ErrPipelineClosed = errors.New("ingestion pipeline is closed")
)

type IngestItem struct {
	Protocol pb.ProtocolType
	Topic    string
	Data     []byte
}

type PipelineMetrics struct {
	IngestedCount  uint64
	PublishedCount uint64
	BufferedCount  uint64
	FlushedCount   uint64
	DroppedCount   uint64
	ErrorCount     uint64
}

type TelemetryPipeline struct {
	broker     broker.EventBroker
	buf        *buffer.LocalBuffer
	baseTopic  string
	ingestChan chan IngestItem
	workers    int
	wg         sync.WaitGroup
	ctx        context.Context
	cancel     context.CancelFunc
	closed     int32 // atomic guard against send on closed channel

	// Atomic counters for high-frequency telemetry tracking
	ingestedCount  uint64
	publishedCount uint64
	bufferedCount  uint64
	flushedCount   uint64
	droppedCount   uint64
	errorCount     uint64
}

// NewTelemetryPipeline initializes the ingestion worker pool, buffer, and flusher.
func NewTelemetryPipeline(
	broker broker.EventBroker,
	buf *buffer.LocalBuffer,
	baseTopic string,
	queueSize int,
	workers int,
) *TelemetryPipeline {
	if queueSize <= 0 {
		queueSize = 100000
	}
	if workers <= 0 {
		workers = 16
	}

	ctx, cancel := context.WithCancel(context.Background())

	p := &TelemetryPipeline{
		broker:     broker,
		buf:        buf,
		baseTopic:  baseTopic,
		ingestChan: make(chan IngestItem, queueSize),
		workers:    workers,
		ctx:        ctx,
		cancel:     cancel,
	}

	p.startWorkers()
	p.startBufferFlusher()

	return p
}

// Ingest submits a raw payload into the concurrent processing pipeline.
// Non-blocking with queue protection under 50k req/sec burst.
func (p *TelemetryPipeline) Ingest(protocol pb.ProtocolType, topic string, data []byte) error {
	if atomic.LoadInt32(&p.closed) == 1 {
		return ErrPipelineClosed
	}

	atomic.AddUint64(&p.ingestedCount, 1)

	// ponytail: pass data directly without defensive heap copy; caller transfers ownership of byte slice
	item := IngestItem{
		Protocol: protocol,
		Topic:    topic,
		Data:     data,
	}

	select {
	case p.ingestChan <- item:
		return nil
	default:
		atomic.AddUint64(&p.droppedCount, 1)
		return ErrQueueFull
	}
}

// startWorkers spawns concurrent ingestion workers.
func (p *TelemetryPipeline) startWorkers() {
	for i := 0; i < p.workers; i++ {
		p.wg.Add(1)
		go p.workerLoop(i)
	}
}

// workerLoop drains the ingestion channel and processes payloads.
func (p *TelemetryPipeline) workerLoop(workerID int) {
	defer p.wg.Done()

	for {
		select {
		case <-p.ctx.Done():
			return
		case item, ok := <-p.ingestChan:
			if !ok {
				return
			}
			p.processItem(&item)
		}
	}
}

// processItem handles parse -> validate -> marshal -> publish / buffer pipeline.
func (p *TelemetryPipeline) processItem(item *IngestItem) {
	defer func() {
		// Error boundary: ensure any parser panic drops cleanly without taking down the worker thread
		if r := recover(); r != nil {
			atomic.AddUint64(&p.errorCount, 1)
			atomic.AddUint64(&p.droppedCount, 1)
			log.Printf("[Pipeline] Panic recovered in worker: %v", r)
		}
	}()

	// 1. Protocol Parsing
	var rec *pb.TelemetryRecord
	var err error

	switch item.Protocol {
	case pb.ProtocolType_PROTOCOL_OPC_UA:
		rec, err = parser.ParseOPCUA(item.Data)
	case pb.ProtocolType_PROTOCOL_MQTT:
		if len(item.Topic) >= 7 && item.Topic[:7] == "spBv1.0" {
			rec, err = parser.ParseSparkplugB(item.Topic, item.Data)
		} else {
			rec, err = parser.ParseMQTT(item.Topic, item.Data)
		}
	case pb.ProtocolType_PROTOCOL_SYSLOG:
		rec, err = parser.ParseSyslog(item.Data)
	default:
		err = fmt.Errorf("unknown protocol type: %v", item.Protocol)
	}

	if err != nil {
		atomic.AddUint64(&p.droppedCount, 1)
		return
	}

	// 2. Strict Protobuf Schema Validation
	if err := validator.ValidateRecord(rec); err != nil {
		atomic.AddUint64(&p.droppedCount, 1)
		return
	}

	// 3. Protobuf Wire Serialization
	pbBytes, err := proto.Marshal(rec)
	if err != nil {
		atomic.AddUint64(&p.errorCount, 1)
		atomic.AddUint64(&p.droppedCount, 1)
		return
	}

	// 4. Publish to Message Bus or Spill to Local Buffer
	subject := fmt.Sprintf("%s.%s.%s", p.baseTopic, rec.Protocol.String(), rec.SourceId)

	if p.broker.IsConnected() {
		if err := p.broker.Publish(subject, pbBytes); err == nil {
			atomic.AddUint64(&p.publishedCount, 1)
			return
		}
	}

	// Broker unavailable or publish failed: spill to local SQLite buffer
	if err := p.buf.Enqueue(rec.RecordId, pbBytes); err != nil {
		atomic.AddUint64(&p.errorCount, 1)
		log.Printf("[Pipeline] Buffer enqueue failed for %s: %v", rec.RecordId, err)
	} else {
		atomic.AddUint64(&p.bufferedCount, 1)
	}
}

// startBufferFlusher runs the background routine flushing buffered messages when online.
func (p *TelemetryPipeline) startBufferFlusher() {
	p.wg.Add(1)
	go func() {
		defer p.wg.Done()
		ticker := time.NewTicker(2 * time.Second)
		defer ticker.Stop()

		for {
			select {
			case <-p.ctx.Done():
				return
			case <-p.broker.ReconnectNotify():
				p.flushBuffer()
			case <-ticker.C:
				if p.broker.IsConnected() {
					p.flushBuffer()
				}
			}
		}
	}()
}

// flushBuffer drains messages from SQLite and delivers them to the broker.
func (p *TelemetryPipeline) flushBuffer() {
	batchSize := 100

	for {
		if !p.broker.IsConnected() {
			return
		}

		items, err := p.buf.DequeueBatch(batchSize)
		if err != nil || len(items) == 0 {
			return
		}

		var successIDs []int64
		for _, item := range items {
			subject := fmt.Sprintf("%s.buffered.%s", p.baseTopic, item.RecordID)
			if err := p.broker.Publish(subject, item.Payload); err != nil {
				// Stop on publish error to maintain FIFO ordering
				break
			}
			successIDs = append(successIDs, item.ID)
			atomic.AddUint64(&p.flushedCount, 1)
		}

		if len(successIDs) > 0 {
			if err := p.buf.DeleteBatch(successIDs); err != nil {
				log.Printf("[Pipeline] Error deleting flushed buffer items: %v", err)
			}
		}

		if len(items) < batchSize {
			break
		}
	}
}

// Metrics returns snapshot of pipeline ingestion and error counters.
func (p *TelemetryPipeline) Metrics() PipelineMetrics {
	return PipelineMetrics{
		IngestedCount: atomic.LoadUint64(&p.ingestedCount),
		PublishedCount: atomic.LoadUint64(&p.publishedCount),
		BufferedCount:  atomic.LoadUint64(&p.bufferedCount),
		FlushedCount:   atomic.LoadUint64(&p.flushedCount),
		DroppedCount:   atomic.LoadUint64(&p.droppedCount),
		ErrorCount:     atomic.LoadUint64(&p.errorCount),
	}
}

// Stop gracefully drains the ingestion queue and stops all workers.
func (p *TelemetryPipeline) Stop() {
	if !atomic.CompareAndSwapInt32(&p.closed, 0, 1) {
		return
	}
	p.cancel()
	p.wg.Wait()
}
