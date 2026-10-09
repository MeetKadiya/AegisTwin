import asyncio
import json
import logging
import os
import time
from typing import Optional

try:
    import nats
    from nats.aio.client import Client as NATSClient
except ImportError:
    nats = None
    NATSClient = None

try:
    from .websocket_hub import ws_hub
except (ImportError, ValueError):
    from streaming.websocket_hub import ws_hub

try:
    from ..database.neo4j_client import graph_engine
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine

logger = logging.getLogger("streaming.nats")


class NATSTelemetryConsumer:
    """Consumes real-time edge telemetry from NATS JetStream, evaluates anomalies, and streams to WebSocket."""

    def __init__(self, nats_url: Optional[str] = None, subject: str = "aegistwin.telemetry.>"):
        self.nats_url = nats_url or os.getenv("NATS_URL", "nats://nats:4222")
        self.subject = subject
        self.nc: Optional[NATSClient] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self.total_consumed = 0
        self.total_anomalies = 0

    async def start(self):
        if not nats:
            logger.warning("[NATS] nats-py is not installed; running in mock/offline mode.")
            return

        self._running = True
        self._task = asyncio.create_task(self._consumer_loop())
        logger.info(f"[NATS] Background consumer scheduled for {self.nats_url}")

    async def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
        if self.nc and self.nc.is_connected:
            try:
                await self.nc.drain()
                await self.nc.close()
            except Exception:
                pass
        logger.info("[NATS] Consumer stopped cleanly.")

    async def _consumer_loop(self):
        retry_delay = 2.0
        while self._running:
            try:
                logger.info(f"[NATS] Connecting to event broker at {self.nats_url}...")
                self.nc = await nats.connect(
                    self.nats_url,
                    connect_timeout=5,
                    reconnect_time_wait=2,
                    max_reconnect_attempts=-1,
                )
                logger.info(f"[NATS] Connected successfully. Subscribing to '{self.subject}'...")
                sub = await self.nc.subscribe(self.subject, cb=self._handle_message)
                retry_delay = 2.0

                while self._running and self.nc.is_connected:
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as err:
                logger.warning(f"[NATS] Connection failure ({err}). Retrying in {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 1.5, 30.0)

    async def _handle_message(self, msg):
        self.total_consumed += 1
        try:
            # Parse JSON or string payload
            payload_str = msg.data.decode("utf-8", errors="replace")
            record = {}
            try:
                record = json.loads(payload_str)
            except json.JSONDecodeError:
                record = {
                    "raw": payload_str,
                    "subject": msg.subject,
                    "timestamp": time.time(),
                }

            source_id = record.get("source_id") or record.get("host") or "unknown"
            metrics = record.get("metrics") or []
            severity = record.get("severity") or "SEVERITY_INFO"

            # 1. Evaluate ICS/OT Anomaly Thresholds
            anomalies = self._detect_anomalies(source_id, metrics, record)

            # 2. Broadcast raw telemetry to WebSocket subscribers
            await ws_hub.broadcast("telemetry", {
                "source_id": source_id,
                "protocol": record.get("protocol", "TELEMETRY"),
                "metrics": metrics,
                "severity": severity,
                "subject": msg.subject,
                "timestamp": record.get("timestamp_ns", time.time_ns()),
            })

            # 3. If anomalies triggered, broadcast high-priority security alert & update twin
            if anomalies:
                self.total_anomalies += len(anomalies)
                for alert in anomalies:
                    logger.warning(f"[ThreatEngine] ANOMALY DETECTED: {alert['title']} on {source_id}")
                    await ws_hub.broadcast("alerts", alert)

        except Exception as e:
            logger.error(f"[NATS] Error processing message on {msg.subject}: {e}")

    def _detect_anomalies(self, source_id: str, metrics: list, record: dict) -> list:
        alerts = []
        now = time.time()

        for m in metrics:
            name = m.get("name", "")
            val = m.get("value", 0.0)

            # ICS / OT Anomaly: Critical vibration threshold exceeded (T0855 Unauthorized Command / T0836)
            if name == "vibration_rms" and val > 4.5:
                alerts.append({
                    "id": f"alt-vib-{int(now * 1000)}",
                    "title": "Industrial Turbine Critical Vibration Anomaly",
                    "source_id": source_id,
                    "metric": name,
                    "value": val,
                    "threshold": 4.5,
                    "severity": "CRITICAL",
                    "mitre_technique": "T0836",
                    "mitre_name": "Modify Parameter",
                    "description": f"Vibration reading ({val} RMS) exceeded safety threshold (4.5 RMS). Possible unauthorized setpoint tampering.",
                    "timestamp": now,
                })

            # ICS / OT Anomaly: Temperature threshold exceeded
            if name == "temperature_c" and val > 80.0:
                alerts.append({
                    "id": f"alt-temp-{int(now * 1000)}",
                    "title": "Core Temperature Exceeded Operational Envelope",
                    "source_id": source_id,
                    "metric": name,
                    "value": val,
                    "threshold": 80.0,
                    "severity": "HIGH",
                    "mitre_technique": "T0855",
                    "mitre_name": "Unauthorized Command Message",
                    "description": f"Temperature sensor ({val}°C) exceeded nominal threshold (80°C).",
                    "timestamp": now,
                })

            # Security Anomaly: Failed login spike
            if name == "failed_logins_per_min" and val > 20:
                alerts.append({
                    "id": f"alt-brute-{int(now * 1000)}",
                    "title": "High Frequency Authentication Brute Force",
                    "source_id": source_id,
                    "metric": name,
                    "value": val,
                    "threshold": 20,
                    "severity": "CRITICAL",
                    "mitre_technique": "T1110",
                    "mitre_name": "Brute Force",
                    "description": f"Failed login attempts ({val}/min) indicate active credential stuffing.",
                    "timestamp": now,
                })

        return alerts


# Singleton NATS consumer instance
nats_consumer = NATSTelemetryConsumer()
