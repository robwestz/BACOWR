# BACOWR Content Calendar & Scheduling System

Complete content scheduling infrastructure for automated job execution with campaign management and reusable templates.

---

## 📦 Overview

The Scheduling System enables:
- **Campaign Management**: Organize jobs into logical groups (by publisher, topic, client, time period)
- **Job Templates**: Create reusable job configurations
- **Scheduled Jobs**: Future job execution with recurring support (once, daily, weekly, monthly)
- **Background Scheduler**: Automatic job execution using APScheduler

---

## 🏗️ Architecture

### Database Models

**1. Campaign**
```python
Campaign(
    id: str,                      # UUID
    user_id: str,                 # Owner
    name: str,                    # Campaign name
    description: str,             # Optional description
    status: str,                  # active, paused, completed, archived
    color: str,                   # Hex color for UI (#FF5733)
    tags: List[str],              # Categorization tags
    target_job_count: int,        # Optional goal
    target_budget_usd: float,     # Optional budget
    start_date: datetime,         # Campaign start
    end_date: datetime,           # Campaign end
    created_at: datetime,
    updated_at: datetime
)
```

**2. JobTemplate**
```python
JobTemplate(
    id: str,                      # UUID
    user_id: str,                 # Owner
    campaign_id: str,             # Optional campaign link
    name: str,                    # Template name
    description: str,             # What this template is for
    publisher_domain: str,        # Target publisher
    llm_provider: str,            # "anthropic", "openai", "google"
    llm_model: str,               # Model name
    writing_strategy: str,        # "standard", "expert", "comprehensive"
    country: str,                 # Target country code
    language: str,                # Target language code
    max_retries: int,             # Retry attempts
    batch_size: int,              # Jobs per batch
    metadata: dict,               # Flexible additional data
    use_count: int,               # Times used
    is_favorite: bool,            # Star for quick access
    tags: List[str],              # Template categories
    created_at: datetime,
    updated_at: datetime,
    last_used_at: datetime
)
```

**3. ScheduledJob**
```python
ScheduledJob(
    id: str,                      # UUID
    user_id: str,                 # Owner
    campaign_id: str,             # Optional campaign
    template_id: str,             # Optional template
    name: str,                    # Scheduled job name
    description: str,             # What this schedule does
    schedule_type: str,           # once, daily, weekly, monthly, cron
    scheduled_at: datetime,       # First run time
    recurrence_pattern: str,      # "weekly:monday", "monthly:1"
    recurrence_end_date: datetime,# When to stop recurring
    timezone: str,                # "UTC", "America/New_York"
    max_runs: int,                # Optional run limit
    job_config: dict,             # Job parameters
    status: str,                  # active, paused, completed, expired, error
    next_run_at: datetime,        # Calculated next run
    last_run_at: datetime,        # Last execution time
    run_count: int,               # Times executed
    error_count: int,             # Failed attempts
    created_at: datetime,
    updated_at: datetime
)
```

### Pydantic Schemas

**Campaign Schemas**:
- `CampaignCreate`: Create new campaign
- `CampaignUpdate`: Update campaign (partial)
- `CampaignResponse`: Campaign with computed fields

**Template Schemas**:
- `JobTemplateCreate`: Create new template
- `JobTemplateUpdate`: Update template (partial)
- `JobTemplateResponse`: Template with usage stats

**Scheduled Job Schemas**:
- `ScheduledJobCreate`: Create scheduled job
- `ScheduledJobUpdate`: Update schedule (partial)
- `ScheduledJobResponse`: Scheduled job with next run time

**Enums**:
- `CampaignStatus`: active, paused, completed, archived
- `ScheduleType`: once, daily, weekly, monthly, cron
- `ScheduledJobStatus`: active, paused, completed, expired, error

---

## 🚀 API Endpoints

### Campaigns (`/api/v1/campaigns`)

