"use client";

import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Search,
  X,
  Boxes,
  Network,
  Activity,
  ShieldAlert,
  FileCheck2,
  Settings,
  Flame,
  Play,
  RotateCcw,
  Server,
  Zap,
  ArrowRight,
  Shield,
  Radio,
  Lock,
  Database,
} from "lucide-react";
import { TopologyNode } from "@/lib/types";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: TopologyNode[];
  onNavigate: (view: any) => void;
  onSelectNode: (node: TopologyNode) => void;
  onRunSimulation: () => void;
  onResetSimulation: () => void;
}

export default function CommandPalette({
  isOpen,
  onClose,
  nodes,
  onNavigate,
  onSelectNode,
  onRunSimulation,
  onResetSimulation,
}: CommandPaletteProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-focus on open
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Global keydown listener for Escape
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // Filtered Assets
  const filteredAssets = useMemo(() => {
    if (!query.trim()) return nodes.slice(0, 6);
    const q = query.toLowerCase();
    return nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(q) ||
        n.ip.toLowerCase().includes(q) ||
        n.tier.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q) ||
        n.vulnerabilities?.some((v) => v.cve.toLowerCase().includes(q) || v.title.toLowerCase().includes(q))
    );
  }, [nodes, query]);

  // Quick navigation items
  const navItems = [
    { id: "viewport", label: "Digital Twin Viewport", icon: Boxes },
    { id: "topology", label: "Asset Inventory Matrix", icon: Network },
    { id: "telemetry", label: "Live Telemetry Stream", icon: Activity },
    { id: "threats", label: "Threat & Anomaly Log", icon: ShieldAlert },
    { id: "compliance", label: "Compliance & Audit", icon: FileCheck2 },
    { id: "settings", label: "SOC Settings & SOAR", icon: Settings },
  ];

  if (!isOpen) return null;

  return (
    <div
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 p-4 bg-canvas/80 backdrop-blur-md animate-in fade-in duration-150 select-none"
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-2xl bg-surface border border-border rounded-2xl shadow-2xl overflow-hidden font-mono text-xs flex flex-col animate-in zoom-in-95 duration-150"
      >
        {/* Search Input Bar */}
        <div className="p-3.5 border-b border-border flex items-center gap-3 bg-surface-subtle">
          <Search className="w-4 h-4 text-cyber-blue shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type to search assets, IPs, CVEs, or commands (e.g. 'vpn', 'cve-2023', 'admin')..."
            className="flex-1 bg-transparent border-none text-typography-primary placeholder-typography-muted focus:outline-none text-xs font-mono"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="p-1 rounded text-typography-muted hover:text-typography-primary"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <kbd className="px-1.5 py-0.5 rounded bg-canvas border border-border text-[10px] text-typography-muted">
            ESC
          </kbd>
        </div>

        {/* Results Container */}
        <div className="max-h-[28rem] overflow-y-auto p-2.5 space-y-3.5">
          {/* Quick Actions */}
          <div>
            <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-typography-muted">
              Adversary Simulation Actions
            </div>
            <div className="space-y-1 mt-1">
              <button
                onClick={() => {
                  onRunSimulation();
                  onClose();
                }}
                className="w-full text-left px-3 py-2 rounded-lg flex items-center justify-between hover:bg-surface-hover text-typography-primary transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <Flame className="w-4 h-4 text-status-critical group-hover:scale-110 transition-transform" />
                  <div>
                    <span className="font-bold text-typography-primary">
                      Run Autonomous Red Team AI Simulation
                    </span>
                    <div className="text-[10px] text-typography-muted">
                      Execute multi-hop lateral movement traversal & MITRE ATT&CK mapping
                    </div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-status-critical/15 text-status-critical font-bold">
                  EXECUTE
                </span>
              </button>

              <button
                onClick={() => {
                  onResetSimulation();
                  onClose();
                }}
                className="w-full text-left px-3 py-2 rounded-lg flex items-center justify-between hover:bg-surface-hover text-typography-primary transition-colors group"
              >
                <div className="flex items-center gap-2.5">
                  <RotateCcw className="w-4 h-4 text-cyber-blue" />
                  <div>
                    <span className="font-semibold text-typography-primary">
                      Reset Network Compromises
                    </span>
                    <div className="text-[10px] text-typography-muted">
                      Clear all adversary footholds back to clean operational baseline
                    </div>
                  </div>
                </div>
                <span className="text-[10px] px-2 py-0.5 rounded bg-surface-subtle text-typography-muted">
                  CLEAN
                </span>
              </button>
            </div>
          </div>

          {/* Navigation Views */}
          <div>
            <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-typography-muted">
              Jump to SOC Console View
            </div>
            <div className="grid grid-cols-2 gap-1.5 mt-1">
              {navItems.map((view) => {
                const Icon = view.icon;
                return (
                  <button
                    key={view.id}
                    onClick={() => {
                      onNavigate(view.id);
                      onClose();
                    }}
                    className="text-left px-3 py-2 rounded-lg flex items-center gap-2.5 hover:bg-surface-hover text-typography-primary transition-colors border border-transparent hover:border-border"
                  >
                    <Icon className="w-3.5 h-3.5 text-cyber-blue shrink-0" />
                    <span className="truncate">{view.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Matching Assets List */}
          <div>
            <div className="px-2.5 py-1 text-[10px] uppercase font-bold text-typography-muted flex items-center justify-between">
              <span>Matching Enterprise Assets ({filteredAssets.length})</span>
            </div>
            <div className="space-y-1 mt-1">
              {filteredAssets.length === 0 ? (
                <div className="text-center py-6 text-typography-muted">
                  No assets found matching "{query}".
                </div>
              ) : (
                filteredAssets.map((asset) => (
                  <button
                    key={asset.id}
                    onClick={() => {
                      onSelectNode(asset);
                      onClose();
                    }}
                    className="w-full text-left px-3 py-2 rounded-lg flex items-center justify-between hover:bg-surface-hover text-typography-primary transition-colors group"
                  >
                    <div className="flex items-center gap-2.5">
                      <Server className="w-3.5 h-3.5 text-cyber-blue group-hover:text-cyber-cyan shrink-0" />
                      <div>
                        <div className="font-bold text-typography-primary flex items-center gap-2">
                          {asset.label}
                          <span className="text-[10px] font-normal text-typography-muted">
                            ({asset.hostname || asset.id})
                          </span>
                        </div>
                        <div className="text-[10px] text-cyber-cyan font-mono">
                          {asset.ip} • Tier: {asset.tier} • Crit: {asset.criticality}/10
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {asset.compromised ? (
                        <span className="px-2 py-0.5 rounded bg-status-critical/20 text-status-critical font-bold text-[10px] animate-pulse">
                          BREACHED
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded bg-status-healthy/10 text-status-healthy text-[10px]">
                          CLEAN
                        </span>
                      )}
                      <ArrowRight className="w-3.5 h-3.5 text-typography-muted group-hover:text-cyber-blue" />
                    </div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-2.5 border-t border-border bg-surface-subtle text-[10px] text-typography-muted flex items-center justify-between">
          <span>Click any item or press ESC to dismiss</span>
          <span>AegisTwin Enterprise SOC</span>
        </div>
      </div>
    </div>
  );
}
