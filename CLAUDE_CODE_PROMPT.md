# CLAUDE CODE PROMPT: BACOWR Production Development

## System Overview

BACOWR (**B**acklink **A**rticle **C**ontent **O**rchestration **W**ith **R**efinement) is an enterprise-grade content generation engine for creating high-quality backlink articles. This is a **production system**, not an MVP or prototype.

### Core Purpose

Generate SEO-optimized backlink articles that:
- Analyze SERP intent and top results
- Profile target pages and publisher sites automatically
- Create natural content that fits the SERP landscape
- Validate quality with comprehensive QC system
- Log every step for complete traceability

### Three-Input Paradigm

The system requires only three inputs to generate complete articles:
```json
{
  "publisher_domain": "example-publisher.com",
  "target_url": "https://client.com/product-x",
  "anchor_text": "best choice for [theme]"
}
```

Everything else is derived automatically through:
- Page profiling (publisher & target)
- SERP research and analysis
- Intent modeling and alignment
- Multi-LLM content generation
- Quality control validation

---

## Architecture Principles

### 1. Production-First Design

**Everything you build must be production-ready:**
- Full error handling and logging
- Comprehensive input validation
- Proper resource cleanup
- Performance optimization
- Security best practices

**No shortcuts. No "TODO: implement later". No MVP compromises.**

### 2. State Machine Foundation

All job execution flows through a deterministic state machine:

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                                ↓ (on QC fail)
                             RESCUE (max 1x)
                                ↓
                               QC → DELIVER or ABORT
```

**Rules:**
- Every state transition is logged
- No loops (hash-based detection)
- RESCUE max once per job
- Automatic ABORT on repeated failures

### 3. Quality Control System

Two-tier QC with:
- **AutoFixOnce**: Automatic corrections for minor issues (link placement, LSI injection, etc)
- **Blocking Conditions**: Human signoff required for serious issues (intent misalignment, no trust sources, etc)

**Critical:** QC is non-negotiable. Articles that fail blocking conditions MUST NOT be delivered.

### 4. Multi-Provider LLM Support

Support for multiple LLM providers with automatic fallback:
- **Anthropic Claude** (Haiku, Sonnet, Opus)
- **OpenAI GPT** (GPT-4o, GPT-4-turbo, etc)
- **Google Gemini** (Flash, Pro 1.5/2.0)

**Cost optimization:** Use cheap models for classification, expensive models only for writing.

### 5. Traceability & Observability

Every job produces complete audit trail:
- `job_package.json` - Complete specification
- `article.md` - Generated content
- `qc_report.json` - Quality validation results
- `execution_log.json` - State machine trace
- `metrics.json` - Performance and cost data

---

## Code Standards

### File Organization

```
BACOWR/
├── src/                    # Core engine code
│   ├── engine/            # State machine, logging
│   ├── qc/                # Quality control
│   ├── profiling/         # Page profiling
│   ├── research/          # SERP research
│   ├── analysis/          # Intent analysis
│   └── writer/            # Content generation
├── config/                # QC rules, policies
├── tests/                 # Comprehensive tests
├── storage/               # Output files
├── api/                   # REST API backend
└── frontend/              # Web UI (separate)
```

### Naming Conventions

**Classes:** PascalCase
```python
class PageProfiler:
class QualityController:
class StateMachine:
```

**Functions/Methods:** snake_case
```python
def run_backlink_job():
def validate_qc_report():
def extract_page_content():
```

**Constants:** UPPER_SNAKE_CASE
```python
MAX_RESCUE_ATTEMPTS = 1
DEFAULT_MIN_WORD_COUNT = 900
QC_BLOCKING_SCORE = 7
```

**Files:** snake_case.py
```
page_profiler.py
quality_controller.py
state_machine.py
```

### Type Hints

**Always use type hints:**
```python
def run_backlink_job(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    llm_provider: Optional[str] = None
) -> Dict[str, Any]:
    pass
```

### Error Handling

**Comprehensive error handling:**
```python
try:
    result = dangerous_operation()
except SpecificException as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    # Graceful degradation or re-raise
    raise
finally:
    cleanup_resources()
```

**Never:**
- Silent failures
- Bare `except:` clauses
- Swallowing exceptions
- Missing error context

### Logging

**Structured logging with context:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Starting job", extra={
    "job_id": job_id,
    "publisher": publisher_domain,
    "target": target_url
})
```

