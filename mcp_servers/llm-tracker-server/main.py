"""FastAPI app to receive and serve LLM usage metrics.

This lightweight server provides endpoints to ingest usage events and to
query recent usage. It is intentionally simple to be easy to extend.
"""
from __future__ import annotations

from typing import List
from datetime import datetime
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.types import LLMUsage, LLMProvider

app = FastAPI(title="LLM Tracker Server")

# In-memory store for usage events in this scaffold. Replace with DB in prod.
_USAGE_EVENTS: List[LLMUsage] = []


class UsageIn(BaseModel):
    provider: LLMProvider
    model: str
    input_tokens: int
    output_tokens: int
    cost: float
    latency_ms: float
    quality_score: float | None = None


@app.post("/usage", status_code=201)
async def ingest_usage(payload: UsageIn) -> dict:
    """Ingest a single LLM usage event.

    The event is appended to an in-memory list for demonstration purposes.
    """
    event = LLMUsage(
        timestamp=datetime.utcnow(),
        provider=payload.provider,
        model=payload.model,
        input_tokens=payload.input_tokens,
        output_tokens=payload.output_tokens,
        cost=payload.cost,
        latency_ms=payload.latency_ms,
        quality_score=payload.quality_score,
    )
    _USAGE_EVENTS.append(event)
    return {"status": "ok", "id": len(_USAGE_EVENTS) - 1}


@app.get("/usage", response_model=List[LLMUsage])
async def list_usage(limit: int = 100) -> List[LLMUsage]:
    """Return recent usage events (most recent first)."""
    if limit <= 0:
        raise HTTPException(status_code=400, detail="limit must be > 0")
    return list(reversed(_USAGE_EVENTS))[:limit]
