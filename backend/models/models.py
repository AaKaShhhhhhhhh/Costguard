from datetime import datetime
from typing import Optional, Any, Dict
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from backend.database.base import Base

class LLMUsage(Base):
    """
    Tracks LLM usage events including tokens, cost, and metadata.
    """
    __tablename__ = "llm_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    provider = Column(String, nullable=False, index=True)
    model = Column(String, nullable=False, index=True)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)

    def __repr__(self):
        return f"<LLMUsage(id={self.id}, provider='{self.provider}', model='{self.model}', cost={self.cost})>"

class CostAnomaly(Base):
    """
    Stores detected cost anomalies with deviation details and severity.
    """
    __tablename__ = "cost_anomaly"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    provider = Column(String, index=True)
    service = Column(String, index=True)
    current_cost = Column(Float)
    expected_cost = Column(Float)
    deviation_percent = Column(Float)
    severity = Column(String, index=True)  # e.g., low, medium, high, critical
    description = Column(String)
    meta = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<CostAnomaly(id='{self.id}', severity='{self.severity}', deviation={self.deviation_percent}%)>"

class OptimizationAction(Base):
    """
    Represents optimization actions that can be taken to reduce costs.
    """
    __tablename__ = "optimization_action"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    action_type = Column(String, index=True)
    description = Column(String)
    estimated_savings = Column(Float)
    risk_level = Column(String, index=True)  # e.g., low, medium, high
    requires_approval = Column(Boolean, default=False)
    auto_approved = Column(Boolean, default=False)
    status = Column(String, default="pending", index=True)  # e.g., pending, approved, denied, executed
    meta = Column(JSON, nullable=True)

    def __repr__(self):
        return f"<OptimizationAction(id='{self.id}', type='{self.action_type}', status='{self.status}')>"