**Log levels:**
- `DEBUG`: Detailed diagnostic info
- `INFO`: Important milestones
- `WARNING`: Recoverable issues
- `ERROR`: Failures requiring attention
- `CRITICAL`: System-level failures

### Documentation

**Every module needs docstring:**
```python
"""
Page profiling module for extracting content and metadata.

This module provides PageProfiler class for analyzing web pages
and extracting key information needed for content generation.

Main classes:
    PageProfiler: Extracts structured data from URLs
    LLMEnhancer: Adds LLM-powered semantic analysis

Example:
    >>> profiler = PageProfiler()
    >>> profile = profiler.profile_url("https://example.com")
    >>> print(profile['page_meta']['title'])
"""
```

**Public functions need docstrings:**
```python
def profile_url(self, url: str) -> Dict[str, Any]:
    """
    Extract comprehensive profile data from a URL.

    Args:
        url: Full URL to profile

    Returns:
        Dict containing page_meta, content_analysis, and entity_extraction

    Raises:
        URLError: If URL is invalid or unreachable
        ParseError: If page content cannot be parsed
    """
```

---

## Testing Requirements

### Test Coverage

**Minimum 80% code coverage** for all production code.

### Test Organization

```
tests/
├── test_schema_validation.py      # JSON Schema tests
├── test_qc_system.py               # QC system tests
├── test_state_machine.py           # State machine tests
├── test_page_profiler.py           # Profiling tests
├── test_serp_researcher.py         # SERP tests
├── test_intent_analyzer.py         # Intent tests
├── test_writer_engine.py           # Writer tests
└── test_e2e_mock.py                # End-to-end tests
```

### Test Structure

```python
import pytest

class TestPageProfiler:
    """Test suite for PageProfiler class."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.profiler = PageProfiler()

    def test_profile_url_success(self):
        """Test successful URL profiling."""
        profile = self.profiler.profile_url("https://example.com")
        assert 'page_meta' in profile
        assert profile['page_meta']['title']

    def test_profile_url_invalid_url(self):
        """Test error handling for invalid URL."""
        with pytest.raises(URLError):
            self.profiler.profile_url("not-a-url")
```

### Mock vs Real Tests

**Mock tests:** Fast, no external dependencies
```python
@patch('requests.get')
def test_with_mock(mock_get):
    mock_get.return_value.text = "<html>Mock content</html>"
    result = fetch_page("http://example.com")
    assert "Mock content" in result
```

**Integration tests:** Real APIs (optional, slower)
```python
@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="No API key")
def test_real_llm():
    result = generate_with_llm("test prompt")
    assert len(result) > 0
```

---

## LLM Integration Guidelines

### Provider Abstraction

**Always code against interface, not implementation:**
```python
from src.writer.production_writer import ProductionWriter

# Good - provider agnostic
writer = ProductionWriter(provider="anthropic")
article = writer.write(job_package)

# Bad - hard-coded provider
from anthropic import Anthropic
client = Anthropic()
```

### Cost Awareness

**Track costs for every LLM call:**
```python
result = llm_call(prompt)
metrics['cost_usd'] += calculate_cost(
    provider=provider,
    model=model,
    input_tokens=result.usage.input_tokens,
    output_tokens=result.usage.output_tokens
)
```

### Fallback Strategy

**Implement graceful degradation:**
```python
providers = ['anthropic', 'openai', 'google']
for provider in providers:
    try:
        result = generate_content(provider=provider)
        break
    except ProviderError as e:
        logger.warning(f"Provider {provider} failed: {e}")
        continue
else:
    raise AllProvidersFailedError()
```

---

## Security Requirements

### API Keys

**Never hardcode API keys:**
```python
# Good
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ConfigurationError("ANTHROPIC_API_KEY not set")

# Bad
api_key = "sk-ant-xxx..."  # NEVER DO THIS
```

### Input Validation

**Validate all external inputs:**
```python
def validate_url(url: str) -> str:
    """Validate and sanitize URL input."""
    parsed = urlparse(url)
    if not parsed.scheme in ['http', 'https']:
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
    if not parsed.netloc:
        raise ValueError("URL missing domain")
    return url
```

### SQL Injection Prevention

**Always use parameterized queries:**
```python
# Good
cursor.execute(
    "SELECT * FROM jobs WHERE user_id = ?",
    (user_id,)
)

# Bad
cursor.execute(
    f"SELECT * FROM jobs WHERE user_id = {user_id}"
)
```

