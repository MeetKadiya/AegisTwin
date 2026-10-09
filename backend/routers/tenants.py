import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

try:
    from ..auth.models import Tenant, TenantAsset, ClassificationEnum, User, RoleEnum
    from ..auth.dependencies import get_current_user, require_permission
    from ..database.postgres_rls import rls_engine
except (ImportError, ValueError):
    from auth.models import Tenant, TenantAsset, ClassificationEnum, User, RoleEnum
    from auth.dependencies import get_current_user, require_permission
    from database.postgres_rls import rls_engine

logger = logging.getLogger("routers.tenants")
router = APIRouter(prefix="/api/tenants", tags=["Multi-Tenancy & RLS"])


class CreateTenantRequest(BaseModel):
    id: str
    name: str
    slug: str
    tier: Optional[str] = "ENTERPRISE"


class CreateAssetRequest(BaseModel):
    id: str
    name: str
    classification: str = "INTERNAL"
    ip_address: str
    tier: str
    tags: Optional[List[str]] = None


@router.get("", dependencies=[Depends(require_permission("manage_tenant"))])
def list_all_tenants():
    """Returns all tenants across the platform (superadmin / tenant_admin)."""
    return rls_engine.list_tenants()


@router.post("", dependencies=[Depends(require_permission("manage_tenant"))])
def create_tenant(req: CreateTenantRequest):
    """Provisions a new enterprise tenant with isolated schema/RLS context."""
    tenant = Tenant(
        id=req.id,
        name=req.name,
        slug=req.slug,
        tier=req.tier or "ENTERPRISE",
    )
    return rls_engine.create_tenant(tenant)


@router.get("/current/assets")
def list_current_tenant_assets(user: User = Depends(get_current_user)):
    """
    Returns assets strictly scoped to the caller's tenant.
    Enforces PostgreSQL Row-Level Security (RLS) isolation policy.
    """
    assets = rls_engine.list_assets(user.tenant_id)
    return {
        "tenant_id": user.tenant_id,
        "asset_count": len(assets),
        "assets": assets,
    }


@router.post("/current/assets", dependencies=[Depends(require_permission("manage_tenant"))])
def create_current_tenant_asset(
    req: CreateAssetRequest,
    user: User = Depends(get_current_user),
):
    """Registers an asset strictly within the caller's tenant boundary."""
    try:
        classification = ClassificationEnum(req.classification.upper())
    except ValueError:
        classification = ClassificationEnum.INTERNAL

    asset = TenantAsset(
        id=req.id,
        tenant_id=user.tenant_id,
        name=req.name,
        classification=classification,
        ip_address=req.ip_address,
        tier=req.tier,
        tags=req.tags or [],
    )
    return rls_engine.create_asset(user.tenant_id, asset)


@router.get("/current/assets/{asset_id}")
def get_tenant_asset(
    asset_id: str,
    user: User = Depends(get_current_user),
):
    """Fetches single asset under RLS isolation. Rejects cross-tenant access with 404."""
    asset = rls_engine.get_asset(user.tenant_id, asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found in current tenant context")
    return asset
