from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.models import LLMUsage, CostAnomaly, OptimizationAction

# --- Helper ---
def ensure_naive_utc(dt):
    if dt and dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

# --- LLM Usage Repositories ---

async def create_llm_usage(db: AsyncSession, usage_data: dict) -> LLMUsage:
    if "timestamp" in usage_data:
        usage_data["timestamp"] = ensure_naive_utc(usage_data["timestamp"])
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
    if "timestamp" in anomaly_data:
        anomaly_data["timestamp"] = ensure_naive_utc(anomaly_data["timestamp"])
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
    if "timestamp" in action_data:
        action_data["timestamp"] = ensure_naive_utc(action_data["timestamp"])
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

async def list_actions(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[OptimizationAction]:
    result = await db.execute(select(OptimizationAction).offset(skip).limit(limit).order_by(OptimizationAction.timestamp.desc()))
    return result.scalars().all()

# --- Summary Repositories ---

async def get_cost_summary(db: AsyncSession) -> dict:
    try:
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        # 1. Total Cost
        cost_stmt = select(func.sum(LLMUsage.cost)).where(LLMUsage.timestamp >= month_start)
        cost_res = await db.execute(cost_stmt)
        raw_total = cost_res.scalar()
        total_cost = float(raw_total or 0.0)

        # 2. Top Services
        service_stmt = (
            select(LLMUsage.provider, func.sum(LLMUsage.cost).label("total"))
            .group_by(LLMUsage.provider)
            .order_by(func.sum(LLMUsage.cost).desc())
            .limit(5)
        )
        service_res = await db.execute(service_stmt)
        rows = service_res.all()
        
        top_services = []
        for provider, cost_sum in rows:
            top_services.append({
                "Service": str(provider or "Unknown"),
                "Cost": float(cost_sum or 0.0)
            })

        return {
            "current_month_cost": total_cost,
            "delta_percent": "+0.0%", 
            "top_services": top_services
        }
        
    except Exception as e:
        print(f"ERROR in get_cost_summary: {e}")
        # Return a valid empty summary instead of 500ing
        return {
            "current_month_cost": 0.0,
            "delta_percent": "0.0%",
            "top_services": []
        }
