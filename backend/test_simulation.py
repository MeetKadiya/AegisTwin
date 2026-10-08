"""
Self-check test suite verifying graph engine, adversary simulation,
MITRE mapping, blast radius calculation, and remediation workflows.
"""
from database.neo4j_client import graph_engine
from database.seed_topology import seed_database
from agents.red_team_agent import red_team_agent
from agents.mitre_mapper import map_cve_to_mitre, get_technique_details
from routers.topology import compute_network_risk_score
from routers.remediation import verify_remediation


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


def test_remediation_credential_and_isolation():
    seed_database()
    # Test isolation
    iso_res = graph_engine.apply_remediation("isolate_node", "web-dmz-01")
    assert iso_res["success"] is True
    node = graph_engine.get_node("web-dmz-01")
    assert node.get("isolated") is True
    edges = [e for e in graph_engine.edges if e["source"] == "web-dmz-01" or e["target"] == "web-dmz-01"]
    assert all(e.get("status") == "blocked" for e in edges)

    # Test credential revocation on host
    cred_res = graph_engine.apply_remediation(
        "revoke_credential",
        "admin-workstation-01",
        {"credential_id": "cached_domain_admin_kerberos_ticket"}
    )
    assert cred_res["success"] is True
    admin_node = graph_engine.get_node("admin-workstation-01")
    assert "cached_domain_admin_kerberos_ticket" not in admin_node.get("credentials", [])
    conn_edges = [e for e in graph_engine.edges if e["source"] == "admin-workstation-01"]
    assert not any(e.get("status") == "revoked" for e in conn_edges)
    print("[PASS] Isolation and credential revocation mutations verified.")


def test_adversary_credential_pivot_and_termination():
    seed_database()
    red_team_agent.reset()

    # Pre-seed foothold on app server with database connection string
    graph_engine.set_compromised("app-srv-01", True, 1)
    red_team_agent.acquired_credentials = ["db_master_connection_string"]

    # Target db-cluster-01 via credential pivot
    step_res = red_team_agent.execute_next_step()
    assert step_res["status"] == "STEP_EXECUTED"
    assert step_res["step"]["target_node"] == "db-cluster-01"
    assert step_res["step"]["technique_id"] == "T1078"

    # Fully sever remaining network and verify clean termination
    for edge in graph_engine.edges:
        edge["status"] = "blocked"

    term_res = red_team_agent.execute_next_step()
    assert term_res["status"] == "COMPLETED"
    assert "No further viable attack paths" in term_res["message"]
    print("[PASS] Credential pivoting and simulation termination verified.")


def test_remediation_verification_delta():
    seed_database()
    red_team_agent.reset()

    # Run unmitigated attack
    red_team_agent.run_full_simulation(max_steps=5)

    # Apply critical fixes: segment VPN from internal networks and patch DC Zerologon
    graph_engine.apply_remediation("block_edge", "vpn-gateway", {"source": "vpn-gateway", "target": "admin-workstation-01"})
    graph_engine.apply_remediation("block_edge", "vpn-gateway", {"source": "vpn-gateway", "target": "ci-cd-runner"})
    graph_engine.apply_remediation("patch_cve", "corp-dc-01", {"cve_id": "CVE-2020-1472"})

    # Run verification re-simulation
    verify_res = verify_remediation()
    assert verify_res["verification_status"] == "VERIFIED"
    assert verify_res["crown_jewels_secured"] is True
    assert verify_res["risk_reduction_achieved"] > 0
    print(f"[PASS] Verification confirmed risk reduction: -{verify_res['risk_reduction_achieved']}%")


def test_edge_cases_and_zero_division():
    # 1. Invalid node ID in blast radius
    blast = graph_engine.calculate_blast_radius("non-existent-host")
    assert "error" in blast

    # 2. Blast radius on isolated node (hops must be 0, reachable count == 1)
    seed_database()
    graph_engine.apply_remediation("isolate_node", "web-dmz-01")
    iso_blast = graph_engine.calculate_blast_radius("web-dmz-01")
    assert iso_blast["blast_radius_count"] == 1

    # 3. Empty topology risk score
    empty_risk = compute_network_risk_score({"nodes": []})
    assert empty_risk["overall_score"] == 0.0

    # 4. Zero criticality nodes (must not raise ZeroDivisionError)
    zero_crit_topo = {
        "nodes": [{"id": "n1", "criticality": 0.0, "compromised": False, "vulnerabilities": []}]
    }
    zero_risk = compute_network_risk_score(zero_crit_topo)
    assert zero_risk["overall_score"] >= 0.0
    print("[PASS] Boundary conditions and zero-division safety verified.")


if __name__ == "__main__":
    test_topology_seed_and_graph()
    test_blast_radius_computation()
    test_mitre_mapping()
    test_red_team_autonomous_simulation()
    test_remediation_and_verification()
    test_remediation_credential_and_isolation()
    test_adversary_credential_pivot_and_termination()
    test_remediation_verification_delta()
    test_edge_cases_and_zero_division()
    print("ALL TESTS PASSED SUCCESSFULLY.")
