# Ready for Validation: Content Calendar & Scheduling System

**Date Added:** 2025-11-09
**Chat A:** Main Build Orchestrator
**Implemented by:** Chat A
**Assigned to:** Chat B (Test & Validation Lab)

---

## 📦 Feature Summary

Complete content scheduling infrastructure with campaign management, reusable job templates, and automated job execution. Users can:
- Organize jobs into campaigns (by publisher, topic, client, time period)
- Create reusable job templates with favorite marking
- Schedule jobs to run once or recurring (daily, weekly, monthly)
- Automatic background execution using APScheduler
- Track campaign progress with stats and analytics

---

## 🎯 What Needs Validation

### Functionality to Test
- [ ] Campaign creation, update, delete
- [ ] Campaign stats calculation (job count, progress, days remaining)
- [ ] Template creation with all configuration options
- [ ] Template usage with overrides
- [ ] Template favorite toggling
- [ ] Template use_count incrementing
- [ ] Scheduled job creation (once, daily, weekly, monthly)
- [ ] Schedule calculation for all recurrence types
- [ ] Pause/resume scheduled jobs
- [ ] Background scheduler execution
- [ ] Job creation from scheduled jobs
- [ ] Template merging with job_config
- [ ] max_runs limit enforcement
- [ ] recurrence_end_date enforcement
- [ ] Error handling and error_count tracking
- [ ] Cascade deletes (campaign -> scheduled jobs)
- [ ] Rate limiting on all endpoints
- [ ] Authentication/authorization

### SEO Expert Input Needed
**Questions for the user:**
1. **Campaign organization**: How do you typically organize your SEO content projects? By publisher? By client? By time period? Does this campaign structure fit?
2. **Scheduling needs**: What recurring schedules would you actually use? Daily? Weekly? Monthly? Other patterns?
3. **Template usage**: Would you actually use templates for common publishers/configurations? What template features are most important?
4. **Calendar view**: Do you need a visual calendar to see upcoming scheduled jobs? What information should it show?
5. **Notifications**: Should you get notified when scheduled jobs run? (Email/webhook integration)
6. **Batch operations**: Do you need to create multiple scheduled jobs at once? Import from CSV?
7. **Timezone handling**: Do you work across multiple timezones? Is UTC sufficient or need timezone UI?
8. **Campaign stats**: What metrics are most important to track for campaigns?

---

## 🔧 Technical Details

### Backend Changes

**Files modified:**
- `api/app/models/database.py` (+160 lines) - Campaign, JobTemplate, ScheduledJob models
- `api/app/models/schemas.py` (+225 lines) - Pydantic schemas and enums
- `api/app/main.py` (+8 lines) - Route registration, scheduler start/stop
- `api/requirements.txt` (+1 line) - Added APScheduler

**Files created:**
- `api/app/routes/campaigns.py` (300 lines) - 7 endpoints
- `api/app/routes/templates.py` (250 lines) - 8 endpoints
- `api/app/routes/scheduling.py` (450 lines) - 11 endpoints
- `api/app/scheduler_service.py` (250 lines) - Background scheduler with APScheduler

**New endpoints:**

*Campaigns* (`/api/v1/campaigns`):
- `POST /` - Create campaign
- `GET /` - List campaigns (filter by status)
- `GET /{id}` - Get campaign
- `PUT /{id}` - Update campaign
- `DELETE /{id}` - Delete campaign
- `POST /{id}/archive` - Archive campaign
- `GET /{id}/stats` - Campaign statistics

*Templates* (`/api/v1/templates`):
- `POST /` - Create template
- `GET /` - List templates (filter by campaign, favorites)
- `GET /{id}` - Get template
- `PUT /{id}` - Update template
- `DELETE /{id}` - Delete template
- `POST /{id}/use` - Create job from template
- `POST /{id}/favorite` - Toggle favorite status
- `GET /{id}/jobs` - List jobs created from template

