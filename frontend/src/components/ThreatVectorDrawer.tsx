"use client";

import React from "react";
import {
  X,
  AlertTriangle,
  ShieldAlert,
  Server,
  Database,
  Lock,
  Flame,
  ArrowRight,
  ShieldCheck,
  Zap,
  Radio,
  Thermometer,
  Cpu,
  Layers,
  ChevronRight,
  ExternalLink,
  Activity,
} from "lucide-react";
import { TopologyNode } from "@/lib/types";

interface ThreatVectorDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  node: TopologyNode | null;
  blastData: any;
  onSimulateCompromise?: (nodeId: string) => void;
  onApplyQuickFix?: (nodeId: string, actionType: string) => void;
  onClearHighlight?: () => void;
  loading?: boolean;
}

export default function ThreatVectorDrawer({
  isOpen,
  onClose,
  node,
  blastData,
  onSimulateCompromise,
  onApplyQuickFix,
  onClearHighlight,
  loading,
}: ThreatVectorDrawerProps) {
  if (!isOpen || !node) return null;

  const riskScore = blastData?.exfiltration_risk_score ?? (node.criticality * 9.2);
  const reachableNodes = blastData?.reachable_nodes || [];
  const criticalAssets = blastData?.critical_assets_reached || [];
  const hopDistances = blastData?.hop_distances || {};
  const metrics = node.metrics || {
    temperature: 42.5,
    voltage: 230.1,
    packetDropRate: 0.02,
    cpuLoad: 48,
    memoryUsage: 62,
    latencyMs: 3.1,
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return "text-status-critical bg-status-critical/15 border-status-critical/40";
    if (score >= 60) return "text-status-warning bg-status-warning/15 border-status-warning/40";
    return "text-status-healthy bg-status-healthy/15 border-status-healthy/40";
  };

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-xl bg-surface border-l border-border shadow-2xl flex flex-col backdrop-blur-xl animate-in slide-in-from-right duration-200 select-none">
      {/* Header */}
      <div className="h-16 border-b border-border px-6 flex items-center justify-between bg-surface-subtle/60 shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyber-blue/10 border border-cyber-blue/20 text-cyber-blue shadow-glow-blue">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface border border-border text-cyber-cyan font-bold uppercase">
                {node.tier}
              </span>
              <span className="text-[10px] font-mono text-typography-muted">
                Crit: {node.criticality}/10
              </span>
            </div>
            <h2 className="text-sm font-bold text-typography-primary flex items-center gap-2 mt-0.5 truncate">
              {node.label}
              <span className="text-xs font-mono font-normal text-typography-muted">
                ({node.ip})
              </span>
            </h2>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-2 text-typography-muted hover:text-typography-primary hover:bg-surface-hover rounded-lg transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Body Content */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 font-mono text-xs">
        {/* Threat Status Banner */}
        <div
          className={`p-4 rounded-xl border flex items-center justify-between ${
            node.compromised
              ? "bg-status-critical/10 border-status-critical/40 shadow-glow-crimson"
              : "bg-surface-subtle border-border"
          }`}
        >
          <div>
            <div className="text-[10px] uppercase tracking-wider font-bold text-typography-muted">
              Vector Threat Status
            </div>
            <div className="text-sm font-bold text-typography-primary mt-0.5 flex items-center gap-2">
              {node.compromised ? (
                <>
                  <Flame className="w-4 h-4 text-status-critical animate-pulse" />
                  <span className="text-status-critical">COMPROMISED HOST FOOTHOLD</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 text-status-healthy" />
                  <span className="text-status-healthy">OPERATIONAL (ACTIVE DEFENSE)</span>
                </>
              )}
            </div>
            <div className="text-[11px] text-typography-muted mt-1">
              {node.compromised
                ? `Foothold established via attack path. Lateral movement active.`
                : `Monitored by AegisTwin digital twin. Zero trust mesh active.`}
            </div>
          </div>

          <div className={`px-3 py-2 rounded-xl border text-center ${getRiskScoreColor(riskScore)}`}>
            <div className="text-xl font-extrabold">{Math.round(riskScore)}</div>
            <div className="text-[9px] uppercase tracking-wider font-bold">Exfil Risk</div>
          </div>
        </div>

        {/* Live OT/ICS Telemetry Grid */}
        <div>
          <div className="text-[10px] uppercase tracking-wider font-bold text-typography-muted mb-2 flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyber-blue" />
            Live Industrial Telemetry (OT Bus & Sensor Readouts)
          </div>
          <div className="grid grid-cols-3 gap-2.5">
            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">Core Temp:</span>
              <div className="text-sm font-bold text-amber-400 mt-0.5 flex items-center gap-1">
                <Thermometer className="w-3.5 h-3.5" />
                {metrics.temperature ? `${metrics.temperature}°C` : "41.5°C"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">Bus Voltage:</span>
              <div className="text-sm font-bold text-typography-primary mt-0.5 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-cyber-cyan" />
                {metrics.voltage ? `${metrics.voltage} V` : "230.1 V"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">Packet Drop:</span>
              <div className="text-sm font-bold text-status-healthy mt-0.5">
                {metrics.packetDropRate ? `${metrics.packetDropRate}%` : "0.01%"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">CPU Load:</span>
              <div className="text-sm font-bold text-cyber-blue mt-0.5 flex items-center gap-1">
                <Cpu className="w-3.5 h-3.5" />
                {metrics.cpuLoad ? `${metrics.cpuLoad}%` : "42%"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">RAM Utilization:</span>
              <div className="text-sm font-bold text-typography-primary mt-0.5">
                {metrics.memoryUsage ? `${metrics.memoryUsage}%` : "58%"}
              </div>
            </div>

            <div className="p-3 rounded-lg bg-surface-subtle border border-border">
              <span className="text-[10px] text-typography-muted">Mesh Latency:</span>
              <div className="text-sm font-bold text-status-healthy mt-0.5">
                {metrics.latencyMs ? `${metrics.latencyMs} ms` : "2.4 ms"}
              </div>
            </div>
          </div>
        </div>

        {/* Known Vulnerabilities & MITRE ATT&CK */}
        <div>
          <div className="text-[10px] uppercase tracking-wider font-bold text-typography-muted mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-status-warning" />
              Discovered Vulnerabilities & CVE Vectors
            </span>
            <span className="text-typography-muted">
              {node.vulnerabilities?.length || 0} CVEs Detected
            </span>
          </div>

          {node.vulnerabilities && node.vulnerabilities.length > 0 ? (
            <div className="space-y-2">
              {node.vulnerabilities.map((vuln, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl border border-status-critical/30 bg-status-critical/5 hover:border-status-critical/50 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-status-critical font-bold text-xs">{vuln.cve}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface border border-border text-cyber-blue">
                        MITRE {vuln.mitre}
                      </span>
                      <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-status-critical/20 text-status-critical border border-status-critical/40">
                        CVSS {vuln.cvss}
                      </span>
                    </div>
                  </div>
                  <div className="text-xs font-semibold text-typography-primary mt-1">
                    {vuln.title}
                  </div>
                  {vuln.description && (
                    <div className="text-[11px] text-typography-muted mt-1 leading-relaxed">
                      {vuln.description}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 rounded-xl border border-border bg-surface-subtle text-typography-muted text-center">
              No unpatched high-severity CVEs identified on this node.
            </div>
          )}
        </div>

        {/* Blast Radius & Downstream Propagation */}
        <div>
          <div className="text-[10px] uppercase tracking-wider font-bold text-typography-muted mb-2 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5 text-cyber-cyan" />
              Downstream Lateral Propagation (Blast Radius)
            </span>
            <span className="text-cyber-cyan">
              {blastData?.blast_radius_count || reachableNodes.length || 0} Nodes Exposed
            </span>
          </div>

          {criticalAssets.length > 0 && (
            <div className="p-3 mb-3 rounded-xl border border-status-critical/40 bg-status-critical/10">
              <div className="text-[10px] text-status-critical font-bold uppercase tracking-wider mb-1 flex items-center gap-1">
                <AlertTriangle className="w-3.5 h-3.5" />
                Critical Crown Jewels at Immediate Risk
              </div>
              <div className="space-y-1 mt-1.5">
                {criticalAssets.map((asset: any) => (
                  <div
                    key={asset.id}
                    className="flex items-center justify-between p-2 rounded bg-surface border border-border text-[11px]"
                  >
                    <div className="flex items-center gap-2">
                      {asset.tier === "Active Directory" ? (
                        <Lock className="w-3.5 h-3.5 text-status-critical" />
                      ) : (
                        <Database className="w-3.5 h-3.5 text-amber-400" />
                      )}
                      <span className="text-typography-primary font-semibold">{asset.label}</span>
                    </div>
                    <span className="text-[10px] text-status-critical font-bold">
                      Criticality {asset.criticality}/10
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {reachableNodes.length > 0 ? (
            <div className="border border-border rounded-xl overflow-hidden max-h-48 overflow-y-auto">
              <table className="w-full text-left text-[11px] font-mono">
                <thead className="bg-surface-subtle text-typography-muted uppercase text-[9px]">
                  <tr>
                    <th className="p-2">Hops</th>
                    <th className="p-2">Target Asset</th>
                    <th className="p-2">IP / Tier</th>
                    <th className="p-2">Risk</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border bg-surface">
                  {reachableNodes.map((n: any) => {
                    const hops = hopDistances[n.id] ?? 1;
                    const isOrigin = n.id === node.id;
                    return (
                      <tr key={n.id} className={isOrigin ? "bg-amber-950/20" : "hover:bg-surface-hover"}>
                        <td className="p-2 text-typography-muted">
                          {isOrigin ? "Origin" : `+${hops} hop`}
                        </td>
                        <td className="p-2 text-typography-primary font-medium">{n.label}</td>
                        <td className="p-2 text-typography-muted">
                          {n.ip} <span className="text-[10px] text-cyber-blue">({n.tier})</span>
                        </td>
                        <td className="p-2 font-bold text-amber-400">
                          {n.criticality >= 8.5 ? "CRITICAL" : "STANDARD"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-3 rounded-xl border border-border bg-surface-subtle text-typography-muted text-center">
              Click "Simulate Blast Radius" on node to compute full breadth-first traversal.
            </div>
          )}
        </div>
      </div>

      {/* Drawer Action Footer */}
      <div className="p-4 border-t border-border bg-surface-subtle/80 flex items-center justify-between gap-3 shrink-0">
        <button
          onClick={() => {
            onClearHighlight?.();
            onClose();
          }}
          className="px-3 py-2 rounded-lg text-xs font-mono text-typography-muted hover:text-typography-primary hover:bg-surface-hover border border-border transition-colors"
        >
          Clear Highlights
        </button>

        <div className="flex items-center gap-2">
          {node.vulnerabilities && node.vulnerabilities.length > 0 && onApplyQuickFix && (
            <button
              onClick={() => onApplyQuickFix(node.id, "patch_cve")}
              disabled={loading}
              className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-mono font-bold bg-cyber-blue hover:bg-blue-500 active:scale-[0.98] text-white transition-all shadow-glow-blue disabled:opacity-50"
            >
              <Zap className="w-3.5 h-3.5" />
              Apply Hotfix
            </button>
          )}

          <button
            onClick={() => {
              onSimulateCompromise?.(node.id);
            }}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-mono font-bold bg-status-critical hover:bg-red-500 active:scale-[0.98] text-white transition-all shadow-glow-crimson disabled:opacity-50 hover:scale-[1.02]"
          >
            <Flame className="w-3.5 h-3.5" />
            Simulate Compromise
          </button>
        </div>
      </div>
    </div>
  );
}
