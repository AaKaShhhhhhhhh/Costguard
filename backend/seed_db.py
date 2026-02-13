import asyncio
import uuid
import os
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.models import CostAnomaly, LLMUsage, Base

# Get DB URL from env
DATABASE_URL = os.getenv("DATABASE_URL")

async def seed_if_empty():
    if not DATABASE_URL:
        print("No DATABASE_URL set, skipping seed.")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if anomalies exist
        result = await session.execute(select(func.count(CostAnomaly.id)))
        count = result.scalar()
        
        if count == 0:
            print("Seeding initial data...")
            
            # Anomaly 1
            a1 = CostAnomaly(
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
            
            # Anomaly 2
            a2 = CostAnomaly(
                id=str(uuid.uuid4()),
                timestamp=datetime.utcnow() - timedelta(hours=2),
                provider="GCP",
                service="BigQuery",
                current_cost=45.0,
                expected_cost=5.0,
                deviation_percent=800.0,
                severity="medium",
                description="High query costs in analytics project",
                meta={"dataset": "analytics_prod"}
            )
            
            session.add_all([a1, a2])
            await session.commit()
            print("Seeded 2 anomalies.")
        else:
            print(f"Database already has {count} anomalies. Skipping seed.")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_if_empty())
