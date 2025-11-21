# BACOWR Production Deployment Guide

Complete guide for running BACOWR in production with LLM APIs and Ahrefs.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd BACOWR
pip install -r requirements.txt
```

### 2. Set API Keys

You need **at least one** LLM provider:

```bash
# Option 1: Anthropic Claude (Recommended for Swedish content)
export ANTHROPIC_API_KEY="sk-ant-xxx..."

# Option 2: OpenAI GPT
export OPENAI_API_KEY="sk-xxx..."

# Option 3: Google Gemini
export GOOGLE_API_KEY="xxx..."

# Optional: Ahrefs for real SERP data
export AHREFS_API_KEY="xxx..."
```

**Tip:** Add these to `~/.bashrc` or `~/.zshrc` for persistence.

### 3. Run Your First Job

#### Using Unified Entry Point (Recommended)

```bash
python run_bacowr.py --mode prod \
  --publisher example.com \
  --target https://target.com/page \
  --anchor "best solution" \
  --llm anthropic \
  --strategy multi_stage
```

#### Using Legacy Script (Still Supported)

```bash
python production_main.py \
  --publisher example.com \
  --target https://target.com/page \
  --anchor "best solution" \
  --llm anthropic \
  --strategy multi_stage
```

---

## 📋 Configuration Options

### LLM Providers

| Provider | Model | Best For | Cost (approx) |
|----------|-------|----------|---------------|
| `anthropic` | Claude 3.5 Sonnet | Swedish content, quality | $3-15/M tokens |
| `openai` | GPT-4o/GPT-5 | General content | $2.50-15/M tokens |
| `google` | Gemini 2.5 Pro | Cost-effective | $1.25-5/M tokens |

**Recommendation:** Start with `anthropic` for Swedish content. The quality is excellent.

### Writing Strategies

| Strategy | Description | Speed | Quality | Cost |
|----------|-------------|-------|---------|------|
| `multi_stage` | 3-stage generation (outline → content → polish) | Slower | Highest | Higher |
| `single_shot` | One LLM call | Faster | Good | Lower |

**Recommendation:** Use `multi_stage` for important content, `single_shot` for bulk jobs.

### SERP Sources

| Source | Setup | Quality | Cost |
|--------|-------|---------|------|
| **Ahrefs** | Set `AHREFS_API_KEY` | Real data | Included in Ahrefs plan |
| **Mock** | No setup | Simulated | Free |

**With Ahrefs Enterprise**, you have access to comprehensive SERP data!

---

## 🎯 Production Usage Patterns

### Pattern 1: High Quality Single Article

```bash
# Using run_bacowr.py (recommended)
python run_bacowr.py --mode prod \
  --publisher mynewssite.se \
  --target https://client.com/product \
  --anchor "bästa produkten" \
  --llm anthropic \
  --strategy multi_stage \
  --verbose

# Or using legacy script
python production_main.py \
  --publisher mynewssite.se \
  --target https://client.com/product \
  --anchor "bästa produkten" \
  --llm anthropic \
  --strategy multi_stage \
  --country se \
  --verbose
```

**When to use:**
- Important client deliveries
- High-value content
- Swedish language (Claude excels here)

**Expected:**
- Duration: 30-60 seconds
- Cost: ~$0.10-0.30 per article
- Quality: Excellent, ready to publish

---

### Pattern 2: Batch Processing

```bash
# Create a batch script
for line in $(cat urls.txt); do
  IFS='|' read -r publisher target anchor <<< "$line"

  python production_main.py \
    --publisher "$publisher" \
    --target "$target" \
    --anchor "$anchor" \
    --llm openai \
    --strategy single_shot \
    --country se

  sleep 2  # Rate limiting
done
```

**When to use:**
- Multiple articles
- Regular content production
- Budget-conscious

**Expected:**
- Duration: 15-30 seconds per article
- Cost: ~$0.05-0.15 per article
- Quality: Good, may need light editing

---

### Pattern 3: A/B Testing Providers

```bash
# Test same job with different providers
for provider in anthropic openai google; do
  python production_main.py \
    --publisher example.com \
    --target https://target.com \
    --anchor "test anchor" \
    --llm $provider \
    --strategy multi_stage \
    --output "output/$provider"
done

# Compare results
diff output/anthropic/job_*_article.md output/openai/job_*_article.md
```

**When to use:**
- Finding best provider for your use case
- Quality validation
- Cost optimization

---

## 🔧 Advanced Configuration

### Environment File Setup

Create `.env` file in project root:

```bash
# LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxx...
OPENAI_API_KEY=sk-xxx...
GOOGLE_API_KEY=xxx...

# SERP
AHREFS_API_KEY=xxx...

# Default settings
DEFAULT_LLM_PROVIDER=anthropic
DEFAULT_STRATEGY=multi_stage
DEFAULT_COUNTRY=se
```

Load with:

```bash
source .env
python production_main.py --publisher example.com ...
```

### Python API Usage

```python
from src.production_api import run_production_job

result = run_production_job(
    publisher_domain='example.com',
    target_url='https://target.com/page',
    anchor_text='best solution',
    llm_provider='anthropic',  # or 'openai', 'google'
    writing_strategy='multi_stage',
    use_ahrefs=True,
    country='se',
    enable_llm_profiling=True
)

if result['status'] == 'DELIVERED':
    print(f"Article saved to: {result['output_files']['article']}")
    print(f"Cost: ${result['metrics']['generation']['cost_usd']:.4f}")
else:
    print(f"Failed: {result['reason']}")
