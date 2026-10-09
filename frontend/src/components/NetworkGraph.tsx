"use client";

import React, { useMemo, memo, useCallback, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  NodeProps,
  Edge,
  Node,
} from "reactflow";
import "reactflow/dist/style.css";
import {
  Server,
  Shield,
  ShieldAlert,
  Database,
  Lock,
  Globe,
  Flame,
  CheckCircle2,
  Terminal,
  Activity,
  Cpu,
  Thermometer,
  Zap,
  Info,
  Radio,
} from "lucide-react";
import { TopologyNode } from "@/lib/types";

// Tier coordinate layout mapping for industrial digital twin
export const TIER_POSITIONS: Record<string, { x: number; y: number }> = {
  "gw-external": { x: 40, y: 220 },
  "web-dmz-01": { x: 280, y: 100 },
  "vpn-gateway": { x: 280, y: 320 },
  "web-app-01": { x: 520, y: 60 },
  "api-gateway": { x: 520, y: 220 },
  "app-srv-01": { x: 760, y: 60 },
  "ci-cd-runner": { x: 760, y: 240 },
  "admin-workstation-01": { x: 760, y: 440 },
  "plc-rtu-substation": { x: 1010, y: 40 },
  "scada-historian-01": { x: 1010, y: 190 },
  "db-cluster-01": { x: 1010, y: 340 },
  "corp-dc-01": { x: 1260, y: 140 },
  "db-cluster-02": { x: 1260, y: 320 },
};

const TIER_X_OFFSETS: Record<string, number> = {
  "DMZ": 280,
  "Web Tier": 520,
  "App Tier": 760,
  "OT/ICS Zone": 1010,
  "DB Tier": 1010,
  "Active Directory": 1260,
};

export const TIER_BADGES: Record<string, { bg: string; text: string; label: string }> = {
  "DMZ": { bg: "bg-purple-950/50 border-purple-500/40", text: "text-purple-300", label: "DMZ" },
  "Web Tier": { bg: "bg-blue-950/50 border-blue-500/40", text: "text-blue-300", label: "Web Tier" },
  "App Tier": { bg: "bg-cyan-950/50 border-cyan-500/40", text: "text-cyan-300", label: "App Tier" },
  "OT/ICS Zone": { bg: "bg-emerald-950/50 border-emerald-500/40", text: "text-emerald-300", label: "OT / Purdue L1" },
  "DB Tier": { bg: "bg-amber-950/50 border-amber-500/40", text: "text-amber-300", label: "DB Storage" },
  "Active Directory": { bg: "bg-rose-950/50 border-rose-500/40", text: "text-rose-300", label: "Identity (Tier 0)" },
};

