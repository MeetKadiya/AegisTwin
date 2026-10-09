"use client";

import React, { useMemo, memo, useCallback } from "react";
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
} from "lucide-react";

// Tier coordinate layout mapping
export const TIER_POSITIONS: Record<string, { x: number; y: number }> = {
  "gw-external": { x: 60, y: 220 },
  "web-dmz-01": { x: 300, y: 140 },
  "vpn-gateway": { x: 300, y: 320 },
  "web-app-01": { x: 540, y: 100 },
  "api-gateway": { x: 540, y: 260 },
  "app-srv-01": { x: 780, y: 80 },
  "app-srv-02": { x: 780, y: 220 },
  "ci-cd-runner": { x: 780, y: 360 },
  "admin-workstation-01": { x: 780, y: 500 },
  "db-cluster-01": { x: 1040, y: 120 },
  "corp-dc-01": { x: 1040, y: 360 },
  "db-cluster-02": { x: 1260, y: 260 },
};

const TIER_X_OFFSETS: Record<string, number> = {
  "DMZ": 200,
  "Web Tier": 450,
  "App Tier": 700,
  "DB Tier": 950,
  "Active Directory": 1100,
};

export const TIER_BADGES: Record<string, { bg: string; text: string; label: string }> = {
  "DMZ": { bg: "bg-purple-950 border-purple-500/50", text: "text-purple-300", label: "DMZ" },
  "Web Tier": { bg: "bg-blue-950 border-blue-500/50", text: "text-blue-300", label: "Web Tier" },
  "App Tier": { bg: "bg-cyan-950 border-cyan-500/50", text: "text-cyan-300", label: "App Tier" },
  "DB Tier": { bg: "bg-amber-950 border-amber-500/50", text: "text-amber-300", label: "Database" },
  "Active Directory": { bg: "bg-rose-950 border-rose-500/50", text: "text-rose-300", label: "Identity / AD" },
};

