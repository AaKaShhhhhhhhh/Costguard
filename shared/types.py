"""Shared type definitions and Pydantic models used across services.

This module centralizes common enums and models so MCP servers, agents,
and the API share the same types.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class CloudProvider(str, Enum):
    """Supported cloud providers."""

    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class Severity(str, Enum):
    """Severity levels for anomalies and alerts."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CostAnomaly(BaseModel):
    """Model describing a detected cost anomaly."""

    id: str = Field(..., description="Unique anomaly identifier")
    timestamp: datetime
    provider: CloudProvider
    service: str
    current_cost: float
    expected_cost: float
    deviation_percent: float
    severity: Severity
    description: str


class OptimizationAction(BaseModel):
    """Represents an optimization recommendation or action."""

    id: str
    timestamp: datetime
    action_type: str
    description: str
    estimated_savings: float
    risk_level: str
    requires_approval: bool
    auto_approved: bool = False
    status: str = "pending"


class LLMUsage(BaseModel):
    """Tracks LLM usage metrics for cost analysis and routing."""

    timestamp: datetime
    provider: LLMProvider
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    quality_score: Optional[float] = None
