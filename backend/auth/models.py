import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RoleEnum(str, Enum):
    SUPERADMIN = "superadmin"
    TENANT_ADMIN = "tenant_admin"
    OPERATOR = "operator"
    ANALYST = "analyst"
    AUDITOR = "auditor"


class ClassificationEnum(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    CRITICAL_OT = "CRITICAL_OT"  # Purdue Level 1/2 ICS Assets (PLCs, RTUs, SCADA)


class Tenant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    tier: str = "ENTERPRISE"
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    email: str
    full_name: str
    role: RoleEnum = RoleEnum.ANALYST
    clearance: List[ClassificationEnum] = Field(default_factory=lambda: [ClassificationEnum.INTERNAL])
    oidc_sub: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TenantAsset(BaseModel):
    id: str
    tenant_id: str
    name: str
    classification: ClassificationEnum = ClassificationEnum.INTERNAL
    ip_address: str
    tier: str  # DMZ, Web, App, DB, OT_Cell
    tags: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ABACDecision(BaseModel):
    allowed: bool
    reason: str
    user_id: str
    tenant_id: str
    action: str
    resource_id: Optional[str] = None
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
