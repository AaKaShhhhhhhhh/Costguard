"""Azure Cost Management integration helpers.

This module provides a minimal async wrapper for querying Azure cost
management APIs. It is deliberately minimal — install `azure-identity` and
`azure-mgmt-costmanagement` for production usage.
"""
from __future__ import annotations

from typing import Dict
import asyncio
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


async def fetch_azure_costs(start: str, end: str) -> Dict[str, float]:
    """Fetch Azure costs for the subscription between `start` and `end`.

    Args:
        start: ISO date string
        end: ISO date string

    Returns:
        Summary dict with `total_cost`.

    Raises:
        RuntimeError: if azure libs or credentials are missing.
    """
    try:
        from azure.identity import DefaultAzureCredential
        from azure.mgmt.costmanagement import CostManagementClient
    except Exception as exc:  # pragma: no cover
        logger.exception("Azure SDK is required for Azure cost integration")
        raise RuntimeError("Azure SDK not available") from exc

    if not settings.azure_subscription_id:
        raise RuntimeError("Azure subscription ID not configured")

    # Placeholder implementation — real queries require detailed config.
    await asyncio.sleep(0)
    return {"total_cost": 0.0}
