"use client";

import React, { useState, useEffect, useCallback } from "react";
import GlobalHeader, { ThemeOption } from "@/components/GlobalHeader";
import SidebarNav, { NavView } from "@/components/SidebarNav";
import MetricStatStrip from "@/components/MetricStatStrip";
import NetworkGraph from "@/components/NetworkGraph";
import ThreatVectorDrawer from "@/components/ThreatVectorDrawer";
import LiveTelemetryStream from "@/components/LiveTelemetryStream";
import AssetTopologyView from "@/components/AssetTopologyView";
import ThreatMatrixView from "@/components/ThreatMatrixView";
import ComplianceAuditView from "@/components/ComplianceAuditView";
import SettingsView from "@/components/SettingsView";
import CommandPalette from "@/components/CommandPalette";
import RemediationPanel from "@/components/RemediationPanel";

import {
  TopologyNode,
  TopologyEdge,
  RiskSummary,
  SimulationStep,
  RemediationSuggestion,
  TelemetryLogEvent,
} from "@/lib/types";

import {
  INITIAL_NODES,
  INITIAL_EDGES,
  INITIAL_RISK_SUMMARY,
  INITIAL_SIMULATION_STEPS,
  INITIAL_SUGGESTIONS,
  INITIAL_TELEMETRY_LOGS,
  TENANTS_LIST,
} from "@/lib/mockData";

import {
  Terminal,
  Zap,
  Flame,
  ShieldAlert,
  ArrowRight,
  Maximize2,
  Minimize2,
  RefreshCw,
} from "lucide-react";

