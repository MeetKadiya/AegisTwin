"use client";

import React, { useState, useRef, useEffect, useMemo } from "react";
import {
  Crosshair,
  Flame,
  Play,
  RotateCcw,
  RefreshCw,
  Search,
  X,
  ChevronDown,
  ShieldAlert,
  Building2,
  CheckCircle2,
  Palette,
  Server,
  Terminal,
  Activity,
  Boxes,
  Network,
  Lock,
  Radio,
} from "lucide-react";
import { TENANTS_LIST } from "@/lib/mockData";
import { TopologyNode } from "@/lib/types";

export type ThemeOption = "cyberpunk" | "cobalt" | "matrix" | "crimson" | "daylight";

export const THEMES: { id: ThemeOption; name: string; icon: string; dotColor: string }[] = [
  { id: "cyberpunk", name: "Electric Cyberpunk", icon: "⚡", dotColor: "#00F0FF" },
  { id: "cobalt", name: "Deep Cobalt SOC", icon: "🛡️", dotColor: "#3B82F6" },
  { id: "matrix", name: "Matrix Emerald OT", icon: "📟", dotColor: "#00FF88" },
  { id: "crimson", name: "Crimson Red Team", icon: "🚨", dotColor: "#FF2A55" },
  { id: "daylight", name: "Daylight Tactical", icon: "☀️", dotColor: "#2563EB" },
];

interface GlobalHeaderProps {
  wsConnected: boolean;
  selectedTenant: string;
  onSelectTenant: (tenantId: string) => void;
  onOpenCommandPalette: () => void;
  activeThreatCount: number;
  loading: boolean;
  nodes: TopologyNode[];
  onSelectNode: (node: TopologyNode) => void;
  onNavigateView: (view: any) => void;
  currentTheme: ThemeOption;
  onSelectTheme: (theme: ThemeOption) => void;
  onRunSimulation: () => void;
  onStepSimulation: () => void;
  onResetSimulation: () => void;
  onRefreshData: () => void;
}