*Scheduling* (`/api/v1/schedule`):
- `POST /` - Create scheduled job
- `GET /` - List scheduled jobs (filter by campaign, status, upcoming)
- `GET /upcoming` - Get upcoming jobs (next N hours)
- `GET /{id}` - Get scheduled job
- `PUT /{id}` - Update scheduled job
- `POST /{id}/pause` - Pause scheduled job
- `POST /{id}/resume` - Resume paused job
- `DELETE /{id}` - Delete scheduled job

**Database changes:**
- New table: `campaigns` (13 columns)
- New table: `job_templates` (18 columns)
- New table: `scheduled_jobs` (19 columns)
- Indexes on: user_id, campaign_id, next_run_at, scheduled_at
- Foreign keys with CASCADE delete

**Dependencies added:**
- `apscheduler==3.10.4` - Background task scheduler

### Frontend Changes

**Status:** ❌ Not implemented yet (backend only)

**Will need:**
- Calendar view component for visualizing scheduled jobs
- Campaign management page (list, create, edit, stats)
- Template library page (list, create, edit, favorite)
- Scheduled job creation form (schedule type, recurrence pattern)
- Integration with existing job creation flow

### Documentation

**Added:**
- `SCHEDULING_SYSTEM.md` (1000+ lines) - Complete documentation with:
  - Architecture overview
  - All endpoint documentation with curl examples
  - Use cases (publisher campaign, client campaigns, template library)
  - Frontend integration examples
  - Scheduler service explanation
  - Testing guide
  - Production checklist
  - Troubleshooting

**Updated:**
- None (backend only implementation)

---

## 🚀 How to Test

### Prerequisites

1. **Install APScheduler:**
   ```bash
   cd /home/user/BACOWR/api
   pip install apscheduler==3.10.4
   ```

2. **Run database migration:**
   ```bash
   cd /home/user/BACOWR/api
   alembic revision --autogenerate -m "Add scheduling system"
   alembic upgrade head
   ```

3. **Start backend:**
   ```bash
   cd /home/user/BACOWR/api
   uvicorn app.main:socket_app --reload
   ```

4. **Get auth token:**
   ```bash
   # Login
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@bacowr.com", "password": "admin123"}'

   # Save token
   export TOKEN="your-jwt-token-here"
   ```

### Test Steps

**1. Campaign Testing:**
```bash
# Create campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forbes Q1 2025",
    "description": "Forbes content for Q1",
    "color": "#1E88E5",
    "tags": ["publisher:forbes", "q1-2025"],
    "target_job_count": 50,
    "target_budget_usd": 500.00,
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-03-31T23:59:59Z"
  }'
# Save campaign_id from response

# List campaigns
curl http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN"

# Get campaign by ID
curl http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN"

# Update campaign
curl -X PUT http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "paused"}'

# Get campaign stats
curl http://localhost:8000/api/v1/campaigns/{campaign_id}/stats \
  -H "Authorization: Bearer $TOKEN"
# Verify: total_jobs, total_scheduled_jobs, days_remaining

# Delete campaign
curl -X DELETE http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN"
```

**2. Template Testing:**
```bash
# Create template
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forbes Expert Template",
    "description": "Expert writing for Forbes",
    "campaign_id": "{campaign_id}",
    "publisher_domain": "forbes.com",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "writing_strategy": "expert",
    "country": "us",
    "language": "en",
    "max_retries": 3,
    "batch_size": 1,
    "tags": ["forbes", "expert"]
  }'
# Save template_id

# List templates
curl http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN"

# Filter by campaign
curl "http://localhost:8000/api/v1/templates?campaign_id={campaign_id}" \
  -H "Authorization: Bearer $TOKEN"

# Toggle favorite
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/favorite \
  -H "Authorization: Bearer $TOKEN"
# Verify: is_favorite toggles

# List favorites only
curl "http://localhost:8000/api/v1/templates?favorites_only=true" \
  -H "Authorization: Bearer $TOKEN"

# Use template (create job with overrides)
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/use \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"country": "uk", "language": "en-GB"}'
# Verify: Job created with template defaults + overrides
# Verify: Template use_count incremented
# Verify: Template last_used_at updated

# Get template
curl http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN"
# Check: use_count increased

# Update template
curl -X PUT http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"writing_strategy": "comprehensive"}'

# Delete template
curl -X DELETE http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN"
```

