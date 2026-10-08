package main

import (
	"fmt"
	"math"
	"os"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"aegistwin/edge-agent/pkg/buffer"
	"aegistwin/edge-agent/pkg/parser"
	"aegistwin/edge-agent/pkg/pipeline"
	"aegistwin/edge-agent/pkg/validator"
	pb "aegistwin/edge-agent/proto"
)

// MockBroker provides a thread-safe in-memory broker for tests.
type MockBroker struct {
	mu            sync.Mutex
	connected     int32
	messages      [][]byte
	reconnectChan chan struct{}
}

func NewMockBroker() *MockBroker {
	return &MockBroker{
		connected:     1,
		messages:      make([][]byte, 0),
		reconnectChan: make(chan struct{}, 1),
	}
}

func (m *MockBroker) Publish(subject string, data []byte) error {
	if atomic.LoadInt32(&m.connected) == 0 {
		return fmt.Errorf("mock broker disconnected")
	}
	m.mu.Lock()
	defer m.mu.Unlock()
	m.messages = append(m.messages, data)
	return nil
}

func (m *MockBroker) IsConnected() bool {
	return atomic.LoadInt32(&m.connected) == 1
}

func (m *MockBroker) ReconnectNotify() <-chan struct{} {
	return m.reconnectChan
}

func (m *MockBroker) SetConnected(conn bool) {
	if conn {
		atomic.StoreInt32(&m.connected, 1)
		select {
		case m.reconnectChan <- struct{}{}:
		default:
		}
	} else {
		atomic.StoreInt32(&m.connected, 0)
	}
}

func (m *MockBroker) Count() int {
	m.mu.Lock()
	defer m.mu.Unlock()
	return len(m.messages)
}

func (m *MockBroker) Close() {
	atomic.StoreInt32(&m.connected, 0)
}

func TestProtocolParsers(t *testing.T) {
	// 1. OPC UA Parser
	opcuaJSON := []byte(`{
		"nodeId": "ns=2;s=Turbine.RPM",
		"value": 3600.5,
		"status": "Good",
		"sourceTimestamp": "2026-10-08T22:00:00Z",
		"metrics": {"vibration_hz": 12.4}
	}`)
	rec, err := parser.ParseOPCUA(opcuaJSON)
	if err != nil {
		t.Fatalf("OPC UA parse failed: %v", err)
	}
	if rec.SourceId != "ns=2;s=Turbine.RPM" {
		t.Errorf("Unexpected source ID: %s", rec.SourceId)
	}
	if len(rec.Metrics) != 2 {
		t.Errorf("Expected 2 metrics, got %d", len(rec.Metrics))
	}

	// 2. MQTT Parser
	mqttJSON := []byte(`{
		"device_id": "plc-gateway-01",
		"temperature": 45.2,
		"pressure_psi": 120.0,
		"status": "nominal"
	}`)
	recMQTT, err := parser.ParseMQTT("aegistwin/devices/plc-gateway-01/telemetry", mqttJSON)
	if err != nil {
		t.Fatalf("MQTT parse failed: %v", err)
	}
	if recMQTT.SourceId != "plc-gateway-01" {
		t.Errorf("Unexpected MQTT source: %s", recMQTT.SourceId)
	}

	// 3. Syslog RFC 5424 Parser
	syslogData := []byte(`<165>1 2026-10-08T22:14:15.003Z border-fw-01 firewall - ID47 [threat@123 severity="high"] Port scan detected from 198.51.100.4`)
	recSys, err := parser.ParseSyslog(syslogData)
	if err != nil {
		t.Fatalf("Syslog parse failed: %v", err)
	}
	if recSys.SourceId != "border-fw-01" {
		t.Errorf("Unexpected Syslog host: %s", recSys.SourceId)
	}
	if recSys.Severity != pb.SeverityLevel_SEVERITY_INFO {
		t.Errorf("Expected severity INFO for PRI 165 (165 mod 8 = 5), got %v", recSys.Severity)
	}
}

func TestProtobufSchemaValidation(t *testing.T) {
	// Valid record
	rec := &pb.TelemetryRecord{
		RecordId:    "rec-001",
		SourceId:    "sensor-01",
		Protocol:    pb.ProtocolType_PROTOCOL_MQTT,
		TimestampNs: time.Now().UnixNano(),
		Metrics: []*pb.MetricDataPoint{
			{Name: "cpu_usage", Value: 75.4},
		},
	}
	if err := validator.ValidateRecord(rec); err != nil {
		t.Fatalf("Valid record failed validation: %v", err)
	}

	// Missing Record ID
	rec.RecordId = ""
	if err := validator.ValidateRecord(rec); err != validator.ErrEmptyRecordID {
		t.Errorf("Expected ErrEmptyRecordID, got %v", err)
	}
	rec.RecordId = "rec-001"

	// NaN metric value
	rec.Metrics[0].Value = math.NaN()
	if err := validator.ValidateRecord(rec); err != validator.ErrNonFiniteMetricVal {
		t.Errorf("Expected ErrNonFiniteMetricVal for NaN, got %v", err)
	}
}

