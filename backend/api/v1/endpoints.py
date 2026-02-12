from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database.base import get_db
from backend.services import repositories
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
    return await repositories.create_anomaly(db, anomaly.dict())

@router.get("/anomalies", response_model=List[schemas.CostAnomaly])
async def list_anomalies(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await repositories.list_anomalies(db, skip=skip, limit=limit)

# --- Optimization Action Endpoints ---

@router.post("/actions", response_model=schemas.OptimizationAction, status_code=status.HTTP_201_CREATED)
async def create_action(action: schemas.OptimizationActionCreate, db: AsyncSession = Depends(get_db)):
    return await repositories.create_action(db, action.dict())

@router.post("/actions/{id}/approve", response_model=schemas.OptimizationAction)
async def approve_action(id: str, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.approve_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    return db_action

@router.post("/actions/{id}/deny", response_model=schemas.OptimizationAction)
async def deny_action(id: str, db: AsyncSession = Depends(get_db)):
    db_action = await repositories.deny_action(db, id)
    if not db_action:
        raise HTTPException(status_code=404, detail="Action not found")
    return db_action
