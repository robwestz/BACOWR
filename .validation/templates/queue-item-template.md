# Ready for Validation: [Feature Name]

**Date Added:** YYYY-MM-DD
**Chat A:** Main Build Orchestrator
**Implemented by:** Chat A
**Assigned to:** Chat B (Test & Validation Lab)

---

## 📦 Feature Summary

Brief description of what was built.

---

## 🎯 What Needs Validation

### Functionality to Test
- [ ] Feature aspect 1
- [ ] Feature aspect 2
- [ ] Edge case handling
- [ ] Error handling
- [ ] Performance
- [ ] User experience

### SEO Expert Input Needed
**Questions for the user:**
1. Does this solve the SEO problem we discussed?
2. Is the data presented in a useful way?
3. Are there missing features that would make this more useful?
4. How does this fit into your SEO workflow?

---

## 🔧 Technical Details

### Backend Changes
- **Files modified:** `api/app/routes/file.py`, `api/app/models/file.py`
- **New endpoints:** `POST /api/v1/feature`, `GET /api/v1/feature/{id}`
- **Database changes:** New table/columns
- **Dependencies added:** None

### Frontend Changes
- **Files modified:** `frontend/src/app/page.tsx`, `frontend/src/components/file.tsx`
- **New components:** `FeatureCard`, `FeatureModal`
- **New API integration:** `featureAPI.create()`, `featureAPI.get()`
- **New routes:** `/feature/new`, `/feature/{id}`

### Documentation
- **Added:** `docs/FEATURE_GUIDE.md`
- **Updated:** `PROJECT_CONTEXT.md`, `README.md`

---

## 🚀 How to Test

### Prerequisites
1. Backend running: `cd api && uvicorn app.main:socket_app --reload`
2. Frontend running: `cd frontend && npm run dev`
3. Database initialized with test data
4. Required API keys configured (if applicable)

### Test Steps

**Backend Testing:**
```bash
# Test endpoint 1
curl -X POST http://localhost:8000/api/v1/feature \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'

# Test endpoint 2
curl http://localhost:8000/api/v1/feature/123
```

**Frontend Testing:**
1. Navigate to http://localhost:3000/feature
2. Click "Create New Feature"
3. Fill in the form
4. Submit and verify response
5. Check that data displays correctly

**Integration Testing:**
1. Create item from frontend
2. Verify it appears in backend
3. Verify it appears in database
4. Test error cases (missing data, invalid input)

### Edge Cases to Test
- [ ] Empty/null values
- [ ] Very long inputs
- [ ] Special characters
- [ ] Rate limiting (if applicable)
- [ ] Permission errors
- [ ] Network errors

---

## 📊 Expected Behavior

**Success case:**
1. User performs action X
2. System responds with Y
3. Data is saved/displayed as Z

**Error cases:**
1. Invalid input → Show error message "..."
2. Network failure → Show retry option
3. Permission denied → Show appropriate message

---

## 🔗 Related

**Commits:**
- `abc123` - Main implementation
- `def456` - Bug fixes

**Pull Request:** (if applicable)
**Related features:** Feature X, Feature Y

**Documentation:**
- `docs/FEATURE_GUIDE.md`
- `API_BACKEND_COMPLETE.md` (section X)

---

## 💬 Notes from Chat A

Any important context, known limitations, or areas that need special attention:

- Note 1: This feature integrates with X, so test that integration
- Note 2: Known limitation is Y, will be fixed in future
- Note 3: Special attention needed on Z

---

## ✅ Ready for Testing

This feature is complete and ready for validation by Chat B + SEO Expert.

**Status:** 🟢 Ready
**Priority:** High/Medium/Low
**Expected validation time:** 30min / 1hr / 2hrs

---

**Created by:** Chat A (Main Build Orchestrator)
**Date:** YYYY-MM-DD
