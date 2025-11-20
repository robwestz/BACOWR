# BACOWR Complete Integration Plan
Based on api/README.md + Current Frontend Status

## 🎯 Målet
**Få job creation att fungera end-to-end från frontend klick till färdig artikel i databasen.**

## ✅ Vad Som Redan Fungerar (Backend)

Enligt `api/README.md`:
- ✅ REST API med FastAPI
- ✅ PostgreSQL database
- ✅ Job management endpoints (`/api/v1/jobs`)
- ✅ Background processing för async job execution
- ✅ Auto-generated docs på `/docs`
- ✅ API Key OCH JWT authentication
- ✅ Cost estimation
- ✅ Analytics endpoints

## ✅ Vad Vi Fixat (Frontend)

- ✅ JWT tokens skickas i Authorization header
- ✅ API endpoints använder `/api/v1` prefix
- ✅ Field names matchar backend (`writing_strategy`)
- ✅ TypeScript types för JobResponse/JobDetailResponse

## 🔴 Vad Som Fortfarande Inte Fungerar

### Problem 1: Response Schema Mismatch
**Frontend förväntar**:
```typescript
{
  job_meta: {
    job_id: "123",
    status: "PENDING",
    ...
  },
  publisher_profile: {...},
  target_profile: {...},
  ...
}
```

**Backend returnerar** (enligt schemas.py):
```typescript
{
  id: "123",
  user_id: "456",
  status: "pending",
  publisher_domain: "aftonbladet.se",
  ...
}
```

**Fix**: Uppdatera alla frontend komponenter att använda platt struktur.

### Problem 2: Navigation Efter Job Creation
**Current**: `router.push(\`/jobs/${job.job_meta.job_id}\`)` ❌
**Should be**: `router.push(\`/jobs/${job.id}\`)` ✅

### Problem 3: Settings Endpoints Saknas
Frontend kallar endpoints som inte finns:
- `/api/v1/users/me/settings` ❌
- `/api/v1/users/me/test-api-key` ❌

**Lösning**: Skapa dessa endpoints ELLER använd .env för LLM keys.

## 📋 Steg-för-Steg Fix Plan

### Steg 1: Fixa Job Creation Navigation (5 min)

**Fil**: `frontend/src/app/jobs/new/page.tsx`

```typescript
// RAD 90 - FÖRE:
router.push(`/jobs/${job.job_meta.job_id}`)

// RAD 90 - EFTER:
router.push(`/jobs/${job.id}`)
```

**Fil**: `frontend/src/lib/api/client.ts`

```typescript
// RAD 84-89 - FÖRE:
create: async (input: JobInput): Promise<JobPackage> => {
  return fetchAPI<JobPackage>('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}

// RAD 84-89 - EFTER:
create: async (input: JobInput): Promise<JobResponse> => {
  return fetchAPI<JobResponse>('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}
```

### Steg 2: Fixa QuickStartWidget (5 min)

**Fil**: `frontend/src/components/dashboard/QuickStartWidget.tsx`

```typescript
// RAD 36-42 - EFTER:
const job = await jobsAPI.create({
  ...input,
  llm_provider: 'auto',
  writing_strategy: 'multi_stage',
})

// RAD 42 - KOMMENTERA UT:
// addJob(job)  // Disable for now, wrong schema

addToast({
  type: 'success',
  title: 'Job Created',
  message: `Job ${job.id} is being generated!`,
})

// RAD 46-47 - EFTER:
router.push(`/jobs/${job.id}`)
```

### Steg 3: Test Job Creation (10 min)

1. **Starta backend**:
```bash
cd api
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

2. **Starta frontend**:
```bash
cd frontend
npm run dev
```

3. **Testa**:
   - Gå till http://localhost:3000
   - Logga in: `admin@bacowr.local` / `admin123`
   - Skapa job via Quick Start widget:
     - Publisher: `aftonbladet.se`
     - Target URL: `https://sv.wikipedia.org/wiki/Artificiell_intelligens`
     - Anchor: `läs mer om AI`
   - Klicka "Create Job"

4. **Förväntat resultat**:
   - ✅ Redirect till `/jobs/<id>`
   - ✅ Job visas i backend logs
   - ✅ Ingen 401 error
   - ✅ Ingen 404 error

