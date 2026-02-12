@echo off
echo 🚀 Setting up CostGuard AI on Windows...

REM Check python
where python >nul 2>&1 || (
  echo Python not found. Please install Python 3.10+.
  exit /b 1
)

REM Create virtual environment
python -m venv .venv
call .venv\Scripts\activate

echo Installing Python dependencies (may take a while)...
pip install -e . || echo Failed to install some packages

if not exist .env (
  copy .env.example .env
  echo Created .env from template. Please update keys.
)

echo Setup complete. Run "make dev" or start services as needed.