---

## Performance Optimization

### Caching Strategy

**Cache expensive operations:**
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_serp_data(query: str) -> Dict:
    """Cached SERP lookup."""
    return expensive_serp_api_call(query)
```

### Batch Processing

**Process multiple jobs efficiently:**
```python
# Parallel processing with rate limiting
from concurrent.futures import ThreadPoolExecutor
import time

def process_batch(jobs, max_workers=3, rate_limit=10):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for job in jobs:
            future = executor.submit(process_job, job)
            futures.append(future)
            time.sleep(1/rate_limit)  # Rate limiting

        results = [f.result() for f in futures]
    return results
```

### Resource Management

**Always clean up resources:**
```python
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = create_connection()
    try:
        yield conn
    finally:
        conn.close()
```

---

## Git Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Emergency fixes

### Commit Messages

**Format:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `perf`: Performance improvement
- `chore`: Maintenance tasks

**Example:**
```
feat(writer): add multi-stage generation strategy

Implement three-stage content generation:
1. Outline generation
2. Content expansion
3. Polish and refinement

This improves article quality by 30% in testing.

Closes #123
```

---

## Deployment

### Environment Configuration

**Use `.env` for configuration:**
```bash
# LLM APIs
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx

# SERP
AHREFS_API_KEY=xxx

# Database
DATABASE_URL=postgresql://user:pass@host/db

# Application
LOG_LEVEL=INFO
MAX_WORKERS=5
RATE_LIMIT=10
```

### Health Checks

**Implement health check endpoints:**
```python
@app.get("/health")
def health_check():
    """Health check endpoint for load balancers."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Monitoring

**Key metrics to track:**
- Job success rate
- Average generation time
- Cost per article
- QC pass/fail rates
- API error rates
- Resource utilization

---

## Critical Reminders

### 1. This is Production Code

Every line of code you write will run in production. Act accordingly:
- Handle all error cases
- Log important events
- Validate all inputs
- Test thoroughly
- Document clearly

### 2. Quality Over Speed

**Never sacrifice quality for speed:**
- Write comprehensive tests
- Add proper error handling
- Document complex logic
- Review before committing

### 3. User Trust

Users depend on this system for their business. Respect that trust:
- Never lose data
- Never expose API keys
- Never skip validation
- Never ignore errors

### 4. Cost Awareness

LLM API calls cost money. Optimize ruthlessly:
- Use cheap models where possible
- Cache aggressively
- Batch efficiently
- Track costs meticulously

---

## Development Workflow

### Before Starting Work

1. Pull latest code: `git pull origin main`
2. Create feature branch: `git checkout -b feature/my-feature`
3. Review relevant docs and tests
4. Plan implementation approach

### During Development

1. Write tests first (TDD)
2. Implement feature
3. Run tests: `pytest tests/`
4. Check code quality: `pylint src/`
5. Update documentation
6. Commit with clear message

### Before Pushing

1. Run full test suite
2. Check test coverage
3. Review changed files
4. Update CHANGELOG.md
5. Push and create PR

---

## Questions to Ask

When implementing new features, always ask:

1. **Error handling**: What can go wrong? How do we handle it?
2. **Testing**: How do we test this? What edge cases exist?
3. **Performance**: Is this efficient? Can it handle production load?
4. **Security**: Are there security implications?
5. **Cost**: Does this add LLM costs? Can we optimize?
6. **Logging**: What do we need to log for debugging?
7. **Documentation**: Is this clear to other developers?
8. **Backwards compatibility**: Does this break existing code?

---

## Resources

### Internal Documentation

- `README.md` - Project overview
- `PRODUCTION_GUIDE.md` - Production usage guide
- `BATCH_GUIDE.md` - Batch processing guide
- `API_BACKEND_COMPLETE.md` - API documentation
- `backlink_engine_ideal_flow.md` - System flow
- `NEXT-A1-ENGINE-ADDENDUM.md` - Formal requirements

### External Resources

- [Anthropic API Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)

---

## Contact & Support

For questions or issues:
- GitHub Issues: https://github.com/robwestz/BACOWR/issues
- Documentation: See `/docs` directory
- Tests: See `/tests` directory for examples

---

**Version:** 1.0.0
**Status:** Production
**Last Updated:** 2025-11-12

**Remember:** This is production code. Write it like your business depends on it—because someone's does.
