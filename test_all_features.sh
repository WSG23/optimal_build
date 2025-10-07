#!/bin/bash
# Comprehensive Feature Testing Script for Optimal Build

set -e

echo "═══════════════════════════════════════════════════"
echo "🧪 OPTIMAL BUILD - FEATURE TESTING SUITE"
echo "═══════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
PASSED=0
FAILED=0

# Helper function
test_endpoint() {
    local name="$1"
    local url="$2"
    local headers="$3"

    echo -n "Testing $name... "
    if curl -s -f ${headers:+-H "$headers"} "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PASS${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}❌ FAIL${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📡 Backend API Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "Health Check" "http://localhost:9400/health"
test_endpoint "OpenAPI Docs" "http://localhost:9400/openapi.json"
test_endpoint "Metrics Endpoint" "http://localhost:9400/health/metrics"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎨 Frontend Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "Home Page" "http://localhost:4400/"
test_endpoint "CAD Upload Page" "http://localhost:4400/#/cad/upload"
test_endpoint "Finance Page" "http://localhost:4400/#/finance"
test_endpoint "Intelligence Page" "http://localhost:4400/#/visualizations/intelligence"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 Feature API Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test_endpoint "Finance Scenarios" "http://localhost:9400/api/v1/finance/scenarios?project_id=401" "X-Role: admin"
test_endpoint "Graph Intelligence" "http://localhost:9400/api/v1/analytics/intelligence/graph?workspaceId=default-investigation" "X-Role: admin"
test_endpoint "Predictive Intelligence" "http://localhost:9400/api/v1/analytics/intelligence/predictive?workspaceId=default-investigation" "X-Role: admin"
test_endpoint "Cross-Correlation" "http://localhost:9400/api/v1/analytics/intelligence/cross-correlation?workspaceId=default-investigation" "X-Role: admin"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 CAD/Import Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get latest import ID
IMPORT_ID=$(curl -s "http://localhost:9400/api/v1/parse/33d3b246-36e2-44b7-948c-b30107252458" -H "X-Role: admin" | python3 -c "import sys, json; print(json.load(sys.stdin).get('import_id', 'none'))" 2>/dev/null || echo "none")

if [ "$IMPORT_ID" != "none" ]; then
    test_endpoint "Import Parse Status" "http://localhost:9400/api/v1/parse/$IMPORT_ID" "X-Role: admin"

    echo -n "Testing Floor Detection... "
    FLOOR_COUNT=$(curl -s "http://localhost:9400/api/v1/parse/$IMPORT_ID" -H "X-Role: admin" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('result',{}).get('detected_floors',[])))" 2>/dev/null || echo "0")
    if [ "$FLOOR_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($FLOOR_COUNT floors detected)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (No floors detected)"
        ((FAILED++))
    fi

    echo -n "Testing Unit Detection... "
    UNIT_COUNT=$(curl -s "http://localhost:9400/api/v1/parse/$IMPORT_ID" -H "X-Role: admin" | python3 -c "import sys, json; d=json.load(sys.stdin); print(len(d.get('result',{}).get('detected_units',[])))" 2>/dev/null || echo "0")
    if [ "$UNIT_COUNT" -gt "0" ]; then
        echo -e "${GREEN}✅ PASS${NC} ($UNIT_COUNT units detected)"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC} (No units detected)"
        ((FAILED++))
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC} Import tests (no recent imports found)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💰 Finance Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -n "Testing Finance Scenarios Data... "
SCENARIO_COUNT=$(curl -s "http://localhost:9400/api/v1/finance/scenarios?project_id=401" -H "X-Role: admin" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
if [ "$SCENARIO_COUNT" -gt "0" ]; then
    echo -e "${GREEN}✅ PASS${NC} ($SCENARIO_COUNT scenarios found)"
    ((PASSED++))
else
    echo -e "${YELLOW}⚠️  WARN${NC} (No scenarios found - run seed script)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Database Tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo -n "Testing Database Connection... "
if cd backend && ../.venv/bin/python -c "from app.core import database; import asyncio; asyncio.run(database.check_database_connection())" 2>/dev/null; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASSED++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAILED++))
fi

echo ""
echo "═══════════════════════════════════════════════════"
echo "📊 TEST SUMMARY"
echo "═══════════════════════════════════════════════════"
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo "Total:  $((PASSED + FAILED))"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED${NC}"
    exit 1
fi
