#!/bin/bash
# Complete backend setup script per Codex's instructions
set -e

echo "🔧 Setting up clean environment for optimal_build backend..."

# 1. Install dependencies (continuing from background process)
echo "⏳ Waiting for pip install to complete..."
# (already running in background)

# 2. Install dev dependencies
echo "📦 Installing dev dependencies..."
.venv/bin/pip install -r backend/requirements-dev.txt -q

# 3. Reset Postgres (WARNING: This wipes all data!)
echo "🗄️  Resetting Postgres database..."
docker compose down -v
docker compose up -d postgres redis minio

# Wait for Postgres to be ready
echo "⏳ Waiting for Postgres to start..."
sleep 10

# 4. Run migrations
echo "🔄 Running database migrations..."
export DATABASE_URL="postgresql://postgres:password@localhost:5432/building_compliance"
export PYTHONPATH=/Users/wakaekihara/GitHub/optimal_build
.venv/bin/alembic -c backend/alembic.ini upgrade heads

# 5. Verify single head
echo "✅ Verifying migration state..."
.venv/bin/alembic -c backend/alembic.ini heads

# 6. Seed database
echo "🌱 Seeding database with properties, finance, and screening data..."
.venv/bin/python -m backend.scripts.seed_properties_projects --reset
.venv/bin/python -m backend.scripts.seed_finance_demo
.venv/bin/python -m backend.scripts.seed_screening

# 7. Create test property (if script exists)
if [ -f "create_test_property.py" ]; then
  echo "🏢 Creating test property..."
  .venv/bin/python create_test_property.py > test_property_id.txt
  echo "✅ Test property ID saved to test_property_id.txt"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the backend:"
echo "  export DATABASE_URL=\"postgresql+asyncpg://postgres:password@localhost:5432/building_compliance\""
echo "  export SQLALCHEMY_DATABASE_URI=\"\$DATABASE_URL\""
echo "  .venv/bin/uvicorn backend.app.main:app --reload --port 9400"
echo ""
echo "To start the frontend:"
echo "  cd frontend && VITE_API_BASE=http://localhost:9400 npm run dev -- --port 4400"
echo ""
echo "Test property ID (if created): $(cat test_property_id.txt 2>/dev/null || echo 'Run create_test_property.py manually')"
