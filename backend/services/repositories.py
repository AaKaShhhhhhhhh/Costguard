from typing import List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import LLMUsage, CostAnomaly, OptimizationAction

# --- LLM Usage Repositories ---

async def create_llm_usage(db: AsyncSession, usage_data: dict) -> LLMUsage:
    db_usage = LLMUsage(**usage_data)
    db.add(db_usage)
    await db.commit()
    await db.refresh(db_usage)
    return db_usage

async def list_llm_usage(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[LLMUsage]:
    result = await db.execute(select(LLMUsage).offset(skip).limit(limit).order_by(LLMUsage.timestamp.desc()))
    return result.scalars().all()

# --- Cost Anomaly Repositories ---

async def create_anomaly(db: AsyncSession, anomaly_data: dict) -> CostAnomaly:
    db_anomaly = CostAnomaly(**anomaly_data)
    db.add(db_anomaly)
    await db.commit()
    await db.refresh(db_anomaly)
    return db_anomaly

async def list_anomalies(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CostAnomaly]:
    result = await db.execute(select(CostAnomaly).offset(skip).limit(limit).order_by(CostAnomaly.timestamp.desc()))
    return result.scalars().all()

# --- Optimization Action Repositories ---

async def create_action(db: AsyncSession, action_data: dict) -> OptimizationAction:
    db_action = OptimizationAction(**action_data)
    db.add(db_action)
    await db.commit()
    await db.refresh(db_action)
    return db_action

async def approve_action(db: AsyncSession, action_id: str) -> Optional[OptimizationAction]:
    result = await db.execute(select(OptimizationAction).where(OptimizationAction.id == action_id))
    db_action = result.scalar_one_or_none()
    if db_action:
        db_action.status = "approved"
        await db.commit()
        await db.refresh(db_action)
    return db_action

async def deny_action(db: AsyncSession, action_id: str) -> Optional[OptimizationAction]:
    result = await db.execute(select(OptimizationAction).where(OptimizationAction.id == action_id))
    db_action = result.scalar_one_or_none()
    if db_action:
        db_action.status = "denied"
        await db.commit()
        await db.refresh(db_action)
    return db_action
