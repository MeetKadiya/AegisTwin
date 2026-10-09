package parser

import (
	"testing"

	pb "aegistwin/edge-agent/proto"
)

func TestParseSparkplugTopicValid(t *testing.T) {
	topic := "spBv1.0/FactoryFloor1/DDATA/EdgeNode01/PLC_Turbine"
	header, err := ParseSparkplugTopic(topic)
	if err != nil {
		t.Fatalf("unexpected error parsing valid topic: %v", err)
	}

	if header.Namespace != "spBv1.0" {
		t.Errorf("expected namespace 'spBv1.0', got '%s'", header.Namespace)
	}
	if header.GroupID != "FactoryFloor1" {
		t.Errorf("expected group 'FactoryFloor1', got '%s'", header.GroupID)
	}
	if header.MessageType != "DDATA" {
		t.Errorf("expected type 'DDATA', got '%s'", header.MessageType)
	}
	if header.EdgeNodeID != "EdgeNode01" {
		t.Errorf("expected edge node 'EdgeNode01', got '%s'", header.EdgeNodeID)
	}
	if header.DeviceID != "PLC_Turbine" {
		t.Errorf("expected device 'PLC_Turbine', got '%s'", header.DeviceID)
	}
}

func TestParseSparkplugTopicNodeOnly(t *testing.T) {
	topic := "spBv1.0/PlantA/NBIRTH/Gateway01"
	header, err := ParseSparkplugTopic(topic)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if header.MessageType != "NBIRTH" || header.DeviceID != "" {
		t.Errorf("expected NBIRTH with empty device, got %s / %s", header.MessageType, header.DeviceID)
	}
}

func TestParseSparkplugTopicInvalid(t *testing.T) {
	invalidTopics := []string{
		"invalid/format",
		"spBv1.0/too/short",
		"other/group/NDATA/node",
	}
	for _, top := range invalidTopics {
		if _, err := ParseSparkplugTopic(top); err == nil {
			t.Errorf("expected error for topic '%s', got nil", top)
		}
	}
}

func TestParseSparkplugBPayload(t *testing.T) {
	topic := "spBv1.0/Sector7/DDATA/Gateway_01/Centrifuge_4"
	jsonPayload := []byte(`{
		"timestamp": 1700000000000,
		"seq": 42,
		"metrics": [
			{"name": "vibration_rms", "datatype": "float", "value": 4.82},
			{"name": "temperature_c", "datatype": "float", "value": 78.5},
			{"name": "cooling_valve_open", "datatype": "boolean", "value": true},
			{"name": "status_msg", "datatype": "string", "value": "nominal"}
		]
	}`)

	rec, err := ParseSparkplugB(topic, jsonPayload)
	if err != nil {
		t.Fatalf("failed to parse Sparkplug B: %v", err)
	}

	if rec.SourceId != "Gateway_01/Centrifuge_4" {
		t.Errorf("expected sourceId 'Gateway_01/Centrifuge_4', got '%s'", rec.SourceId)
	}
	if len(rec.Metrics) != 3 {
		t.Errorf("expected 3 numeric metrics, got %d", len(rec.Metrics))
	}
	if rec.Attributes["status_msg"] != "nominal" {
		t.Errorf("expected string attribute 'nominal', got '%s'", rec.Attributes["status_msg"])
	}
	if rec.Attributes["sparkplug_seq"] != "42" {
		t.Errorf("expected seq '42', got '%s'", rec.Attributes["sparkplug_seq"])
	}
	if rec.Severity != pb.SeverityLevel_SEVERITY_INFO {
		t.Errorf("expected SEVERITY_INFO, got %v", rec.Severity)
	}
}

func TestParseSparkplugBDeathSeverity(t *testing.T) {
	topic := "spBv1.0/Sector7/DDEATH/Gateway_01/Centrifuge_4"
	jsonPayload := []byte(`{
		"timestamp": 1700000000000,
		"metrics": []
	}`)

	rec, err := ParseSparkplugB(topic, jsonPayload)
	if err != nil {
		t.Fatalf("unexpected error: %v", err)
	}
	if rec.Severity != pb.SeverityLevel_SEVERITY_ERROR {
		t.Errorf("expected DDEATH to produce SEVERITY_ERROR, got %v", rec.Severity)
	}
}
