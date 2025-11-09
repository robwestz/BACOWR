# Analytics Dashboard Guide

## Overview

BACOWR provides comprehensive analytics for tracking job performance, costs, success rates, and system-wide metrics. The analytics system offers real-time insights into your content generation workflow with detailed breakdowns and export capabilities.

---

## Quick Start

```bash
# Get overall analytics for last 30 days
curl -X GET http://localhost:8000/api/v1/analytics?days=30 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Get cost breakdown
curl -X GET http://localhost:8000/api/v1/analytics/cost-breakdown \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Export as CSV
curl -X GET http://localhost:8000/api/v1/analytics/export/csv \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o jobs_export.csv
```

---

## Analytics Endpoints

### GET /api/v1/analytics

Get comprehensive analytics overview.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "total_jobs": 150,
  "jobs_by_status": {
    "delivered": 120,
    "blocked": 20,
    "aborted": 10
  },
  "jobs_by_provider": {
    "anthropic": 100,
    "openai": 50
  },
  "jobs_by_strategy": {
    "multi_stage": 120,
    "single_shot": 30
  },
  "total_cost": 45.50,
  "avg_generation_time": 38.5,
  "success_rate": 80.0,
  "period_start": "2025-10-10T00:00:00Z",
  "period_end": "2025-11-09T00:00:00Z"
}
```

**Metrics Included:**
- **total_jobs**: Total number of jobs created
- **jobs_by_status**: Breakdown by PENDING, PROCESSING, DELIVERED, BLOCKED, ABORTED
- **jobs_by_provider**: Usage per LLM provider
- **jobs_by_strategy**: multi_stage vs single_shot
- **total_cost**: Total spending in USD
- **avg_generation_time**: Average seconds per job
- **success_rate**: Percentage of jobs that delivered successfully

---

### GET /api/v1/analytics/cost-breakdown

Detailed cost analysis by provider and strategy.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "total_cost": 45.50,
  "cost_by_provider": {
    "anthropic": {
      "total_cost": 30.00,
      "avg_cost_per_job": 0.30,
      "job_count": 100
    },
    "openai": {
      "total_cost": 15.50,
      "avg_cost_per_job": 0.31,
      "job_count": 50
    }
  },
  "cost_by_strategy": {
    "multi_stage": {
      "total_cost": 38.40,
      "avg_cost_per_job": 0.32,
      "job_count": 120
    },
    "single_shot": {
      "total_cost": 7.10,
      "avg_cost_per_job": 0.24,
      "job_count": 30
    }
  },
  "most_expensive_jobs": [
    {
      "job_id": "550e8400-e29b-41d4-a716-446655440000",
      "cost": 0.85,
      "provider": "anthropic",
      "strategy": "multi_stage",
      "created_at": "2025-11-08T12:00:00Z",
      "status": "delivered"
    }
  ],
  "period_days": 30
}
```

**Use Cases:**
- Compare provider costs
- Identify expensive jobs
- Optimize strategy selection
- Budget planning

---

### GET /api/v1/analytics/performance

Performance metrics and quality analysis.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "generation_time_by_provider": {
    "anthropic": {
      "avg_seconds": 35.2,
      "min_seconds": 18.5,
      "max_seconds": 65.3,
      "sample_count": 100
    },
    "openai": {
      "avg_seconds": 42.1,
      "min_seconds": 22.0,
      "max_seconds": 78.9,
      "sample_count": 50
    }
  },
  "qc_metrics": {
    "total_jobs": 150,
    "delivered_jobs": 120,
    "delivery_rate": 80.0,
    "avg_qc_score": 85.5,
    "avg_issue_count": 1.2
  },
  "qc_status_breakdown": {
    "PASS": 90,
    "PASS_WITH_AUTOFIX": 30,
    "BLOCKED": 20
  },
  "period_days": 30
}
```

**Metrics Explained:**
- **generation_time_by_provider**: Speed comparison across providers
- **qc_metrics**: Quality control statistics
- **delivery_rate**: Percentage of jobs that passed QC
- **avg_qc_score**: Average quality score (0-100)
- **qc_status_breakdown**: Distribution of QC outcomes

---

### GET /api/v1/analytics/time-series

Time-series data for charts and trends.

**Query Parameters:**
- `days` - Number of days to include (default: 30)
- `interval` - Grouping interval: "day", "week", or "month" (default: "day")

**Response:**
```json
{
  "interval": "day",
  "period_days": 30,
  "data": [
    {
      "date": "2025-11-01T00:00:00Z",
      "job_count": 5,
      "cost": 1.50,
      "delivered_count": 4,
      "success_rate": 80.0
    },
    {
      "date": "2025-11-02T00:00:00Z",
      "job_count": 8,
      "cost": 2.40,
      "delivered_count": 7,
      "success_rate": 87.5
    }
  ]
}
```

**Visualization Use Cases:**
- Line charts for job volume over time
- Cost trend analysis
- Success rate tracking
- Identify peak usage periods

**Example with Chart.js:**
```javascript
const response = await fetch('/api/v1/analytics/time-series?days=30&interval=day');
const { data } = await response.json();

