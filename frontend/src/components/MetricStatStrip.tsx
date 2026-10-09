"use client";

import React from "react";
import {
  ShieldAlert,
  Server,
  Activity,
  Flame,
  Radio,
  TrendingDown,
  TrendingUp,
  Cpu,
  Zap,
} from "lucide-react";
import { RiskSummary } from "@/lib/types";

interface MetricStatStripProps {
  riskSummary: RiskSummary;
  compromisedCount: number;
  totalAssets: number;
}

export default function MetricStatStrip({
  riskSummary,
  compromisedCount,
  totalAssets,
}: MetricStatStripProps) {
  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return "text-status-critical bg-status-critical/10 border-status-critical/30";
    if (score >= 60) return "text-status-warning bg-status-warning/10 border-status-warning/30";
    if (score >= 35) return "text-status-warning/80 bg-status-warning/5 border-status-warning/20";
    return "text-status-healthy bg-status-healthy/10 border-status-healthy/30";
  };

  // Sparkline data generators
  const healthSparkline = [82, 85, 84, 88, 86, 89, 91, 90, 92, 89];
  const throughputSparkline = [2800, 3100, 3400, 3200, 3600, 3900, 3750, 4100, 3840];

  return (
    <section className="border-b border-border bg-surface/50 px-4 py-2 grid grid-cols-2 md:grid-cols-5 gap-3 shrink-0 select-none text-xs font-mono">
      {/* 1. Posture Risk Score */}
      <div className="p-2.5 rounded-lg bg-surface border border-border flex items-center justify-between shadow-soc-card">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-typography-muted font-bold">
            Posture Risk Score
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-extrabold text-typography-primary">
              {riskSummary.overall_score}
            </span>
            <span className="text-[10px] text-typography-muted">/ 100</span>
          </div>
          <div className="text-[10px] text-typography-muted flex items-center gap-1 mt-0.5">
            <TrendingDown className="w-3 h-3 text-status-healthy" />
            <span>-12.4% vs last baseline</span>
          </div>
        </div>
        <div
          className={`px-2 py-1 rounded border text-[11px] font-bold flex flex-col items-center justify-center ${getRiskScoreColor(
            riskSummary.overall_score
          )}`}
        >
          <Activity className="w-3.5 h-3.5 mb-0.5" />
          <span>{riskSummary.level || "HIGH"}</span>
        </div>
      </div>

      {/* 2. Total Monitored Assets */}
      <div className="p-2.5 rounded-lg bg-surface border border-border flex items-center justify-between shadow-soc-card">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-typography-muted font-bold">
            Monitored Assets
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-extrabold text-typography-primary">
              {totalAssets || riskSummary.total_hosts || 13}
            </span>
            <span className="text-[10px] text-cyber-blue font-semibold">100% ONLINE</span>
          </div>
          <div className="text-[10px] text-typography-muted flex items-center gap-1.5 mt-0.5">
            <span className="text-cyber-cyan">5 OT/ICS</span> •{" "}
            <span className="text-typography-primary">8 IT Enterprise</span>
          </div>
        </div>
        <div className="p-2 rounded-lg bg-cyber-blue/10 border border-cyber-blue/20 text-cyber-blue">
          <Server className="w-4 h-4" />
        </div>
      </div>

      {/* 3. Active Anomalies & Compromises */}
      <div
        className={`p-2.5 rounded-lg bg-surface border transition-all shadow-soc-card flex items-center justify-between ${
          compromisedCount > 0
            ? "border-status-critical/60 shadow-glow-crimson bg-status-critical/5"
            : "border-border"
        }`}
      >
        <div>
          <div className="text-[10px] uppercase tracking-wider text-typography-muted font-bold">
            Compromised Footholds
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className={`text-xl font-extrabold ${
                compromisedCount > 0 ? "text-status-critical animate-pulse" : "text-status-healthy"
              }`}
            >
              {compromisedCount}
            </span>
            <span className="text-[10px] text-typography-muted">
              / {riskSummary.total_hosts || 13} hosts
            </span>
          </div>
          <div className="text-[10px] text-typography-muted mt-0.5">
            {compromisedCount > 0 ? (
              <span className="text-status-critical font-bold">CRITICAL BREACH ACTIVE</span>
            ) : (
              <span className="text-status-healthy">Perimeter Secure</span>
            )}
          </div>
        </div>
        <div
          className={`p-2 rounded-lg border ${
            compromisedCount > 0
              ? "bg-status-critical/20 border-status-critical/40 text-status-critical"
              : "bg-status-healthy/10 border-status-healthy/20 text-status-healthy"
          }`}
        >
          <Flame className={`w-4 h-4 ${compromisedCount > 0 ? "animate-pulse" : ""}`} />
        </div>
      </div>

      {/* 4. System Health Index with Sparkline */}
      <div className="p-2.5 rounded-lg bg-surface border border-border flex items-center justify-between shadow-soc-card">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-typography-muted font-bold">
            System Health Index
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-extrabold text-status-healthy">
              {riskSummary.network_health_index || 89.2}%
            </span>
            <span className="text-[10px] text-typography-muted">OT Grid</span>
          </div>
          <div className="text-[10px] text-typography-muted mt-0.5">
            Purdue Level 0-3 Normal
          </div>
        </div>
        {/* Inline Mini Sparkline */}
        <div className="w-16 h-8 flex items-end gap-[3px] pt-1">
          {healthSparkline.map((val, idx) => {
            const heightPercent = Math.max(15, (val - 75) * 4);
            return (
              <div
                key={idx}
                className="w-1 bg-status-healthy/60 rounded-t hover:bg-status-healthy transition-all"
                style={{ height: `${heightPercent}%` }}
                title={`Health: ${val}%`}
              />
            );
          })}
        </div>
      </div>

      {/* 5. Network Throughput & Bus Telemetry */}
      <div className="p-2.5 rounded-lg bg-surface border border-border flex items-center justify-between shadow-soc-card">
        <div>
          <div className="text-[10px] uppercase tracking-wider text-typography-muted font-bold">
            OT Bus Throughput
          </div>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-extrabold text-cyber-cyan">
              {riskSummary.throughput_mbps || 3840}
            </span>
            <span className="text-[10px] text-typography-muted">Mbps</span>
          </div>
          <div className="text-[10px] text-typography-muted mt-0.5 flex items-center gap-1">
            <span className="text-status-healthy font-semibold">0.02%</span> drop rate
          </div>
        </div>
        {/* Inline Mini Sparkline */}
        <div className="w-16 h-8 flex items-end gap-[3px] pt-1">
          {throughputSparkline.map((val, idx) => {
            const heightPercent = Math.max(15, (val / 4200) * 100);
            return (
              <div
                key={idx}
                className="w-1 bg-cyber-cyan/50 rounded-t hover:bg-cyber-cyan transition-all"
                style={{ height: `${heightPercent}%` }}
                title={`Throughput: ${val} Mbps`}
              />
            );
          })}
        </div>
      </div>
    </section>
  );
}
