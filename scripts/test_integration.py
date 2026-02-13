import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "default_secret_key"
HEADERS = {"X-API-Key": API_KEY}

async def test_integration():
    async with httpx.AsyncClient() as client:
        # 1. Create a dummy action
        print("Creating dummy action...")
        action_payload = {
            "id": "act-test-001",
            "timestamp": "2023-10-27T10:00:00Z",
            "action_type": "scale_down",
            "description": "Test Integration Action",
            "estimated_savings": 100.0,
            "risk_level": "low",
            "requires_approval": True,
            "status": "pending"
        }
        resp = await client.post(f"{BASE_URL}/actions", json=action_payload, headers=HEADERS)
        if resp.status_code not in [200, 201]:
            print(f"Failed to create action: {resp.status_code} - {resp.text}")
            sys.exit(1)
        
        print("Action created.")

        # 2. Approve the action (Triggers Archestra notification)
        print("Approving action to trigger Archestra notification...")
        resp = await client.post(f"{BASE_URL}/actions/act-test-001/approve", headers=HEADERS)
        if resp.status_code == 200:
            print(f"SUCCESS: Action approved. Backend checks: {resp.json().get('status')}")
            print("Check backend logs to verify Archestra notification was attempted.")
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_integration())
    except Exception as e:
        print(f"Error: {e}")
