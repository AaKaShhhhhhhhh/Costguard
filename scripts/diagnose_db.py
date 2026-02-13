import asyncio
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.models import LLMUsage, Base
from datetime import datetime

DATABASE_URL = "postgresql+asyncpg://costguard:dev-password@postgres:5432/costguard"

async def check_db():
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        print("DEBUG: Checking database connection...")
        try:
            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            
            # Simple count
            res = await session.execute(select(func.count(LLMUsage.id)))
            count = res.scalar()
            print(f"DEBUG: Found {count} usage records total.")
            
            # Sum for current month
            res = await session.execute(
                select(func.sum(LLMUsage.cost))
                .where(LLMUsage.timestamp >= month_start)
            )
            total = res.scalar()
            print(f"DEBUG: Total cost for month: {total}")
            
        except Exception as e:
            print(f"ERROR: Database check failed: {e}")
            import traceback
            traceback.print_exc()
            
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db())
