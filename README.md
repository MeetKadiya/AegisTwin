# AegisTwin: Enterprise AI Cyber Attack Digital Twin & SOC Platform

<div align="center">

![AegisTwin Banner](https://img.shields.io/badge/AegisTwin-Enterprise_SOC_v2.4-00F0FF?style=for-the-badge&logo=shield&logoColor=white)
![Next.js 14](https://img.shields.io/badge/Next.js_14-App_Router-black?style=for-the-badge&logo=next.js)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Neo4j](https://img.shields.io/badge/Neo4j-Graph_Engine-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)
![MITRE ATT&CK](https://img.shields.io/badge/MITRE-ATT%26CK_v14-EF4444?style=for-the-badge)
![IEC 62443](https://img.shields.io/badge/Compliance-IEC_62443_%7C_NIST_CSF_2.0-10B981?style=for-the-badge)

<p align="center">
  <b>Autonomous Red Team Adversary Simulation • Industrial IoT (OT) Digital Twin • Graph-Driven SOAR Remediation • Cryptographic Audit Ledger</b>
</p>

</div>

---

## Executive Summary

**AegisTwin** is a containerized, enterprise-grade **Cyber Attack Digital Twin and Security Operations Center (SOC)** platform. Designed for hybrid IT enterprise infrastructures and Industrial Automation & Control Systems (IACS/OT under the Purdue Model), AegisTwin enables security teams to model complex network topologies, simulate autonomous multi-hop adversary attack paths, attribute threat vectors to the **MITRE ATT&CK** framework, compute downstream compromise blast radiuses, and deploy automated zero-trust remediation playbooks.

---

## Architectural Architecture

```
                                  +-------------------------------------------------------+
                                  |            AegisTwin Enterprise SOC Frontend          |
                                  |                      (Next.js 14 / Port 3000)         |
                                  | - Electric Cyberpunk & Slate SOC Multi-Theme Engine   |
                                  | - React Flow Digital Twin Canvas (OT Telemetry Cards) |
                                  | - Global Command Palette (Cmd + K) & Live Search Bar  |
                                  | - Monospaced Real-Time Telemetry Stream Console       |
                                  | - Threat Vector & Attack Path Drawer (Blast Radius)   |
                                  +---------------------------+---------------------------+
                                                              |
                                                    WebSocket / REST API
                                                              v
                                  +-------------------------------------------------------+
                                  |             FastAPI Core Orchestration Engine         |
                                  |                        (Port 8000)                    |
                                  | - Autonomous LLM Red Team Adversary Simulation Agent  |
                                  | - MITRE ATT&CK Matrix Attribution Engine (TTPs)       |
                                  | - Topological Blast Radius BFS Risk Calculation       |
                                  | - Multi-Tenancy Row-Level Security (PostgreSQL RLS)   |
                                  | - IEC 62443 / NIST CSF 2.0 Regulatory Mapper         |
                                  | - Cryptographic SHA-256 Merkle Audit Ledger           |
                                  +---------------------------+---------------------------+
                                                              |
                                    +-------------------------+-------------------------+
                                    v                                                   v
                     +-----------------------------+                     +-----------------------------+
                     |    Neo4j Graph Database     |                     |    NATS Streaming Broker    |
                     | - Enterprise Topology Nodes |                     | - Low-Latency Pub/Sub Hub   |
                     | - Purdue Model L0-L4 Edges  |                     | - Full-Duplex WebSockets    |
                     | - Zero-Trust Blocked Paths  |                     | - SOAR Webhook Dispatcher   |
                     +-----------------------------+                     +-----------------------------+
```

---

## Key Platform Capabilities

### 1. Modern Enterprise SOC Design System
- **Slate SOC & Electric Cyberpunk Theme:** Dark-mode-first security palette featuring Deep Obsidian (`#06080F`), Slate Panels (`#0C101D`), Hairline Gridlines (`#1C273E`), Electric Cyan (`#00F0FF`), Emerald Glow (`#00E676`), and Laser Crimson (`#FF1744`).
- **Live Multi-Theme Switcher:** Switch on the fly between 5 specialized themes:
  - ⚡ **Electric Cyberpunk** *(Default — High-contrast neon obsidian)*
  - 🛡️ **Deep Cobalt SOC** *(Azure Sentinel / CrowdStrike Blue)*
  - 📟 **Matrix Emerald OT** *(Industrial SCADA Phosphor)*
  - 🚨 **Crimson Red Team** *(Adversary Breach Operations)*
  - ☀️ **Daylight Tactical** *(High-contrast daytime light mode)*
- **High Data Density:** Micro-glow indicator badges, glassmorphic dropdowns, and compact padding tailored for continuous SOC operator workflows.

### 2. Global Search & Command Palette (`Cmd + K` / `Ctrl + K`)
- **Interactive Header Search:** Real-time search bar with instant query suggestions, asset matching, IP resolution, and CVE search.
- **Deep Command Palette:** Global modal with keyboard navigation (`Arrow keys`, `Enter`, `Escape`) to instantly jump between assets, views, and automated adversary simulations.

### 3. Digital Twin Schematic Viewport ([NetworkGraph](file:///i:/AegisTwin/frontend/src/components/NetworkGraph.tsx))
- **Interactive Multi-Tier Topology:** Renders DMZ, Web Tier, App Tier, DB Tier, Active Directory (Tier 0), and OT/ICS Purdue Level 1–2 zones.
- **Live Sensor Hover Cards:** Displays real-time industrial telemetry (Core Temperature °C, Bus Voltage V, Packet Drop Rate %, CPU Load %, Active Port Listeners).
- **Dynamic Lateral Movement Edges:** Animated laser crimson paths illuminate adversary pivots; dashed gray lines indicate zero-trust segmented boundaries.

### 4. Threat Vector & Blast Radius Drawer ([ThreatVectorDrawer](file:///i:/AegisTwin/frontend/src/components/ThreatVectorDrawer.tsx))
- **"What Happens If This Host Is Compromised?" Simulator:** Breadth-first graph traversal mapping downstream reachable nodes, exposed CVEs, and crown jewels at risk.
- **MITRE ATT&CK Attribution:** Direct TTP mapping (`T1190`, `T1021.001`, `T1068`, `T1003`) with harvested credentials alerts.

### 5. High-Throughput Live Telemetry Stream ([LiveTelemetryStream](file:///i:/AegisTwin/frontend/src/components/LiveTelemetryStream.tsx))
- High-density monospaced event console with live severity pills (`INFO`, `WARN`, `CRITICAL`), channel filters (`TELEMETRY`, `SECURITY`, `SIMULATION`, `SOAR`), pause/resume toggle, auto-scroll lock, and JSON log export.

### 6. Regulatory Compliance & Merkle Ledger ([ComplianceAuditView](file:///i:/AegisTwin/frontend/src/components/ComplianceAuditView.tsx))
- Continuous automated evaluation against **IEC 62443-3-3**, **NIST CSF 2.0**, and **SOC 2 Type II**.
- Cryptographically chained SHA-256 immutable audit ledger with one-click full chain integrity verification and printable executive dossier export.

---

## Directory Structure

```text
AegisTwin/
├── backend/                       # Python FastAPI Backend Service
│   ├── agents/                    # Autonomous Red Team & Remediation Agents
│   │   ├── red_team_agent.py      # LLM & Heuristic Multi-Hop Adversary Engine
│   │   └── remediation_agent.py   # SOAR Playbook Generation & Validation
│   ├── audit/                     # Cryptographic Immutable Merkle Audit Ledger
│   │   └── immutable_audit_log.py # SHA-256 Chained Block Verification
│   ├── auth/                      # ABAC, OPA Client & Tenant Context Models
│   ├── compliance/                # IEC 62443, NIST CSF & Report Generator
│   ├── database/                  # Neo4j Graph Engine & PostgreSQL RLS
│   │   ├── neo4j_client.py        # In-Memory & Neo4j Bolt Graph Operations
│   │   └── seed_topology.py       # Enterprise Multi-Tier Seed Data
│   ├── integrations/              # SOAR Webhook & SIEM Dispatchers
│   ├── routers/                   # API Endpoints (Topology, Simulation, Stream)
│   └── streaming/                 # NATS Consumer & WebSocket Full-Duplex Hub
├── frontend/                      # Next.js 14 SOC Dashboard
│   ├── src/
│   │   ├── app/                   # App Router Pages & Global Styles
│   │   │   ├── dashboard/page.tsx # Main Bento Grid SOC Workspace
│   │   │   ├── globals.css        # Theme Variables & Glow Animations
│   │   │   └── layout.tsx         # Root Layout & Metadata
│   │   ├── components/            # UI Components
│   │   │   ├── AssetTopologyView.tsx # Purdue L0-L4 Inventory Table
│   │   │   ├── BlastRadiusModal.tsx  # Standalone Blast Simulator Modal
│   │   │   ├── CommandPalette.tsx    # Cmd+K Quick Navigation Modal
│   │   │   ├── ComplianceAuditView.tsx # IEC 62443 & SHA-256 Ledger
│   │   │   ├── GlobalHeader.tsx      # Header, Search & Theme Switcher
│   │   │   ├── LiveTelemetryStream.tsx # Real-Time Event Console
│   │   │   ├── MetricStatStrip.tsx   # Top Row KPI Cards & Sparklines
│   │   │   ├── NetworkGraph.tsx      # React Flow Digital Twin Canvas
│   │   │   ├── RemediationPanel.tsx  # Playbooks & Verification Action
│   │   │   ├── SettingsView.tsx      # SOC Parameters & SOAR Config
│   │   │   ├── SidebarNav.tsx        # Collapsible Navigation Bar
│   │   │   ├── ThreatMatrixView.tsx  # MITRE ATT&CK Matrix Breakdown
│   │   │   └── ThreatVectorDrawer.tsx # Slide-Out Blast & Sensor Drawer
│   │   └── lib/                      # Type Definitions & Mock Baseline
│   └── tailwind.config.js         # Tailwind Design Tokens & Shadows
└── docker-compose.yml             # Multi-Container Deployment Specification
```

---

## Getting Started

### Option A: Complete Platform with Docker Compose

Run the entire stack (FastAPI, Next.js, Neo4j, Redis, NATS) in one command:

```bash
docker compose up --build
```

Access the interfaces:
- **SOC Enterprise Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Neo4j Graph Browser:** [http://localhost:7474](http://localhost:7474) *(Default: `neo4j` / `aegistwin2026`)*

---

### Option B: Standalone Local Development

#### 1. Backend Service (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### 2. Frontend Application (Next.js 14)
```bash
cd frontend
npm install
npm run dev
```

Visit [http://localhost:3000](http://localhost:3000) in your browser.

---

## Verification & Automated Test Suites

AegisTwin includes automated test suites covering all operational subsystems:

### 1. Backend Simulation & Compliance Tests
```bash
cd backend
python test_simulation.py
python test_compliance_audit.py
python test_multi_tenancy_abac.py
```

### 2. Frontend Production Build & Typecheck
```bash
cd frontend
npm run build
```

Expected output:
```text
✓ Compiled successfully
✓ Linting and checking validity of types
✓ Generating static pages (5/5)
✓ Finalizing page optimization
```

---

## License

Enterprise Security Operations License. Developed for critical infrastructure and autonomous cyber defense simulations.
