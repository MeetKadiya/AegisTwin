/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#090d16",
        surface: "#111827",
        "surface-card": "#1a2234",
        border: "#24324a",
        accent: {
          blue: "#38bdf8",
          red: "#f43f5e",
          green: "#10b981",
          amber: "#f59e0b",
          purple: "#a855f7"
        }
      },
      fontFamily: {
        mono: ["JetBrains Mono", "Courier New", "monospace"]
      }
    },
  },
  plugins: [],
};
