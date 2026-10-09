/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Dynamic Theme-Mapped Palette
        canvas: "var(--canvas)",
        surface: {
          DEFAULT: "var(--surface)",
          panel: "var(--surface)",
          hover: "var(--surface-hover)",
          card: "var(--surface)",
          subtle: "var(--surface-subtle)",
          elevated: "var(--surface-hover)",
        },
        border: {
          DEFAULT: "var(--border)",
          hairline: "var(--border)",
          subtle: "var(--border)",
          active: "var(--primary)",
        },
        cyber: {
          blue: "var(--primary)",
          cyan: "var(--secondary)",
          purple: "var(--secondary)",
        },
        status: {
          healthy: "var(--status-healthy)",
          warning: "var(--status-warning)",
          critical: "var(--status-critical)",
        },
        typography: {
          primary: "var(--text-primary)",
          muted: "var(--text-muted)",
          dim: "var(--text-muted)",
        },
        // Backwards compatibility aliases
        background: "var(--canvas)",
        accent: {
          blue: "var(--primary)",
          cyan: "var(--secondary)",
          red: "var(--status-critical)",
          green: "var(--status-healthy)",
          amber: "var(--status-warning)",
          purple: "var(--secondary)",
        },
      },
      fontFamily: {
        sans: ["Inter", "Geist", "Plus Jakarta Sans", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Geist Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        "glow-blue": "0 0 20px -3px var(--accent-glow)",
        "glow-cyan": "0 0 20px -3px var(--accent-glow)",
        "glow-crimson": "0 0 20px -3px rgba(255, 23, 68, 0.45)",
        "glow-amber": "0 0 20px -3px rgba(255, 179, 0, 0.4)",
        "glow-emerald": "0 0 20px -3px rgba(0, 230, 118, 0.4)",
        "soc-card": "0 4px 20px -2px rgba(0, 0, 0, 0.5)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "radar-sweep": "radar 4s linear infinite",
      },
      keyframes: {
        radar: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
    },
  },
  plugins: [],
};
