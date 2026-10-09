"use client";

import React, { useState, useMemo, useRef, useEffect } from "react";
import {
  Activity,
  Play,
  Pause,
  Search,
  Filter,
  Trash2,
  Download,
  Terminal,
  ShieldAlert,
  Radio,
  ArrowDown,
  Layers,
} from "lucide-react";
import { TelemetryLogEvent } from "@/lib/types";

interface LiveTelemetryStreamProps {
  logs: TelemetryLogEvent[];
  onClearLogs?: () => void;
  isStreaming?: boolean;
}

export default function LiveTelemetryStream({
  logs,
  onClearLogs,
  isStreaming = true,
}: LiveTelemetryStreamProps) {
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [filterChannel, setFilterChannel] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll on new logs when enabled
  useEffect(() => {
    if (autoScroll && !isPaused && logContainerRef.current) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [logs, autoScroll, isPaused]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (filterSeverity !== "ALL" && log.level !== filterSeverity) return false;
      if (filterChannel !== "ALL" && log.channel !== filterChannel) return false;
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesMsg = log.message.toLowerCase().includes(query);
        const matchesSource = log.source.toLowerCase().includes(query);
        const matchesIp = log.ip?.toLowerCase().includes(query);
        const matchesMitre = log.mitre?.toLowerCase().includes(query);
        if (!matchesMsg && !matchesSource && !matchesIp && !matchesMitre) return false;
      }
      return true;
    });
  }, [logs, filterSeverity, filterChannel, searchQuery]);

  const getSeverityBadge = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return (
          <span className="px-1.5 py-0.5 rounded bg-status-critical/15 text-status-critical border border-status-critical/40 font-mono font-bold text-[9px] shadow-glow-crimson animate-pulse">
            CRITICAL
          </span>
        );
      case "WARN":
        return (
          <span className="px-1.5 py-0.5 rounded bg-status-warning/15 text-status-warning border border-status-warning/40 font-mono font-bold text-[9px]">
            WARN
          </span>
        );
      default:
        return (
          <span className="px-1.5 py-0.5 rounded bg-cyber-blue/15 text-cyber-blue border border-cyber-blue/30 font-mono text-[9px]">
            INFO
          </span>
        );
    }
  };

  const handleExportLogs = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(filteredLogs, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `aegistwin_telemetry_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex flex-col h-full bg-surface border border-border rounded-xl overflow-hidden shadow-soc-card select-none font-mono">
      {/* Console Header Bar */}
      <div className="p-3 border-b border-border bg-surface-subtle/80 flex flex-wrap items-center justify-between gap-2 shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-cyber-blue/10 border border-cyber-blue/30 text-cyber-blue">
            <Terminal className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-typography-primary flex items-center gap-2">
              Live Telemetry Stream
              <span className={`w-2 h-2 rounded-full ${isPaused ? "bg-status-warning" : "bg-status-healthy live-beacon"}`} />
            </h3>
            <div className="text-[10px] text-typography-muted">
              {filteredLogs.length} events buffered • WebSocket full duplex
            </div>
          </div>
        </div>

        {/* Controls: Pause, Auto-scroll, Export, Clear */}
        <div className="flex items-center gap-1.5 text-xs">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`flex items-center gap-1 px-2.5 py-1 rounded-md border text-[11px] transition-colors ${
              isPaused
                ? "bg-status-warning/20 border-status-warning/40 text-status-warning font-bold"
                : "bg-surface hover:bg-surface-hover border-border text-typography-primary"
            }`}
            title={isPaused ? "Resume stream" : "Pause stream"}
          >
            {isPaused ? <Play className="w-3 h-3 fill-current" /> : <Pause className="w-3 h-3 fill-current" />}
            <span>{isPaused ? "PAUSED" : "LIVE"}</span>
          </button>

          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`p-1 rounded-md border text-[11px] transition-colors ${
              autoScroll
                ? "bg-cyber-blue/15 border-cyber-blue/40 text-cyber-blue"
                : "bg-surface hover:bg-surface-hover border-border text-typography-muted"
            }`}
            title={autoScroll ? "Auto-scroll ON" : "Auto-scroll OFF"}
          >
            <ArrowDown className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={handleExportLogs}
            className="p-1 rounded-md bg-surface hover:bg-surface-hover border border-border text-typography-muted hover:text-typography-primary transition-colors"
            title="Export filtered logs as JSON"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          {onClearLogs && (
            <button
              onClick={onClearLogs}
              className="p-1 rounded-md bg-surface hover:bg-surface-hover border border-border text-typography-muted hover:text-status-critical transition-colors"
              title="Clear event buffer"
            >
              <Trash2 className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Toolbar Strip */}
      <div className="p-2 border-b border-border bg-surface/50 flex flex-wrap items-center justify-between gap-2 text-xs">
        {/* Search Input */}
        <div className="relative flex-1 min-w-[180px]">
          <Search className="w-3.5 h-3.5 text-typography-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter logs by IP, host, CVE..."
            className="w-full pl-8 pr-2 py-1 rounded bg-canvas border border-border text-[11px] text-typography-primary placeholder-typography-muted focus:outline-none focus:border-cyber-blue"
          />
        </div>

        {/* Severity Selector Pills */}
        <div className="flex items-center gap-1 text-[10px]">
          {["ALL", "CRITICAL", "WARN", "INFO"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`px-2 py-0.5 rounded border transition-colors ${
                filterSeverity === sev
                  ? "bg-surface-hover text-typography-primary border-cyber-blue font-bold"
                  : "bg-surface-subtle text-typography-muted border-border hover:text-typography-primary"
              }`}
            >
              {sev}
            </button>
          ))}
        </div>

        {/* Channel Selector Pills */}
        <div className="hidden lg:flex items-center gap-1 text-[10px]">
          {["ALL", "TELEMETRY", "SECURITY", "SIMULATION", "SOAR"].map((chan) => (
            <button
              key={chan}
              onClick={() => setFilterChannel(chan)}
              className={`px-1.5 py-0.5 rounded border transition-colors ${
                filterChannel === chan
                  ? "bg-cyber-blue/20 text-cyber-blue border-cyber-blue/40 font-bold"
                  : "bg-surface-subtle text-typography-muted border-border hover:text-typography-primary"
              }`}
            >
              {chan}
            </button>
          ))}
        </div>
      </div>

      {/* Streaming Events Table / List */}
      <div
        ref={logContainerRef}
        className="flex-1 overflow-y-auto divide-y divide-border/60 bg-canvas text-[11px]"
      >
        {filteredLogs.length === 0 ? (
          <div className="text-center py-16 text-typography-muted">
            <Radio className="w-6 h-6 mx-auto mb-2 text-border" />
            No telemetry frames matching current filters.
          </div>
        ) : (
          filteredLogs.map((log) => (
            <div
              key={log.id}
              className={`px-3 py-2 hover:bg-surface-subtle transition-colors flex items-start gap-3 group ${
                log.level === "CRITICAL"
                  ? "bg-status-critical/5 hover:bg-status-critical/10"
                  : ""
              }`}
            >
              {/* Timestamp */}
              <div className="text-[10px] text-typography-muted shrink-0 w-20 pt-0.5">
                {log.timestamp}
              </div>

              {/* Severity Pill */}
              <div className="shrink-0 w-16">{getSeverityBadge(log.level)}</div>

              {/* Channel */}
              <div className="text-[10px] text-cyber-cyan shrink-0 w-24 truncate hidden sm:block">
                [{log.channel}]
              </div>

              {/* Source */}
              <div className="text-[11px] text-typography-primary font-semibold shrink-0 w-32 truncate" title={log.source}>
                {log.source}
              </div>

              {/* Message Payload */}
              <div className="flex-1 text-typography-primary break-words leading-relaxed">
                <span>{log.message}</span>
                {log.mitre && (
                  <span className="ml-2 inline-flex items-center px-1.5 py-0.2 rounded bg-surface border border-border text-[9px] text-cyber-blue font-bold">
                    MITRE {log.mitre}
                  </span>
                )}
                {log.ip && (
                  <span className="ml-2 text-[10px] text-typography-muted">({log.ip})</span>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
