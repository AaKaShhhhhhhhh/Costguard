"""Slack notifications helper using `httpx`.

Provide a simple async `post_message` function that sends messages to a
configured Slack webhook or bot token. Uses `httpx` for async HTTP calls and
reads configuration from `shared.config`.
"""
from __future__ import annotations

from typing import Any, Dict
import httpx
import logging

from shared.config import settings

logger = logging.getLogger(__name__)


async def post_message(channel: str, text: str) -> Dict[str, Any]:
    """Post a message to Slack using the bot token from settings.

    Args:
        channel: Channel name (e.g., '#cost-alerts') or channel ID.
        text: Message text.

    Returns:
        Parsed Slack API response.

    Raises:
        RuntimeError: If Slack token is missing or the API returns an error.
    """
    if not settings.slack_bot_token:
        raise RuntimeError("Slack bot token not configured")

    url = "https://slack.com/api/chat.postMessage"
    headers = {"Authorization": f"Bearer {settings.slack_bot_token}", "Content-Type": "application/json; charset=utf-8"}
    payload = {"channel": channel, "text": text}

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        try:
            data = resp.json()
        except Exception:
            logger.exception("Invalid JSON from Slack API")
            raise RuntimeError("Invalid response from Slack API")

    if not data.get("ok"):
        logger.error("Slack API error: %s", data)
        raise RuntimeError(f"Slack API error: {data.get('error')}")

    return data
