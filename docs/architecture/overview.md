# BACOWR Architecture Overview

## System Overview

BACOWR (BacklinkContent Writer) is an AI-powered content generation system designed for SEO professionals who need to create backlink articles at scale. The system processes batches of 175-link assignments, generating high-quality, contextually relevant articles for each link.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js 14)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Job Creator │  │ Batch Review │  │  Analytics   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────────┬────────────────────────────────┘
                             │ REST API (WebSocket for progress)
┌────────────────────────────┼────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  API Routes  │  │  Middleware  │  │   Services   │      │
│  │  - Jobs      │  │  - Auth      │  │  - LLM       │      │
│  │  - Batches   │  │  - RateLimit │  │  - Batch     │      │
│  │  - Analytics │  │  - Audit     │  │  - Backlink  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                             │                                │
│                    ┌────────┴─────────┐                      │
│                    │ Database Layer   │                      │
│                    │  (SQLAlchemy)    │                      │
│                    └────────┬─────────┘                      │
└─────────────────────────────┼──────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  PostgreSQL/SQLite │
                    └────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 External Services (LLM Providers)            │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐           │
│  │  Claude  │     │   GPT    │     │  Gemini  │           │
│  └──────────┘     └──────────┘     └──────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Frontend (Next.js 14)

**Technology Stack:**
- Next.js 14 with App Router
- TypeScript for type safety
- Tailwind CSS for styling
- React Query for data fetching
- Zustand for state management

**Key Features:**
- Single-page job creation with real-time validation
- Batch review interface with approve/reject/regenerate controls
- Real-time progress tracking via WebSocket
- Analytics dashboard with filtering and export

**Directory Structure:**
```
frontend/src/app/
├── jobs/
│   ├── new/page.tsx          # Job creation form
│   └── [id]/page.tsx         # Job detail view
├── batches/
│   ├── page.tsx              # Batch list
│   └── [id]/review/page.tsx  # Batch review UI
├── analytics/page.tsx        # Analytics dashboard
└── components/               # Reusable components
```

### 2. Backend API (FastAPI)

**Technology Stack:**
- FastAPI for high-performance async API
- SQLAlchemy ORM for database operations
- Pydantic for data validation
- SlowAPI for rate limiting
- Alembic for database migrations

**API Structure:**
```
/api/v1/
├── jobs/                    # Job management
│   ├── POST /               # Create job
│   ├── GET /{id}            # Get job status
│   └── POST /{id}/execute   # Start job execution
├── batches/                 # Batch review workflow
│   ├── POST /               # Create batch from jobs
│   ├── GET /{id}            # Get batch details
│   ├── POST /{id}/items/{item_id}/review  # Review item
│   └── POST /{id}/export    # Export approved batch
├── analytics/               # Analytics endpoints
│   ├── GET /jobs/stats      # Job statistics
│   └── GET /backlinks/stats # Backlink statistics
├── audit/                   # Audit logging (admin only)
│   ├── GET /logs            # Audit log query
│   └── GET /security-events # Security events
└── ws/                      # WebSocket connections
    └── /jobs/{id}           # Job progress updates
```

**Middleware Stack:**
```python
Request → CORS → Rate Limiting → Audit Logging → Auth → Route Handler
```

### 3. Database Layer

**Schema Design:**

**Core Tables:**
- `users` - User authentication and profiles
- `jobs` - Individual content generation jobs
- `backlinks` - Generated backlink articles (1:1 with jobs)
- `batches` - Collection of jobs for Day 2 QA review
- `batch_review_items` - Individual items within a batch with QC snapshots
- `audit_logs` - Complete audit trail of all actions

**Key Relationships:**
```
User (1) ──→ (N) Jobs
Jobs (N) ──→ (1) Batch
Batch (1) ──→ (N) BatchReviewItems
BatchReviewItems (1) ──→ (1) Jobs (QC snapshot)
User (1) ──→ (N) AuditLogs
```

**Migration Strategy:**
- Alembic for version control
- Auto-generated migrations from model changes
- Both upgrade and downgrade paths
- Environment-based DATABASE_URL configuration

### 4. LLM Integration Layer

**Multi-Provider Support:**

