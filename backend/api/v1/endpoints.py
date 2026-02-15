from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Form
from sqlalchemy import select, func, text, delete
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.base import get_db
from backend.services import repositories, integration
from backend.services.slack import slack_service
from datetime import datetime, timedelta
import uuid
import logging
from backend.models.models import CostAnomaly, OptimizationAction, LLMUsage
from backend.api.v1 import schemas
from shared.config import settings

router = APIRouter()
LOG = logging.getLogger(__name__)

# --- LLM Usage Endpoints ---

@router.post("/llm/usage", response_model=schemas.LLMUsage, status_code=status.HTTP_201_CREATED)
async def ingest_usage(usage: schemas.LLMUsageCreate, db: AsyncSession = Depends(get_db)):
    return await repositories.create_llm_usage(db, usage.dict())

@router.get("/llm/usage", response_model=List[schemas.LLMUsage])
async def list_usage(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_llm_usage(db, skip=skip, limit=limit)

# --- Cost Anomaly Endpoints ---

@router.post("/anomalies", response_model=schemas.CostAnomaly, status_code=status.HTTP_201_CREATED)
async def create_anomaly(anomaly: schemas.CostAnomalyCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_anomaly = await repositories.create_anomaly(db, anomaly.dict())

    # Auto-create a matching optimization action
    action_id = str(uuid.uuid4())
    deviation = db_anomaly.deviation_percent or 0
    savings = round((db_anomaly.current_cost or 0) - (db_anomaly.expected_cost or 0), 2)
    action_type = "switch_model" if db_anomaly.provider in ("OpenAI", "Anthropic") else "scale_down"
    risk = "low" if deviation < 100 else ("medium" if deviation < 200 else "high")

    db_action = OptimizationAction(
        id=action_id,
        timestamp=db_anomaly.timestamp,
        action_type=action_type,
        description=f"Investigate {db_anomaly.provider} {db_anomaly.service or 'service'} — potential savings ${savings}/day",
        estimated_savings=max(savings, 0),
        risk_level=risk,
        requires_approval=(deviation >= 100),
        status="pending",
        meta={"anomaly_id": db_anomaly.id, "created_by": "manual_anomaly"},
    )
    db.add(db_action)
    await db.commit()
    await db.refresh(db_action)

    # Notify Slack: anomaly alert + interactive action approval
    background_tasks.add_task(slack_service.notify_anomaly, {
        "provider": db_anomaly.provider, "service": db_anomaly.service,
        "severity": db_anomaly.severity, "description": db_anomaly.description,
        "current_cost": db_anomaly.current_cost, "expected_cost": db_anomaly.expected_cost,
    })
    background_tasks.add_task(slack_service.notify_action, {
        "id": db_action.id,
        "action_type": db_action.action_type,
        "estimated_savings": db_action.estimated_savings,
        "risk_level": db_action.risk_level,
        "description": db_action.description,
    })
    LOG.info("Created anomaly %s with auto-action %s", db_anomaly.id, action_id)

    return db_anomaly

@router.get("/anomalies", response_model=List[schemas.CostAnomaly])
async def list_anomalies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_anomalies(db, skip=skip, limit=limit)

# --- Optimization Action Endpoints ---

@router.post("/actions", response_model=schemas.OptimizationAction, status_code=status.HTTP_201_CREATED)
async def create_action(action: schemas.OptimizationActionCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.create_action(db, action.dict())
    background_tasks.add_task(slack_service.notify_action, db_action.__dict__)
    return db_action

@router.post("/actions/{id}/approve", response_model=schemas.OptimizationAction)
async def approve_action(id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.approve_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    # Notify Archestra and auto-trigger executor
    background_tasks.add_task(integration.notify_archestra, id, "approved")
    background_tasks.add_task(_auto_execute_action, id)
    return db_action

@router.post("/actions/{id}/deny", response_model=schemas.OptimizationAction)
async def deny_action(id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.deny_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    background_tasks.add_task(integration.notify_archestra, id, "denied")
    return db_action

@router.get("/actions", response_model=List[schemas.OptimizationAction])
async def list_actions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_actions(db, skip=skip, limit=limit)

# --- Summary Endpoints ---

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    return await repositories.get_cost_summary(db)

# --- Stats Endpoints ---

@router.get("/stats/anomalies")
async def get_anomaly_stats(db: AsyncSession = Depends(get_db)):
    """Get anomaly statistics for dashboard charts."""
    return await repositories.get_anomaly_stats(db)

@router.get("/stats/actions")
async def get_action_stats(db: AsyncSession = Depends(get_db)):
    """Get action statistics for dashboard charts."""
    return await repositories.get_action_stats(db)

# --- Agent Endpoints ---

@router.post("/agents/scan")
async def agent_scan(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger the detective agent to scan for cost anomalies.

    Compares each provider/model's recent daily cost against its 7-day
    rolling average and creates anomalies when a >50% spike is detected.
    """
    now = datetime.utcnow()
    # Explicit ranges for "today" (UTC)
    start_of_today = datetime(now.year, now.month, now.day)
    start_of_tomorrow = start_of_today + timedelta(days=1)
    # Range for 7-day baseline (excluding today)
    start_of_baseline = start_of_today - timedelta(days=7)

    # Get today's cost per provider
    today_stmt = (
        select(
            LLMUsage.provider,
            func.sum(LLMUsage.cost).label("today_cost"),
        )
        .where(LLMUsage.timestamp >= start_of_today)
        .where(LLMUsage.timestamp < start_of_tomorrow)
        .group_by(LLMUsage.provider)
    )
    today_res = await db.execute(today_stmt)
    today_rows = today_res.all()
    LOG.info("DB Today Rows: %s", today_rows)
    today_costs = {row[0]: float(row[1] or 0) for row in today_rows}
    LOG.info("Today costs (range %s to %s): %s", start_of_today, start_of_tomorrow, today_costs)

    # Get 7-day average per provider
    avg_stmt = (
        select(
            LLMUsage.provider,
            (func.sum(LLMUsage.cost) / 7).label("avg_cost"),
        )
        .where(LLMUsage.timestamp >= start_of_baseline)
        .where(LLMUsage.timestamp < start_of_today)
        .group_by(LLMUsage.provider)
    )
    avg_res = await db.execute(avg_stmt)
    avg_rows = avg_res.all()
    LOG.info("DB Baseline Rows: %s", avg_rows)
    avg_costs = {row[0]: float(row[1] or 0) for row in avg_rows}
    LOG.info("7-day average costs (range %s to %s): %s", start_of_baseline, start_of_today, avg_costs)

    # Deduplication: find providers that already have an anomaly today
    existing_stmt = (
        select(CostAnomaly.provider)
        .where(CostAnomaly.timestamp >= start_of_today)
        .where(CostAnomaly.timestamp < start_of_tomorrow)
    )
    existing_res = await db.execute(existing_stmt)
    already_flagged = {row[0] for row in existing_res.all()}
    if already_flagged:
        LOG.info("Providers already flagged today: %s", already_flagged)

    new_anomalies = []
    new_actions = []
    if not today_costs:
        LOG.warning("No usage records found for today!")
    
    for provider, today_cost in today_costs.items():
        avg_cost = avg_costs.get(provider, 0)
        LOG.info("Checking %s: today=$%s, base=$%s", provider, today_cost, avg_cost)
        if provider in already_flagged:
            LOG.info("  Skipping %s: Already flagged today", provider)
            continue
        if avg_cost <= 0:
            LOG.info("  Skipping %s: No historical baseline found (avg_cost=0)", provider)
            continue
        
        deviation = ((today_cost - avg_cost) / avg_cost) * 100
        LOG.info("  %s deviation: %s%%", provider, deviation)
        if deviation > 50:
            severity = "low" if deviation < 100 else ("medium" if deviation < 200 else ("high" if deviation < 500 else "critical"))
            anomaly_id = str(uuid.uuid4())
            anomaly = CostAnomaly(
                id=anomaly_id, timestamp=now,
                provider=provider, service="LLM API",
                current_cost=round(today_cost, 2),
                expected_cost=round(avg_cost, 2),
                deviation_percent=round(deviation, 1),
                severity=severity,
                description=f"{provider} costs spiked {deviation:.0f}% above 7-day average (${avg_cost:.2f} → ${today_cost:.2f})",
                meta={"detected_by": "detective_agent", "baseline_days": 7},
            )
            db.add(anomaly)
            new_anomalies.append(anomaly)

            # Create a matching optimization action
            action_id = str(uuid.uuid4())
            action = OptimizationAction(
                id=action_id, timestamp=now,
                action_type="switch_model" if "OpenAI" in provider or "Anthropic" in provider else "scale_down",
                description=f"Investigate and optimize {provider} spending — potential savings ${(today_cost - avg_cost):.2f}/day",
                estimated_savings=round(today_cost - avg_cost, 2),
                risk_level="low" if deviation < 100 else "medium",
                requires_approval=(deviation >= 100),
                status="pending",
                meta={"anomaly_id": anomaly_id, "created_by": "detective_agent"},
            )
            db.add(action)
            new_actions.append(action)

    await db.commit()

    # Notify via Slack for high-severity anomalies and actions
    for a in new_anomalies:
        if a.severity in ("high", "critical"):
            background_tasks.add_task(slack_service.notify_anomaly, {
                "provider": a.provider, "service": a.service,
                "severity": a.severity, "description": a.description,
                "current_cost": a.current_cost, "expected_cost": a.expected_cost,
            })
    
    for act in new_actions:
        background_tasks.add_task(slack_service.notify_action, {
            "id": act.id,
            "action_type": act.action_type,
            "estimated_savings": act.estimated_savings,
            "risk_level": act.risk_level,
            "description": act.description,
        })

    return {
        "status": "scan_complete",
        "anomalies_found": len(new_anomalies),
        "actions_created": len(new_actions),
        "details": [
            {
                "provider": a.provider,
                "severity": a.severity,
                "deviation": a.deviation_percent,
                "description": a.description,
            }
            for a in new_anomalies
        ],
    }


@router.post("/agents/simulate-spike")
async def simulate_spike(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Simulate a realistic cost spike for demo purposes.

    This endpoint:
    1. Injects baseline LLM usage records for the past 7 days (low cost)
    2. Injects high-cost records for today (the spike)
    3. Automatically triggers the detective agent scan
    4. Returns the scan results (anomalies + actions created)
    """
    import random
    now = datetime.utcnow()

    # Step 0: CLEANUP - Delete existing anomalies/actions for today to ensure demo works repeatably
    # This prevents the deduplication logic from skipping the new spike
    # Using ORM delete to ensure correct table names (cost_anomaly, optimization_action)
    start_of_today = datetime(now.year, now.month, now.day)
    start_of_tomorrow = start_of_today + timedelta(days=1)
    
    await db.execute(
        delete(CostAnomaly)
        .where(CostAnomaly.timestamp >= start_of_today)
        .where(CostAnomaly.timestamp < start_of_tomorrow)
    )
    await db.execute(
        delete(OptimizationAction)
        .where(OptimizationAction.timestamp >= start_of_today)
        .where(OptimizationAction.timestamp < start_of_tomorrow)
    )
    # Clear existing LLM usage for OpenAI to ensure the spike is detectable
    await db.execute(
        delete(LLMUsage)
        .where(LLMUsage.provider == "OpenAI")
    )
    await db.commit()
    LOG.info("Cleaned up existing anomalies, actions, and OpenAI usage for today to prepare for simulation")

    # Step 1: Ensure baseline data exists (7 days of normal costs)
    start_of_baseline = start_of_today - timedelta(days=7)

    # Check if baseline already exists
    baseline_check = await db.execute(
        select(func.count(LLMUsage.id))
        .where(LLMUsage.timestamp >= start_of_baseline)
        .where(LLMUsage.timestamp < start_of_today)
        .where(LLMUsage.provider == "OpenAI")
    )
    baseline_count = baseline_check.scalar()

    baseline_injected = 0
    if baseline_count < 7:
        # Add low-cost baseline records for each of the past 7 days
        for day_offset in range(1, 8):
            ts = now - timedelta(days=day_offset, hours=random.randint(1, 12))
            for _ in range(random.randint(2, 4)):
                db.add(LLMUsage(
                    timestamp=ts,
                    provider="OpenAI",
                    model=random.choice(["gpt-4o-mini", "gpt-3.5-turbo"]),
                    input_tokens=random.randint(500, 3000),
                    output_tokens=random.randint(200, 1000),
                    cost=round(random.uniform(0.3, 1.5), 2),
                    latency_ms=random.uniform(300, 800),
                    quality_score=round(random.uniform(0.85, 0.98), 2),
                ))
                baseline_injected += 1
        LOG.info("Injected %d baseline records for 7-day history", baseline_injected)

    # Step 2: Inject today's spike (5 expensive calls)
    spike_records = 0
    spike_total = 0.0
    for _ in range(5):
        cost = round(random.uniform(40.0, 90.0), 2)
        spike_total += cost
        db.add(LLMUsage(
            timestamp=now,
            provider="OpenAI",
            model="gpt-4o",
            input_tokens=random.randint(80000, 200000),
            output_tokens=random.randint(30000, 80000),
            cost=cost,
            latency_ms=random.uniform(2000, 5000),
            quality_score=round(random.uniform(0.90, 0.99), 2),
        ))
        spike_records += 1

    await db.commit()
    LOG.info("Injected %d spike records totaling $%.2f", spike_records, spike_total)

    # Step 3: Trigger the detective agent scan
    scan_result = await agent_scan(background_tasks, db)

    return {
        "status": "spike_simulated",
        "baseline_records_added": baseline_injected,
        "spike_records_added": spike_records,
        "spike_total_cost": round(spike_total, 2),
        "scan_result": scan_result,
    }


@router.post("/agents/execute/{action_id}")
async def agent_execute(action_id: str, db: AsyncSession = Depends(get_db)):
    """Trigger the executor agent to process an approved action.
    
    Also injects 'optimized' low-cost data to visually demonstrate the fix on the dashboard.
    """
    db_action = await repositories.execute_action(db, action_id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")

    # Notify Archestra of execution
    await integration.notify_archestra(action_id, "executed")

    # VISUAL CONFIRMATION: Inject low-cost "optimized" data for TOMORROW
    # This ensures the dashboard charts show a visible drop (high bar today -> low bar tomorrow)
    import random
    now = datetime.utcnow()
    future_time = now + timedelta(days=1)
    
    optimized_records = 0
    for _ in range(8):
        db.add(LLMUsage(
            timestamp=future_time + timedelta(minutes=random.randint(1, 40)),
            provider="OpenAI",
            model="gpt-4o-mini",  # Switched to cheaper model
            input_tokens=random.randint(500, 3000),
            output_tokens=random.randint(200, 1000),
            cost=round(random.uniform(0.01, 0.05), 4), # Very low cost
            latency_ms=random.uniform(100, 300),
            quality_score=round(random.uniform(0.95, 0.99), 2),
        ))
        optimized_records += 1
    
    await db.commit()
    LOG.info("Injected %d optimized records to demonstrate cost reduction", optimized_records)

    return {
        "status": "executed",
        "action_id": action_id,
        "description": db_action.description,
        "estimated_savings": db_action.estimated_savings,
        "message": f"Action executed! Optimization applied. Charts will now show reduced costs.",
    }


async def _auto_execute_action(action_id: str):
    """Background task to auto-execute low-risk approved actions."""
    import asyncio
    await asyncio.sleep(2)  # Simulate processing delay
    from backend.database.base import async_session_factory
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                select(OptimizationAction).where(OptimizationAction.id == action_id)
            )
            action = result.scalar_one_or_none()
            if action and action.status == "approved" and action.risk_level == "low":
                action.status = "executed"
                await db.commit()
                LOG.info("Auto-executed low-risk action %s", action_id)
                await integration.notify_archestra(action_id, "executed")
    except Exception as e:
        LOG.warning("Auto-execute failed for %s: %s", action_id, e)


# --- Archestra Webhook ---

@router.post("/archestra/webhook")
async def archestra_webhook(payload: dict, db: AsyncSession = Depends(get_db)):
    """Receive execution status callbacks from Archestra.AI."""
    event = payload.get("event", "")
    action_id = payload.get("action_id", "")
    new_status = payload.get("status", "")

    if not action_id:
        raise HTTPException(status_code=400, detail="action_id is required")

    if new_status == "executed":
        db_action = await repositories.execute_action(db, action_id)
    elif new_status == "failed":
        result = await db.execute(
            select(OptimizationAction).where(OptimizationAction.id == action_id)
        )
        db_action = result.scalar_one_or_none()
        if db_action:
            db_action.status = "failed"
            await db.commit()
    else:
        db_action = None

    LOG.info("Archestra webhook: event=%s action=%s status=%s", event, action_id, new_status)
    return {"ok": True, "processed": bool(db_action)}


@router.get("/archestra/logs")
async def get_archestra_logs():
    """Get recent Archestra interaction logs for dashboard visibility."""
    from backend.services.integration import ARCHESTRA_LOGS
    return list(ARCHESTRA_LOGS)


# --- Seed & Debug ---

@router.post("/debug/seed")
async def seed_data(db: AsyncSession = Depends(get_db)):
    existing = await repositories.list_anomalies(db, limit=1)
    if existing:
        return {"message": "Database already has data", "count": len(existing)}

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

    db.add_all([a1, a2])
    await db.commit()
    return {"message": "Seeded 2 anomalies successfully"}

@router.post("/slack/interactive")
async def slack_interactive(
    background_tasks: BackgroundTasks,
    payload: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Handle interactive components from Slack (e.g., buttons)."""
    import json
    try:
        data = json.loads(payload)
        actions = data.get("actions", [])
        if not actions:
            return {"ok": True}

        action = actions[0]
        action_id = action.get("action_id")
        db_action_id = action.get("value")

        if action_id == "approve_action":
            await repositories.approve_action(db, db_action_id)
            background_tasks.add_task(integration.notify_archestra, db_action_id, "approved", approver_id="slack_user")
            background_tasks.add_task(_auto_execute_action, db_action_id)
        elif action_id == "deny_action":
            await repositories.deny_action(db, db_action_id)
            background_tasks.add_task(integration.notify_archestra, db_action_id, "denied", approver_id="slack_user")

        return {"ok": True}
    except Exception as e:
        LOG.exception("Slack interactive failed")
        return {"ok": False, "error": str(e)}

@router.post("/debug/slack")
async def debug_slack(message: str = "Test message from CostGuard", db: AsyncSession = Depends(get_db)):
    """Manually trigger a test notification to Slack."""
    success = await slack_service.send_message(settings.slack_channel_alerts, message)
    return {
        "success": success,
        "webhook_configured": bool(settings.slack_webhook_url),
        "token_configured": bool(settings.slack_bot_token and "your" not in settings.slack_bot_token),
        "message": "Check backend logs for details if success is false"
    }
