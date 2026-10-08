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
	ErrMalformedOPCUA = errors.New("malformed OPC UA payload")
)

type opcUaPayload struct {
	NodeID          string                 `json:"nodeId"`
	Value           interface{}            `json:"value"`
	StatusCode      string                 `json:"status"`
	SourceTimestamp string                 `json:"sourceTimestamp"`
	ServerTimestamp string                 `json:"serverTimestamp"`
	Metrics         map[string]float64     `json:"metrics"`
	Properties      map[string]interface{} `json:"properties"`
}

// ParseOPCUA converts raw OPC UA JSON telemetry into a standardized Protobuf TelemetryRecord.
func ParseOPCUA(data []byte) (*pb.TelemetryRecord, error) {
	if len(data) == 0 {
		return nil, ErrMalformedOPCUA
	}

	var parsed opcUaPayload
	if err := json.Unmarshal(data, &parsed); err != nil {
		return nil, fmt.Errorf("%w: %v", ErrMalformedOPCUA, err)
	}

	if parsed.NodeID == "" && len(parsed.Metrics) == 0 {
		return nil, fmt.Errorf("%w: missing nodeId and metrics", ErrMalformedOPCUA)
	}

	// Determine timestamp
	ts := time.Now().UnixNano()
	if parsed.SourceTimestamp != "" {
		if t, err := time.Parse(time.RFC3339Nano, parsed.SourceTimestamp); err == nil {
			ts = t.UnixNano()
		} else if t, err := time.Parse(time.RFC3339, parsed.SourceTimestamp); err == nil {
			ts = t.UnixNano()
		}
	}

	sourceID := parsed.NodeID
	if sourceID == "" {
		sourceID = "opcua-unknown-node"
	}

	// Severity mapping from OPC UA status
	severity := pb.SeverityLevel_SEVERITY_INFO
	statusLower := strings.ToLower(parsed.StatusCode)
	if strings.Contains(statusLower, "bad") {
		severity = pb.SeverityLevel_SEVERITY_ERROR
	} else if strings.Contains(statusLower, "uncertain") {
		severity = pb.SeverityLevel_SEVERITY_WARN
	}

	metrics := make([]*pb.MetricDataPoint, 0, len(parsed.Metrics)+1)

	// Direct numeric value
	if parsed.Value != nil {
		switch v := parsed.Value.(type) {
		case float64:
			metrics = append(metrics, &pb.MetricDataPoint{
				Name:        sourceID,
				Value:       v,
				TimestampNs: ts,
			})
		case int:
			metrics = append(metrics, &pb.MetricDataPoint{
				Name:        sourceID,
				Value:       float64(v),
				TimestampNs: ts,
			})
		}
	}

	for k, v := range parsed.Metrics {
		metrics = append(metrics, &pb.MetricDataPoint{
			Name:        k,
			Value:       v,
			TimestampNs: ts,
		})
	}

	attrs := make(map[string]string)
	if parsed.StatusCode != "" {
		attrs["opcua_status"] = parsed.StatusCode
	}
	if parsed.NodeID != "" {
		attrs["node_id"] = parsed.NodeID
	}
	for k, v := range parsed.Properties {
		attrs[k] = fmt.Sprintf("%v", v)
	}

	recID := fmt.Sprintf("opcua-%d-%s", ts, strings.ReplaceAll(sourceID, ";", "-"))

	return &pb.TelemetryRecord{
		RecordId:        recID,
		SourceId:        sourceID,
		Protocol:        pb.ProtocolType_PROTOCOL_OPC_UA,
		Severity:        severity,
		TimestampNs:     ts,
		Metrics:         metrics,
		Attributes:      attrs,
		RawPayload:      data,
		IngestionTimeNs: time.Now().UnixNano(),
		SchemaVersion:   1,
	}, nil
}