func TestBufferOutageAndReconnectionFlush(t *testing.T) {
	dbFile := "./test_buffer.db"
	defer os.Remove(dbFile)

	buf, err := buffer.NewLocalBuffer(dbFile, 10000)
	if err != nil {
		t.Fatalf("Failed creating buffer: %v", err)
	}
	defer buf.Close()

	mockBroker := NewMockBroker()
	pipe := pipeline.NewTelemetryPipeline(mockBroker, buf, "test.telemetry", 10000, 4)
	defer pipe.Stop()

	// 1. Broker is initially online -> publishes directly
	payload := []byte(`{"device_id":"sensor-10","temp":25.0}`)
	if err := pipe.Ingest(pb.ProtocolType_PROTOCOL_MQTT, "test/sensor-10", payload); err != nil {
		t.Fatalf("Ingest failed: %v", err)
	}

	time.Sleep(50 * time.Millisecond)
	if mockBroker.Count() != 1 {
		t.Errorf("Expected 1 published message, got %d", mockBroker.Count())
	}

	// 2. Disconnect broker (simulate network outage)
	mockBroker.SetConnected(false)

	// Ingest 25 messages while offline
	for i := 0; i < 25; i++ {
		p := []byte(fmt.Sprintf(`{"device_id":"sensor-%d","val":%d}`, i, i))
		pipe.Ingest(pb.ProtocolType_PROTOCOL_MQTT, "test/offline", p)
	}

	// Wait for workers to finish buffering all 25 messages
	deadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(deadline) {
		if pipe.Metrics().BufferedCount >= 25 {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}

	count, err := buf.Count()
	if err != nil {
		t.Fatalf("Buffer count failed: %v", err)
	}
	if count != 25 {
		t.Fatalf("Expected 25 buffered messages in SQLite, got %d", count)
	}

	// 3. Reconnect broker -> buffer flusher drains
	mockBroker.SetConnected(true)

	// Wait for background flusher to drain buffer
	flushDeadline := time.Now().Add(3 * time.Second)
	for time.Now().Before(flushDeadline) {
		c, _ := buf.Count()
		if c == 0 && pipe.Metrics().FlushedCount >= 25 {
			break
		}
		time.Sleep(20 * time.Millisecond)
	}

	countAfter, _ := buf.Count()
	if countAfter != 0 {
		t.Errorf("Expected 0 buffered messages after flush, got %d", countAfter)
	}

	metrics := pipe.Metrics()
	if metrics.FlushedCount != 25 {
		t.Errorf("Expected 25 flushed messages, got %d", metrics.FlushedCount)
	}
}

func TestHighThroughputConcurrency(t *testing.T) {
	dbFile := "./test_perf_buffer.db"
	defer os.Remove(dbFile)

	buf, err := buffer.NewLocalBuffer(dbFile, 100000)
	if err != nil {
		t.Fatalf("Failed creating buffer: %v", err)
	}
	defer buf.Close()

	mockBroker := NewMockBroker()
	// High capacity queue & 16 workers
	pipe := pipeline.NewTelemetryPipeline(mockBroker, buf, "perf.telemetry", 100000, 16)
	defer pipe.Stop()

	totalRequests := 50000
	concurrency := 50
	requestsPerRoutine := totalRequests / concurrency

	payload := []byte(`{"device_id":"edge-perf-node","cpu_load":42.5,"mem_mb":1024}`)

	start := time.Now()
	var wg sync.WaitGroup

	for c := 0; c < concurrency; c++ {
		wg.Add(1)
		go func(routineID int) {
			defer wg.Done()
			for i := 0; i < requestsPerRoutine; i++ {
				if err := pipe.Ingest(pb.ProtocolType_PROTOCOL_MQTT, "perf/test", payload); err != nil {
					// Queue saturation handled gracefully
				}
			}
		}(c)
	}

	wg.Wait()
	duration := time.Since(start)

	// Allow workers to finish draining queue
	time.Sleep(200 * time.Millisecond)

	metrics := pipe.Metrics()
	throughput := float64(metrics.IngestedCount) / duration.Seconds()

	t.Logf("Completed %d ingestions in %v (Throughput: %.2f req/sec, Published: %d, Dropped: %d, Errors: %d)",
		metrics.IngestedCount, duration, throughput, metrics.PublishedCount, metrics.DroppedCount, metrics.ErrorCount)

	if metrics.ErrorCount > 0 {
		t.Errorf("Expected 0 errors during concurrent ingestion, got %d", metrics.ErrorCount)
	}
	if metrics.IngestedCount != uint64(totalRequests) {
		t.Errorf("Expected %d ingested requests, got %d", totalRequests, metrics.IngestedCount)
	}
}
