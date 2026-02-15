"""Enhanced seed script — generates 30 days of realistic demo data."""
import asyncio
import uuid
import os
import random
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.models.models import CostAnomaly, LLMUsage, OptimizationAction, Base

DATABASE_URL = os.getenv("DATABASE_URL")

PROVIDERS = ["OpenAI", "Anthropic", "Google", "AWS Bedrock"]
MODELS = {
    "OpenAI": ["gpt-4o", "gpt-3.5-turbo", "gpt-4o-mini"],
    "Anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
    "Google": ["gemini-pro", "gemini-flash"],
    "AWS Bedrock": ["titan-express", "titan-lite"],
}
SERVICES = {
    "AWS": ["Lambda", "EC2", "S3", "RDS", "EKS"],
    "GCP": ["BigQuery", "Cloud Run", "GKE", "Cloud Functions"],
    "Azure": ["App Service", "AKS", "Cosmos DB", "Functions"],
}
SEVERITIES = ["low", "medium", "high", "critical"]
ACTION_TYPES = ["scale_down", "rightsize", "switch_model", "enable_caching", "terminate_idle"]
STATUSES = ["pending", "approved", "denied", "executed"]


async def seed_if_empty():
    if not DATABASE_URL:
        print("No DATABASE_URL set, skipping seed.")
        return

    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(func.count(CostAnomaly.id)))
        count = result.scalar()

        if count == 0:
            print("Seeding 30 days of demo data...")
            now = datetime.utcnow()

            # --- LLM Usage: ~10 records per day for 30 days ---
            llm_records = []
            for day_offset in range(30):
                day = now - timedelta(days=day_offset)
                num_calls = random.randint(6, 15)
                for _ in range(num_calls):
                    provider = random.choice(PROVIDERS)
                    model = random.choice(MODELS[provider])
                    input_tok = random.randint(50, 5000)
                    output_tok = random.randint(20, 3000)
                    # Cost varies by model tier
                    base_cost = {"gpt-4o": 0.03, "gpt-3.5-turbo": 0.002, "gpt-4o-mini": 0.005,
                                 "claude-3-opus": 0.06, "claude-3-sonnet": 0.015, "claude-3-haiku": 0.003,
                                 "gemini-pro": 0.01, "gemini-flash": 0.004,
                                 "titan-express": 0.008, "titan-lite": 0.003}
                    cost = round(base_cost.get(model, 0.01) * (input_tok + output_tok) / 1000, 4)
                    # Add some daily variance (spike on certain days)
                    if day_offset in [3, 7, 14, 21]:
                        cost *= random.uniform(2.0, 5.0)
                    ts = day.replace(hour=random.randint(0, 23), minute=random.randint(0, 59))
                    llm_records.append(LLMUsage(
                        timestamp=ts, provider=provider, model=model,
                        input_tokens=input_tok, output_tokens=output_tok,
                        cost=round(cost, 4),
                        latency_ms=round(random.uniform(100, 3000), 1),
                        quality_score=round(random.uniform(0.7, 1.0), 2),
                    ))
            session.add_all(llm_records)
            print(f"  Seeded {len(llm_records)} LLM usage records.")

            # --- Anomalies: spread across last 30 days ---
            anomaly_records = []
            anomaly_data = [
                ("AWS", "Lambda", 150.0, 20.0, 650.0, "high", "Unexpected Lambda cost spike in us-east-1"),
                ("GCP", "BigQuery", 45.0, 5.0, 800.0, "medium", "High query costs in analytics project"),
                ("Azure", "App Service", 320.0, 80.0, 300.0, "high", "App Service plan overprovisioned"),
                ("AWS", "EC2", 89.0, 30.0, 196.7, "medium", "EC2 usage spike in eu-west-1"),
                ("GCP", "Cloud Run", 25.0, 8.0, 212.5, "low", "Cloud Run autoscaling triggered excessively"),
                ("AWS", "RDS", 200.0, 50.0, 300.0, "high", "RDS storage costs doubled"),
                ("Azure", "Cosmos DB", 150.0, 40.0, 275.0, "critical", "Cosmos DB RU consumption spike"),
                ("GCP", "GKE", 180.0, 60.0, 200.0, "medium", "GKE node pool scaled unexpectedly"),
                ("AWS", "S3", 35.0, 10.0, 250.0, "low", "S3 GET request costs elevated"),
                ("Azure", "AKS", 250.0, 100.0, 150.0, "high", "AKS cluster costs above budget"),
            ]
            for i, (prov, svc, cur, exp, dev, sev, desc) in enumerate(anomaly_data):
                ts = now - timedelta(days=random.randint(0, 29), hours=random.randint(0, 23))
                anomaly_records.append(CostAnomaly(
                    id=str(uuid.uuid4()), timestamp=ts,
                    provider=prov, service=svc,
                    current_cost=cur, expected_cost=exp,
                    deviation_percent=dev, severity=sev,
                    description=desc,
                    meta={"region": random.choice(["us-east-1", "eu-west-1", "ap-south-1"])}
                ))
            session.add_all(anomaly_records)
            print(f"  Seeded {len(anomaly_records)} anomalies.")

            # --- Actions: linked to anomalies ---
            action_records = []
            action_data = [
                ("scale_down", "Scale down Lambda concurrency in us-east-1", 80.0, "low", "executed"),
                ("rightsize", "Rightsize BigQuery slots for analytics", 25.0, "medium", "approved"),
                ("scale_down", "Reduce App Service plan tier", 160.0, "medium", "pending"),
                ("switch_model", "Switch GPT-4o calls to GPT-4o-mini for simple queries", 45.0, "low", "executed"),
                ("enable_caching", "Enable response caching for repeated prompts", 30.0, "low", "approved"),
                ("terminate_idle", "Terminate idle RDS instances", 120.0, "high", "pending"),
                ("rightsize", "Rightsize Cosmos DB RU allocation", 90.0, "medium", "denied"),
                ("scale_down", "Reduce GKE node pool max size", 70.0, "medium", "pending"),
            ]
            for atype, desc, savings, risk, stat in action_data:
                ts = now - timedelta(days=random.randint(0, 15), hours=random.randint(0, 23))
                action_records.append(OptimizationAction(
                    id=str(uuid.uuid4()), timestamp=ts,
                    action_type=atype, description=desc,
                    estimated_savings=savings, risk_level=risk,
                    requires_approval=(risk != "low"),
                    auto_approved=(risk == "low"),
                    status=stat,
                ))
            session.add_all(action_records)
            print(f"  Seeded {len(action_records)} optimization actions.")

            await session.commit()
            print("Seeding complete!")
        else:
            print(f"Database already has {count} anomalies. Skipping seed.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed_if_empty())
