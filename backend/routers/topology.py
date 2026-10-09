from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

try:
    from ..database.neo4j_client import graph_engine
    from ..database.seed_topology import seed_database
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from database.seed_topology import seed_database


router = APIRouter(prefix="/api/topology", tags=["Topology"])


class BlastRadiusRequest(BaseModel):
    node_id: str


def compute_network_risk_score(topology: Dict[str, Any]) -> Dict[str, Any]:
    """Calculates overall network risk score based on asset criticality, exposed CVEs, and compromises."""
    nodes = topology.get("nodes", [])
    if not nodes:
        return {"overall_score": 0.0, "level": "LOW", "compromised_assets": 0}

    total_crit = sum(float(n.get("criticality") or 5.0) for n in nodes) or 1.0
    compromised = [n for n in nodes if n.get("compromised")]
    comp_crit = sum(float(n.get("criticality") or 5.0) for n in compromised)

    vulns_cvss = []
    for n in nodes:
        for v in n.get("vulnerabilities", []):
            vulns_cvss.append(float(v.get("cvss") or 5.0))

    avg_cvss = (sum(vulns_cvss) / len(vulns_cvss)) if vulns_cvss else 0.0
    compromise_ratio = len(compromised) / len(nodes)
    critical_compromised = any(float(n.get("criticality") or 0) >= 9.0 for n in compromised)

    score = (compromise_ratio * 40.0) + ((comp_crit / total_crit) * 30.0) + (avg_cvss * 3.0)
    if critical_compromised:
        score += 20.0

    final_score = round(min(100.0, max(0.0, score)), 1)
    if final_score >= 80:
        level = "CRITICAL"
    elif final_score >= 60:
        level = "HIGH"
    elif final_score >= 35:
        level = "MEDIUM"
    else:
        level = "LOW"

    return {
        "overall_score": final_score,
        "level": level,
        "total_hosts": len(nodes),
        "compromised_count": len(compromised),
        "vulnerability_count": len(vulns_cvss)
    }


@router.get("")
def get_topology():
    """Returns the current digital twin network graph topology."""
    topology = graph_engine.get_topology()
    risk = compute_network_risk_score(topology)
    return {
        "nodes": topology["nodes"],
        "edges": topology["edges"],
        "risk_summary": risk
    }


@router.post("/seed")
def seed_network():
    """Initializes or resets the digital twin network topology."""
    res = seed_database()
    return {"message": "Network seeded successfully", "details": res}


class AttackPathsRequest(BaseModel):
    node_id: str
    target_node_id: Optional[str] = None
    max_depth: Optional[int] = 5


@router.post("/blast-radius")
def calculate_blast_radius(req: BlastRadiusRequest):
    """Calculates the downstream compromise blast radius for a given host."""
    res = graph_engine.calculate_blast_radius(req.node_id)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.post("/attack-paths")
def calculate_attack_paths(req: AttackPathsRequest):
    """Calculates topological lateral movement attack propagation paths to critical targets."""
    res = graph_engine.calculate_attack_paths(req.node_id, req.target_node_id, req.max_depth or 5)
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res


@router.get("/node/{node_id}")
def get_node_details(node_id: str):
    """Returns detailed asset information for a single node."""
    node = graph_engine.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Host node not found")
    return node


@router.post("/node/{node_id}/compromise")
def compromise_node(node_id: str):
    """Directly sets a host as compromised for what-if adversary simulation scenarios."""
    node = graph_engine.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Host node not found")
    graph_engine.set_compromised(node_id, True)
    return {"status": "COMPROMISED", "node_id": node_id}
