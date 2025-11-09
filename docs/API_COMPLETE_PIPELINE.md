# Complete Pipeline API Documentation

## Overview

The **Complete Pipeline** (`/jobs/create-complete`) endpoint provides a fully orchestrated backlink content generation system following the **Next-A1 specification**. This endpoint takes minimal input (3 parameters) and returns a complete, QC-validated article.

## Architecture

### Pipeline Flow

```
INPUT (3 params) → BacklinkJobOrchestrator
  ↓
1. Profile Target URL (page_profiler.py)
  ↓
2. Profile Publisher Domain (page_profiler.py)
  ↓
3. Classify Anchor Text (intent_analyzer.py)
  ↓
4. Generate SERP Queries (serp_researcher.py)
  ↓
5. Fetch SERP Data (serp_api.py → SerpAPI)
  ↓
6. Analyze Intent Alignment (intent_analyzer.py)
  ↓
7. Generate Content (writer_engine.py → LLM)
  ↓
8. Validate QC (qc_validator.py → 8 Next-A1 criteria)
  ↓
9. Package Results (BacklinkJobPackage format)
  ↓
OUTPUT → article_content + job_package + qc_report
```

### Components

**Core Services:**
- `job_orchestrator.py` - Orchestrates complete pipeline
- `writer_engine.py` - LLM content generation (Claude/GPT/Gemini)
- `serp_api.py` - Real SERP data integration (SerpAPI)
- `qc_validator.py` - Next-A1 QC validation (8 criteria)

**Existing Modules:**
- `page_profiler.py` - Target/publisher profiling
- `serp_researcher.py` - Query generation
- `intent_analyzer.py` - Intent alignment analysis

## API Endpoint

### POST `/api/v1/jobs/create-complete`

Create and execute a complete backlink content generation job.

**Authentication:** Required (Bearer token)

**Rate Limit:** 10 requests/hour per user

**Request Body:**

```json
{
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://example.com/casino-guide",
  "anchor_text": "bästa online casino",
  "llm_provider": "anthropic",
  "writing_strategy": "expert",
  "country": "se",
  "use_ahrefs": false,
  "enable_llm_profiling": true
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `publisher_domain` | string | Yes | Domain where content will be published |
| `target_url` | string | Yes | URL that will receive the backlink |
| `anchor_text` | string | Yes | Proposed anchor text for the link |
| `llm_provider` | string | No | LLM provider: "anthropic", "openai", "google", or "auto" (default: "auto") |
| `writing_strategy` | string | No | "expert" (default), "standard", "comprehensive" |
| `country` | string | No | Country code for SERP research (default: "se") |
| `use_ahrefs` | boolean | No | Use Ahrefs data (requires API key) (default: true) |
| `enable_llm_profiling` | boolean | No | Enable LLM-enhanced profiling (default: true) |

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "status": "PENDING",
  "publisher_domain": "aftonbladet.se",
  "target_url": "https://example.com/casino-guide",
  "anchor_text": "bästa online casino",
  "llm_provider": "anthropic",
  "writing_strategy": "expert",
  "country": "se",
  "estimated_cost": 0.06,
  "created_at": "2025-11-09T10:30:00Z",
  "started_at": null,
  "completed_at": null
}
```

**Job Status Values:**
- `PENDING` - Job queued, not yet started
- `PROCESSING` - Job is running
- `DELIVERED` - Content generated successfully (QC: PASS or WARNING)
- `BLOCKED` - Content failed QC validation (QC: BLOCKED)
- `ABORTED` - Job failed due to error

## Checking Job Status

### GET `/api/v1/jobs/{job_id}`

