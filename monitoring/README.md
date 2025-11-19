# BACOWR Monitoring Stack

Production-ready observability with Prometheus and Grafana.

## Features

- 📊 **Prometheus**: Metrics collection and alerting
- 📈 **Grafana**: Beautiful dashboards and visualization
- 🚨 **Alerts**: Pre-configured alert rules for critical metrics
- 📦 **Docker**: Easy deployment with docker-compose
- 🔧 **Auto-discovery**: Automatic metrics endpoint discovery

---

## Quick Start

### 1. Start Monitoring Stack

```bash
# From BACOWR root directory
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Access Dashboards

**Grafana**:
- URL: http://localhost:3001
- Username: `admin`
- Password: `admin`
- Change password on first login!

**Prometheus**:
- URL: http://localhost:9090
- Query interface and alerts

**Metrics Endpoint**:
- URL: http://localhost:8000/metrics
- Raw Prometheus metrics from FastAPI

### 3. View Dashboards

Navigate to Grafana → Dashboards → Browse:
1. **BACOWR API Performance** - Request rate, latency, errors
2. **BACOWR Business Metrics** - Jobs, costs, QC scores

---

## Architecture

```
┌─────────────────┐
│  FastAPI App    │
│  :8000/metrics  │
└────────┬────────┘
         │
         │ scrape metrics
         ↓
┌─────────────────┐     ┌─────────────────┐
│   Prometheus    │────→│    Grafana      │
│     :9090       │     │      :3001      │
└─────────────────┘     └─────────────────┘
         │
         │ evaluate alerts
         ↓
┌─────────────────┐
│  Alert Manager  │ (optional)
│     :9093       │
└─────────────────┘
```

---

## Available Metrics

### API Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `api_requests_total` | Counter | Total API requests by endpoint, method, status |
| `api_request_duration_seconds` | Histogram | Request duration (p50, p95, p99) |
| `http_requests_inprogress` | Gauge | Currently processing requests |

### LLM Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `llm_generation_duration_seconds` | Histogram | LLM generation time by provider/model |
| `llm_generation_cost_dollars` | Counter | LLM costs in USD by provider/model |

### Job Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `active_jobs` | Gauge | Currently active jobs |
| `jobs_completed_total` | Counter | Completed jobs by status (delivered/blocked/failed) |
| `qc_score` | Histogram | QC score distribution |

### Batch Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `batch_review_progress_percent` | Gauge | Batch processing progress per batch_id |

---

## Dashboards

### 1. API Performance Dashboard

**Panels**:
- Requests per Second (QPS)
- p95 Response Time
- Error Rate (%)
- Request Rate by Endpoint
- Response Time Percentiles (p50, p95, p99)
- HTTP Status Codes (2xx, 4xx, 5xx)

**Use Cases**:
- Monitor API health
- Detect performance degradation
- Identify slow endpoints
- Track error spikes

### 2. Business Metrics Dashboard

**Panels**:
- Active Jobs (current)
- Jobs Delivered (last hour)
- LLM Cost per Hour
- Delivery Success Rate (%)
- Job Completion Rate by Status
- LLM Generation Time (p50, p95)
- LLM Costs by Provider
- Batch Review Progress

**Use Cases**:
- Track business KPIs
- Monitor LLM costs
- Measure QC effectiveness
- Track batch processing

---

## Alert Rules

Pre-configured alerts in `alert_rules.yml`:

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **HighAPIErrorRate** | Error rate > 5% for 5min | Critical | Page on-call |
| **HighAPILatency** | p95 latency > 2s for 5min | Warning | Investigate |
| **HighQCBlockRate** | QC blocks > 15% for 30min | Warning | Review QC rules |
| **HighLLMCosts** | Costs > $10/hour for 15min | Warning | Check usage |
| **APIDown** | API unavailable for 2min | Critical | Page on-call |
| **TooManyActiveJobs** | >100 active jobs for 10min | Warning | Check for stuck jobs |

---

## Configuration

### Prometheus Configuration

Edit `prometheus.yml` to:
- Change scrape intervals
- Add new scrape targets
- Configure alerting

```yaml
scrape_configs:
  - job_name: 'bacowr-api'
    static_configs:
      - targets: ['host.docker.internal:8000']
    scrape_interval: 10s
```

### Alert Rules

Edit `alert_rules.yml` to:
- Add new alerts
- Modify thresholds
- Change severity levels

```yaml
- alert: HighAPIErrorRate
  expr: (rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m])) > 0.05
  for: 5m
  labels:
    severity: critical
