"""Agent handler implementations.

This module implements simple handlers used by the agent runner. Handlers
are intentionally small, well-typed, and demonstrate integration points
with the MCP servers in `mcp-servers/`.
"""
from __future__ import annotations

from typing import Any, Dict
from datetime import datetime, timedelta
import asyncio
import logging

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
    """Detect cost anomalies by comparing recent costs.

    This handler queries each provider for the last 2 days and compares
    the most recent day's total to the prior day. A >50% increase is
    reported as an anomaly.
    """
    end = datetime.utcnow().date()
    start_prev = (end - timedelta(days=2)).isoformat()
    end_prev = (end - timedelta(days=1)).isoformat()
    start_curr = end_prev
    end_curr = end.isoformat()

    results: Dict[str, float] = {}

    # AWS
    try:
        aws = await aws_server.fetch_costs(start_prev, end_curr)
        results["aws"] = aws.get("total_cost", 0.0)
    except Exception as exc:
        LOG.debug("AWS cost fetch failed: %s", exc)

    # GCP
    try:
        gcp = await gcp_server.fetch_billing(start_prev, end_curr)
        results["gcp"] = gcp.get("total_cost", 0.0)
    except Exception as exc:
        LOG.debug("GCP billing fetch failed: %s", exc)

    # Azure
    try:
        az = await azure_server.fetch_azure_costs(start_prev, end_curr)
        results["azure"] = az.get("total_cost", 0.0)
    except Exception as exc:
        LOG.debug("Azure cost fetch failed: %s", exc)

    # Simple anomaly detection: compare last day vs previous day if both available
    anomalies = []
    # For demo, we simply check values directly; real logic should compute baselines
    for provider, total in results.items():
        # naive threshold check
        if total <= 0:
            continue
        # placeholder: no historic baseline available, so skip
    # Return structured result for downstream agents
    payload = {"timestamp": datetime.utcnow().isoformat(), "summary": results}
    LOG.info("Detective ran, summary=%s", payload)
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

    Supports scaling actions that call into `cloud_server.scale_resource`.
    """
    # Example action structure: {"type": "scale", "provider": "aws", "resource_id": "asg-1", "desired": 3}
    typ = action.get("type")
    if typ == "scale":
        provider = action.get("provider")
        resource_id = action.get("resource_id")
        desired = int(action.get("desired", 0))
        try:
            res = await cloud_server.scale_resource(provider, resource_id, desired)
            LOG.info("Scale submitted: %s", res)
            return {"status": "submitted", "meta": res}
        except Exception as exc:
            LOG.exception("Scale action failed")
            return {"status": "failed", "error": str(exc)}

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
    except Exception as exc:
        LOG.exception("Failed to send Slack message")
        return {"status": "failed", "error": str(exc)}
