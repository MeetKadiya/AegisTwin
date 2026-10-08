import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisTwin | Autonomous AI Cyber Attack Digital Twin",
  description: "Enterprise Network Topology Threat Simulation with Neo4j and MITRE ATT&CK Mapping",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-background text-slate-100">
        {children}
      </body>
    </html>
  );
}
