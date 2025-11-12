# BACOWR API Guide

**Complete REST API for BACOWR Content Generation System**

Version: 1.0.0
Base URL: `http://localhost:8000` (development) | `https://api.bacowr.com` (production)

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Endpoints](#endpoints)
   - [Jobs](#jobs)
   - [Backlinks](#backlinks)
   - [Analytics](#analytics)
   - [Users](#users-admin)
   - [WebSocket](#websocket)
4. [Error Handling](#error-handling)
5. [Rate Limiting](#rate-limiting)
6. [Examples](#examples)
7. [Deployment](#deployment)

---

## Overview

The BACOWR API provides programmatic access to the backlink content generation engine. It supports:

- **Job Management**: Create and monitor content generation jobs
- **Backlink Tracking**: Store and analyze historical backlinks
- **Analytics**: Cost estimation, success rates, and performance metrics
- **Real-time Updates**: WebSocket support for job progress
- **Multi-User**: User management with API key authentication

### Base URLs

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`
- **API Prefix**: `/api/v1`

### API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Authentication

BACOWR uses **API Key authentication** via headers.

### Getting Your API Key

1. Start the API server
2. Check the startup logs for the default admin API key:

```
======================================================================
DEFAULT ADMIN USER CREATED
======================================================================
Email:   admin@bacowr.local
API Key: bacowr_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
======================================================================
⚠️  SAVE THIS API KEY - IT WON'T BE SHOWN AGAIN!
======================================================================
```

### Using API Key

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: bacowr_your_api_key_here" \
     http://localhost:8000/api/v1/jobs
```

### Authentication Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | API key required | No API key provided |
| 401 | Invalid API key | API key not found or invalid |
| 403 | User account is inactive | User has been deactivated |
| 403 | Admin privileges required | Endpoint requires admin access |

---

## Endpoints

### Health Check

**GET** `/health`

Check API health status (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "service": "bacowr-api",
  "version": "1.0.0"
}
```

---

## Jobs

Manage content generation jobs.

### Create Job

**POST** `/api/v1/jobs`

Create a new content generation job. The job will be processed asynchronously in the background.

**Request Body:**
```json
{
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
  "anchor_text": "läs mer om AI",
  "llm_provider": "anthropic",
  "writing_strategy": "multi_stage",
  "country": "se",
  "use_ahrefs": true,
  "enable_llm_profiling": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `publisher_domain` | string | Yes | Publisher domain (no protocol) |
| `target_url` | string | Yes | Target URL with protocol |
| `anchor_text` | string | Yes | Anchor text for the link |
| `llm_provider` | string | No | LLM provider: `auto`, `anthropic`, `openai`, `google` (default: `auto`) |
| `writing_strategy` | string | No | Strategy: `multi_stage`, `single_shot` (default: `multi_stage`) |
| `country` | string | No | Country code for SERP (default: `se`) |
| `use_ahrefs` | boolean | No | Use Ahrefs SERP data (default: `true`) |
| `enable_llm_profiling` | boolean | No | Enable LLM-enhanced profiling (default: `true`) |

**Response:** `201 Created`
```json
{
  "id": "job_uuid",
  "user_id": "user_uuid",
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
  "anchor_text": "läs mer om AI",
  "llm_provider": "anthropic",
  "writing_strategy": "multi_stage",
  "country": "se",
  "status": "pending",
  "estimated_cost": 0.06,
  "actual_cost": null,
  "created_at": "2025-11-12T10:30:00Z",
  "started_at": null,
  "completed_at": null,
  "error_message": null
}
```

---

### List Jobs

**GET** `/api/v1/jobs`

List all jobs for the current user with pagination.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page (max: 100) |
| `status` | string | - | Filter by status: `pending`, `processing`, `delivered`, `blocked`, `aborted` |

**Example:**
```bash
GET /api/v1/jobs?page=1&page_size=20&status=delivered
```

**Response:** `200 OK`
```json
{
  "items": [
    {
      "id": "job_uuid",
      "publisher_domain": "aftonbladet.se",
      "status": "delivered",
      "created_at": "2025-11-12T10:30:00Z",
      ...
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 20,
  "total_pages": 3
}
```

---

### Get Job Details

**GET** `/api/v1/jobs/{job_id}`

Get detailed information about a specific job, including article, QC report, and execution log.

**Response:** `200 OK`
```json
{
  "id": "job_uuid",
  "user_id": "user_uuid",
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://target.com",
  "anchor_text": "anchor text",
  "status": "delivered",
  "article_text": "# Article Title\n\nArticle content...",
  "job_package": { /* Complete BacklinkJobPackage */ },
  "qc_report": {
    "status": "PASS",
    "overall_score": 9.5,
    "issues": [],
    ...
  },
  "execution_log": {
    "metadata": { /* State machine transitions */ },
    "log_entries": [...]
  },
  "metrics": {
    "generation": {
      "provider": "anthropic",
      "model": "claude-3-haiku-20240307",
      "duration_seconds": 32.5
    }
  },
  "estimated_cost": 0.06,
  "actual_cost": 0.058,
  "created_at": "2025-11-12T10:30:00Z",
  "completed_at": "2025-11-12T10:30:45Z"
}
```

---

### Get Job Article

**GET** `/api/v1/jobs/{job_id}/article`

Get only the article text for a job (Markdown format).

**Response:** `200 OK`
```json
{
  "job_id": "job_uuid",
  "article": "# Article Title\n\nArticle content...",
  "created_at": "2025-11-12T10:30:45Z"
}
```

---

### Delete Job

**DELETE** `/api/v1/jobs/{job_id}`

Delete a job. Only pending or completed jobs can be deleted.

**Response:** `204 No Content`

---

## Backlinks

Track and analyze historical backlinks.

### Create Backlink

**POST** `/api/v1/backlinks`

Add a new backlink to your tracking database.

**Request Body:**
```json
{
  "publisher_domain": "aftonbladet.se",
  "publisher_url": "https://aftonbladet.se/article/12345",
  "target_url": "https://client.com/product",
  "anchor_text": "best product",
  "domain_authority": 85,
  "page_authority": 72,
  "traffic_estimate": 50000,
  "category": "news",
  "language": "sv",
  "notes": "Published on 2025-11-10",
  "tags": ["news", "product"],
  "published_at": "2025-11-10T12:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "id": "backlink_uuid",
  "user_id": "user_uuid",
  "publisher_domain": "aftonbladet.se",
  ...
}
```

---

### Bulk Import Backlinks

**POST** `/api/v1/backlinks/bulk`

Import multiple backlinks at once (max 1000 per request).

**Request Body:**
```json
{
  "backlinks": [
    {
      "publisher_domain": "site1.com",
      "target_url": "https://target.com/page1",
      "anchor_text": "anchor 1"
    },
    {
      "publisher_domain": "site2.com",
      "target_url": "https://target.com/page2",
      "anchor_text": "anchor 2"
    }
  ]
}
```

**Response:** `201 Created`
```json
{
  "imported_count": 2,
  "message": "Successfully imported 2 backlinks"
}
```

---

### List Backlinks

**GET** `/api/v1/backlinks`

List backlinks with filtering and pagination.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number |
| `page_size` | integer | Items per page |
| `publisher_domain` | string | Filter by publisher |
| `category` | string | Filter by category |
| `language` | string | Filter by language |
| `search` | string | Search in anchor, domain, or URL |

**Example:**
```bash
GET /api/v1/backlinks?category=news&language=sv&page=1
```

---

### Get Backlink Statistics

**GET** `/api/v1/backlinks/stats`

Get aggregated statistics about your backlinks.

**Response:** `200 OK`
```json
{
  "total_count": 150,
  "by_publisher": {
    "aftonbladet.se": 45,
    "svd.se": 32,
    "dn.se": 28
  },
  "by_category": {
    "news": 80,
    "technology": 50,
    "business": 20
  },
  "by_language": {
    "sv": 120,
    "en": 30
  },
  "avg_domain_authority": 68.5,
  "avg_page_authority": 54.2,
  "total_traffic_estimate": 2500000
}
```

---

### Delete Backlink

**DELETE** `/api/v1/backlinks/{backlink_id}`

Delete a backlink record.

**Response:** `204 No Content`

---

## Analytics

### Estimate Cost

**POST** `/api/v1/analytics/cost/estimate`

Estimate cost for content generation jobs.

**Request Body:**
```json
{
  "llm_provider": "anthropic",
  "writing_strategy": "multi_stage",
  "num_jobs": 100
}
```

**Response:** `200 OK`
```json
{
  "num_jobs": 100,
  "provider": "anthropic",
  "strategy": "multi_stage",
  "estimated_cost_per_job": 0.06,
  "estimated_total_cost": 6.00,
  "estimated_time_seconds": 3000
}
```

---

### Get Analytics

**GET** `/api/v1/analytics`

Get usage analytics for your account.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `days` | integer | 30 | Number of days to include |

**Response:** `200 OK`
```json
{
  "total_jobs": 125,
  "jobs_by_status": {
    "delivered": 110,
    "blocked": 10,
    "aborted": 5
  },
  "jobs_by_provider": {
    "anthropic": 100,
    "openai": 25
  },
  "jobs_by_strategy": {
    "multi_stage": 100,
    "single_shot": 25
  },
  "total_cost": 7.50,
  "avg_generation_time": 32.5,
  "success_rate": 88.0,
  "period_start": "2025-10-13T00:00:00Z",
  "period_end": "2025-11-12T10:30:00Z"
}
```

---

### Get Available Providers

**GET** `/api/v1/analytics/providers`

Get information about available LLM providers and strategies.

**Response:** `200 OK`
```json
{
  "providers": [
    {
      "id": "anthropic",
      "name": "Anthropic Claude",
      "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
      "default_model": "claude-3-haiku-20240307",
      "tested": true,
      "available": true
    },
    ...
  ],
  "strategies": [
    {
      "id": "multi_stage",
      "name": "Multi-Stage",
      "description": "Best quality - 3 LLM calls",
      "estimated_time": "30-60 seconds",
      "recommended": true
    },
    ...
  ]
}
```

---

## Users (Admin)

User management endpoints (requires admin privileges).

### List Users

**GET** `/api/v1/users`

List all users (admin only).

**Response:** `200 OK`
```json
[
  {
    "id": "user_uuid",
    "email": "user@example.com",
    "api_key": "bacowr_xxx",
    "is_active": true,
    "is_admin": false,
    "created_at": "2025-11-01T00:00:00Z"
  }
]
```

---

### Create User

**POST** `/api/v1/users`

Create a new user (admin only).

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "optional_password"
}
```

**Response:** `201 Created`

---

### Get Current User

**GET** `/api/v1/users/me`

Get information about the current user.

---

### Activate/Deactivate User

**PATCH** `/api/v1/users/{user_id}/activate`
**PATCH** `/api/v1/users/{user_id}/deactivate`

Enable or disable a user account (admin only).

---

### Regenerate API Key

**POST** `/api/v1/users/{user_id}/regenerate-api-key`

Generate a new API key for a user (admin only).

**Warning:** This invalidates the old API key.

---

### Delete User

**DELETE** `/api/v1/users/{user_id}`

Delete a user and all associated data (admin only).

---

## WebSocket

Real-time job progress updates via WebSocket.

### Connect to Job

**WebSocket** `/api/v1/ws/jobs/{job_id}?api_key=your_api_key`

Connect to receive real-time progress updates for a job.

**JavaScript Example:**
```javascript
const jobId = "job_uuid";
const apiKey = "bacowr_your_api_key";

const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/jobs/${jobId}?api_key=${apiKey}`);

ws.onopen = () => {
  console.log("Connected to job progress updates");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`[${data.status}] ${data.progress}% - ${data.message}`);

  if (data.status === "delivered") {
    console.log("Job completed successfully!");
    ws.close();
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from job updates");
};

// Keep connection alive
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send("ping");
  }
}, 30000);
```

**Message Format:**
```json
{
  "job_id": "job_uuid",
  "status": "processing",
  "progress": 45.5,
  "message": "Generating article content...",
  "timestamp": "2025-11-12T10:30:15Z"
}
```

**Progress Stages:**
- `0%` - Job created
- `10%` - Starting content generation
- `50%` - Processing (during generation)
- `100%` - Completed (delivered/blocked/aborted)

---

## Error Handling

### Error Response Format

All errors return JSON with `detail` field:

```json
{
  "detail": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 204 | No Content | Successful deletion |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Common Errors

**Validation Error (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "publisher_domain"],
      "msg": "Publisher domain should not include protocol",
      "type": "value_error"
    }
  ]
}
```

**Not Found (404):**
```json
{
  "detail": "Job not found"
}
```

---

## Rate Limiting

Currently, no rate limiting is enforced. Best practices:

- **Batch jobs** instead of making individual requests
- **Monitor costs** before running large batches
- **Use webhooks or WebSocket** instead of polling

---

## Examples

### Complete Job Flow

```bash
#!/bin/bash

API_KEY="bacowr_your_api_key_here"
BASE_URL="http://localhost:8000/api/v1"

# 1. Create job
JOB_RESPONSE=$(curl -s -X POST "$BASE_URL/jobs" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
    "anchor_text": "läs mer om AI",
    "llm_provider": "anthropic",
    "writing_strategy": "multi_stage"
  }')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.id')
echo "Created job: $JOB_ID"

# 2. Poll for completion
while true; do
  STATUS=$(curl -s "$BASE_URL/jobs/$JOB_ID" \
    -H "X-API-Key: $API_KEY" | jq -r '.status')

  echo "Status: $STATUS"

  if [[ "$STATUS" == "delivered" ]] || [[ "$STATUS" == "blocked" ]] || [[ "$STATUS" == "aborted" ]]; then
    break
  fi

  sleep 5
done

# 3. Get article
curl -s "$BASE_URL/jobs/$JOB_ID/article" \
  -H "X-API-Key: $API_KEY" | jq -r '.article' > article.md

echo "Article saved to article.md"

# 4. Save backlink
curl -s -X POST "$BASE_URL/backlinks" \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
    "anchor_text": "läs mer om AI",
    "category": "technology",
    "language": "sv"
  }'

echo "Backlink saved"
```

### Python Example

```python
import requests
import time

API_KEY = "bacowr_your_api_key"
BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {"X-API-Key": API_KEY}

# Create job
job_data = {
    "publisher_domain": "aftonbladet.se",
    "target_url": "https://sv.wikipedia.org/wiki/Artificiell_intelligens",
    "anchor_text": "läs mer om AI",
    "llm_provider": "anthropic",
    "writing_strategy": "multi_stage"
}

response = requests.post(f"{BASE_URL}/jobs", json=job_data, headers=HEADERS)
job = response.json()
job_id = job["id"]

print(f"Created job: {job_id}")

# Poll for completion
while True:
    response = requests.get(f"{BASE_URL}/jobs/{job_id}", headers=HEADERS)
    job = response.json()
    status = job["status"]

    print(f"Status: {status}")

    if status in ["delivered", "blocked", "aborted"]:
        break

    time.sleep(5)

# Get article
response = requests.get(f"{BASE_URL}/jobs/{job_id}/article", headers=HEADERS)
article = response.json()["article"]

with open("article.md", "w") as f:
    f.write(article)

print("Article saved to article.md")

# Get analytics
response = requests.get(f"{BASE_URL}/analytics", headers=HEADERS)
analytics = response.json()
print(f"\nTotal jobs: {analytics['total_jobs']}")
print(f"Total cost: ${analytics['total_cost']:.2f}")
print(f"Success rate: {analytics['success_rate']:.1f}%")
```

---

## Deployment

### Docker Deployment

```bash
# 1. Set environment variables
export ANTHROPIC_API_KEY="your_key"
export DATABASE_URL="postgresql://user:pass@localhost:5432/bacowr"

# 2. Build and run
docker-compose up -d

# 3. Check logs
docker-compose logs -f api

# 4. Access API
curl http://localhost:8000/health
```

### Production Checklist

- [ ] Set all required API keys in environment
- [ ] Use PostgreSQL (not SQLite) for production
- [ ] Configure CORS for your frontend domain
- [ ] Enable HTTPS (reverse proxy with nginx/traefik)
- [ ] Set up backup for database
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerts
- [ ] Document API key distribution process
- [ ] Set rate limiting if needed

### Environment Variables

Required:
```bash
# At least one LLM provider
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-proj-xxx
GOOGLE_API_KEY=xxx

# Database
DATABASE_URL=postgresql://user:pass@host:5432/bacowr
```

Optional:
```bash
# SERP Research
AHREFS_API_KEY=xxx

# Application
LOG_LEVEL=INFO
OUTPUT_DIR=storage/output
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_STRATEGY=multi_stage

# Frontend CORS
FRONTEND_URL=https://your-frontend.com
```

---

## Support

- **Documentation**: [README.md](README.md)
- **Production Guide**: [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)
- **Batch Processing**: [BATCH_GUIDE.md](BATCH_GUIDE.md)
- **Issues**: https://github.com/robwestz/BACOWR/issues

---

**Version**: 1.0.0
**Last Updated**: 2025-11-12
**Status**: Production Ready
