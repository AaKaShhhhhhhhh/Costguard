# CostGuard Backend Implementation Plan

## Required Folder Structure
```
backend/
├─ api/
│  ├─ main.py
│  └─ v1/
│     ├─ routes.py
│     └─ endpoints.py
├─ models/
│  └─ models.py
├─ services/
│  └─ repositories.py
├─ database/
│  └─ base.py
├─ alembic/
│  ├─ env.py
│  ├─ script.py.mako
│  └─ versions/
├─ alembic.ini
├─ tests/
│  └─ test_api.py
├─ run_tests.sh
├─ README.md
└─ IMPLEMENTATION_PLAN.md
```

## Dependencies
- fastapi
- uvicorn
- sqlalchemy
- alembic
- asyncpg
- aiosqlite
- pydantic
- pydantic-settings
- pytest
- httpx

## Order of Implementation
1. Project structure & structure boilerplate.
2. Database models and base configuration.
3. Alembic initialization and migration.
4. Repository layer.
5. API layer (Schemas -> Endpoints -> Routes -> Main).
6. Authentication.
7. Testing.
8. Documentation.

## Migration Plan
- Use `alembic init alembic` inside `backend/`.
- Configure `alembic.ini` and `env.py` for async support.
- Initial migration covering all three models.

## Testing Strategy
- Pytest with `httpx.AsyncClient`.
- SQLite in-memory database with schema creation on setup.
- Override `get_db` dependency for testing.
