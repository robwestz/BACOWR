# BACOWR API Reference

**Version:** 1.0.0 (API v1)
**Last Updated:** 2025-11-19
**Base URL**: `https://api.bacowr.com/v1` (production) | `http://localhost:5000/api/v1` (development)
**Authentication**: JWT Bearer tokens (v1.8+) | API Keys (v1.6-1.7)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Core Endpoints](#core-endpoints)
4. [Request/Response Format](#requestresponse-format)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Webhooks](#webhooks)
8. [API Changelog](#api-changelog)

---

## Overview

The BACOWR API follows **REST principles** with JSON payloads. All endpoints return consistent response structures with proper HTTP status codes.

### API Principles

- **RESTful**: Resource-oriented URLs (`/jobs`, `/jobs/{id}`, etc.)
- **JSON**: All requests and responses use `application/json`
- **Idempotent**: GET, PUT, DELETE are idempotent; POST creates new resources
- **Stateless**: Each request contains full authentication context
- **Versioned**: API version in URL (`/v1/`, `/v2/`) for backward compatibility

### Base Response Structure

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-19T14:30:00Z",
    "request_id": "req_abc123",
    "version": "v1"
  }
}
```

---

## Authentication

### JWT Bearer Tokens (v1.8+)

**Obtain Token**:
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..."
  }
}
```

**Use Token**:
```http
GET /v1/jobs
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Keys (v1.6-1.7, Legacy)

```http
GET /v1/jobs
X-API-Key: sk_live_abc123...
```

---

## Core Endpoints

### Jobs API

#### Create Job

**Endpoint**: `POST /v1/jobs`

**Description**: Create a new backlink article generation job.

**Request**:
```http
POST /v1/jobs
Content-Type: application/json
Authorization: Bearer {token}

{
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://example.com/product",
  "anchor_text": "best project management tools",
  "options": {
    "llm_provider": "anthropic",
    "strategy": "multi_stage",
    "preflight_mode": "heavy"
  }
}
```

**Request Schema**:
```typescript
interface CreateJobRequest {
  publisher_domain: string;          // Required: e.g., "aftonbladet.se"
  target_url: string;                // Required: URL to link to
  anchor_text: string;               // Required: 3-150 chars
  idempotency_key?: string;          // Optional: max 255 chars, for safe retries
  options?: {
    llm_provider?: "anthropic" | "openai" | "google"; // Default: "anthropic"
    strategy?: "single_stage" | "multi_stage";         // Default: "multi_stage"
    preflight_mode?: "light" | "heavy";                // Default: "heavy"
    custom_instructions?: string;                      // Optional: max 500 chars
  };
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "RECEIVE",
    "created_at": "2025-11-19T14:30:00Z",
    "estimated_completion": "2025-11-19T14:32:00Z"
  },
  "meta": {
    "timestamp": "2025-11-19T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Anchor text must be between 3 and 150 characters",
    "field": "anchor_text",
    "details": {
      "provided_length": 2,
      "min_length": 3,
      "max_length": 150
    }
  }
}
```

---

#### Get Job Status

**Endpoint**: `GET /v1/jobs/{job_id}`

**Description**: Retrieve job status and results.

**Request**:
```http
GET /v1/jobs/job_xyz789
Authorization: Bearer {token}
```

**Response** (200 OK - Job In Progress):
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "WRITE",
    "progress": 65,
    "created_at": "2025-11-19T14:30:00Z",
    "updated_at": "2025-11-19T14:31:30Z",
    "estimated_completion": "2025-11-19T14:32:00Z",
    "state_history": [
      {"state": "RECEIVE", "timestamp": "2025-11-19T14:30:00Z"},
      {"state": "PREFLIGHT", "timestamp": "2025-11-19T14:30:05Z"},
      {"state": "WRITE", "timestamp": "2025-11-19T14:31:20Z"}
    ]
  }
}
```

