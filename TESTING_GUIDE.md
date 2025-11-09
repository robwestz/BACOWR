# BACOWR Complete Pipeline - Testing Guide

## ✅ Status: Ready for Testing

All core services tested and working! The complete pipeline is ready for end-to-end testing.

## Prerequisites

### 1. Install Dependencies

```bash
cd /home/user/BACOWR
pip install -r requirements.txt
```

### 2. Set Environment Variables

Create a `.env` file or export these variables:

```bash
# Required for complete pipeline
export SERPAPI_KEY="your_serpapi_key_here"
export ANTHROPIC_API_KEY="your_anthropic_key_here"

# Database (if testing via API)
export DATABASE_URL="postgresql://user:pass@localhost/bacowr"
export JWT_SECRET_KEY="your_secret_key"

# Optional
export OPENAI_API_KEY="your_openai_key"
export GOOGLE_API_KEY="your_google_key"
export AHREFS_API_KEY="your_ahrefs_key"
```

### 3. Get API Keys

**SerpAPI (Required):**
- Sign up at https://serpapi.com/
- Free tier: 100 searches/month
- Cost: ~$0.005 per search

**Anthropic Claude (Required):**
- Sign up at https://console.anthropic.com/
- Get API key from settings
- Cost: ~$0.06 per article (with expert strategy)

## Quick Verification Tests

### Test 1: Core Services (No API keys needed)

```bash
cd /home/user/BACOWR
python tests/test_core_services.py
```

**Expected Output:**
```
============================================================
Testing Core Services
============================================================

1. Job Orchestrator...
   ✓ Initialized
   ✓ Has execute() method

2. Writer Engine...
   ✓ Initialized
   ✓ Has generate() method
   ✓ Has _build_prompt() method

3. SERP API Integration...
   ✓ Initialized
   ✓ Has research() method

4. Next-A1 QC Validator...
   ✓ Initialized
   ✓ Has validate() method
   ✓ Has all 8 QC criteria methods

🎉 All Core Services Tests Passed!
```

### Test 2: API Server Startup

```bash
cd /home/user/BACOWR
python -m uvicorn api.app.main:app --reload
```

**Expected Output:**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Check endpoint documentation at: http://127.0.0.1:8000/docs

### Test 3: Complete Pipeline Test (Requires API keys)

**Option A: Via Python Script**

Create `test_pipeline.py`:

```python
import asyncio
import os
import sys
sys.path.insert(0, '/home/user/BACOWR')

from api.app.services.job_orchestrator import BacklinkJobOrchestrator

async def test_pipeline():
    """Test complete pipeline with real inputs."""

    # Initialize orchestrator
    orchestrator = BacklinkJobOrchestrator(
        llm_provider='anthropic'
    )

    # Test inputs - Swedish government education page
    publisher_domain = "svd.se"
    target_url = "https://www.regeringen.se/regeringens-politik/skolpolitik/"
    anchor_text = "utbildningssystemet"

    print("Testing Complete Pipeline...")
    print(f"Publisher: {publisher_domain}")
    print(f"Target: {target_url}")
    print(f"Anchor: {anchor_text}")
    print("\nExecuting pipeline...\n")

    try:
        result = await orchestrator.execute(
            publisher_domain=publisher_domain,
            target_url=target_url,
            anchor_text=anchor_text,
            user_id="test_user",
            country="se",
            language="sv",
            writing_strategy="expert"
        )

        print("=" * 60)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)

        # Print results
        print(f"\nArticle length: {len(result.get('article_content', ''))} characters")
        print(f"QC Status: {result.get('qc_report', {}).get('status')}")
        print(f"QC Score: {result.get('qc_report', {}).get('overall_score')}")
        print(f"Bridge Type: {result.get('job_package', {}).get('intent_extension', {}).get('recommended_bridge_type')}")

        # Print QC scores
        qc_scores = result.get('qc_report', {}).get('scores', {})
        print("\nQC Criteria Scores:")
        for criterion, score in qc_scores.items():
            print(f"  {criterion}: {score}")

        # Print issues
        issues = result.get('qc_report', {}).get('issues', [])
        if issues:
            print(f"\nIssues ({len(issues)}):")
            for issue in issues[:5]:  # Show first 5
                print(f"  - [{issue['severity']}] {issue['message']}")

        return True

    except Exception as e:
        print("=" * 60)
        print("❌ PIPELINE FAILED")
        print("=" * 60)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_pipeline())
    sys.exit(0 if success else 1)
```

Run it:

```bash
python test_pipeline.py
```

**Option B: Via API Endpoint**

1. Start the API server:
```bash
python -m uvicorn api.app.main:app --reload
```

