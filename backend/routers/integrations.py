import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel

try:
    from ..integrations.soar_webhook_dispatcher import soar_dispatcher
except (ImportError, ValueError):
    from integrations.soar_webhook_dispatcher import soar_dispatcher

logger = logging.getLogger("routers.integrations")
router = APIRouter(prefix="/api/integrations", tags=["SOAR & ITSM Integrations"])


class ManualAlertDispatchRequest(BaseModel):
    title: str = "Host Compromise Detected"
    source_id: str = "web-dmz-01"
    mitre_technique: str = "T1190"
    mitre_name: str = "Exploit Public-Facing Application"
    severity: str = "CRITICAL"
    description: str = "Adversary established shell access via CVE-2023-38606."


class InboundRemediationWebhookPayload(BaseModel):
    incident_id: Optional[str] = None
    action_type: str  # isolate_node, patch_cve, block_edge, revoke_credential
    target_id: str
    details: Optional[Dict[str, Any]] = None


@router.post("/soar/dispatch")
async def dispatch_soar_alert(req: ManualAlertDispatchRequest):
    """
    Manually or programmatically triggers outbound security incident dispatch
    to Splunk HEC, Microsoft Sentinel, Jira, and ServiceNow.
    """
    res = await soar_dispatcher.dispatch_security_alert(req.model_dump())
    return res


@router.post("/webhook/{provider}")
async def inbound_soar_webhook(
    provider: str,
    payload: InboundRemediationWebhookPayload,
    request: Request,
    x_signature: Optional[str] = Header(None, alias="X-Aegis-Signature"),
):
    """
    Inbound closed-loop webhook:
    Executed by ServiceNow, Jira, or Splunk SOAR when a human analyst or playbook
    approves an automated containment action. Mutates graph topology, severs attack edges,
    and updates digital twin risk state in real time.
    """
    raw_body = await request.body()
    if not soar_dispatcher.verify_webhook_signature(x_signature, raw_body):
        raise HTTPException(status_code=401, detail="Invalid HMAC-SHA256 webhook signature.")

    try:
        record = await soar_dispatcher.execute_inbound_closed_loop_remediation(
            provider=provider,
            payload=payload.model_dump(),
        )
        return {
            "status": "REMEDIATION_ENFORCED",
            "message": f"Successfully enforced closed-loop action '{payload.action_type}' from {provider.upper()}.",
            "details": record,
        }
    except Exception as err:
        logger.error(f"[SOAR Webhook Error] {err}")
        raise HTTPException(status_code=400, detail=str(err))


@router.get("/soar/history")
def get_soar_integration_history():
    """Returns historical records of dispatched alerts and closed-loop remediations."""
    return {
        "dispatched_count": len(soar_dispatcher.dispatched_events),
        "remediated_count": len(soar_dispatcher.remediated_incidents),
        "recent_dispatches": soar_dispatcher.dispatched_events[-10:],
        "recent_remediations": soar_dispatcher.remediated_incidents[-10:],
    }
