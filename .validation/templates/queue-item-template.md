# Validation Queue Item: [Feature Name]

**Submitted By**: Chat A (Development Lab)
**Date**: YYYY-MM-DD
**Priority**: [High / Medium / Low]
**Estimated Test Time**: [15 mins / 30 mins / 1 hour / 2+ hours]

---

## 📋 Feature Overview

**Feature Name**: [Descriptive name]

**Purpose**: [What problem does this solve?]

**User Story**:
> As a [SEO professional / user], I want [feature] so that [benefit].

**Scope**:
- [What's included]
- [What's included]
- [What's NOT included]

---

## 🎯 Test Instructions

**IMPORTANT**: Follow these steps in order. Each step includes expected behavior.

### Prerequisites
Before testing, ensure:
- [ ] Backend is running: `cd api && uvicorn main:app --reload`
- [ ] Frontend is running: `cd frontend && npm run dev` (if applicable)
- [ ] Database is migrated: [migration commands if needed]
- [ ] Test data is loaded: [data setup if needed]

### Step-by-Step Testing

#### Step 1: [Action to perform]
**Instructions**:
1. [Detailed step 1]
2. [Detailed step 2]
3. [Detailed step 3]

**Expected Behavior**:
- [What should happen]
- [What should be displayed]
- [What should be in the response/console]

**Acceptance Criteria**:
- [ ] [Specific criterion 1]
- [ ] [Specific criterion 2]

---

#### Step 2: [Action to perform]
**Instructions**:
1. [Detailed step 1]
2. [Detailed step 2]

**Expected Behavior**:
- [What should happen]

**Acceptance Criteria**:
- [ ] [Specific criterion]

---

#### Step 3: [Edge Case Testing]
**Instructions**:
1. [Test edge case 1: e.g., empty input]
2. [Test edge case 2: e.g., very long input]
3. [Test edge case 3: e.g., special characters]

**Expected Behavior**:
- [How errors should be handled]
- [What validation messages should appear]

**Acceptance Criteria**:
- [ ] [Graceful error handling]
- [ ] [Clear error messages]

---

## 🔍 Test Scenarios

### Scenario 1: Happy Path
**Description**: [Normal user flow]
**Steps**:
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Result**: [What should happen]

---

### Scenario 2: Edge Case - [Name]
**Description**: [Unusual but valid case]
**Steps**:
1. [Step 1]
2. [Step 2]

**Expected Result**: [What should happen]

---

### Scenario 3: Error Case - [Name]
**Description**: [Invalid input or error condition]
**Steps**:
1. [Step 1]
2. [Step 2]

**Expected Result**: [How error should be handled]

---

## 🧪 Test Data

**Sample Input 1**:
```json
{
  "field1": "value1",
  "field2": "value2"
}
```

**Sample Input 2** (Edge case):
```json
{
  "field1": "",
  "field2": null
}
```

**Sample Input 3** (Large dataset):
```json
{
  "items": [
    // Array with 100+ items
  ]
}
```

**Test URLs**:
- Frontend: `http://localhost:3000/path/to/feature`
- Backend API: `http://localhost:8000/api/endpoint`

**Test Credentials** (if needed):
- Username: `test@example.com`
- Password: `test123`

---

## 🔧 Technical Details

### Files Changed
**Backend**:
- `api/routes/[filename].py` - [What changed]
- `api/models/[filename].py` - [What changed]
- `api/schemas/[filename].py` - [What changed]

**Frontend**:
- `frontend/app/[path]/page.tsx` - [What changed]
- `frontend/components/[filename].tsx` - [What changed]
- `frontend/lib/[filename].ts` - [What changed]

**Database**:
- `api/migrations/[version].py` - [Schema changes]

**Configuration**:
- `.env` - [New environment variables if any]

### API Endpoints (if applicable)

#### Endpoint 1
**Method**: `POST`
**Path**: `/api/endpoint-name`
**Request**:
```json
{
  "param1": "string",
  "param2": 123
}
```
**Response** (Success):
```json
{
  "status": "success",
  "data": {
    "result": "value"
  }
}
```
**Response** (Error):
```json
{
  "status": "error",
  "message": "Error description"
}
```

#### Endpoint 2
**Method**: `GET`
**Path**: `/api/endpoint-name/{id}`
**Response**:
```json
{
  "id": 1,
  "field": "value"
}
```

### Database Changes

**New Tables**:
- `table_name` - [Description]
  - Columns: [list columns]

**Modified Tables**:
- `table_name` - [What changed]
  - Added: [columns]
  - Modified: [columns]
  - Removed: [columns]

**Migrations**:
```bash
# Run this to apply database changes
alembic upgrade head
```

---

## 🎯 SEO-Specific Validation

**IMPORTANT**: Ask the user (SEO expert) these questions:

### Content Quality
- [ ] Does the generated content meet SEO standards?
- [ ] Is the content unique and valuable?
- [ ] Are keywords naturally integrated?
- [ ] Is the tone appropriate for backlink content?

### Workflow
- [ ] Does this fit into a typical SEO campaign workflow?
- [ ] Is the process intuitive for SEO professionals?
- [ ] Are there any missing features for real-world use?

### Terminology
- [ ] Is SEO terminology used correctly?
- [ ] Are labels and UI text clear to SEO professionals?
- [ ] Are any terms confusing or misleading?

### Use Case Validation
- [ ] Can this be used in actual SEO campaigns?
- [ ] Does it solve a real SEO pain point?
- [ ] What improvements would make it more useful?

---

## ✅ Acceptance Criteria

**Functional Requirements**:
- [ ] Feature works as described
- [ ] All API endpoints return correct data
- [ ] UI displays data correctly
- [ ] Error handling works properly
- [ ] Input validation prevents bad data

**Non-Functional Requirements**:
- [ ] Performance: API responds in < 2 seconds
- [ ] Performance: UI renders in < 1 second
- [ ] Security: Input is properly validated
- [ ] Security: No SQL injection vulnerabilities
- [ ] UX: Loading states are shown
- [ ] UX: Error messages are clear

**SEO Requirements**:
- [ ] Meets SEO professional's needs
- [ ] Content quality is acceptable
- [ ] Workflow is intuitive
- [ ] Terminology is correct

---

## 🚨 Known Issues / Limitations

**Current Limitations**:
- [Limitation 1 - explain why it exists]
- [Limitation 2 - planned for future?]

**Not Tested Yet**:
- [Feature aspect 1 - should Chat B focus on this]
- [Feature aspect 2]

**Potential Issues to Watch For**:
- [Area that might be problematic]
- [Edge case that needs extra attention]

---

## 📝 Additional Context

### Related Features
- [Feature 1 that this builds upon]
- [Feature 2 that this integrates with]

### Design Decisions
**Why did we implement it this way?**
- Decision 1: [Reason]
- Decision 2: [Reason]

### Future Enhancements
- [Enhancement 1 - not in scope for this validation]
- [Enhancement 2 - planned for later]

---

## 🎨 UI/UX Notes (if applicable)

**Design Expectations**:
- [Layout description]
- [Color scheme]
- [Interactive elements]

**Responsive Behavior**:
- Desktop: [Expected behavior]
- Tablet: [Expected behavior]
- Mobile: [Expected behavior]

**Accessibility**:
- [ ] Keyboard navigation works
- [ ] Screen reader compatible
- [ ] ARIA labels present

---

## 🔐 Security Considerations

**Areas to Test**:
- [ ] Input validation (SQL injection, XSS)
- [ ] Authentication (if required)
- [ ] Authorization (correct permissions)
- [ ] Data sanitization
- [ ] Rate limiting (if applicable)

**Security Requirements**:
- [Requirement 1]
- [Requirement 2]

---

## 📊 Performance Expectations

**Backend**:
- API response time: < 2 seconds
- Database queries: Optimized (no N+1)
- Memory usage: Reasonable

**Frontend**:
- Initial load: < 2 seconds
- Interaction response: < 500ms
- Rendering: Smooth (60fps)

**Load Testing** (if applicable):
- Can handle: [X concurrent users]
- Can process: [Y requests/second]

---

## 🧪 Regression Testing

**Features to Check**:
Make sure this new feature didn't break:
- [ ] [Existing feature 1]
- [ ] [Existing feature 2]
- [ ] [Existing feature 3]

---

## 📸 Visual Reference (if applicable)

**Screenshots** (if Chat A created mockups):
- [Description of screenshot 1]
- [Description of screenshot 2]

**Video Demo** (if applicable):
- [Description of demo video]

---

## 🤝 Chat B - Start Here!

**Quick Start for Chat B**:

1. **Read this entire document** - It contains all test instructions
2. **Set up environment**:
   ```bash
   # Start backend
   cd api && uvicorn main:app --reload

   # Start frontend (new terminal)
   cd frontend && npm run dev
   ```
3. **Follow test instructions** in order (see "Test Instructions" section)
4. **Work WITH the user** - Ask for their SEO perspective (see "SEO-Specific Validation")
5. **Create validation report**:
   ```bash
   cp .validation/templates/validation-report-template.md \
      .validation/reports/[feature-name]-$(date +%Y-%m-%d).md
   ```
6. **Document findings** thoroughly
7. **Move this file to completed**:
   ```bash
   mv .validation/queue/[feature-name].md \
      .validation/queue/completed/
   ```

---

## ❓ Questions for Chat B

If anything is unclear, these might help:
- **What does this feature do?** See "Feature Overview"
- **How do I test it?** See "Test Instructions"
- **What should I focus on?** See "Acceptance Criteria" and "SEO-Specific Validation"
- **What test data should I use?** See "Test Data"
- **What API endpoints exist?** See "Technical Details > API Endpoints"

---

## 📞 Need Help?

If you're stuck:
1. Read `.validation/README.md` for system overview
2. Check `.validation/SETUP_CHAT_B.md` for Chat B guidelines
3. Ask the user for clarification
4. Review related files in the "Files Changed" section

---

*Queue item submitted by Chat A on YYYY-MM-DD*
*Priority: [High/Medium/Low] | Estimated test time: [time]*
