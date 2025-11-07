# BACOWR Batch Processing Guide

Complete guide to batch processing for high-volume content generation.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Batch Runner](#batch-runner)
3. [Batch Monitoring](#batch-monitoring)
4. [Batch Scheduling](#batch-scheduling)
5. [Input Formats](#input-formats)
6. [Rate Limiting](#rate-limiting)
7. [Cost Optimization](#cost-optimization)
8. [Error Recovery](#error-recovery)
9. [Best Practices](#best-practices)

---

## Quick Start

### 1. Create Batch Input File

Create a CSV file with your jobs:

```csv
publisher,target,anchor,llm_provider,strategy,country
aftonbladet.se,https://example.com/page1,anchor text 1,auto,multi_stage,se
svd.se,https://example.com/page2,anchor text 2,anthropic,single_shot,se
```

### 2. Run Batch

```bash
# Basic batch run (sequential)
python batch_runner.py --input jobs.csv

# With 3 parallel workers
python batch_runner.py --input jobs.csv --parallel 3

# With rate limiting
python batch_runner.py --input jobs.csv --rate-limit 10
```

### 3. Monitor Progress

```bash
# Watch live progress
python batch_monitor.py --watch storage/batch_output/

# View completed batch report
python batch_monitor.py --report storage/batch_output/batch_report_*.json --details
```

---

## Batch Runner

The batch runner processes multiple content generation jobs from CSV or JSON input.

### Basic Usage

```bash
python batch_runner.py --input jobs.csv
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--input FILE` | Input file (CSV or JSON) | Required |
| `--output DIR` | Output directory | `storage/batch_output/` |
| `--parallel N` | Number of parallel workers | `1` |
| `--rate-limit N` | Max API calls per minute | No limit |
| `--no-recovery` | Disable progress recovery | Enabled |

### Parallel Processing

Run multiple jobs simultaneously:

```bash
# 3 parallel workers
python batch_runner.py --input jobs.csv --parallel 3
```

**Important**:
- Start with `--parallel 1` to ensure stability
- Increase gradually based on API rate limits
- Monitor API costs carefully with parallel processing

### Rate Limiting

Enforce API rate limits:

```bash
# Max 10 API calls per minute
python batch_runner.py --input jobs.csv --rate-limit 10
```

**Recommended limits**:
- Anthropic Claude: 10-20 calls/minute (tier dependent)
- OpenAI GPT: 20-50 calls/minute (tier dependent)
- Google Gemini: 10-30 calls/minute (tier dependent)

### Example with All Options

```bash
python batch_runner.py \
  --input large_batch.csv \
  --output production_output/ \
  --parallel 2 \
  --rate-limit 15
```

---

## Batch Monitoring

Real-time monitoring and reporting for batch jobs.

### Live Monitoring

Watch batch progress in real-time:

```bash
python batch_monitor.py --watch storage/batch_output/
```

This will:
- Auto-detect new batch reports
- Display live statistics
- Show activity updates every 10 seconds
- Track completed jobs in real-time

### View Batch Report

Display summary of completed batch:

```bash
python batch_monitor.py --report storage/batch_output/batch_report_20251107_140000.json
```

### Detailed Results

Show per-job details:

```bash
python batch_monitor.py --report batch_report.json --details
```

### Example Output

```
======================================================================
BACOWR BATCH MONITOR
======================================================================

Started:    2025-11-07T14:00:00
Completed:  2025-11-07T14:15:23
Duration:   923.4s (15.4 minutes)

Configuration:
  Workers:      3
  Rate limit:   10

Results:
  Total:        50
  ✓ Delivered:  47 (94.0%)
  ⚠ Blocked:    2
  ✗ Aborted:    1

LLM Provider Usage:
  anthropic: 30 jobs (avg 18.5s)
  openai: 17 jobs (avg 22.3s)

Writing Strategy:
  multi_stage: 35 jobs
  single_shot: 15 jobs

Performance:
  Avg time:     19.2s
  Min time:     11.3s
  Max time:     45.7s
```

---

## Batch Scheduling

Schedule and distribute batch jobs over time.

### Split Large Batches

Split a large batch into manageable chunks:

```bash
# Split into chunks of 10 jobs
python batch_scheduler.py --input large_batch.csv --chunk-size 10 --split-only
```

This creates:
```
storage/batch_chunks/
  chunk_20251107_140000_001.csv  (jobs 1-10)
  chunk_20251107_140000_002.csv  (jobs 11-20)
  chunk_20251107_140000_003.csv  (jobs 21-30)
  ...
```

### Schedule for Specific Time

Run batch at specific time:

```bash
# Start at 23:00 tonight
python batch_scheduler.py --input jobs.csv --time 23:00
```

### Distributed Processing

Split and distribute with intervals:

```bash
# Split into chunks of 10, run every 15 minutes
python batch_scheduler.py \
  --input large_batch.csv \
  --chunk-size 10 \
  --interval 15
```

### Full Example

```bash
# Split 100-job batch into chunks of 10
# Start at 23:00, run every 15 minutes
# With rate limiting and parallel processing
python batch_scheduler.py \
  --input 100_jobs.csv \
  --chunk-size 10 \
  --time 23:00 \
  --interval 15 \
  --parallel 2 \
  --rate-limit 10
```

This will:
1. Split 100 jobs into 10 chunks
2. Start first chunk at 23:00
3. Run subsequent chunks every 15 minutes
4. Complete around 01:15 (2.25 hours total)
5. Process 2 jobs in parallel per chunk
6. Respect 10 calls/minute rate limit

---

## Input Formats

### CSV Format

```csv
publisher,target,anchor,llm_provider,strategy,country,use_ahrefs,enable_llm_profiling
example.com,https://target.com/page1,anchor text,auto,multi_stage,se,true,true
example2.com,https://target.com/page2,another anchor,anthropic,single_shot,se,false,true
```

**Required columns**:
- `publisher`: Domain where content will be published
- `target`: URL to link to
- `anchor`: Anchor text for the link

**Optional columns**:
- `llm_provider`: `auto`, `anthropic`, `openai`, or `google` (default: `auto`)
- `strategy`: `multi_stage` or `single_shot` (default: `multi_stage`)
- `country`: Country code for SERP (default: `se`)
- `use_ahrefs`: `true` or `false` (default: `true`)
- `enable_llm_profiling`: `true` or `false` (default: `true`)

### JSON Format

```json
{
  "jobs": [
    {
      "publisher": "example.com",
      "target": "https://target.com/page1",
      "anchor": "anchor text",
      "llm_provider": "auto",
      "strategy": "multi_stage",
      "country": "se",
      "use_ahrefs": true,
      "enable_llm_profiling": true
    },
    {
      "publisher": "example2.com",
      "target": "https://target.com/page2",
      "anchor": "another anchor",
      "llm_provider": "anthropic",
      "strategy": "single_shot"
    }
  ]
}
```

**Advantages of JSON**:
- More expressive (nested data, arrays)
- Better for programmatic generation
- Easier to validate with JSON schema

**Advantages of CSV**:
- Simple to create in spreadsheet software
- Easy to edit manually
- Smaller file size
- Better for simple batch jobs

---

## Rate Limiting

### Understanding Rate Limits

Each LLM provider has different rate limits:

| Provider | Tier | Requests/Min | Tokens/Min |
|----------|------|--------------|------------|
| Anthropic | Tier 1 | 5 | 10,000 |
| Anthropic | Tier 2 | 10 | 40,000 |
| Anthropic | Tier 3 | 20 | 80,000 |
| OpenAI | Free | 3 | 40,000 |
| OpenAI | Tier 1 | 60 | 200,000 |
| OpenAI | Tier 2 | 500 | 2,000,000 |
| Google | Free | 15 | 1,000,000 |
| Google | Paid | 360 | 4,000,000 |

### Configuring Rate Limits

#### Conservative (Recommended for Start)

```bash
python batch_runner.py --input jobs.csv --rate-limit 5
```

Start conservative and increase gradually.

#### Balanced

```bash
python batch_runner.py --input jobs.csv --rate-limit 10 --parallel 2
```

Good balance of speed and safety.

#### Aggressive (Monitor Costs!)

```bash
python batch_runner.py --input jobs.csv --rate-limit 20 --parallel 3
```

Maximum speed, but monitor API usage carefully.

### Handling Rate Limit Errors

The batch runner automatically:
1. Enforces rate limits before making calls
2. Tracks call timestamps
3. Waits when limit is reached
4. Resumes processing automatically

If you still hit rate limits:
- Reduce `--rate-limit` value
- Reduce `--parallel` workers
- Split into smaller batches with `batch_scheduler.py`

---

## Cost Optimization

### Strategy Comparison

| Strategy | LLM Calls | Quality | Speed | Cost |
|----------|-----------|---------|-------|------|
| `multi_stage` | 3 | ★★★★★ | Slower | Higher |
| `single_shot` | 1 | ★★★★☆ | Faster | Lower |

### Cost Estimates

Based on typical article (1000 words):

| Provider | Model | Strategy | Cost/Article |
|----------|-------|----------|--------------|
| Anthropic | Haiku | single_shot | $0.02 |
| Anthropic | Haiku | multi_stage | $0.06 |
| Anthropic | Sonnet | single_shot | $0.08 |
| Anthropic | Sonnet | multi_stage | $0.24 |
| OpenAI | GPT-4o-mini | single_shot | $0.03 |
| OpenAI | GPT-4o-mini | multi_stage | $0.09 |
| OpenAI | GPT-4o | single_shot | $0.15 |
| OpenAI | GPT-4o | multi_stage | $0.45 |
| Google | Flash | single_shot | $0.01 |
| Google | Flash | multi_stage | $0.03 |

### Cost Optimization Tips

1. **Use Cheaper Models for Testing**
   ```bash
   # Use Haiku for testing
   python batch_runner.py --input test_jobs.csv
   ```

2. **Single-Shot for High Volume**
   ```bash
   # Fast and cheap for large batches
   python batch_runner.py --input large_batch.csv --strategy single_shot
   ```

3. **Multi-Stage for Premium Content**
   ```bash
   # Best quality for important clients
   python batch_runner.py --input premium_jobs.csv --strategy multi_stage
   ```

4. **Mix Strategies in Same Batch**
   - Use CSV/JSON to specify strategy per job
   - Premium clients get `multi_stage`
   - Standard clients get `single_shot`

5. **Monitor Costs with Batch Reports**
   ```bash
   python batch_monitor.py --report batch_report.json
   ```
   Shows provider usage and can estimate costs.

---

## Error Recovery

### Automatic Recovery

Batch runner automatically:
- Retries failed API calls (up to 3 times)
- Falls back to alternative providers
- Continues processing remaining jobs
- Saves progress in batch report

### Handling Failed Jobs

After batch completes, check report:

```bash
python batch_monitor.py --report batch_report.json --details
```

Look for `ABORTED` jobs and identify errors.

### Retry Failed Jobs

Extract failed jobs and retry:

```python
import json

# Load report
with open('batch_report.json', 'r') as f:
    report = json.load(f)

# Extract failed jobs
failed = [r for r in report['results'] if r['status'] == 'ABORTED']

# Create retry batch
retry_jobs = []
for job in failed:
    config = job['job_config']
    retry_jobs.append({
        'publisher': config['publisher_domain'],
        'target': config['target_url'],
        'anchor': config['anchor_text']
    })

# Save retry batch
with open('retry_batch.json', 'w') as f:
    json.dump({'jobs': retry_jobs}, f, indent=2)
```

Then run retry batch:

```bash
python batch_runner.py --input retry_batch.json
```

### Manual Intervention for BLOCKED Jobs

Jobs blocked by QC require manual review:

1. Check QC report:
   ```bash
   cat storage/batch_output/job_*_qc_report.json
   ```

2. Review issues and decide:
   - Fix job_package and regenerate
   - Override QC for acceptable quality
   - Skip job entirely

---

## Best Practices

### 1. Start Small

Always test with a small batch first:

```bash
# Test with 3-5 jobs
python batch_runner.py --input test_jobs.csv
```

Verify:
- Output quality
- Cost per job
- Processing time
- Error rate

### 2. Scale Gradually

Increase batch size progressively:

1. Start: 5 jobs
2. Then: 25 jobs
3. Then: 100 jobs
4. Production: 500+ jobs

### 3. Use Scheduling for Large Batches

For batches > 100 jobs:

```bash
python batch_scheduler.py \
  --input large_batch.csv \
  --chunk-size 25 \
  --interval 10
```

Benefits:
- Respects rate limits naturally
- Distributes API load
- Allows monitoring between chunks
- Reduces risk of mass failures

### 4. Monitor API Usage

Check your API dashboard regularly:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/usage
- Google: https://console.cloud.google.com/

Set up billing alerts!

### 5. Mix Strategies

Don't use same strategy for all jobs:

```csv
publisher,target,anchor,strategy
premium-client.com,https://...,anchor,multi_stage
standard-client.com,https://...,anchor,single_shot
test-site.com,https://...,anchor,single_shot
```

### 6. Backup Batch Reports

Batch reports contain valuable data:

```bash
# Backup reports regularly
cp storage/batch_output/batch_report_*.json backups/
```

Reports include:
- Job configurations
- Execution times
- Errors and issues
- Provider usage
- Cost estimates

### 7. Use Version Control for Input Files

Track your batch input files:

```bash
git add batches/production_batch_20251107.csv
git commit -m "Add production batch for Nov 7"
```

This helps with:
- Reproducing results
- Tracking what was generated when
- Auditing and compliance

### 8. Schedule During Off-Peak Hours

Run large batches at night:

```bash
python batch_scheduler.py --input large_batch.csv --time 23:00
```

Benefits:
- Lower API contention
- Better response times
- Less risk of disrupting other services

### 9. Test with Mock SERP First

For development, disable Ahrefs:

```bash
python batch_runner.py --input jobs.csv --no-ahrefs
```

Then enable for production:

```bash
python batch_runner.py --input jobs.csv  # Uses Ahrefs if key available
```

### 10. Document Your Batches

Keep notes on what each batch is for:

```
batches/
  README.md                           <- Document batch purposes
  client_a_nov_backlinks.csv         <- Descriptive names
  client_b_product_pages.json
  internal_blog_posts.csv
```

---

## Complete Example Workflow

### Scenario: 50-job batch for client

#### 1. Prepare Input

Create `client_backlinks.csv`:

```csv
publisher,target,anchor,llm_provider,strategy,country
example.com,https://client.com/product-a,product A,anthropic,multi_stage,se
example.com,https://client.com/product-b,product B,anthropic,multi_stage,se
...
```

#### 2. Test with Subset

```bash
# Test first 3 jobs
head -4 client_backlinks.csv > test_batch.csv
python batch_runner.py --input test_batch.csv --output test_output/
```

#### 3. Review Test Results

```bash
python batch_monitor.py --report test_output/batch_report_*.json --details
```

Check quality of generated articles.

#### 4. Run Full Batch

```bash
python batch_scheduler.py \
  --input client_backlinks.csv \
  --chunk-size 10 \
  --time 23:00 \
  --interval 10 \
  --parallel 2 \
  --rate-limit 10 \
  --output production/client_batch/
```

#### 5. Monitor Progress

In another terminal:

```bash
python batch_monitor.py --watch production/client_batch/
```

#### 6. Review Results

Next morning:

```bash
python batch_monitor.py \
  --report production/client_batch/batch_report_*.json \
  --details
```

#### 7. Handle Any Failures

Check for failed/blocked jobs and retry if needed.

#### 8. Deliver

```bash
# Articles are in production/client_batch/
ls production/client_batch/*_article.md
```

---

## Troubleshooting

### Batch Runner Not Starting

**Symptoms**: Script exits immediately

**Causes**:
- No API keys set
- Input file not found
- Invalid input format

**Solutions**:
```bash
# Check API keys
echo $ANTHROPIC_API_KEY

# Verify input file
cat jobs.csv

# Try with verbose
python batch_runner.py --input jobs.csv --verbose
```

### High Failure Rate

**Symptoms**: Many `ABORTED` jobs

**Causes**:
- Invalid URLs
- Network issues
- API quota exceeded

**Solutions**:
- Review error messages in batch report
- Check API usage dashboard
- Reduce rate limit or parallel workers

### Slow Processing

**Symptoms**: Jobs taking longer than expected

**Causes**:
- Using `multi_stage` strategy
- Rate limiting too conservative
- Large target pages

**Solutions**:
- Switch to `single_shot` for speed
- Increase `--rate-limit` if API allows
- Monitor with `batch_monitor.py --watch`

### API Rate Limit Errors

**Symptoms**: 429 errors in output

**Causes**:
- Rate limit set too high
- Multiple processes using same API key

**Solutions**:
```bash
# Reduce rate limit
python batch_runner.py --input jobs.csv --rate-limit 5

# Use sequential processing
python batch_runner.py --input jobs.csv --parallel 1
```

### Memory Issues

**Symptoms**: Script crashes with memory errors

**Causes**:
- Too many parallel workers
- Large batch files
- Memory leaks

**Solutions**:
- Reduce `--parallel` to 1
- Split batch with `batch_scheduler.py`
- Process in smaller chunks

---

## Support

For issues or questions:

1. Check this guide
2. Review PRODUCTION_GUIDE.md
3. Check batch reports for error details
4. Review API provider documentation
5. Contact development team

---

**Last Updated**: 2025-11-07
**Version**: 1.0.0
**BACOWR Project**: Del 3B Implementation
