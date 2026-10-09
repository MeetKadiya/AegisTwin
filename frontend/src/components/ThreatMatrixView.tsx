"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Flame,
  Crosshair,
  ArrowRight,
  Key,
  Layers,
  Terminal,
  Clock,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { SimulationStep } from "@/lib/types";

interface ThreatMatrixViewProps {
  steps: SimulationStep[];
  onSelectStepNode?: (nodeId: string) => void;
}

export default function ThreatMatrixView({
  steps,
  onSelectStepNode,
}: ThreatMatrixViewProps) {
  const [selectedTactic, setSelectedTactic] = useState<string>("ALL");

  const tacticsList = [
    "ALL",
    "Initial Access",
    "Execution",
    "Privilege Escalation",
    "Credential Access",
    "Lateral Movement",
    "Collection",
    "Exfiltration",
  ];

  const filteredSteps = steps.filter((step) => {
    if (selectedTactic !== "ALL" && step.tactic.toLowerCase() !== selectedTactic.toLowerCase()) {
      return false;
    }
    return true;
  });

  // Calculate technique distribution
  const techniqueCounts: Record<string, number> = {};
  steps.forEach((s) => {
    const key = `${s.technique_id} - ${s.technique_name}`;
    techniqueCounts[key] = (techniqueCounts[key] || 0) + 1;
  });

  return (
    <div className="flex flex-col h-full bg-canvas p-4 space-y-4 select-none font-mono text-xs overflow-y-auto">
      {/* Header Banner */}
      <div className="p-4 rounded-xl bg-surface border border-border flex flex-wrap items-center justify-between gap-4 shadow-soc-card">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-status-critical/15 border border-status-critical/30 text-status-critical shadow-glow-crimson">
            <ShieldAlert className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-typography-primary flex items-center gap-2">
              Autonomous Adversary Execution & MITRE ATT&CK Matrix
              <span className="text-[10px] px-2 py-0.5 rounded bg-status-critical/20 text-status-critical border border-status-critical/40 font-bold">
                {steps.length} Attack Steps
              </span>
            </h2>
            <p className="text-[11px] text-typography-muted">
              Deterministic adversary traversal across Neo4j topology • Kill-chain attribution
            </p>
          </div>
        </div>

        {/* Tactical Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {tacticsList.map((tactic) => (
            <button
              key={tactic}
              onClick={() => setSelectedTactic(tactic)}
              className={`px-2.5 py-1 rounded-md border text-[11px] transition-colors ${
                selectedTactic === tactic
                  ? "bg-status-critical/20 text-status-critical border-status-critical/50 font-bold"
                  : "bg-surface-subtle text-typography-muted border-border hover:text-typography-primary hover:bg-surface-hover"
              }`}
            >
              {tactic}
            </button>
          ))}
        </div>
      </div>

      {/* MITRE ATT&CK Tactics Grid Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-2">
        {[
          { name: "Reconnaissance", id: "TA0043", hits: 0 },
          { name: "Initial Access", id: "TA0001", hits: steps.filter(s => s.tactic.includes("Initial")).length },
          { name: "Execution", id: "TA0002", hits: steps.filter(s => s.tactic.includes("Execution")).length },
          { name: "Priv Escalation", id: "TA0004", hits: steps.filter(s => s.tactic.includes("Privilege")).length },
          { name: "Defense Evasion", id: "TA0005", hits: 0 },
          { name: "Credential Access", id: "TA0006", hits: steps.filter(s => s.tactic.includes("Credential")).length },
          { name: "Lateral Movement", id: "TA0008", hits: steps.filter(s => s.tactic.includes("Lateral")).length },
          { name: "Exfiltration", id: "TA0010", hits: steps.filter(s => s.tactic.includes("Exfiltration")).length },
        ].map((tac, idx) => (
          <div
            key={idx}
            className={`p-2.5 rounded-lg border text-center transition-all ${
              tac.hits > 0
                ? "bg-status-critical/10 border-status-critical/40 shadow-glow-crimson"
                : "bg-surface border-border opacity-60"
            }`}
          >
            <div className="text-[9px] text-typography-muted">{tac.id}</div>
            <div className="text-[11px] font-bold text-typography-primary truncate mt-0.5">
              {tac.name}
            </div>
            <div
              className={`text-sm font-extrabold mt-1 ${
                tac.hits > 0 ? "text-status-critical" : "text-typography-muted"
              }`}
            >
              {tac.hits}
            </div>
          </div>
        ))}
      </div>

      {/* Kill Chain Event Cards Timeline */}
      <div className="space-y-3">
        {filteredSteps.length === 0 ? (
          <div className="text-center py-20 bg-surface border border-border rounded-xl text-typography-muted">
            <Flame className="w-8 h-8 mx-auto mb-2 text-border" />
            No attack steps matching current tactic filter.
          </div>
        ) : (
          filteredSteps.map((step) => (
            <div
              key={step.step_number}
              className="p-4 rounded-xl border border-status-critical/30 bg-surface hover:border-status-critical/60 transition-all shadow-soc-card flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              {/* Left Column: Step & MITRE */}
              <div className="space-y-1.5 flex-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded bg-status-critical/20 text-status-critical border border-status-critical/40 font-bold text-[10px]">
                    STEP {step.step_number}
                  </span>
                  <span className="text-cyber-cyan font-bold text-xs uppercase tracking-wider">
                    {step.tactic}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-canvas border border-border text-cyber-blue font-bold text-[10px]">
                    {step.technique_id}
                  </span>
                  <span className="text-typography-primary font-semibold text-xs">
                    {step.technique_name}
                  </span>
                </div>

                {/* Traversal Pivot: Source -> Target */}
                <div className="flex items-center gap-2 text-xs pt-1">
                  <span className="text-typography-muted">{step.source_name || step.source_node}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-status-critical" />
                  <span className="text-status-critical font-bold">
                    {step.target_name} ({step.target_ip})
                  </span>
                </div>

                {/* Narrative */}
                <div className="p-2.5 rounded-lg bg-canvas border border-border text-typography-primary leading-relaxed text-[11px] mt-1.5">
                  {step.action_description}
                </div>
              </div>

              {/* Right Column: Acquired Credentials & Actions */}
              <div className="shrink-0 flex flex-col items-end gap-2">
                {step.credentials_harvested && step.credentials_harvested.length > 0 && (
                  <div className="p-2 rounded-lg bg-status-warning/10 border border-status-warning/30 text-amber-300 text-[10px] space-y-1">
                    <div className="font-bold flex items-center gap-1">
                      <Key className="w-3 h-3 text-status-warning" />
                      Acquired Credentials:
                    </div>
                    {step.credentials_harvested.map((c, i) => (
                      <div key={i} className="font-mono underline text-amber-400">
                        {c}
                      </div>
                    ))}
                  </div>
                )}

                {onSelectStepNode && (
                  <button
                    onClick={() => onSelectStepNode(step.target_node)}
                    className="px-3 py-1.5 rounded-lg bg-surface-subtle hover:bg-surface-hover border border-border text-cyber-blue hover:text-cyber-cyan text-xs font-semibold flex items-center gap-1.5 transition-colors"
                  >
                    <Crosshair className="w-3.5 h-3.5" />
                    Inspect Target Node
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