**3. Scheduled Jobs Testing:**
```bash
# Create one-time scheduled job (2 minutes from now)
SCHEDULED_TIME=$(date -u -d '+2 minutes' +"%Y-%m-%dT%H:%M:%SZ")
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test One-Time Job\",
    \"description\": \"Testing one-time execution\",
    \"campaign_id\": \"{campaign_id}\",
    \"template_id\": \"{template_id}\",
    \"schedule_type\": \"once\",
    \"scheduled_at\": \"$SCHEDULED_TIME\",
    \"timezone\": \"UTC\",
    \"job_config\": {
      \"publisher_domain\": \"forbes.com\",
      \"country\": \"us\"
    }
  }"
# Save scheduled_job_id
# Wait 2 minutes and check Jobs table

# Create daily recurring job
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Forbes Content",
    "schedule_type": "daily",
    "scheduled_at": "2025-11-10T09:00:00Z",
    "recurrence_end_date": "2025-12-31T23:59:59Z",
    "max_runs": 50,
    "template_id": "{template_id}",
    "job_config": {"publisher_domain": "forbes.com"}
  }'

# Create weekly recurring job (every Monday)
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Monday Job",
    "schedule_type": "weekly",
    "scheduled_at": "2025-11-11T09:00:00Z",
    "recurrence_pattern": "weekly:monday",
    "template_id": "{template_id}",
    "job_config": {"publisher_domain": "forbes.com"}
  }'

# Create monthly recurring job (1st of month)
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Newsletter",
    "schedule_type": "monthly",
    "scheduled_at": "2025-12-01T08:00:00Z",
    "recurrence_pattern": "monthly:1",
    "template_id": "{template_id}",
    "job_config": {"publisher_domain": "forbes.com"}
  }'

# List all scheduled jobs
curl http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN"

# Filter active only
curl "http://localhost:8000/api/v1/schedule?status_filter=active" \
  -H "Authorization: Bearer $TOKEN"

# Filter by campaign
curl "http://localhost:8000/api/v1/schedule?campaign_id={campaign_id}" \
  -H "Authorization: Bearer $TOKEN"

# Get upcoming jobs (next 24 hours)
curl "http://localhost:8000/api/v1/schedule/upcoming?hours=24" \
  -H "Authorization: Bearer $TOKEN"
# Verify: upcoming_count, jobs array, cutoff_time

# Get scheduled job by ID
curl http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN"
# Check: next_run_at calculated correctly

# Update scheduled job
curl -X PUT http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scheduled_at": "2025-11-15T10:00:00Z"}'
# Verify: next_run_at recalculated

# Pause scheduled job
curl -X POST http://localhost:8000/api/v1/schedule/{scheduled_job_id}/pause \
  -H "Authorization: Bearer $TOKEN"
# Verify: status = "paused"

# Resume scheduled job
curl -X POST http://localhost:8000/api/v1/schedule/{scheduled_job_id}/resume \
  -H "Authorization: Bearer $TOKEN"
# Verify: status = "active", next_run_at recalculated

# Delete scheduled job
curl -X DELETE http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN"
```

