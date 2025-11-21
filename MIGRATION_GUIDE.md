# BACOWR Entry Point Consolidation - Migration Guide

## Overview

BACOWR now has a **single, unified entry point** (`run_bacowr.py`) that replaces multiple scattered startup scripts. This makes the project easier to use and maintain.

## What Changed?

### New Entry Point

**One script to rule them all:** `run_bacowr.py`

```bash
# Development mode (mock data, no API keys needed)
python run_bacowr.py --mode dev --publisher example.com --target https://example.com --anchor "test"

# Production mode (real LLM, requires API keys)
python run_bacowr.py --mode prod --publisher example.com --target https://example.com --anchor "test"

# Interactive demo
python run_bacowr.py --mode demo
```

### Simplified Startup Scripts

`start_bacowr.sh` and `start_bacowr.ps1` are now simple wrappers that:
- Automatically create and activate virtual environment
- Install dependencies if needed
- Copy .env.example to .env if needed
- Call run_bacowr.py with your preferred mode

```bash
# Unix/Linux/macOS
./start_bacowr.sh              # Runs in dev mode
./start_bacowr.sh --mode prod  # Runs in production mode

# Windows
.\start_bacowr.ps1              # Runs in dev mode
.\start_bacowr.ps1 -Mode prod   # Runs in production mode
```

### New Verification Script

`verify_startup.py` - Smoke test to verify installation:

```bash
python verify_startup.py
```

Checks:
- Python version
- Required dependencies
- Project structure
- Configuration files
- Module imports
- Basic functionality

## Migration Path

### If you were using `main.py`:

**Before:**
```bash
python main.py --publisher example.com --target https://example.com --anchor "test" --mock
```

**Now (recommended):**
```bash
python run_bacowr.py --mode dev --publisher example.com --target https://example.com --anchor "test"
```

**Or (still works):**
```bash
python main.py --publisher example.com --target https://example.com --anchor "test" --mock
```

### If you were using `production_main.py`:

**Before:**
```bash
python production_main.py --publisher example.com --target https://example.com --anchor "test" --llm anthropic
```

**Now (recommended):**
```bash
python run_bacowr.py --mode prod --publisher example.com --target https://example.com --anchor "test" --llm anthropic
```

**Or (still works):**
```bash
python production_main.py --publisher example.com --target https://example.com --anchor "test" --llm anthropic
```

### If you were using `quickstart.py`:

**Before:**
```bash
python quickstart.py
```

**Now (recommended):**
```bash
python run_bacowr.py --mode demo --demo-type quickstart
```

**Or (still works):**
```bash
python quickstart.py
```

### If you were using `interactive_demo.py`:

**Before:**
```bash
python interactive_demo.py
```

**Now (recommended):**
```bash
python run_bacowr.py --mode demo --demo-type interactive
```

**Or (still works):**
```bash
python interactive_demo.py
```

## Backward Compatibility

All legacy scripts (`main.py`, `production_main.py`, `quickstart.py`, `interactive_demo.py`, etc.) **still work** and are marked with deprecation notices. You can continue using them while you migrate.

## Docker Changes

### Dockerfile

The default CMD now runs `run_bacowr.py --mode prod`. You can override:

```bash
# Run in dev mode
docker run bacowr python run_bacowr.py --mode dev --publisher example.com --target https://example.com --anchor "test"

# Run API server
docker run bacowr python -m uvicorn api.app.main:app --host 0.0.0.0 --port 8000
```

### docker-compose.yml

The compose file now:
- Loads `.env` file automatically
- Mounts config as read-only
- Uses environment variables from .env for all settings
- Runs API server by default (overrides Dockerfile CMD)

```bash
# Copy .env.example to .env first
cp .env.example .env

# Start services
docker-compose up --build
```

## Environment Variables

The `.env.example` file has been simplified with:
- Clear comments for each setting
- Links to get API keys
- Better defaults for development

**Development:** You don't need API keys for dev mode (uses mock data)
**Production:** At least one LLM API key is required

## Benefits

### For New Users
- One simple entry point
- Clear modes (dev/prod/demo)
- Automatic environment setup with startup scripts
- Better error messages

### For Existing Users
- Backward compatible
- Clearer project structure
- Easier to maintain
- Better documentation

### For CI/CD
- Single entry point to test
- Verification script for smoke tests
- Consistent interface

## Getting Help

If you encounter issues:

1. Run verification script:
   ```bash
   python verify_startup.py
   ```

2. Check your .env file:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. Use the help flag:
   ```bash
   python run_bacowr.py --help
   ```

4. Check the documentation:
   - [README.md](README.md) - Complete overview
   - [QUICKSTART_LOCAL.md](QUICKSTART_LOCAL.md) - Local setup
   - [PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md) - Production usage

## Questions?

Open an issue on GitHub: https://github.com/robwestz/BACOWR/issues

---

**Note:** Legacy scripts will be maintained for backward compatibility but won't receive new features. Please migrate to `run_bacowr.py` for the best experience.
