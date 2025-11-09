# BACOWR Publisher Research & Analytics System

Advanced publisher performance tracking, insights generation, and smart recommendations for optimal backlink targeting.

---

## 📦 Overview

The Publisher Research System provides:
- **Performance Metrics**: Track success rates, quality scores, and costs per publisher
- **AI-Powered Insights**: Automated recommendations, warnings, and optimization suggestions
- **Publisher Comparison**: Compare multiple publishers side-by-side
- **Smart Recommendations**: Get publisher suggestions based on your criteria
- **Trend Analysis**: Monitor performance trends over time

---

## 🏗️ Architecture

### Database Models

**1. PublisherMetrics**
```python
PublisherMetrics(
    id: str,
    user_id: str,
    publisher_domain: str,

    # Job statistics
    total_jobs: int,
    successful_jobs: int,
    failed_jobs: int,
    pending_jobs: int,
    success_rate: float,  # 0-100

    # Quality metrics
    avg_qc_score: float,  # 0-100
    avg_issue_count: float,
    quality_trend: str,  # improving, stable, declining

    # Cost metrics
    total_cost_usd: float,
    avg_cost_per_job: float,
    cost_trend: str,  # increasing, stable, decreasing

    # Performance metrics
    avg_generation_time_seconds: float,
    avg_retry_count: float,

    # Provider analytics
    most_used_provider: str,  # anthropic, openai, google
    most_used_strategy: str,  # multi_stage, single_shot
    provider_distribution: dict,  # {"anthropic": 60, "openai": 40}

    # Recommendation
    recommendation_score: float,  # 0-100 (weighted composite score)
    recommendation_reason: str,  # Human-readable explanation

    # Timestamps
    first_job_at: datetime,
    last_job_at: datetime,
    last_updated_at: datetime,
    created_at: datetime
)
```

**2. PublisherInsight**
```python
PublisherInsight(
    id: str,
    user_id: str,
    publisher_domain: str,

    # Insight classification
    insight_type: str,  # recommendation, warning, success_pattern, failure_pattern, optimization
    priority: str,  # high, medium, low

    # Content
    title: str,
    description: str,
    action_items: List[str],  # Suggested actions

    # Supporting data
    confidence_score: float,  # 0-100
    sample_size: int,  # Number of jobs analyzed
    evidence: dict,  # Supporting statistics

    # Metadata
    is_active: bool,  # Can be dismissed
    is_automated: bool,  # AI-generated vs manual
    tags: List[str],

    # Timestamps
    created_at: datetime,
    updated_at: datetime,
    expires_at: datetime  # Auto-expire old insights
)
```

### Recommendation Score Calculation

The recommendation score (0-100) is a weighted composite:

**Formula:**
```python
score = (success_rate/100 * 40) +  # 40% weight
        (avg_qc_score/100 * 30) +   # 30% weight
        (cost_score * 20) +          # 20% weight
        (sample_size_score * 10)     # 10% weight
```

**Components:**
- **Success Rate** (40%): Percentage of delivered jobs
- **Quality Score** (30%): Average QC score (higher is better)
- **Cost Efficiency** (20%): Lower cost = higher score ($0.10 = 20 pts, $1.00 = 0 pts)
- **Sample Size Reliability** (10%): More jobs = more reliable (20+ jobs = 10 pts)

---

## 🚀 API Endpoints

### Publisher Metrics (`/api/v1/publishers/metrics`)