Get complete job details including article, QC report, and metrics.

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "DELIVERED",
  "article_text": "<!DOCTYPE html>...",
  "job_package": {
    "job_meta": {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-11-09T10:30:00Z",
      "spec_version": "Next-A1-SERP-First-v1"
    },
    "input_minimal": {
      "publisher_domain": "aftonbladet.se",
      "target_url": "https://example.com/casino-guide",
      "anchor_text": "bästa online casino"
    },
    "publisher_profile": { ... },
    "target_profile": { ... },
    "anchor_profile": { ... },
    "serp_research_extension": { ... },
    "intent_extension": {
      "serp_intent_primary": "commercial_research",
      "target_page_intent": "transactional",
      "recommended_bridge_type": "pivot",
      "intent_alignment": {
        "overall": "partial"
      }
    },
    "links_extension": {
      "bridge_type": "pivot",
      "anchor_swap": { ... },
      "placement": { ... }
    }
  },
  "qc_report": {
    "status": "PASS",
    "overall_score": 87.5,
    "scores": {
      "preflight": 100,
      "draft": 85,
      "anchor": 90,
      "trust": 80,
      "intent": 95,
      "lsi": 88,
      "fit": 82,
      "compliance": 100
    },
    "results": {
      "preflight": {
        "status": "PASS",
        "issues": []
      },
      ...
    },
    "issues": [
      {
        "criterion": "draft",
        "severity": "warning",
        "message": "Subtopic coverage 65% (target: 70%)"
      }
    ],
    "recommendations": [
      "Consider adding more LSI terms in near-window",
      "Expand coverage of required subtopics"
    ]
  },
  "metrics": {
    "profiling": {
      "target_profiling_time": 2.3,
      "publisher_profiling_time": 1.8
    },
    "generation": {
      "provider": "anthropic",
      "strategy": "expert",
      "duration_seconds": 8.5
    },
    "qc": {
      "validation_time": 0.8
    }
  },
  "actual_cost": 0.058,
  "created_at": "2025-11-09T10:30:00Z",
  "started_at": "2025-11-09T10:30:05Z",
  "completed_at": "2025-11-09T10:30:25Z"
}
```

## WebSocket Real-time Updates

Connect to WebSocket for real-time job progress:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === 'job_update') {
    console.log(`Job ${data.job_id}: ${data.message} (${data.progress}%)`);
  }

  if (data.type === 'job_completed') {
    console.log(`Job ${data.job_id} completed!`);
  }

  if (data.type === 'job_error') {
    console.error(`Job ${data.job_id} failed: ${data.error}`);
  }
};
```

**Progress Updates:**
- 10% - Job started, profiling target and publisher
- 15% - Profiling complete
- 30% - SERP research complete
- 45% - Intent analysis complete
- 60% - Content generation started
- 85% - QC validation running
- 100% - Job complete

## Next-A1 QC Criteria

The pipeline validates content against 8 QC criteria:

1. **Preflight** - Bridge type matches intent alignment
2. **Draft** - Word count ≥900, ≥2 H2 sections, ≥60% subtopic coverage
3. **Anchor** - NOT in H1/H2 headers, risk assessment
4. **Trust** - T1-T4 source quality validation
5. **Intent** - No 'off' alignments in intent_extension
6. **LSI** - 6-10 LSI terms in near-window (±2 sentences)
7. **Fit** - Readability (LIX 35-45), tone matching
8. **Compliance** - Auto-detect required disclaimers (gambling, finance, health, crypto)

**Scoring:**
- Each criterion scored 0-100
- Overall score is weighted average
- **PASS**: ≥80 overall, all critical criteria pass
- **WARNING**: 50-79 overall, some issues present
- **BLOCKED**: <50 overall or critical failure

## Bridge Types

The system automatically selects bridge type based on intent alignment:

### Strong Bridge
- **When**: All intents aligned
- **Strategy**: Direct, natural connection
- **Link Placement**: Early in first relevant H2 section
- **Trust Requirements**: 1 standard source (T1/T2/T3)

### Pivot Bridge
- **When**: Partial alignment (e.g., info publisher → commercial target)
- **Strategy**: Informational bridge connecting themes
- **Link Placement**: Middle sections after pivot established
- **Trust Requirements**: 1-2 sources supporting pivot angle

### Wrapper Bridge
- **When**: Weak connection, overall alignment 'off'
- **Strategy**: Meta-framework (methodology, risk, innovation, comparison)
- **Link Placement**: Late, after extensive context wrapping
- **Trust Requirements**: 2-3 sources, triangulation pattern

