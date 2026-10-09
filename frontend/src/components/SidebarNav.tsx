"use client";

import React from "react";
import {
  Boxes,
  Network,
  Activity,
  ShieldAlert,
  FileCheck2,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Zap,
} from "lucide-react";

export type NavView = "viewport" | "topology" | "telemetry" | "threats" | "compliance" | "settings";

interface SidebarNavProps {
  currentView: NavView;
  onSelectView: (view: NavView) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  threatCount: number;
  assetCount: number;
  telemetryCount: number;
}

export default function SidebarNav({
  currentView,
  onSelectView,
  collapsed,
  onToggleCollapse,
  threatCount,
  assetCount,
  telemetryCount,
}: SidebarNavProps) {
  const navItems = [
    {
      id: "viewport" as NavView,
      label: "Digital Twin Viewport",
      shortLabel: "Twin",
      icon: Boxes,
      badge: null,
      description: "3D & Schematic Network Stage",
    },
    {
      id: "topology" as NavView,
      label: "Asset Topology",
      shortLabel: "Assets",
      icon: Network,
      badge: assetCount > 0 ? `${assetCount}` : null,
      description: "OT / IT Asset Inventory & Matrix",
    },
    {
      id: "telemetry" as NavView,
      label: "Live Telemetry Stream",
      shortLabel: "Telemetry",
      icon: Activity,
      badge: telemetryCount > 0 ? "LIVE" : null,
      badgeColor: "bg-status-healthy/20 text-status-healthy border-status-healthy/30",
      description: "High-density streaming log console",
    },
    {
      id: "threats" as NavView,
      label: "Threat & Anomaly Log",
      shortLabel: "Threats",
      icon: ShieldAlert,
      badge: threatCount > 0 ? `${threatCount}` : null,
      badgeColor: "bg-status-critical/20 text-status-critical border-status-critical/40 font-bold",
      description: "MITRE ATT&CK & Adversary Paths",
    },
    {
      id: "compliance" as NavView,
      label: "Compliance & Audit",
      shortLabel: "Audit",
      icon: FileCheck2,
      badge: "88%",
      badgeColor: "bg-cyber-blue/20 text-cyber-blue border-cyber-blue/30",
      description: "IEC 62443, NIST CSF & SHA-256 Ledger",
    },
    {
      id: "settings" as NavView,
      label: "Settings & SOAR",
      shortLabel: "Config",
      icon: Settings,
      badge: null,
      description: "SOC Parameters & Integrations",
    },
  ];

  return (
    <aside
      className={`h-[calc(100vh-3.5rem)] border-r border-border bg-surface flex flex-col justify-between transition-all duration-200 select-none shrink-0 z-20 ${
        collapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Top Nav Items */}
      <div className="p-2 space-y-1 overflow-y-auto">
        {!collapsed && (
          <div className="px-3 pt-2 pb-1.5 text-[10px] uppercase font-mono font-bold tracking-wider text-typography-muted">
            Operations & Control
          </div>
        )}

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentView === item.id;

          return (
            <button
              key={item.id}
              onClick={() => onSelectView(item.id)}
              title={collapsed ? `${item.label} - ${item.description}` : undefined}
              className={`w-full group relative flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-mono transition-all duration-150 ${
                isActive
                  ? "bg-surface-hover text-typography-primary font-semibold shadow-soc-card border border-border"
                  : "text-typography-muted hover:text-typography-primary hover:bg-surface-subtle"
              }`}
            >
              {/* Cyber blue active vertical bar */}
              {isActive && (
                <div className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-cyber-blue shadow-glow-blue" />
              )}

              <Icon
                className={`w-4 h-4 shrink-0 transition-colors ${
                  isActive ? "text-cyber-blue" : "text-typography-muted group-hover:text-cyber-cyan"
                }`}
              />

              {!collapsed && (
                <div className="flex-1 flex items-center justify-between text-left truncate">
                  <span className="truncate">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded border font-mono ${
                        item.badgeColor || "bg-surface-subtle text-typography-muted border-border"
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              )}

              {collapsed && item.badge && (
                <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-status-critical" />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Footer: System Version & Collapse Toggle */}
      <div className="p-2 border-t border-border bg-surface-subtle/50">
        {!collapsed && (
          <div className="px-3 py-2 rounded-lg bg-surface/80 border border-border text-[11px] font-mono text-typography-muted mb-2">
            <div className="flex items-center justify-between text-typography-primary font-bold">
              <span className="flex items-center gap-1.5 text-cyber-blue">
                <Shield className="w-3 h-3" /> AegisTwin SOC
              </span>
              <span className="text-[10px] text-status-healthy font-semibold">AIRGAP READY</span>
            </div>
            <div className="text-[10px] text-typography-muted mt-0.5 truncate">
              Kernel v2.4 • Neo4j Engine
            </div>
          </div>
        )}

        <button
          onClick={onToggleCollapse}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-surface-subtle hover:bg-surface-hover text-typography-muted hover:text-typography-primary border border-border text-xs font-mono transition-colors"
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4 text-cyber-blue" />
          ) : (
            <>
              <ChevronLeft className="w-4 h-4" />
              <span className="text-[11px]">Collapse Menu</span>
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