2. Create a user and get auth token (or use existing):
```bash
# This depends on your auth setup
# For testing, you might need to create a test user first
```

3. Create a job:
```bash
curl -X POST http://localhost:8000/api/v1/jobs/create-complete \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "publisher_domain": "svd.se",
    "target_url": "https://www.regeringen.se/regeringens-politik/skolpolitik/",
    "anchor_text": "utbildningssystemet",
    "llm_provider": "anthropic",
    "writing_strategy": "expert",
    "country": "se"
  }'
```

4. Check job status:
```bash
curl http://localhost:8000/api/v1/jobs/{job_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## What to Test

### Core Functionality

- [ ] **Profiling**: Target and publisher profiles are accurate
- [ ] **SERP Research**: Real SERP data fetched via SerpAPI
- [ ] **Intent Analysis**: Correct bridge type recommended
- [ ] **Content Generation**: Article generated with proper structure
- [ ] **QC Validation**: All 8 criteria validated
- [ ] **Package Format**: Output matches BacklinkJobPackage schema

### Bridge Types

Test different scenarios:

1. **Strong Bridge** (aligned intents)
   - Publisher: Educational news site
   - Target: Government education policy
   - Anchor: "utbildningspolitiken"

2. **Pivot Bridge** (partial alignment)
   - Publisher: Tech blog
   - Target: Casino reviews
   - Anchor: "spelupplevelse online"

3. **Wrapper Bridge** (weak alignment)
   - Publisher: Health magazine
   - Target: Casino affiliate
   - Anchor: "online underhållning"

### QC Criteria

Verify all 8 criteria are checked:

1. **Preflight**: Bridge type matches intent alignment
2. **Draft**: Word count ≥900, ≥2 H2 sections, subtopic coverage ≥60%
3. **Anchor**: NOT in H1/H2, risk assessment
4. **Trust**: T1-T4 source quality
5. **Intent**: No 'off' alignments
6. **LSI**: 6-10 LSI terms in near-window
7. **Fit**: Readability (LIX 35-45), tone match
8. **Compliance**: Required disclaimers detected

## Expected Timings

- **Profiling**: 2-4 seconds
- **SERP Research**: 3-5 seconds (API calls)
- **Intent Analysis**: 1-2 seconds
- **Content Generation**: 8-15 seconds (LLM call)
- **QC Validation**: 1-2 seconds
- **Total**: ~15-30 seconds per job

## Troubleshooting

### Common Issues

**1. "SERPAPI_KEY not found"**
```bash
export SERPAPI_KEY="your_key_here"
```

**2. "ANTHROPIC_API_KEY not found"**
```bash
export ANTHROPIC_API_KEY="your_key_here"
```

**3. "Target URL returned HTTP 404"**
- Check target URL is accessible
- Try different target URL

**4. "QC Status: BLOCKED"**
- Review QC report issues
- Content didn't meet Next-A1 criteria
- May need parameter adjustments

**5. Database connection error**
- Ensure PostgreSQL is running
- Check DATABASE_URL is correct

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Success Criteria

✅ Pipeline completes without errors
✅ Article generated (≥900 words)
✅ QC score ≥80 (PASS status)
✅ Bridge type appropriate for intent alignment
✅ All 8 QC criteria evaluated
✅ Output matches BacklinkJobPackage schema
✅ Execution time <30 seconds

## Next Steps After Testing

Once pipeline works:

1. **Performance Optimization**
   - Cache SERP results
   - Parallel profiling
   - LLM prompt optimization

2. **Quality Improvements**
   - Fine-tune QC thresholds
   - Expand LSI term database
   - Improve intent detection

3. **Feature Additions**
   - Multi-language support
   - Custom QC profiles
   - Batch processing
   - Advanced analytics

4. **Production Deployment**
   - Set up monitoring
   - Configure rate limiting
   - Add error alerting
   - Deploy to cloud

## Support

For issues:
1. Check logs: `tail -f api/logs/bacowr.log`
2. Review QC report for content issues
3. Verify all environment variables set
4. Run smoke tests: `python tests/test_core_services.py`

## Test Data Suggestions

Good test cases:

**Swedish Examples:**
- Publisher: "svd.se", "aftonbladet.se", "dn.se"
- Targets: Government sites (.se), educational institutions
- Anchors: Generic Swedish phrases

**English Examples:**
- Publisher: "techcrunch.com", "theverge.com"
- Targets: Tech product pages, SaaS sites
- Anchors: Generic tech terms

Avoid:
- YMYL topics without proper disclaimers
- Exact-match money anchors
- Low-quality target pages
