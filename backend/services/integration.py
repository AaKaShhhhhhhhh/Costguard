import os
import httpx
import logging

logger = logging.getLogger(__name__)

ARCHESTRA_API_URL = os.getenv("ARCHESTRA_API_URL", "https://api.archestra.ai")
ARCHESTRA_API_KEY = os.getenv("ARCHESTRA_API_KEY", "")


async def notify_archestra(action_id: str, status: str, approver_id: str = "unknown") -> bool:
    """
    Notify Archestra that an action has been approved or denied.

    Args:
        action_id: The ID of the action.
        status: 'approved' or 'denied'.
        approver_id: ID of the user who approved/denied.

    Returns:
        True if notification was successful, False otherwise.
    """
    url = f"{ARCHESTRA_API_URL}/api/v1/webhooks/workflow/resume"

    payload = {
        "event": "action_review",
        "action_id": action_id,
        "status": status,
        "approver": approver_id,
    }

    headers = {
        "Content-Type": "application/json",
    }
    if ARCHESTRA_API_KEY:
        headers["Authorization"] = f"Bearer {ARCHESTRA_API_KEY}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in [200, 201, 202]:
                logger.info("Notified Archestra for action %s: %s", action_id, resp.status_code)
                return True
            else:
                logger.warning("Archestra returned %s: %s", resp.status_code, resp.text)
                return False
    except Exception as e:
        logger.warning("Could not reach Archestra: %s", e)
        return False