**4. Background Scheduler Testing:**
```bash
# Check backend logs for scheduler startup
# Look for: "✓ Job scheduler started (polling every 1 minute)"

# Create job scheduled 1 minute from now
SCHEDULED_TIME=$(date -u -d '+1 minute' +"%Y-%m-%dT%H:%M:%SZ")
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Scheduler Test\",
    \"schedule_type\": \"once\",
    \"scheduled_at\": \"$SCHEDULED_TIME\",
    \"template_id\": \"{template_id}\",
    \"job_config\": {\"publisher_domain\": \"forbes.com\"}
  }"

# Wait 2 minutes

# Check Jobs table for newly created job
curl http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN"
# Verify: Job created with metadata containing scheduled_job_id

# Check ScheduledJob updated
curl http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN"
# Verify: run_count = 1
# Verify: last_run_at is set
# Verify: next_run_at = null (for once schedule)
# Verify: status = "completed"

# Check backend logs
# Look for: "Created job {job_id} from scheduled job {scheduled_job_id}"
# Look for: "Successfully processed scheduled job..."
```

**5. Edge Cases & Error Handling:**
```bash
# Test: scheduled_at in the past
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Past Job",
    "schedule_type": "once",
    "scheduled_at": "2020-01-01T00:00:00Z",
    "job_config": {"publisher_domain": "forbes.com"}
  }'
# Expected: 400 Bad Request - "scheduled_at must be in the future"

# Test: Invalid campaign_id
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Job",
    "campaign_id": "non-existent",
    "schedule_type": "once",
    "scheduled_at": "2025-12-01T00:00:00Z",
    "job_config": {}
  }'
# Expected: 404 Not Found - "Campaign not found"

# Test: Invalid template_id
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Job",
    "template_id": "non-existent",
    "schedule_type": "once",
    "scheduled_at": "2025-12-01T00:00:00Z",
    "job_config": {}
  }'
# Expected: 404 Not Found - "Template not found"

# Test: Resume non-paused job
curl -X POST http://localhost:8000/api/v1/schedule/{active_job_id}/resume \
  -H "Authorization: Bearer $TOKEN"
# Expected: 400 Bad Request - "Can only resume paused jobs"

# Test: max_runs enforcement
# Create job with max_runs=1, schedule 1 min from now, wait for execution
# Verify: After 1 run, status = "completed", next_run_at = null

# Test: recurrence_end_date enforcement
# Create daily job with recurrence_end_date in past
# Verify: Scheduler marks as "expired"

# Test: Cascade delete (delete campaign with scheduled jobs)
curl -X DELETE http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN"
# Verify: All scheduled_jobs with that campaign_id are deleted

# Test: Invalid color format
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test", "color": "red"}'
# Expected: 422 Validation Error - color must match #RRGGBB pattern
```

**6. Rate Limiting Testing:**
```bash
# Test: Create 40 campaigns in 1 minute (limit is 30/minute)
for i in {1..40}; do
  curl -X POST http://localhost:8000/api/v1/campaigns \
    -H "Authorization: Bearer $TOKEN" \
    -d "{\"name\": \"Campaign $i\"}" &
done
wait
# Expected: Some requests return 429 Too Many Requests
```

