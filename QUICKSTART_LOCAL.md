# BACOWR Quick Start - Lokal Utveckling

Kom igång med BACOWR på din lokala maskin på 10 minuter.

## 🚀 Snabbstart (5 minuter)

### 1. Backend Setup (2 min)

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

# Redis (optional, använder in-memory fallback om ej tillgänglig)
# REDIS_URL=redis://localhost:6379
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

### 2. Frontend Setup (2 min)

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

### 3. Verifiera Installation (1 min)

Öppna en ny terminal:

```bash
# Kör integration test
python test_integration.py

# Testa API endpoint
curl http://localhost:8000/health

# Förväntat svar:
# {"status":"healthy","service":"bacowr-api","version":"1.0.0"}
```

## 🎯 Första Testet

### Skapa ett Job via API

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
