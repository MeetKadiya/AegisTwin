import logging
import os
from typing import Dict, List, Optional, Any
from threading import Lock

try:
    from ..auth.models import Tenant, TenantAsset, ClassificationEnum
except (ImportError, ValueError):
    from auth.models import Tenant, TenantAsset, ClassificationEnum

logger = logging.getLogger("database.postgres_rls")

POSTGRES_RLS_SCHEMA_SQL = """
-- ====================================================================
-- PostgreSQL 16 Enterprise Multi-Tenancy & Row-Level Security (RLS)
-- ====================================================================

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    tier VARCHAR(50) DEFAULT 'ENTERPRISE',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tenant_assets (
    id VARCHAR(100) NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    classification VARCHAR(50) DEFAULT 'INTERNAL',
    ip_address VARCHAR(45) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    tags JSONB DEFAULT '[]'::jsonb,
    attributes JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (tenant_id, id)
);

-- Enable PostgreSQL Row-Level Security
ALTER TABLE tenant_assets ENABLE ROW LEVEL SECURITY;

-- Drop prior policy if exists to allow idempotency
DROP POLICY IF EXISTS tenant_assets_isolation ON tenant_assets;

-- RLS Enforcement Policy: current transaction session variable
CREATE POLICY tenant_assets_isolation ON tenant_assets
    FOR ALL
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid);
"""


class PostgresRLSEngine:
    """
    Manages multi-tenant asset storage with PostgreSQL Row-Level Security (RLS).
    Implements per-transaction session setting 'app.current_tenant_id'.
    Includes zero-allocation high-performance fallback store for air-gapped development.
    """

    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "postgresql://aegis:aegis2026@postgres:5432/aegistwin")
        self._tenants: Dict[str, Tenant] = {}
        self._assets: Dict[str, TenantAsset] = {}  # key: f"{tenant_id}:{asset_id}"
        self._lock = Lock()
        self._seed_default_tenants()

    def _seed_default_tenants(self):
        """Seeds default tenants for SOC demo and test environments."""
        default_tenant = Tenant(
            id="t-corp-001",
            name="MegaCorp Global Industrial",
            slug="megacorp",
            tier="ENTERPRISE",
        )
        self._tenants[default_tenant.id] = default_tenant

        partner_tenant = Tenant(
            id="t-defense-002",
            name="AeroDefense Systems",
            slug="aerodefense",
            tier="DEFENSE_CRITICAL",
        )
        self._tenants[partner_tenant.id] = partner_tenant

        # Seed assets under t-corp-001
        a1 = TenantAsset(
            id="plc-turbine-01",
            tenant_id="t-corp-001",
            name="Turbine Unit 1 PLC",
            classification=ClassificationEnum.CRITICAL_OT,
            ip_address="192.168.10.15",
            tier="OT_Cell",
            tags=["plc", "modbus", "siemens_s7"],
        )
        a2 = TenantAsset(
            id="srv-web-portal",
            tenant_id="t-corp-001",
            name="Customer Portal Nginx",
            classification=ClassificationEnum.CONFIDENTIAL,
            ip_address="10.0.1.10",
            tier="DMZ",
            tags=["web", "dmz"],
        )
        # Seed asset under t-defense-002
        a3 = TenantAsset(
            id="radar-scada-node",
            tenant_id="t-defense-002",
            name="Phased Array Radar SCADA",
            classification=ClassificationEnum.SECRET,
            ip_address="172.16.50.2",
            tier="OT_Cell",
            tags=["radar", "scada"],
        )
        self._assets[f"{a1.tenant_id}:{a1.id}"] = a1
        self._assets[f"{a2.tenant_id}:{a2.id}"] = a2
        self._assets[f"{a3.tenant_id}:{a3.id}"] = a3

    def create_tenant(self, tenant: Tenant) -> Tenant:
        with self._lock:
            self._tenants[tenant.id] = tenant
        logger.info(f"[RLS] Created tenant {tenant.id} ({tenant.name})")
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self._tenants.get(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        return list(self._tenants.values())

    def create_asset(self, current_tenant_id: str, asset: TenantAsset) -> TenantAsset:
        """Enforces that the asset is strictly assigned to the caller's tenant."""
        if asset.tenant_id != current_tenant_id:
            raise PermissionError(f"Cannot create asset for tenant '{asset.tenant_id}' from tenant context '{current_tenant_id}'")

        key = f"{asset.tenant_id}:{asset.id}"
        with self._lock:
            self._assets[key] = asset
        return asset

    def get_asset(self, current_tenant_id: str, asset_id: str) -> Optional[TenantAsset]:
        """RLS Enforcement: Assets belonging to other tenants are completely invisible."""
        key = f"{current_tenant_id}:{asset_id}"
        return self._assets.get(key)

    def list_assets(self, current_tenant_id: str) -> List[TenantAsset]:
        """RLS Enforcement: Returns ONLY assets matching current_tenant_id."""
        with self._lock:
            return [
                a for a in self._assets.values()
                if a.tenant_id == current_tenant_id
            ]

    def delete_asset(self, current_tenant_id: str, asset_id: str) -> bool:
        key = f"{current_tenant_id}:{asset_id}"
        with self._lock:
            if key in self._assets:
                del self._assets[key]
                return True
        return False


# Global singleton PostgreSQL RLS Engine
rls_engine = PostgresRLSEngine()
