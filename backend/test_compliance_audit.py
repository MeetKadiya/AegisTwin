import pytest
from audit.immutable_audit_log import ImmutableAuditLogger, GENESIS_HASH
from compliance.compliance_mapper import ComplianceEngine
from compliance.report_generator import ExecutiveReportGenerator
from database.seed_topology import seed_database


@pytest.fixture(autouse=True)
def setup_topology():
    seed_database()


def test_immutable_audit_log_append_and_chain():
    logger = ImmutableAuditLogger()
    assert logger.total_blocks == 1  # Genesis block

    # Append events
    b1 = logger.log(
        tenant_id="t-corp-001",
        actor_id="admin-01",
        action="ISOLATE_NODE",
        resource_type="HOST",
        resource_id="web-dmz-01",
        payload={"reason": "Compromised by adversary"},
    )
    assert b1.index == 1
    assert b1.previous_hash == logger.get_entries()[1]["current_hash"]

    b2 = logger.log(
        tenant_id="t-corp-001",
        actor_id="admin-01",
        action="PATCH_CVE",
        resource_type="VULNERABILITY",
        resource_id="CVE-2021-44228",
        payload={"cve": "CVE-2021-44228"},
    )
    assert b2.index == 2
    assert b2.previous_hash == b1.current_hash

    # Validate complete chain
    is_valid, msg, tampered_idx = logger.verify_chain_integrity()
    assert is_valid is True
    assert tampered_idx is None
    assert "valid and untampered" in msg


def test_immutable_audit_log_tamper_detection():
    logger = ImmutableAuditLogger()

    for i in range(4):
        logger.log(
            tenant_id="t-corp-001",
            actor_id=f"user-{i}",
            action=f"ACTION_{i}",
            resource_type="HOST",
            resource_id=f"host-{i}",
        )

    # Initial chain must be valid
    is_valid, _, _ = logger.verify_chain_integrity()
    assert is_valid is True

    # Malicious tampering: adversary secretly alters payload in block 2
    tampered_block = logger._chain[2]
    tampered_block.payload = {"tampered": "hacked_data"}

    # Verification must catch the tampering at block 2
    is_valid_after, error_msg, tampered_idx = logger.verify_chain_integrity()
    assert is_valid_after is False
    assert tampered_idx == 2
    assert "tampered" in error_msg.lower()


def test_compliance_mapping_frameworks():
    engine = ComplianceEngine()
    eval_res = engine.evaluate_compliance(tenant_id="t-corp-001")

    assert "frameworks" in eval_res
    frameworks = eval_res["frameworks"]

    # IEC 62443 verification
    assert "iec_62443" in frameworks
    iec = frameworks["iec_62443"]
    assert iec["compliance_score"] > 50.0
    assert len(iec["controls"]) >= 4

    # NIST CSF 2.0 verification
    assert "nist_csf_2" in frameworks
    nist = frameworks["nist_csf_2"]
    assert nist["compliance_score"] > 50.0
    assert len(nist["controls"]) >= 5

    # SOC 2 verification
    assert "soc2_type2" in frameworks
    soc2 = frameworks["soc2_type2"]
    assert soc2["compliance_score"] > 50.0
    assert len(soc2["controls"]) >= 4

    # Overall grade
    assert eval_res["overall_compliance_grade"] in ["A", "B"]


def test_executive_report_generation():
    generator = ExecutiveReportGenerator()

    # JSON report
    json_report = generator.generate_json_report(tenant_id="t-corp-001")
    assert "metadata" in json_report
    assert "executive_summary" in json_report
    assert "compliance_frameworks" in json_report
    assert "cryptographic_audit_ledger" in json_report
    assert json_report["cryptographic_audit_ledger"]["verified"] is True

    # HTML printable report
    html_report = generator.generate_html_report(tenant_id="t-corp-001")
    assert "<!DOCTYPE html>" in html_report
    assert "Executive Compliance & Security Audit Dossier" in html_report
    assert "CRYPTOGRAPHIC CHAIN VERIFIED" in html_report
    assert "IEC 62443" in html_report
    assert "NIST CSF 2.0" in html_report
    assert "SOC 2 Type II" in html_report