// High-performance memoized host node component with OT telemetry hover cards
const CustomHostNode = memo(function CustomHostNode({ data }: NodeProps) {
  const [showHover, setShowHover] = useState(false);
  const isCompromised = data.compromised;
  const isBlastRadius = data.isBlastRadius;
  const isIsolated = data.isolated;
  const tierStyle = TIER_BADGES[data.tier] || {
    bg: "bg-surface-subtle border-border",
    text: "text-typography-muted",
    label: data.tier || "Host",
  };

  const getNodeIcon = () => {
    if (data.type === "Gateway" || data.type === "VPN")
      return <Globe className="w-4 h-4 text-purple-400" />;
    if (data.type === "PLC Controller" || data.tier === "OT/ICS Zone")
      return <Radio className="w-4 h-4 text-emerald-400" />;
    if (data.type === "Database" || data.type === "Key Management / Vault")
      return <Database className="w-4 h-4 text-amber-400" />;
    if (data.type === "Domain Controller")
      return <Lock className="w-4 h-4 text-rose-400" />;
    return <Server className="w-4 h-4 text-cyber-cyan" />;
  };

  let borderStyle = "border-border bg-surface hover:border-cyber-blue/60";
  let statusBadge = (
    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-healthy/10 border border-status-healthy/30 text-[10px] text-status-healthy font-mono">
      <span className="w-1.5 h-1.5 rounded-full bg-status-healthy" />
      <span>OPERATIONAL</span>
    </div>
  );

  if (isCompromised) {
    borderStyle = "border-status-critical bg-status-critical/10 shadow-glow-crimson node-compromised";
    statusBadge = (
      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-critical/20 border border-status-critical/50 text-[10px] text-status-critical font-mono font-bold">
        <span className="w-1.5 h-1.5 rounded-full bg-status-critical animate-ping" />
        <span>COMPROMISED {data.compromise_step ? `(Step ${data.compromise_step})` : ""}</span>
      </div>
    );
  } else if (isBlastRadius) {
    borderStyle = "border-status-warning bg-status-warning/10 shadow-glow-amber node-blast";
    statusBadge = (
      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-warning/20 border border-status-warning/40 text-[10px] text-status-warning font-mono font-bold">
        <span className="w-1.5 h-1.5 rounded-full bg-status-warning" />
        <span>IN BLAST PATH (+{data.blastHops || 1} HOP)</span>
      </div>
    );
  } else if (isIsolated) {
    borderStyle = "border-gray-700 bg-surface-subtle/80 opacity-50";
    statusBadge = (
      <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-gray-800 border border-gray-700 text-[10px] text-gray-400 font-mono">
        <Shield className="w-3 h-3 text-gray-400" />
        <span>QUARANTINED</span>
      </div>
    );
  }

  const handleClick = useCallback(() => {
    data.onSelectNode?.(data);
  }, [data]);

  const metrics = data.metrics || {
    temperature: 42.1,
    voltage: 230.0,
    packetDropRate: 0.02,
    cpuLoad: 45,
    memoryUsage: 55,
  };

  return (
    <div
      onClick={handleClick}
      onMouseEnter={() => setShowHover(true)}
      onMouseLeave={() => setShowHover(false)}
      className={`relative min-w-[220px] max-w-[250px] rounded-xl border p-3 cursor-pointer select-none transition-all duration-150 shadow-soc-card ${borderStyle}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="w-2.5 h-2.5 !bg-cyber-blue border border-canvas"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-2.5 h-2.5 !bg-cyber-blue border border-canvas"
      />

      {/* Top Header Row */}
      <div className="flex items-center justify-between mb-2">
        <span
          className={`text-[9px] px-1.5 py-0.5 rounded border font-mono font-semibold uppercase tracking-wider ${tierStyle.bg} ${tierStyle.text}`}
        >
          {tierStyle.label}
        </span>
        <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-surface-subtle border border-border text-typography-muted">
          Crit: {data.criticality || 5}/10
        </span>
      </div>

      {/* Asset Identity */}
      <div className="flex items-start gap-2.5 mb-2.5">
        <div className="p-2 rounded-lg bg-surface-subtle border border-border mt-0.5 shrink-0">
          {getNodeIcon()}
        </div>
        <div className="overflow-hidden">
          <div className="font-bold text-xs text-typography-primary truncate" title={data.label}>
            {data.label}
          </div>
          <div className="text-[10px] text-cyber-cyan font-mono truncate">{data.ip}</div>
          <div className="text-[9px] text-typography-muted font-mono truncate">{data.os || "Linux Kernel"}</div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="pt-2 border-t border-border flex items-center justify-between">
        {statusBadge}
        {data.vulnerabilities && data.vulnerabilities.length > 0 && (
          <span className="text-[9px] bg-status-critical/15 text-status-critical border border-status-critical/30 font-mono px-1.5 py-0.5 rounded font-semibold">
            {data.vulnerabilities.length} CVE{data.vulnerabilities.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Micro Telemetry Readout */}
      <div className="mt-2 pt-1.5 border-t border-border/60 grid grid-cols-2 gap-1 text-[9px] font-mono text-typography-muted">
        <div className="flex items-center gap-1">
          <Thermometer className="w-2.5 h-2.5 text-amber-400" />
          <span>{metrics.temperature ? `${metrics.temperature}°C` : "38.2°C"}</span>
        </div>
        <div className="flex items-center gap-1 justify-end">
          <Cpu className="w-2.5 h-2.5 text-cyber-blue" />
          <span>CPU: {metrics.cpuLoad ? `${metrics.cpuLoad}%` : "42%"}</span>
        </div>
      </div>

      {/* Node Hover Card (Telemetry Overlay) */}
      {showHover && (
        <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-3 rounded-xl glass-dropdown z-50 text-[11px] font-mono shadow-2xl pointer-events-none animate-in fade-in zoom-in-95 duration-150">
          <div className="flex items-center justify-between pb-1.5 border-b border-border text-typography-primary font-bold">
            <span className="truncate">{data.label}</span>
            <span className="text-cyber-cyan">{data.ip}</span>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2 text-[10px]">
            <div>
              <span className="text-typography-muted">Temperature:</span>
              <div className="font-semibold text-amber-400">{metrics.temperature || 42}°C</div>
            </div>
            <div>
              <span className="text-typography-muted">Bus Voltage:</span>
              <div className="font-semibold text-typography-primary">{metrics.voltage || 230} V</div>
            </div>
            <div>
              <span className="text-typography-muted">Packet Drop:</span>
              <div className="font-semibold text-status-healthy">{metrics.packetDropRate || 0.01}%</div>
            </div>
            <div>
              <span className="text-typography-muted">CPU / RAM:</span>
              <div className="font-semibold text-cyber-blue">{metrics.cpuLoad || 40}% / {metrics.memoryUsage || 55}%</div>
            </div>
          </div>

          {data.services && data.services.length > 0 && (
            <div className="mt-2 pt-1.5 border-t border-border">
              <span className="text-typography-muted text-[10px]">Active Port Listeners:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {data.services.slice(0, 3).map((srv: string, i: number) => (
                  <span key={i} className="text-[9px] px-1 rounded bg-canvas border border-border text-typography-primary">
                    {srv}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="mt-2 pt-1 border-t border-border/60 text-[9px] text-cyber-blue text-center">
            Click to inspect attack vector & blast radius
          </div>
        </div>
      )}
    </div>
  );
});

interface NetworkGraphProps {
  topology: {
    nodes: any[];
    edges: any[];
  };
  onSelectNode: (node: TopologyNode) => void;
  blastRadiusData?: {
    reachable_nodes: any[];
    hop_distances: Record<string, number>;
    origin_node?: any;
  } | null;
}

export default function NetworkGraph({
  topology,
  onSelectNode,
  blastRadiusData,
}: NetworkGraphProps) {
  const nodeTypes = useMemo(() => ({ hostNode: CustomHostNode }), []);

  // Compute blast radius lookup map
  const blastLookup = useMemo(() => {
    const map = new Map<string, number>();
    if (blastRadiusData?.hop_distances) {
      Object.entries(blastRadiusData.hop_distances).forEach(([nid, hops]) => {
        map.set(nid, hops);
      });
    }
    return map;
  }, [blastRadiusData]);

  // Transform raw nodes to deduplicated React Flow nodes with auto-grid fallback
  const flowNodes: Node[] = useMemo(() => {
    const seen = new Set<string>();
    const validNodes = (topology.nodes || []).filter(
      (node) => Boolean(node?.id && node?.type !== "Vulnerability")
    );

    return validNodes
      .filter((node) => {
        if (seen.has(node.id)) return false;
        seen.add(node.id);
        return true;
      })
      .map((node, idx) => {
        let pos = TIER_POSITIONS[node.id];
        if (!pos) {
          const xBase = TIER_X_OFFSETS[node.tier] || 500;
          const yBase = 60 + (idx % 6) * 140;
          pos = { x: xBase, y: yBase };
        }
        const hops = blastLookup.get(node.id);
        const isOrigin = blastRadiusData?.origin_node?.id === node.id;

        return {
          id: node.id,
          type: "hostNode",
          position: pos,
          data: {
            ...node,
            isBlastRadius: !!hops && !isOrigin,
            blastHops: hops,
            onSelectNode,
          },
        };
      });
  }, [topology.nodes, blastLookup, blastRadiusData, onSelectNode]);

  // Deduplicate and style edges efficiently
  const flowEdges: Edge[] = useMemo(() => {
    const compNodeIds = new Set(
      (topology.nodes || []).filter((n) => n.compromised).map((n) => n.id)
    );

    const seenEdges = new Set<string>();

    return (topology.edges || [])
      .filter((edge) => {
        const key = `${edge.source}->${edge.target}`;
        if (seenEdges.has(key)) return false;
        seenEdges.add(key);
        return true;
      })
      .map((edge) => {
        const isTraversed =
          compNodeIds.has(edge.source) && compNodeIds.has(edge.target);
        const isBlocked = edge.status === "blocked";

        let strokeColor = "#222D3F";
        let animated = false;
        let strokeWidth = 2;

        if (isBlocked) {
          strokeColor = "#6B7280";
        } else if (isTraversed) {
          strokeColor = "#EF4444";
          animated = true;
          strokeWidth = 3;
        }

        return {
          id: edge.id || `e-${edge.source}-${edge.target}`,
          source: edge.source,
          target: edge.target,
          type: "smoothstep",
          animated,
          style: {
            stroke: strokeColor,
            strokeWidth,
            strokeDasharray: isBlocked ? "5,5" : undefined,
          },
          label: isBlocked ? "BLOCKED" : undefined,
          labelStyle: { fill: "#EF4444", fontSize: 10, fontFamily: "JetBrains Mono, monospace", fontWeight: 700 },
        };
      });
  }, [topology.edges, topology.nodes]);

  return (
    <div className="w-full h-full relative rounded-xl overflow-hidden border border-border bg-canvas">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.12 }}
        onlyRenderVisibleElements={true}
        attributionPosition="bottom-right"
        minZoom={0.2}
        maxZoom={1.8}
      >
        <Background color="#1A2130" gap={24} size={1} />
        <Controls className="!bg-surface !border-border !text-typography-muted fill-typography-muted rounded-lg shadow-soc-card" />
        <MiniMap
          nodeColor={(n) => {
            if (n.data?.compromised) return "#EF4444";
            if (n.data?.isBlastRadius) return "#F59E0B";
            if (n.data?.tier === "OT/ICS Zone") return "#10B981";
            return "#3B82F6";
          }}
          maskColor="rgba(10, 13, 20, 0.85)"
          className="!bg-surface !border !border-border rounded-lg"
        />
      </ReactFlow>

      {/* Tactical Attack Path Legend Overlay */}
      <div className="absolute top-3 left-3 bg-surface/90 border border-border p-3 rounded-xl z-10 text-xs font-mono space-y-1.5 shadow-soc-card backdrop-blur-md">
        <div className="text-[10px] font-bold text-typography-muted uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-cyber-blue" />
          Digital Twin State Legend
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-status-healthy shadow-glow-emerald" />
          <span className="text-typography-primary">Operational Clean Asset</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-status-critical shadow-glow-crimson animate-pulse" />
          <span className="text-status-critical font-bold">Compromised Foothold</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-status-warning shadow-glow-amber" />
          <span className="text-status-warning">Blast Path Reachable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-status-critical" />
          <span className="text-typography-muted">Lateral Movement Pivot</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 border-t border-dashed border-gray-500" />
          <span className="text-gray-400">Zero Trust Blocked Edge</span>
        </div>
      </div>
    </div>
  );
}