**Response** (200 OK - Job Complete):
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "DELIVER",
    "progress": 100,
    "created_at": "2025-11-19T14:30:00Z",
    "completed_at": "2025-11-19T14:32:15Z",
    "duration_seconds": 135,
    "article": {
      "title": "Bästa projektverktyg för distansarbete 2024",
      "content": "...",
      "word_count": 1247,
      "backlink": {
        "anchor_text": "best project management tools",
        "target_url": "https://example.com/product",
        "position": 487
      }
    },
    "qc_report": {
      "status": "PASS",
      "score": 92,
      "checks": {
        "word_count": {"passed": true, "actual": 1247, "required": 900},
        "trust_sources": {"passed": true, "count": 3, "required": 1},
        "anchor_naturalness": {"passed": true, "score": 8.5},
        "intent_alignment": {"passed": true, "confidence": 0.89}
      }
    },
    "cost": {
      "llm": 0.12,
      "serp": 0.03,
      "total": 0.15,
      "currency": "USD"
    }
  }
}
```

**Response** (200 OK - Job Blocked):
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "BLOCKED",
    "created_at": "2025-11-19T14:30:00Z",
    "blocked_at": "2025-11-19T14:32:45Z",
    "qc_report": {
      "status": "FAIL",
      "score": 42,
      "checks": {
        "word_count": {"passed": false, "actual": 687, "required": 900},
        "trust_sources": {"passed": false, "count": 0, "required": 1}
      },
      "issues": [
        {
          "severity": "high",
          "category": "word_count",
          "message": "Article too short (687 words, minimum 900)",
          "auto_fixable": true
        },
        {
          "severity": "high",
          "category": "trust_sources",
          "message": "No Tier 1 trust sources cited",
          "auto_fixable": false,
          "action": "Manual review required - add authoritative sources"
        }
      ]
    }
  }
}
```

---

#### List Jobs

**Endpoint**: `GET /v1/jobs`

**Description**: List all jobs with pagination and filtering.

**Request**:
```http
GET /v1/jobs?status=DELIVER&limit=20&offset=0&sort=-created_at
Authorization: Bearer {token}
```

**Query Parameters**:
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `status` | string | Filter by status (RECEIVE, PREFLIGHT, WRITE, QC, RESCUE, DELIVER, BLOCKED, ERROR) | All |
| `publisher_domain` | string | Filter by publisher | All |
| `limit` | integer | Results per page (max 100) | 20 |
| `offset` | integer | Pagination offset | 0 |
| `sort` | string | Sort field (`created_at`, `-created_at`, `status`) | `-created_at` |
| `date_from` | ISO 8601 | Filter jobs created after | None |
| `date_to` | ISO 8601 | Filter jobs created before | None |

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "job_xyz789",
        "status": "DELIVER",
        "publisher_domain": "aftonbladet.se",
        "target_url": "https://example.com/product",
        "anchor_text": "best project management tools",
        "created_at": "2025-11-19T14:30:00Z",
        "completed_at": "2025-11-19T14:32:15Z"
      },
      // ... more jobs
    ],
    "pagination": {
      "total": 347,
      "limit": 20,
      "offset": 0,
      "has_more": true,
      "next_offset": 20
    }
  }
}
```

---

#### Cancel Job

**Endpoint**: `DELETE /v1/jobs/{job_id}`

**Description**: Cancel a job in progress (cannot cancel completed jobs).

**Request**:
```http
DELETE /v1/jobs/job_xyz789
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "job_id": "job_xyz789",
    "status": "CANCELLED",
    "cancelled_at": "2025-11-19T14:31:00Z"
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "success": false,
  "error": {
    "code": "CANNOT_CANCEL_COMPLETED_JOB",
    "message": "Job has already completed and cannot be cancelled",
    "job_status": "DELIVER"
  }
}
```

---

### Batch API

#### Create Batch

**Endpoint**: `POST /v1/batches`

**Description**: Create a batch of multiple jobs.

**Request**:
```http
POST /v1/batches
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Swedish News Sites - December 2025",
  "jobs": [
    {
      "publisher_domain": "aftonbladet.se",
      "target_url": "https://example.com/product-a",
      "anchor_text": "best project tools"
    },
    {
      "publisher_domain": "svd.se",
      "target_url": "https://example.com/product-b",
      "anchor_text": "top remote work software"
    }
    // ... up to 175 jobs
  ],
  "options": {
    "llm_provider": "anthropic",
    "strategy": "multi_stage",
    "chunk_size": 25,
    "parallel_jobs": 5
  }
}
```

**Response** (201 Created):
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "name": "Swedish News Sites - December 2025",
    "total_jobs": 175,
    "status": "RUNNING",
    "created_at": "2025-11-19T14:30:00Z",
    "estimated_completion": "2025-11-19T15:00:00Z",
    "progress": {
      "completed": 0,
      "in_progress": 25,
      "pending": 150,
      "failed": 0
    }
  }
}
```

