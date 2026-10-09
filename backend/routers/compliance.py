import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import HTMLResponse

try:
    from ..compliance.compliance_mapper import compliance_engine
    from ..compliance.report_generator import report_generator
    from ..audit.immutable_audit_log import audit_logger
    from ..auth.models import User
    from ..auth.dependencies import get_current_user, require_permission
except (ImportError, ValueError):
    from compliance.compliance_mapper import compliance_engine
    from compliance.report_generator import report_generator
    from audit.immutable_audit_log import audit_logger
    from auth.models import User
    from auth.dependencies import get_current_user, require_permission

logger = logging.getLogger("routers.compliance")
router = APIRouter(prefix="/api/compliance", tags=["Compliance & Audit"])


@router.get("/status")
def get_compliance_status(user: User = Depends(get_current_user)):
    """
    Evaluates live digital twin state against IEC 62443, NIST CSF 2.0,
    and SOC 2 Type II trust criteria for the caller's tenant.
    """
    return compliance_engine.evaluate_compliance(tenant_id=user.tenant_id)


@router.get("/audit-trail")
def get_audit_trail(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
):
    """
    Returns cryptographically chained immutable audit records.
    Accessible to auditors and administrators.
    """
    entries = audit_logger.get_entries(
        tenant_id=user.tenant_id,
        limit=limit,
        offset=offset,
    )
    return {
        "tenant_id": user.tenant_id,
        "total_ledger_blocks": audit_logger.total_blocks,
        "returned_count": len(entries),
        "audit_blocks": entries,
    }


@router.get("/audit-trail/verify")
def verify_audit_ledger_integrity(user: User = Depends(get_current_user)):
    """
    Performs full SHA-256 cryptographic verification of the audit chain from genesis to head.
    Detects any block mutation, deletion, or insertion attempt.
    """
    is_valid, msg, tampered_idx = audit_logger.verify_chain_integrity()
    return {
        "status": "VERIFIED" if is_valid else "CORRUPTED",
        "is_valid": is_valid,
        "total_blocks_verified": audit_logger.total_blocks,
        "message": msg,
        "tampered_block_index": tampered_idx,
    }


@router.get("/report")
def get_executive_report(user: User = Depends(get_current_user)):
    """Compiles complete executive regulatory compliance dossier in structured JSON."""
    return report_generator.generate_json_report(tenant_id=user.tenant_id)


@router.get("/report/export", response_class=HTMLResponse)
def export_printable_compliance_report(user: User = Depends(get_current_user)):
    """
    One-click export of styled executive compliance and audit report.
    Printable or saveable directly to PDF via standard browser print dialog.
    """
    html_content = report_generator.generate_html_report(tenant_id=user.tenant_id)
    return HTMLResponse(content=html_content)
