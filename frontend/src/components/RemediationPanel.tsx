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

interface RemediationSuggestion {
  id: string;
  title: string;
  action_type: string;
  target_id: string;
  details?: any;
  category: string;
  priority: string;
  predicted_risk_reduction: number;
  mitre_reference: string;
  description: string;
}

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

  return (
    <div className="flex flex-col h-full bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md">
      {/* Panel Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
            <Wrench className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-100 flex items-center gap-1.5">
              Automated Remediation Playbooks
              <Sparkles className="w-3.5 h-3.5 text-accent-blue" />
            </h3>
            <p className="text-[11px] text-slate-400">
              Graph-driven mitigation with one-click re-simulation verification
            </p>
          </div>
        </div>

        {/* Verification Action */}
        <button
          onClick={onVerifyRemediation}
          disabled={loading || appliedRemediations.length === 0}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-semibold bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:pointer-events-none text-white transition-all shadow-md shadow-emerald-950/50"
        >
          <Play className="w-3 h-3 fill-current" />
          Verify Mitigation
        </button>
      </div>

      {/* Verification Result Banner (if active) */}
      {verificationResult && (
        <div className="p-3 mx-4 mt-4 rounded-xl border border-emerald-500/40 bg-emerald-950/30 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <div className="font-bold text-emerald-300">
                Remediation Verification Passed
              </div>
              <div className="text-[11px] text-slate-300">
                {verificationResult.crown_jewels_secured
                  ? "Adversary blocked from Active Directory & Vault."
                  : "Adversary progression restricted."}
              </div>
            </div>
          </div>
          <div className="text-right font-mono">
            <div className="text-emerald-400 font-bold flex items-center gap-1">
              <TrendingDown className="w-3.5 h-3.5" />
              -{verificationResult.risk_reduction_achieved}% Risk
            </div>
            <div className="text-[10px] text-slate-400">
              New Score: {verificationResult.current_risk_score} ({verificationResult.current_risk_level})
            </div>
          </div>
        </div>
      )}

      {/* Suggestions List */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {suggestions.length === 0 ? (
          <div className="text-center py-8 text-slate-500 text-xs font-mono">
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
                    ? "bg-slate-900/50 border-emerald-500/30 opacity-75"
                    : "bg-slate-800/40 border-slate-700 hover:border-slate-600"
                }`}
              >
                {/* Header row */}
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                    {sug.category}
                  </span>
                  <div className="flex items-center gap-1.5 text-[11px] font-mono font-bold text-emerald-400">
                    <TrendingDown className="w-3 h-3" />
                    -{sug.predicted_risk_reduction}% Risk
                  </div>
                </div>

                {/* Title */}
                <div className="text-xs font-semibold text-slate-100 mb-1">
                  {sug.title}
                </div>

                {/* Description */}
                <div className="text-[11px] text-slate-400 mb-2 leading-relaxed">
                  {sug.description}
                </div>

                {/* Footer with MITRE reference and apply action */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[10px] font-mono">
                  <span className="text-slate-400">{sug.mitre_reference}</span>

                  {isApplied ? (
                    <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                      <CheckCircle className="w-3.5 h-3.5" />
                      Applied
                    </span>
                  ) : (
                    <button
                      onClick={() => handleApply(sug)}
                      disabled={isApplying || loading}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-semibold transition-colors disabled:opacity-50"
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
