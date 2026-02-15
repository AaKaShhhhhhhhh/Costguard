import asyncio
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from backend.database.base import AsyncSessionLocal
from backend.models.models import LLMUsage

async def simulate_anomaly():
    """Insert high-cost LLM usage records for 'today' to trigger the detective agent."""
    print("🚀 Simulating high-cost anomaly for OpenAI...")
    
    async with AsyncSessionLocal() as session:
        now = datetime.utcnow()
        
        # --- Add Baseline Data (last 7 days) ---
        print("📊 Adding baseline data for the past week...")
        for day in range(1, 8):
            ts = now - timedelta(days=day)
            # Normal cost is low ($0.5 - $2.0)
            cost = round(random.uniform(0.5, 2.0), 2)
            usage = LLMUsage(
                timestamp=ts,
                provider="OpenAI",
                model="gpt-4o",
                input_tokens=random.randint(1000, 5000),
                output_tokens=random.randint(500, 2000),
                cost=cost,
                latency_ms=random.uniform(500, 1500),
                quality_score=0.98
            )
            session.add(usage)
            
        # --- Add Anomaly Data (Today) ---
        print("🚀 Simulating high-cost anomaly for OpenAI today...")
        for i in range(5):
            cost = round(random.uniform(50.0, 100.0), 2)
            usage = LLMUsage(
                timestamp=now,
                provider="OpenAI",
                model="gpt-4o",
                input_tokens=random.randint(100000, 200000),
                output_tokens=random.randint(50000, 100000),
                cost=cost,
                latency_ms=random.uniform(3000, 6000),
                quality_score=0.95
            )
            session.add(usage)
            print(f"  Added today record: OpenAI - ${cost}")
            
        await session.commit()
        print("\n✅ Simulation complete! Baseline and Anomaly records inserted.")
        print("🔍 Now go to the dashboard 'Agent Control' page and run 'Anomaly Scan'.")

if __name__ == "__main__":
    asyncio.run(simulate_anomaly())
