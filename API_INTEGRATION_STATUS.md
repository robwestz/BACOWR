# BACOWR API Integration Status

## ✅ Fixed Issues (Just Pushed)

### 1. **JWT Authentication Now Works** ✅
- **Problem**: API client wasn't sending JWT tokens with requests
- **Fix**: `fetchAPI()` now automatically:
  - Gets `access_token` from localStorage  - Adds `Authorization: Bearer <token>` header to all requests
  - Auto-redirects to `/login` on 401 Unauthorized
- **Impact**: All API calls now properly authenticated

### 2. **API Endpoint Paths Corrected** ✅
- **Problem**: Frontend called `/api/jobs`, backend expected `/api/v1/jobs`
- **Fix**: Updated all API endpoints:
  - Jobs: `/api/v1/jobs`
  - Batches: `/api/v1/batches`
  - Backlinks: `/api/v1/backlinks`
  - Analytics: `/api/v1/analytics`
  - Auth: `/api/v1/auth`
  - Users: `/api/v1/users`
- **Impact**: API calls will now reach correct endpoints

### 3. **Field Name Mismatch Fixed** ✅
- **Problem**: Frontend sent `strategy`, backend expected `writing_strategy`
- **Fix**: Updated JobInput type and all job creation calls
- **Files Changed**:
  - `frontend/src/types/index.ts` - JobInput interface
  - `frontend/src/app/jobs/new/page.tsx` - Job wizard
  - `frontend/src/components/dashboard/QuickStartWidget.tsx` - Quick start widget
- **Impact**: Job creation payload now matches backend schema

### 4. **TypeScript Types Aligned** ✅
- **Added**: `JobResponse` and `JobDetailResponse` matching backend schemas
- **Backend JobResponse** returns:
  ```typescript
  {
    id: string
    user_id: string
    publisher_domain: string
    target_url: string
    anchor_text: string
    status: string
    estimated_cost: number
    created_at: string
    ...
  }
  ```
- **Impact**: Frontend now knows correct response structure

## 🔴 Remaining Issues to Fix

### 1. **Frontend Components Use Wrong Schema**
- **Problem**: Components expect `JobPackage` with `job_meta.job_id`, but backend returns `JobResponse` with `id`
- **Affected Components**:
  - `QuickStartWidget.tsx` - Line 42: `addJob(job)` expects JobPackage
  - `new/page.tsx` - Line 90: `router.push(/jobs/${job.job_meta.job_id})` - should be `job.id`
  - `JobCard.tsx` - Expects job_meta structure
  - `JobProgressBar.tsx` - Expects job_meta structure
- **Solution Needed**: Update all components to use `JobResponse` schema:
  ```typescript
  // OLD:
  router.push(`/jobs/${job.job_meta.job_id}`)

  // NEW:
  router.push(`/jobs/${job.id}`)
  ```

### 2. **Settings API Endpoints Don't Exist** 🔴
- **Problem**: Frontend calls `/api/v1/users/me/settings` but backend has no such endpoint
- **Frontend Calls** (that will fail):
  - `GET /api/v1/users/me/settings` - Get user settings
  - `PATCH /api/v1/users/me/settings` - Update settings
  - `POST /api/v1/users/me/test-api-key` - Test API key
- **Backend Has**: Only basic user management in `/api/v1/users`
- **Solution Needed**: Create settings endpoints in backend or disable settings page for now

### 3. **API Keys Not Stored in Database** 🔴
- **Problem**: User model doesn't have fields for LLM provider API keys
- **Current User Model**:
  - Has `api_key` (for BACOWR authentication)
  - No fields for: anthropic_api_key, openai_api_key, etc.
- **Solution Needed**:
  - Add JSON field `llm_api_keys` to User model
  - Create migration
  - OR use environment variables for LLM keys (simpler for single user)

### 4. **Job List Response Format Unknown** ⚠️
- **Problem**: Unknown what `/api/v1/jobs?page=1` returns
- **Frontend Expects**: `PaginatedResponse<JobResponse>`
- **Need to Verify**: Backend pagination format matches frontend expectations

## 🧪 Testing Steps

### Step 1: Test Authentication
```bash
# Start backend
cd api
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
uvicorn app.main:app --reload --port 8000

# Start frontend (new terminal)
cd frontend
npm run dev
```

**Test**:
1. Open http://localhost:3000
2. Should redirect to `/login`
3. Login with: `admin@bacowr.local` / `admin123`
4. Should redirect to dashboard

### Step 2: Test Job Creation (Will Partially Fail)
1. Click "Create New Job" or use Quick Start Widget
2. Fill in:
   - Publisher Domain: `aftonbladet.se`
   - Target URL: `https://sv.wikipedia.org/wiki/Artificiell_intelligens`
   - Anchor Text: `läs mer om AI`
