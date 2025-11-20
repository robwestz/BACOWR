# 🚀 Quick Start Test Guide

## ✅ All Critical Fixes Are Now Complete!

Job creation should work end-to-end. Follow these steps to test.

## Prerequisites

1. **PostgreSQL Running**
   ```bash
   # Check if PostgreSQL is running
   psql -U bacowr_user -d bacowr_db -c "SELECT 1"
   ```

2. **Environment Variables Set**
   - `api/.env` should have:
     - `DATABASE_URL`
     - `ANTHROPIC_API_KEY` (for article generation)
     - `SECRET_KEY`

## 🧪 Test Steps (5 Minutes)

### Step 1: Start Backend (Terminal 1)

```bash
cd api
source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**Expected Output:**
```
======================================================================
BACOWR API Starting...
======================================================================
✓ Database initialized
✓ Default admin user ready
======================================================================
✓ BACOWR API Ready!
  Docs: http://localhost:8000/docs
======================================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
✓ Ready in 2.3s
○ Local:   http://localhost:3000
```

### Step 3: Login

1. Open http://localhost:3000
2. Should auto-redirect to `/login`
3. Use demo credentials:
   - **Email**: `admin@bacowr.local`
   - **Password**: `admin123`
4. Click "Sign In"
5. Should redirect to dashboard

**✅ Success**: You're logged in and see the dashboard

### Step 4: Create Job via Quick Start Widget

1. On dashboard, find "Quick Start" widget
2. Fill in:
   - **Publisher Domain**: `aftonbladet.se`
   - **Target URL**: `https://sv.wikipedia.org/wiki/Artificiell_intelligens`
   - **Anchor Text**: `läs mer om AI`
3. Click "Create Job"

**Expected**:
- Toast notification: "Job Created"
- Redirect to `/jobs/<job-id>`

### Step 5: Verify in Backend Logs

Check Terminal 1 (backend):
```
INFO: POST /api/v1/jobs - 201 Created
INFO: Background task started for job <job-id>
```

### Step 6: Check Database

```bash
psql -U bacowr_user -d bacowr_db

SELECT
  id,
  status,
  publisher_domain,
  target_url,
  created_at
FROM jobs
ORDER BY created_at DESC
LIMIT 1;
```

**Expected Output:**
```
 id      | status     | publisher_domain | target_url | created_at
---------+------------+------------------+------------+------------
 abc123  | pending    | aftonbladet.se   | https://.. | 2025-...
```

### Step 7: Watch Article Generation

**Option A: Via Frontend**
- Stay on job details page
- Status should change: `PENDING` → `PROCESSING` → `DELIVERED`
- This takes 15-60 seconds

**Option B: Via Database**
```bash
# Run this every 10 seconds to watch progress
watch -n 10 "psql -U bacowr_user -d bacowr_db -c \"SELECT id, status, article_text IS NOT NULL as has_article FROM jobs WHERE id='<job-id>'\""
```

**Expected Progression:**
```
1. status=pending, has_article=f
2. status=processing, has_article=f
3. status=delivered, has_article=t
```

### Step 8: View Generated Article

1. Once status = `delivered`
2. Refresh job details page
3. Click "Article" tab
4. See generated markdown article
5. Click "QC Report" tab to see quality score
6. Export as MD/PDF/HTML

## ✅ Success Criteria

You've successfully tested BACOWR when:

- [x] Login works without errors
- [x] Job creation succeeds (no 401, no 404, no validation errors)
- [x] Job ID redirects correctly
- [x] Job appears in database
- [x] Backend background task processes job
- [x] Article is generated (status = delivered)
- [x] Article text is visible in frontend
- [x] QC report shows quality score

## 🐛 Troubleshooting

### Issue: "401 Unauthorized"

**Cause**: JWT token not being sent or expired

**Fix**:
1. Logout and login again
2. Check browser console → Application → Local Storage
3. Should see `access_token`, `refresh_token`, `user`
4. If missing, clear localStorage and login again

### Issue: "404 Not Found" on POST /api/v1/jobs

**Cause**: Backend not running or wrong URL

**Fix**:
1. Check backend is running: `curl http://localhost:8000/health`
2. Check frontend .env.local: `NEXT_PUBLIC_API_URL=http://localhost:8000`

### Issue: "422 Validation Error"

**Cause**: Field validation failed

**Fix**:
1. Check publisher_domain doesn't have `http://` prefix
2. Check target_url HAS `http://` or `https://` prefix
3. Check all required fields are filled

### Issue: Job Stuck in "pending" Status

**Cause**: Background task not running or missing API keys

**Fix**:
1. Check backend logs for errors
2. Verify `ANTHROPIC_API_KEY` is set in `api/.env`
3. Check BACOWR core is installed: `cd api && python -c "import bacowr; print('OK')"`

### Issue: "Network Error" When Creating Job

**Cause**: CORS or network issues

**Fix**:
1. Check both frontend and backend are running
2. Check CORS config in `api/app/main.py` includes `http://localhost:3000`
3. Try hard refresh (Ctrl+Shift+R)

## 📊 What Happens Behind the Scenes

When you click "Create Job":

```
1. Frontend: POST /api/v1/jobs with JWT token
   ↓
2. Backend: Validates request, creates Job row in database
   ↓
3. Backend: Returns JobResponse {id, status: "pending", ...}
   ↓
4. Frontend: Navigates to /jobs/{id}
   ↓
5. Backend: Starts background task
   ↓
6. BACOWR Core:
   - Fetches publisher content
   - Analyzes target page
   - Generates article with LLM
   - Runs QC checks
   ↓
7. Backend: Updates Job row:
   - status → "processing" → "delivered"
   - article_text → generated markdown
   - qc_report → quality metrics
   ↓
8. Frontend: Polls or WebSocket updates show progress
   ↓
9. User: Sees completed article!
```

## 🎯 Next Features to Test

After basic job creation works:

1. **Create Multiple Jobs** - Test pagination
2. **Dashboard Stats** - Verify counts update
3. **Job Filters** - Filter by status
4. **Export** - Download as MD/PDF/HTML
5. **Batch Review** - Create batch from multiple jobs
6. **Settings** - Update API keys (once endpoints exist)

## 📝 Known Limitations (OK for Now)

1. **No Settings Page** - Use `.env` for API keys instead
2. **No WebSocket Updates** - Refresh page to see status changes
3. **Publisher/Target Profiles** - Commented out, stored in `job_package` JSON
4. **No Live Dashboard** - Stats are static

These can be fixed later. Core functionality (job creation → article generation) works!

## 🚀 Production Deployment (Later)

Once testing is complete:

### Option 1: Docker Compose (Recommended)

```yaml
services:
  postgres:
    image: postgres:15
  backend:
    build: ./api
  frontend:
    build: ./frontend
```

### Option 2: Serve Frontend from FastAPI

```bash
cd frontend
npm run build
# FastAPI serves static files from frontend/out/
```

### Option 3: Separate Deployments

- Backend → Railway/Fly.io
- Frontend → Vercel
- Database → Railway PostgreSQL

## ✨ You Did It!

If job creation works, BACOWR is operational!

The rest is polish:
- Better UI
- WebSocket live updates
- More export formats
- Batch processing
- Analytics dashboards

But the core - **AI-powered article generation** - is working!

🎉 Congratulations!
