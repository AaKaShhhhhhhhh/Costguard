"""GCP Billing integration helpers.

This module provides a placeholder `fetch_billing` function. It attempts
to use `google-cloud-billing` if available; otherwise it raises an
informative error. The function signature is async to fit MCP server usage.
"""
from __future__ import annotations

from typing import Dict
import asyncio
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


async def fetch_billing(start: str, end: str) -> Dict[str, float]:
    """Fetch billing data for a GCP project between `start` and `end`.

    Args:
        start: ISO date string for range start.
        end: ISO date string for range end.

    Returns:
        A mapping summarizing costs.

    Raises:
        RuntimeError: Missing credentials or library.
    """
    try:
        from google.cloud import billing_v1
    except Exception as exc:  # pragma: no cover
        logger.exception("google-cloud-billing is required for GCP integration")
        raise RuntimeError("google-cloud-billing library missing") from exc

    if not settings.gcp_project_id or not settings.gcp_credentials_path:
        raise RuntimeError("GCP project or credentials not configured")

    # Placeholder implementation: real implementation would use BigQuery
    # or Cloud Billing export to query costs. Here we return a stub.
    await asyncio.sleep(0)
    return {"total_cost": 0.0}
