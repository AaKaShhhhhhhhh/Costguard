"""AWS Cost Explorer integration helpers.

Provides an async `fetch_costs` function that returns cost metrics for a
given time range. Uses `boto3` when available; otherwise a clear
ImportError is raised. The function accepts `start` and `end` as ISO
date strings and returns a dict summary.
"""
from __future__ import annotations

from typing import Dict
import asyncio
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


async def fetch_costs(start: str, end: str) -> Dict[str, float]:
    """Fetch cost metrics from AWS Cost Explorer.

    Args:
        start: ISO date string for range start (YYYY-MM-DD).
        end: ISO date string for range end (YYYY-MM-DD).

    Returns:
        A dictionary with aggregated cost metrics.

    Raises:
        RuntimeError: If AWS credentials are not configured or boto3 missing.
    """
    try:
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError
    except Exception as exc:  # pragma: no cover - dependency check
        logger.exception("boto3 is required for AWS Cost Explorer integration")
        raise RuntimeError("boto3 is required for AWS integration") from exc

    if not settings.aws_access_key_id or not settings.aws_secret_access_key:
        raise RuntimeError("AWS credentials are not configured in environment")

    # Run blocking boto3 call in threadpool
    def _call_ce() -> Dict[str, float]:
        client = boto3.client(
            "ce",
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region,
        )
        try:
            response = client.get_cost_and_usage(
                TimePeriod={"Start": start, "End": end},
                Granularity="DAILY",
                Metrics=["UnblendedCost"],
            )
        except (BotoCoreError, ClientError) as exc:
            logger.exception("AWS Cost Explorer API call failed")
            raise RuntimeError("AWS Cost Explorer API call failed") from exc

        # Aggregate total
        total = 0.0
        for res in response.get("ResultsByTime", []):
            for group in res.get("Groups", []) or []:
                pass
            amount = res.get("Total", {}).get("UnblendedCost", {}).get("Amount")
            try:
                total += float(amount or 0.0)
            except Exception:
                continue

        return {"total_cost": total}

    result = await asyncio.get_event_loop().run_in_executor(None, _call_ce)
    return result