```

---

## 📊 Understanding Output

### Output Files

Each job creates 5 files in `storage/output/`:

1. **`{job_id}_job_package.json`** - Complete job specification
2. **`{job_id}_article.md`** - Generated article (markdown)
3. **`{job_id}_qc_report.json`** - Quality control report
4. **`{job_id}_execution_log.json`** - Step-by-step execution log
5. **`{job_id}_metrics.json`** - Performance and cost metrics

### QC Status Meanings

| Status | Meaning | Action |
|--------|---------|--------|
| `PASS` | Article meets all QC criteria | Ready to publish |
| `PASS_WITH_AUTOFIX` | Had minor issues, auto-fixed | Review fixes, likely OK |
| `BLOCKED` | Failed QC, auto-fix couldn't solve | Manual review required |

### Common QC Issues

1. **Missing LSI terms** - Auto-fixed by injecting terms
2. **Link placement** - Auto-fixed by moving link
3. **No trust sources** - Requires human signoff
4. **Intent misalignment** - Requires human signoff

---

## 💰 Cost Optimization

### Strategy 1: Use Cheaper Models for Classification

```python
from src.production_api import run_production_job

# Use cheap model (Haiku/Mini) for profiling,
# expensive model (Sonnet/GPT-4) only for writing
result = run_production_job(
    publisher_domain='example.com',
    target_url='https://target.com',
    anchor_text='anchor',
    llm_provider='anthropic',  # Will use Haiku for profiling, Sonnet for writing
    writing_strategy='multi_stage'
)
```

**Savings:** ~40-50% cost reduction

### Strategy 2: Cache SERP Results

Ahrefs data for same query can be reused:

```python
# Cache SERP for 24 hours
from src.research.ahrefs_serp import AhrefsEnhancedResearcher

researcher = AhrefsEnhancedResearcher()
# Implement caching layer (Redis, file cache, etc)
```

**Savings:** Significant for repeated queries

### Strategy 3: Batch Processing

Process multiple jobs in one session:

```python
jobs = [...]  # List of jobs
for job in jobs:
    result = run_production_job(**job)
    # Sleep between jobs to respect rate limits
    time.sleep(2)
```

---

## 🐛 Troubleshooting

### Issue: "No LLM API keys found"

**Solution:**
```bash
# Check env vars
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY
echo $GOOGLE_API_KEY

# Set at least one
export ANTHROPIC_API_KEY="sk-ant-xxx..."
```

### Issue: "Ahrefs API error"

**Solutions:**
1. Check API key: `echo $AHREFS_API_KEY`
2. Verify Enterprise plan access
3. Check rate limits (Ahrefs has daily quotas)
4. Use `--no-ahrefs` flag to fallback to mock

### Issue: "QC keeps blocking"

**Solutions:**
1. Check `storage/output/{job_id}_qc_report.json` for specific issues
2. Review forbidden angles in `intent_extension`
3. Ensure publisher tone matches content
4. May need to adjust QC thresholds in `config/thresholds.yaml`

### Issue: "Articles too short"

**Solution:**
```python
# Adjust word count requirement
job_package['generation_constraints']['min_word_count'] = 1200
```

### Issue: "Wrong language detected"

**Solution:**
```python
# Force language
job_package['generation_constraints']['language'] = 'sv'
```

---

## 📈 Performance Benchmarks

Based on testing (approximate):

| Configuration | Duration | Cost | Quality |
|---------------|----------|------|---------|
| Anthropic + Multi-stage + Ahrefs | 45s | $0.25 | ⭐⭐⭐⭐⭐ |
| OpenAI + Multi-stage + Ahrefs | 35s | $0.20 | ⭐⭐⭐⭐ |
| Google + Single-shot + Ahrefs | 20s | $0.10 | ⭐⭐⭐ |
| Any + Mock SERP | 25s | $0.15 | ⭐⭐⭐ |

---

## 🔒 Security Best Practices

### 1. Never Commit API Keys

Add to `.gitignore`:
```
.env
*.key
*_api_key.txt
```

### 2. Use Environment Variables

```bash
# Good
export ANTHROPIC_API_KEY=$(cat ~/secrets/anthropic.key)

# Bad (hardcoded in code)
api_key = "sk-ant-xxx..."  # NEVER DO THIS
```

### 3. Rotate Keys Regularly

Set calendar reminder to rotate API keys every 90 days.

### 4. Monitor Usage

Check LLM provider dashboards regularly for:
- Unusual spikes
- Unauthorized access
- Cost overruns

---

## 📞 Support & Next Steps

### Getting Help

1. Check execution logs: `storage/output/{job_id}_execution_log.json`
2. Review QC report: `storage/output/{job_id}_qc_report.json`
3. Run with `--verbose` flag for detailed output
4. Check GitHub issues: https://github.com/robwestz/BACOWR/issues

### Monitoring Production

Recommended monitoring:
```python
import json
from pathlib import Path

# Load metrics
metrics_files = Path('storage/output').glob('*_metrics.json')

total_cost = 0
for mf in metrics_files:
    with open(mf) as f:
        metrics = json.load(f)
        total_cost += metrics.get('generation', {}).get('cost_usd', 0)

print(f"Total spent: ${total_cost:.2f}")
```

---

## 🎉 You're Ready!

Start with a test run:

```bash
python production_main.py \
  --publisher test.com \
  --target https://example.com \
  --anchor "test link" \
  --llm anthropic \
  --verbose
```

Check the output in `storage/output/` and iterate from there!

---

**Version:** 1.0
**Last Updated:** 2025-11-07
**Status:** Production Ready
