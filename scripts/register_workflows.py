"""Script to manually register CostGuard workflows with Archestra.AI.
Use this to verify authentication and make agents visible in the Archestra UI.
"""
import asyncio
import os
import yaml
from backend.services.integration import register_workflow

# Robustly find the workflows directory
# Inside Docker, this should be /app/workflows
WORKFLOW_DIR = os.path.abspath(os.path.join(os.getcwd(), "workflows"))
if not os.path.exists(WORKFLOW_DIR):
    # Fallback to relative to script
    WORKFLOW_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workflows"))

async def main():
    print(f"🚀 Registering CostGuard Workflows with Archestra.AI...")
    print(f"📂 Searching for workflows in: {WORKFLOW_DIR}")
    
    workflows = ["optimization.yaml", "cost-monitoring.yaml"]
    
    for flow_file in workflows:
        path = os.path.join(WORKFLOW_DIR, flow_file)
        if not os.path.exists(path):
            print(f"❌ Could not find {flow_file} at {path}")
            continue
            
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            
        name = config.get("name", flow_file)
        print(f"📡 Registering {name}...")
        
        success, response_text = await register_workflow_verbose(name, config)
        if success:
            print(f"✅ Successfully registered {name}")
        else:
            print(f"❌ Failed to register {name}.")
            print(f"   Response: {response_text}")

async def register_workflow_verbose(name, config):
    """Wrapper to get response text."""
    from backend.services.integration import _get_archestra_url, _get_headers
    import httpx
    url = f"{_get_archestra_url()}/api/v1/workflows"
    payload = {"name": name, "config": config}
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload, headers=_get_headers())
            return (resp.status_code in [200, 201]), resp.text
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    asyncio.run(main())
