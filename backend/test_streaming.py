import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from streaming.websocket_hub import WebSocketHub, ClientSession
from streaming.nats_consumer import NATSTelemetryConsumer


@pytest.mark.anyio
async def test_websocket_hub_registration():
    hub = WebSocketHub()
    mock_ws = AsyncMock()

    session = await hub.register(mock_ws, "test-client-1")
    assert session.client_id == "test-client-1"
    assert session.is_active is True
    assert hub.stats()["active_connections"] == 1

    await hub.unregister("test-client-1")
    assert hub.stats()["active_connections"] == 0
    assert session.is_active is False


@pytest.mark.anyio
async def test_websocket_hub_subscription_filtering():
    hub = WebSocketHub()
    mock_ws_all = AsyncMock()
    mock_ws_alerts = AsyncMock()

    s_all = await hub.register(mock_ws_all, "client-all")
    s_alerts = await hub.register(mock_ws_alerts, "client-alerts")

    # Set specific subscription
    hub.update_subscriptions("client-alerts", {"alerts"})

    # Broadcast on telemetry topic
    await hub.broadcast("telemetry", {"msg": "telemetry_data"})
    await asyncio.sleep(0.05)

    # client-all should receive it (has "*"), client-alerts should not
    assert s_all.messages_sent > 0 or not s_all.send_queue.empty()
    assert s_alerts.send_queue.empty()

    # Broadcast on alerts topic
    await hub.broadcast("alerts", {"severity": "CRITICAL"})
    await asyncio.sleep(0.05)

    # client-alerts should receive the alert
    assert s_alerts.messages_sent > 0 or not s_alerts.send_queue.empty()

    await hub.unregister("client-all")
    await hub.unregister("client-alerts")


@pytest.mark.anyio
async def test_websocket_hub_backpressure_drop():
    hub = WebSocketHub()
    mock_ws = AsyncMock()
    # Mock send_text to be extremely slow so queue fills up immediately
    mock_ws.send_text = AsyncMock(side_effect=lambda x: asyncio.sleep(10))

    # Create session with tiny queue of 2 items
    session = await hub.register(mock_ws, "slow-client")
    session.send_queue = asyncio.Queue(maxsize=2)

    # Dispatch 10 frames
    for i in range(10):
        await hub.broadcast("telemetry", {"seq": i})

    stats = hub.stats()
    assert stats["total_broadcasts"] == 10
    # At least some frames must be dropped due to bounded queue capacity
    assert stats["total_dropped"] > 0

    await hub.unregister("slow-client")


def test_nats_anomaly_detection_ics():
    consumer = NATSTelemetryConsumer()

    # Nominal readings: no alerts
    nominal_metrics = [
        {"name": "vibration_rms", "value": 1.2},
        {"name": "temperature_c", "value": 45.0},
    ]
    alerts = consumer._detect_anomalies("turbine-01", nominal_metrics, {})
    assert len(alerts) == 0

    # Critical OT vibration reading: T0836
    vib_metrics = [
        {"name": "vibration_rms", "value": 5.8},
    ]
    alerts = consumer._detect_anomalies("turbine-01", vib_metrics, {})
    assert len(alerts) == 1
    assert alerts[0]["mitre_technique"] == "T0836"
    assert alerts[0]["severity"] == "CRITICAL"

    # Thermal anomaly: T0855
    temp_metrics = [
        {"name": "temperature_c", "value": 92.4},
    ]
    alerts = consumer._detect_anomalies("plc-reactor-02", temp_metrics, {})
    assert len(alerts) == 1
    assert alerts[0]["mitre_technique"] == "T0855"

    # IT Brute-force anomaly: T1110
    auth_metrics = [
        {"name": "failed_logins_per_min", "value": 35},
    ]
    alerts = consumer._detect_anomalies("corp-dc-01", auth_metrics, {})
    assert len(alerts) == 1
    assert alerts[0]["mitre_technique"] == "T1110"