const chartData = {
  labels: data.map(d => d.date),
  datasets: [{
    label: 'Jobs per Day',
    data: data.map(d => d.job_count)
  }, {
    label: 'Cost per Day ($)',
    data: data.map(d => d.cost)
  }]
};
```

---

### GET /api/v1/analytics/export/csv

Export jobs as CSV file.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
- Content-Type: `text/csv`
- Filename: `bacowr_jobs_YYYYMMDD.csv`

**CSV Columns:**
- Job ID
- Created At
- Status
- Publisher
- Target URL
- Anchor Text
- Provider
- Strategy
- Estimated Cost
- Actual Cost
- Started At
- Completed At

**Example:**
```bash
# Download CSV
curl -X GET "http://localhost:8000/api/v1/analytics/export/csv?days=30" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o jobs_export.csv

# Open in Excel/Sheets
open jobs_export.csv
```

**Use Cases:**
- Import into Excel for custom analysis
- Share data with team members
- Archive historical records
- Create custom reports

---

### GET /api/v1/analytics/export/json

Export jobs as JSON file.

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
- Content-Type: `application/json`
- Filename: `bacowr_jobs_YYYYMMDD.json`

**Example:**
```bash
# Download JSON
curl -X GET "http://localhost:8000/api/v1/analytics/export/json?days=30" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o jobs_export.json

# Process with jq
cat jobs_export.json | jq '.[] | select(.status == "delivered") | .cost' | jq -s add
```

---

## Admin Analytics

Admins get access to system-wide analytics across all users.

### GET /api/v1/analytics/admin/overview

System-wide analytics overview (admin only).

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "total_jobs": 500,
  "total_cost": 150.00,
  "total_users": 25,
  "active_users": 15,
  "jobs_by_status": {
    "delivered": 400,
    "blocked": 75,
    "aborted": 25
  },
  "top_users": [
    {
      "email": "user1@example.com",
      "job_count": 100,
      "total_cost": 30.00
    },
    {
      "email": "user2@example.com",
      "job_count": 85,
      "total_cost": 25.50
    }
  ],
  "provider_usage": {
    "anthropic": 350,
    "openai": 150
  },
  "period_days": 30
}
```

**Metrics:**
- **total_users**: All registered users
- **active_users**: Users who created jobs in period
- **top_users**: Ranked by job count with costs
- **provider_usage**: System-wide provider distribution

---

### GET /api/v1/analytics/admin/user/{user_id}

Analytics for a specific user (admin only).

**Path Parameters:**
- `user_id` - User ID to analyze

**Query Parameters:**
- `days` - Number of days to include (default: 30)

**Response:**
```json
{
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2025-10-01T00:00:00Z"
  },
  "analytics": {
    "total_jobs": 50,
    "total_cost": 15.00,
    "success_rate": 85.0,
    "period_days": 30
  }
}
```

**Use Cases:**
- Monitor user activity
- Identify heavy users for upselling
- Support troubleshooting
- Usage auditing

---

## Usage Examples

### Python

```python
import requests

# Setup
access_token = "your_access_token_here"
headers = {"Authorization": f"Bearer {access_token}"}

# Get overall analytics
response = requests.get(
    "http://localhost:8000/api/v1/analytics?days=30",
    headers=headers
)
analytics = response.json()

print(f"Total Jobs: {analytics['total_jobs']}")
print(f"Total Cost: ${analytics['total_cost']:.2f}")
print(f"Success Rate: {analytics['success_rate']:.1f}%")

# Get cost breakdown
cost_response = requests.get(
    "http://localhost:8000/api/v1/analytics/cost-breakdown",
    headers=headers
)
cost_data = cost_response.json()

for provider, stats in cost_data['cost_by_provider'].items():
    print(f"{provider}: ${stats['total_cost']:.2f} ({stats['job_count']} jobs)")

# Export to CSV
csv_response = requests.get(
    "http://localhost:8000/api/v1/analytics/export/csv",
    headers=headers
)

with open('jobs_export.csv', 'w') as f:
    f.write(csv_response.text)
```

### JavaScript/TypeScript

```typescript
// Fetch analytics
const fetchAnalytics = async (days: number = 30) => {
  const response = await fetch(
    `http://localhost:8000/api/v1/analytics?days=${days}`,
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  return await response.json();
};

