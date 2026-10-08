import os
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import httpx
try:
    from ..database.neo4j_client import graph_engine
    from .mitre_mapper import get_technique_details, map_cve_to_mitre
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from agents.mitre_mapper import get_technique_details, map_cve_to_mitre


logger = logging.getLogger("red_team_agent")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OLLAMA_URL = os.getenv("OLLAMA_URL", "")


class RedTeamSimulationEngine:
    """
    Autonomous Red Team Simulation Engine that acts as an advanced persistent threat (APT).
    Queries current topology state, evaluates attack vectors, invokes LLM / heuristic reasoning,
    and updates live compromise states with MITRE ATT&CK attribution.
    """

    def __init__(self):
        self.simulation_history: List[Dict[str, Any]] = []
        self.step_counter: int = 0
        self.acquired_credentials: List[str] = []

    def reset(self):
        self.simulation_history = []
        self.step_counter = 0
        self.acquired_credentials = []
        graph_engine.reset_compromises()

    def get_attackable_perimeter(self) -> List[Dict[str, Any]]:
        """Finds entry points accessible from external network."""
        topology = graph_engine.get_topology()
        nodes = {n["id"]: n for n in topology["nodes"]}
        perimeter = []
        for nid in ["gw-external", "web-dmz-01", "vpn-gateway"]:
            if nid in nodes and not nodes[nid].get("isolated"):
                perimeter.append(nodes[nid])
        return perimeter

    def get_candidate_attack_paths(self) -> List[Dict[str, Any]]:
        """
        Analyzes graph: for every compromised node, inspects outgoing active edges
        to uncompromised targets and catalogs viable exploits or credential pivots.
        """
        topology = graph_engine.get_topology()
        nodes = {n["id"]: n for n in topology["nodes"]}
        edges = topology["edges"]

        compromised_nodes = [n for n in nodes.values() if n.get("compromised")]

        # If no foothold yet, perimeter nodes are candidates
        if not compromised_nodes:
            candidates = []
            for p in self.get_attackable_perimeter():
                for vuln in p.get("vulnerabilities", []):
                    candidates.append({
                        "source": "EXTERNAL_ATTACKER",
                        "source_name": "Adversary Infrastructure (Internet)",
                        "target": p["id"],
                        "target_name": p.get("label", p["id"]),
                        "target_tier": p.get("tier"),
                        "vuln": vuln,
                        "type": "cve_exploit"
                    })
                if p.get("services"):
                    candidates.append({
                        "source": "EXTERNAL_ATTACKER",
                        "source_name": "Adversary Infrastructure (Internet)",
                        "target": p["id"],
                        "target_name": p.get("label", p["id"]),
                        "target_tier": p.get("tier"),
                        "vuln": None,
                        "service": p["services"][0],
                        "type": "recon_probe"
                    })
            return candidates

        # Evaluate lateral movement from compromised footholds
        candidates = []
        for c_node in compromised_nodes:
            cid = c_node["id"]
            # Look at connected outgoing edges
            for edge in edges:
                if edge["source"] == cid and edge.get("status", "active") == "active":
                    target_id = edge["target"]
                    target = nodes.get(target_id)
                    if not target:
                        continue
                    if target.get("isolated"):
                        continue

                    # If not yet compromised
                    if not target.get("compromised"):
                        # Target has unpatched vulnerabilities
                        target_vulns = target.get("vulnerabilities", [])
                        if target_vulns:
                            for v in target_vulns:
                                candidates.append({
                                    "source": cid,
                                    "source_name": c_node.get("label", cid),
                                    "target": target_id,
                                    "target_name": target.get("label", target_id),
                                    "target_tier": target.get("tier"),
                                    "vuln": v,
                                    "type": "lateral_cve_exploit"
                                })

                        # Target accessible via harvested credentials
                        cred_match = False
                        for cred in self.acquired_credentials:
                            if "admin" in cred.lower() or "deploy" in cred.lower() or "connection" in cred.lower():
                                cred_match = True
                                break

                        if cred_match or not target_vulns:
                            candidates.append({
                                "source": cid,
                                "source_name": c_node.get("label", cid),
                                "target": target_id,
                                "target_name": target.get("label", target_id),
                                "target_tier": target.get("tier"),
                                "vuln": None,
                                "type": "credential_pivot",
                                "services": target.get("services", [])
                            })

        return candidates

    def _decide_with_llm(self, candidates: List[Dict[str, Any]], current_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Calls OpenAI or Ollama LLM if configured."""
        if not OPENAI_API_KEY and not OLLAMA_URL:
            return None

        prompt = f"""
You are an autonomous Red Team AI simulating an advanced nation-state adversary.
Current Footholds: {json.dumps(current_state.get('compromised_nodes', []))}
Acquired Credentials: {json.dumps(self.acquired_credentials)}
Available Candidate Attack Paths:
{json.dumps(candidates, indent=2)}

Select the highest-impact attack step. Output strictly valid JSON matching:
{{
  "selected_target": "<target_node_id>",
  "selected_source": "<source_node_id>",
  "technique_id": "<MITRE_T_ID>",
  "action_description": "<concise tactical description of the exploit and outcome>",
  "target_impact": "<criticality impact or privilege attained>"
}}
"""
        try:
            if OPENAI_API_KEY:
                # Direct HTTP call avoiding heavy Langchain dependency
                resp = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "system", "content": "You are a cyber adversary simulation engine."},
                                     {"role": "user", "content": prompt}],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.2
                    },
                    timeout=8.0
                )
                if resp.status_code == 200:
                    return json.loads(resp.json()["choices"][0]["message"]["content"])

            elif OLLAMA_URL:
                resp = httpx.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={"model": "llama3", "prompt": prompt, "format": "json", "stream": False},
                    timeout=10.0
                )
                if resp.status_code == 200:
                    return json.loads(resp.json()["response"])
        except Exception as e:
            logger.warning(f"LLM decision failed, falling back to autonomous heuristic: {e}")

        return None

    def execute_next_step(self) -> Dict[str, Any]:
        """
        Executes one autonomous red team attack step.
        Evaluates candidate paths, executes the chosen action, updates graph state,
        and logs MITRE ATT&CK mapping.
        """
        candidates = self.get_candidate_attack_paths()

        if not candidates:
            # Check if all high-value targets are compromised or unreachable
            topology = graph_engine.get_topology()
            nodes = topology["nodes"]
            compromised = [n for n in nodes if n.get("compromised")]
            return {
                "status": "COMPLETED",
                "message": "Simulation ended: No further viable attack paths reachable from current foothold.",
                "total_steps": self.step_counter,
                "total_compromised": len(compromised)
            }

        self.step_counter += 1

        # Sort candidates by impact priority (Domain Controller / DB tier > App Tier > DMZ)
        def candidate_score(c: Dict[str, Any]) -> float:
            target_id = c["target"]
            node = graph_engine.get_node(target_id) or {}
            base = float(node.get("criticality") or 5.0)
            if c.get("vuln"):
                base += float(c["vuln"].get("cvss") or 5.0)
            return base

        candidates.sort(key=candidate_score, reverse=True)

        # Attempt LLM selection
        current_state = {
            "step": self.step_counter,
            "compromised_nodes": [n["id"] for n in graph_engine.get_topology()["nodes"] if n.get("compromised")]
        }
        llm_decision = self._decide_with_llm(candidates, current_state)

        if llm_decision and "selected_target" in llm_decision:
            chosen = next((c for c in candidates if c["target"] == llm_decision["selected_target"]), candidates[0])
            technique_id = llm_decision.get("technique_id", "T1190")
            narrative = llm_decision.get("action_description", "")
        else:
            # High-fidelity autonomous adversary heuristic
            chosen = candidates[0]
            target_node = graph_engine.get_node(chosen["target"]) or {}

            if chosen.get("vuln"):
                vuln = chosen["vuln"]
                technique_id = vuln.get("mitre", "T1190")
                narrative = (
                    f"Adversary exploited {vuln.get('cve')} ({vuln.get('title')}) "
                    f"on {target_node.get('label', chosen['target'])} [{target_node.get('ip')}]. "
                    f"Established remote code execution payload."
                )
            elif chosen["type"] == "credential_pivot":
                technique_id = "T1078"
                narrative = (
                    f"Adversary leveraged harvested credentials to authenticate against "
                    f"{target_node.get('label', chosen['target'])} via legitimate protocol. "
                    f"Gained shell access."
                )
            else:
                technique_id = "T1046"
                narrative = f"Adversary mapped open services and established foothold on {chosen['target']}."

        # Execute compromise
        target_id = chosen["target"]
        graph_engine.set_compromised(target_id, True, self.step_counter)
        target_node = graph_engine.get_node(target_id) or {}

        # Harvest new credentials from compromised target
        new_creds = target_node.get("credentials", [])
        for c in new_creds:
            if c not in self.acquired_credentials:
                self.acquired_credentials.append(c)

        mitre_info = get_technique_details(technique_id)

        # ponytail: standard ISO 8601 UTC timestamp replaces static mock string
        step_record = {
            "step_number": self.step_counter,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_node": chosen["source"],
            "source_name": chosen["source_name"],
            "target_node": target_id,
            "target_name": target_node.get("label", target_id),
            "target_ip": target_node.get("ip"),
            "target_tier": target_node.get("tier"),
            "technique_id": technique_id,
            "technique_name": mitre_info["name"],
            "tactic": mitre_info["tactic"],
            "action_description": narrative,
            "exploit_used": chosen["vuln"]["cve"] if chosen.get("vuln") else ("Service Reconnaissance" if chosen.get("type") == "recon_probe" else "Valid Accounts / Credential Pivot"),
            "credentials_harvested": new_creds,
            "mitre_details": mitre_info,
            "success": True
        }

        self.simulation_history.append(step_record)
        return {
            "status": "STEP_EXECUTED",
            "step": step_record,
            "total_compromised_count": len([n for n in graph_engine.get_topology()["nodes"] if n.get("compromised")]),
            "remaining_candidates": len(candidates) - 1
        }

    def run_full_simulation(self, max_steps: int = 10) -> Dict[str, Any]:
        """Runs the autonomous adversary loop until completion or max_steps reached."""
        steps = []
        for _ in range(max_steps):
            res = self.execute_next_step()
            if res.get("status") == "STEP_EXECUTED":
                steps.append(res["step"])
            else:
                break
        return {
            "status": "SIMULATION_FINISHED",
            "steps": steps,
            "total_steps": len(steps),
            "history": self.simulation_history
        }


# Singleton agent instance
red_team_agent = RedTeamSimulationEngine()
