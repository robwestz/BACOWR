# BACOWR Startup Script for Windows
# Run with: .\start_bacowr.ps1

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🚀 BACOWR - Complete Setup & Start (Windows)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running from project root
if (-not (Test-Path "start_bacowr.ps1")) {
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

$npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCmd) {
    Write-Host "❌ npm is required but not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ All dependencies found" -ForegroundColor Green
Write-Host ""

# Step 1: Backend Setup
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🔧 Step 1: Backend Setup" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Set-Location api

# Create .env if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating backend .env file..." -ForegroundColor Yellow
    @"
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
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional, uses in-memory fallback)
# REDIS_URL=redis://localhost:6379
"@ | Out-File -FilePath ".env" -Encoding UTF8
    Write-Host "✓ Backend .env created" -ForegroundColor Green
} else {
    Write-Host "⚠ Backend .env already exists, skipping" -ForegroundColor Yellow
}

# Install backend dependencies
Write-Host "📦 Installing backend dependencies..." -ForegroundColor Yellow
python -m pip install -q -r requirements.txt 2>&1 | Out-Null

# Run migrations
Write-Host "🗄️  Running database migrations..." -ForegroundColor Yellow
if (-not (Test-Path "alembic/versions") -or ((Get-ChildItem "alembic/versions" -ErrorAction SilentlyContinue).Count -eq 0)) {
    Write-Host "Creating initial migration..." -ForegroundColor Yellow
    alembic revision --autogenerate -m "Initial migration" 2>&1 | Out-Null
}
alembic upgrade head 2>&1 | Out-Null

Write-Host "✓ Backend setup complete" -ForegroundColor Green
Set-Location ..

# Step 2: Frontend Setup
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🎨 Step 2: Frontend Setup" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

Set-Location frontend

# Create .env.local if it doesn't exist
if (-not (Test-Path ".env.local")) {
    Write-Host "📝 Creating frontend .env.local file..." -ForegroundColor Yellow
    @"
NEXT_PUBLIC_API_URL=http://localhost:8000
"@ | Out-File -FilePath ".env.local" -Encoding UTF8
    Write-Host "✓ Frontend .env.local created" -ForegroundColor Green
} else {
    Write-Host "⚠ Frontend .env.local already exists, skipping" -ForegroundColor Yellow
}

# Install frontend dependencies
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing frontend dependencies (this may take a few minutes)..." -ForegroundColor Yellow
    npm install 2>&1 | Out-Null
    Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "⚠ Frontend dependencies already installed, skipping" -ForegroundColor Yellow
}

Set-Location ..

# Step 3: Start Services
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "🚀 Step 3: Starting Services" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# Kill any existing processes on ports 8000 and 3000
Write-Host "🧹 Cleaning up old processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 1

# Start backend
Write-Host "🔌 Starting backend on http://localhost:8000 ..." -ForegroundColor Yellow
Set-Location api
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
}
Set-Location ..

Write-Host "   Backend Job ID: $($backendJob.Id)" -ForegroundColor Gray

# Wait for backend to start
Write-Host "⏳ Waiting for backend to start..." -ForegroundColor Yellow
$maxAttempts = 30
$attempt = 0
$backendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Backend is ready!" -ForegroundColor Green
            $backendReady = $true
            break
        }
    } catch {
        # Backend not ready yet
    }
    Start-Sleep -Seconds 1
    $attempt++
}

if (-not $backendReady) {
    Write-Host "❌ Backend failed to start within 30 seconds" -ForegroundColor Red
    Stop-Job $backendJob
    Remove-Job $backendJob
    exit 1
}

# Start frontend
Write-Host ""
Write-Host "🎨 Starting frontend on http://localhost:3000 ..." -ForegroundColor Yellow
Set-Location frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    npm run dev
}
Set-Location ..

Write-Host "   Frontend Job ID: $($frontendJob.Id)" -ForegroundColor Gray

# Wait for frontend to start
Write-Host "⏳ Waiting for frontend to start..." -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0
$frontendReady = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:3000" -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✓ Frontend is ready!" -ForegroundColor Green
            $frontendReady = $true
            break
        }
    } catch {
        # Frontend not ready yet
    }
    Start-Sleep -Seconds 1
    $attempt++
}

if (-not $frontendReady) {
    Write-Host "❌ Frontend failed to start within 60 seconds" -ForegroundColor Red
    Stop-Job $backendJob, $frontendJob
    Remove-Job $backendJob, $frontendJob
    exit 1
}

# Final message
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "🎉 BACOWR IS RUNNING!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Open your browser:" -ForegroundColor White
Write-Host "   Frontend: " -NoNewline -ForegroundColor White
Write-Host "http://localhost:3000" -ForegroundColor Green
Write-Host "   Backend:  " -NoNewline -ForegroundColor White
Write-Host "http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "🔐 Default Login:" -ForegroundColor White
Write-Host "   Email:    " -NoNewline -ForegroundColor White
Write-Host "admin@bacowr.local" -ForegroundColor Green
Write-Host "   Password: " -NoNewline -ForegroundColor White
Write-Host "admin123" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Job IDs:" -ForegroundColor White
Write-Host "   Backend:  $($backendJob.Id)" -ForegroundColor Gray
Write-Host "   Frontend: $($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "🛑 To stop:" -ForegroundColor White
Write-Host "   Press Ctrl+C or close this window" -ForegroundColor Yellow
Write-Host "   Or run: Stop-Job $($backendJob.Id),$($frontendJob.Id); Remove-Job $($backendJob.Id),$($frontendJob.Id)" -ForegroundColor Gray
Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

# Open browser
Write-Host "🌐 Opening browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 2
Start-Process "http://localhost:3000"

# Keep script running and show output
Write-Host "✨ Press Ctrl+C to stop all services" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend Output:" -ForegroundColor Yellow
Write-Host "─────────────────────────────────────────────────────────────────────" -ForegroundColor Gray

try {
    while ($true) {
        # Show backend output
        Receive-Job $backendJob | Write-Host

        # Show frontend output
        Receive-Job $frontendJob | Write-Host

        # Check if jobs are still running
        if ($backendJob.State -eq 'Failed' -or $frontendJob.State -eq 'Failed') {
            Write-Host ""
            Write-Host "❌ One or more services failed" -ForegroundColor Red
            break
        }

        Start-Sleep -Milliseconds 500
    }
} finally {
    Write-Host ""
    Write-Host "🛑 Stopping services..." -ForegroundColor Yellow
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host "✓ Services stopped" -ForegroundColor Green
}