### Edge Cases to Test
- [ ] scheduled_at in the past
- [ ] max_runs = 0
- [ ] max_runs = 1 (single execution then complete)
- [ ] recurrence_end_date before scheduled_at
- [ ] recurrence_end_date in the past
- [ ] Invalid campaign_id
- [ ] Invalid template_id
- [ ] Delete campaign with scheduled jobs (cascade)
- [ ] Delete template used by scheduled job (should fail or set template_id to null?)
- [ ] Resume active job (should fail)
- [ ] Pause completed job (should fail or be allowed?)
- [ ] Weekly pattern: "weekly:invalidday"
- [ ] Monthly pattern: "monthly:32" (invalid day)
- [ ] Monthly pattern: "monthly:31" in February (should use Feb 28/29)
- [ ] Template with missing required fields
- [ ] job_config with invalid JSON
- [ ] Color format validation (#RRGGBB)
- [ ] Tag array with empty strings
- [ ] Very long campaign/template names (>255 chars)
- [ ] Negative target_job_count
- [ ] Negative target_budget_usd
- [ ] Rate limiting (30 creates per minute)

---

## 📊 Expected Behavior

**Success case (Campaign creation):**
1. User creates campaign with name, description, color, targets
2. API returns 201 Created with campaign object
3. Campaign appears in list
4. Stats endpoint shows initial values (0 jobs, 100% progress if no target)

**Success case (Template usage):**
1. User creates template with Forbes config
2. User marks as favorite
3. User uses template with country override
4. Job created with template defaults + override
5. Template use_count increments
6. Template last_used_at updates

**Success case (Scheduled job - daily):**
1. User creates daily scheduled job starting 2025-11-10 09:00 UTC
2. API calculates next_run_at = 2025-11-10 09:00 UTC
3. Scheduler polls database every minute
4. At 2025-11-10 09:00 UTC, scheduler creates Job from config
5. Scheduler updates: run_count=1, last_run_at=2025-11-10 09:00, next_run_at=2025-11-11 09:00
6. Process repeats daily until max_runs or recurrence_end_date

**Success case (One-time job):**
1. User schedules job for specific datetime
2. Scheduler executes at that time
3. Creates Job
4. Updates scheduled_job: status="completed", next_run_at=null

**Error cases:**
1. scheduled_at in past → 400 Bad Request
2. Invalid campaign_id → 404 Not Found
3. Invalid template_id → 404 Not Found
4. Resume non-paused job → 400 Bad Request
5. Invalid recurrence_pattern → 400 Bad Request or ignored (document this)
6. Rate limit exceeded → 429 Too Many Requests
7. Scheduler error (5 consecutive) → scheduled_job.status = "error"

---

## 🔗 Related

**Commits:**
- Not committed yet (will commit after creating this queue item)

**Pull Request:** (if applicable)
N/A (working on feature branch: claude/del3b-content-generation-011CUtTfMcDsrLTYBZ8i89v5)

**Related features:**
- Job creation API (uses scheduled jobs)
- Campaign analytics (future frontend)
- Calendar UI (future frontend)
- Notification system (can integrate: notify when scheduled job runs)

**Documentation:**
- `SCHEDULING_SYSTEM.md` - Complete documentation (1000+ lines)
- `API_BACKEND_COMPLETE.md` - Will need update
- `PROJECT_CONTEXT.md` - Will need update

---

## 💬 Notes from Chat A

### Important Context

1. **Backend only implementation**: This is backend infrastructure only. Frontend calendar/campaign UI not implemented yet. All testing must be done via curl/Postman.

2. **APScheduler polling**: The scheduler polls every 1 minute. This means jobs won't execute exactly at scheduled_at, but within 1 minute of it. For production, this interval can be adjusted.

3. **Timezone handling**: Currently everything is UTC. Frontend will need timezone conversion for user display. Timezone field exists but not fully utilized yet.

4. **Template flexibility**: Templates provide defaults but job_config can override any field. Test this thoroughly - it's a key feature.

5. **Cascade deletes**: Deleting a campaign deletes all its scheduled_jobs and templates. This is intentional but needs to be documented/confirmed with user.

6. **Error recovery**: If scheduler fails to create a job 5 times, scheduled_job is marked as "error". Manual intervention needed to resume. This prevents infinite retry loops.

7. **Database migration required**: The three new tables (campaigns, job_templates, scheduled_jobs) require migration. Don't forget this step!

8. **Rate limiting uses existing config**: Same limits as job creation (30/minute). May need separate limits for scheduling operations based on usage.

### Known Limitations

1. **No cron support**: schedule_type="cron" is defined but not implemented. Need cron parser library (e.g., croniter).

2. **No timezone UI**: Timezone field exists but no UI for selecting timezone. Everything defaults to UTC.

3. **No conflict detection**: System doesn't warn if you schedule 100 jobs at the same time. Could overload system.

4. **No job history**: Scheduled jobs don't track history of all executions. Only run_count, last_run_at.

5. **No batch scheduling**: Can't create multiple scheduled jobs from CSV or bulk operation.

6. **No campaign pause**: Pausing a campaign doesn't pause all its scheduled jobs. Need to add this feature or document.

7. **Delete template with active schedules**: Not sure what happens if you delete a template that scheduled jobs are using. Need to test!

8. **Monthly overflow edge case**: "monthly:31" in February uses last day (28/29). Document this clearly.

### Areas Needing Special Attention

1. **Schedule calculation accuracy**: The `calculate_next_run()` function is complex. Test all schedule types thoroughly:
   - once → should return None after first run
   - daily → should add exactly 24 hours
   - weekly:monday → should find next Monday
   - monthly:1 → should handle month boundaries (Dec→Jan)
   - monthly:31 → should handle Feb (28/29)

2. **Scheduler reliability**: APScheduler must survive server restarts. Test:
   - Create scheduled job
   - Restart server
   - Verify scheduler still processes it

3. **Race conditions**: What if two scheduler instances run? (Shouldn't happen with max_instances=1, but test)

4. **max_runs and recurrence_end_date interaction**: What if both are set? Which takes precedence? (First to trigger)

5. **Template merging logic**: job_config overrides template. Verify:
   - All template fields can be overridden
   - Missing fields from template are used
   - job_config-only fields work

6. **Error handling**: Simulate job creation failures:
   - Invalid publisher_domain
   - Missing required fields
   - Verify error_count increments
   - Verify status changes to "error" after 5 failures

7. **Authentication**: All endpoints are protected. Test:
   - Cannot access other users' campaigns
   - Cannot use other users' templates
   - Cannot schedule jobs for other users

8. **Database performance**: With 1000s of scheduled jobs, is the query efficient?
   - Index on next_run_at is critical
   - Index on (user_id, campaign_id) for filtering

### Testing Priority

**High Priority (Must Test)**:
1. ✅ All schedule types (once, daily, weekly, monthly)
2. ✅ Background scheduler execution (end-to-end)
3. ✅ Template usage with overrides
4. ✅ max_runs enforcement
5. ✅ recurrence_end_date enforcement
6. ✅ Pause/resume functionality
7. ✅ Cascade deletes
8. ✅ Authentication/authorization

**Medium Priority (Should Test)**:
1. Campaign stats accuracy
2. Template use_count incrementing
3. Favorite toggling
4. Error handling and error_count
5. Rate limiting
6. Edge cases (past dates, invalid IDs)
7. Update operations (recalculate next_run)

**Low Priority (Nice to Test)**:
1. Very long names (255 char limit)
2. Special characters in names
3. Empty tags array
4. Null optional fields
5. Performance with many scheduled jobs

---

## ✅ Ready for Testing

This feature is complete (backend) and ready for validation by Chat B + SEO Expert.

**Status:** 🟢 Ready (Backend Complete, Frontend Pending)
**Priority:** High (Major feature for content calendar functionality)
**Expected validation time:** 2-3 hours (including migration, curl testing, scheduler testing)

**Testing checklist for Chat B:**
- [ ] Run database migration
- [ ] Install APScheduler dependency
- [ ] Test all campaign endpoints
- [ ] Test all template endpoints
- [ ] Test all scheduled job endpoints
- [ ] Test background scheduler execution
- [ ] Test all schedule types (once, daily, weekly, monthly)
- [ ] Test pause/resume
- [ ] Test max_runs and recurrence_end_date
- [ ] Test template usage with overrides
- [ ] Test cascade deletes
- [ ] Test error cases and validation
- [ ] Test authentication/authorization
- [ ] Test rate limiting
- [ ] Verify documentation accuracy
- [ ] Gather SEO expert feedback on workflow fit
- [ ] Generate validation report with findings
- [ ] Suggest frontend UI/UX requirements

---

**Created by:** Chat A (Main Build Orchestrator)
**Date:** 2025-11-09
**Ready for:** Chat B (Test & Validation Lab)
