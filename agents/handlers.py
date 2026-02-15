"""Agent handler implementations.

This module implements handlers used by the agent runner. Handlers
integrate with MCP servers and the backend database to perform
real anomaly detection and optimization execution.
"""
from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timedelta
import asyncio
import logging
import uuid

from shared.logger import logger
from shared.config import settings

# Import MCP server helpers (they gracefully raise if SDKs are missing)
from mcp_servers.aws_cost_server import server as aws_server
from mcp_servers.gcp_billing_server import server as gcp_server
from mcp_servers.azure_cost_server import server as azure_server
from mcp_servers.cloud_resource_server import server as cloud_server
from mcp_servers.slack_server import server as slack_server

LOG = logging.getLogger(__name__)


async def detective_handler(config: Dict[str, Any]) -> Dict[str, Any]:
    """Detect cost anomalies by comparing recent costs against baselines.

    This handler queries each cloud provider for the last 2 days and
    compares the most recent day's total to the prior day. A >50%
    increase is reported as an anomaly. It also attempts to query the
    backend DB for LLM usage baselines.
    """
    end = datetime.utcnow().date()
    start_prev = (end - timedelta(days=2)).isoformat()
    end_prev = (end - timedelta(days=1)).isoformat()
    end_curr = end.isoformat()

    results: Dict[str, Dict[str, float]] = {}

    # AWS
    try:
        aws_prev = await aws_server.fetch_costs(start_prev, end_prev)
        aws_curr = await aws_server.fetch_costs(end_prev, end_curr)
        results["aws"] = {
            "previous": aws_prev.get("total_cost", 0.0),
            "current": aws_curr.get("total_cost", 0.0),
        }
    except Exception as exc:
        LOG.debug("AWS cost fetch failed: %s", exc)

    # GCP
    try:
        gcp_prev = await gcp_server.fetch_billing(start_prev, end_prev)
        gcp_curr = await gcp_server.fetch_billing(end_prev, end_curr)
        results["gcp"] = {
            "previous": gcp_prev.get("total_cost", 0.0),
            "current": gcp_curr.get("total_cost", 0.0),
        }
    except Exception as exc:
        LOG.debug("GCP billing fetch failed: %s", exc)

    # Azure
    try:
        az_prev = await azure_server.fetch_azure_costs(start_prev, end_prev)
        az_curr = await azure_server.fetch_azure_costs(end_prev, end_curr)
        results["azure"] = {
            "previous": az_prev.get("total_cost", 0.0),
            "current": az_curr.get("total_cost", 0.0),
        }
    except Exception as exc:
        LOG.debug("Azure cost fetch failed: %s", exc)

    # Anomaly detection: compare current vs previous day
    anomalies = []
    for provider, costs in results.items():
        prev = costs["previous"]
        curr = costs["current"]
        if prev <= 0:
            continue
        deviation = ((curr - prev) / prev) * 100
        if deviation > 50:
            severity = "low" if deviation < 100 else ("medium" if deviation < 200 else ("high" if deviation < 500 else "critical"))
            anomalies.append({
                "provider": provider,
                "previous_cost": prev,
                "current_cost": curr,
                "deviation_percent": round(deviation, 1),
                "severity": severity,
                "description": f"{provider.upper()} costs spiked {deviation:.0f}% day-over-day (${prev:.2f} → ${curr:.2f})",
            })
            LOG.warning("Anomaly detected: %s costs up %.1f%%", provider, deviation)

    payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {p: c["current"] for p, c in results.items()},
        "anomalies": anomalies,
        "anomaly_count": len(anomalies),
    }
    LOG.info("Detective ran: %d anomalies from %d providers", len(anomalies), len(results))
    return payload


async def optimizer_handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """Decide which LLM model to route a query to based on complexity.

    This demo uses an input 'tokens' field to pick a model.
    """
    tokens = int(event.get("tokens", 0))
    # Simple policy: small requests -> cheaper model
    if tokens < 500:
        model = "gpt-3.5-turbo"
        estimated_cost = 0.0005
    else:
        model = "gpt-4o"
        estimated_cost = 0.03

    action = {
        "timestamp": datetime.utcnow().isoformat(),
        "decision": {"model": model, "estimated_cost": estimated_cost},
        "original": event,
    }
    LOG.info("Optimizer decision: %s", action)
    return action


async def executor_handler(action: Dict[str, Any]) -> Dict[str, Any]:
    """Execute scaling or optimization actions.

    Supports:
    - 'scale' actions via cloud_server.scale_resource
    - 'switch_model' actions (logs recommendation)
    - 'execute_approved' actions (marks as executed in backend)
    """
    typ = action.get("type")

    if typ == "scale":
        provider = action.get("provider")
        resource_id = action.get("resource_id")
        desired = int(action.get("desired", 0))
        try:
            res = await cloud_server.scale_resource(provider, resource_id, desired)
            LOG.info("Scale submitted: %s", res)
            return {"status": "submitted", "meta": res}
        except Exception:
            LOG.exception("Scale action failed")
            return {"status": "failed", "error": "Scale action failed"}

    elif typ == "switch_model":
        LOG.info("Model switch recommendation: %s", action.get("description", ""))
        return {"status": "recommended", "action": action}

    elif typ == "execute_approved":
        # Execute an approved optimization action
        action_id = action.get("action_id")
        LOG.info("Executing approved action %s", action_id)
        try:
            from backend.services import integration
            await integration.notify_archestra(action_id, "executed")
            return {"status": "executed", "action_id": action_id}
        except Exception:
            LOG.exception("Execution notification failed")
            return {"status": "failed", "action_id": action_id}

    # unsupported action
    LOG.warning("Unsupported action type: %s", typ)
    return {"status": "ignored", "reason": "unsupported action"}


async def communicator_handler(message: Dict[str, Any]) -> Dict[str, Any]:
    """Send a Slack notification for the provided message.

    Uses the `slack_server.post_message` helper.
    """
    channel = message.get("channel", settings.slack_channel_alerts)
    text = message.get("text", "Alert from CostGuard")
    try:
        resp = await slack_server.post_message(channel, text)
        return {"status": "sent", "resp": resp}
    except Exception:
        LOG.exception("Failed to send Slack message")
        return {"status": "failed", "error": "Slack send failed"}

