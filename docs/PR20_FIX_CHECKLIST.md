# PR #20 Gemini Fixes - Quick Checklist

## 🟡 Documentation Fixes (All Medium Priority)

- [ ] **Fix 1** - Pagination: Make cursor vs offset consistent in api_reference.md
- [ ] **Fix 2** - Auth: Show JWT as primary, API key as legacy in all examples
- [ ] **Fix 3** - Schema: Add `idempotency_key` field to Job Create schema
- [ ] **Fix 4** - Diagrams: Fix QC→CMS connection in system_architecture.md
- [ ] **Fix 5** - State Machine: Ensure rescue flow consistent across diagrams
- [ ] **Fix 6** - Roadmap: Move implemented features from Backlog to Implemented
- [ ] **Fix 7** - Duplicates: Remove SEO Campaign Manager from Incubator (keep in Roadmap)

## ✅ After All Fixes

- [ ] Review all API examples for consistency
- [ ] Verify Mermaid diagrams render correctly
- [ ] Check no contradictions remain
- [ ] Cross-reference with actual code implementation
- [ ] Verify roadmap accurately reflects shipped features

## 📝 Files to Edit

- `docs/architecture/api_reference.md` - Fixes 1, 2, 3
- `docs/architecture/system_architecture.md` - Fixes 4, 5
- `docs/future.md` - Fixes 6, 7

## 📊 Impact

- **Risk:** None (documentation only)
- **Urgency:** Medium (improves clarity, prevents confusion)
- **Time:** 30 minutes total
- **Dependencies:** None

## 🔧 Quick Test

After fixes, verify:
```bash
# Check Mermaid diagrams render
# Use: https://mermaid.live or VS Code Mermaid extension

# Check for contradictions
grep -r "pagination" docs/architecture/
grep -r "JWT\|API key" docs/architecture/
grep -r "idempotency" docs/architecture/

# Verify roadmap sections don't overlap
grep -r "SEO Campaign Manager" docs/future.md
```

**Full details in:** `PR20_GEMINI_FIXES.md`
**Estimated total time:** 30 minutes