**GET /**
```bash
# List all publisher metrics
curl http://localhost:8000/api/v1/publishers/metrics \
  -H "Authorization: Bearer $TOKEN"

# Filter by minimum jobs
curl "http://localhost:8000/api/v1/publishers/metrics?min_jobs=5" \
  -H "Authorization: Bearer $TOKEN"

# Sort by different criteria
curl "http://localhost:8000/api/v1/publishers/metrics?sort_by=success_rate" \
  -H "Authorization: Bearer $TOKEN"
# Options: recommendation_score, success_rate, total_jobs

# Response:
[
  {
    "id": "metric-123",
    "user_id": "user-456",
    "publisher_domain": "forbes.com",
    "total_jobs": 25,
    "successful_jobs": 22,
    "failed_jobs": 2,
    "pending_jobs": 1,
    "success_rate": 88.0,
    "avg_qc_score": 87.5,
    "avg_issue_count": 1.2,
    "quality_trend": "stable",
    "total_cost_usd": 12.50,
    "avg_cost_per_job": 0.50,
    "cost_trend": "stable",
    "avg_generation_time_seconds": 45.3,
    "avg_retry_count": 0.2,
    "most_used_provider": "anthropic",
    "most_used_strategy": "expert",
    "provider_distribution": {"anthropic": 20, "openai": 5},
    "recommendation_score": 82.5,
    "recommendation_reason": "Excellent success rate, high quality content, cost-effective, reliable data (25 jobs)",
    "first_job_at": "2025-10-01T10:00:00Z",
    "last_job_at": "2025-11-09T15:30:00Z",
    "last_updated_at": "2025-11-09T20:00:00Z",
    "created_at": "2025-10-01T10:00:00Z"
  }
]
```

**GET /{publisher_domain}**
```bash
# Get metrics for specific publisher
curl http://localhost:8000/api/v1/publishers/metrics/forbes.com \
  -H "Authorization: Bearer $TOKEN"

# Force refresh (recalculate from jobs)
curl "http://localhost:8000/api/v1/publishers/metrics/forbes.com?refresh=true" \
  -H "Authorization: Bearer $TOKEN"
```

**POST /refresh**
```bash
# Refresh all publisher metrics (rate limited: 10/hour)
curl -X POST http://localhost:8000/api/v1/publishers/metrics/refresh \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "message": "Metrics refresh initiated",
  "publishers_updated": 12
}
```

### Publisher Comparison (`/api/v1/publishers/compare`)

**POST /**
```bash
# Compare 2-10 publishers
curl -X POST http://localhost:8000/api/v1/publishers/compare \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domains": ["forbes.com", "techcrunch.com", "huffpost.com"],
    "metrics": ["success_rate", "avg_qc_score", "avg_cost_per_job"]
  }'

# Response:
{
  "publishers": [
    {
      "publisher_domain": "forbes.com",
      "total_jobs": 25,
      "success_rate": 88.0,
      "avg_qc_score": 87.5,
      "avg_cost_per_job": 0.50,
      "recommendation_score": 82.5,
      "rank": 1
    },
    {
      "publisher_domain": "techcrunch.com",
      "total_jobs": 18,
      "success_rate": 72.2,
      "avg_qc_score": 80.1,
      "avg_cost_per_job": 0.35,
      "recommendation_score": 75.3,
      "rank": 2
    },
    {
      "publisher_domain": "huffpost.com",
      "total_jobs": 12,
      "success_rate": 58.3,
      "avg_qc_score": 65.0,
      "avg_cost_per_job": 0.45,
      "recommendation_score": 62.1,
      "rank": 3
    }
  ],
  "best_publisher": "forbes.com",
  "metrics_compared": ["success_rate", "avg_qc_score", "avg_cost_per_job"],
  "comparison_date": "2025-11-09T20:00:00Z"
}
```

### Publisher Recommendations (`/api/v1/publishers/recommendations`)

**POST /**
```bash
# Get balanced recommendations (default)
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 5,
    "min_jobs": 3,
    "criteria": "balanced"
  }'

# Cost-optimized recommendations
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "min_jobs": 5,
    "criteria": "cost_optimized"
  }'

# Quality-focused recommendations
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "limit": 10,
    "min_jobs": 5,
    "criteria": "quality_focused"
  }'

# Response:
{
  "recommendations": [
    {...},  # PublisherMetrics objects (sorted by criteria)
    {...},
    {...}
  ],
  "criteria": "balanced",
  "total_publishers_evaluated": 15
}
```

**Criteria Explanations:**
- **balanced**: Sorts by recommendation_score (weighted composite of all factors)
- **cost_optimized**: Prioritizes lowest cost/job, then success rate
- **quality_focused**: Prioritizes highest QC scores, then success rate

### Publisher Insights (`/api/v1/publishers/insights`)

**GET /**
```bash
# List all insights
curl http://localhost:8000/api/v1/publishers/insights \
  -H "Authorization: Bearer $TOKEN"

# Filter by publisher
curl "http://localhost:8000/api/v1/publishers/insights?publisher_domain=forbes.com" \
  -H "Authorization: Bearer $TOKEN"

# Filter by insight type
curl "http://localhost:8000/api/v1/publishers/insights?insight_type=warning" \
  -H "Authorization: Bearer $TOKEN"
# Types: recommendation, warning, success_pattern, failure_pattern, optimization

# Filter by priority
curl "http://localhost:8000/api/v1/publishers/insights?priority=high" \
  -H "Authorization: Bearer $TOKEN"
# Priorities: high, medium, low

# Include dismissed insights
curl "http://localhost:8000/api/v1/publishers/insights?active_only=false" \
  -H "Authorization: Bearer $TOKEN"

# Response:
[
  {
    "id": "insight-789",
    "user_id": "user-456",
    "publisher_domain": "forbes.com",
    "insight_type": "recommendation",
    "priority": "high",
    "title": "High-Quality Publisher: forbes.com",
    "description": "This publisher consistently produces high-quality content with an average QC score of 87.5/100. Recommended for important backlink opportunities.",
    "action_items": [
      "Prioritize this publisher for critical backlinks",
      "Current configuration (expert) works well",
      "Consider creating a template for this publisher"
    ],
    "confidence_score": 90.0,
    "sample_size": 25,
    "evidence": {
      "avg_qc_score": 87.5,
      "success_rate": 88.0,
      "total_jobs": 25
    },
    "is_active": true,
    "is_automated": true,
    "tags": ["quality", "recommendation"],
    "created_at": "2025-11-09T18:00:00Z",
    "updated_at": "2025-11-09T18:00:00Z",
    "expires_at": null
  }
]
```

**GET /{insight_id}**
```bash
# Get specific insight
curl http://localhost:8000/api/v1/publishers/insights/{insight_id} \
  -H "Authorization: Bearer $TOKEN"
```

**POST /**
```bash
# Create manual insight
curl -X POST http://localhost:8000/api/v1/publishers/insights \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "forbes.com",
    "insight_type": "recommendation",
    "priority": "medium",
    "title": "Custom Insight",
    "description": "Manual observation about this publisher",
    "action_items": ["Try X", "Test Y"],
    "confidence_score": 75.0,
    "sample_size": 10,
    "tags": ["custom"]
  }'
```

**PUT /{insight_id}**
```bash
# Dismiss insight
curl -X PUT http://localhost:8000/api/v1/publishers/insights/{insight_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_active": false
  }'

# Change priority
curl -X PUT http://localhost:8000/api/v1/publishers/insights/{insight_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "low"
  }'
```

**DELETE /{insight_id}**
```bash
# Delete insight
curl -X DELETE http://localhost:8000/api/v1/publishers/insights/{insight_id} \
  -H "Authorization: Bearer $TOKEN"
```

**POST /generate/{publisher_domain}**
```bash
# Generate AI-powered insights (rate limited: 20/hour)
curl -X POST http://localhost:8000/api/v1/publishers/insights/generate/forbes.com \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "message": "Generated 3 insights for forbes.com",
  "insights_created": 3,
  "publisher_domain": "forbes.com"
}
```

---

## 🤖 Automated Insight Generation

The system automatically generates insights based on publisher metrics. Here are the 5 automated insight patterns:

### 1. Low Success Rate Warning

**Trigger**: `total_jobs >= 5 AND success_rate < 50%`

**Example:**
```json
{
  "insight_type": "warning",
  "priority": "high",
  "title": "Low Success Rate for huffpost.com",
  "description": "Only 45.0% of jobs succeeded for this publisher. Out of 20 jobs, 11 failed. Consider reviewing job configurations or trying different approaches.",
  "action_items": [
    "Review failed job error messages",
    "Try different writing strategies",
    "Verify publisher domain requirements",
    "Consider using a different LLM provider"
  ],
  "confidence_score": 95.0,
  "sample_size": 20
}
```

### 2. High Quality Recommendation

**Trigger**: `total_jobs >= 5 AND avg_qc_score >= 85`

**Example:**
```json
{
  "insight_type": "recommendation",
  "priority": "high",
  "title": "High-Quality Publisher: forbes.com",
  "description": "This publisher consistently produces high-quality content with an average QC score of 87.5/100. Recommended for important backlink opportunities.",
  "action_items": [
    "Prioritize this publisher for critical backlinks",
    "Current configuration (expert) works well",
    "Consider creating a template for this publisher"
  ],
  "confidence_score": 90.0,
  "sample_size": 25
}
```

### 3. Cost Optimization Opportunity

**Trigger**: `total_jobs >= 5 AND avg_cost_per_job > 0.75`

**Example:**
```json
{
  "insight_type": "optimization",
  "priority": "medium",
  "title": "High Cost for techcrunch.com",
  "description": "Average cost per job is $0.85, which is above typical rates. Consider cost optimization strategies.",
  "action_items": [
    "Try different LLM providers (cost comparison)",
    "Use single-shot strategy instead of multi-stage",
    "Review if all features are necessary",
    "Compare with similar publishers"
  ],
  "confidence_score": 85.0,
  "sample_size": 18
}
```

### 4. Success Pattern

**Trigger**: `total_jobs >= 10 AND success_rate >= 85%`

**Example:**
```json
{
  "insight_type": "success_pattern",
  "priority": "medium",
  "title": "Reliable Publisher: forbes.com",
  "description": "Strong track record with 88.0% success rate across 25 jobs. Most successful with anthropic using expert strategy.",
  "action_items": [
    "Continue using current configuration",
    "Scale up jobs for this publisher",
    "Document what works for future reference"
  ],
  "confidence_score": 92.0,
  "sample_size": 25
}
```

### 5. Declining Quality Warning

**Trigger**: `quality_trend == "declining" AND total_jobs >= 10`

**Example:**
```json
{
  "insight_type": "warning",
  "priority": "medium",
  "title": "Declining Quality for huffpost.com",
  "description": "Quality scores have been declining recently. Current average: 65.0/100. Review recent changes or publisher guidelines updates.",
  "action_items": [
    "Compare recent jobs to earlier successful ones",
    "Check if publisher changed their requirements",
    "Review any configuration changes",
    "Consider reverting to previous successful settings"
  ],
  "confidence_score": 80.0,
  "sample_size": 15
}
```

---

## 🎯 Use Cases

### Use Case 1: Find Best Publishers

**Goal**: Identify top-performing publishers for scaling

```bash
# Get top 10 balanced recommendations
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "limit": 10,
    "min_jobs": 5,
    "criteria": "balanced"
  }'

# Review recommendations
# Top result: forbes.com (score: 82.5)
# - 88% success rate
# - 87.5 QC score
# - $0.50 per job
# - 25 jobs (reliable data)

# Decision: Scale up Forbes content generation
```

### Use Case 2: Cost Optimization

**Goal**: Find cheapest publishers without sacrificing quality

```bash
# Get cost-optimized recommendations
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "limit": 10,
    "min_jobs": 3,
    "criteria": "cost_optimized"
  }'

# Compare top 3
curl -X POST http://localhost:8000/api/v1/publishers/compare \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "publisher_domains": ["medium.com", "dev.to", "hashnode.com"],
    "metrics": ["avg_cost_per_job", "success_rate", "avg_qc_score"]
  }'

# Result: medium.com is cheapest ($0.25/job) with acceptable quality (75/100)
```

### Use Case 3: Troubleshoot Low Success Rate

**Goal**: Understand why a publisher is failing

```bash
# Get metrics for failing publisher
curl "http://localhost:8000/api/v1/publishers/metrics/huffpost.com?refresh=true" \
  -H "Authorization: Bearer $TOKEN"

# Result: 45% success rate, 11/20 failed

# Generate insights
curl -X POST http://localhost:8000/api/v1/publishers/insights/generate/huffpost.com \
  -H "Authorization: Bearer $TOKEN"

# Review automated insights
curl "http://localhost:8000/api/v1/publishers/insights?publisher_domain=huffpost.com&priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Insight suggests:
# - Review failed job error messages
# - Try different writing strategies
# - Verify publisher domain requirements

# Action: Review failed jobs, adjust strategy
```

### Use Case 4: Publisher Portfolio Analysis

**Goal**: Get overview of all publishers

```bash
# List all publishers sorted by recommendation score
curl "http://localhost:8000/api/v1/publishers/metrics?sort_by=recommendation_score&min_jobs=3" \
  -H "Authorization: Bearer $TOKEN"

# Result:
# 1. forbes.com (82.5) - excellent
# 2. techcrunch.com (75.3) - good
# 3. medium.com (72.1) - acceptable
# 4. huffpost.com (62.1) - needs improvement
# 5. buzzfeed.com (45.2) - avoid

# Get high-priority insights for portfolio
curl "http://localhost:8000/api/v1/publishers/insights?priority=high" \
  -H "Authorization: Bearer $TOKEN"

# Decision matrix:
# - Scale: forbes.com, techcrunch.com
# - Optimize: medium.com (reduce cost)
# - Fix: huffpost.com (improve success rate)
# - Pause: buzzfeed.com (too unreliable)
```

### Use Case 5: Quality-First Strategy

**Goal**: Only use publishers with QC scores > 80

```bash
# Get quality-focused recommendations
curl -X POST http://localhost:8000/api/v1/publishers/recommendations \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "limit": 20,
    "min_jobs": 5,
    "criteria": "quality_focused"
  }'

# Filter publishers with avg_qc_score >= 80
# Create campaign with these publishers only

# Monitor quality trends
curl "http://localhost:8000/api/v1/publishers/insights?insight_type=warning" \
  -H "Authorization: Bearer $TOKEN"

# Alert if any publisher shows "declining quality" trend
```

---

## 📊 Metrics Calculation Details

### How Metrics are Calculated

Metrics are calculated by aggregating job data:

**Success Rate:**
```python
success_rate = (successful_jobs / total_jobs) * 100
# successful_jobs = jobs with status="delivered"
# failed_jobs = jobs with status in ["blocked", "aborted"]
```

**Average QC Score:**
```python
avg_qc_score = sum(qc_scores) / len(qc_scores)
# Only from delivered jobs with qc_report.overall_score
```

**Average Cost:**
```python
avg_cost_per_job = sum(actual_costs) / len(actual_costs)
# Only from jobs with actual_cost set
```

**Trends:**
```python
def calculate_trend(current, previous):
    if previous is None:
        return "stable"
    change_pct = ((current - previous) / previous) * 100
    if abs(change_pct) < 5:
        return "stable"
    elif change_pct > 0:
        return "improving"  # For quality
    else:
        return "declining"
```

### When Metrics Update

Metrics are updated:
1. **Automatically**: When POST /metrics/refresh is called
2. **On-demand**: When GET /metrics/{domain}?refresh=true
3. **Manually**: Via update_publisher_metrics() service function

**Not updated automatically** on every job completion (performance reasons).

### Metrics Refresh Strategy

```bash
# Option 1: Refresh all (rate limited: 10/hour)
curl -X POST http://localhost:8000/api/v1/publishers/metrics/refresh \
  -H "Authorization: Bearer $TOKEN"

# Option 2: Refresh specific publisher
curl "http://localhost:8000/api/v1/publishers/metrics/forbes.com?refresh=true" \
  -H "Authorization: Bearer $TOKEN"

# Option 3: Background job (future enhancement)
# Set up cron job or scheduler to call refresh every 6 hours
```

---

## 🔍 Frontend Integration Examples

### Publisher Dashboard

```typescript
// Fetch all publisher metrics
const { data: publishers } = useQuery({
  queryKey: ['publishers', 'metrics'],
  queryFn: async () => {
    const response = await fetch('/api/v1/publishers/metrics?min_jobs=3&sort_by=recommendation_score')
    return response.json()
  }
})

// Display dashboard
<PublisherDashboard>
  {publishers.map(pub => (
    <PublisherCard key={pub.id}>
      <h3>{pub.publisher_domain}</h3>
      <ScoreBadge score={pub.recommendation_score} />
      <Stats>
        <Stat label="Success Rate" value={`${pub.success_rate}%`} />
        <Stat label="Quality" value={pub.avg_qc_score} />
        <Stat label="Cost/Job" value={`$${pub.avg_cost_per_job}`} />
        <Stat label="Jobs" value={pub.total_jobs} />
      </Stats>
      <TrendIndicators>
        <Trend type="quality" direction={pub.quality_trend} />
        <Trend type="cost" direction={pub.cost_trend} />
      </TrendIndicators>
    </PublisherCard>
  ))}
</PublisherDashboard>
```

### Publisher Comparison Tool

```typescript
// Compare selected publishers
const comparePublishers = async (domains: string[]) => {
  const response = await fetch('/api/v1/publishers/compare', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      publisher_domains: domains,
      metrics: ['success_rate', 'avg_qc_score', 'avg_cost_per_job']
    })
  })
  return response.json()
}

// Display comparison
<ComparisonTable>
  <thead>
    <tr>
      <th>Rank</th>
      <th>Publisher</th>
      <th>Success Rate</th>
      <th>Quality</th>
      <th>Cost/Job</th>
      <th>Score</th>
    </tr>
  </thead>
  <tbody>
    {comparison.publishers.map(pub => (
      <tr key={pub.publisher_domain}>
        <td><RankBadge rank={pub.rank} /></td>
        <td>{pub.publisher_domain}</td>
        <td>{pub.success_rate}%</td>
        <td>{pub.avg_qc_score}</td>
        <td>${pub.avg_cost_per_job}</td>
        <td><ScoreBadge score={pub.recommendation_score} /></td>
      </tr>
    ))}
  </tbody>
</ComparisonTable>
```

### Insights Panel

```typescript
// Fetch insights
const { data: insights } = useQuery({
  queryKey: ['publishers', 'insights', 'active'],
  queryFn: async () => {
    const response = await fetch('/api/v1/publishers/insights?active_only=true')
    return response.json()
  }
})

// Group by priority
const highPriority = insights?.filter(i => i.priority === 'high') || []
const mediumPriority = insights?.filter(i => i.priority === 'medium') || []

// Display
<InsightsPanel>
  <Section title="High Priority" count={highPriority.length}>
    {highPriority.map(insight => (
      <InsightCard key={insight.id} insight={insight} />
    ))}
  </Section>
  <Section title="Medium Priority" count={mediumPriority.length}>
    {mediumPriority.map(insight => (
      <InsightCard key={insight.id} insight={insight} />
    ))}
  </Section>
</InsightsPanel>

// Dismiss insight
const dismissInsight = async (insightId: string) => {
  await fetch(`/api/v1/publishers/insights/${insightId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ is_active: false })
  })
  queryClient.invalidateQueries(['publishers', 'insights'])
}
```

---

## 🛠️ Database Migrations

The publisher research system requires database migrations:

```bash
cd api

# Create migration
alembic revision --autogenerate -m "Add publisher research tables"

# Apply migration
alembic upgrade head
```

**Migration includes**:
- `publisher_metrics` table
- `publisher_insights` table
- Unique index on (user_id, publisher_domain) for metrics
- Indexes on recommendation_score, success_rate
- Indexes on insight_type, priority, is_active

---

## 📊 Rate Limiting

Publisher research endpoints have specific rate limits:

```python
RATE_LIMITS = {
    "list_jobs": "60/minute",       # List metrics, insights
    "get_job": "100/minute",        # Get single metric/insight
    "create_job": "30/minute",      # Create/update/delete
    "analytics": "60/minute",       # Compare, recommendations
    "refresh_metrics": "10/hour",   # Expensive: refresh all metrics
    "generate_insights": "20/hour", # AI-powered: generate insights
}
```

---

## 🔐 Security

**Authentication**: All endpoints require JWT authentication via `get_current_user`

**Authorization**: Users can only access their own:
- Publisher metrics
- Publisher insights

**Data Privacy**: Metrics are calculated per-user, never shared across users

---

## 🧪 Testing

### Manual Testing

```bash
# 1. Start backend
cd api
uvicorn app.main:socket_app --reload

# 2. Create some jobs first
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"publisher_domain": "forbes.com", ...}'

# 3. Refresh metrics
curl -X POST http://localhost:8000/api/v1/publishers/metrics/refresh \
  -H "Authorization: Bearer $TOKEN"

# 4. View metrics
curl http://localhost:8000/api/v1/publishers/metrics \
  -H "Authorization: Bearer $TOKEN"

# 5. Generate insights
curl -X POST http://localhost:8000/api/v1/publishers/insights/generate/forbes.com \
  -H "Authorization: Bearer $TOKEN"

# 6. View insights
curl http://localhost:8000/api/v1/publishers/insights \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🚦 Production Checklist

Before deploying:

- [ ] Run database migrations
- [ ] Test metrics calculation with real job data
- [ ] Verify recommendation score algorithm
- [ ] Test insight generation for all 5 patterns
- [ ] Configure rate limiting (Redis for distributed)
- [ ] Set up scheduled metrics refresh (cron job)
- [ ] Monitor metrics calculation performance
- [ ] Test with large datasets (1000+ jobs)
- [ ] Verify indexes are used in queries
- [ ] Add logging for metrics updates
- [ ] Test cascade deletes (user deletion)
- [ ] Verify trends calculation accuracy
- [ ] Test comparison with 10 publishers
- [ ] Add monitoring for insight generation failures

---

## 📝 Future Enhancements

1. **Automated Metrics Refresh**: Background task to update metrics every 6 hours
2. **Historical Trends**: Track metrics over time (monthly snapshots)
3. **Predictive Analytics**: ML model to predict job success before running
4. **Competitive Benchmarking**: Compare your performance to aggregated anonymous data
5. **Custom Scoring**: Let users define their own recommendation score weights
6. **Insight Notifications**: Email/webhook when high-priority insights are generated
7. **Publisher Discovery**: Suggest new publishers based on successful ones
8. **A/B Testing**: Track experiments (different strategies for same publisher)
9. **Cost Forecasting**: Predict monthly costs based on planned jobs
10. **Quality Alerts**: Real-time notifications when quality drops below threshold

---

## 🐛 Troubleshooting

**Issue**: Metrics showing 0 jobs
- Check: Are there completed jobs for this publisher?
- Solution: Run metrics refresh with `?refresh=true`

**Issue**: Recommendation score seems wrong
- Check: Review the score components (success_rate, avg_qc_score, avg_cost)
- Solution: Verify job data (qc_report, actual_cost are populated)

**Issue**: No insights generated
- Check: Does publisher have at least 3 jobs?
- Check: Are metrics up to date?
- Solution: Refresh metrics first, then generate insights

**Issue**: Trends showing "stable" when visually different
- Check: Trend calculation requires >5% change
- Solution: This is expected for small variations

**Issue**: Comparison failing
- Check: Are all publishers in the comparison request actually in metrics table?
- Solution: Refresh metrics for missing publishers

---

## 📚 Related Documentation

- **API Backend**: `API_BACKEND_COMPLETE.md`
- **Database Models**: `api/app/models/database.py`
- **Pydantic Schemas**: `api/app/models/schemas.py`
- **Metrics Service**: `api/app/services/publisher_metrics.py`
- **Rate Limiting**: `PRODUCTION_FEATURES.md`

---

**Created**: 2025-11-09
**Version**: 1.0.0
**Status**: ✅ Backend Complete (Frontend Pending)
