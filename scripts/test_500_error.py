import asyncio
import httpx

async def check_api():
    url = "http://localhost:8000/api/v1/anomalies"
    headers = {"X-API-Key": "default_secret_key"}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(check_api())