// High-performance memoized host node component
const CustomHostNode = memo(function CustomHostNode({ data }: NodeProps) {
  const isCompromised = data.compromised;
  const isBlastRadius = data.isBlastRadius;
  const isIsolated = data.isolated;
  const tierStyle = TIER_BADGES[data.tier] || { bg: "bg-slate-850 border-slate-700", text: "text-slate-300", label: data.tier || "Host" };

  const getNodeIcon = () => {
    if (data.type === "Gateway" || data.type === "VPN") return <Globe className="w-4 h-4 text-purple-400" />;
    if (data.type === "Database" || data.type === "Key Management") return <Database className="w-4 h-4 text-amber-400" />;
    if (data.type === "Domain Controller") return <Lock className="w-4 h-4 text-rose-400" />;
    return <Server className="w-4 h-4 text-cyan-400" />;
  };

  let borderStyle = "border-slate-800 bg-slate-900";
  let statusBadge = (
    <div className="flex items-center gap-1 text-[11px] text-emerald-400 font-mono">
      <CheckCircle2 className="w-3 h-3 text-emerald-400" />
      <span>CLEAN</span>
    </div>
  );

  if (isCompromised) {
    borderStyle = "border-rose-500 bg-rose-950/90 shadow-md shadow-rose-950/60";
    statusBadge = (
      <div className="flex items-center gap-1 text-[11px] text-rose-400 font-mono font-bold">
        <Flame className="w-3.5 h-3.5 text-rose-500 animate-pulse" />
        <span>COMPROMISED {data.compromise_step ? `(Step ${data.compromise_step})` : ""}</span>
      </div>
    );
  } else if (isBlastRadius) {
    borderStyle = "border-amber-400 bg-amber-950/80 shadow-md shadow-amber-950/60";
    statusBadge = (
      <div className="flex items-center gap-1 text-[11px] text-amber-300 font-mono font-bold">
        <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
        <span>BLAST RADIUS (Hop +{data.blastHops || 1})</span>
      </div>
    );
  } else if (isIsolated) {
    borderStyle = "border-gray-600 bg-gray-900/90 opacity-60";
    statusBadge = (
      <div className="flex items-center gap-1 text-[11px] text-gray-400 font-mono">
        <Shield className="w-3 h-3 text-gray-400" />
        <span>ISOLATED</span>
      </div>
    );
  }

  const handleClick = useCallback(() => {
    data.onSelectNode?.(data);
  }, [data]);

  return (
    <div
      onClick={handleClick}
      className={`relative min-w-[210px] max-w-[240px] rounded-lg border p-3 cursor-pointer select-none ${borderStyle}`}
    >
      <Handle type="target" position={Position.Left} className="w-2.5 h-2.5 !bg-slate-400 border-none" />
      <Handle type="source" position={Position.Right} className="w-2.5 h-2.5 !bg-slate-400 border-none" />

      {/* Top Header */}
      <div className="flex items-center justify-between mb-2">
        <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono font-semibold ${tierStyle.bg} ${tierStyle.text}`}>
          {tierStyle.label}
        </span>
        <span className="text-[10px] font-mono px-1 rounded bg-slate-800 text-slate-300">
          Crit: {data.criticality || 5}/10
        </span>
      </div>

      {/* Asset Name & Icon */}
      <div className="flex items-start gap-2 mb-2">
        <div className="p-1.5 rounded bg-slate-800 border border-slate-700 mt-0.5">
          {getNodeIcon()}
        </div>
        <div className="overflow-hidden">
          <div className="font-semibold text-xs text-slate-100 truncate" title={data.label}>
            {data.label}
          </div>
          <div className="text-[11px] text-slate-400 font-mono truncate">
            {data.ip}
          </div>
        </div>
      </div>

      {/* Status Bar */}
      <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
        {statusBadge}
        {data.vulnerabilities && data.vulnerabilities.length > 0 && (
          <span className="text-[10px] bg-red-950 text-rose-300 border border-rose-800 font-mono px-1.5 py-0.5 rounded">
            {data.vulnerabilities.length} CVE{data.vulnerabilities.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {/* Quick Action Simulator Hint */}
      <div className="mt-2 pt-1 border-t border-slate-800/80 text-[9px] text-slate-400 text-center font-mono hover:text-accent-blue">
        Click to Simulate Blast Radius
      </div>
    </div>
  );
});

interface NetworkGraphProps {
  topology: {
    nodes: any[];
    edges: any[];
  };
  onSelectNode: (node: any) => void;
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
          const yBase = 80 + (idx % 5) * 130;
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

        let strokeColor = "#334155";
        let animated = false;
        let strokeWidth = 2;

        if (isBlocked) {
          strokeColor = "#64748b";
        } else if (isTraversed) {
          strokeColor = "#f43f5e";
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
          labelStyle: { fill: "#f87171", fontSize: 10, fontFamily: "monospace" },
        };
      });
  }, [topology.edges, topology.nodes]);

  return (
    <div className="w-full h-full relative rounded-xl overflow-hidden border border-slate-800 bg-[#070b13]">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        onlyRenderVisibleElements={true}
        attributionPosition="bottom-right"
        minZoom={0.25}
        maxZoom={1.75}
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="!bg-slate-900 !border-slate-700 !text-slate-200 fill-slate-200 rounded-lg shadow-xl" />
        <MiniMap
          nodeColor={(n) => {
            if (n.data?.compromised) return "#f43f5e";
            if (n.data?.isBlastRadius) return "#f59e0b";
            return "#3b82f6";
          }}
          maskColor="rgba(7, 11, 19, 0.7)"
          className="!bg-slate-900 !border !border-slate-800 rounded-lg"
        />
      </ReactFlow>

      {/* Legend Overlay */}
      <div className="absolute top-4 left-4 bg-slate-900/95 border border-slate-800 p-3 rounded-lg z-10 text-xs font-mono space-y-1.5 shadow-xl">
        <div className="text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
          <Terminal className="w-3.5 h-3.5 text-accent-blue" />
          Attack Path Legend
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
          <span className="text-slate-300">Clean / Monitored Asset</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
          <span className="text-rose-400 font-bold">Compromised Foothold</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-amber-400 shadow-sm shadow-amber-400/50" />
          <span className="text-amber-300">Blast Radius Reachable</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 bg-rose-500" />
          <span className="text-slate-400">Active Lateral Movement</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-5 h-0.5 border-t border-dashed border-slate-500" />
          <span className="text-slate-500">Segmented / Blocked Edge</span>
        </div>
      </div>
    </div>
  );
}
