import pytest
import pytest_asyncio
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.database.base import Base, get_db
from backend.api.main import app

# --- Test Database Configuration ---

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# --- Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="function")
async def client(db_session):
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

# --- Authentication Header ---

headers = {"X-API-Key": os.getenv("API_KEY", "default_secret_key")}

# --- Tests ---

@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_unauthorized_request(client):
    response = await client.get("/api/v1/llm/usage")
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_ingest_llm_usage(client):
    payload = {
        "timestamp": "2026-02-12T12:00:00Z",
        "provider": "openai",
        "model": "gpt-4o",
        "input_tokens": 100,
        "output_tokens": 50,
        "cost": 0.005,
        "latency_ms": 150.5,
        "quality_score": 0.95
    }
    response = await client.post("/api/v1/llm/usage", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["provider"] == "openai"
    assert "id" in data

@pytest.mark.asyncio
async def test_list_llm_usage(client):
    # Ingest some data first
    payload = {
        "timestamp": "2026-02-12T12:00:00Z",
        "provider": "anthropic",
        "model": "claude-3",
        "input_tokens": 200,
        "output_tokens": 100,
        "cost": 0.01
    }
    await client.post("/api/v1/llm/usage", json=payload, headers=headers)
    
    response = await client.get("/api/v1/llm/usage", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["provider"] == "anthropic"

@pytest.mark.asyncio
async def test_create_anomaly(client):
    payload = {
        "id": "anom-001",
        "timestamp": "2026-02-12T12:00:00Z",
        "provider": "openai",
        "service": "completions",
        "current_cost": 50.0,
        "expected_cost": 10.0,
        "deviation_percent": 400.0,
        "severity": "high",
        "description": "Sudden spike in openai completions cost"
    }
    response = await client.post("/api/v1/anomalies", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "anom-001"
    assert data["severity"] == "high"

@pytest.mark.asyncio
async def test_create_optimization_action(client):
    payload = {
        "id": "act-001",
        "timestamp": "2026-02-12T12:00:00Z",
        "action_type": "model_switching",
        "description": "Switch from gpt-4 to gpt-3.5-turbo",
        "estimated_savings": 500.0,
        "risk_level": "low",
        "requires_approval": True,
        "status": "pending"
    }
    response = await client.post("/api/v1/actions", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "act-001"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_approve_optimization_action(client):
    # Create action first
    payload = {
        "id": "act-002",
        "timestamp": "2026-02-12T12:00:00Z",
        "action_type": "caching",
        "status": "pending"
    }
    await client.post("/api/v1/actions", json=payload, headers=headers)
    
    # Approve it
    response = await client.post("/api/v1/actions/act-002/approve", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "approved"