3. Submit

**Expected**:
- ✅ API call should succeed (no 401, no 404)
- ❌ Navigation will fail because frontend tries `job.job_meta.job_id` instead of `job.id`
- Check browser console for errors

### Step 3: Check Backend Logs
```bash
# Backend terminal should show:
INFO: POST /api/v1/jobs - 201 Created
```

### Step 4: Verify in Database
```bash
# Connect to PostgreSQL
psql -U bacowr_user -d bacowr_db

# Check jobs table
SELECT id, status, publisher_domain, target_url FROM jobs ORDER BY created_at DESC LIMIT 5;
```

## 🔧 Quick Fixes Needed

### Fix 1: Update Job Navigation
**File**: `frontend/src/app/jobs/new/page.tsx:90`

```typescript
// CHANGE FROM:
router.push(`/jobs/${job.job_meta.job_id}`)

// CHANGE TO:
router.push(`/jobs/${job.id}`)
```

### Fix 2: Disable Settings Page Temporarily
**File**: `frontend/src/components/layout/Sidebar.tsx`

Comment out Settings link until backend supports it:
```typescript
// { href: '/settings', label: 'Settings', icon: Settings },
```

### Fix 3: Use Environment Variables for LLM Keys
Instead of storing in database, use `.env`:

**File**: `api/.env`
```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
AHREFS_API_KEY=...
```

**File**: `api/app/core/bacowr_wrapper.py`
Read from environment instead of user settings.

## 📝 Architecture Question: Merge Frontend & Backend?

**User Suggestion**: "det verkar problematiskt att frontend och backend är två separata delar, kan vi bygga ihop det?"

### Option 1: Serve Frontend from FastAPI (Recommended)
**Pros**:
- Single deployment
- Single URL
- No CORS issues
- Frontend can be static build

**Implementation**:
```bash
# Build frontend
cd frontend && npm run build

# Serve from FastAPI
# Add to api/main.py:
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="../frontend/out", html=True), name="frontend")
```

**Cons**:
- FastAPI serves static files (less efficient than Nginx, but fine for small scale)
- Need to configure Next.js for static export

### Option 2: Next.js API Routes as Proxy
**Pros**:
- Keep Next.js features (SSR, Image Optimization)
- Single deployment on Vercel/similar

**Implementation**:
```typescript
// frontend/src/app/api/[...path]/route.ts
export async function POST(request: Request) {
  // Proxy to FastAPI
  const response = await fetch(`http://localhost:8000${request.url}`, {
    method: request.method,
    headers: request.headers,
    body: request.body
  })
  return response
}
```

**Cons**:
- More complex
- Two runtimes (Node.js + Python)

### Option 3: Rebuild Backend in Next.js API Routes
**Pros**:
- Single codebase
- Single language (TypeScript)

**Cons**:
- Complete rewrite
- Lose FastAPI benefits
- BACOWR core is Python-based

### Recommendation
**Option 1** is best for your use case:
1. Build frontend as static files
2. Serve from FastAPI
3. Single Docker container
4. Single URL

## 🎯 Next Actions (Priority Order)

1. **[HIGH]** Fix job navigation to use `job.id` instead of `job.job_meta.job_id`
2. **[HIGH]** Test job creation end-to-end
3. **[MEDIUM]** Add LLM API keys to `.env` file (backend)
4. **[MEDIUM]** Disable or remove Settings page from frontend
5. **[LOW]** Consider merging frontend + backend deployment
6. **[LOW]** Create settings endpoints if user management is needed

## 📊 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Authentication | ✅ Fixed | JWT tokens now sent correctly |
| API Endpoints | ✅ Fixed | All use `/api/v1` prefix |
| Job Creation Request | ✅ Fixed | Correct field names |
| Job Creation Response | ⚠️ Partial | Backend works, frontend navigation broken |
| Settings Page | 🔴 Broken | No backend endpoints |
| Job Details Page | ⚠️ Unknown | Depends on schema alignment |
| Dashboard | ⚠️ Unknown | Depends on API responses |

## 🔍 Debugging Tips

If job creation fails:
```typescript
// Add to frontend/src/app/jobs/new/page.tsx:91
catch (error) {
  console.log('API Error:', error)
  console.log('Error details:', error.details)
  // Check if error.status === 401 -> auth problem
  // Check if error.status === 404 -> endpoint problem
  // Check if error.status === 422 -> validation problem
}
```

Check backend logs:
```bash
# Backend should show detailed error
# Look for FastAPI validation errors
```

## ✨ After These Fixes

Once the above fixes are done:
1. Job creation will work end-to-end
2. User can see job status in real-time
3. Articles will be generated
4. QC reports will be available
5. Full BACOWR workflow operational

**Main blocker now**: Frontend component schema mismatch with backend response.
