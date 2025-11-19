# PR #23 Gemini Fixes - Quick Checklist

## 🔥 High Priority (Do First)

- [ ] **Fix 1** - Remove sys.path manipulation in:
  - `api/app/routes/export.py` (lines 16-18)
  - `examples/export_integration_example.py` (lines 13-15)
  - Create `setup.py` and install with `pip install -e .`

## 🟡 Medium Priority (Do Second)

- [ ] **Fix 2** - Remove redundant PrometheusMiddleware class
  - Delete middleware class in `api/app/middleware/prometheus.py` (lines 105-137)
  - Remove from `api/app/main.py`
  - Keep only Instrumentator

- [ ] **Fix 3** - Consistent auth manager initialization
  - Create singleton pattern or use FastAPI Depends
  - Apply to all export endpoints

- [ ] **Fix 4** - Replace print() with logging
  - `api/app/routes/export.py`
  - `src/export/google_sheets.py`
  - `src/export/google_docs.py`
  - `examples/export_integration_example.py`

- [ ] **Fix 5** - Pin dependencies with upper bounds in `requirements.txt`
  - Google Workspace libs: `>=X.0.0,<Y.0.0`
  - Prometheus libs: `>=X.0.0,<Y.0.0`

## ✅ After All Fixes

- [ ] Test imports work: `python -c "from src.export.google_sheets import GoogleSheetsExporter"`
- [ ] Run export tests: `pytest tests/test_export*.py -v`
- [ ] Check Prometheus metrics: Visit `/metrics`, verify no duplicates
- [ ] Test Google Sheets export (real credentials)
- [ ] Test Google Docs export (real credentials)
- [ ] Verify logging (no print statements)
- [ ] Fresh install test: `pip install -r requirements.txt`

## 📝 Files to Edit

- `setup.py` - Create new
- `requirements.txt` - Fix dependency pins
- `api/app/routes/export.py` - Fixes 1, 3, 4
- `api/app/middleware/prometheus.py` - Fix 2
- `api/app/main.py` - Fix 2
- `src/export/google_sheets.py` - Fix 4
- `src/export/google_docs.py` - Fix 4
- `examples/export_integration_example.py` - Fixes 1, 4

## 📊 Priority & Impact

| Fix | Priority | Impact | Time |
|-----|----------|--------|------|
| Fix 1 | 🔥 High | Major | 15m |
| Fix 2 | 🟡 Medium | Cleanup | 5m |
| Fix 3 | 🟡 Medium | Better | 10m |
| Fix 4 | 🟡 Medium | Professional | 10m |
| Fix 5 | 🟡 Medium | Stability | 5m |

**Total time:** ~45 minutes

## 🔧 Quick Start

```bash
# 1. Checkout PR branch
git checkout claude/bacowr-vision-quality-01CDULfvDikphGFJTmBQv4B2

# 2. Follow PR23_GEMINI_FIXES.md step by step

# 3. Test
pytest tests/ -v

# 4. Commit
git commit -am "fix: Apply Gemini code review fixes for PR #23"
```

**Full details in:** `docs/PR23_GEMINI_FIXES.md`
