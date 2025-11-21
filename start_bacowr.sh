#!/bin/bash
# BACOWR Startup Wrapper (Simplified)
# 
# This script is a simplified wrapper for run_bacowr.py
# For full web application (backend + frontend), see the legacy/ folder
#
# Usage:
#   ./start_bacowr.sh              # Runs in dev mode (mock)
#   ./start_bacowr.sh --mode prod  # Runs in production mode (with LLM)

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================================================"
echo "🚀 BACOWR - BacklinkContent Engine"
echo "======================================================================"
echo ""

# Check if running from project root
if [ ! -f "run_bacowr.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the BACOWR project root${NC}"
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is required but not installed${NC}"
    exit 1
fi

# Check if .env exists, if not suggest using .env.example
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ No .env file found${NC}"
    if [ -f ".env.example" ]; then
        echo "  Copying .env.example to .env..."
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env from .env.example${NC}"
        echo "  Please edit .env and add your API keys before running in production mode"
        echo ""
    fi
fi

# Check if virtual environment exists
if [ ! -d ".venv" ] && [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ No virtual environment found${NC}"
    echo "  Creating virtual environment..."
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Activated virtual environment (.venv)${NC}"
elif [ -d "venv" ]; then
    source venv/bin/activate
    echo -e "${GREEN}✓ Activated virtual environment (venv)${NC}"
fi

# Check if dependencies are installed
if ! python3 -c "import dotenv" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
fi

# Default mode is dev, but allow override
MODE="dev"

# Parse mode argument
if [ "$1" = "--mode" ]; then
    # Check if second argument exists
    if [ -n "$2" ]; then
        MODE="$2"
        shift 2
    else
        echo -e "${RED}Error: --mode requires an argument${NC}"
        exit 1
    fi
elif [ -n "$1" ]; then
    # Check if first argument is --mode=value format
    if [[ "$1" == --mode=* ]]; then
        MODE="${1#--mode=}"
        shift
    else
        # Keep first argument as-is, use default mode
        MODE="dev"
    fi
fi

echo "Starting BACOWR in ${MODE} mode..."
echo ""

# Run run_bacowr.py with provided mode and any additional arguments
python3 run_bacowr.py --mode "$MODE" "$@"
