import json
import httpx
import logging
from collections import deque
from datetime import datetime
from shared.config import settings

logger = logging.getLogger(__name__)

# In-memory log store for Dashboard
ARCHESTRA_LOGS = deque(maxlen=50)

def log_archestra_event(event_type: str, status: str, details: str):
    entry = {
        "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
        "type": event_type,
        "status": status,
        "details": details
    }
    ARCHESTRA_LOGS.appendleft(entry)
    logger.info(f"[Archestra Bridge] {event_type}: {status} - {details}")

def _get_api_url() -> str:
    # Use the public ngrok URL directly from settings
    return settings.archestra_api_url

async def _get_headers() -> dict:
    token = settings.archestra_mcp_token or settings.archestra_api_key
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "CostGuard/1.0"
    }
    return headers

async def notify_archestra(action_id: str, status: str, approver_id: str = "unknown") -> bool:
    """
    Sends a CHAT MESSAGE to the Archestra Agent via A2A API.
    """
    url = _get_api_url()
    headers = await _get_headers()
    
    # Construct a natural language message for the agent
    message_text = (
        f"🚨 **Cost Anomaly Detected!**\n\n"
        f"**Action ID:** `{action_id}`\n"
        f"**Status:** {status}\n"
        f"**Approver:** {approver_id}\n\n"
        f"Please analyze this anomaly and suggest remediation steps."
    )
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "message/send",
        "params": {
            "message": {
                "parts": [{"kind": "text", "text": message_text}]
            }
        }
    }
    
    log_archestra_event("Bridge", "Sending", f"Chatting with Agent about action {action_id}")
    
    try:
        # Increase timeout to 45s to match LLM latency and dashboard timeout
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            
            if resp.status_code == 200:
                result_data = resp.json()
                
                # Check for JSON-RPC Protocol Level Error
                if "error" in result_data:
                    error_info = result_data["error"]
                    err_msg = error_info.get("message", "Unknown RPC error")
                    err_code = error_info.get("code", "unknown")
                    log_archestra_event("Bridge", "Failed", f"RPC Error {err_code}: {err_msg}")
                    log_archestra_event("Debug", "Raw Error", json.dumps(result_data)[:300])
                    return False

                # Parse A2A/MCP JSON-RPC response for message content
                agent_reply = "Message delivered."
                
                try:
                    # Log the raw JSON for successful responses (sampled)
                    log_archestra_event("Debug", "Raw Success", json.dumps(result_data)[:200])

                    # In A2A, the result often contains the message parts
                    if "result" in result_data:
                        result = result_data["result"]
                        # Check if result is the message itself or has a message key
                        msg_obj = result.get("message") if isinstance(result, dict) else None
                        
                        # Fallback: sometimes the result IS the message object
                        if not msg_obj and isinstance(result, dict) and "parts" in result:
                            msg_obj = result
                            
                        if msg_obj:
                            parts = msg_obj.get("parts", [])
                            if parts:
                                agent_reply = " ".join([p.get("text", "") for p in parts if p.get("kind") == "text"])
                except Exception as e:
                    logger.warning(f"Failed to parse agent reply text: {e}")
                    log_archestra_event("Debug", "Parse Error", str(e))

                log_archestra_event("Bridge", "Success", "Agent received the chat message")
                log_archestra_event("Agent", "Reply", agent_reply)
                return True
            else:
                logger.error(f"A2A Call failed {resp.status_code}: {resp.text}")
                log_archestra_event("Debug", "Error", f"HTTP {resp.status_code}: {resp.text[:100]}")
                return False
                
    except Exception as e:
        logger.error(f"A2A Exception: {e}")
        log_archestra_event("Bridge", "Failed", f"Timeout or Connection Error: {str(e)}")
        return False

# Legacy Stubs
async def register_workflow(name: str, config: dict) -> bool:
    return True

async def get_execution_status(action_id: str) -> dict:
    return {"status": "chat_sent"}
