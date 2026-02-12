# CostGuard Backend

Asynchronous FastAPI-based backend for CostGuard with SQLAlchemy persistence and Alembic migrations.

## Virtualenv Setup

```bash
python -m venv .venv
# On Windows
.\.venv\Scripts\activate
# On Unix or MacOS
source .venv/bin/activate

pip install -e .
pip install -r requirements.txt
```

## Required Dependencies

All required libraries are listed in [requirements.txt](file:///c:/Users/himan/Desktop/Project/Costguard/backend/requirements.txt).

- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `sqlalchemy`: SQL toolkit and ORM
- `alembic`: Database migrations
- `aiosqlite`: Async SQLite driver (for local dev/test)
- `asyncpg`: Async PostgreSQL driver (for production)
- `pydantic`: Data validation
- `pytest`, `pytest-asyncio`, `httpx`: Testing

## Environment Variables (.env)

Create a `.env` file in the `backend/` directory:

```env
DATABASE_URL=sqlite+aiosqlite:///./costguard.db
API_KEY=your_secret_api_key_here
```

## Database Migrations

Run migrations from the `backend/` directory:

```bash
# Set PYTHONPATH to include the project root if needed
$env:PYTHONPATH=".." # PowerShell

# Run migrations
python -m alembic upgrade head
```

## Running the Server

Start the FastAPI server:

```bash
python -m uvicorn backend.api.main:app --reload
```

The API will be available at `http://localhost:8000`.
Documentation can be accessed at `http://localhost:8000/docs`.

## Running Tests

Execute the test suite:

```bash
# On Unix/MacOS
./run_tests.sh

# On Windows (PowerShell)
$env:PYTHONPATH=".."
pytest tests -v
```
