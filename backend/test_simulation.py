"""
Self-check test suite verifying graph engine, adversary simulation,
MITRE mapping, blast radius calculation, and remediation workflows.
"""
from database.neo4j_client import graph_engine
from database.seed_topology import seed_database
from agents.red_team_agent import red_team_agent
from agents.mitre_mapper import map_cve_to_mitre, get_technique_details
from routers.topology import compute_network_risk_score


def test_topology_seed_and_graph():
    res = seed_database()
    assert res["node_count"] >= 10, "Should seed at least 10 enterprise hosts"
    assert res["edge_count"] >= 10, "Should seed connections across tiers"

    topo = graph_engine.get_topology()
    nodes = {n["id"]: n for n in topo["nodes"]}
    assert "corp-dc-01" in nodes
    assert "db-cluster-01" in nodes
    assert "gw-external" in nodes
    print("[PASS] Topology seed verified.")


def test_blast_radius_computation():
    seed_database()
    blast = graph_engine.calculate_blast_radius("vpn-gateway")
    assert "blast_radius_count" in blast
    assert blast["blast_radius_count"] >= 3
    assert blast["exfiltration_risk_score"] > 0
    assert blast["risk_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    print(f"[PASS] Blast radius from VPN gateway: {blast['blast_radius_count']} reachable nodes, Risk: {blast['exfiltration_risk_score']}")


def test_mitre_mapping():
    log4shell_mitre = map_cve_to_mitre("CVE-2021-44228")
    assert log4shell_mitre["id"] == "T1190"
    assert "Initial Access" in log4shell_mitre["tactic"]

    t1003 = get_technique_details("T1003")
    assert "Credential Access" in t1003["tactic"]
    print("[PASS] MITRE ATT&CK mapping verified.")


def test_red_team_autonomous_simulation():
    seed_database()
    red_team_agent.reset()
    sim_result = red_team_agent.run_full_simulation(max_steps=5)
    assert sim_result["total_steps"] > 0
    for step in sim_result["steps"]:
        assert "technique_id" in step
        assert "target_node" in step
        assert step["success"] is True

    # Check that at least some nodes are marked compromised
    topo = graph_engine.get_topology()
    compromised = [n for n in topo["nodes"] if n.get("compromised")]
    assert len(compromised) > 0
    print(f"[PASS] Simulation executed {sim_result['total_steps']} steps. Compromised {len(compromised)} nodes.")


def test_remediation_and_verification():
    seed_database()
    # Apply patch to web-app-01
    rem = graph_engine.apply_remediation("patch_cve", "web-app-01", {"cve_id": "CVE-2021-44228"})
    assert rem["success"] is True

    web_node = graph_engine.get_node("web-app-01")
    vulns = [v["cve"] for v in web_node.get("vulnerabilities", [])]
    assert "CVE-2021-44228" not in vulns

    # Sever connection from VPN to admin jumpbox
    rem_edge = graph_engine.apply_remediation("block_edge", "vpn-gateway", {"source": "vpn-gateway", "target": "admin-workstation-01"})
    assert rem_edge["success"] is True
    print("[PASS] Remediation graph mutations verified.")


if __name__ == "__main__":
    test_topology_seed_and_graph()
    test_blast_radius_computation()
    test_mitre_mapping()
    test_red_team_autonomous_simulation()
    test_remediation_and_verification()
    print("ALL TESTS PASSED SUCCESSFULLY.")
