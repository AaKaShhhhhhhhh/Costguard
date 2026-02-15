from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy import select, update, func, cast, Date
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

async def execute_action(db: AsyncSession, action_id: str) -> Optional[OptimizationAction]:
    """Mark an action as executed after the executor agent processes it."""
    result = await db.execute(select(OptimizationAction).where(OptimizationAction.id == action_id))
    db_action = result.scalar_one_or_none()
    if db_action:
        db_action.status = "executed"
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

        # 1. Total Cost this month
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

        # 3. Daily cost history (last 30 days)
        thirty_days_ago = now - timedelta(days=30)
        daily_stmt = (
            select(
                func.date(LLMUsage.timestamp).label("date"),
                func.sum(LLMUsage.cost).label("cost")
            )
            .where(LLMUsage.timestamp >= thirty_days_ago)
            .group_by(func.date(LLMUsage.timestamp))
            .order_by(func.date(LLMUsage.timestamp))
        )
        daily_res = await db.execute(daily_stmt)
        daily_rows = daily_res.all()
        daily_costs = [{"date": str(d), "cost": float(c or 0)} for d, c in daily_rows]

        # 4. Provider breakdown
        provider_stmt = (
            select(LLMUsage.provider, func.sum(LLMUsage.cost).label("total"))
            .group_by(LLMUsage.provider)
            .order_by(func.sum(LLMUsage.cost).desc())
        )
        provider_res = await db.execute(provider_stmt)
        provider_rows = provider_res.all()
        provider_breakdown = [{"provider": str(p), "cost": float(c or 0)} for p, c in provider_rows]

        return {
            "current_month_cost": total_cost,
            "delta_percent": "+0.0%",
            "top_services": top_services,
            "daily_costs": daily_costs,
            "provider_breakdown": provider_breakdown,
        }

    except Exception as e:
        print(f"ERROR in get_cost_summary: {e}")
        return {
            "current_month_cost": 0.0,
            "delta_percent": "0.0%",
            "top_services": [],
            "daily_costs": [],
            "provider_breakdown": [],
        }


# --- Stats Repositories ---

async def get_anomaly_stats(db: AsyncSession) -> dict:
    """Get anomaly statistics for dashboard charts."""
    try:
        # Severity breakdown
        sev_stmt = (
            select(CostAnomaly.severity, func.count(CostAnomaly.id).label("count"))
            .group_by(CostAnomaly.severity)
        )
        sev_res = await db.execute(sev_stmt)
        severity_breakdown = [{"severity": s or "unknown", "count": int(c)} for s, c in sev_res.all()]

        # Provider breakdown
        prov_stmt = (
            select(CostAnomaly.provider, func.count(CostAnomaly.id).label("count"))
            .group_by(CostAnomaly.provider)
        )
        prov_res = await db.execute(prov_stmt)
        provider_breakdown = [{"provider": p or "unknown", "count": int(c)} for p, c in prov_res.all()]

        # Timeline (anomalies per day for last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        timeline_stmt = (
            select(
                func.date(CostAnomaly.timestamp).label("date"),
                func.count(CostAnomaly.id).label("count"),
                func.avg(CostAnomaly.deviation_percent).label("avg_deviation")
            )
            .where(CostAnomaly.timestamp >= thirty_days_ago)
            .group_by(func.date(CostAnomaly.timestamp))
            .order_by(func.date(CostAnomaly.timestamp))
        )
        timeline_res = await db.execute(timeline_stmt)
        timeline = [{"date": str(d), "count": int(c), "avg_deviation": float(dev or 0)} for d, c, dev in timeline_res.all()]

        return {
            "severity_breakdown": severity_breakdown,
            "provider_breakdown": provider_breakdown,
            "timeline": timeline,
        }
    except Exception as e:
        print(f"ERROR in get_anomaly_stats: {e}")
        return {"severity_breakdown": [], "provider_breakdown": [], "timeline": []}


async def get_action_stats(db: AsyncSession) -> dict:
    """Get optimization action statistics for dashboard charts."""
    try:
        status_stmt = (
            select(OptimizationAction.status, func.count(OptimizationAction.id).label("count"))
            .group_by(OptimizationAction.status)
        )
        status_res = await db.execute(status_stmt)
        status_breakdown = [{"status": s or "unknown", "count": int(c)} for s, c in status_res.all()]

        # Total estimated savings
        savings_stmt = select(func.sum(OptimizationAction.estimated_savings))
        savings_res = await db.execute(savings_stmt)
        total_savings = float(savings_res.scalar() or 0.0)

        # Savings by status
        saved_stmt = (
            select(func.sum(OptimizationAction.estimated_savings))
            .where(OptimizationAction.status.in_(["approved", "executed"]))
        )
        saved_res = await db.execute(saved_stmt)
        realized_savings = float(saved_res.scalar() or 0.0)

        return {
            "status_breakdown": status_breakdown,
            "total_potential_savings": total_savings,
            "realized_savings": realized_savings,
        }
    except Exception as e:
        print(f"ERROR in get_action_stats: {e}")
        return {"status_breakdown": [], "total_potential_savings": 0, "realized_savings": 0}
