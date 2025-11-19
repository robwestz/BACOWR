# PR #18 Gemini Fixes - Quick Checklist

## 🔥 Critical (Do First)

- [ ] **Fix 1** - Add `joinedload(BatchReviewItem.job)` in batch_review.py ~line 199
- [ ] **Fix 2** - Remove N+1 loop in batches.py ~line 191-201
- [ ] **Fix 3** - Fix bare except in audit.py middleware ~line 73-87
- [ ] **Fix 4** - Use `rate_limit_error_handler` in rate_limit.py
- [ ] **Fix 5** - Replace Python aggregation with SQL in audit routes

## 🟡 Important (Do Second)

- [ ] **Fix 6** - Change `status_code` to Integer + migration
- [ ] **Fix 7** - Change `duration_ms` to Integer + migration
- [ ] **Fix 8** - Fix bare except in audit routes ~line 340-345
- [ ] **Fix 9** - Remove or use `get_rate_limit_for_env()`
- [ ] **Fix 10** - Remove duplicate Batch query in batches.py ~line 125-137

## ✅ After All Fixes

- [ ] Run tests: `pytest tests/e2e/ tests/test_batches.py tests/test_audit.py -v`
- [ ] Test batch with 100+ items (should be <500ms)
- [ ] Test audit stats with 10k+ logs (should be <1s)
- [ ] Verify rate limit returns JSON
- [ ] Check SQLAlchemy logs for N+1 queries (should be gone)

## 📝 Notes

- Full details in `PR18_GEMINI_FIXES.md`
- Apply fixes in order shown in main doc
- Create database migration for Fix 6-7
- Test after each fix

**Estimated total time:** 45-60 minutes