export default function GlobalHeader({
  wsConnected,
  selectedTenant,
  onSelectTenant,
  onOpenCommandPalette,
  activeThreatCount,
  loading,
  nodes,
  onSelectNode,
  onNavigateView,
  currentTheme,
  onSelectTheme,
  onRunSimulation,
  onStepSimulation,
  onResetSimulation,
  onRefreshData,
}: GlobalHeaderProps) {
  const [tenantDropdownOpen, setTenantDropdownOpen] = useState(false);
  const [themeDropdownOpen, setThemeDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchDropdownOpen, setSearchDropdownOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  const currentTenantObj = TENANTS_LIST.find((t) => t.id === selectedTenant) || TENANTS_LIST[0];
  const activeThemeObj = THEMES.find((t) => t.id === currentTheme) || THEMES[0];

  // Close search dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchContainerRef.current && !searchContainerRef.current.contains(e.target as Node)) {
        setSearchDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Filtered live results for the header search
  const searchResults = useMemo(() => {
    if (!searchQuery.trim()) return [];
    const q = searchQuery.toLowerCase();
    return nodes.filter(
      (n) =>
        n.label.toLowerCase().includes(q) ||
        n.ip.toLowerCase().includes(q) ||
        n.tier.toLowerCase().includes(q) ||
        n.type.toLowerCase().includes(q) ||
        n.vulnerabilities?.some((v) => v.cve.toLowerCase().includes(q) || v.title.toLowerCase().includes(q))
    ).slice(0, 6);
  }, [nodes, searchQuery]);

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (searchResults.length > 0) {
      onSelectNode(searchResults[0]);
      setSearchDropdownOpen(false);
      setSearchQuery("");
    } else {
      onOpenCommandPalette();
      setSearchDropdownOpen(false);
    }
  };

  return (
    <header className="h-14 border-b border-border bg-surface/95 px-4 flex items-center justify-between shrink-0 backdrop-blur-md z-30 select-none">
      {/* Left Section: Brand & Multi-Tenant Selector */}
      <div className="flex items-center gap-3">
        {/* Brand Logo */}
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-gradient-to-tr from-cyber-blue to-cyber-cyan text-white shadow-glow-blue">
            <Crosshair className="w-4 h-4 animate-spin-slow" />
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-extrabold text-sm tracking-tight text-typography-primary uppercase">
              Aegis<span className="text-cyber-blue">Twin</span>
            </span>
            <span className="text-[10px] font-mono font-bold px-1.5 py-0.2 rounded bg-surface-subtle text-cyber-blue border border-border">
              SOC
            </span>
          </div>
        </div>

        <div className="h-4 w-[1px] bg-border" />

        {/* Tenant Selector Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setTenantDropdownOpen(!tenantDropdownOpen);
              setThemeDropdownOpen(false);
            }}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-surface-subtle hover:bg-surface-hover border border-border text-xs font-mono text-typography-primary transition-colors"
          >
            <Building2 className="w-3.5 h-3.5 text-cyber-blue" />
            <span className="max-w-[140px] truncate">{currentTenantObj.name}</span>
            <ChevronDown className="w-3 h-3 text-typography-muted" />
          </button>

          {tenantDropdownOpen && (
            <div className="absolute left-0 top-full mt-1.5 w-64 rounded-lg glass-dropdown p-1.5 z-50 text-xs font-mono">
              <div className="px-2 py-1 text-[10px] uppercase font-bold text-typography-muted tracking-wider">
                Select Isolated Tenant Context
              </div>
              {TENANTS_LIST.map((t) => (
                <button
                  key={t.id}
                  onClick={() => {
                    onSelectTenant(t.id);
                    setTenantDropdownOpen(false);
                  }}
                  className={`w-full text-left px-2 py-1.5 rounded flex items-center justify-between transition-colors ${
                    selectedTenant === t.id
                      ? "bg-cyber-blue/15 text-cyber-blue border border-cyber-blue/30 font-bold"
                      : "text-typography-primary hover:bg-surface-hover"
                  }`}
                >
                  <div className="truncate">
                    <div>{t.name}</div>
                    <div className="text-[10px] text-typography-muted">{t.region}</div>
                  </div>
                  {t.criticalThreats > 0 ? (
                    <span className="text-[10px] px-1 rounded bg-status-critical/20 text-status-critical">
                      {t.criticalThreats}
                    </span>
                  ) : (
                    <CheckCircle2 className="w-3 h-3 text-status-healthy" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Real-time Connection Status Pill */}
        <div
          className={`flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-[10px] font-mono transition-all ${
            wsConnected
              ? "bg-status-healthy/10 border-status-healthy/30 text-status-healthy shadow-glow-emerald"
              : "bg-status-warning/10 border-status-warning/30 text-status-warning"
          }`}
        >
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              wsConnected ? "bg-status-healthy live-beacon" : "bg-status-warning"
            }`}
          />
          <span className="font-semibold">{wsConnected ? "LIVE" : "DISCONNECTED"}</span>
        </div>
      </div>

      {/* Center Section: Interactive Search Bar & Button */}
      <div ref={searchContainerRef} className="flex-1 max-w-lg mx-3 relative">
        <form onSubmit={handleSearchSubmit} className="relative flex items-center">
          {/* Clickable Search Icon Button */}
          <button
            type="submit"
            onClick={() => {
              if (!searchQuery.trim()) {
                onOpenCommandPalette();
              } else {
                handleSearchSubmit();
              }
            }}
            title="Execute Search / Open Palette"
            className="absolute left-2.5 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-surface text-typography-muted hover:text-cyber-blue transition-colors cursor-pointer z-10"
          >
            <Search className="w-3.5 h-3.5" />
          </button>

          {/* Interactive Live Search Input */}
          <input
            ref={searchInputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setSearchDropdownOpen(true);
            }}
            onFocus={() => {
              if (searchQuery.trim()) setSearchDropdownOpen(true);
            }}
            placeholder="Search assets, IPs, CVEs, or threats... (Press Enter or ⌘K)"
            className="w-full pl-9 pr-16 py-1.5 rounded-lg bg-canvas border border-border text-xs font-mono text-typography-primary placeholder-typography-muted focus:outline-none focus:border-cyber-blue focus:ring-1 focus:ring-cyber-blue transition-all"
          />

          {/* Right Action Icons in Search Bar */}
          <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1.5">
            {searchQuery && (
              <button
                type="button"
                onClick={() => {
                  setSearchQuery("");
                  setSearchDropdownOpen(false);
                }}
                className="p-0.5 text-typography-muted hover:text-typography-primary"
                title="Clear search query"
              >
                <X className="w-3 h-3" />
              </button>
            )}

            {/* Clickable Cmd+K Badge */}
            <button
              type="button"
              onClick={onOpenCommandPalette}
              title="Open Full Command Palette (Cmd + K / Ctrl + K)"
              className="inline-flex items-center gap-0.5 px-1.5 py-0.5 text-[10px] font-mono rounded bg-surface border border-border text-typography-muted hover:text-cyber-blue hover:border-cyber-blue/50 transition-colors cursor-pointer"
            >
              <span>⌘</span>K
            </button>
          </div>
        </form>

        {/* Live Search Results Dropdown */}
        {searchDropdownOpen && searchQuery.trim() && (
          <div className="absolute left-0 right-0 top-full mt-1.5 rounded-xl glass-dropdown p-2 z-50 text-xs font-mono shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex items-center justify-between px-2 py-1 text-[10px] uppercase font-bold text-typography-muted border-b border-border">
              <span>Matching Assets & Threats ({searchResults.length})</span>
              <span className="text-cyber-blue">Press Enter to select</span>
            </div>

            <div className="mt-1 space-y-1 max-h-64 overflow-y-auto">
              {searchResults.length === 0 ? (
                <div className="p-3 text-center text-typography-muted text-xs">
                  No assets or CVEs found for "{searchQuery}".
                  <button
                    onClick={() => {
                      onOpenCommandPalette();
                      setSearchDropdownOpen(false);
                    }}
                    className="block mx-auto mt-1 text-cyber-blue hover:underline font-bold"
                  >
                    Open Deep Command Search ⌘K
                  </button>
                </div>
              ) : (
                searchResults.map((asset) => (
                  <button
                    key={asset.id}
                    onClick={() => {
                      onSelectNode(asset);
                      setSearchDropdownOpen(false);
                      setSearchQuery("");
                    }}
                    className="w-full text-left p-2 rounded-lg hover:bg-surface-hover flex items-center justify-between transition-colors group"
                  >
                    <div className="flex items-center gap-2">
                      <Server className="w-3.5 h-3.5 text-cyber-blue group-hover:text-cyber-cyan" />
                      <div>
                        <div className="font-bold text-typography-primary">{asset.label}</div>
                        <div className="text-[10px] text-cyber-cyan">{asset.ip} • {asset.tier}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5">
                      {asset.compromised && (
                        <span className="px-1.5 py-0.2 rounded bg-status-critical/20 text-status-critical text-[10px] font-bold">
                          BREACHED
                        </span>
                      )}
                      {asset.vulnerabilities && asset.vulnerabilities.length > 0 && (
                        <span className="px-1 py-0.2 rounded bg-surface border border-border text-typography-muted text-[10px]">
                          {asset.vulnerabilities[0].cve}
                        </span>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>

            <div className="pt-2 mt-1 border-t border-border flex items-center justify-between text-[10px] text-typography-muted px-1">
              <span>Quick Navigation</span>
              <button
                onClick={() => {
                  onOpenCommandPalette();
                  setSearchDropdownOpen(false);
                }}
                className="text-cyber-blue hover:underline"
              >
                Open Full Command Palette →
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Right Section: Theme Picker, Threat Badge, & Action Buttons */}
      <div className="flex items-center gap-2.5">
        {/* Dynamic Color Theme Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => {
              setThemeDropdownOpen(!themeDropdownOpen);
              setTenantDropdownOpen(false);
            }}
            className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-surface-subtle hover:bg-surface-hover border border-border text-xs font-mono text-typography-primary transition-colors"
            title="Switch AegisTwin Theme"
          >
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: activeThemeObj.dotColor }}
            />
            <span className="hidden sm:inline text-[11px] font-semibold">{activeThemeObj.name}</span>
            <ChevronDown className="w-3 h-3 text-typography-muted" />
          </button>

          {themeDropdownOpen && (
            <div className="absolute right-0 top-full mt-1.5 w-56 rounded-xl glass-dropdown p-1.5 z-50 text-xs font-mono shadow-2xl">
              <div className="px-2 py-1 text-[10px] uppercase font-bold text-typography-muted flex items-center gap-1.5">
                <Palette className="w-3 h-3 text-cyber-blue" />
                Select Color Theme
              </div>
              <div className="space-y-0.5 mt-1">
                {THEMES.map((theme) => (
                  <button
                    key={theme.id}
                    onClick={() => {
                      onSelectTheme(theme.id);
                      setThemeDropdownOpen(false);
                    }}
                    className={`w-full text-left px-2.5 py-1.5 rounded-lg flex items-center justify-between transition-colors ${
                      currentTheme === theme.id
                        ? "bg-cyber-blue/15 text-cyber-blue border border-cyber-blue/30 font-bold"
                        : "text-typography-primary hover:bg-surface-hover"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ backgroundColor: theme.dotColor }}
                      />
                      <span>{theme.name}</span>
                    </div>
                    {currentTheme === theme.id && <CheckCircle2 className="w-3.5 h-3.5 text-cyber-blue" />}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Active Threat Counter Badge */}
        {activeThreatCount > 0 ? (
          <div className="hidden xl:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-critical/15 border border-status-critical/40 text-status-critical text-[11px] font-mono font-bold shadow-glow-crimson animate-pulse">
            <ShieldAlert className="w-3 h-3" />
            <span>{activeThreatCount} BREACH</span>
          </div>
        ) : (
          <div className="hidden xl:flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-status-healthy/10 border border-status-healthy/30 text-status-healthy text-[11px] font-mono">
            <CheckCircle2 className="w-3 h-3" />
            <span>SECURE</span>
          </div>
        )}

        <div className="h-4 w-[1px] bg-border" />

        {/* Adversary Simulation Action Buttons */}
        <div className="flex items-center gap-1.5 font-mono text-xs">
          <button
            onClick={onRunSimulation}
            disabled={loading}
            title="Launch autonomous Red Team simulation"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-status-critical hover:bg-red-500 active:scale-[0.98] text-white font-bold transition-all shadow-glow-crimson disabled:opacity-50 hover:scale-[1.02]"
          >
            <Flame className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Run Red Team</span>
          </button>

          <button
            onClick={onStepSimulation}
            disabled={loading}
            title="Execute single lateral movement step"
            className="flex items-center gap-1 px-2 py-1.5 rounded-md bg-surface-subtle hover:bg-surface-hover text-typography-primary border border-border transition-all active:scale-[0.98] disabled:opacity-50 hover:scale-[1.02]"
          >
            <Play className="w-3 h-3 fill-current text-cyber-blue" />
            <span className="hidden md:inline">Step</span>
          </button>

          <button
            onClick={onResetSimulation}
            disabled={loading}
            title="Reset compromise states"
            className="p-1.5 rounded-md bg-surface-subtle hover:bg-surface-hover text-typography-muted hover:text-typography-primary border border-border transition-colors active:scale-[0.98] disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={onRefreshData}
            disabled={loading}
            title="Refresh digital twin state"
            className="p-1.5 rounded-md bg-surface-subtle hover:bg-surface-hover text-typography-muted hover:text-cyber-blue border border-border transition-colors active:scale-[0.98] disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyber-blue" : ""}`} />
          </button>
        </div>
      </div>
    </header>
  );
}