## Cost Estimates

**Per-job costs (approximate):**

| Provider | Strategy | Cost |
|----------|----------|------|
| Anthropic Claude | expert | $0.06 |
| Anthropic Claude | standard | $0.04 |
| OpenAI GPT-4 | expert | $0.09 |
| OpenAI GPT-4 | standard | $0.05 |
| Google Gemini | expert | $0.03 |
| Google Gemini | standard | $0.02 |

**Additional costs:**
- SERP API (SerpAPI): ~$0.005 per query (1 main + 2-3 cluster = ~$0.02)
- Ahrefs API (optional): ~$0.10 per request

## Error Handling

**Common Errors:**

| Status Code | Error | Solution |
|------------|-------|----------|
| 400 | Invalid input | Check required parameters |
| 401 | Unauthorized | Provide valid authentication token |
| 429 | Rate limit exceeded | Wait or upgrade plan |
| 503 | SERP API not configured | Set SERPAPI_KEY environment variable |
| 500 | Internal error | Check logs, retry request |

**Job Failures:**

If job status is `ABORTED`, check `error_message` field:
- "Target URL returned HTTP 404" - Target page not found
- "SERP API failed" - SERP API error (check API key)
- "Content generation failed" - LLM error (check API key)
- "QC validation failed" - Content didn't meet Next-A1 criteria

## Example: Complete Workflow

### 1. Create Job

```bash
curl -X POST https://api.bacowr.com/api/v1/jobs/create-complete \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "svd.se",
    "target_url": "https://example.com/guide",
    "anchor_text": "läs mer här",
    "llm_provider": "anthropic",
    "writing_strategy": "expert"
  }'
```

### 2. Get Job Status

```bash
curl https://api.bacowr.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. Download Article

```bash
curl https://api.bacowr.com/api/v1/jobs/550e8400-e29b-41d4-a716-446655440000/article \
  -H "Authorization: Bearer YOUR_TOKEN" \
  > article.html
```

## Testing

**Requirements:**
- Valid API authentication token
- SERPAPI_KEY environment variable (for real SERP data)
- LLM API key (ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY)

**Test Command:**

```bash
# Set environment variables
export SERPAPI_KEY="your_serpapi_key"
export ANTHROPIC_API_KEY="your_anthropic_key"

# Start API server
cd /home/user/BACOWR
python -m uvicorn api.app.main:app --reload

# Create test job
curl -X POST http://localhost:8000/api/v1/jobs/create-complete \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "svd.se",
    "target_url": "https://www.regeringen.se/regeringens-politik/skolpolitik/",
    "anchor_text": "utbildningssystemet",
    "llm_provider": "anthropic",
    "writing_strategy": "expert"
  }'
```

## Environment Variables

Required environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/bacowr

# Authentication
JWT_SECRET_KEY=your_secret_key

# LLM Providers (at least one required)
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# SERP Research (required for complete pipeline)
SERPAPI_KEY=...

# Optional
AHREFS_API_KEY=...
```

## Comparison: Complete Pipeline vs Legacy

| Feature | Legacy (`/jobs`) | Complete Pipeline (`/jobs/create-complete`) |
|---------|------------------|---------------------------------------------|
| SERP Research | Mock/optional | Real (SerpAPI) required |
| Intent Analysis | Basic | Full Next-A1 intent_extension |
| Bridge Type | Manual | Automatic (strong/pivot/wrapper) |
| QC Validation | Post-generation | Integrated 8-criteria |
| Output Format | Markdown | HTML + BacklinkJobPackage |
| Schema Compliance | Partial | Full Next-A1 |
| Cost | Lower | Higher (SERP + LLM) |
| Quality | Good | Next-A1 certified |

## Next Steps

1. **Test the endpoint** with real inputs
2. **Monitor QC scores** to validate quality
3. **Adjust parameters** (writing_strategy, bridge_type) based on results
4. **Scale production** once validated

## Support

For issues or questions:
- Check logs: `tail -f api/logs/bacowr.log`
- Review QC report for content issues
- Verify environment variables are set
- Contact: support@bacowr.com
