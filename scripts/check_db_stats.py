import asyncio
from datetime import datetime, timedelta
from backend.database.base import AsyncSessionLocal
from backend.models.models import LLMUsage
from sqlalchemy import select, func

async def check_db():
    print("--- DB Record Check ---")
    async with AsyncSessionLocal() as session:
        # Check daily distribution
        stmt = (
            select(
                func.date(LLMUsage.timestamp).label("date"),
                func.count(LLMUsage.id).label("count"),
                func.sum(LLMUsage.cost).label("total_cost"),
                LLMUsage.provider
            )
            .group_by(func.date(LLMUsage.timestamp), LLMUsage.provider)
            .order_by(func.date(LLMUsage.timestamp).desc())
        )
        result = await session.execute(stmt)
        rows = result.all()
        
        if not rows:
            print("❌ No records found in LLMUsage table.")
            return

        for row in rows:
            print(f"Date: {row.date} | Provider: {row.provider:12} | Records: {row.count:3} | Total Cost: ${row.total_cost:8.2f}")
            
        # Check current baseline calculation
        now = datetime.utcnow()
        start_of_today = datetime(now.year, now.month, now.day)
        start_of_baseline = start_of_today - timedelta(days=7)
        
        print(f"\nScanning logic parameters:")
        print(f"  Now: {now}")
        print(f"  Start of Today: {start_of_today}")
        print(f"  Start of Baseline: {start_of_baseline}")
        
        # Today's scan check
        today_cnt = await session.execute(select(func.count(LLMUsage.id)).where(LLMUsage.timestamp >= start_of_today))
        print(f"Records marked as 'Today' (>= {start_of_today}): {today_cnt.scalar()}")
        
        # Baseline check
        base_cnt = await session.execute(
            select(func.count(LLMUsage.id))
            .where(LLMUsage.timestamp >= start_of_baseline)
            .where(LLMUsage.timestamp < start_of_today)
        )
        print(f"Records marked as 'Baseline' ({start_of_baseline} to {start_of_today}): {base_cnt.scalar()}")

if __name__ == "__main__":
    asyncio.run(check_db())
