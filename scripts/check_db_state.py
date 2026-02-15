import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func
import os

# Use the host-accessible mapping
DATABASE_URL = "postgresql+asyncpg://costguard:dev-password@localhost:5432/costguard"

async def check_db():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check LLM Usage
        from backend.models.models import LLMUsage, CostAnomaly, OptimizationAction
        
        usage_res = await session.execute(select(func.count(LLMUsage.id)))
        usage_count = usage_res.scalar()
        print(f"Total LLM Usage records: {usage_count}")
        
        # Check Today's usage
        from datetime import datetime
        now = datetime.utcnow()
        start_of_today = datetime(now.year, now.month, now.day)
        
        today_res = await session.execute(
            select(func.sum(LLMUsage.cost))
            .where(LLMUsage.timestamp >= start_of_today)
        )
        today_cost = today_res.scalar()
        print(f"Today's total cost: {today_cost}")
        
        # Check baseline
        start_of_baseline = start_of_today - datetime.timedelta(days=7) if hasattr(datetime, "timedelta") else now # Fix below
        import datetime as dt
        start_of_baseline = start_of_today - dt.timedelta(days=7)
        
        baseline_res = await session.execute(
            select(func.sum(LLMUsage.cost))
            .where(LLMUsage.timestamp >= start_of_baseline)
            .where(LLMUsage.timestamp < start_of_today)
        )
        baseline_cost = baseline_res.scalar()
        print(f"Baseline total cost (last 7 days): {baseline_cost}")
        
        # Check Anomalies
        anom_res = await session.execute(select(func.count(CostAnomaly.id)))
        print(f"Total Anomalies: {anom_res.scalar()}")

if __name__ == "__main__":
    import os
    import sys
    # Add project root to path for imports
    sys.path.append(os.getcwd())
    asyncio.run(check_db())
