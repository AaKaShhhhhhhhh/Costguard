import asyncio
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.models import CostAnomaly, Base

DATABASE_URL = "sqlite+aiosqlite:///./backend/costguard.db"

async def seed_data():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        anomaly = CostAnomaly(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            provider="AWS",
            service="Lambda",
            current_cost=150.0,
            expected_cost=20.0,
            deviation_percent=650.0,
            severity="high",
            description="Unexpected Lambda cost spike in us-east-1",
            meta={"region": "us-east-1"}
        )
        session.add(anomaly)
        await session.commit()
        print(f"Seeded anomaly: {anomaly.id}")

if __name__ == "__main__":
    asyncio.run(seed_data())