The system supports multiple LLM providers with automatic fallback:

```python
class LLMService:
    def __init__(self):
        self.providers = [
            ClaudeProvider(),
            OpenAIProvider(),
            GeminiProvider()
        ]

    async def generate_content(self, job: Job):
        """Generate content with fallback logic"""
        for provider in self.providers:
            try:
                return await provider.generate(job)
            except Exception:
                continue  # Try next provider
        raise AllProvidersFailedError()
```

**Provider Configuration:**
- Each provider has configurable API keys, models, and rate limits
- System tracks provider usage and costs
- Automatic retry with exponential backoff
- Circuit breaker pattern for failing providers

### 5. Security Architecture

**Authentication & Authorization:**
- JWT-based authentication
- Role-based access control (user, admin)
- Secure password hashing with bcrypt
- Token refresh mechanism

**Rate Limiting:**
- SlowAPI with Redis backend (in-memory fallback)
- Per-user rate limits: 1000/day, 100/hour
- Expensive operations: 10/minute, 100/hour
- IP-based rate limiting for unauthenticated requests

**Audit Logging:**
- Complete audit trail of all API requests
- User activity tracking
- Security event detection (failed logins, unauthorized access)
- PII sanitization in logs (passwords, tokens redacted)

**Data Sanitization:**
```python
SENSITIVE_FIELDS = {
    'password', 'token', 'api_key', 'secret',
    'authorization', 'cookie', 'session'
}

def sanitize_data(data: Dict) -> Dict:
    """Recursively sanitize sensitive data"""
    # Redact values for sensitive fields
```

## Data Flow

### Single Job Workflow (Day 1)

```
1. User creates job via POST /api/v1/jobs
   ↓
2. Backend validates input, creates Job record (status: pending)
   ↓
3. User triggers execution via POST /api/v1/jobs/{id}/execute
   ↓
4. Background task starts:
   a. Fetch backlink URL and extract context
   b. Generate article content via LLM
   c. Create Backlink record with generated content
   d. Update Job status to completed
   ↓
5. Frontend polls or WebSocket receives completion event
   ↓
6. User reviews generated content
```

### Batch Review Workflow (Day 2 QA)

```
1. User creates batch from completed jobs via POST /api/v1/batches
   ↓
2. Backend creates Batch and BatchReviewItems:
   - Takes QC snapshot of each job's current state
   - Stores original backlink content for comparison
   - Initializes review_status: pending
   ↓
3. User opens batch review UI
   ↓
4. For each item, user can:

   APPROVE:
   ├─→ POST /batches/{id}/items/{item_id}/review
   │   {decision: "approve", notes: "..."}
   ├─→ Backend updates item.review_status = approved
   └─→ Increment batch.stats.approved_count

   REJECT:
   ├─→ POST /batches/{id}/items/{item_id}/review
   │   {decision: "reject", notes: "why it failed"}
   ├─→ Backend updates item.review_status = rejected
   └─→ Increment batch.stats.rejected_count

   REGENERATE:
   ├─→ POST /batches/{id}/items/{item_id}/review
   │   {decision: "needs_regeneration", notes: "what to fix"}
   ├─→ Backend updates item.review_status = needs_regeneration
   ├─→ Triggers background regeneration task
   ├─→ Updates Job with new content
   ├─→ Updates item.review_status = regenerated
   └─→ User can re-review the regenerated content
   ↓
5. When batch complete (all items approved or rejected):
   ├─→ User exports via POST /batches/{id}/export
   └─→ Receives JSON with all approved content
```

## Scalability Considerations

### Current Scale (MVP)

- **Target**: 1000 jobs/day per user
- **Batch Size**: 175 links/batch
- **Storage**: SQLite for development, PostgreSQL for production
- **Concurrent Jobs**: 10 per user (rate limited)

### Future Scale (Production)

**Horizontal Scaling:**
- Stateless API servers (can run multiple instances)
- Background job queue (Celery + Redis)
- Database read replicas for analytics queries

**Caching Strategy:**
- Redis for:
  - Rate limiting counters
  - Session data
  - Frequently accessed job status
  - WebSocket connection tracking

