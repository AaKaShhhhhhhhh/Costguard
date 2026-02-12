#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up CostGuard AI..."

# Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3.10+ is required"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 16+ is required"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if python3 - <<'PY'
import sys
v = sys.version_info
print(v[:2] < (3,10))
PY | grep True &> /dev/null; then
    echo "❌ Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✅ Prerequisites met"

# Install uv (as requested by template)
echo "📦 Installing uv package manager (if available)..."
pip install --upgrade uv || true

# Install MCP Inspector
echo "🔍 Installing MCP Inspector..."
npm install -g @modelcontextprotocol/inspector || true

# Create virtual environment
echo "🐍 Creating virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install -e . || true

# Create .env file from template
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your API keys"
fi

# Initialize database if script exists
if [ -f scripts/init-db.py ]; then
    echo "🗄️  Initializing database..."
    python scripts/init-db.py || true
fi

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Update .env with your API keys"
echo "  2. Run 'make dev' to start development environment"
echo "  3. Access dashboard at http://localhost:8501"
