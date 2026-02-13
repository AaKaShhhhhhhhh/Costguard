import asyncio
import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "default_secret_key"
HEADERS = {"X-API-Key": API_KEY}

async def test_endpoints():
    async with httpx.AsyncClient() as client:
        # Test GET /summary
        print("Testing GET /summary...")
        resp = await client.get(f"{BASE_URL}/summary", headers=HEADERS)
        if resp.status_code == 200:
            print(f"SUCCESS: {resp.json()}")
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
            sys.exit(1)

        # Test GET /actions
        print("\nTesting GET /actions...")
        resp = await client.get(f"{BASE_URL}/actions", headers=HEADERS)
        if resp.status_code == 200:
            print(f"SUCCESS: {len(resp.json())} actions found.")
        else:
            print(f"FAILURE: {resp.status_code} - {resp.text}")
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(test_endpoints())
    except Exception as e:
        print(f"Error: {e}")
        print("Ensure backend is running on localhost:8000")
