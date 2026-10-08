"use client";

import React from "react";
import {
  X,
  AlertTriangle,
  ShieldAlert,
  Server,
  Database,
  Lock,
  ArrowRight,
  Flame,
  CheckCircle,
  ExternalLink,
} from "lucide-react";

interface BlastRadiusModalProps {
  isOpen: boolean;
  onClose: () => void;
  node: any;
  blastData: any;
  onSimulateCompromise?: (nodeId: string) => void;
  onClearHighlight?: () => void;
}

export default function BlastRadiusModal({
  isOpen,
  onClose,
  node,
  blastData,
  onSimulateCompromise,
  onClearHighlight,
}: BlastRadiusModalProps) {
  if (!isOpen || !node) return null;

  const riskScore = blastData?.exfiltration_risk_score ?? 0;
  const reachableNodes = blastData?.reachable_nodes || [];
  const criticalAssets = blastData?.critical_assets_reached || [];
  const hopDistances = blastData?.hop_distances || {};

  const getRiskColor = (score: number) => {
    if (score >= 80) return "text-rose-500 border-rose-500/50 bg-rose-950/40";
    if (score >= 60) return "text-orange-500 border-orange-500/50 bg-orange-950/40";
    if (score >= 35) return "text-amber-400 border-amber-500/50 bg-amber-950/40";
    return "text-emerald-400 border-emerald-500/50 bg-emerald-950/40";
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-3xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl p-6 text-slate-100">
        {/* Header */}
        <div className="flex items-start justify-between pb-4 mb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-xl">
              <ShieldAlert className="w-6 h-6 text-amber-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                  {node.tier}
                </span>
                <span className="text-xs font-mono text-slate-400">
                  Asset Criticality: {node.criticality}/10
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mt-1">
                {node.label}
                <span className="text-sm font-normal text-slate-400 font-mono">
                  ({node.ip})
                </span>
              </h2>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-slate-400 transition-colors rounded-lg hover:text-slate-100 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* What Happens If Compromised Banner */}
        <div className="p-4 mb-6 border rounded-xl bg-amber-950/30 border-amber-500/30 flex items-center justify-between">
          <div>
            <div className="text-xs font-mono uppercase tracking-wider text-amber-400 font-bold mb-1">
              "What Happens If This Server Is Compromised?" Blast Simulation
            </div>
            <p className="text-sm text-slate-300">
              Downstream lateral propagation reveals reachable nodes, identity tokens, and exfiltration vectors.
            </p>
          </div>
          <div className={`px-4 py-2 rounded-xl border text-center font-mono ${getRiskColor(riskScore)}`}>
            <div className="text-2xl font-black">{riskScore}</div>
            <div className="text-[10px] tracking-wider uppercase font-semibold">Exfiltration Risk</div>
          </div>
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
            <div className="text-xs text-slate-400 font-mono">Downstream Reachable</div>
            <div className="text-2xl font-bold text-slate-100 mt-1">
              {blastData?.blast_radius_count || 0} / {blastData?.total_nodes || 12}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Hosts exposed to lateral pivot
            </div>
          </div>

          <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
            <div className="text-xs text-slate-400 font-mono">Crown Jewels at Risk</div>
            <div className="text-2xl font-bold text-rose-400 mt-1">
              {criticalAssets.length}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Assets with criticality ≥ 8.5
            </div>
          </div>

          <div className="p-4 bg-slate-800/60 border border-slate-700/60 rounded-xl">
            <div className="text-xs text-slate-400 font-mono">Downstream CVEs Exposed</div>
            <div className="text-2xl font-bold text-amber-400 mt-1">
              {blastData?.vulnerabilities_exposed || 0}
            </div>
            <div className="text-[11px] text-slate-400 mt-1">
              Unpatched exploits in reach
            </div>
          </div>
        </div>

        {/* Critical Crown Jewels Alert */}
        {criticalAssets.length > 0 && (
          <div className="mb-6 p-4 rounded-xl border border-rose-500/40 bg-rose-950/20">
            <div className="flex items-center gap-2 text-rose-400 font-bold text-sm mb-2">
              <AlertTriangle className="w-4 h-4" />
              Critical Infrastructure in Blast Path
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {criticalAssets.map((asset: any) => (
                <div
                  key={asset.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/80 border border-rose-800/30 text-xs"
                >
                  <div className="flex items-center gap-2">
                    {asset.tier === "Active Directory" ? (
                      <Lock className="w-4 h-4 text-rose-400" />
                    ) : (
                      <Database className="w-4 h-4 text-amber-400" />
                    )}
                    <div>
                      <div className="font-semibold text-slate-200">{asset.label}</div>
                      <div className="text-[10px] text-slate-400 font-mono">{asset.ip}</div>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-900/60 text-rose-300">
                    Crit {asset.criticality}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Downstream Assets Reachable Table */}
        <div className="mb-6">
          <h3 className="text-xs font-mono text-slate-400 uppercase tracking-wider mb-2">
            Reachable Assets Sequence (Breadth-First Traversal)
          </h3>
          <div className="border border-slate-800 rounded-xl overflow-hidden max-h-56 overflow-y-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-800/90 text-slate-300 uppercase text-[10px]">
                <tr>
                  <th className="p-2.5">Hops</th>
                  <th className="p-2.5">Asset Label</th>
                  <th className="p-2.5">IP / Tier</th>
                  <th className="p-2.5">Criticality</th>
                  <th className="p-2.5">Known CVEs</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 bg-slate-900/60">
                {reachableNodes.map((n: any) => {
                  const hops = hopDistances[n.id] ?? 0;
                  const isCurrent = n.id === node.id;
                  return (
                    <tr
                      key={n.id}
                      className={isCurrent ? "bg-amber-950/20 font-bold" : "hover:bg-slate-800/40"}
                    >
                      <td className="p-2.5 text-slate-400">
                        {isCurrent ? "Origin (0)" : `+${hops} hop`}
                      </td>
                      <td className="p-2.5 text-slate-200">{n.label}</td>
                      <td className="p-2.5 text-slate-400">
                        {n.ip} <span className="text-[10px] text-slate-500">({n.tier})</span>
                      </td>
                      <td className="p-2.5">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] ${
                            n.criticality >= 8.5
                              ? "bg-rose-950 text-rose-300 border border-rose-800"
                              : "bg-slate-800 text-slate-300"
                          }`}
                        >
                          {n.criticality}/10
                        </span>
                      </td>
                      <td className="p-2.5 text-slate-400">
                        {n.vulnerabilities && n.vulnerabilities.length > 0 ? (
                          <span className="text-rose-400">
                            {n.vulnerabilities.map((v: any) => v.cve).join(", ")}
                          </span>
                        ) : (
                          <span className="text-slate-600">None</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <button
            onClick={() => {
              onClearHighlight?.();
              onClose();
            }}
            className="px-4 py-2 rounded-xl text-xs font-mono text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            Clear Blast Highlights
          </button>
          <div className="flex gap-2">
            <button
              onClick={() => {
                onSimulateCompromise?.(node.id);
                onClose();
              }}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-rose-600 hover:bg-rose-500 text-white transition-colors shadow-lg shadow-rose-900/30"
            >
              <Flame className="w-4 h-4" />
              Set as Compromised Foothold
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
