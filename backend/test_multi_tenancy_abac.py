import pytest
import time
from auth.models import Tenant, User, TenantAsset, RoleEnum, ClassificationEnum
from auth.opa_client import OPAEngine
from auth.jwt_validator import OIDCTokenValidator
from database.postgres_rls import PostgresRLSEngine


def test_tenant_isolation_rls():
    engine = PostgresRLSEngine()

    t_alpha = Tenant(id="t-alpha", name="Alpha Corp", slug="alpha")
    t_beta = Tenant(id="t-beta", name="Beta Energy", slug="beta")
    engine.create_tenant(t_alpha)
    engine.create_tenant(t_beta)

    asset_alpha = TenantAsset(
        id="alpha-srv-01",
        tenant_id="t-alpha",
        name="Alpha Gateway",
        classification=ClassificationEnum.CONFIDENTIAL,
        ip_address="10.1.1.1",
        tier="DMZ",
    )
    asset_beta = TenantAsset(
        id="beta-plc-01",
        tenant_id="t-beta",
        name="Beta Substation PLC",
        classification=ClassificationEnum.CRITICAL_OT,
        ip_address="10.2.1.1",
        tier="OT_Cell",
    )

    engine.create_asset("t-alpha", asset_alpha)
    engine.create_asset("t-beta", asset_beta)

    # Cross-tenant creation rejection
    with pytest.raises(PermissionError):
        engine.create_asset("t-alpha", asset_beta)

    # RLS Isolation: Alpha only sees alpha assets
    alpha_assets = engine.list_assets("t-alpha")
    alpha_ids = [a.id for a in alpha_assets]
    assert "alpha-srv-01" in alpha_ids
    assert "beta-plc-01" not in alpha_ids

    # RLS Isolation: Beta only sees beta assets
    beta_assets = engine.list_assets("t-beta")
    beta_ids = [a.id for a in beta_assets]
    assert "beta-plc-01" in beta_ids
    assert "alpha-srv-01" not in beta_ids

    # Cross-tenant single get returns None
    assert engine.get_asset("t-alpha", "beta-plc-01") is None
    assert engine.get_asset("t-beta", "alpha-srv-01") is None


def test_opa_abac_role_restrictions():
    opa = OPAEngine()

    analyst = User(
        id="u-analyst",
        tenant_id="t-alpha",
        email="analyst@alpha.corp",
        full_name="Alice Analyst",
        role=RoleEnum.ANALYST,
    )
    operator = User(
        id="u-operator",
        tenant_id="t-alpha",
        email="operator@alpha.corp",
        full_name="Bob Operator",
        role=RoleEnum.OPERATOR,
    )
    auditor = User(
        id="u-auditor",
        tenant_id="t-alpha",
        email="auditor@alpha.corp",
        full_name="Carol Auditor",
        role=RoleEnum.AUDITOR,
    )

    res = {"id": "host-web", "tenant_id": "t-alpha", "classification": "INTERNAL"}

    # Analyst can view topology, but CANNOT run simulation or remediate
    assert opa.evaluate(analyst, "view_topology", res).allowed is True
    assert opa.evaluate(analyst, "calculate_blast_radius", res).allowed is True
    dec_sim = opa.evaluate(analyst, "run_simulation", res)
    assert dec_sim.allowed is False
    assert "read-only" in dec_sim.reason

    dec_rem = opa.evaluate(analyst, "apply_remediation", res)
    assert dec_rem.allowed is False

    # Operator CAN run simulation and remediate
    assert opa.evaluate(operator, "run_simulation", res).allowed is True
    assert opa.evaluate(operator, "apply_remediation", res).allowed is True

    # Auditor CAN view audit logs, but CANNOT mutate
    assert opa.evaluate(auditor, "view_audit_logs", res).allowed is True
    assert opa.evaluate(auditor, "step_adversary", res).allowed is False


def test_opa_abac_tenant_boundary_violation():
    opa = OPAEngine()
    user_alpha = User(
        id="u-admin",
        tenant_id="t-alpha",
        email="admin@alpha.corp",
        full_name="Alpha Admin",
        role=RoleEnum.TENANT_ADMIN,
    )
    # Resource in t-beta
    res_beta = {"id": "asset-beta-99", "tenant_id": "t-beta", "classification": "INTERNAL"}

    decision = opa.evaluate(user_alpha, "view_topology", res_beta)
    assert decision.allowed is False
    assert "Tenant boundary violation" in decision.reason


def test_opa_abac_classification_clearance():
    opa = OPAEngine()

    operator_no_ot = User(
        id="u-op-standard",
        tenant_id="t-alpha",
        email="op@alpha.corp",
        full_name="Standard Operator",
        role=RoleEnum.OPERATOR,
        clearance=[ClassificationEnum.INTERNAL, ClassificationEnum.CONFIDENTIAL],
    )
    operator_ot = User(
        id="u-op-ot",
        tenant_id="t-alpha",
        email="ot_op@alpha.corp",
        full_name="OT Operator",
        role=RoleEnum.OPERATOR,
        clearance=[ClassificationEnum.INTERNAL, ClassificationEnum.CRITICAL_OT],
    )

    ot_asset = {
        "id": "nuclear-turbine-plc-01",
        "tenant_id": "t-alpha",
        "classification": "CRITICAL_OT",
    }

    # Standard operator blocked from CRITICAL_OT asset
    dec_blocked = opa.evaluate(operator_no_ot, "modify_setpoint", ot_asset)
    assert dec_blocked.allowed is False
    assert "CRITICAL_OT" in dec_blocked.reason

    # Certified OT operator allowed
    dec_ok = opa.evaluate(operator_ot, "modify_setpoint", ot_asset)
    assert dec_ok.allowed is True


def test_oidc_jwt_token_validation():
    validator = OIDCTokenValidator()

    # Generate token with operator + ot_certified claim
    token = validator.create_mock_token(
        user_id="usr-99",
        tenant_id="t-defense",
        email="eng@defense.gov",
        role="operator",
        clearance=["CRITICAL_OT"],
        expires_in_sec=1800,
    )

    user = validator.validate_token(token)
    assert user.id == "usr-99"
    assert user.tenant_id == "t-defense"
    assert user.role == RoleEnum.OPERATOR
    assert ClassificationEnum.CRITICAL_OT in user.clearance

    # Expired token test
    expired_token = validator.create_mock_token(
        user_id="usr-99",
        tenant_id="t-defense",
        email="eng@defense.gov",
        role="operator",
        expires_in_sec=-10,
    )
    with pytest.raises(ValueError, match="Token has expired"):
        validator.validate_token(expired_token)


def test_superadmin_universal_override():
    opa = OPAEngine()
    superadmin = User(
        id="u-root",
        tenant_id="system-root",
        email="root@aegistwin.global",
        full_name="Platform Superadmin",
        role=RoleEnum.SUPERADMIN,
    )
    foreign_critical_asset = {
        "id": "top-secret-plc",
        "tenant_id": "t-foreign-tenant",
        "classification": "CRITICAL_OT",
    }
    decision = opa.evaluate(superadmin, "modify_setpoint", foreign_critical_asset)
    assert decision.allowed is True
    assert "SUPERADMIN role override" in decision.reason
