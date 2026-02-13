from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.base import get_db
from backend.services import repositories, integration
from datetime import datetime, timedelta
import uuid
from backend.models.models import CostAnomaly
from backend.api.v1 import schemas

router = APIRouter()

# --- LLM Usage Endpoints ---

@router.post("/llm/usage", response_model=schemas.LLMUsage, status_code=status.HTTP_201_CREATED)
async def ingest_usage(usage: schemas.LLMUsageCreate, db: AsyncSession = Depends(get_db)):
    return await repositories.create_llm_usage(db, usage.dict())

@router.get("/llm/usage", response_model=List[schemas.LLMUsage])
async def list_usage(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_llm_usage(db, skip=skip, limit=limit)

# --- Cost Anomaly Endpoints ---

@router.post("/anomalies", response_model=schemas.CostAnomaly, status_code=status.HTTP_201_CREATED)
async def create_anomaly(anomaly: schemas.CostAnomalyCreate, db: AsyncSession = Depends(get_db)):
    db_anomaly = await repositories.create_anomaly(db, anomaly.dict())
    
    # Simulate Team C Notification requirement
    print(f"ALARM: Slack notification sent to #cost-alerts: New {db_anomaly.severity} anomaly detected on {db_anomaly.service}")
    
    return db_anomaly

@router.get("/anomalies", response_model=List[schemas.CostAnomaly])
async def list_anomalies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_anomalies(db, skip=skip, limit=limit)

# --- Optimization Action Endpoints ---

@router.post("/actions", response_model=schemas.OptimizationAction, status_code=status.HTTP_201_CREATED)
async def create_action(action: schemas.OptimizationActionCreate, db: AsyncSession = Depends(get_db)):
    return await repositories.create_action(db, action.dict())

@router.post("/actions/{id}/approve", response_model=schemas.OptimizationAction)
async def approve_action(id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.approve_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Notify Archestra in background
    background_tasks.add_task(integration.notify_archestra, id, "approved")
    
    return db_action

@router.post("/actions/{id}/deny", response_model=schemas.OptimizationAction)
async def deny_action(id: str, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.deny_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Notify Archestra in background
    background_tasks.add_task(integration.notify_archestra, id, "denied")

    return db_action

@router.get("/actions", response_model=List[schemas.OptimizationAction])
async def list_actions(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_actions(db, skip=skip, limit=limit)

# --- Summary Endpoints ---

@router.get("/summary")
async def get_summary(db: AsyncSession = Depends(get_db)):
    print("DEBUG: Endpoint - calling get_cost_summary")
    try:
        res = await repositories.get_cost_summary(db)
        print(f"DEBUG: Endpoint - get_cost_summary returned: {res}")
        return res
    except Exception as e:
        print(f"DEBUG: Endpoint - error in summary: {e}")
        raise

@router.post("/debug/seed")
async def seed_data(db: AsyncSession = Depends(get_db)):
    # Check if anomalies exist
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
