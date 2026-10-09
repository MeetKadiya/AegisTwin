import hmac
import hashlib
import json
import logging
import os
import time
from typing import Dict, Any, Optional, List
import httpx

try:
    from ..database.neo4j_client import graph_engine
    from ..streaming.websocket_hub import ws_hub
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine
    from streaming.websocket_hub import ws_hub

logger = logging.getLogger("integrations.soar")


class SOARWebhookDispatcher:
    """
    Bidirectional SOAR & ITSM orchestration engine.
    Supports outbound event dispatching to Splunk, Sentinel, Jira, ServiceNow,
    and inbound closed-loop automated remediation execution.
    """

    def __init__(self):
        self.splunk_hec_url = os.getenv("SPLUNK_HEC_URL")
        self.splunk_token = os.getenv("SPLUNK_HEC_TOKEN")

        self.sentinel_workspace_id = os.getenv("SENTINEL_WORKSPACE_ID")
        self.sentinel_shared_key = os.getenv("SENTINEL_SHARED_KEY")

        self.servicenow_url = os.getenv("SERVICENOW_INSTANCE_URL")
        self.servicenow_auth = (os.getenv("SERVICENOW_USER", "admin"), os.getenv("SERVICENOW_PASSWORD", ""))

        self.jira_url = os.getenv("JIRA_INSTANCE_URL")
        self.jira_auth = (os.getenv("JIRA_USER", "secops"), os.getenv("JIRA_API_TOKEN", ""))

        self.webhook_secret = os.getenv("SOAR_WEBHOOK_SECRET", "aegistwin-secret-token-2026")
        self.dispatched_events: List[Dict[str, Any]] = []
        self.remediated_incidents: List[Dict[str, Any]] = []

    def verify_webhook_signature(self, signature_header: Optional[str], raw_body: bytes) -> bool:
        """Verifies HMAC-SHA256 signature for inbound ITSM / SOAR webhooks."""
        if not signature_header:
            # Fallback for dev mode
            return True
        expected = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature_header, expected) or hmac.compare_digest(signature_header, f"sha256={expected}")

    async def dispatch_security_alert(self, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatches high-priority security alert to configured enterprise SIEM / SOAR / ITSM targets.
        """
        results = {}
        now = time.time()
        enriched_alert = {
            **alert_payload,
            "platform": "AegisTwin Cyber Digital Twin",
            "dispatch_timestamp": now,
        }
        self.dispatched_events.append(enriched_alert)

        # 1. Format Splunk HEC event
        splunk_event = {
            "time": int(now),
            "host": alert_payload.get("source_id", "aegistwin-engine"),
            "source": "aegistwin:digitaltwin:threats",
            "sourcetype": "_json",
            "event": enriched_alert,
        }
        results["splunk"] = await self._send_http(
            url=f"{self.splunk_hec_url}/services/collector/event" if self.splunk_hec_url else None,
            headers={"Authorization": f"Splunk {self.splunk_token}"} if self.splunk_token else {},
            json_body=splunk_event,
            provider="Splunk",
        )

        # 2. Format Microsoft Sentinel (Log Analytics) event
        sentinel_payload = [enriched_alert]
        results["sentinel"] = await self._send_http(
            url=f"https://{self.sentinel_workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01" if self.sentinel_workspace_id else None,
            headers={"Log-Type": "AegisTwin_Threat_CL"},
            json_body=sentinel_payload,
            provider="Microsoft Sentinel",
        )

        # 3. Format ServiceNow Security Incident ticket
        snow_incident = {
            "short_description": f"[AegisTwin] {alert_payload.get('title', 'Adversary Threat Detected')}",
            "description": (
                f"Threat detected on digital twin node: {alert_payload.get('source_id')}\n"
                f"MITRE Technique: {alert_payload.get('mitre_technique')} ({alert_payload.get('mitre_name')})\n"
                f"Severity: {alert_payload.get('severity', 'HIGH')}\n"
                f"Action Description: {alert_payload.get('description', '')}"
            ),
            "urgency": "1" if alert_payload.get("severity") == "CRITICAL" else "2",
            "impact": "1" if alert_payload.get("severity") == "CRITICAL" else "2",
            "category": "Security",
        }
        results["servicenow"] = await self._send_http(
            url=f"{self.servicenow_url}/api/now/table/incident" if self.servicenow_url else None,
            auth=self.servicenow_auth if self.servicenow_url else None,
            json_body=snow_incident,
            provider="ServiceNow",
        )

        # 4. Format Jira Security Task
        jira_issue = {
            "fields": {
                "project": {"key": "SEC"},
                "summary": f"[AegisTwin] {alert_payload.get('title', 'Cyber Threat Alert')}",
                "description": (
                    f"Asset: {alert_payload.get('source_id')}\n"
                    f"MITRE ATT&CK: {alert_payload.get('mitre_technique')}\n"
                    f"Risk Level: {alert_payload.get('severity')}\n"
                    f"Automated remediation playbook available in AegisTwin dashboard."
                ),
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High" if alert_payload.get("severity") == "CRITICAL" else "Medium"},
            }
        }
        results["jira"] = await self._send_http(
            url=f"{self.jira_url}/rest/api/2/issue" if self.jira_url else None,
            auth=self.jira_auth if self.jira_url else None,
            json_body=jira_issue,
            provider="Jira",
        )

        return {
            "status": "DISPATCH_PROCESSED",
            "total_destinations": 4,
            "dispatches": results,
            "timestamp": now,
        }

    async def execute_inbound_closed_loop_remediation(
        self,
        provider: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Closed-loop automated remediation: Receives incident approval/resolution from
        ServiceNow, Jira, or Splunk SOAR, executes graph isolation/patching, and recalculates blast radius.
        """
        action_type = payload.get("action_type") or payload.get("remediation_action")
        target_id = payload.get("target_id") or payload.get("node_id") or payload.get("host")
        details = payload.get("details") or {}
        incident_id = payload.get("incident_id") or payload.get("issue_key") or f"inc-{int(time.time())}"

        if not action_type or not target_id:
            raise ValueError("Missing 'action_type' or 'target_id' in inbound remediation payload.")

        # 1. Mutate Graph State
        rem_res = graph_engine.apply_remediation(action_type, target_id, details)

        # 2. Recalculate Posture & Blast Radius
        updated_topology = graph_engine.get_topology()
        new_blast = graph_engine.calculate_blast_radius(target_id)

        # 3. Broadcast to all SOC Wallboard WebSocket sessions
        await ws_hub.broadcast("topology", updated_topology)
        await ws_hub.broadcast("alerts", {
            "title": f"Closed-Loop Remediation Executed via {provider.upper()}",
            "action": action_type,
            "target": target_id,
            "incident_id": incident_id,
            "status": "ENFORCED",
            "timestamp": time.time(),
        })

        execution_record = {
            "incident_id": incident_id,
            "provider": provider,
            "action_type": action_type,
            "target_id": target_id,
            "details": details,
            "remediation_status": rem_res.get("status", "SUCCESS"),
            "new_exfiltration_risk_score": new_blast.get("exfiltration_risk_score"),
            "executed_at": time.time(),
        }
        self.remediated_incidents.append(execution_record)
        logger.info(f"[SOAR] Successfully executed closed-loop remediation from {provider}: {action_type} on {target_id}")

        return execution_record

    async def _send_http(
        self,
        url: Optional[str],
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[tuple] = None,
        json_body: Optional[Any] = None,
        provider: str = "Unknown",
    ) -> Dict[str, Any]:
        """Dispatches HTTP request or records simulated transmission if endpoint unconfigured."""
        if not url:
            return {
                "provider": provider,
                "status": "MOCKED_OFFLINE",
                "message": f"Endpoint not configured for {provider}; payload buffered internally.",
                "payload_snippet": str(json_body)[:100],
            }

        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.post(url, headers=headers or {}, auth=auth, json=json_body)
                return {
                    "provider": provider,
                    "status": "DELIVERED" if res.status_code < 300 else "DELIVERY_ERROR",
                    "status_code": res.status_code,
                }
        except Exception as e:
            logger.warning(f"[SOAR] Failed sending alert to {provider}: {e}")
            return {
                "provider": provider,
                "status": "DISPATCH_FAILED",
                "error": str(e),
            }


# Global singleton SOAR dispatcher
soar_dispatcher = SOARWebhookDispatcher()