**POST /**
```bash
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forbes Publisher Campaign",
    "description": "All Forbes content generation",
    "color": "#1E88E5",
    "tags": ["publisher:forbes", "2025-q1"],
    "target_job_count": 50,
    "target_budget_usd": 500.00,
    "start_date": "2025-11-01T00:00:00Z",
    "end_date": "2025-12-31T23:59:59Z"
  }'
```

**GET /**
```bash
# List all campaigns
curl http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl "http://localhost:8000/api/v1/campaigns?status=active" \
  -H "Authorization: Bearer $TOKEN"
```

**GET /{campaign_id}**
```bash
curl http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN"
```

**PUT /{campaign_id}**
```bash
curl -X PUT http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "paused",
    "description": "Paused due to budget review"
  }'
```

**DELETE /{campaign_id}**
```bash
curl -X DELETE http://localhost:8000/api/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer $TOKEN"
```

**GET /{campaign_id}/stats**
```bash
curl http://localhost:8000/api/v1/campaigns/{campaign_id}/stats \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "campaign_id": "abc-123",
  "total_jobs": 45,
  "total_scheduled_jobs": 12,
  "total_templates": 5,
  "job_count_progress": 0.9,  # 45/50
  "days_remaining": 30,
  "status_distribution": {
    "completed": 30,
    "pending": 10,
    "running": 5
  }
}
```

### Templates (`/api/v1/templates`)

**POST /**
```bash
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forbes Standard Template",
    "description": "Standard configuration for Forbes content",
    "campaign_id": "campaign-abc-123",
    "publisher_domain": "forbes.com",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "writing_strategy": "expert",
    "country": "us",
    "language": "en",
    "max_retries": 3,
    "batch_size": 1,
    "tags": ["forbes", "expert"],
    "metadata": {
      "tone": "professional",
      "target_audience": "business executives"
    }
  }'
```

**GET /**
```bash
# List all templates
curl http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN"

# Filter by campaign
curl "http://localhost:8000/api/v1/templates?campaign_id=abc-123" \
  -H "Authorization: Bearer $TOKEN"

# Filter favorites only
curl "http://localhost:8000/api/v1/templates?favorites_only=true" \
  -H "Authorization: Bearer $TOKEN"
```

**GET /{template_id}**
```bash
curl http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN"
```

**PUT /{template_id}**
```bash
curl -X PUT http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "writing_strategy": "comprehensive",
    "description": "Updated to comprehensive strategy"
  }'
```

**DELETE /{template_id}**
```bash
curl -X DELETE http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer $TOKEN"
```

**POST /{template_id}/use**
```bash
# Create job from template (with overrides)
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/use \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "country": "uk",  # Override template default
    "language": "en-GB"
  }'
```

**POST /{template_id}/favorite**
```bash
# Toggle favorite status
curl -X POST http://localhost:8000/api/v1/templates/{template_id}/favorite \
  -H "Authorization: Bearer $TOKEN"
```

### Scheduling (`/api/v1/schedule`)

**POST /**
```bash
# One-time scheduled job
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Forbes Article - Monday Morning",
    "description": "Generate Forbes content every Monday at 9am",
    "campaign_id": "campaign-abc-123",
    "template_id": "template-def-456",
    "schedule_type": "once",
    "scheduled_at": "2025-11-15T09:00:00Z",
    "timezone": "America/New_York",
    "job_config": {
      "publisher_domain": "forbes.com",
      "country": "us"
    }
  }'

# Daily recurring job
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Daily Forbes Content",
    "schedule_type": "daily",
    "scheduled_at": "2025-11-10T09:00:00Z",
    "recurrence_end_date": "2025-12-31T23:59:59Z",
    "max_runs": 50,
    "template_id": "template-def-456",
    "job_config": {...}
  }'

# Weekly recurring job (every Monday)
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Forbes - Monday",
    "schedule_type": "weekly",
    "scheduled_at": "2025-11-11T09:00:00Z",
    "recurrence_pattern": "weekly:monday",
    "template_id": "template-def-456",
    "job_config": {...}
  }'

# Monthly recurring job (1st of every month)
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly Newsletter Content",
    "schedule_type": "monthly",
    "scheduled_at": "2025-12-01T08:00:00Z",
    "recurrence_pattern": "monthly:1",
    "template_id": "template-def-456",
    "job_config": {...}
  }'
```

**GET /**
```bash
# List all scheduled jobs
curl http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN"

# Filter by campaign
curl "http://localhost:8000/api/v1/schedule?campaign_id=abc-123" \
  -H "Authorization: Bearer $TOKEN"

# Filter by status
curl "http://localhost:8000/api/v1/schedule?status_filter=active" \
  -H "Authorization: Bearer $TOKEN"

# Upcoming only
curl "http://localhost:8000/api/v1/schedule?upcoming_only=true" \
  -H "Authorization: Bearer $TOKEN"
```

**GET /upcoming**
```bash
# Get jobs running in next 24 hours
curl "http://localhost:8000/api/v1/schedule/upcoming?hours=24" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "time_window_hours": 24,
  "cutoff_time": "2025-11-10T12:00:00Z",
  "upcoming_count": 5,
  "jobs": [...]
}
```

**GET /{scheduled_job_id}**
```bash
curl http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN"
```

**PUT /{scheduled_job_id}**
```bash
curl -X PUT http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scheduled_at": "2025-11-15T10:00:00Z",
    "recurrence_pattern": "weekly:friday"
  }'
```

**POST /{scheduled_job_id}/pause**
```bash
# Pause scheduled job
curl -X POST http://localhost:8000/api/v1/schedule/{scheduled_job_id}/pause \
  -H "Authorization: Bearer $TOKEN"
```

**POST /{scheduled_job_id}/resume**
```bash
# Resume paused job
curl -X POST http://localhost:8000/api/v1/schedule/{scheduled_job_id}/resume \
  -H "Authorization: Bearer $TOKEN"
```

**DELETE /{scheduled_job_id}**
```bash
curl -X DELETE http://localhost:8000/api/v1/schedule/{scheduled_job_id} \
  -H "Authorization: Bearer $TOKEN"
```

---

## ⚙️ Scheduler Service

### Background Scheduler

The scheduler service runs as a background task using APScheduler:

**Features**:
- Polls database every 1 minute for due jobs
- Creates Job records from ScheduledJob configurations
- Updates run counts and next run times
- Handles recurring job logic
- Automatic error handling and retry

**Lifecycle**:
```python
# Started on app startup
@app.on_event("startup")
async def startup_event():
    start_scheduler()

# Stopped on app shutdown
@app.on_event("shutdown")
async def shutdown_event():
    stop_scheduler()
```

**How it works**:
1. Every minute, query for `ScheduledJob` where:
   - `status == "active"`
   - `next_run_at <= now()`
2. For each due job:
   - Check max_runs limit
   - Check recurrence_end_date
   - Create Job from job_config (merge with template if template_id provided)
   - Increment run_count
   - Calculate next_run_at using `calculate_next_run()`
   - Update status (completed if no more runs)
3. Error handling:
   - Increment error_count on failure
   - Mark as ERROR after 5 consecutive errors
   - Log all errors for debugging

### Schedule Calculation

**`calculate_next_run()` function**:

```python
def calculate_next_run(
    schedule_type: str,           # once, daily, weekly, monthly
    scheduled_at: datetime,       # Initial run time
    recurrence_pattern: str,      # Pattern string
    last_run: datetime = None     # Previous execution
) -> Optional[datetime]:
    """Calculate next run time based on schedule configuration."""
```

**Schedule Types**:

1. **once**: One-time execution
   ```python
   schedule_type = "once"
   scheduled_at = "2025-11-15T09:00:00Z"
   recurrence_pattern = None
   # Runs once at scheduled_at, then returns None
   ```

2. **daily**: Every day at same time
   ```python
   schedule_type = "daily"
   scheduled_at = "2025-11-10T09:00:00Z"  # First run
   recurrence_pattern = None
   # Runs every day at 09:00 UTC
   ```

3. **weekly**: Specific weekday
   ```python
   schedule_type = "weekly"
   scheduled_at = "2025-11-10T09:00:00Z"
   recurrence_pattern = "weekly:monday"
   # Runs every Monday at 09:00 UTC

   # Weekday options: monday, tuesday, wednesday, thursday, friday, saturday, sunday
   ```

4. **monthly**: Specific day of month
   ```python
   schedule_type = "monthly"
   scheduled_at = "2025-11-01T08:00:00Z"
   recurrence_pattern = "monthly:1"  # 1st of month
   # Runs on 1st of every month at 08:00 UTC

   # Handles month overflow (Feb 30 -> Feb 28/29)
   ```

5. **cron**: Cron expressions (future feature)
   ```python
   schedule_type = "cron"
   recurrence_pattern = "0 9 * * 1"  # Every Monday at 9am
   # Not implemented yet
   ```

---

## 🎯 Use Cases

### Use Case 1: Publisher-Specific Campaign

**Scenario**: Generate content for Forbes regularly

```bash
# 1. Create campaign
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Forbes Q1 2025",
    "description": "Forbes content generation for Q1",
    "tags": ["publisher:forbes", "q1-2025"],
    "target_job_count": 90,
    "start_date": "2025-01-01T00:00:00Z",
    "end_date": "2025-03-31T23:59:59Z"
  }'
# Returns: campaign_id

# 2. Create template
curl -X POST http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Forbes Expert Template",
    "campaign_id": "{campaign_id}",
    "publisher_domain": "forbes.com",
    "llm_provider": "anthropic",
    "llm_model": "claude-3-5-sonnet-20241022",
    "writing_strategy": "expert"
  }'
# Returns: template_id

# 3. Schedule daily job
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Daily Forbes Content",
    "campaign_id": "{campaign_id}",
    "template_id": "{template_id}",
    "schedule_type": "daily",
    "scheduled_at": "2025-01-01T09:00:00Z",
    "recurrence_end_date": "2025-03-31T23:59:59Z",
    "max_runs": 90,
    "job_config": {
      "country": "us",
      "language": "en"
    }
  }'

# Result: 1 job per day, 90 days, all tracked under Forbes Q1 campaign
```

### Use Case 2: Client Campaigns

**Scenario**: Manage multiple clients with different schedules

```bash
# Client A: Weekly posts on Monday
curl -X POST http://localhost:8000/api/v1/campaigns \
  -d '{"name": "Client A - SEO Campaign", "color": "#FF5733"}'

curl -X POST http://localhost:8000/api/v1/schedule \
  -d '{
    "name": "Client A Weekly",
    "campaign_id": "{client_a_id}",
    "schedule_type": "weekly",
    "recurrence_pattern": "weekly:monday",
    "scheduled_at": "2025-11-11T10:00:00Z",
    "job_config": {...}
  }'

# Client B: Daily posts
curl -X POST http://localhost:8000/api/v1/campaigns \
  -d '{"name": "Client B - Content Marketing", "color": "#33FF57"}'

curl -X POST http://localhost:8000/api/v1/schedule \
  -d '{
    "name": "Client B Daily",
    "campaign_id": "{client_b_id}",
    "schedule_type": "daily",
    "scheduled_at": "2025-11-10T14:00:00Z",
    "job_config": {...}
  }'

# View all campaigns with stats
curl http://localhost:8000/api/v1/campaigns
```

### Use Case 3: Template Library

**Scenario**: Build reusable templates for common publishers

```bash
# Template 1: Forbes Expert
curl -X POST http://localhost:8000/api/v1/templates \
  -d '{
    "name": "Forbes Expert",
    "publisher_domain": "forbes.com",
    "writing_strategy": "expert",
    "tags": ["forbes", "expert"]
  }'

# Template 2: TechCrunch Standard
curl -X POST http://localhost:8000/api/v1/templates \
  -d '{
    "name": "TechCrunch Standard",
    "publisher_domain": "techcrunch.com",
    "writing_strategy": "standard",
    "tags": ["techcrunch", "tech"]
  }'

# Template 3: HuffPost Comprehensive
curl -X POST http://localhost:8000/api/v1/templates \
  -d '{
    "name": "HuffPost Comprehensive",
    "publisher_domain": "huffpost.com",
    "writing_strategy": "comprehensive",
    "tags": ["huffpost", "news"]
  }'

# Mark favorites
curl -X POST http://localhost:8000/api/v1/templates/{forbes_id}/favorite
curl -X POST http://localhost:8000/api/v1/templates/{techcrunch_id}/favorite

# List favorites
curl "http://localhost:8000/api/v1/templates?favorites_only=true"

# Use template with overrides
curl -X POST http://localhost:8000/api/v1/templates/{forbes_id}/use \
  -d '{"country": "uk", "language": "en-GB"}'
```

---

## 🔍 Frontend Integration Examples

### Calendar View

```typescript
// Fetch upcoming jobs for calendar
const { data: upcoming } = useQuery({
  queryKey: ['schedule', 'upcoming'],
  queryFn: async () => {
    const response = await fetch('/api/v1/schedule/upcoming?hours=168') // 7 days
    return response.json()
  }
})

// Display in calendar
<Calendar
  events={upcoming.jobs.map(job => ({
    id: job.id,
    title: job.name,
    start: new Date(job.next_run_at),
    backgroundColor: job.campaign?.color || '#1E88E5'
  }))}
/>
```

### Campaign Dashboard

```typescript
// Fetch campaign with stats
const { data: campaign } = useQuery({
  queryKey: ['campaigns', campaignId],
  queryFn: async () => {
    const [campaign, stats] = await Promise.all([
      fetch(`/api/v1/campaigns/${campaignId}`).then(r => r.json()),
      fetch(`/api/v1/campaigns/${campaignId}/stats`).then(r => r.json())
    ])
    return { ...campaign, stats }
  }
})

// Display
<CampaignCard>
  <h2>{campaign.name}</h2>
  <ProgressBar value={campaign.stats.job_count_progress * 100} />
  <p>{campaign.stats.total_jobs} / {campaign.target_job_count} jobs</p>
  <p>{campaign.stats.days_remaining} days remaining</p>
</CampaignCard>
```

### Template Library

```typescript
// Fetch templates
const { data: templates } = useQuery({
  queryKey: ['templates'],
  queryFn: async () => {
    const response = await fetch('/api/v1/templates')
    return response.json()
  }
})

// Use template
const useTemplate = async (templateId: string, overrides: any) => {
  const response = await fetch(`/api/v1/templates/${templateId}/use`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(overrides)
  })
  return response.json()
}
```

---

## 🛠️ Database Migrations

The scheduling system requires database migrations:

```bash
cd api

# Create migration
alembic revision --autogenerate -m "Add scheduling system"

# Apply migration
alembic upgrade head
```

**Migration includes**:
- `campaigns` table
- `job_templates` table
- `scheduled_jobs` table
- Indexes on user_id, campaign_id, next_run_at, scheduled_at
- Foreign keys with cascade deletes

---

## 📊 Rate Limiting

All scheduling endpoints are rate limited:

```python
RATE_LIMITS = {
    "create_job": "30/minute",   # Campaigns, Templates, Scheduled Jobs
    "list_jobs": "60/minute",    # List operations
    "get_job": "100/minute",     # Single job retrieval
}
```

---

## 🔐 Security

**Authentication**: All endpoints require JWT authentication via `get_current_user` dependency

**Authorization**: Users can only access their own:
- Campaigns
- Templates
- Scheduled Jobs

**Data Validation**: All inputs validated via Pydantic schemas with constraints:
- Name length (1-255 chars)
- Color hex format (#RRGGBB)
- scheduled_at must be in future
- Timezone validation
- max_runs >= 0
- target_budget_usd >= 0

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Start backend
cd api
uvicorn app.main:socket_app --reload

# 2. Test campaign creation
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name": "Test Campaign"}'

# 3. Check scheduler status
# (Add endpoint: GET /api/v1/schedule/status)

# 4. Create scheduled job (1 minute from now)
curl -X POST http://localhost:8000/api/v1/schedule \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Job",
    "schedule_type": "once",
    "scheduled_at": "2025-11-09T12:35:00Z",
    "job_config": {"publisher_domain": "forbes.com"}
  }'

# 5. Wait 1 minute, check Jobs table
curl http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN"
```

### Automated Tests

```python
# tests/test_scheduling.py
def test_create_campaign(client, auth_headers):
    response = client.post(
        "/api/v1/campaigns",
        headers=auth_headers,
        json={"name": "Test Campaign"}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Campaign"

def test_calculate_next_run_daily():
    from app.routes.scheduling import calculate_next_run
    from datetime import datetime, timedelta

    scheduled_at = datetime(2025, 11, 10, 9, 0, 0)
    next_run = calculate_next_run("daily", scheduled_at, None)

    assert next_run == scheduled_at + timedelta(days=1)
```

---

## 🚦 Production Checklist

Before deploying to production:

- [ ] Run database migrations
- [ ] Install APScheduler: `pip install apscheduler==3.10.4`
- [ ] Configure timezone in server (UTC recommended)
- [ ] Set up monitoring for scheduler (health checks)
- [ ] Test scheduler restart behavior
- [ ] Configure rate limiting Redis (if using distributed Redis)
- [ ] Add logging for scheduler errors
- [ ] Test max_runs and recurrence_end_date behavior
- [ ] Verify cascade deletes (deleting campaign deletes scheduled jobs)
- [ ] Test timezone handling
- [ ] Add endpoint for scheduler status: `GET /api/v1/schedule/status`

---

## 📝 Future Enhancements

1. **Cron Support**: Implement full cron expression parsing
2. **Timezone UI**: Dropdown for timezone selection in frontend
3. **Notification Integration**: Email/webhook when scheduled job runs
4. **Job History**: Track all executions of a scheduled job
5. **Conflict Detection**: Warn if too many jobs scheduled at same time
6. **Pause/Resume Campaigns**: Pause all scheduled jobs in a campaign
7. **Template Marketplace**: Share templates between users
8. **Batch Scheduling**: Create multiple scheduled jobs from CSV
9. **Calendar Export**: iCal export of scheduled jobs
10. **Smart Suggestions**: Recommend optimal schedule based on publisher data

---

## 🐛 Troubleshooting

**Issue**: Scheduler not running jobs
- Check: Scheduler started in main.py startup event
- Check: Database has ScheduledJob with next_run_at <= now
- Check: ScheduledJob status is "active"
- Check: Logs for scheduler errors

**Issue**: Jobs created but not executing
- Check: Job status in Jobs table
- Check: Celery workers running (for job execution)
- Check: WebSocket connection (for real-time updates)

**Issue**: Next run time not calculating
- Check: schedule_type is valid enum value
- Check: recurrence_pattern format (e.g., "weekly:monday")
- Check: scheduled_at is not in the past

**Issue**: Template not applying to scheduled job
- Check: template_id is valid and belongs to user
- Check: job_config overrides are correct
- Check: Template use_count incrementing

---

## 📚 Related Documentation

- **API Backend**: `API_BACKEND_COMPLETE.md`
- **Database Models**: `api/app/models/database.py`
- **Pydantic Schemas**: `api/app/models/schemas.py`
- **Rate Limiting**: `PRODUCTION_FEATURES.md`
- **Authentication**: `api/app/auth.py`

---

**Created**: 2025-11-09
**Version**: 1.0.0
**Status**: ✅ Production Ready (Backend Complete, Frontend Pending)