```

### Grafana Dashboards

Dashboards are auto-provisioned from `grafana/dashboards/`:
- `bacowr-api.json` - API Performance
- `bacowr-business.json` - Business Metrics

Edit JSON files to customize panels and queries.

---

## Querying Metrics

### Prometheus Query Examples

**Request rate**:
```promql
rate(api_requests_total[5m])
```

**p95 latency**:
```promql
histogram_quantile(0.95, rate(api_request_duration_seconds_bucket[5m]))
```

**Error rate**:
```promql
(rate(api_requests_total{status=~"5.."}[5m]) / rate(api_requests_total[5m])) * 100
```

**LLM costs per hour**:
```promql
rate(llm_generation_cost_dollars[1h]) * 3600
```

**Active jobs**:
```promql
active_jobs
```

---

## Tracking Metrics in Code

### Track LLM Generation

```python
from api.app.middleware import track_llm_generation

# After LLM call
track_llm_generation(
    provider="anthropic",
    model="claude-3-haiku",
    duration=25.3,  # seconds
    cost=0.12       # USD
)
```

### Track Job Completion

```python
from api.app.middleware import track_job_completion

# When job completes
track_job_completion(status="delivered")  # or "blocked", "failed"
```

### Update Active Jobs

```python
from api.app.middleware import set_active_jobs

# Periodically update
active_count = db.query(Job).filter(Job.status == "processing").count()
set_active_jobs(active_count)
```

### Track Batch Progress

```python
from api.app.middleware import set_batch_progress

# During batch review
set_batch_progress(
    batch_id="batch_abc123",
    progress_percent=75.0
)
```

### Track QC Score

```python
from api.app.middleware import track_qc_score

# After QC
track_qc_score(score=92.5)
```

---

## Production Deployment

### Environment Variables

```bash
# Enable metrics (default: true)
ENABLE_METRICS=true

# Prometheus retention (default: 30 days)
PROMETHEUS_RETENTION=30d
```

### Resource Limits

Add to `docker-compose.monitoring.yml`:

```yaml
services:
  prometheus:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### Data Persistence

Volumes are created for data persistence:
- `prometheus_data`: Prometheus time-series data (30 days)
- `grafana_data`: Grafana dashboards and config

**Backup**:
```bash
docker run --rm -v bacowr_prometheus_data:/data -v $(pwd):/backup ubuntu tar czf /backup/prometheus-backup.tar.gz /data
```

---

## Troubleshooting

### Metrics endpoint not working

**Check FastAPI is running**:
```bash
curl http://localhost:8000/metrics
```

**Expected output**: Prometheus text format metrics

### Prometheus not scraping

**Check Prometheus targets**:
1. Open http://localhost:9090/targets
2. Verify `bacowr-api` is UP
3. Check "Last Scrape" time

**Common issues**:
- FastAPI not running on port 8000
- Docker network issues (use `host.docker.internal`)
- Firewall blocking port 8000

### Grafana dashboards not loading

**Check datasource**:
1. Grafana → Configuration → Data Sources
2. Verify Prometheus is configured
3. Test connection

**Re-provision dashboards**:
```bash
docker-compose -f docker-compose.monitoring.yml restart grafana
```

### High memory usage

**Reduce Prometheus retention**:
```yaml
command:
  - '--storage.tsdb.retention.time=7d'  # Instead of 30d
```

**Reduce scrape frequency**:
```yaml
scrape_interval: 30s  # Instead of 10s
```

---

## Advanced Configuration

### Add Alertmanager

Uncomment in `docker-compose.monitoring.yml`:

```yaml
alertmanager:
  image: prom/alertmanager:latest
  ports:
    - "9093:9093"
  # ... configuration
```

Create `alertmanager.yml`:
```yaml
route:
  receiver: 'email'
receivers:
  - name: 'email'
    email_configs:
      - to: 'ops@example.com'
        from: 'alertmanager@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'user'
        auth_password: 'pass'
```

### Add Node Exporter

For system metrics (CPU, memory, disk):

```yaml
node-exporter:
  image: prom/node-exporter:latest
  ports:
    - "9100:9100"
```

### Custom Grafana Plugins

```yaml
grafana:
  environment:
    - GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-clock-panel
```

---

## Monitoring Best Practices

1. **Set up alerts** for critical metrics (error rate, latency)
2. **Review dashboards** daily during initial deployment
3. **Track costs** closely - LLM costs can add up quickly
4. **Establish baselines** for normal operation
5. **Document incidents** and update alerts accordingly
6. **Regular backups** of Prometheus and Grafana data
7. **Test alerts** to ensure they fire correctly

---

## Support

**Issues**: https://github.com/bacowr/bacowr/issues
**Prometheus Docs**: https://prometheus.io/docs/
**Grafana Docs**: https://grafana.com/docs/

---

**Maintained by**: Kappa Team (Monitoring)
**Status**: ✅ Production Ready
**Version**: 1.0.0
