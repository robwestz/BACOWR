#!/bin/bash
# Complete BACOWR Setup and Start Script
# This script sets up and starts both backend and frontend

set -e  # Exit on error

echo "======================================================================"
echo "🚀 BACOWR - Complete Setup & Start"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "start_bacowr.sh" ]; then
    echo -e "${RED}❌ Error: Please run this script from the BACOWR project root${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check dependencies
echo "📋 Checking dependencies..."
if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is required but not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ All dependencies found${NC}"
echo ""

# Step 1: Backend Setup
echo "======================================================================"
echo "🔧 Step 1: Backend Setup"
echo "======================================================================"

cd api

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating backend .env file..."
    cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./bacowr.db

# API Keys (add your keys here)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Server
FRONTEND_URL=http://localhost:3000
DEBUG=true

# Auth (JWT)
SECRET_KEY=dev-secret-key-change-in-production-$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional, uses in-memory fallback)
# REDIS_URL=redis://localhost:6379
EOF
    echo -e "${GREEN}✓ Backend .env created${NC}"
else
    echo -e "${YELLOW}⚠ Backend .env already exists, skipping${NC}"
fi

# Install backend dependencies
echo "📦 Installing backend dependencies..."
pip install -q -r requirements.txt > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠ Some backend dependencies may have failed. Continuing...${NC}"
}

# Run migrations
echo "🗄️  Running database migrations..."
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions 2>/dev/null)" ]; then
    echo "Creating initial migration..."
    alembic revision --autogenerate -m "Initial migration" > /dev/null 2>&1 || true
fi
alembic upgrade head > /dev/null 2>&1 || {
    echo -e "${YELLOW}⚠ Database migration may have failed. Continuing...${NC}"
}

echo -e "${GREEN}✓ Backend setup complete${NC}"
cd ..

# Step 2: Frontend Setup
echo ""
echo "======================================================================"
echo "🎨 Step 2: Frontend Setup"
echo "======================================================================"

cd frontend

# Create .env.local if it doesn't exist
if [ ! -f ".env.local" ]; then
    echo "📝 Creating frontend .env.local file..."
    cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
    echo -e "${GREEN}✓ Frontend .env.local created${NC}"
else
    echo -e "${YELLOW}⚠ Frontend .env.local already exists, skipping${NC}"
fi

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
if [ ! -d "node_modules" ]; then
    npm install > /dev/null 2>&1 || {
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠ Frontend dependencies already installed, skipping${NC}"
fi

cd ..

# Step 3: Start Services
echo ""
echo "======================================================================"
echo "🚀 Step 3: Starting Services"
echo "======================================================================"
echo ""

# Kill any existing processes on ports 8000 and 3000
echo "🧹 Cleaning up old processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo "🔌 Starting backend on http://localhost:8000 ..."
cd api
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "   Backend PID: $BACKEND_PID"
echo "   Logs: backend.log"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Backend failed to start. Check backend.log${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
done

# Start frontend
echo ""
echo "🎨 Starting frontend on http://localhost:3000 ..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo "   Frontend PID: $FRONTEND_PID"
echo "   Logs: frontend.log"

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
for i in {1..60}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Frontend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 60 ]; then
        echo -e "${RED}❌ Frontend failed to start. Check frontend.log${NC}"
        kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
        exit 1
    fi
done

# Final message
echo ""
echo "======================================================================"
echo "🎉 BACOWR IS RUNNING!"
echo "======================================================================"
echo ""
echo "🌐 Open your browser:"
echo "   Frontend: ${GREEN}http://localhost:3000${NC}"
echo "   Backend:  ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "🔐 Default Login:"
echo "   Email:    ${GREEN}admin@bacowr.local${NC}"
echo "   Password: ${GREEN}admin123${NC}"
echo ""
echo "📊 Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📝 Logs:"
echo "   Backend:  ${YELLOW}tail -f backend.log${NC}"
echo "   Frontend: ${YELLOW}tail -f frontend.log${NC}"
echo ""
echo "🛑 To stop:"
echo "   ${YELLOW}kill $BACKEND_PID $FRONTEND_PID${NC}"
echo "   or press Ctrl+C"
echo ""
echo "======================================================================"
echo ""

# Keep script running and forward signals
trap "echo ''; echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM

# Open browser (optional)
if command_exists open; then
    echo "🌐 Opening browser..."
    sleep 2
    open http://localhost:3000
elif command_exists xdg-open; then
    echo "🌐 Opening browser..."
    sleep 2
    xdg-open http://localhost:3000
fi

# Wait for processes
echo "✨ Press Ctrl+C to stop all services"
wait
