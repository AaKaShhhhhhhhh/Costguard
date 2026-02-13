import asyncio
import httpx
import uuid
from datetime import datetime

BACKEND_URL = "http://localhost:8000/api/v1"
API_KEY = "default_secret_key"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

async def seed_data():
    async with httpx.AsyncClient() as client:
        print("--- Seeding LLM Usage ---")
        usage_data = [
            {"provider": "OpenAI", "model": "gpt-4", "input_tokens": 1000, "output_tokens": 500, "cost": 0.045},
            {"provider": "Anthropic", "model": "claude-3-opus", "input_tokens": 500, "output_tokens": 200, "cost": 0.15},
            {"provider": "Google", "model": "gemini-1.5-pro", "input_tokens": 2000, "output_tokens": 800, "cost": 0.02},
        ]
        for u in usage_data:
            r = await client.post(f"{BACKEND_URL}/llm/usage", json=u, headers=HEADERS)
            print(f"Usage created: {r.status_code}")

        print("\n--- Seeding Anomaly ---")
        anomaly_id = str(uuid.uuid4())[:8]
        anomaly = {
            "id": anomaly_id,
            "provider": "Anthropic",
            "service": "Claude 3 API",
            "current_cost": 500.0,
            "expected_cost": 50.0,
            "deviation_percent": 900.0,
            "severity": "critical",
            "description": "Sudden spike in Claude-3 usage detected from unknown project.",
            "meta": {"project": "hidden-mining-op"}
        }
        r = await client.post(f"{BACKEND_URL}/anomalies", json=anomaly, headers=HEADERS)
        print(f"Anomaly created: {r.status_code}")

        print("\n--- Seeding Action ---")
        action = {
            "id": f"ACT-{anomaly_id}",
            "action_type": "quarantine",
            "description": "Suspend API access for project 'hidden-mining-op'",
            "estimated_savings": 450.0,
            "risk_level": "high",
            "requires_approval": True,
            "status": "pending"
        }
        r = await client.post(f"{BACKEND_URL}/actions", json=action, headers=HEADERS)
        print(f"Action created: {r.status_code}")

if __name__ == "__main__":
    asyncio.run(seed_data())
