#!/bin/bash
set -e

# Run migrations
echo "Running migrations..."
alembic -c backend/alembic.ini upgrade head

echo "Seeding data (if empty)..."
python backend/seed_db.py

echo "Starting backend..."
exec uvicorn backend.api.main:app --host 0.0.0.0 --port 8000
