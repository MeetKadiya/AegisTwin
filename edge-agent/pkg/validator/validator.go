package validator

import (
	"errors"
	"math"
	"strings"
	"time"

	pb "aegistwin/edge-agent/proto"
)

var (
	ErrEmptyRecordID      = errors.New("record_id cannot be empty")
	ErrEmptySourceID      = errors.New("source_id cannot be empty")
	ErrInvalidProtocol    = errors.New("protocol must be OPC_UA, MQTT, or SYSLOG")
	ErrInvalidTimestamp   = errors.New("timestamp_ns must be a valid epoch nanoseconds timestamp")
	ErrEmptyContent       = errors.New("record must contain at least one metric, attribute, or raw_payload")
	ErrInvalidMetricName  = errors.New("metric name cannot be empty")
	ErrNonFiniteMetricVal = errors.New("metric value must be a finite number (not NaN or Inf)")
)

const (
	minTimestampNs = int64(946684800000000000) // 2000-01-01T00:00:00Z
)

// ValidateRecord enforces strict Protobuf schema invariants before message bus dispatch.
func ValidateRecord(rec *pb.TelemetryRecord) error {
	if rec == nil {
		return errors.New("telemetry record is nil")
	}

	if strings.TrimSpace(rec.RecordId) == "" {
		return ErrEmptyRecordID
	}

	if strings.TrimSpace(rec.SourceId) == "" {
		return ErrEmptySourceID
	}

	switch rec.Protocol {
	case pb.ProtocolType_PROTOCOL_OPC_UA, pb.ProtocolType_PROTOCOL_MQTT, pb.ProtocolType_PROTOCOL_SYSLOG:
		// valid
	default:
		return ErrInvalidProtocol
	}

	// Validate timestamp sanity (must not be zero, ancient, or distant future)
	maxFutureNs := time.Now().Add(24 * time.Hour).UnixNano()
	if rec.TimestampNs < minTimestampNs || rec.TimestampNs > maxFutureNs {
		return ErrInvalidTimestamp
	}

	// Record must carry actual telemetry payload
	if len(rec.Metrics) == 0 && len(rec.Attributes) == 0 && len(rec.RawPayload) == 0 {
		return ErrEmptyContent
	}

	// Validate each metric data point
	for _, m := range rec.Metrics {
		if m == nil {
			continue
		}
		if strings.TrimSpace(m.Name) == "" {
			return ErrInvalidMetricName
		}
		if math.IsNaN(m.Value) || math.IsInf(m.Value, 0) {
			return ErrNonFiniteMetricVal
		}
	}

	return nil
}
