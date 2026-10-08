package parser

import (
	"errors"
	"fmt"
	"regexp"
	"strconv"
	"strings"
	"time"

	pb "aegistwin/edge-agent/proto"
)

var (
	ErrMalformedSyslog = errors.New("malformed Syslog payload")

	// RFC 5424: <PRI>VERSION TIMESTAMP HOSTNAME APP-NAME PROCID MSGID [STRUCTURED-DATA] MSG
	rfc5424Regex = regexp.MustCompile(`^<(\d{1,3})>1\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*(?:\[(.*?)\])?\s*(.*)$`)

	// RFC 3164: <PRI>Mmm dd hh:mm:ss HOSTNAME TAG: MSG
	rfc3164Regex = regexp.MustCompile(`^<(\d{1,3})>([A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+(\S+)\s+([^:]+):\s*(.*)$`)
)

// ParseSyslog converts raw Syslog datagrams into standardized TelemetryRecord.
func ParseSyslog(data []byte) (*pb.TelemetryRecord, error) {
	line := strings.TrimSpace(string(data))
	if len(line) == 0 {
		return nil, ErrMalformedSyslog
	}

	var (
		priStr   string
		tsStr    string
		hostname string
		appName  string
		msg      string
		ts       = time.Now().UnixNano()
		attrs    = make(map[string]string)
	)

	if matches := rfc5424Regex.FindStringSubmatch(line); len(matches) > 0 {
		priStr = matches[1]
		tsStr = matches[2]
		hostname = matches[3]
		appName = matches[4]
		attrs["proc_id"] = matches[5]
		attrs["msg_id"] = matches[6]
		if matches[7] != "" {
			attrs["structured_data"] = matches[7]
		}
		msg = matches[8]

		if t, err := time.Parse(time.RFC3339Nano, tsStr); err == nil {
			ts = t.UnixNano()
		} else if t, err := time.Parse(time.RFC3339, tsStr); err == nil {
			ts = t.UnixNano()
		}
	} else if matches := rfc3164Regex.FindStringSubmatch(line); len(matches) > 0 {
		priStr = matches[1]
		tsStr = matches[2]
		hostname = matches[3]
		appName = matches[4]
		msg = matches[5]

		// RFC 3164 has no year; use current year
		currentYear := time.Now().Year()
		timeWithYear := fmt.Sprintf("%d %s", currentYear, tsStr)
		if t, err := time.Parse("2006 Jan _2 15:04:05", timeWithYear); err == nil {
			ts = t.UnixNano()
		}
	} else {
		// Fallback for simple PRI or unstructured syslog
		if strings.HasPrefix(line, "<") {
			endIdx := strings.Index(line, ">")
			if endIdx > 1 && endIdx <= 4 {
				priStr = line[1:endIdx]
				msg = strings.TrimSpace(line[endIdx+1:])
				hostname = "syslog-host"
				appName = "syslog"
			}
		}
		if priStr == "" {
			return nil, ErrMalformedSyslog
		}
	}

	pri, _ := strconv.Atoi(priStr)
	severityNum := pri % 8
	facilityNum := pri / 8

	var severity pb.SeverityLevel
	switch severityNum {
	case 0, 1, 2:
		severity = pb.SeverityLevel_SEVERITY_CRITICAL
	case 3:
		severity = pb.SeverityLevel_SEVERITY_ERROR
	case 4:
		severity = pb.SeverityLevel_SEVERITY_WARN
	case 5, 6:
		severity = pb.SeverityLevel_SEVERITY_INFO
	default:
		severity = pb.SeverityLevel_SEVERITY_DEBUG
	}

	attrs["facility"] = strconv.Itoa(facilityNum)
	attrs["app_name"] = appName
	attrs["hostname"] = hostname
	attrs["syslog_message"] = msg

	sourceID := hostname
	if sourceID == "" || sourceID == "-" {
		sourceID = "syslog-source"
	}

	recID := fmt.Sprintf("syslog-%s-%d", sourceID, ts)

	return &pb.TelemetryRecord{
		RecordId:        recID,
		SourceId:        sourceID,
		Protocol:        pb.ProtocolType_PROTOCOL_SYSLOG,
		Severity:        severity,
		TimestampNs:     ts,
		Metrics:         nil,
		Attributes:      attrs,
		RawPayload:      data,
		IngestionTimeNs: time.Now().UnixNano(),
		SchemaVersion:   1,
	}, nil
}
