# API Key Management Guide

**Location:** `config/api_keys.py`

All API keys (both internal and external) are centrally managed in one place.

## Overview

The `APIKeyManager` loads and validates all API keys from the `.env` file, providing:
- ✅ Centralized key management
- ✅ Automatic validation on startup
- ✅ Type-safe key access
- ✅ Fallback to mock mode if keys missing
- ✅ Clear status reporting

## Quick Start

### 1. Create .env File

```bash
cp .env.template .env
# Edit .env and add your API keys
```

### 2. Use in Code

```python
from config.api_keys import api_keys, APIKeyType

# Check if key is available
if api_keys.has_key(APIKeyType.ANTHROPIC):
    key = api_keys.get_key(APIKeyType.ANTHROPIC)
    # use key...

# Or use convenience functions
from config.api_keys import get_anthropic_key, get_openai_key

anthropic_key = get_anthropic_key()  # Returns None if not set
```

### 3. Check Status

```bash
# Run the key manager directly to see configuration status
python config/api_keys.py
```

Output:
```
======================================================================
API Key Configuration Status
======================================================================
✓ Anthropic Claude       - Claude API for content generation
✗ OpenAI GPT             - GPT-4/GPT-3.5 for content generation
✗ Google Gemini          - Gemini for content generation
✗ Ahrefs API             - SERP and competitor data
✗ SerpAPI                - Search engine results
✗ Database URL           - PostgreSQL connection string
✗ Redis URL              - Redis cache for performance
======================================================================
Available LLM providers: anthropic
======================================================================
```

## API Key Types

### LLM Providers (at least one required for production)

| Provider | Environment Variable | Required | Description |
|----------|---------------------|----------|-------------|
| Anthropic Claude | `ANTHROPIC_API_KEY` | Optional* | Recommended for quality |
| OpenAI GPT | `OPENAI_API_KEY` | Optional* | Good alternative |
| Google Gemini | `GOOGLE_API_KEY` | Optional* | Experimental |

*At least one LLM provider required for production. System runs in mock mode if none provided.

### Research & Data Providers (all optional)

| Provider | Environment Variable | Fallback |
|----------|---------------------|----------|
| Ahrefs API | `AHREFS_API_KEY` | Mock SERP data |
| SerpAPI | `SERPAPI_KEY` | Mock search results |

### Infrastructure (all optional)

| Service | Environment Variable | Default |
|---------|---------------------|---------|
| Database | `DATABASE_URL` | SQLite (local file) |
| Redis Cache | `REDIS_URL` | No caching |

## Usage Examples

### Example 1: Initialize LLM Client

```python
from config.api_keys import api_keys, APIKeyType

# Check what providers are available
available = api_keys.get_available_llm_providers()
# Returns: ["anthropic", "openai"]

# Use first available provider
if "anthropic" in available:
    key = api_keys.get_key(APIKeyType.ANTHROPIC)
    import anthropic
    client = anthropic.Anthropic(api_key=key)
```

### Example 2: Conditional Feature Enabling

```python
from config.api_keys import api_keys, APIKeyType

class ResearchService:
    def __init__(self):
        self.use_real_data = api_keys.has_key(APIKeyType.AHREFS)

    def fetch_serp(self, query: str):
        if self.use_real_data:
            # Use real Ahrefs API
            api_key = api_keys.get_key(APIKeyType.AHREFS)
            return self._fetch_from_ahrefs(query, api_key)
        else:
            # Fallback to mock data
            return self._generate_mock_serp(query)
```

### Example 3: Status Check in Health Endpoint

```python
from fastapi import FastAPI
from config.api_keys import api_keys

app = FastAPI()

@app.get("/health/keys")
def api_key_status():
    """Check which API keys are configured"""
    return {
        "status": "ok",
        "keys": api_keys.get_status(),
        "llm_providers": api_keys.get_available_llm_providers()
    }
```

## Validation

The `APIKeyManager` automatically validates keys on initialization:

1. **Required Keys**: System fails to start if missing
2. **Optional Keys**: Warning logged but system continues
3. **LLM Providers**: At least one must be configured (warning if none)

```python
# This happens automatically on import
from config.api_keys import api_keys

# Keys are loaded and validated
# Missing required keys raise ValueError
# Missing optional keys log warnings
```

## Adding New API Keys

### Step 1: Add to APIKeyType Enum

```python
class APIKeyType(Enum):
    # ... existing keys ...
    MY_NEW_SERVICE = "my_service"
```

### Step 2: Add Configuration

```python
class APIKeyManager:
    KEY_CONFIGS = {
        # ... existing configs ...
        APIKeyType.MY_NEW_SERVICE: APIKeyConfig(
            name="My New Service",
            env_var="MY_SERVICE_API_KEY",
            required=False,
            description="Description of what this key is for"
        ),
    }
```

### Step 3: Add Convenience Function (optional)

```python
def get_my_service_key() -> Optional[str]:
    """Get My Service API key"""
    return api_keys.get_key(APIKeyType.MY_NEW_SERVICE)
```

### Step 4: Update .env.template

```bash
# My New Service
# Get your key at: https://example.com/
MY_SERVICE_API_KEY=
```

## Security Best Practices

1. **Never commit .env file**
   - `.env` is in `.gitignore`
   - Only commit `.env.template`

2. **Rotate keys regularly**
   - Update keys in `.env` file
   - Restart application to load new keys

3. **Use environment variables in production**
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   export OPENAI_API_KEY=sk-...
   # Application reads from environment
   ```

4. **Minimal permissions**
   - Use API keys with minimal required permissions
   - Separate keys for dev/staging/production

5. **Monitor usage**
   - Check API key usage dashboards
   - Set up billing alerts
   - Rotate if suspicious activity detected

## Troubleshooting

### "No LLM providers available" Warning

**Cause:** No LLM provider API keys configured

**Solution:**
1. Add at least one LLM key to `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```
2. Restart application

### "Missing required API keys" Error

**Cause:** A required key (if any) is not set

**Solution:**
1. Check which key is missing in error message
2. Add to `.env` file
3. Restart application

### Key Not Loading

**Cause:** Environment variable not set or `.env` file not found

**Solution:**
1. Verify `.env` file exists in project root
2. Check variable name matches exactly
3. No spaces around `=` in `.env`:
   ```bash
   # Correct:
   ANTHROPIC_API_KEY=sk-ant-...

   # Wrong:
   ANTHROPIC_API_KEY = sk-ant-...  # ← extra spaces
   ```

### Check Current Status

```bash
# Method 1: Run manager directly
python config/api_keys.py

# Method 2: In Python
python -c "from config.api_keys import api_keys; api_keys.print_status()"

# Method 3: Check API endpoint
curl http://localhost:8000/health/keys
```

## Migration from Old System

If you were previously using API keys directly from `os.getenv()`:

**Before:**
```python
import os
anthropic_key = os.getenv('ANTHROPIC_API_KEY')
if anthropic_key:
    client = anthropic.Anthropic(api_key=anthropic_key)
```

**After:**
```python
from config.api_keys import get_anthropic_key

anthropic_key = get_anthropic_key()
if anthropic_key:
    client = anthropic.Anthropic(api_key=anthropic_key)
```

Benefits:
- ✅ Centralized validation
- ✅ Type safety
- ✅ Better error messages
- ✅ Status reporting
- ✅ Consistent access pattern

---

**Last Updated:** 2025-11-19
**Maintainer:** BACOWR Development Team
