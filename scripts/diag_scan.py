import asyncio
from datetime import datetime, timedelta
from backend.database.base import AsyncSessionLocal
from backend.models.models import LLMUsage
from sqlalchemy import select, func

async def diag():
    print("--- Diagnostic Start ---")
    async with AsyncSessionLocal() as db:
        now = datetime.utcnow()
        today = now.date()
        week_ago = (now - timedelta(days=7)).date()
        
        print(f"Server Time: {now}")
        print(f"Target Today: {today}")
        print(f"Target Week Ago: {week_ago}")
        
        # 1. Total count
        res = await db.execute(select(func.count(LLMUsage.id)))
        print(f"Total LLMUsage records: {res.scalar()}")
        
        # 2. Today's records
        today_stmt = select(LLMUsage.provider, func.sum(LLMUsage.cost)).where(func.date(LLMUsage.timestamp) == today).group_by(LLMUsage.provider)
        today_res = await db.execute(today_stmt)
        today_costs = {row[0]: float(row[1] or 0) for row in today_res.all()}
        print(f"Today costs: {today_costs}")
        
        # 3. 7-day average
        avg_stmt = select(LLMUsage.provider, (func.sum(LLMUsage.cost) / 7)).where(func.date(LLMUsage.timestamp) >= week_ago).where(func.date(LLMUsage.timestamp) < today).group_by(LLMUsage.provider)
        avg_res = await db.execute(avg_stmt)
        avg_costs = {row[0]: float(row[1] or 0) for row in avg_res.all()}
        print(f"7-day avg: {avg_costs}")
        
        # 4. Detailed check for OpenAI
        openai_recs = await db.execute(select(LLMUsage.timestamp, LLMUsage.cost).where(LLMUsage.provider == "OpenAI").order_by(LLMUsage.timestamp.desc()).limit(10))
        print("Recent OpenAI records:")
        for r in openai_recs.all():
            print(f"  {r[0]} | ${r[1]}")
            
    print("--- Diagnostic End ---")

if __name__ == "__main__":
    asyncio.run(diag())
