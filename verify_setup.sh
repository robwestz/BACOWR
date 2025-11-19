#!/bin/bash
# BACOWR Setup Verification Script
# Verifies that the local environment is ready to run

echo "======================================================================"
echo "BACOWR Setup Verification"
echo "======================================================================"
echo ""

PASSED=0
FAILED=0

# Test 1: Python version
echo "1. Checking Python version..."
if python --version | grep -q "Python 3.1"; then
    echo "   ✓ Python 3.11+ detected"
    ((PASSED++))
else
    echo "   ✗ Python 3.11+ required"
    ((FAILED++))
fi

# Test 2: Backend dependencies
echo ""
echo "2. Checking backend dependencies..."
cd api 2>/dev/null || cd .
if python -c "import fastapi, sqlalchemy, anthropic" 2>/dev/null; then
    echo "   ✓ Core backend dependencies installed"
    ((PASSED++))
else
    echo "   ✗ Missing backend dependencies. Run: pip install -r api/requirements.txt"
    ((FAILED++))
fi

# Test 3: Monitoring dependencies
echo ""
echo "3. Checking monitoring dependencies..."
if python -c "import structlog, prometheus_client" 2>/dev/null; then
    echo "   ✓ Monitoring dependencies installed"
    ((PASSED++))
else
    echo "   ✗ Missing monitoring deps. Run: pip install structlog prometheus-client prometheus-fastapi-instrumentator"
    ((FAILED++))
fi

# Test 4: Google API dependencies
echo ""
echo "4. Checking Google API dependencies..."
if python -c "from google.oauth2.credentials import Credentials" 2>/dev/null; then
    echo "   ✓ Google API dependencies installed"
    ((PASSED++))
else
    echo "   ✗ Missing Google deps. Run: pip install google-api-python-client google-auth-oauthlib"
    ((FAILED++))
fi

# Test 5: Database setup
echo ""
echo "5. Checking database..."
cd "$(dirname "$0")/api" 2>/dev/null || cd api 2>/dev/null || true
if [ -f "bacowr.db" ] || [ -f "../api/bacowr.db" ]; then
    echo "   ✓ Database file exists"
    ((PASSED++))
else
    echo "   ⚠ Database not initialized. Run: cd api && alembic upgrade head"
    ((FAILED++))
fi

# Test 6: Environment file
echo ""
echo "6. Checking environment configuration..."
if [ -f ".env" ] || [ -f "api/.env" ]; then
    echo "   ✓ .env file exists"
    ((PASSED++))
else
    echo "   ✗ Missing .env file. See QUICKSTART_LOCAL.md for template"
    ((FAILED++))
fi

# Test 7: Frontend dependencies
echo ""
echo "7. Checking frontend setup..."
cd ../frontend 2>/dev/null || cd frontend 2>/dev/null || true
if [ -d "node_modules" ]; then
    echo "   ✓ Frontend dependencies installed"
    ((PASSED++))
else
    echo "   ⚠ Frontend not set up. Run: cd frontend && npm install"
    ((FAILED++))
fi

# Test 8: Integration test
echo ""
echo "8. Running integration test..."
cd .. || true
if python test_integration.py > /dev/null 2>&1; then
    echo "   ✓ Integration test passed"
    ((PASSED++))
else
    echo "   ✗ Integration test failed. Run: python test_integration.py"
    ((FAILED++))
fi

# Results
echo ""
echo "======================================================================"
echo "Verification Results"
echo "======================================================================"
echo "✓ Passed: $PASSED/8"
echo "✗ Failed: $FAILED/8"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All checks passed! You're ready to run BACOWR."
    echo ""
    echo "Next steps:"
    echo "  1. Terminal 1: cd api && python -m uvicorn app.main:app --reload"
    echo "  2. Terminal 2: cd frontend && npm run dev"
    echo "  3. Open: http://localhost:3000"
    exit 0
else
    echo "⚠ $FAILED check(s) failed. Fix the issues above before running."
    echo ""
    echo "Quick fixes:"
    echo "  • Missing deps: pip install -r requirements.txt -r api/requirements.txt"
    echo "  • Database: cd api && alembic upgrade head"
    echo "  • Frontend: cd frontend && npm install"
    echo "  • .env file: See QUICKSTART_LOCAL.md"
    exit 1
fi
