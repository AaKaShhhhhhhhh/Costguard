"""Diagnostics script to test Archestra.AI authentication combinations.
"""
import asyncio
import httpx
import os
import sys
from shared.config import settings

# Fallback to manual .env reading if settings didn't pick it up (due to missing restart)
def get_env_var(name):
    val = os.getenv(name)
    if val: return val
    try:
        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.strip().startswith(f"{name}="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
    except: pass
    return None

API_KEY = get_env_var("ARCHESTRA_API_KEY") or settings.archestra_api_key
MCP_TOKEN = get_env_var("ARCHESTRA_MCP_TOKEN") or settings.archestra_mcp_token
TEAM_TOKEN = get_env_var("ARCHESTRA_TEAM_TOKEN") or settings.archestra_team_token

print(f"🔑 API_KEY present: {bool(API_KEY)}")
print(f"🎫 MCP_TOKEN present: {bool(MCP_TOKEN)}")
print(f"👥 TEAM_TOKEN present: {bool(TEAM_TOKEN)}")

if not API_KEY and not TEAM_TOKEN:
    print("❌ Critical: No tokens found in environment OR .env file.")
    sys.exit(1)

async def test_combo(name, headers):
    print(f"\n--- Testing: {name} ---")
    headers["Content-Type"] = "application/json"
    url = f"{settings.archestra_api_url}/api/v1/auth/me"
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers=headers)
            print(f"    Status: {resp.status_code}")
            if resp.status_code < 400:
                print(f"    ✅ SUCCESS!")
                print(f"    Body: {resp.text[:100]}")
                return True
            if resp.status_code == 403:
                print(f"    🚫 403 Body: {resp.text}")
    except Exception as e:
        print(f"    Error: {e}")
    return False

async def main():
    combos = []
    
    # 1. Team Token variations
    if TEAM_TOKEN:
        combos.append(("Raw Team Token", {"Authorization": TEAM_TOKEN}))
        combos.append(("Bearer Team Token", {"Authorization": f"Bearer {TEAM_TOKEN}"}))
        combos.append(("X-Archestra-Org-Token", {"X-Archestra-Org-Token": TEAM_TOKEN}))
        combos.append(("X-Team-Token", {"X-Team-Token": TEAM_TOKEN}))

    # 2. Dual Combos
    if API_KEY and TEAM_TOKEN:
        combos.append(("Auth: Key (Raw) + Team Token Header", {
            "Authorization": API_KEY,
            "X-Archestra-Org-Token": TEAM_TOKEN
        }))
        combos.append(("Auth: Key (Raw) + X-Team-Token", {
            "Authorization": API_KEY,
            "X-Team-Token": TEAM_TOKEN
        }))
        combos.append(("Auth: Team (Raw) + API Key Header", {
            "Authorization": TEAM_TOKEN,
            "X-Api-Key": API_KEY
        }))

    # 3. The Control (Raw Platform Key)
    if API_KEY:
        combos.append(("Raw Platform Key (Control)", {"Authorization": API_KEY}))

    for name, headers in combos:
        if await test_combo(name, headers):
            print(f"\n✅ FOUND WORKING COMBINATION: {name}")
            return

    print("\n❌ All combinations failed.")

if __name__ == "__main__":
    asyncio.run(main())
