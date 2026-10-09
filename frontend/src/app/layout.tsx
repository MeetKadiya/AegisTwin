import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AegisTwin Enterprise SOC | AI Cyber Attack Digital Twin",
  description: "Enterprise Industrial IoT & Network Digital Twin with MITRE ATT&CK Autonomous Simulation, IEC 62443 Compliance, and Graph-Driven SOAR Remediation",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-canvas text-typography-primary selection:bg-cyber-blue/30 selection:text-cyber-blue font-sans">
        {children}
      </body>
    </html>
  );
}
