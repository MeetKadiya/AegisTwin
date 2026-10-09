"use client";

import React, { useState, useMemo } from "react";
import {
  Network,
  Search,
  Filter,
  Server,
  Globe,
  Database,
  Lock,
  Radio,
  Flame,
  Shield,
  ShieldAlert,
  Thermometer,
  Cpu,
  Zap,
  Crosshair,
  ExternalLink,
  ChevronDown,
} from "lucide-react";
import { TopologyNode } from "@/lib/types";

interface AssetTopologyViewProps {
  nodes: TopologyNode[];
  onSelectNode: (node: TopologyNode) => void;
  onNavigateToGraph: (nodeId?: string) => void;
}

export default function AssetTopologyView({
  nodes,
  onSelectNode,
  onNavigateToGraph,
}: AssetTopologyViewProps) {
  const [selectedTier, setSelectedTier] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");

  const tiers = ["ALL", "DMZ", "Web Tier", "App Tier", "DB Tier", "Active Directory", "OT/ICS Zone"];

  const filteredNodes = useMemo(() => {
    return nodes.filter((node) => {
      if (selectedTier !== "ALL" && node.tier !== selectedTier) return false;
      if (selectedStatus === "COMPROMISED" && !node.compromised) return false;
      if (selectedStatus === "OPERATIONAL" && node.compromised) return false;

      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const matchesLabel = node.label.toLowerCase().includes(query);
        const matchesIp = node.ip.toLowerCase().includes(query);
        const matchesHost = node.hostname?.toLowerCase().includes(query);
        const matchesType = node.type.toLowerCase().includes(query);
        const matchesCve = node.vulnerabilities?.some((v) =>
          v.cve.toLowerCase().includes(query)
        );
        if (!matchesLabel && !matchesIp && !matchesHost && !matchesType && !matchesCve)
          return false;
      }
      return true;
    });
  }, [nodes, selectedTier, selectedStatus, searchQuery]);

  const getNodeIcon = (type: string, tier: string) => {
    if (type === "Gateway" || type === "VPN") return <Globe className="w-3.5 h-3.5 text-purple-400" />;
    if (tier === "OT/ICS Zone" || type === "PLC Controller")
      return <Radio className="w-3.5 h-3.5 text-emerald-400" />;
    if (type === "Database" || type === "Key Management / Vault")
      return <Database className="w-3.5 h-3.5 text-amber-400" />;
    if (type === "Domain Controller") return <Lock className="w-3.5 h-3.5 text-rose-400" />;
    return <Server className="w-3.5 h-3.5 text-cyber-cyan" />;
  };

  return (
    <div className="flex flex-col h-full bg-canvas p-4 space-y-3 select-none font-mono text-xs overflow-hidden">
      {/* Top Filter Bar */}
      <div className="p-3 bg-surface border border-border rounded-xl flex flex-wrap items-center justify-between gap-3 shadow-soc-card shrink-0">
        <div className="flex items-center gap-3 flex-1 min-w-[240px]">
          <div className="p-2 rounded-lg bg-cyber-blue/10 border border-cyber-blue/30 text-cyber-blue">
            <Network className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-typography-primary">
              Enterprise Asset Inventory & Topology Matrix
            </h2>
            <p className="text-[10px] text-typography-muted">
              {filteredNodes.length} of {nodes.length} assets displayed • Purdue L0-L4 Hierarchy
            </p>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative w-72">
          <Search className="w-3.5 h-3.5 text-typography-muted absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search host, IP, tier, CVE..."
            className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-canvas border border-border text-xs text-typography-primary placeholder-typography-muted focus:outline-none focus:border-cyber-blue"
          />
        </div>
      </div>

      {/* Tier Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 shrink-0">
        <span className="text-[10px] uppercase font-bold text-typography-muted flex items-center gap-1">
          <Filter className="w-3 h-3" /> Tier:
        </span>
        {tiers.map((tier) => (
          <button
            key={tier}
            onClick={() => setSelectedTier(tier)}
            className={`px-2.5 py-1 rounded-md border text-[11px] font-mono transition-colors whitespace-nowrap ${
              selectedTier === tier
                ? "bg-cyber-blue/20 text-cyber-blue border-cyber-blue/50 font-bold"
                : "bg-surface text-typography-muted border-border hover:text-typography-primary hover:bg-surface-hover"
            }`}
          >
            {tier}
          </button>
        ))}

        <div className="h-4 w-[1px] bg-border mx-1" />

        <button
          onClick={() => setSelectedStatus(selectedStatus === "COMPROMISED" ? "ALL" : "COMPROMISED")}
          className={`px-2.5 py-1 rounded-md border text-[11px] font-mono transition-colors flex items-center gap-1.5 ${
            selectedStatus === "COMPROMISED"
              ? "bg-status-critical/20 text-status-critical border-status-critical/50 font-bold"
              : "bg-surface text-typography-muted border-border hover:text-status-critical"
          }`}
        >
          <Flame className="w-3 h-3" />
          Compromised Only
        </button>
      </div>

      {/* Asset Data Table */}
      <div className="flex-1 bg-surface border border-border rounded-xl overflow-hidden shadow-soc-card flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-surface-subtle text-typography-muted uppercase text-[10px] border-b border-border sticky top-0 z-10">
              <tr>
                <th className="p-3">Asset & Hostname</th>
                <th className="p-3">IP Address</th>
                <th className="p-3">Tier</th>
                <th className="p-3">Status</th>
                <th className="p-3">Criticality</th>
                <th className="p-3">OT Sensors (Temp/Volt)</th>
                <th className="p-3">Known CVEs</th>
                <th className="p-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60 bg-surface">
              {filteredNodes.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-8 text-center text-typography-muted">
                    No enterprise assets matched your search filter.
                  </td>
                </tr>
              ) : (
                filteredNodes.map((node) => {
                  const metrics = node.metrics || {
                    temperature: 42,
                    voltage: 230,
                    packetDropRate: 0.01,
                    cpuLoad: 35,
                  };

                  return (
                    <tr
                      key={node.id}
                      onClick={() => onSelectNode(node)}
                      className={`hover:bg-surface-hover cursor-pointer transition-colors ${
                        node.compromised ? "bg-status-critical/5" : ""
                      }`}
                    >
                      {/* Asset & Hostname */}
                      <td className="p-3">
                        <div className="flex items-center gap-2.5">
                          <div className="p-1.5 rounded bg-surface-subtle border border-border">
                            {getNodeIcon(node.type, node.tier)}
                          </div>
                          <div>
                            <div className="font-bold text-typography-primary">{node.label}</div>
                            <div className="text-[10px] text-typography-muted">{node.hostname || node.id}</div>
                          </div>
                        </div>
                      </td>

                      {/* IP Address */}
                      <td className="p-3 text-cyber-cyan font-semibold">{node.ip}</td>

                      {/* Tier */}
                      <td className="p-3">
                        <span className="px-2 py-0.5 rounded text-[10px] bg-surface-subtle border border-border text-typography-primary font-semibold">
                          {node.tier}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="p-3">
                        {node.compromised ? (
                          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-critical/15 border border-status-critical/40 text-status-critical text-[10px] font-bold shadow-glow-crimson animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-status-critical" />
                            <span>COMPROMISED</span>
                          </div>
                        ) : (
                          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-healthy/10 border border-status-healthy/30 text-status-healthy text-[10px]">
                            <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
                            <span>OPERATIONAL</span>
                          </div>
                        )}
                      </td>

                      {/* Criticality */}
                      <td className="p-3">
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                            node.criticality >= 8.5
                              ? "bg-status-critical/20 text-status-critical border border-status-critical/40"
                              : node.criticality >= 7.0
                              ? "bg-status-warning/20 text-status-warning border border-status-warning/40"
                              : "bg-surface-subtle text-typography-muted border border-border"
                          }`}
                        >
                          {node.criticality}/10
                        </span>
                      </td>

                      {/* OT Sensors */}
                      <td className="p-3 text-[11px]">
                        <div className="flex items-center gap-2">
                          <span className="text-amber-400 flex items-center gap-0.5">
                            <Thermometer className="w-3 h-3" />
                            {metrics.temperature ? `${metrics.temperature}°C` : "N/A"}
                          </span>
                          <span className="text-typography-muted">•</span>
                          <span className="text-cyber-cyan">{metrics.voltage ? `${metrics.voltage}V` : "N/A"}</span>
                        </div>
                      </td>

                      {/* Known CVEs */}
                      <td className="p-3">
                        {node.vulnerabilities && node.vulnerabilities.length > 0 ? (
                          <div className="flex items-center gap-1">
                            <span className="px-1.5 py-0.5 rounded bg-status-critical/20 text-status-critical border border-status-critical/30 font-bold text-[10px]">
                              {node.vulnerabilities[0].cve}
                            </span>
                            {node.vulnerabilities.length > 1 && (
                              <span className="text-[10px] text-typography-muted">
                                +{node.vulnerabilities.length - 1}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-[10px] text-status-healthy">CLEAN</span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="p-3 text-right">
                        <div className="inline-flex items-center gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onSelectNode(node);
                            }}
                            className="p-1 rounded hover:bg-surface-subtle text-typography-muted hover:text-cyber-blue transition-colors"
                            title="Inspect threat vector & blast radius"
                          >
                            <ShieldAlert className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onNavigateToGraph(node.id);
                            }}
                            className="p-1 rounded hover:bg-surface-subtle text-typography-muted hover:text-cyber-cyan transition-colors"
                            title="Locate in digital twin graph"
                          >
                            <Crosshair className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
