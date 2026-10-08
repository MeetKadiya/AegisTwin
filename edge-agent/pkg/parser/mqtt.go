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
	ErrMalformedMQTT = errors.New("malformed MQTT payload")
)

// ParseMQTT converts an MQTT topic and message body into a Protobuf TelemetryRecord.
func ParseMQTT(topic string, data []byte) (*pb.TelemetryRecord, error) {
	if len(data) == 0 {
		return nil, ErrMalformedMQTT
	}

	var rawMap map[string]interface{}
	if err := json.Unmarshal(data, &rawMap); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrMalformedMQTT, err)
	}

	// Extract device ID from topic or payload
	sourceID := "mqtt-unknown"
	parts := strings.Split(strings.Trim(topic, "/"), "/")
	if len(parts) >= 2 {
		sourceID = parts[len(parts)-2]
		if sourceID == "devices" || sourceID == "telemetry" || sourceID == "sensors" {
			sourceID = parts[len(parts)-1]
		}
	} else if len(parts) == 1 && parts[0] != "" {
		sourceID = parts[0]
	}

	if devID, ok := rawMap["device_id"].(string); ok && devID != "" {
		sourceID = devID
	} else if clientID, ok := rawMap["client_id"].(string); ok && clientID != "" {
		sourceID = clientID
	}

	ts := time.Now().UnixNano()
	if rawTs, ok := rawMap["timestamp"].(float64); ok && rawTs > 0 {
		// Detect seconds vs millis vs nanos
		if rawTs < 1e11 {
			ts = int64(rawTs * 1e9)
		} else if rawTs < 1e14 {
			ts = int64(rawTs * 1e6)
		} else {
			ts = int64(rawTs)
		}
	} else if strTs, ok := rawMap["timestamp"].(string); ok {
		if t, err := time.Parse(time.RFC3339, strTs); err == nil {
			ts = t.UnixNano()
		}
	}

	metrics := make([]*pb.MetricDataPoint, 0, len(rawMap))
	attrs := make(map[string]string)
	attrs["mqtt_topic"] = topic

	for k, v := range rawMap {
		if k == "timestamp" || k == "device_id" || k == "client_id" {
			continue
		}
		switch val := v.(type) {
		case float64:
			metrics = append(metrics, &pb.MetricDataPoint{
				Name:        k,
				Value:       val,
				TimestampNs: ts,
			})
		case string:
			attrs[k] = val
		case bool:
			boolVal := 0.0
			if val {
				boolVal = 1.0
			}
			metrics = append(metrics, &pb.MetricDataPoint{
				Name:        k,
				Value:       boolVal,
				TimestampNs: ts,
			})
		}
	}

	recID := fmt.Sprintf("mqtt-%s-%d", sourceID, ts)

	return &pb.TelemetryRecord{
		RecordId:        recID,
		SourceId:        sourceID,
		Protocol:        pb.ProtocolType_PROTOCOL_MQTT,
		Severity:        pb.SeverityLevel_SEVERITY_INFO,
		TimestampNs:     ts,
		Metrics:         metrics,
		Attributes:      attrs,
		RawPayload:      data,
		IngestionTimeNs: time.Now().UnixNano(),
		SchemaVersion:   1,
	}, nil
}