### Steg 4: Verifiera i Database (5 min)

```bash
# Anslut till PostgreSQL
psql -U bacowr_user -d bacowr_db

# Kolla senaste jobbet
SELECT
  id,
  status,
  publisher_domain,
  target_url,
  anchor_text,
  created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 1;

# Förväntat:
# status = 'pending' eller 'processing'
# publisher_domain = 'aftonbladet.se'
```

### Steg 5: Fixa Job Details Page (15 min)

**Fil**: `frontend/src/app/jobs/[id]/page.tsx`

Läs nuvarande fil och uppdatera alla referenser:
- `job_meta.job_id` → `id`
- `job_meta.status` → `status`
- `job_meta.created_at` → `created_at`
- `qc_report` finns kvar (JSON field i database)
- `article_text` finns kvar (text field i database)

### Steg 6: Disable Settings Page Temporärt (2 min)

**Fil**: `frontend/src/components/layout/Sidebar.tsx`

```typescript
// Kommentera ut Settings länken:
const navigation = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/jobs/new', label: 'New Job', icon: PlusCircle },
  { href: '/backlinks', label: 'Backlinks', icon: Link },
  { href: '/batches', label: 'Batches', icon: Package },
  // { href: '/settings', label: 'Settings', icon: Settings },  // DISABLE
]
```

### Steg 7: Konfigurera LLM Keys i Backend .env (5 min)

**Fil**: `api/.env`

```env
# Database
DATABASE_URL=postgresql://bacowr_user:din_password@localhost:5432/bacowr_db

# LLM API Keys (istället för att spara i database)
ANTHROPIC_API_KEY=sk-ant-api03-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
AHREFS_API_KEY=...  # Optional

# JWT
SECRET_KEY=din-secret-key-här
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Environment
ENVIRONMENT=development
FRONTEND_URL=http://localhost:3000
```

### Steg 8: Verifiera Att BACOWR Core Fungerar (10 min)

**Test backend direkt via curl**:

```bash
# Logga in och få token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@bacowr.local",
    "password": "admin123"
  }'

# Spara access_token från response

# Skapa job med token
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer <din-access-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
    "anchor_text": "läs mer om AI",
    "llm_provider": "anthropic",
    "writing_strategy": "multi_stage"
  }'

# Kolla job status
curl http://localhost:8000/api/v1/jobs/<job-id> \
  -H "Authorization: Bearer <din-access-token>"
```

**Förväntat**:
- Job skapas med status `pending`
- Backend background task startar
- Status ändras till `processing`
- Efter 15-60 sekunder: status blir `delivered`
- `article_text` populeras med genererad artikel

### Steg 9: Fix Dashboard Stats (Optional - 10 min)

**Fil**: `frontend/src/app/page.tsx`

Uppdatera dashboard att använda `/api/v1/analytics/dashboard` endpoint:

```typescript
const { data: stats } = useQuery({
  queryKey: ['dashboard-stats'],
  queryFn: () => statsAPI.dashboard(),
  refetchInterval: 30000, // Refresh every 30 seconds
})
```

### Steg 10: Testa Hela Flödet (15 min)

**Komplett end-to-end test**:

1. Frontend → Backend → Database → Article Generation → Frontend Display

**Test scenario**:
```
1. Logga in
2. Skapa nytt job
3. Se job i "Live Jobs Monitor"
4. Status ändras från PENDING → PROCESSING → DELIVERED
5. Klicka på job → se full artikel
6. Verifiera QC report
7. Export artikel som Markdown
```

## 🏗️ Förslag: Slå Ihop Frontend + Backend (Senare)

**Nuvarande**: Två separata servrar
- Frontend: http://localhost:3000 (Next.js dev server)
- Backend: http://localhost:8000 (FastAPI)

**Föreslagen Production Setup**:

### Option A: Serve Frontend från FastAPI

```python
# api/app/main.py
from fastapi.staticfiles import StaticFiles

# Build frontend first
# cd frontend && npm run build && npm run export

app.mount("/", StaticFiles(directory="../frontend/out", html=True), name="frontend")
```

**Fördelar**:
- En server
- En URL
- Inga CORS problem
- Enkel deployment

