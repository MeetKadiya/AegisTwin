package parser

import (
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"time"

	pb "aegistwin/edge-agent/proto"
)

var (
	// ErrInvalidSparkplugTopic is returned when the topic does not follow spBv1.0 namespace
	ErrInvalidSparkplugTopic = errors.New("invalid Sparkplug B topic structure")
	// ErrEmptySparkplugPayload is returned when the data payload is zero bytes
	ErrEmptySparkplugPayload = errors.New("empty Sparkplug B payload")
)

// SparkplugMetric represents a single metric within a Sparkplug B payload
type SparkplugMetric struct {
	Name        string      `json:"name"`
	Alias       uint64      `json:"alias,omitempty"`
	Timestamp   uint64      `json:"timestamp,omitempty"`
	Datatype    string      `json:"datatype,omitempty"`
	IsHistorical bool       `json:"is_historical,omitempty"`
	IsNull      bool        `json:"is_null,omitempty"`
	Value       interface{} `json:"value"`
}

// SparkplugPayload represents the JSON payload format of Sparkplug B
type SparkplugPayload struct {
	Timestamp uint64            `json:"timestamp"`
	Metrics   []SparkplugMetric `json:"metrics"`
	Seq       *int64            `json:"seq,omitempty"`
	UUID      string            `json:"uuid,omitempty"`
	Body      []byte            `json:"body,omitempty"`
}

// SparkplugTopicHeader parses spBv1.0/<group_id>/<message_type>/<edge_node_id>/[device_id]
type SparkplugTopicHeader struct {
	Namespace   string // "spBv1.0"
	GroupID     string
	MessageType string // NBIRTH, NDEATH, DBIRTH, DDEATH, NDATA, DDATA, NCMD, DCMD
	EdgeNodeID  string
	DeviceID    string
}

// ParseSparkplugTopic extracts metadata elements from a Sparkplug B topic.
func ParseSparkplugTopic(topic string) (*SparkplugTopicHeader, error) {
	trimmed := strings.Trim(topic, "/")
	parts := strings.Split(trimmed, "/")
	if len(parts) < 4 || parts[0] != "spBv1.0" {
		return nil, fmt.Errorf("%w: expected spBv1.0/<group>/<type>/<edge_node>/[device], got '%s'", ErrInvalidSparkplugTopic, topic)
	}

	header := &SparkplugTopicHeader{
		Namespace:   parts[0],
		GroupID:     parts[1],
		MessageType: strings.ToUpper(parts[2]),
		EdgeNodeID:  parts[3],
	}
	if len(parts) >= 5 {
		header.DeviceID = parts[4]
	}
	return header, nil
}

// ParseSparkplugB converts a Sparkplug B message into a normalized Protobuf TelemetryRecord.
func ParseSparkplugB(topic string, data []byte) (*pb.TelemetryRecord, error) {
	if len(data) == 0 {
		return nil, ErrEmptySparkplugPayload
	}

	header, err := ParseSparkplugTopic(topic)
	if err != nil {
		return nil, err
	}

	var spPayload SparkplugPayload
	if err := json.Unmarshal(data, &spPayload); err != nil {
		return nil, fmt.Errorf("failed to unmarshal Sparkplug B payload: %w", err)
	}

	nowNs := time.Now().UnixNano()
	tsNs := nowNs
	if spPayload.Timestamp > 0 {
		// Sparkplug B timestamp is in milliseconds
		tsNs = int64(spPayload.Timestamp) * 1_000_000
	}

	sourceID := header.EdgeNodeID
	if header.DeviceID != "" {
		sourceID = fmt.Sprintf("%s/%s", header.EdgeNodeID, header.DeviceID)
	}

	pbMetrics := make([]*pb.MetricDataPoint, 0, len(spPayload.Metrics))
	attrs := make(map[string]string, 6+len(spPayload.Metrics))
	attrs["sparkplug_namespace"] = header.Namespace
	attrs["sparkplug_group"] = header.GroupID
	attrs["sparkplug_msg_type"] = header.MessageType
	attrs["sparkplug_edge_node"] = header.EdgeNodeID
	if header.DeviceID != "" {
		attrs["sparkplug_device"] = header.DeviceID
	}
	if spPayload.Seq != nil {
		attrs["sparkplug_seq"] = fmt.Sprintf("%d", *spPayload.Seq)
	}

	severity := pb.SeverityLevel_SEVERITY_INFO
	if header.MessageType == "NDEATH" || header.MessageType == "DDEATH" {
		severity = pb.SeverityLevel_SEVERITY_ERROR
	}

	for _, m := range spPayload.Metrics {
		if m.Name == "" && m.Alias > 0 {
			m.Name = fmt.Sprintf("alias_%d", m.Alias)
		}
		if m.Name == "" {
			continue
		}

		metricTs := tsNs
		if m.Timestamp > 0 {
			metricTs = int64(m.Timestamp) * 1_000_000
		}

		switch v := m.Value.(type) {
		case float64:
			pbMetrics = append(pbMetrics, &pb.MetricDataPoint{
				Name:        m.Name,
				Value:       v,
				TimestampNs: metricTs,
				Unit:        m.Datatype,
			})
		case bool:
			val := 0.0
			if v {
				val = 1.0
			}
			pbMetrics = append(pbMetrics, &pb.MetricDataPoint{
				Name:        m.Name,
				Value:       val,
				TimestampNs: metricTs,
				Unit:        "boolean",
			})
		case string:
			attrs[m.Name] = v
		default:
			if v != nil {
				attrs[m.Name] = fmt.Sprintf("%v", v)
			}
		}
	}

	recID := fmt.Sprintf("spb-%s-%s-%d", header.GroupID, sourceID, tsNs)

	return &pb.TelemetryRecord{
		RecordId:        recID,
		SourceId:        sourceID,
		Protocol:        pb.ProtocolType_PROTOCOL_MQTT,
		Severity:        severity,
		TimestampNs:     tsNs,
		Metrics:         pbMetrics,
		Attributes:      attrs,
		RawPayload:      data,
		IngestionTimeNs: nowNs,
		SchemaVersion:   1,
	}, nil
}
