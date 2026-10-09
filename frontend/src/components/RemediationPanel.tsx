"use client";

import React, { useState } from "react";
import {
  Wrench,
  ShieldCheck,
  CheckCircle,
  Play,
  TrendingDown,
  Lock,
  ArrowRight,
  Sparkles,
  Zap,
} from "lucide-react";
import { RemediationSuggestion } from "@/lib/types";

interface RemediationPanelProps {
  suggestions: RemediationSuggestion[];
  onApplyRemediation: (suggestion: RemediationSuggestion) => Promise<void>;
  onVerifyRemediation: () => Promise<void>;
  appliedRemediations: string[];
  verificationResult: any;
  loading: boolean;
}

export default function RemediationPanel({
  suggestions,
  onApplyRemediation,
  onVerifyRemediation,
  appliedRemediations,
  verificationResult,
  loading,
}: RemediationPanelProps) {
  const [applyingId, setApplyingId] = useState<string | null>(null);

  const handleApply = async (sug: RemediationSuggestion) => {
    setApplyingId(sug.id);
    try {
      await onApplyRemediation(sug);
    } finally {
      setApplyingId(null);
    }
  };

  const getPriorityBadge = (priority: string) => {
    if (priority.includes("P0") || priority.includes("CRITICAL")) {
      return (
        <span className="text-[10px] px-2 py-0.5 rounded font-mono font-bold bg-status-critical/15 text-status-critical border border-status-critical/30">
          {priority}
        </span>
      );
    }
    return (
      <span className="text-[10px] px-2 py-0.5 rounded font-mono font-semibold bg-status-warning/15 text-status-warning border border-status-warning/30">
        {priority}
      </span>
    );
  };

  return (
    <div className="flex flex-col h-full bg-surface border-l border-border select-none font-mono text-xs overflow-hidden">
      {/* Panel Header */}
      <div className="p-3.5 border-b border-border flex items-center justify-between bg-surface-subtle/80 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-status-healthy/10 border border-status-healthy/20 text-status-healthy">
            <Wrench className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-xs font-bold text-typography-primary flex items-center gap-1.5">
              Automated Remediation Playbooks
              <Sparkles className="w-3.5 h-3.5 text-cyber-blue" />
            </h3>
            <p className="text-[10px] text-typography-muted">
              Graph-driven mitigation with one-click re-simulation
            </p>
          </div>
        </div>

        {/* Verification Action */}
        <button
          onClick={onVerifyRemediation}
          disabled={loading || appliedRemediations.length === 0}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold bg-status-healthy hover:bg-emerald-500 active:scale-[0.98] disabled:opacity-40 disabled:pointer-events-none text-white transition-all shadow-glow-emerald hover:scale-[1.02]"
        >
          <Play className="w-3 h-3 fill-current" />
          Verify Mitigation
        </button>
      </div>

      {/* Verification Result Banner (if active) */}
      {verificationResult && (
        <div className="p-3 mx-3 mt-3 rounded-xl border border-status-healthy/40 bg-status-healthy/10 flex items-center justify-between text-xs shrink-0 shadow-glow-emerald">
          <div className="flex items-center gap-2.5">
            <ShieldCheck className="w-5 h-5 text-status-healthy shrink-0" />
            <div>
              <div className="font-bold text-status-healthy">
                Mitigation Simulation Verified
              </div>
              <div className="text-[10px] text-typography-primary">
                {verificationResult.crown_jewels_secured
                  ? "Adversary blocked from Active Directory & Vault."
                  : "Adversary progression restricted."}
              </div>
            </div>
          </div>
          <div className="text-right font-mono">
            <div className="text-status-healthy font-extrabold flex items-center gap-1 justify-end">
              <TrendingDown className="w-3.5 h-3.5" />
              -{verificationResult.risk_reduction_achieved}% Risk
            </div>
            <div className="text-[10px] text-typography-muted">
              New Score: {verificationResult.current_risk_score} ({verificationResult.current_risk_level})
            </div>
          </div>
        </div>
      )}

      {/* Suggestions List */}
      <div className="flex-1 p-3 overflow-y-auto space-y-2.5">
        {suggestions.length === 0 ? (
          <div className="text-center py-16 text-typography-muted text-xs">
            <ShieldCheck className="w-8 h-8 text-status-healthy mx-auto mb-2 opacity-60" />
            No pending remediation actions. Network graph is fully hardened.
          </div>
        ) : (
          suggestions.map((sug) => {
            const isApplied = appliedRemediations.includes(sug.id);
            const isApplying = applyingId === sug.id;

            return (
              <div
                key={sug.id}
                className={`p-3 rounded-xl border transition-all ${
                  isApplied
                    ? "bg-surface-subtle/50 border-status-healthy/30 opacity-75"
                    : "bg-surface border-border hover:border-cyber-blue/50"
                }`}
              >
                {/* Header row */}
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    {getPriorityBadge(sug.priority)}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-subtle text-typography-muted border border-border">
                      {sug.category}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-[11px] font-mono font-bold text-status-healthy">
                    <TrendingDown className="w-3.5 h-3.5" />
                    -{sug.predicted_risk_reduction}% Risk
                  </div>
                </div>

                {/* Title */}
                <div className="text-xs font-semibold text-typography-primary mb-1">
                  {sug.title}
                </div>

                {/* Description */}
                <div className="text-[11px] text-typography-muted mb-2 leading-relaxed">
                  {sug.description}
                </div>

                {/* Footer with MITRE reference and apply action */}
                <div className="flex items-center justify-between pt-2 border-t border-border/60 text-[10px]">
                  <span className="text-cyber-cyan">{sug.mitre_reference}</span>

                  {isApplied ? (
                    <span className="flex items-center gap-1 text-status-healthy font-bold">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Applied
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApply(sug)}
                      disabled={isApplying || loading}
                      className="flex items-center gap-1 px-3 py-1 rounded-md bg-cyber-blue hover:bg-blue-500 active:scale-[0.98] text-white font-bold transition-all shadow-glow-blue disabled:opacity-50 hover:scale-[1.02]"
                    >
                      <Zap className="w-3 h-3" />
                      {isApplying ? "Deploying..." : "Apply Fix"}
                    </button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
