import logging
from typing import Optional, Callable, Dict, Any
from fastapi import Header, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

try:
    from .models import User, RoleEnum, ClassificationEnum
    from .jwt_validator import oidc_validator
    from .opa_client import opa_engine
    from ..database.postgres_rls import rls_engine
except (ImportError, ValueError):
    from auth.models import User, RoleEnum, ClassificationEnum
    from auth.jwt_validator import oidc_validator
    from auth.opa_client import opa_engine
    from database.postgres_rls import rls_engine

logger = logging.getLogger("auth.dependencies")
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
) -> User:
    """
    Resolves the authenticated user from OIDC/SAML Bearer JWT or fallback development headers.
    """
    if credentials and credentials.credentials:
        try:
            return oidc_validator.validate_token(credentials.credentials)
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    # Fallback to dev headers or default analyst persona for headless development
    tenant_id = x_tenant_id or "t-corp-001"
    role_str = (x_user_role or "analyst").lower()

    role = RoleEnum.ANALYST
    clearance = [ClassificationEnum.INTERNAL]
    if role_str == "superadmin":
        role = RoleEnum.SUPERADMIN
        clearance.extend([ClassificationEnum.CONFIDENTIAL, ClassificationEnum.SECRET, ClassificationEnum.CRITICAL_OT])
    elif role_str == "tenant_admin" or role_str == "admin":
        role = RoleEnum.TENANT_ADMIN
        clearance.extend([ClassificationEnum.CONFIDENTIAL, ClassificationEnum.CRITICAL_OT])
    elif role_str == "operator":
        role = RoleEnum.OPERATOR
        clearance.append(ClassificationEnum.CRITICAL_OT)
    elif role_str == "auditor":
        role = RoleEnum.AUDITOR

    return User(
        id=f"dev-{role.value}",
        tenant_id=tenant_id,
        email=f"{role.value}@{tenant_id}.corp",
        full_name=f"Dev {role.value.capitalize()}",
        role=role,
        clearance=clearance,
    )


def require_permission(action: str, resource_loader: Optional[Callable[..., Dict[str, Any]]] = None):
    """
    FastAPI dependency factory enforcing Open Policy Agent (OPA) ABAC authorization.
    """
    async def _permission_dependency(
        user: User = Depends(get_current_user),
    ):
        resource = None
        if resource_loader:
            resource = resource_loader()

        decision = opa_engine.evaluate(user, action, resource)
        if not decision.allowed:
            logger.warning(f"[ABAC DENIED] User {user.id} ({user.role.value}) -> Action '{action}': {decision.reason}")
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "ACCESS_DENIED",
                    "reason": decision.reason,
                    "action": action,
                    "tenant_id": user.tenant_id,
                    "required_policy": "OPA-ABAC-v1",
                },
            )
        return user

    return _permission_dependency