---

#### Get Batch Status

**Endpoint**: `GET /v1/batches/{batch_id}`

**Request**:
```http
GET /v1/batches/batch_abc123
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "batch_id": "batch_abc123",
    "name": "Swedish News Sites - December 2025",
    "total_jobs": 175,
    "status": "RUNNING",
    "created_at": "2025-11-19T14:30:00Z",
    "updated_at": "2025-11-19T14:45:00Z",
    "progress": {
      "completed": 87,
      "in_progress": 25,
      "pending": 58,
      "failed": 5,
      "blocked": 0,
      "percentage": 49.7
    },
    "summary": {
      "successful_jobs": 87,
      "blocked_jobs": 0,
      "failed_jobs": 5,
      "avg_qc_score": 88.3,
      "total_cost": 12.45
    },
    "job_ids": [
      "job_xyz789",
      "job_abc456",
      // ... all job IDs
    ]
  }
}
```

---

### CMS Integration API

#### Export to WordPress

**Endpoint**: `POST /v1/jobs/{job_id}/export/wordpress`

**Description**: Export completed job directly to WordPress.

**Request**:
```http
POST /v1/jobs/job_xyz789/export/wordpress
Content-Type: application/json
Authorization: Bearer {token}

{
  "wordpress_url": "https://myblog.com",
  "username": "admin",
  "application_password": "xxxx xxxx xxxx xxxx xxxx xxxx",
  "post_status": "draft",
  "categories": [12, 45],
  "tags": ["SEO", "backlinks", "project management"]
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "wordpress_post_id": 1234,
    "post_url": "https://myblog.com/wp-admin/post.php?post=1234&action=edit",
    "published_url": null,
    "status": "draft"
  }
}
```

---

### Analytics API

#### Get User Stats

**Endpoint**: `GET /v1/analytics/stats`

**Description**: Get user-level usage statistics.

**Request**:
```http
GET /v1/analytics/stats?period=30d
Authorization: Bearer {token}
```

**Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "period": "30d",
    "jobs": {
      "total": 342,
      "successful": 287,
      "blocked": 42,
      "failed": 13,
      "success_rate": 83.9
    },
    "quality": {
      "avg_qc_score": 87.5,
      "avg_word_count": 1156,
      "avg_trust_sources": 2.3
    },
    "cost": {
      "total": 45.67,
      "avg_per_job": 0.13,
      "llm": 32.45,
      "serp": 13.22,
      "currency": "USD"
    },
    "performance": {
      "avg_duration_seconds": 48,
      "cache_hit_rate": 0.31
    }
  }
}
```

---

## Request/Response Format

### Common Headers

**Request Headers**:
```
Authorization: Bearer {token}
Content-Type: application/json
Accept: application/json
User-Agent: BACOWR-Client/1.0
```

**Response Headers**:
```
Content-Type: application/json
X-Request-ID: req_abc123
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1700580000
```

### Pagination

All list endpoints support offset-based pagination:

**Request**:
```http
GET /v1/jobs?limit=20&offset=40
```

**Response includes**:
```json
{
  "data": { ... },
  "pagination": {
    "total": 347,
    "limit": 20,
    "offset": 40,
    "has_more": true,
    "next_offset": 60
  }
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| **200** | OK | Successful GET, PUT, DELETE |
| **201** | Created | Successful POST (job/batch created) |
| **400** | Bad Request | Invalid input, validation error |
| **401** | Unauthorized | Missing or invalid auth token |
| **403** | Forbidden | Valid auth but insufficient permissions |
| **404** | Not Found | Resource doesn't exist (job_id not found) |
| **422** | Unprocessable Entity | Job blocked by QC (semantic error, not syntax) |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server-side error |
| **503** | Service Unavailable | Maintenance mode or overload |

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "field": "field_name",
    "details": { ... }
  },
  "meta": {
    "timestamp": "2025-11-19T14:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Input validation failed |
| `INVALID_PUBLISHER` | 400 | Publisher domain not supported |
| `INVALID_URL` | 400 | Target URL malformed or unreachable |
| `ANCHOR_TOO_LONG` | 400 | Anchor text exceeds 150 characters |
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `JOB_NOT_FOUND` | 404 | Job ID doesn't exist |
| `JOB_BLOCKED` | 422 | Job failed QC validation |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `SERP_API_ERROR` | 500 | SERP provider API failed |
| `LLM_API_ERROR` | 500 | LLM provider API failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limiting

### Default Limits

| Tier | Requests/Hour | Concurrent Jobs | Batch Size |
|------|---------------|-----------------|------------|
| **Free** | 100 | 5 | 25 |
| **Pro** | 1000 | 20 | 175 |
| **Enterprise** | Custom | Custom | Custom |

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1700580000
```

### Rate Limit Exceeded Response

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 100 requests/hour exceeded",
    "retry_after": 3600,
    "reset_at": "2025-11-19T15:00:00Z"
  }
}
```

**HTTP 429 Response includes** `Retry-After` header:
```
Retry-After: 3600
```

---

## Webhooks

### Webhook Events

Subscribe to events to receive real-time notifications:

| Event | Trigger |
|-------|---------|
| `job.created` | Job created successfully |
| `job.completed` | Job reached DELIVER state |
| `job.blocked` | Job blocked by QC |
| `job.failed` | Job encountered error |
| `batch.completed` | All jobs in batch finished |

### Webhook Payload

**POST to your webhook URL**:
```json
{
  "event": "job.completed",
  "timestamp": "2025-11-19T14:32:15Z",
  "data": {
    "job_id": "job_xyz789",
    "status": "DELIVER",
    "article_url": "https://api.bacowr.com/v1/jobs/job_xyz789/article.html"
  },
  "signature": "sha256=abc123..."
}
```

### Webhook Signature Verification

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## API Changelog

### v1.0 (Current)

**Released**: 2025-11-19

**Features**:
- Jobs API (create, get, list, cancel)
- Batch API (create, get status)
- CMS export (WordPress)
- Analytics API (stats)
- JWT authentication
- Rate limiting
- Webhooks

**Breaking Changes**: None (initial release)

---

### Planned: v2.0 (Q2 2026)

**New Features**:
- GraphQL API endpoint
- Real-time job progress via WebSockets
- Bulk operations API
- Advanced filtering and search
- API versioning in headers (prefer over URL)
- OpenAPI 3.1 specification published

**Deprecations**:
- API Key authentication (JWT only)
- `/v1/` URL prefix (use header: `Accept-Version: v2`)

---

## Code Examples

### Python SDK

```python
import bacowr

# Using JWT token (recommended for v1.8+)
client = bacowr.Client(token="eyJhbGciOiJIUzI1NiIs...")

# Or using legacy API key (deprecated, for backward compatibility)
# client = bacowr.Client(api_key="sk_live_abc123")

# Create job
job = client.jobs.create(
    publisher_domain="aftonbladet.se",
    target_url="https://example.com/product",
    anchor_text="best project management tools"
)

print(f"Job created: {job.job_id}")

# Wait for completion
job.wait_for_completion(timeout=120)

if job.status == "DELIVER":
    print(f"Article: {job.article.content}")
    print(f"QC Score: {job.qc_report.score}")
else:
    print(f"Job blocked: {job.qc_report.issues}")
```

### JavaScript SDK

```javascript
import { BacowrClient } from 'bacowr-js';

// Using JWT token (recommended for v1.8+)
const client = new BacowrClient({ token: 'eyJhbGciOiJIUzI1NiIs...' });

// Or using legacy API key (deprecated, for backward compatibility)
// const client = new BacowrClient({ apiKey: 'sk_live_abc123' });

// Create job
const job = await client.jobs.create({
  publisherDomain: 'aftonbladet.se',
  targetUrl: 'https://example.com/product',
  anchorText: 'best project management tools'
});

console.log(`Job created: ${job.jobId}`);

// Poll for completion
const result = await job.waitForCompletion({ timeout: 120000 });

if (result.status === 'DELIVER') {
  console.log(`Article: ${result.article.content}`);
} else {
  console.error(`Job blocked: ${result.qcReport.issues}`);
}
```

### cURL

```bash
# Create job
curl -X POST https://api.bacowr.com/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://example.com/product",
    "anchor_text": "best project management tools"
  }'

# Get job status
curl https://api.bacowr.com/v1/jobs/job_xyz789 \
  -H "Authorization: Bearer $TOKEN"
```

---

## Best Practices

### 1. Error Handling

Always check `success` field and handle errors gracefully:

```python
response = client.jobs.create(...)
if not response.success:
    print(f"Error: {response.error.message}")
    if response.error.code == "VALIDATION_ERROR":
        # Handle validation error
    elif response.error.code == "RATE_LIMIT_EXCEEDED":
        # Wait and retry
```

### 2. Polling vs Webhooks

For real-time updates, use **webhooks** instead of polling:

```python
# ❌ Bad: Polling every 5 seconds
while job.status not in ["DELIVER", "BLOCKED", "ERROR"]:
    time.sleep(5)
    job.refresh()

# ✅ Good: Use webhooks
client.webhooks.subscribe("job.completed", my_webhook_url)
```

### 3. Batch Processing

Use batch API for multiple jobs (more efficient):

```python
# ❌ Bad: Sequential job creation
for job_data in jobs:
    client.jobs.create(**job_data)  # Slow, 175 API calls

# ✅ Good: Batch creation
client.batches.create(jobs=jobs)  # Fast, 1 API call
```

### 4. Idempotency

Use `idempotency_key` to safely retry job creation without creating duplicates:

```python
# First request - creates new job, returns 201
job = client.jobs.create(
    publisher_domain="example.com",
    target_url="https://target.com",
    anchor_text="test",
    idempotency_key="unique-request-id-12345"
)
# Returns: status=201, job_id="job_abc123"

# Retry same request (e.g., after network error)
# Returns existing job, not a duplicate
job = client.jobs.create(
    publisher_domain="example.com",
    target_url="https://target.com",
    anchor_text="test",
    idempotency_key="unique-request-id-12345"  # Same key
)
# Returns: status=200, job_id="job_abc123" (same job)
```

**Notes:**
- Idempotency keys expire after 24 hours
- Use unique keys per logical job (e.g., UUID, hash of inputs)
- Retries with same key return existing job, not 409 Conflict

---

## Support

**API Issues**: https://github.com/bacowr/bacowr/issues
**Documentation**: https://docs.bacowr.com
**Status Page**: https://status.bacowr.com

---

**Document Maintained By**: Module J (API Contract) & Module Q (Quality)
**Last Review**: 2025-11-19
**Next Review**: After v2.0 API release

*"An API is a user interface for developers."* — Unknown

This API reference provides the contract for interacting with BACOWR programmatically. For architecture details, see `docs/architecture/system_architecture.md`.
