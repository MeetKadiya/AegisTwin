import pytest
from agents.mitre_mapper import map_cve_to_mitre, get_technique_details, MITRE_TECHNIQUES
from database.neo4j_client import graph_engine
from database.seed_topology import seed_database
from integrations.soar_webhook_dispatcher import SOARWebhookDispatcher


@pytest.fixture(autouse=True)
def setup_topology():
    seed_database()


def test_mitre_ics_techniques_mapping():
    # Test ICS Technique T0855
    t0855 = get_technique_details("T0855")
    assert t0855["id"] == "T0855"
    assert t0855["name"] == "Unauthorized Command Message"
    assert t0855.get("matrix") == "ICS"
    assert "Impair Process Control" in t0855["tactic"]

    # Test ICS Technique T0836
    t0836 = get_technique_details("T0836")
    assert t0836["id"] == "T0836"
    assert t0836["name"] == "Modify Parameter"
    assert t0836.get("matrix") == "ICS"

    # Test OT CVE mapping
    mapped_schneider = map_cve_to_mitre("CVE-2022-29951")
    assert mapped_schneider["id"] == "T0855"

    mapped_siemens = map_cve_to_mitre("CVE-2021-32998")
    assert mapped_siemens["id"] == "T0836"

    mapped_rockwell = map_cve_to_mitre("CVE-2023-3595")
    assert mapped_rockwell["id"] == "T0843"


def test_topological_attack_paths_calculation():
    # Calculate attack propagation paths originating from vpn-gateway
    res = graph_engine.calculate_attack_paths(start_node_id="vpn-gateway", max_depth=5)

    assert "error" not in res
    assert res["total_attack_paths_found"] > 0
    assert res["target_critical_assets_exposed"] > 0
    assert res["highest_risk_path_score"] > 60.0

    # Chokepoint analysis must identify critical intermediate node
    top_choke = res["top_chokepoint_node"]
    assert top_choke is not None
    assert top_choke["node_id"] in ["ci-cd-runner", "admin-workstation-01", "corp-dc-01", "app-srv-01"]
    assert top_choke["paths_mitigated_percentage"] > 0.0

    # Verify MITRE chain exists on paths
    first_path = res["attack_paths"][0]
    assert len(first_path["path_ids"]) >= 2
    assert "destination_asset" in first_path
    assert isinstance(first_path["mitre_chain"], list)


@pytest.mark.anyio
async def test_soar_outbound_dispatch():
    dispatcher = SOARWebhookDispatcher()
    alert = {
        "title": "ICS PLC Setpoint Tampering Anomaly",
        "source_id": "plc-turbine-01",
        "mitre_technique": "T0836",
        "mitre_name": "Modify Parameter",
        "severity": "CRITICAL",
        "description": "High vibration threshold breached under unauthorized Modbus command.",
    }

    res = await dispatcher.dispatch_security_alert(alert)
    assert res["status"] == "DISPATCH_PROCESSED"
    assert res["total_destinations"] == 4

    dispatches = res["dispatches"]
    assert "splunk" in dispatches
    assert "sentinel" in dispatches
    assert "servicenow" in dispatches
    assert "jira" in dispatches


@pytest.mark.anyio
async def test_soar_inbound_closed_loop_remediation():
    dispatcher = SOARWebhookDispatcher()

    # Pre-condition: check vpn-gateway has active outgoing edges
    topo_before = graph_engine.get_topology()
    vpn_edges_before = [
        e for e in topo_before["edges"]
        if (e["source"] == "vpn-gateway" or e["target"] == "vpn-gateway") and e["status"] == "active"
    ]
    assert len(vpn_edges_before) > 0

    # Inbound ServiceNow remediation approval
    inbound_payload = {
        "incident_id": "INC-SEC-89211",
        "action_type": "isolate_node",
        "target_id": "vpn-gateway",
        "details": {"approved_by": "SecOps Lead (ServiceNow)"},
    }

    result = await dispatcher.execute_inbound_closed_loop_remediation(
        provider="servicenow",
        payload=inbound_payload,
    )

    assert result["incident_id"] == "INC-SEC-89211"
    assert result["provider"] == "servicenow"
    assert result["action_type"] == "isolate_node"
    assert result["target_id"] == "vpn-gateway"

    # Post-condition: vpn-gateway must now be isolated and its edges blocked
    topo_after = graph_engine.get_topology()
    vpn_node = [n for n in topo_after["nodes"] if n["id"] == "vpn-gateway"][0]
    assert vpn_node.get("isolated") is True

    vpn_edges_after = [
        e for e in topo_after["edges"]
        if (e["source"] == "vpn-gateway" or e["target"] == "vpn-gateway") and e["status"] == "active"
    ]
    assert len(vpn_edges_after) == 0