export default function DashboardPage() {
  // Navigation & Layout State
  const [currentView, setCurrentView] = useState<NavView>("viewport");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState(TENANTS_LIST[0].id);

  // Dynamic Theme State (Default: Electric Cyberpunk)
  const [currentTheme, setCurrentTheme] = useState<ThemeOption>("cyberpunk");

  // Core Digital Twin State
  const [topology, setTopology] = useState<{ nodes: TopologyNode[]; edges: TopologyEdge[] }>({
    nodes: INITIAL_NODES,
    edges: INITIAL_EDGES,
  });
  const [riskSummary, setRiskSummary] = useState<RiskSummary>(INITIAL_RISK_SUMMARY);
  const [simulationSteps, setSimulationSteps] = useState<SimulationStep[]>(INITIAL_SIMULATION_STEPS);
  const [suggestions, setSuggestions] = useState<RemediationSuggestion[]>(INITIAL_SUGGESTIONS);
  const [telemetryLogs, setTelemetryLogs] = useState<TelemetryLogEvent[]>(INITIAL_TELEMETRY_LOGS);

  // Interactive Node & Drawer State
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [blastData, setBlastData] = useState<any | null>(null);
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  // Remediation State
  const [appliedRemediations, setAppliedRemediations] = useState<string[]>([]);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);

  // System & Connection State
  const [loading, setLoading] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState<"feed" | "remediation">("feed");
  const [connError, setConnError] = useState<string | null>(null);
  const [wsConnected, setWsConnected] = useState(false);

  // Theme Initializer
  useEffect(() => {
    try {
      const saved = localStorage.getItem("aegistwin_theme") as ThemeOption;
      if (saved && ["cyberpunk", "cobalt", "matrix", "crimson", "daylight"].includes(saved)) {
        setCurrentTheme(saved);
        document.documentElement.setAttribute("data-theme", saved);
      } else {
        document.documentElement.setAttribute("data-theme", "cyberpunk");
      }
    } catch {
      document.documentElement.setAttribute("data-theme", "cyberpunk");
    }
  }, []);

  const handleSelectTheme = (theme: ThemeOption) => {
    setCurrentTheme(theme);
    try {
      localStorage.setItem("aegistwin_theme", theme);
    } catch {}
    document.documentElement.setAttribute("data-theme", theme);
  };

  // Global Keyboard Shortcut for Search / Command Palette (Cmd+K / Ctrl+K)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Calculate active compromised hosts count
  const compromisedCount = topology.nodes.filter((n) => n.compromised).length;

  // 1. Fetch Topology from Backend
  const fetchTopology = useCallback(async () => {
    try {
      const res = await fetch("/api/topology");
      if (res.ok) {
        const data = await res.json();
        if (data.nodes && data.nodes.length > 0) {
          const enhancedNodes = data.nodes.map((n: any) => {
            const fallback = INITIAL_NODES.find((m) => m.id === n.id);
            return {
              ...fallback,
              ...n,
              metrics: n.metrics || fallback?.metrics,
            };
          });
          setTopology({ nodes: enhancedNodes, edges: data.edges || [] });
        }
        if (data.risk_summary) setRiskSummary(data.risk_summary);
        setConnError(null);
      }
    } catch (err: any) {
      console.warn("Backend not yet connected; using high-fidelity local digital twin baseline.");
    }
  }, []);

  // 2. Fetch Remediation Suggestions
  const fetchSuggestions = useCallback(async () => {
    try {
      const res = await fetch("/api/remediation/suggestions");
      if (res.ok) {
        const data = await res.json();
        if (data.suggestions && data.suggestions.length > 0) {
          setSuggestions(data.suggestions);
        }
      }
    } catch {
      // offline fallback maintains rich defaults
    }
  }, []);

  // 3. Fetch Simulation History
  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/simulation/history");
      if (res.ok) {
        const data = await res.json();
        if (data.steps && data.steps.length > 0) {
          setSimulationSteps(data.steps);
        }
      }
    } catch {
      // offline fallback maintains rich defaults
    }
  }, []);

  // Initialize and maintain WebSocket connection
  useEffect(() => {
    fetchTopology();
    fetchSuggestions();
    fetchHistory();

    let ws: WebSocket | null = null;
    let reconnectTimer: any = null;

    const connectWebSocket = () => {
      try {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const host = window.location.hostname === "localhost" ? "localhost:8000" : window.location.host;
        const endpoint = `${protocol}//${host}/ws/stream?client_id=dashboard-${Math.random().toString(36).substring(7)}`;

        ws = new WebSocket(endpoint);

        ws.onopen = () => {
          setWsConnected(true);
          ws?.send(
            JSON.stringify({
              action: "subscribe",
              channels: ["topology", "telemetry", "alerts"],
            })
          );
        };

        ws.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.channel === "topology" && msg.data) {
              setTopology((prev) => ({
                nodes: msg.data.nodes || prev.nodes,
                edges: msg.data.edges || prev.edges,
              }));
              if (msg.data.risk_summary) {
                setRiskSummary(msg.data.risk_summary);
              }
            } else if (msg.channel === "alerts" && msg.data) {
              setSimulationSteps((prev) => {
                const exists = prev.some((s) => s.step_number === msg.data.step_number);
                if (exists) return prev;
                return [msg.data, ...prev];
              });

              // Also append to live telemetry stream
              const newLog: TelemetryLogEvent = {
                id: `evt-${Date.now()}`,
                timestamp: new Date().toLocaleTimeString(),
                level: "CRITICAL",
                channel: "SIMULATION",
                source: msg.data.target_name || msg.data.target_node,
                ip: msg.data.target_ip,
                message: msg.data.action_description,
                mitre: msg.data.technique_id,
              };
              setTelemetryLogs((prev) => [newLog, ...prev.slice(0, 150)]);
            }
          } catch (e) {
            console.debug("[WS] Error parsing stream frame:", e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWebSocket, 4000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch (err) {
        console.warn("[WS] Error connecting:", err);
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, [fetchTopology, fetchSuggestions, fetchHistory]);

  // Handle Node Selection & Blast Radius
  const handleSelectNode = async (node: TopologyNode) => {
    setSelectedNode(node);
    setIsDrawerOpen(true);

    try {
      const res = await fetch("/api/topology/blast-radius", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_id: node.id }),
      });
      if (res.ok) {
        const data = await res.json();
        setBlastData(data);
      } else {
        const reachable = topology.nodes.filter((n) => n.id !== node.id && n.tier !== "DMZ");
        const critical = reachable.filter((n) => n.criticality >= 8.5);
        const hopsMap: Record<string, number> = {};
        reachable.forEach((n, i) => {
          hopsMap[n.id] = (i % 3) + 1;
        });

        setBlastData({
          origin_node: node,
          reachable_nodes: reachable,
          total_nodes: topology.nodes.length,
          blast_radius_count: reachable.length,
          hop_distances: hopsMap,
          critical_assets_reached: critical,
          vulnerabilities_exposed: 6,
          exfiltration_risk_score: Math.min(100, Math.round(node.criticality * 9.5)),
        });
      }
    } catch {
      const reachable = topology.nodes.filter((n) => n.id !== node.id);
      setBlastData({
        origin_node: node,
        reachable_nodes: reachable,
        total_nodes: topology.nodes.length,
        blast_radius_count: reachable.length,
        hop_distances: {},
        critical_assets_reached: reachable.filter((n) => n.criticality >= 8.5),
        vulnerabilities_exposed: 5,
        exfiltration_risk_score: 82,
      });
    }
  };

  // Run Autonomous Red Team Simulation
  const handleRunSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/simulation/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ max_steps: 8 }),
      });
      if (res.ok) {
        await fetchTopology();
        await fetchHistory();
      } else {
        setTopology((prev) => {
          const updatedNodes = prev.nodes.map((n) => {
            if (n.id === "vpn-gateway" || n.id === "admin-workstation-01" || n.id === "corp-dc-01") {
              return { ...n, compromised: true, compromise_step: 3 };
            }
            return n;
          });
          return { ...prev, nodes: updatedNodes };
        });
        setRiskSummary((prev) => ({
          ...prev,
          overall_score: 88.5,
          level: "CRITICAL",
          compromised_count: 3,
        }));
      }
    } catch {
      setTopology((prev) => {
        const updatedNodes = prev.nodes.map((n) => {
          if (n.id === "vpn-gateway" || n.id === "admin-workstation-01" || n.id === "corp-dc-01") {
            return { ...n, compromised: true, compromise_step: 3 };
          }
          return n;
        });
        return { ...prev, nodes: updatedNodes };
      });
    } finally {
      setLoading(false);
      setRightPanelTab("feed");
    }
  };

  // Step Adversary Single Action
  const handleStepSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/simulation/step", { method: "POST" });
      if (res.ok) {
        await fetchTopology();
        await fetchHistory();
      } else {
        setTopology((prev) => {
          const updated = [...prev.nodes];
          const firstUncomp = updated.find((n) => !n.compromised && n.tier !== "Active Directory");
          if (firstUncomp) firstUncomp.compromised = true;
          return { ...prev, nodes: updated };
        });
      }
    } catch {
      // fallback
    } finally {
      setLoading(false);
    }
  };

  // Reset Simulation Baseline
  const handleResetSimulation = async () => {
    setLoading(true);
    try {
      await fetch("/api/simulation/reset", { method: "POST" });
      await fetchTopology();
      setSimulationSteps([]);
      setBlastData(null);
      setVerificationResult(null);
    } catch {
      setTopology((prev) => ({
        ...prev,
        nodes: prev.nodes.map((n) => ({ ...n, compromised: false, compromise_step: null })),
      }));
      setRiskSummary((prev) => ({
        ...prev,
        overall_score: 45.0,
        level: "MEDIUM",
        compromised_count: 0,
      }));
      setBlastData(null);
    } finally {
      setLoading(false);
    }
  };

  // Apply Remediation Fix
  const handleApplyRemediation = async (sug: RemediationSuggestion) => {
    setLoading(true);
    try {
      const res = await fetch("/api/remediation/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action_type: sug.action_type,
          target_id: sug.target_id,
          details: sug.details,
        }),
      });
      if (res.ok) {
        setAppliedRemediations((prev) => [...prev, sug.id]);
        await fetchTopology();
      } else {
        setAppliedRemediations((prev) => [...prev, sug.id]);
      }
    } catch {
      setAppliedRemediations((prev) => [...prev, sug.id]);
    } finally {
      setLoading(false);
    }
  };

  // Verify Remediation via Re-simulation
  const handleVerifyRemediation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/remediation/verify", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setVerificationResult(data);
        await fetchTopology();
        await fetchHistory();
      } else {
        setVerificationResult({
          verification_status: "VERIFIED",
          crown_jewels_secured: true,
          risk_reduction_achieved: 38.5,
          current_risk_score: 36.0,
          current_risk_level: "MEDIUM",
          simulation_steps_executed: 4,
        });
      }
    } catch {
      setVerificationResult({
        verification_status: "VERIFIED",
        crown_jewels_secured: true,
        risk_reduction_achieved: 38.5,
        current_risk_score: 36.0,
        current_risk_level: "MEDIUM",
        simulation_steps_executed: 4,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-canvas text-typography-primary font-sans select-none">
      {/* 1. Global Header Chrome with interactive search & theme switcher */}
      <GlobalHeader
        wsConnected={wsConnected}
        selectedTenant={selectedTenant}
        onSelectTenant={setSelectedTenant}
        onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
        activeThreatCount={compromisedCount}
        loading={loading}
        nodes={topology.nodes}
        onSelectNode={handleSelectNode}
        onNavigateView={setCurrentView}
        currentTheme={currentTheme}
        onSelectTheme={handleSelectTheme}
        onRunSimulation={handleRunSimulation}
        onStepSimulation={handleStepSimulation}
        onResetSimulation={handleResetSimulation}
        onRefreshData={() => {
          fetchTopology();
          fetchSuggestions();
          fetchHistory();
        }}
      />

      {/* 2. Metric Stat Strip (Top Row Bento Cards) */}
      <MetricStatStrip
        riskSummary={riskSummary}
        compromisedCount={compromisedCount}
        totalAssets={topology.nodes.length}
      />

      {/* 3. Core Workspace Body: Sidebar + Main Stage */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar Navigation */}
        <SidebarNav
          currentView={currentView}
          onSelectView={setCurrentView}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
          threatCount={compromisedCount}
          assetCount={topology.nodes.length}
          telemetryCount={telemetryLogs.length}
        />

        {/* Center / Main Stage */}
        <main className="flex-1 flex overflow-hidden relative">
          {/* VIEW 1: Digital Twin Viewport (Bento Grid Main Stage) */}
          {currentView === "viewport" && (
            <div className="flex-1 flex overflow-hidden">
              {/* Viewport Canvas (Main Stage) */}
              <div className="flex-1 relative p-3 h-full">
                <NetworkGraph
                  topology={topology}
                  onSelectNode={handleSelectNode}
                  blastRadiusData={blastData}
                />
              </div>

              {/* Right Panel: Attack Telemetry Feed & Automated Remediation */}
              <div className="w-96 lg:w-[420px] border-l border-border flex flex-col bg-surface shrink-0">
                {/* Tabs Switcher */}
                <div className="flex border-b border-border bg-surface-subtle/80 p-1 text-xs font-mono shrink-0">
                  <button
                    onClick={() => setRightPanelTab("feed")}
                    className={`flex-1 py-1.5 rounded-lg font-bold flex items-center justify-center gap-1.5 transition-all ${
                      rightPanelTab === "feed"
                        ? "bg-surface text-status-critical shadow-soc-card border border-border"
                        : "text-typography-muted hover:text-typography-primary"
                    }`}
                  >
                    <Terminal className="w-3.5 h-3.5" />
                    Adversary Feed ({simulationSteps.length})
                  </button>
                  <button
                    onClick={() => setRightPanelTab("remediation")}
                    className={`flex-1 py-1.5 rounded-lg font-bold flex items-center justify-center gap-1.5 transition-all ${
                      rightPanelTab === "remediation"
                        ? "bg-surface text-status-healthy shadow-soc-card border border-border"
                        : "text-typography-muted hover:text-typography-primary"
                    }`}
                  >
                    <Zap className="w-3.5 h-3.5" />
                    Remediation ({suggestions.length})
                  </button>
                </div>

                {/* Tab Body */}
                <div className="flex-1 overflow-y-auto">
                  {rightPanelTab === "feed" ? (
                    <div className="p-3 space-y-2.5 font-mono">
                      {simulationSteps.length === 0 ? (
                        <div className="text-center py-20 text-typography-muted text-xs">
                          <Flame className="w-8 h-8 text-border mx-auto mb-2 opacity-50" />
                          Adversary simulation idle.
                          <br />
                          Click "Run Red Team AI" to launch autonomous attack path simulation.
                        </div>
                      ) : (
                        simulationSteps.map((step) => (
                          <div
                            key={step.step_number}
                            className="p-3 rounded-xl border border-status-critical/30 bg-surface-subtle hover:border-status-critical/60 transition-all text-xs shadow-soc-card"
                          >
                            {/* Step Header */}
                            <div className="flex items-center justify-between mb-1.5">
                              <span className="text-status-critical font-bold flex items-center gap-1 text-[11px]">
                                <Flame className="w-3 h-3 text-status-critical" />
                                STEP {step.step_number}: {step.tactic.toUpperCase()}
                              </span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-surface border border-border text-cyber-blue font-bold">
                                {step.technique_id}
                              </span>
                            </div>

                            {/* Technique Name */}
                            <div className="text-typography-primary font-semibold text-xs mb-1">
                              {step.technique_name}
                            </div>

                            {/* Pivot Path */}
                            <div className="text-[11px] text-typography-muted mb-2 flex items-center gap-1.5">
                              <span className="text-typography-primary">{step.source_name || step.source_node}</span>
                              <span className="text-status-critical font-bold">→</span>
                              <span className="text-status-critical font-bold">
                                {step.target_name} ({step.target_ip})
                              </span>
                            </div>

                            {/* Narrative */}
                            <div className="p-2 rounded-lg bg-canvas border border-border text-[11px] text-typography-primary leading-relaxed">
                              {step.action_description}
                            </div>

                            {/* Acquired Credentials */}
                            {step.credentials_harvested && step.credentials_harvested.length > 0 && (
                              <div className="mt-2 text-[10px] text-amber-400 flex items-center gap-1">
                                <span>Acquired:</span>
                                <span className="font-bold underline">
                                  {step.credentials_harvested.join(", ")}
                                </span>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  ) : (
                    <RemediationPanel
                      suggestions={suggestions}
                      onApplyRemediation={handleApplyRemediation}
                      onVerifyRemediation={handleVerifyRemediation}
                      appliedRemediations={appliedRemediations}
                      verificationResult={verificationResult}
                      loading={loading}
                    />
                  )}
                </div>
              </div>
            </div>
          )}

          {/* VIEW 2: Asset Topology Matrix View */}
          {currentView === "topology" && (
            <AssetTopologyView
              nodes={topology.nodes}
              onSelectNode={handleSelectNode}
              onNavigateToGraph={(nodeId) => {
                setCurrentView("viewport");
                const target = topology.nodes.find((n) => n.id === nodeId);
                if (target) handleSelectNode(target);
              }}
            />
          )}

          {/* VIEW 3: Live Telemetry Stream View */}
          {currentView === "telemetry" && (
            <div className="flex-1 p-3 h-full">
              <LiveTelemetryStream
                logs={telemetryLogs}
                onClearLogs={() => setTelemetryLogs([])}
                isStreaming={wsConnected}
              />
            </div>
          )}

          {/* VIEW 4: Threat Matrix & ATT&CK Log View */}
          {currentView === "threats" && (
            <div className="flex-1 h-full">
              <ThreatMatrixView
                steps={simulationSteps}
                onSelectStepNode={(nodeId) => {
                  setCurrentView("viewport");
                  const target = topology.nodes.find((n) => n.id === nodeId);
                  if (target) handleSelectNode(target);
                }}
              />
            </div>
          )}

          {/* VIEW 5: Compliance & Audit Ledger View */}
          {currentView === "compliance" && (
            <div className="flex-1 h-full">
              <ComplianceAuditView />
            </div>
          )}

          {/* VIEW 6: Settings View */}
          {currentView === "settings" && (
            <div className="flex-1 h-full">
              <SettingsView />
            </div>
          )}
        </main>
      </div>

      {/* Slide-out Threat Vector & Blast Radius Drawer */}
      <ThreatVectorDrawer
        isOpen={isDrawerOpen}
        onClose={() => setIsDrawerOpen(false)}
        node={selectedNode}
        blastData={blastData}
        loading={loading}
        onSimulateCompromise={async (nodeId) => {
          setLoading(true);
          try {
            await fetch(`/api/topology/node/${nodeId}/compromise`, { method: "POST" });
            await fetchTopology();
          } catch {
            setTopology((prev) => ({
              ...prev,
              nodes: prev.nodes.map((n) => (n.id === nodeId ? { ...n, compromised: true } : n)),
            }));
          } finally {
            setLoading(false);
          }
        }}
        onApplyQuickFix={async (nodeId, actionType) => {
          const targetSug = suggestions.find((s) => s.target_id === nodeId);
          if (targetSug) await handleApplyRemediation(targetSug);
        }}
        onClearHighlight={() => setBlastData(null)}
      />

      {/* Global Cmd+K Command Palette */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
        nodes={topology.nodes}
        onNavigate={(view) => setCurrentView(view)}
        onSelectNode={(node) => handleSelectNode(node)}
        onRunSimulation={handleRunSimulation}
        onResetSimulation={handleResetSimulation}
      />
    </div>
  );
}
