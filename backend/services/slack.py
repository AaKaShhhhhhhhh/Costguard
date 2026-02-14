import os
import logging
import httpx
from typing import Dict, Any, Optional
from shared.config import settings

logger = logging.getLogger(__name__)

class SlackService:
    """Service to handle Slack notifications using Bot Tokens or Webhooks."""
    
    def __init__(self):
        self.token = settings.slack_bot_token
        self.webhook_url = settings.slack_webhook_url
        self.api_url = "https://slack.com/api/chat.postMessage"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8"
        }

    async def send_message(self, channel: str, text: str, blocks: Optional[list] = None) -> bool:
        """Send a message via Webhook (preferred) or Bot Token."""
        logger.info(f"Attempting to send Slack message to {channel}...")
        
        # 1. Try Webhook first (simpler for community workspaces)
        if self.webhook_url and "hooks.slack.com" in self.webhook_url:
            logger.info("Using Slack Webhook for notification.")
            payload = {"text": text}
            if blocks:
                payload["blocks"] = blocks
            
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(self.webhook_url, json=payload)
                    if resp.status_code == 200:
                        logger.info("Slack Webhook delivered successfully.")
                        return True
                    else:
                        logger.error(f"Slack Webhook returned error {resp.status_code}: {resp.text}")
            except Exception as e:
                logger.error(f"Slack Webhook failed with exception: {e}")
                # Fallback to token if it exists

        # 2. Try Bot Token
        if not self.token or "your-slack-bot-token" in self.token:
            logger.warning(f"Slack not configured (No Valid Webhook or Token). self.webhook_url='{self.webhook_url}'")
            return False

        logger.info(f"Using Slack Bot Token for notification to {channel}.")
        payload = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(self.api_url, json=payload, headers=self.headers)
                data = resp.json()
                if data.get("ok"):
                    logger.info("Slack Bot message delivered successfully.")
                    return True
                else:
                    logger.error(f"Slack API error: {data.get('error')}")
                    return False
        except Exception as e:
            logger.error(f"Slack Token API failed with exception: {e}")
            return False

    async def notify_anomaly(self, anomaly: Dict[str, Any]) -> bool:
        """Send a rich notification for a cost anomaly."""
        channel = settings.slack_channel_alerts
        severity_emoji = {
            "critical": "🚨",
            "high": "🔥",
            "medium": "⚠️",
            "low": "ℹ️"
        }.get(anomaly.get("severity", "").lower(), "🔍")

        text = f"{severity_emoji} *New Anomaly Detected!*"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"{severity_emoji} *New Anomaly Detected in {anomaly.get('provider')}*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Service:*\n{anomaly.get('service')}"},
                    {"type": "mrkdwn", "text": f"*Severity:*\n{anomaly.get('severity').upper()}"},
                    {"type": "mrkdwn", "text": f"*Current Cost:*\n${float(anomaly.get('current_cost') or 0.0):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Expected:*\n${float(anomaly.get('expected_cost') or 0.0):,.2f}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{anomaly.get('description')}"
                }
            }
        ]
        
        return await self.send_message(channel, text, blocks)

    async def notify_action(self, action: Dict[str, Any]) -> bool:
        """Send a notification for a pending optimization action."""
        channel = settings.slack_channel_approvals
        text = f"💡 *New Optimization Action Pending Approval*"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"💡 *New Optimization Action Pending Approval*"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Type:*\n{action.get('action_type')}"},
                    {"type": "mrkdwn", "text": f"*Savings:*\n${action.get('estimated_savings'):,.2f}"},
                    {"type": "mrkdwn", "text": f"*Risk:*\n{action.get('risk_level')}"}
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Description:*\n{action.get('description')}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "✅ Approve"
                        },
                        "style": "primary",
                        "action_id": "approve_action",
                        "value": str(action.get("id"))
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "❌ Deny"
                        },
                        "style": "danger",
                        "action_id": "deny_action",
                        "value": str(action.get("id"))
                    }
                ]
            }
        ]
        
        return await self.send_message(channel, text, blocks)

slack_service = SlackService()
