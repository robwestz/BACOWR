# BACOWR Quickstart Guide

Get started with BACOWR in 3 minutes.

## Install

```bash
# Clone and enter directory
cd BACOWR

# Install dependencies
pip install -r requirements.txt
```

## Run (Mock Mode - No API Keys Required)

**Note:** CLI (`main.py`) has a known initialization issue. Use Python API or FastAPI instead.

### Option 1: Python API (Recommended)

```python
from src.core_api import run_backlink_job

result = run_backlink_job(
    publisher_domain="example.com",
    target_url="https://example.org",
    anchor_text="test link",
    mock=True
)

print(result['article'])  # Generated article
print(result['status'])   # DELIVERED/BLOCKED/ABORTED
```

### Option 2: FastAPI Server

```bash
cd api
uvicorn app.main:app --reload

# Visit http://localhost:8000/docs
```

## Run Tests

```bash
# All tests
pytest -v

# Quick smoke test
pytest tests/test_e2e_mock.py::TestE2EBasicWorkflow::test_e2e_mock_success_path -v

# API smoke test
python tools/api_smoke_test.py
```

## Production Mode (With API Keys)

```bash
# Set your LLM API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run with real LLM via Python API
python -c "
from src.core_api import run_backlink_job
import os

result = run_backlink_job(
    publisher_domain='example.com',
    target_url='https://example.org',
    anchor_text='test link',
    mock=False  # Use real LLM
)
print(f'Status: {result[\"status\"]}')
print(f'Article: {len(result[\"article\"])} chars')
"
```

## Next Steps

- Read [DEBUG_NOTES.md](docs/DEBUG_NOTES.md) for detailed setup
- Read [README.md](README.md) for architecture overview
- Check [API_GUIDE.md](API_GUIDE.md) for API documentation

## Need Help?

- Check test files in `tests/` for examples
- Check API docs at http://localhost:8000/docs
- Report issues on GitHub