// Get time-series data for chart
const fetchTimeSeries = async () => {
  const response = await fetch(
    'http://localhost:8000/api/v1/analytics/time-series?days=30&interval=day',
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  const { data } = await response.json();

  // Format for Chart.js
  return {
    labels: data.map(d => new Date(d.date).toLocaleDateString()),
    datasets: [{
      label: 'Jobs',
      data: data.map(d => d.job_count)
    }, {
      label: 'Cost ($)',
      data: data.map(d => d.cost)
    }]
  };
};

// Download CSV
const downloadCSV = async () => {
  const response = await fetch(
    'http://localhost:8000/api/v1/analytics/export/csv',
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `jobs_${new Date().toISOString().split('T')[0]}.csv`;
  a.click();
};
```

### React Hook

```typescript
import { useState, useEffect } from 'react';

function useAnalytics(days: number = 30) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const response = await fetch(
          `/api/v1/analytics?days=${days}`,
          {
            headers: {
              'Authorization': `Bearer ${getAccessToken()}`
            }
          }
        );

        if (!response.ok) throw new Error('Failed to fetch analytics');

        const data = await response.json();
        setAnalytics(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [days]);

  return { analytics, loading, error };
}

// Usage in component
function AnalyticsDashboard() {
  const { analytics, loading } = useAnalytics(30);

  if (loading) return <div>Loading...</div>;

  return (
    <div>
      <h1>Analytics Dashboard</h1>
      <div className="stats">
        <div>Total Jobs: {analytics.total_jobs}</div>
        <div>Total Cost: ${analytics.total_cost.toFixed(2)}</div>
        <div>Success Rate: {analytics.success_rate.toFixed(1)}%</div>
      </div>
    </div>
  );
}
```

---

## Dashboard Visualization

### Recommended Charts

**1. Job Volume Over Time**
- Type: Line chart
- Data: Time-series endpoint with interval=day
- Y-Axis: Job count
- Use: Track usage trends

**2. Cost Breakdown**
- Type: Pie chart
- Data: Cost breakdown by provider
- Use: Budget allocation

**3. Success Rate Trend**
- Type: Area chart
- Data: Time-series with success_rate
- Y-Axis: Percentage (0-100%)
- Use: Quality monitoring

**4. Provider Performance**
- Type: Bar chart
- Data: Performance metrics by provider
- Compare: Generation time, cost, success rate
- Use: Provider selection

**5. Status Distribution**
- Type: Doughnut chart
- Data: Jobs by status
- Use: Pipeline health

### Sample Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  Total Jobs: 150    Cost: $45.50    Success: 80%  │
└─────────────────────────────────────────────────────┘

┌──────────────────────┬───────────────────────────────┐
│  Jobs Over Time      │  Cost by Provider             │
│  [Line Chart]        │  [Pie Chart]                  │
│                      │                               │
│                      │                               │
└──────────────────────┴───────────────────────────────┘

┌──────────────────────┬───────────────────────────────┐
│  Success Rate Trend  │  Provider Performance         │
│  [Area Chart]        │  [Bar Chart]                  │
│                      │                               │
│                      │                               │
└──────────────────────┴───────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  Recent Jobs Table                                   │
│  [Data Table with pagination]                       │
└─────────────────────────────────────────────────────┘
```

---

## Performance Optimization

### Caching Strategy

For high-traffic scenarios, implement caching:

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache analytics for 5 minutes
@lru_cache(maxsize=100)
def get_cached_analytics(user_id: str, days: int, cache_key: str):
    # cache_key updates every 5 minutes
    # Actual analytics query here
    pass

# In endpoint
cache_key = datetime.utcnow().strftime("%Y%m%d%H%M")[:-1]  # 5-min blocks
analytics = get_cached_analytics(current_user.id, days, cache_key)
```

### Query Optimization

- Use database indexes on `created_at`, `user_id`, `status`
- Limit time ranges for time-series queries
- Use pagination for export functions
- Consider pre-aggregation for admin analytics

---

## Troubleshooting

### "No data available"

**Problem**: Analytics show zero jobs

**Solutions:**
1. Check date range - might be too narrow
2. Verify jobs exist with `GET /api/v1/jobs`
3. Ensure jobs have `created_at` timestamps

### "Slow analytics queries"

**Problem**: Analytics take too long to load

**Solutions:**
1. Reduce `days` parameter (try 7 or 14 instead of 30)
2. Use time-series with larger intervals (week instead of day)
3. Add database indexes if missing
4. Implement caching

### "Export fails"

**Problem**: CSV/JSON export returns error

**Solutions:**
1. Check if jobs exist in the period
2. Verify authentication token
3. Try smaller date ranges first
4. Check server memory for large exports

---

## Best Practices

1. **Regular Monitoring**: Check analytics weekly to identify trends
2. **Cost Tracking**: Monitor `cost_by_provider` to optimize spending
3. **Quality Focus**: Track `success_rate` and `qc_metrics` for improvements
4. **Export Backups**: Regularly export data for archival
5. **Time Ranges**: Use appropriate intervals (day/week/month) based on data volume

---

## Related Documentation

- [API Backend Guide](./API_BACKEND_COMPLETE.md)
- [Authentication Guide](./AUTH_GUIDE.md)
- [WebSocket Guide](./WEBSOCKET_GUIDE.md)
- [Production Guide](./PRODUCTION_GUIDE.md)

---

**Version:** 1.0.0
**Last Updated:** 2025-11-09
**Status:** Production-ready
