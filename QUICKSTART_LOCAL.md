# BACOWR Quick Start - Lokal Utveckling

Kom igång med BACOWR på din lokala maskin på 5 minuter.

## 🚀 Snabbstart (5 minuter)

### Metod 1: Använd Startskript (Rekommenderat)

Det enklaste sättet att komma igång:

```bash
# Unix/Linux/macOS
./start_bacowr.sh

# Windows
.\start_bacowr.ps1
```

Skriptet gör automatiskt:
- Skapar virtuell miljö
- Installerar dependencies
- Kopierar .env.example till .env
- Kör BACOWR i dev-läge

### Metod 2: Manuell Setup

Om du vill ha mer kontroll:

```bash
# 1. Skapa virtuell miljö
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. Installera dependencies
pip install -r requirements.txt

# 3. Kopiera .env.example till .env
cp .env.example .env
# Redigera .env och lägg till dina API-nycklar (valfritt för dev-läge)

# 4. Kör i dev-läge (använder mock data)
python run_bacowr.py --mode dev \
  --publisher example.com \
  --target https://example.com/page \
  --anchor "test link"
```

### 3. Verifiera Installation

```bash
# Kör verifieringsskript
python verify_startup.py

# Förväntat resultat: Alla checks ska passa
```

## 🎯 Nästa Steg

### Kör i Production Mode

När du har lagt till API-nycklar i .env:

```bash
# Sätt API key (om inte i .env)
export ANTHROPIC_API_KEY='your-key-here'

# Kör med riktig LLM
python run_bacowr.py --mode prod \
  --publisher aftonbladet.se \
  --target https://sv.wikipedia.org/wiki/Artificiell_intelligens \
  --anchor "läs mer om AI"
```

### Interaktiv Demo

```bash
python run_bacowr.py --mode demo
```

## 🐳 Docker Alternative

Om du föredrar Docker:

```bash
# Kopiera och redigera .env
cp .env.example .env
# Lägg till dina API-nycklar i .env

# Starta med docker-compose
docker-compose up --build

# API körs på http://localhost:8000
# Dokumentation: http://localhost:8000/docs
```

## 🌐 Fullständig Web Application

För att köra hela web-applikationen (backend + frontend):

### 1. Backend Setup

```bash
# Gå till API-katalogen
cd api

# Skapa .env fil
cat > .env << 'EOF'
# Database
DATABASE_URL=sqlite:///./bacowr.db

# API Keys (lägg till dina nycklar)
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
GOOGLE_API_KEY=your_google_key_here

# Server
FRONTEND_URL=http://localhost:3000
DEBUG=true

# Auth
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF

# Installera dependencies
pip install -r requirements.txt

# Kör migrations
alembic upgrade head

# Starta backend
python -m uvicorn app.main:app --reload --port 8000
```

Backend körs nu på: **http://localhost:8000**
API Docs: **http://localhost:8000/docs**

### 2. Frontend Setup

Öppna en ny terminal:

```bash
# Gå till frontend-katalogen
cd frontend

# Skapa .env.local fil
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF

# Installera dependencies (om inte redan gjort)
npm install

# Starta dev server
npm run dev
```

Frontend körs nu på: **http://localhost:3000**

## 📝 Exempel: Första Jobbet

### Via CLI (Snabbast)

```bash
python run_bacowr.py --mode dev \
  --publisher example.com \
  --target https://example.com/page \
  --anchor "test link" \
  --verbose
```

### Via API (Om du kör web-applikationen)

```bash
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "Test Job 1",
    "target_url": "https://example.com/page",
    "backlink_url": "https://mysite.com",
    "anchor_text": "test anchor",
    "context": "SEO article about technology"
  }'
```

### Via Web UI

1. Öppna **http://localhost:3000**
2. Gå till "Jobs" → "Create Job"
3. Fyll i formuläret
4. Klicka "Create Job"
5. Se progress i realtid via WebSocket

## 📊 Testa Nya Features

### 1. Batch Review Workflow (Wave 2)

```bash
# Skapa batch från flera jobb
curl -X POST http://localhost:8000/api/v1/batches \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Batch 1",
    "description": "Testing batch review",
    "job_ids": ["job-id-1", "job-id-2", "job-id-3"]
  }'

# Visa batch review UI
open http://localhost:3000/batches
```

### 2. Prometheus Metrics (PR #23)

```bash
# Se metrics endpoint
curl http://localhost:8000/metrics

# Öppna Grafana dashboards (om docker-compose används)
open http://localhost:3001
```

### 3. Google Workspace Export (PR #23)

```bash
# Exportera jobb till Google Sheets
curl -X POST http://localhost:8000/api/v1/export/jobs/to-sheets \
  -H "Content-Type: application/json" \
  -d '{
    "job_ids": ["job-id-1", "job-id-2"],
    "spreadsheet_title": "BACOWR Export Test"
  }'
```

### 4. Audit Logging

```bash
# Visa audit logs
curl http://localhost:8000/api/v1/audit/logs?limit=10

# Filtrera på action
curl http://localhost:8000/api/v1/audit/logs?action=job_created
```

## 🔍 Troubleshooting

### Backend startar inte

**Problem:** `ModuleNotFoundError`
```bash
# Lösning: Installera alla dependencies
pip install -r requirements.txt
pip install -r ../requirements.txt  # Root dependencies
```

**Problem:** `Database migration failed`
```bash
# Lösning: Reset database
rm bacowr.db
alembic upgrade head
```

### Frontend startar inte

**Problem:** `Module not found`
```bash
# Lösning: Reinstall
rm -rf node_modules package-lock.json
npm install
```

**Problem:** `API connection refused`
```bash
# Lösning: Kontrollera att backend kör
curl http://localhost:8000/health

# Om inte, starta backend först
cd ../api && python -m uvicorn app.main:app --reload
```

### Google Export fungerar inte

**Problem:** `Missing credentials`
```bash
# Lösning: Skapa Google OAuth credentials
# 1. Gå till https://console.cloud.google.com
# 2. Skapa projekt
# 3. Enable Google Sheets API och Google Docs API
# 4. Skapa OAuth 2.0 credentials
# 5. Ladda ner credentials.json till api/credentials/google/credentials.json
```

## 🧪 Kör Alla Tester

```bash
# Integration test
python test_integration.py

# Backend tester
cd api
pytest tests/

# E2E tester
python tests/e2e/test_critical_workflows.py

# Smoke test
python tools/smoke_test_wave1.py
```

## 📚 Mer Information

- **Full Setup Guide:** `docs/development/setup.md`
- **Architecture:** `docs/architecture/overview.md`
- **API Reference:** http://localhost:8000/docs
- **Deployment:** `docs/deployment/production.md`

## 🎉 Du är igång!

Nästa steg:
1. ✅ Testa skapa ett jobb
2. ✅ Testa batch review workflow
3. ✅ Kolla Prometheus metrics
4. ✅ Testa Google export (om credentials finns)
5. 🚀 Kör i produktion (se `docs/deployment/production.md`)

---

**Behöver hjälp?** Kolla `docs/development/setup.md` för detaljerad dokumentation.
