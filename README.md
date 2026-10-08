# AegisTwin: AI Cyber Attack Digital Twin

A containerized, autonomous **AI Cyber Attack Digital Twin** platform. Simulates enterprise network topologies, maps attack paths using graph databases (Neo4j), runs autonomous LLM-driven threat simulations, attributes actions to the MITRE ATT&CK framework, and calculates real-time blast radiuses and risk remediation metrics.

---

## Architecture Overview

```
                                 +-----------------------------+
                                 | Next.js Frontend (Port 3000)|
                                 |  - React Flow Topology View |
                                 |  - Blast Radius Modal       |
                                 |  - Remediation Playbooks    |
                                 +--------------+--------------+
                                                |
                                                v
                                 +-----------------------------+
                                 |   FastAPI Backend (Port 8000)|
                                 |  - Autonomous Red Team AI   |
                                 |  - MITRE ATT&CK Engine      |
                                 |  - Risk Scoring & Playbooks |
                                 +-------+-------------+-------+
                                         |             |
                         +---------------+             +---------------+
                         v                                             v
          +-------------------------------+             +-------------------------------+
          |    Neo4j Graph Database       |             |  Redis + Celery Async Worker  |
          | - Enterprise Multi-Tier Graph |             | - Background Threat Simulation|
          | - Attack Path Traversal       |             +-------------------------------+
          +-------------------------------+
```

---

## Core Features

1. **Enterprise Network Graph Topology (Neo4j):**
   - Multi-tier seed: DMZ (`gw-external`, `web-dmz-01`, `vpn-gateway`), Web Tier (`web-app-01`, `api-gateway`), App Tier (`app-srv-01`, `app-srv-02`, `ci-cd-runner`), DB Tier (`db-cluster-01`, `db-cluster-02`), and Active Directory (`corp-dc-01`, `admin-workstation-01`).
   - Graph models: Hosts, CVEs (Log4Shell, ZeroLogon, Spring4Shell, etc.), services, cached credentials, and network edges.
   - Built-in zero-dependency in-memory graph fallback for standalone development.

2. **Autonomous AI Red Team Agent:**
   - Multi-step adversary simulation loop with dual execution engine (LLM reasoning via OpenAI/Ollama + autonomous tactical heuristic fallback).
   - Maps every exploit, pivot, and credential dump directly to **MITRE ATT&CK TTPs** (`T1190`, `T1059`, `T1078`, `T1003`, `T1068`, etc.).

3. **Interactive React Flow Attack-Path Visualization:**
   - Live visual compromise states: Clean (Green) vs Compromised (Pulse Red) vs Blast Radius (Amber).
   - "What happens if this server is compromised?" one-click simulator calculating reachable nodes, downstream assets, and exfiltration risk score (0-100).

4. **Automated Remediation & Verification:**
   - Ranked remediation suggestions (patch CVE, isolate node, sever edge, revoke credentials).
   - One-click verification re-simulation showing delta risk reduction and protection of crown jewels.

---

## Quickstart with Docker Compose

Run the entire platform with a single command:

```bash
docker compose up --build
```

- **Frontend Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI OpenAPI Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Neo4j Browser:** [http://localhost:7474](http://localhost:7474) (Credentials: `neo4j` / `aegistwin2026`)

---

## Standalone Local Development

### Backend (Python FastAPI)
```bash
cd backend
pip install -r requirements.txt
python test_simulation.py  # Run self-check tests
uvicorn main:app --reload --port 8000
```

### Frontend (Next.js 14)
```bash
cd frontend
npm install
npm run dev
```

---

## Verification & Self-Check Test Suite

The platform includes an automated test suite verifying graph initialization, adversary simulation, MITRE mapping, blast radius calculation, and remediation:

```bash
cd backend
python test_simulation.py
```
Output:
```text
[PASS] Topology seed verified.
[PASS] Blast radius from VPN gateway: 7 reachable nodes, Risk: 85.8
[PASS] MITRE ATT&CK mapping verified.
[PASS] Simulation executed 5 steps. Compromised 5 nodes.
[PASS] Remediation graph mutations verified.
ALL TESTS PASSED SUCCESSFULLY.
```
