"use client";

import React, { useState, useEffect, useCallback } from "react";
import NetworkGraph from "@/components/NetworkGraph";
import BlastRadiusModal from "@/components/BlastRadiusModal";
import RemediationPanel from "@/components/RemediationPanel";
import {
  Shield,
  ShieldAlert,
  Flame,
  Play,
  RotateCcw,
  Zap,
  Terminal,
  Activity,
  Layers,
  Database,
  Crosshair,
  TrendingDown,
  RefreshCw,
  Info,
} from "lucide-react";

export default function DashboardPage() {
  const [topology, setTopology] = useState<{ nodes: any[]; edges: any[] }>({
    nodes: [],
    edges: [],
  });
  const [riskSummary, setRiskSummary] = useState<any>({
    overall_score: 75.0,
    level: "HIGH",
    total_hosts: 12,
    compromised_count: 0,
    vulnerability_count: 8,
  });

  const [simulationSteps, setSimulationSteps] = useState<any[]>([]);
  const [selectedNode, setSelectedNode] = useState<any | null>(null);
  const [blastData, setBlastData] = useState<any | null>(null);
  const [isBlastModalOpen, setIsBlastModalOpen] = useState(false);

  const [suggestions, setSuggestions] = useState<any[]>([]);
  const [appliedRemediations, setAppliedRemediations] = useState<string[]>([]);
  const [verificationResult, setVerificationResult] = useState<any | null>(null);

  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"feed" | "remediation">("feed");

  // Fetch topology from backend
  const fetchTopology = useCallback(async () => {
    try {
      const res = await fetch("/api/topology");
      if (res.ok) {
        const data = await res.json();
        setTopology({ nodes: data.nodes || [], edges: data.edges || [] });
        if (data.risk_summary) setRiskSummary(data.risk_summary);
      }
    } catch (err) {
      console.warn("API request failed, using default simulated data:", err);
    }
  }, []);

  // Fetch remediation suggestions
  const fetchSuggestions = useCallback(async () => {
    try {
      const res = await fetch("/api/remediation/suggestions");
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
      }
    } catch (err) {
      console.warn("Failed fetching suggestions:", err);
    }
  }, []);

  // Fetch simulation history
  const fetchHistory = useCallback(async () => {
    try {
      const res = await fetch("/api/simulation/history");
      if (res.ok) {
        const data = await res.json();
        setSimulationSteps(data.steps || []);
      }
    } catch (err) {
      console.warn("Failed fetching history:", err);
    }
  }, []);

  useEffect(() => {
    fetchTopology();
    fetchSuggestions();
    fetchHistory();
  }, [fetchTopology, fetchSuggestions, fetchHistory]);

  // Handle node selection for blast radius
  const handleSelectNode = async (node: any) => {
    setSelectedNode(node);
    try {
      const res = await fetch("/api/topology/blast-radius", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ node_id: node.id }),
      });
      if (res.ok) {
        const data = await res.json();
        setBlastData(data);
        setIsBlastModalOpen(true);
      }
    } catch (err) {
      console.error("Blast radius calculation error:", err);
    }
  };

  // Run full autonomous simulation
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
        setActiveTab("feed");
      }
    } finally {
      setLoading(false);
    }
  };

  // Run single adversary step
  const handleStepSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/simulation/step", { method: "POST" });
      if (res.ok) {
        await fetchTopology();
        await fetchHistory();
        setActiveTab("feed");
      }
    } finally {
      setLoading(false);
    }
  };

  // Reset simulation state
  const handleResetSimulation = async () => {
    setLoading(true);
    try {
      await fetch("/api/simulation/reset", { method: "POST" });
      await fetchTopology();
      setSimulationSteps([]);
      setBlastData(null);
      setVerificationResult(null);
    } finally {
      setLoading(false);
    }
  };

  // Apply remediation fix
  const handleApplyRemediation = async (sug: any) => {
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
      }
    } finally {
      setLoading(false);
    }
  };

  // Verify remediation via re-simulation
  const handleVerifyRemediation = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/remediation/verify", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setVerificationResult(data);
        await fetchTopology();
        await fetchHistory();
      }
    } finally {
      setLoading(false);
    }
  };

  const getRiskScoreColor = (score: number) => {
    if (score >= 80) return "text-rose-500 bg-rose-950/40 border-rose-500/40";
    if (score >= 60) return "text-orange-500 bg-orange-950/40 border-orange-500/40";
    if (score >= 35) return "text-amber-400 bg-amber-950/40 border-amber-500/40";
    return "text-emerald-400 bg-emerald-950/40 border-emerald-500/40";
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-slate-100">
      {/* Top Header Navbar */}
      <header className="h-16 border-b border-slate-800 bg-slate-950/80 px-6 flex items-center justify-between shrink-0 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-rose-600 to-amber-500 text-white shadow-lg shadow-rose-900/30">
            <Crosshair className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base font-bold tracking-tight text-slate-100 flex items-center gap-2">
              AegisTwin
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-800 text-accent-blue border border-slate-700">
                AI Cyber Attack Digital Twin
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-mono">
              Neo4j Graph Topology • Autonomous Red Team Simulation • MITRE ATT&CK
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 font-mono text-xs">
          <button
            onClick={handleRunSimulation}
            disabled={loading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-bold transition-all shadow-md shadow-rose-950/50 disabled:opacity-50"
          >
            <Flame className="w-3.5 h-3.5" />
            Run Red Team AI
          </button>

          <button
            onClick={handleStepSimulation}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all disabled:opacity-50"
          >
            <Play className="w-3 h-3 fill-current" />
            Step Adversary
          </button>

          <button
            onClick={handleResetSimulation}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-850 hover:bg-slate-800 text-slate-300 border border-slate-700/80 transition-all disabled:opacity-50"
          >
            <RotateCcw className="w-3 h-3" />
            Reset
          </button>
        </div>
      </header>

      {/* KPI Stats Strip */}
      <section className="h-14 border-b border-slate-800 bg-slate-900/40 px-6 flex items-center justify-between text-xs font-mono shrink-0">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Posture Risk Score:</span>
            <div
              className={`px-2 py-0.5 rounded border font-bold flex items-center gap-1.5 ${getRiskScoreColor(
                riskSummary.overall_score
              )}`}
            >
              <Activity className="w-3.5 h-3.5" />
              {riskSummary.overall_score} / 100 ({riskSummary.level})
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Hosts:</span>
            <span className="text-slate-100 font-bold">{riskSummary.total_hosts}</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Compromised Footholds:</span>
            <span
              className={`font-bold ${
                riskSummary.compromised_count > 0 ? "text-rose-400 animate-pulse" : "text-emerald-400"
              }`}
            >
              {riskSummary.compromised_count}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400">Discovered CVEs:</span>
            <span className="text-amber-400 font-bold">{riskSummary.vulnerability_count}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-[11px] text-slate-400">
          <span className="flex items-center gap-1 text-slate-300">
            <Database className="w-3 h-3 text-accent-blue" />
            Neo4j Graph Store Active
          </span>
        </div>
      </section>

      {/* Main Workspace Body */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left / Center Graph Area */}
        <div className="flex-1 relative p-4 h-full">
          <NetworkGraph
            topology={topology}
            onSelectNode={handleSelectNode}
            blastRadiusData={blastData}
          />
        </div>

        {/* Right Sidebar: Feed & Remediation */}
        <div className="w-[430px] border-l border-slate-800 flex flex-col bg-slate-950/60 shrink-0">
          {/* Tabs Switcher */}
          <div className="flex border-b border-slate-800 bg-slate-900/60 p-1 text-xs font-mono">
            <button
              onClick={() => setActiveTab("feed")}
              className={`flex-1 py-2 rounded-lg font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === "feed"
                  ? "bg-slate-800 text-rose-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              Attack Telemetry ({simulationSteps.length})
            </button>
            <button
              onClick={() => setActiveTab("remediation")}
              className={`flex-1 py-2 rounded-lg font-bold flex items-center justify-center gap-1.5 transition-all ${
                activeTab === "remediation"
                  ? "bg-slate-800 text-emerald-400 shadow-sm"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              <Zap className="w-3.5 h-3.5" />
              Remediate ({suggestions.length})
            </button>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-y-auto">
            {activeTab === "feed" ? (
              <div className="p-4 space-y-3 font-mono">
                {simulationSteps.length === 0 ? (
                  <div className="text-center py-16 text-slate-500 text-xs">
                    <Flame className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
                    Adversary simulation idle.
                    <br />
                    Click "Run Red Team AI" to launch autonomous attack path simulation.
                  </div>
                ) : (
                  simulationSteps.map((step) => (
                    <div
                      key={step.step_number}
                      className="p-3.5 rounded-xl border border-rose-900/40 bg-slate-900/70 hover:border-rose-700/60 transition-all text-xs"
                    >
                      {/* Step Header */}
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-rose-400 font-bold flex items-center gap-1 text-[11px]">
                          <Flame className="w-3 h-3 text-rose-500" />
                          STEP {step.step_number}: {step.tactic.toUpperCase()}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800/80 font-bold">
                          {step.technique_id}
                        </span>
                      </div>

                      {/* Technique Name */}
                      <div className="text-slate-200 font-semibold text-xs mb-1">
                        {step.technique_name}
                      </div>

                      {/* Source -> Target Pivot */}
                      <div className="text-[11px] text-slate-400 mb-2 flex items-center gap-1.5">
                        <span className="text-slate-300">{step.source_name || step.source_node}</span>
                        <span className="text-rose-500 font-bold">→</span>
                        <span className="text-rose-300 font-bold">
                          {step.target_name} ({step.target_ip})
                        </span>
                      </div>

                      {/* Tactical Narrative */}
                      <div className="p-2 rounded-lg bg-black/40 border border-slate-800 text-[11px] text-slate-300 leading-relaxed">
                        {step.action_description}
                      </div>

                      {/* Harvested Credentials Alert */}
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

      {/* Blast Radius Simulator Modal */}
      <BlastRadiusModal
        isOpen={isBlastModalOpen}
        onClose={() => setIsBlastModalOpen(false)}
        node={selectedNode}
        blastData={blastData}
        onSimulateCompromise={async (nodeId) => {
          // Immediately step simulation from selected node
          await handleStepSimulation();
        }}
        onClearHighlight={() => setBlastData(null)}
      />
    </div>
  );
}
