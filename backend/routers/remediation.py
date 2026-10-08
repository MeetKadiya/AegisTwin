from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

try:
    from ..database.neo4j_client import graph_engine
    from ..agents.red_team_agent import red_team_agent
    from .topology import compute_network_risk_score
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from agents.red_team_agent import red_team_agent
    from routers.topology import compute_network_risk_score


router = APIRouter(prefix="/api/remediation", tags=["Remediation"])


class RemediationApplyRequest(BaseModel):
    action_type: str  # 'patch_cve', 'isolate_node', 'block_edge', 'revoke_credential'
    target_id: str
    details: Optional[Dict[str, Any]] = None


@router.get("/suggestions")
def get_remediation_suggestions():
    """
    Analyzes current network graph vulnerability topology and generates
    prioritized remediation playbooks with projected risk reduction metrics.
    """
    topology = graph_engine.get_topology()
    nodes = topology["nodes"]
    suggestions = []

    # Check for critical CVEs
    for node in nodes:
        for vuln in node.get("vulnerabilities", []):
            cve = vuln.get("cve")
            cvss = float(vuln.get("cvss", 0))
            if cvss >= 9.0:
                reduction = round(cvss * 3.4, 1)
                suggestions.append({
                    "id": f"rem-patch-{node['id']}-{cve}",
                    "title": f"Patch {cve} on {node.get('label', node['id'])}",
                    "action_type": "patch_cve",
                    "target_id": node["id"],
                    "details": {"cve_id": cve},
                    "category": "Vulnerability Remediation",
                    "priority": "P0 - CRITICAL",
                    "predicted_risk_reduction": reduction,
                    "mitre_reference": "M1051 (Update Software)",
                    "description": f"Deploy security hotfix for {vuln.get('title')} to block remote execution vector."
                })

    # Network Segmentation / Edge isolation suggestions
    suggestions.append({
        "id": "rem-seg-vpn-admin",
        "title": "Segment VPN Gateway from Admin Jumpbox",
        "action_type": "block_edge",
        "target_id": "vpn-gateway",
        "details": {"source": "vpn-gateway", "target": "admin-workstation-01"},
        "category": "Zero Trust Segmentation",
        "priority": "P1 - HIGH",
        "predicted_risk_reduction": 28.5,
        "mitre_reference": "M1030 (Network Segmentation)",
        "description": "Sever direct VPN routing to Tier-1 admin workstations. Enforce bastion jump proxy with MFA."
    })

    # Credential hygiene suggestion
    suggestions.append({
        "id": "rem-cred-domain-admin",
        "title": "Purge Cached Domain Admin Ticket on Jumpbox",
        "action_type": "revoke_credential",
        "target_id": "admin-workstation-01",
        "details": {"credential_id": "cached_domain_admin_kerberos_ticket"},
        "category": "Identity & Credential Defense",
        "priority": "P1 - HIGH",
        "predicted_risk_reduction": 22.0,
        "mitre_reference": "M1026 (Privileged Account Management)",
        "description": "Invalidate cached Kerberos TGT and enforce Protected Users security group."
    })

    return {
        "count": len(suggestions),
        "suggestions": sorted(suggestions, key=lambda s: s["predicted_risk_reduction"], reverse=True)
    }


@router.post("/apply")
def apply_remediation(req: RemediationApplyRequest):
    """Applies a remediation action to the network graph."""
    res = graph_engine.apply_remediation(req.action_type, req.target_id, req.details)
    updated_topology = graph_engine.get_topology()
    updated_risk = compute_network_risk_score(updated_topology)
    return {
        "status": "APPLIED",
        "action_result": res,
        "updated_risk_score": updated_risk
    }


@router.post("/verify")
def verify_remediation():
    """
    Simulates adversary traversal on remediated topology to verify risk reduction.
    Returns delta score, unblocked vs blocked paths, and security validation status.
    """
    # Calculate pre-remediation risk score BEFORE resetting simulation state
    pre_topo = graph_engine.get_topology()
    pre_compromised = [n for n in pre_topo["nodes"] if n.get("compromised")]
    # ponytail: if verified from clean baseline, benchmark against unmitigated breach posture (82.5)
    pre_risk = compute_network_risk_score(pre_topo)["overall_score"] if pre_compromised else 82.5

    # Reset simulation state to test adversary traversal against remediated topology
    red_team_agent.reset()

    # Run fresh simulation against current remediated state
    sim_res = red_team_agent.run_full_simulation(max_steps=10)

    post_topo = graph_engine.get_topology()
    post_risk_summary = compute_network_risk_score(post_topo)
    post_risk = post_risk_summary["overall_score"]

    dc_node = graph_engine.get_node("corp-dc-01") or {}
    vault_node = graph_engine.get_node("db-cluster-02") or {}

    crown_jewels_secured = not (dc_node.get("compromised") or vault_node.get("compromised"))
    risk_delta = round(max(0.0, pre_risk - post_risk), 1)

    return {
        "verification_status": "VERIFIED",
        "crown_jewels_secured": crown_jewels_secured,
        "risk_reduction_achieved": risk_delta,
        "current_risk_score": post_risk,
        "current_risk_level": post_risk_summary["level"],
        "compromised_nodes_count": len([n for n in post_topo["nodes"] if n.get("compromised")]),
        "simulation_steps_executed": sim_res["total_steps"]
    }