**Database Optimization:**
- Indexed columns: user_id, status, created_at, batch_id
- Partitioning for audit_logs (by timestamp)
- Archive old completed jobs to cold storage

## Monitoring & Observability

### Metrics (Optional - Wave 3)

If monitoring is enabled:

```
Prometheus Metrics:
├── api_requests_total (counter by endpoint, method, status)
├── api_request_duration_seconds (histogram)
├── llm_generation_duration_seconds (histogram by provider)
├── llm_generation_cost_dollars (counter by provider)
├── active_jobs (gauge)
└── batch_review_progress_percent (gauge by batch_id)
```

### Logging Strategy

**Application Logs:**
- Structured JSON logging
- Log levels: DEBUG (dev), INFO (prod), ERROR (always)
- Correlation IDs for request tracking

**Audit Logs:**
- All API requests logged to database
- Retention: 90 days minimum
- Queryable via admin API

## Technology Decisions

### Why FastAPI?

- **Performance**: Async/await support for I/O-bound LLM operations
- **Developer Experience**: Auto-generated OpenAPI docs, Pydantic validation
- **Ecosystem**: Rich middleware ecosystem (CORS, rate limiting, auth)

### Why Next.js 14?

- **Modern React**: App Router with Server Components
- **Performance**: Built-in optimization (images, fonts, code splitting)
- **Developer Experience**: TypeScript, hot reload, API routes

### Why SQLAlchemy?

- **Flexibility**: Works with SQLite (dev) and PostgreSQL (prod)
- **ORM Benefits**: Type-safe queries, relationship management
- **Migration Support**: Alembic integration

### Why Multi-Provider LLM Support?

- **Reliability**: Fallback if primary provider is down
- **Cost Optimization**: Route to cheapest provider for simple tasks
- **Quality**: Use best provider for each content type
- **Vendor Lock-in**: Avoid dependency on single LLM vendor

## Security Best Practices

1. **Input Validation**: All API inputs validated via Pydantic schemas
2. **SQL Injection**: Protected by SQLAlchemy ORM (parameterized queries)
3. **XSS**: Frontend sanitizes all user-generated content
4. **CSRF**: Token-based authentication (stateless JWT)
5. **Rate Limiting**: Prevents abuse and DoS attacks
6. **Audit Logging**: Complete trail for security investigations
7. **Secret Management**: Environment variables, never in code
8. **HTTPS Only**: Enforced in production via middleware

## Deployment Architecture

```
Development:
├── SQLite database (file-based)
├── In-memory rate limiting
└── Hot reload enabled

Production:
├── PostgreSQL database (Railway/managed)
├── Redis for rate limiting and caching
├── Environment-based configuration
├── Alembic migrations on deployment
└── Health check endpoints for monitoring
```

## API Versioning Strategy

- **Current**: `/api/v1/*` (all endpoints)
- **Future**: `/api/v2/*` when breaking changes needed
- **Deprecation**: Old versions supported for 6 months minimum
- **Version Headers**: Optional `API-Version` header for client control

## Error Handling

**HTTP Status Codes:**
- `200 OK` - Successful request
- `201 Created` - Resource created
- `400 Bad Request` - Validation error
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource doesn't exist
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Unexpected error

**Error Response Format:**
```json
{
  "detail": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",
  "field": "email",
  "timestamp": "2025-11-19T12:34:56Z"
}
```

## Testing Strategy

**Backend:**
- Unit tests: Service layer logic
- Integration tests: API endpoints with test database
- E2E tests: Complete workflows (job creation → execution → batch review)
- Smoke tests: Critical path validation

**Frontend:**
- Component tests: React Testing Library
- E2E tests: Playwright for user workflows
- Visual regression: Chromatic for UI changes

**CI/CD:**
- GitHub Actions runs all tests on PR
- Deployment blocked if tests fail
- Automatic migration on successful deployment

## References

- [API Documentation](../api/openapi.yaml)
- [Database Migrations Guide](../../api/DATABASE_MIGRATIONS.md)
- [Deployment Guide](../deployment/production.md)
- [Development Setup](../development/setup.md)
- [Orchestration Framework](../orchestration/framework.md)
