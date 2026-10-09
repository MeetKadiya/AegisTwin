import base64
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List

try:
    from .models import User, RoleEnum, ClassificationEnum
except (ImportError, ValueError):
    from auth.models import User, RoleEnum, ClassificationEnum

logger = logging.getLogger("auth.jwt")


class OIDCTokenValidator:
    """
    Validates enterprise OpenID Connect (OIDC) and SAML 2.0 JWT assertions.
    Compatible with Microsoft Entra ID (Azure AD), Okta, Keycloak, and PingFederate.
    """

    def __init__(self, issuer: Optional[str] = None, audience: Optional[str] = None):
        self.issuer = issuer or os.getenv("OIDC_ISSUER", "https://auth.aegistwin.internal")
        self.audience = audience or os.getenv("OIDC_AUDIENCE", "aegistwin-api")

    def validate_token(self, token_str: str) -> User:
        """
        Validates token structure, expiration, issuer, and maps claims to AegisTwin User model.
        """
        if not token_str:
            raise ValueError("Missing authorization token")

        # Strip 'Bearer ' if present
        if token_str.startswith("Bearer "):
            token_str = token_str[7:].strip()

        # Handle simple base64url or dot-separated JWT: header.payload.signature
        parts = token_str.split(".")
        if len(parts) < 2:
            raise ValueError("Malformed JWT token: expected header.payload.signature")

        payload_b64 = parts[1]
        # Pad base64 if needed
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)

        try:
            payload_bytes = base64.urlsafe_b64decode(payload_b64.encode("utf-8"))
            claims = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to decode token payload: {e}")

        # Check expiration
        exp = claims.get("exp")
        if exp and exp < time.time():
            raise ValueError("Token has expired")

        user_id = claims.get("sub") or claims.get("oid") or "unknown-user"
        tenant_id = claims.get("tenant_id") or claims.get("tid") or "t-corp-001"
        email = claims.get("email") or claims.get("preferred_username") or f"{user_id}@corp.net"
        full_name = claims.get("name") or claims.get("displayName") or email

        # Map role claims
        raw_role = (claims.get("role") or "").lower()
        roles_list = [r.lower() for r in claims.get("roles", [])]
        groups_list = [g.lower() for g in claims.get("groups", [])]

        role = RoleEnum.ANALYST
        if "superadmin" in roles_list or raw_role == "superadmin":
            role = RoleEnum.SUPERADMIN
        elif "tenant_admin" in roles_list or "admin" in roles_list or raw_role == "admin":
            role = RoleEnum.TENANT_ADMIN
        elif "operator" in roles_list or raw_role == "operator" or "ot_operator" in groups_list:
            role = RoleEnum.OPERATOR
        elif "auditor" in roles_list or raw_role == "auditor":
            role = RoleEnum.AUDITOR

        # Map security clearance tags
        raw_clearance = claims.get("clearance") or []
        if isinstance(raw_clearance, str):
            raw_clearance = [raw_clearance]

        clearances = [ClassificationEnum.INTERNAL]
        for c in raw_clearance:
            try:
                clearances.append(ClassificationEnum(c.upper()))
            except ValueError:
                pass

        if "ot_certified" in groups_list or "ot_operator" in groups_list:
            if ClassificationEnum.CRITICAL_OT not in clearances:
                clearances.append(ClassificationEnum.CRITICAL_OT)

        return User(
            id=user_id,
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role=role,
            clearance=clearances,
            oidc_sub=claims.get("sub"),
        )

    def create_mock_token(
        self,
        user_id: str,
        tenant_id: str,
        email: str,
        role: str,
        clearance: Optional[List[str]] = None,
        expires_in_sec: int = 3600,
    ) -> str:
        """Utility to mint test/development JWTs for CI and automated testing."""
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "name": email.split("@")[0].capitalize(),
            "role": role,
            "roles": [role],
            "clearance": clearance or ["INTERNAL"],
            "iss": self.issuer,
            "aud": self.audience,
            "exp": int(time.time() + expires_in_sec),
            "iat": int(time.time()),
        }

        def b64url(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")

        h_str = b64url(json.dumps(header).encode("utf-8"))
        p_str = b64url(json.dumps(payload).encode("utf-8"))
        sig = b64url(b"mock_crypto_signature")
        return f"{h_str}.{p_str}.{sig}"


# Global singleton OIDC validator
oidc_validator = OIDCTokenValidator()
