from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

# --- LLM Usage Schemas ---

class LLMUsageBase(BaseModel):
    timestamp: datetime
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: Optional[float] = None
    quality_score: Optional[float] = None

class LLMUsageCreate(LLMUsageBase):
    pass

class LLMUsage(LLMUsageBase):
    id: int

    class Config:
        from_attributes = True

# --- Cost Anomaly Schemas ---

class CostAnomalyBase(BaseModel):
    id: str
    timestamp: datetime
    provider: Optional[str] = None
    service: Optional[str] = None
    current_cost: Optional[float] = None
    expected_cost: Optional[float] = None
    deviation_percent: Optional[float] = None
    severity: Optional[str] = None
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class CostAnomalyCreate(CostAnomalyBase):
    pass

class CostAnomaly(CostAnomalyBase):
    class Config:
        from_attributes = True

# --- Optimization Action Schemas ---

class OptimizationActionBase(BaseModel):
    id: str
    timestamp: datetime
    action_type: Optional[str] = None
    description: Optional[str] = None
    estimated_savings: Optional[float] = None
    risk_level: Optional[str] = None
    requires_approval: bool = False
    auto_approved: bool = False
    status: str = "pending"
    meta: Optional[Dict[str, Any]] = None

class OptimizationActionCreate(OptimizationActionBase):
    pass

class OptimizationAction(OptimizationActionBase):
    class Config:
        from_attributes = True

# --- Cost Summary Schemas ---

class CostSummary(BaseModel):
    current_month_cost: float
    delta_percent: str
    top_services: List[Dict[str, Any]]

