"use client";

import React, { useState } from "react";
import {
  Settings,
  Save,
  Radio,
  Sliders,
  Webhook,
  CheckCircle2,
  Bell,
  Cpu,
  Shield,
} from "lucide-react";

export default function SettingsView() {
  const [maxHops, setMaxHops] = useState(8);
  const [stealthMode, setStealthMode] = useState(false);
  const [soarEndpoint, setSoarEndpoint] = useState("https://soar.aegis.corp/api/v1/webhook/quarantine");
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <div className="flex flex-col h-full bg-canvas p-4 space-y-4 select-none font-mono text-xs overflow-y-auto">
      {/* Header Banner */}
      <div className="p-4 rounded-xl bg-surface border border-border flex items-center justify-between shadow-soc-card">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-cyber-blue/10 border border-cyber-blue/30 text-cyber-blue shadow-glow-blue">
            <Settings className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-typography-primary">
              Security Operations Center & Adversary Engine Settings
            </h2>
            <p className="text-[11px] text-typography-muted">
              Configure autonomous Red Team agent, telemetry buffer thresholds, and SOAR automation
            </p>
          </div>
        </div>

        <button
          onClick={handleSave}
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-cyber-blue hover:bg-blue-500 active:scale-[0.98] text-white font-bold transition-all shadow-glow-blue"
        >
          {saved ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
          <span>{saved ? "Saved" : "Save Changes"}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Red Team Agent Simulation Tuning */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-4 shadow-soc-card">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <Sliders className="w-4 h-4 text-cyber-blue" />
            <h3 className="font-bold text-typography-primary text-xs">Adversary AI Simulation Parameters</h3>
          </div>

          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-typography-muted mb-1">
                <span>Maximum Attack Path Depth (Hops):</span>
                <span className="font-bold text-typography-primary">{maxHops} hops</span>
              </div>
              <input
                type="range"
                min="2"
                max="15"
                value={maxHops}
                onChange={(e) => setMaxHops(Number(e.target.value))}
                className="w-full accent-cyber-blue bg-canvas h-1.5 rounded-lg appearance-none cursor-pointer"
              />
            </div>

            <div className="flex items-center justify-between pt-2">
              <div>
                <div className="font-semibold text-typography-primary">Evasion & Stealth Simulation</div>
                <div className="text-[10px] text-typography-muted">
                  Simulate adversary defense evasion (T1036 Masquerading)
                </div>
              </div>
              <input
                type="checkbox"
                checked={stealthMode}
                onChange={(e) => setStealthMode(e.target.checked)}
                className="w-4 h-4 accent-cyber-blue rounded cursor-pointer"
              />
            </div>
          </div>
        </div>

        {/* SOAR Webhook & Security Incident Dispatch */}
        <div className="p-4 rounded-xl bg-surface border border-border space-y-4 shadow-soc-card">
          <div className="flex items-center gap-2 pb-2 border-b border-border">
            <Webhook className="w-4 h-4 text-cyber-cyan" />
            <h3 className="font-bold text-typography-primary text-xs">SOAR Webhook & Incident Response</h3>
          </div>

          <div className="space-y-3">
            <div>
              <label className="text-[10px] text-typography-muted block mb-1">
                Automated Containment Dispatch URL:
              </label>
              <input
                type="text"
                value={soarEndpoint}
                onChange={(e) => setSoarEndpoint(e.target.value)}
                className="w-full px-3 py-1.5 rounded bg-canvas border border-border text-typography-primary text-[11px] focus:outline-none focus:border-cyber-blue"
              />
            </div>

            <div className="text-[10px] text-typography-muted leading-relaxed">
              When critical crown jewels are breached or reached by lateral movement, AegisTwin dispatches an HMAC-signed JSON payload triggering automated firewall and zero-trust microsegmentation.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