**Process**:
1. Build frontend: `npm run build`
2. Export static: `npm run export` → skapar `frontend/out/`
3. FastAPI serverar static files från `/`
4. API routes på `/api/v1/*`

### Option B: Docker Compose (Rekommenderat för production)

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: bacowr_db
      POSTGRES_USER: bacowr_user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./api
    environment:
      DATABASE_URL: postgresql://bacowr_user:password@postgres:5432/bacowr_db
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
    ports:
      - "8000:8000"
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    environment:
      NEXT_PUBLIC_API_URL: http://backend:8000
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  postgres_data:
```

**Run**:
```bash
docker-compose up -d
```

## 📊 Success Metrics

När allt fungerar ska du kunna:

1. ✅ Logga in utan errors
2. ✅ Skapa job från frontend
3. ✅ Se job köra i realtid
4. ✅ Läsa färdig artikel
5. ✅ Se QC report med score
6. ✅ Export artikel som Markdown/PDF
7. ✅ Se kostnad för jobbet
8. ✅ Se historik av alla jobb
9. ✅ Filtrera jobb efter status
10. ✅ Analytics dashboard med stats

## 🚀 Quick Win Path (30 min total)

Snabbaste vägen till fungerande system:

```bash
# 1. Fix navigation (5 min)
# Edit: frontend/src/app/jobs/new/page.tsx line 90
# Change: job.job_meta.job_id → job.id

# 2. Fix API return type (2 min)
# Edit: frontend/src/lib/api/client.ts line 84
# Change: Promise<JobPackage> → Promise<JobResponse>

# 3. Build frontend (3 min)
cd frontend
npm run build

# 4. Configure backend (5 min)
cd api
# Add ANTHROPIC_API_KEY to .env

# 5. Start backend (2 min)
uvicorn app.main:app --reload

# 6. Start frontend (2 min)
cd frontend
npm run dev

# 7. Test (10 min)
# Open http://localhost:3000
# Login
# Create job
# Verify it works!
```

## 🐛 Debugging Checklist

Om något inte fungerar:

### Backend Issues
```bash
# Check logs
tail -f api/logs/app.log

# Check database connection
psql -U bacowr_user -d bacowr_db -c "SELECT 1"

# Check if API is running
curl http://localhost:8000/health

# Check API docs
open http://localhost:8000/docs
```

### Frontend Issues
```bash
# Check browser console for errors
# F12 → Console

# Check network requests
# F12 → Network → filter "api"

# Check localStorage for tokens
# F12 → Application → Local Storage
# Should see: access_token, refresh_token, user

# Build with verbose output
npm run build -- --debug
```

### Authentication Issues
```bash
# Test login directly
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@bacowr.local", "password": "admin123"}'

# Should return: {access_token, refresh_token, user}
```

### Database Issues
```bash
# Check if tables exist
psql -U bacowr_user -d bacowr_db -c "\dt"

# Check users table
psql -U bacowr_user -d bacowr_db -c "SELECT email, role FROM users"

# Check jobs table
psql -U bacowr_user -d bacowr_db -c "SELECT id, status FROM jobs ORDER BY created_at DESC LIMIT 5"
```

## 📝 Next Steps After Basic Integration Works

1. **WebSocket för live updates** - Se jobb progress i realtid
2. **Batch review workflow** - QA process för bulk content
3. **Settings page backend** - Spara LLM keys per user
4. **Export funktioner** - PDF, Google Docs
5. **Analytics dashboard** - Grafer och stats
6. **User management** - Multi-user support
7. **Cost tracking** - Budget limits
8. **Backlinks library** - Import historical data

## 🎯 Sammanfattning

**Just nu behöver vi**:
1. Fixa `job.job_meta.job_id` → `job.id` (2 rader kod)
2. Testa att job creation fungerar
3. Verifiera att artikel genereras i backend

**Sedan kan vi**:
4. Fixa resten av UI:t att matcha backend schema
5. Aktivera alla features (backlinks, analytics, exports)
6. Slå ihop deployment för production

**Timeline**:
- **Today**: Fix navigation, test job creation (30 min)
- **This week**: Full schema alignment, all features working
- **Next week**: Production deployment strategy

Vill du att jag fixar navigation-buggen nu så vi kan testa?
