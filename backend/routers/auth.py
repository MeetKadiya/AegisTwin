import logging
from typing import Optional, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

try:
    from ..auth.models import User, RoleEnum, ClassificationEnum, ABACDecision
    from ..auth.jwt_validator import oidc_validator
    from ..auth.opa_client import opa_engine
    from ..auth.dependencies import get_current_user
except (ImportError, ValueError):
    from auth.models import User, RoleEnum, ClassificationEnum, ABACDecision
    from auth.jwt_validator import oidc_validator
    from auth.opa_client import opa_engine
    from auth.dependencies import get_current_user

logger = logging.getLogger("routers.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication & ABAC"])


class LoginRequest(BaseModel):
    user_id: str = "analyst-01"
    tenant_id: str = "t-corp-001"
    email: str = "analyst@megacorp.internal"
    role: str = "analyst"  # superadmin, tenant_admin, operator, analyst, auditor
    clearance: Optional[List[str]] = None


class ABACEvalRequest(BaseModel):
    action: str
    resource: Optional[dict] = None


@router.post("/token")
def generate_token(req: LoginRequest):
    """Mints an enterprise JWT for testing or API integration matching OIDC claims."""
    token = oidc_validator.create_mock_token(
        user_id=req.user_id,
        tenant_id=req.tenant_id,
        email=req.email,
        role=req.role,
        clearance=req.clearance,
    )
    return {
        "access_token": token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "role": req.role,
        "tenant_id": req.tenant_id,
    }


@router.get("/me")
def get_user_profile(user: User = Depends(get_current_user)):
    """Returns the authenticated principal, assigned tenant, and classification clearance."""
    return {
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "clearance": [c.value for c in user.clearance],
    }


@router.post("/evaluate")
def evaluate_abac_policy(
    req: ABACEvalRequest,
    user: User = Depends(get_current_user),
) -> ABACDecision:
    """Direct dry-run policy evaluation using the OPA ABAC engine."""
    return opa_engine.evaluate(user, req.action, req.resource)
