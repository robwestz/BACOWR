# BACOWR Wave 1 Smoke Test

## Purpose

Test the complete BACOWR backend pipeline end-to-end without requiring LLM API keys.

## What It Tests

The smoke test validates:

1. ✅ **Preflight Phase**
   - Publisher domain profiling
   - Target URL profiling
   - Anchor text classification

2. ✅ **SERP Research**
   - Mock SERP data generation
   - Intent analysis

3. ✅ **Content Generation**
   - Article generation (mock mode)
   - Bridge type implementation
   - LSI term injection

4. ✅ **Quality Control**
   - QC validation
   - AutoFix (if applicable)

5. ✅ **Storage**
   - File generation (JSON + Markdown)
   - Output directory structure

## Running the Test

### Without API Keys (Mock Mode)

```bash
python tools/smoke_test_wave1.py
```

This automatically detects missing API keys and enables mock mode.

### With Real LLM API Keys (Optional)

```bash
# Set API keys in environment
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export OPENAI_API_KEY="sk-..."
# OR
export GOOGLE_API_KEY="..."

# Run test
python tools/smoke_test_wave1.py
```

### Force Mock Mode (Even With API Keys)

```bash
export BACOWR_LLM_MODE=mock
python tools/smoke_test_wave1.py
```

## Expected Output

### Successful Run

```
================================================================================
  BACOWR WAVE 1 SMOKE TEST
================================================================================

--- Environment Check ---

✗ ANTHROPIC_API_KEY: NOT SET
✗ OPENAI_API_KEY: NOT SET
✗ GOOGLE_API_KEY: NOT SET

⚠ No LLM API keys found - will auto-enable mock mode

--- Test Input ---

Publisher:  konsumenternas.se
Target:     https://sv.wikipedia.org/wiki/Artificiell_intelligens
Anchor:     läs mer om AI
LLM Mode:   MOCK

--- Running BACOWR Pipeline ---

Starting job execution...
Warning: Ahrefs API key not found. Will use mock data.

--- Results ---

Job ID:     job_20251119_173921_d0c0b425
Status:     DELIVERED
Article:    ✓ Generated (189 words)

Article preview (first 300 chars):
--------------------------------------------------------------------------------
# Complete Guide to Untitled
...
--------------------------------------------------------------------------------
QC Status:  WARNING
QC Issues:  2 found
LLM Used:   mock / mock

Output files:
  ✓ job_package: /home/user/BACOWR/storage/smoke_test_output/...
  ✓ article: /home/user/BACOWR/storage/smoke_test_output/...
  ✓ qc_report: /home/user/BACOWR/storage/smoke_test_output/...
  ✓ execution_log: /home/user/BACOWR/storage/smoke_test_output/...
  ✓ metrics: /home/user/BACOWR/storage/smoke_test_output/...

--- Test Verdict ---

✅ SUCCESS: Job completed successfully!

Wave 1 backend pipeline is WORKING:
  ✓ Preflight (publisher + target profiling)
  ✓ SERP research (mock mode)
  ✓ Intent analysis
  ✓ Article generation (mock mode)
  ✓ QC validation
  ✓ Storage
```

## Output Files

The test creates files in `storage/smoke_test_output/`:

- **`{job_id}_job_package.json`** - Complete job context and profiles
- **`{job_id}_article.md`** - Generated article in Markdown
- **`{job_id}_qc_report.json`** - Quality control validation results
- **`{job_id}_execution_log.json`** - Step-by-step execution trace
- **`{job_id}_metrics.json`** - Performance and cost metrics

## Mock Mode Details

When running in mock mode:

- **SERP data**: Uses realistic mock search results
- **LLM generation**: Generates a ~200-word template article
- **Cost**: $0.00 (no API calls)
- **Speed**: Very fast (~1-2 seconds)

Mock mode articles include:
- Basic structure (H1, H2, paragraphs)
- Link placement with anchor text
- LSI terms
- Swedish language content

**Note:** Mock articles are shorter (~200 words) vs. production (~900+ words).

## Troubleshooting

### Import Errors

```
ModuleNotFoundError: No module named 'src'
```

**Solution:** Run from project root:
```bash
cd /path/to/BACOWR
python tools/smoke_test_wave1.py
```

### Missing Dependencies

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

### Permission Errors

```
PermissionError: [Errno 13] Permission denied: 'storage/smoke_test_output'
```

**Solution:** Create directory:
```bash
mkdir -p storage/smoke_test_output
chmod 755 storage/smoke_test_output
```

## Integration with CI/CD

Add to your CI/CD pipeline:

```yaml
# .github/workflows/test.yml
- name: Run Wave 1 Smoke Test
  run: |
    python tools/smoke_test_wave1.py
  env:
    BACOWR_LLM_MODE: mock
```

This validates the backend pipeline without requiring API keys in CI.

## Next Steps

After verifying backend with this test:

1. **Start API server:** `cd api && python -m app.main`
2. **Start frontend:** `cd frontend && npm run dev`
3. **Test full stack:** Create article via GUI at http://localhost:3000

## See Also

- [README.md](../README.md) - Main documentation
- [API_GUIDE.md](../API_GUIDE.md) - API endpoints
- [PRODUCTION_GUIDE.md](../PRODUCTION_GUIDE.md) - Production deployment
