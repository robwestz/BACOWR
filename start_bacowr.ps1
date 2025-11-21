# BACOWR Startup Wrapper for Windows (Simplified)
# 
# This script is a simplified wrapper for run_bacowr.py
# For full web application (backend + frontend), see the legacy/ folder
#
# Usage:
#   .\start_bacowr.ps1              # Runs in dev mode (mock)
#   .\start_bacowr.ps1 -Mode prod   # Runs in production mode (with LLM)

param(
    [string]$Mode = "dev"
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🚀 BACOWR - BacklinkContent Engine" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running from project root
if (-not (Test-Path "run_bacowr.py")) {
    Write-Host "❌ Error: Please run this script from the BACOWR project root" -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host "📋 Checking dependencies..." -ForegroundColor Yellow
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Python is required but not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Python found" -ForegroundColor Green
Write-Host ""

# Check if .env exists, if not suggest using .env.example
if (-not (Test-Path ".env")) {
    Write-Host "⚠ No .env file found" -ForegroundColor Yellow
    if (Test-Path ".env.example") {
        Write-Host "  Copying .env.example to .env..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Created .env from .env.example" -ForegroundColor Green
        Write-Host "  Please edit .env and add your API keys before running in production mode" -ForegroundColor Yellow
        Write-Host ""
    }
}

# Check if virtual environment exists
if (-not (Test-Path ".venv") -and -not (Test-Path "venv")) {
    Write-Host "⚠ No virtual environment found" -ForegroundColor Yellow
    Write-Host "  Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
    Write-Host ""
}

# Activate virtual environment if it exists
if (Test-Path ".venv") {
    & .\.venv\Scripts\Activate.ps1
    Write-Host "✓ Activated virtual environment (.venv)" -ForegroundColor Green
} elseif (Test-Path "venv") {
    & .\venv\Scripts\Activate.ps1
    Write-Host "✓ Activated virtual environment (venv)" -ForegroundColor Green
}

# Check if dependencies are installed
try {
    python -c "import dotenv" 2>$null
} catch {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    python -m pip install -q -r requirements.txt
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
    Write-Host ""
}

Write-Host "Starting BACOWR in $Mode mode..." -ForegroundColor Cyan
Write-Host ""

# Run run_bacowr.py with provided mode and any additional arguments
$additionalArgs = $args
python run_bacowr.py --mode $Mode @additionalArgs
