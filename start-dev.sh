#!/bin/bash
# Load environment variables from backend/.env and start development servers

set -a  # automatically export all variables
source backend/.env
set +a

echo "✅ Loaded environment from backend/.env"
echo "   DATABASE_URL: $DATABASE_URL"
echo ""

exec make dev
