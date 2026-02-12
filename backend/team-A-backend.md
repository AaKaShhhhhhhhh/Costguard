# Team A — Backend & Persistence Guide

This document explains exactly what Team A should implement: API, database models, migrations, and tests. It includes data formats, setup steps, example SQLAlchemy models, Alembic migration hints, and example endpoints.

Summary
- Owner: Team A
- Scope: implement the `backend/` FastAPI service, SQLAlchemy models, Alembic migrations, repositories, and unit tests. Replace in-memory stores used by `mcp-servers/llm-tracker-server` and `agents/` with DB persistence.

Environments & prerequisites
- Python 3.10+
- Install project dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install sqlalchemy alembic asyncpg psycopg[binary]  # if using Postgres
```

- Set `.env` (copy from `.env.example`) and set `DATABASE_URL`.
  - For local dev, use SQLite: `DATABASE_URL=sqlite+aiosqlite:///./costguard.db`
  - For production or CI, prefer Postgres: `postgresql+asyncpg://user:pass@localhost:5432/costguard`

Project structure (what Team A will add)

```
backend/
├─ api/
│  ├─ __init__.py
│  ├─ main.py            # FastAPI app
│  └─ v1/
│     ├─ routes.py       # router registration
│     └─ endpoints.py    # endpoints implementations
├─ models/
│  └─ models.py          # SQLAlchemy ORM models
├─ services/
│  └─ repositories.py    # DB access functions
├─ database/
│  └─ base.py            # engine, session maker
└─ tests/
   └─ test_api.py
```

Data formats (Pydantic / API payloads)

- LLM usage event (ingest): matches `shared/types.LLMUsage`

```json
{
  "timestamp": "2026-02-12T12:00:00Z",
  "provider": "openai",
  "model": "gpt-4o",
  "input_tokens": 120,
  "output_tokens": 80,
  "cost": 0.012,
  "latency_ms": 210,
  "quality_score": 0.98
}
```

- Cost anomaly object (persisted): matches `shared/types.CostAnomaly` (store JSON with fields)

- Optimization action object: matches `shared/types.OptimizationAction`.

DB schema (example SQLAlchemy models)

Add `backend/models/models.py`:

```py
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class LLMUsage(Base):
    __tablename__ = "llm_usage"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False)
    latency_ms = Column(Float, nullable=True)
    quality_score = Column(Float, nullable=True)

class CostAnomaly(Base):
    __tablename__ = "cost_anomaly"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    provider = Column(String)
    service = Column(String)
    current_cost = Column(Float)
    expected_cost = Column(Float)
    deviation_percent = Column(Float)
    severity = Column(String)
    description = Column(String)
    meta = Column(JSON, nullable=True)

class OptimizationAction(Base):
    __tablename__ = "optimization_action"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    action_type = Column(String)
    description = Column(String)
    estimated_savings = Column(Float)
    risk_level = Column(String)
    requires_approval = Column(Boolean, default=False)
    auto_approved = Column(Boolean, default=False)
    status = Column(String, default="pending")
    meta = Column(JSON, nullable=True)
```

Async DB setup (example)

Create `backend/database/base.py`:

```py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from shared.config import settings

engine = create_async_engine(settings.database_url, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

Alembic migrations

1. Install alembic in your env: `pip install alembic`
2. Initialize alembic in repo root:

```bash
alembic init alembic
```

3. Edit `alembic.ini` to set `sqlalchemy.url = <your DATABASE_URL or use env var>`.
4. Configure `env.py` to use async engine and import `Base` from `backend.models.models`.
5. Create initial migration:

```bash
alembic revision --autogenerate -m "initial schema"
alembic upgrade head
```

API endpoints (examples)

- `POST /api/v1/llm/usage` — ingest LLM usage (write into `llm_usage` table)
- `GET /api/v1/llm/usage` — list recent usage
- `POST /api/v1/anomalies` — insert anomaly
- `GET /api/v1/anomalies` — fetch anomalies
- `POST /api/v1/actions` — create optimization action
- `POST /api/v1/actions/{id}/approve` — approve action (record approver)

Example `backend/api/main.py` (minimal):

```py
from fastapi import FastAPI, Depends
from backend.database.base import get_db

app = FastAPI()

@app.post('/api/v1/llm/usage')
async def ingest_usage(payload: dict, db=Depends(get_db)):
    # validate using pydantic, write to DB
    return {"status":"ok"}
```

Repository layer & services

- Implement `backend/services/repositories.py` with CRUD functions using `AsyncSession` (separate business logic from endpoints).

Tests

- Add `backend/tests/test_api.py` that uses `httpx.AsyncClient` and a test database (e.g., sqlite in-memory) to verify endpoints.

CI notes

- Add GitHub Actions job to run tests and alembic migrations.

Security & operational notes

- Do not commit `.env`.
- Use DB connection pooling and credential rotation for production.
- Add RBAC and authentication for endpoints (JWT or API keys) — Team A should propose an authentication plan.

Deliverables (concrete)

1. `backend/` scaffold with working `POST /api/v1/llm/usage` that persists events.
2. SQLAlchemy models implemented and Alembic migration generated.
3. Unit tests and CI job that runs tests.
4. README in `backend/` with setup steps.

If you want, I can scaffold the `backend/` minimal files now (models, DB base, main app, and one endpoint). Reply 'scaffold backend' and I'll create them.
