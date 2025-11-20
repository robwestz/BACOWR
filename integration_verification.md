# BACOWR Integration Verification

## ✅ System Status (Verified: 2025-11-20)

### Services Running
- **Frontend (Next.js)**: http://localhost:3000 ✓
- **Backend (FastAPI)**: http://localhost:8000 ✓
- **API Documentation**: http://localhost:8000/docs ✓

### Database
- **Type**: SQLite
- **Location**: /home/user/BACOWR/api/bacowr.db
- **Status**: Initialized ✓
- **Tables**: users, jobs, job_results, backlinks, batches, batch_review_items, audit_logs ✓

## 🔗 Integration Points

### 1. Frontend → Backend API
**Location**: `/home/user/BACOWR/frontend/src/lib/api/client.ts`

```typescript
// API Base URL (Line 18)
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Job Creation Endpoint (Line 86-91)
create: async (input: JobInput): Promise<JobResponse> => {
  return fetchAPI<JobResponse>('/api/v1/jobs', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}
```

### 2. Backend API Routes
**Location**: `/home/user/BACOWR/api/app/main.py`

```python
# Router Mounting (Lines 106-117)
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(backlinks.router, prefix="/api/v1")
app.include_router(batches.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
```

**Job Routes**: `/home/user/BACOWR/api/app/routes/jobs.py`
```python
# Job Router (Line 19)
router = APIRouter(prefix="/jobs", tags=["jobs"])

# Full path: /api/v1/jobs
```

### 3. Authentication Flow

**Frontend (client.ts:38-48)**:
- Stores JWT token in localStorage: `access_token`
- Adds `Authorization: Bearer {token}` header to all requests
- Auto-redirects to login on 401 errors

**Backend (auth.py)**:
- Login endpoint: `POST /api/v1/auth/login`
- Password hashing: Direct bcrypt (fixed compatibility issue)
- JWT token generation and validation

### 4. CORS Configuration
**Location**: `/home/user/BACOWR/api/app/main.py:34-42`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", ...],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Allows**: Frontend (localhost:3000) → Backend (localhost:8000) ✓

## 📊 Complete Job Creation Flow

```
User (Browser)
    ↓
Frontend (localhost:3000)
    ↓ [HTTP POST /api/v1/jobs]
    ↓ [Authorization: Bearer {JWT}]
    ↓
Backend API (localhost:8000)
    ↓ [Auth Middleware validates JWT]
    ↓
Job Router (/api/v1/jobs)
    ↓ [Creates Job in DB]
    ↓ [Runs BACOWR background task]
    ↓
Database (bacowr.db)
    ↓ [Stores job, results, metrics]
    ↓
Response → Frontend
    ↓
User sees job status
```

## 🔐 Authentication

**Default Admin User**:
- Email: `admin@bacowr.local`
- Password: `admin123`
- Created automatically on backend startup

**Login Process**:
1. User enters credentials in frontend (`/login`)
2. Frontend calls `POST /api/v1/auth/login`
3. Backend validates with bcrypt
4. Backend returns JWT access_token + refresh_token
5. Frontend stores tokens in localStorage
6. All subsequent requests include Bearer token

## 🗄️ Database Schema

**Tables Created** (via `/home/user/BACOWR/api/app/database.py`):

1. **users** - User accounts and API keys
2. **jobs** - Content generation jobs
3. **job_results** - Job analytics and QC scores
4. **backlinks** - Published backlink records
5. **batches** - Batch review collections
6. **batch_review_items** - Items within batches
7. **audit_logs** - Audit trail for compliance

## 🧪 Testing the Integration

### Test 1: Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"bacowr-api","version":"1.0.0"}
```

### Test 2: Frontend Loading
```bash
curl http://localhost:3000 | grep "BACOWR"
# Expected: HTML with BACOWR title
```

### Test 3: Login (Get JWT Token)
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@bacowr.local","password":"admin123"}'
# Expected: {"access_token":"eyJ...", "refresh_token":"eyJ...", "user":{...}}
```

### Test 4: Create Job (Requires JWT)
```bash
TOKEN="<your_jwt_token_here>"
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://example.com",
    "anchor_text": "test link",
    "llm_provider": "auto",
    "writing_strategy": "multi_stage"
  }'
# Expected: Job created with job_id
```

## 📁 Key Files Integration Map

### Frontend Files
- **API Client**: `frontend/src/lib/api/client.ts` → All API calls
- **Types**: `frontend/src/types/index.ts` → Shared types with backend
- **Hooks**: `frontend/src/hooks/` → State management
- **Pages**: `frontend/src/app/` → Next.js 14 App Router

### Backend Files
- **Main App**: `api/app/main.py` → FastAPI app, CORS, router mounting
- **Job Routes**: `api/app/routes/jobs.py` → Job creation endpoints
- **Auth**: `api/app/auth.py` → JWT auth, password hashing (bcrypt)
- **Database**: `api/app/database.py` → SQLAlchemy setup
- **Models**: `api/app/models/` → DB models and Pydantic schemas
- **BACOWR Core**: `api/app/core/bacowr_wrapper.py` → Content generation

### Configuration Files
- **Backend Env**: `api/.env` → DATABASE_URL, FRONTEND_URL, API keys
- **Frontend Env**: `frontend/.env.local` → NEXT_PUBLIC_API_URL
- **Package Files**: `api/requirements.txt`, `frontend/package.json`

## 🎯 User Journey: Creating First Job

1. **Navigate to Frontend**: http://localhost:3000
2. **Login**: 
   - Email: admin@bacowr.local
   - Password: admin123
3. **Dashboard**: View quick start widget
4. **Create Job**:
   - Publisher Domain: e.g., `aftonbladet.se`
   - Target URL: e.g., `https://sv.wikipedia.org/wiki/AI`
   - Anchor Text: e.g., `läs mer om AI`
   - LLM Provider: Auto (or Claude/GPT/Gemini)
   - Strategy: Multi-Stage (recommended)
5. **Submit**: Job queued and processed in background
6. **Monitor**: Real-time updates via WebSocket or polling
7. **View Results**: Article text, QC report, execution logs
8. **Export**: Download as MD, PDF, or HTML

## ✅ All Components Verified Connected

- ✅ Frontend serves on port 3000
- ✅ Backend serves on port 8000
- ✅ CORS allows cross-origin requests
- ✅ API routes mounted at /api/v1
- ✅ Frontend calls correct /api/v1/* endpoints
- ✅ JWT authentication working
- ✅ Database initialized with all tables
- ✅ Default admin user created
- ✅ Password hashing with bcrypt functional
- ✅ Job creation flow complete
- ✅ Background task processing configured

## 🚀 Ready for Use

The complete BACOWR application is now fully operational and all components are properly integrated.
