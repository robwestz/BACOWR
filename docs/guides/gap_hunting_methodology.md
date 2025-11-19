# Gap Hunting Methodology

**Version:** 1.0.0
**Last Updated:** 2025-11-19
**Purpose:** Systematic approach to discovering blind spots, gaps, and improvement opportunities in BACOWR

---

## Philosophy

> **"You can't fix what you don't know is broken."**

Gap hunting is the practice of **actively seeking** what's missing, incomplete, or could be better. It's not about finding bugs (that's testing) - it's about finding **missing functionality, unclear processes, and suboptimal designs**.

**Key Principle:** Assume there are always gaps. The question is not "if" but "where" and "how critical".

---

## The 7 Gap Categories

Every gap falls into one of these categories:

1. **Architecture Gaps** - Missing or incomplete system structure
2. **Feature Gaps** - Functionality that should exist but doesn't
3. **Quality Gaps** - Code/prompts/UX that work but could be better
4. **Process Gaps** - Missing workflows or unclear procedures
5. **Knowledge Gaps** - Undocumented decisions or tribal knowledge
6. **Integration Gaps** - Disconnected modules or poor handoffs
7. **Future Gaps** - Things that will become problems as system scales

---

## Gap Hunting Techniques

### Technique 1: The Dependency Walk

**Goal:** Find gaps by following dependencies

**Steps:**
1. Open `bacowr_master_orchestration_checklist.json`
2. Pick a module with `depends_on` field
3. For each dependency:
   - Is it implemented?
   - Is it complete?
   - Is the interface clear?
   - Does data flow cleanly?

**Example:**
```
Module G (QA) depends on:
- Module B (Models) ← Are QC models complete?
- Module F (Storage) ← Can we persist QA state?

Gap found: Module F only has file storage, no DB persistence
→ Add to Gap Analysis as "Database integration" (P0)
```

**Common Gaps Found:**
- Missing prerequisite modules
- Circular dependencies
- Unclear interfaces
- Data format mismatches

---

### Technique 2: The Error Path Analysis

**Goal:** Find gaps by imagining what can go wrong

**Steps:**
1. Pick a critical user flow (e.g., "Generate article")
2. For each step, ask "What if this fails?"
3. Check if failure is handled gracefully
4. Check if user gets actionable error message

**Example:**
```
User flow: Generate article
1. Preflight fetches HTML
   → What if URL is 404?
   → What if HTML is malformed?
   → What if site blocks scraping?

Gap found: No retry logic for transient network errors
→ Add to Gap Analysis as "Failure recovery" (P3)
```

**Common Gaps Found:**
- Missing error handling
- Non-actionable error messages
- Silent failures
- No fallback strategies

---

### Technique 3: The "But What About...?" Game

**Goal:** Find edge cases and assumptions

**Steps:**
1. Read a piece of code or documentation
2. Ask "But what about...?" repeatedly
3. Keep going until you find an unanswered question

**Example:**
```
Code: "Generate article with anchor text"

But what about... emoji in anchor text?
But what about... anchor text > 200 characters?
But what about... anchor text in non-Latin script?
But what about... anchor text with HTML entities?

Gap found: No input validation on anchor text length
→ Add to Gap Analysis as "Input validation" (P2)
```

**Common Gaps Found:**
- Edge cases
- Invalid input handling
- Assumption violations
- Internationalization issues

---

### Technique 4: The Competitive Tear-Down

**Goal:** Find gaps by comparing to competitors

**Steps:**
1. List 3-5 competitor products (Clearscope, MarketMuse, Surfer SEO)
2. For each competitor feature:
   - Does BACOWR have this?
   - If yes, is it as good?
   - If no, should it?
3. Document justified gaps vs. missing features

**Example:**
```
Competitor: Clearscope has real-time content grading

BACOWR: QC runs only after article is complete

Question: Should we have real-time QC feedback during writing?

Gap found: No real-time feedback during article generation
→ Add to future.md as "Real-time QC suggestions" (Incubator)
```

**Common Gaps Found:**
- Missing features competitors have
- Worse UX than market standard
- Opportunities for differentiation

---

### Technique 5: The Scale Test

**Goal:** Find gaps that appear at scale

**Steps:**
1. Imagine 10x current usage
2. What breaks? What slows down?
3. Imagine 100x current usage
4. What's impossible?

**Example:**
```
Current: 10 articles/day
At 100 articles/day: File storage might slow down
At 1000 articles/day: File storage is untenable, need DB

Gap found: No database layer
→ Add to Gap Analysis as "Database integration" (P0)
```

**Common Gaps Found:**
- Performance bottlenecks
- Storage limitations
- Cost explosions
- Operational overhead

---

### Technique 6: The User Journey Map

**Goal:** Find UX gaps by simulating user experience

**Steps:**
1. Define a user persona (e.g., "Anna, SEO specialist, non-technical")
2. Walk through their entire journey
3. Note every friction point, confusion, or delay
4. Check if each step meets UX Quality Principles

**Example:**
```
Anna's journey:
1. Opens BACOWR → Sees dashboard ✅
2. Clicks "New Job" → Form has 12 fields ❌ (too complex)
3. Fills form → No validation until submit ❌
4. Submits → Spins for 45 seconds with no feedback ❌
5. Sees "Job failed: SERP_ERROR" → What does that mean? ❌

Gaps found:
- Form too complex (missing Quick Start widget)
- No real-time validation
- No progress feedback
- Non-actionable error messages

→ Add all to Gap Analysis (P1 - UX critical)
```

**Common Gaps Found:**
- Confusing UX flows
- Missing feedback
- Non-intuitive terminology
- Inaccessibility

---

### Technique 7: The "Day 2" Simulation

**Goal:** Find operational gaps that appear post-launch

**Steps:**
1. Imagine BACOWR has been running for 3 months
2. What maintenance tasks are needed?
3. What monitoring/alerting exists?
4. What happens when things go wrong?

**Example:**
```
Day 2 scenarios:
- Ahrefs API key expires → How do we know? How do we fix?
- LLM costs spike → Do we get alerted? Can we see why?
- User reports bad article → Can we debug? Do we have logs?
- New LLM model releases → How do we upgrade? Test? Roll back?

Gaps found:
- No monitoring/alerting
- No cost spike detection
- Logs not centralized
- No rollback strategy

→ Add to Gap Analysis as "Observability" (P3)
```

**Common Gaps Found:**
- Missing monitoring
- No alerting
- Poor debuggability
- Difficult upgrades

---

## Gap Documentation Template

When you find a gap, document it consistently:

```markdown
### [Category] Gap: [Short Description]

- **Current**: [What exists today]
- **Gap**: [What is missing or incomplete]
- **Risk**: [What could go wrong - be specific]
- **Impact**: [High/Medium/Low]
- **Likelihood**: [High/Medium/Low (of risk occurring)]
- **User Impact**: [Who is affected and how]
- **Technical Debt**: [Is this accumulating debt?]
- **Mitigation**: [How to fix - be concrete]
- **Owner**: [Which module (A-Q)]
- **Estimated Effort**: [Days of work]
- **Priority**: [P0/P1/P2/P3/P4]
- **Dependencies**: [What must exist first]
- **Discovered By**: [Technique used]
- **Date**: [YYYY-MM-DD]
```

**Example:**
```markdown
### Architecture Gap: No Database Layer

- **Current**: File-based storage in storage/output/
- **Gap**: No persistent database for multi-user scenarios
- **Risk**: Cannot scale beyond single-user sessions; data loss on file corruption; slow queries
- **Impact**: High (blocks v1.5 hosted app)
- **Likelihood**: High (as soon as we add users)
- **User Impact**: All users - cannot use hosted version
- **Technical Debt**: Yes - accumulating with every file-based feature
- **Mitigation**: Implement PostgreSQL layer (Module F2)
  1. Design schema (jobs, users, backlinks, QC reports)
  2. Add SQLAlchemy models
  3. Create migration scripts
  4. Update storage interfaces
  5. Migrate existing file data
- **Owner**: Module F2
- **Estimated Effort**: 2-3 days
- **Priority**: P0
- **Dependencies**: None (can start immediately)
- **Discovered By**: Dependency Walk (Module H needs user DB)
- **Date**: 2025-11-19
```

---

## Gap Hunting Schedule

### Per-Session (Every LLM session)
- Run **1-2 quick techniques** (5-10 min)
- Document any gaps found
- Add to vision doc if significant

### Weekly (Or every 5 sessions)
- Run **full gap hunt** (1-2 hours)
- Use 3-4 different techniques
- Update Risk Prioritization Matrix
- Create action items for P0/P1 gaps

### Monthly (Or every 20 sessions)
- **Comprehensive audit** using all 7 techniques
- Compare to previous audit (trend analysis)
- Update roadmap based on findings
- Archive low-priority gaps

---

## Gap Hunting Anti-Patterns

**❌ Don't:**
1. **Hunt gaps without documenting them** - If you don't write it down, it's lost
2. **Find gaps and immediately implement** - Prioritize first, implement later
3. **Assume gaps are bugs** - Gaps are missing features/structure, bugs are broken features
4. **Blame others for gaps** - Gaps are inevitable, blame is unproductive
5. **Hunt gaps without context** - Read vision doc first, understand what's intentionally not built
6. **Document vague gaps** - "Code quality is bad" is useless; "No type hints on 40% of functions" is actionable
7. **Find only your domain's gaps** - A backend dev should also find UX gaps

**✅ Do:**
1. **Document every gap, even small ones** - Pattern emerges from accumulation
2. **Prioritize ruthlessly** - Not all gaps need fixing
3. **Distinguish between gap and enhancement** - Gap = should exist; Enhancement = nice-to-have
4. **Look for systemic issues** - 5 small gaps might be 1 architectural gap
5. **Celebrate gap discovery** - Finding gaps is success, not failure
6. **Update vision doc immediately** - Don't let gap knowledge decay
7. **Use multiple techniques** - Each technique finds different gap types

---

## Gap Metrics

Track these over time:

| Metric | Definition | Target |
|--------|------------|--------|
| **Total Gaps** | Open gaps in vision doc | Decreasing over time |
| **P0 Gaps** | Critical gaps blocking users | 0 before launch |
| **P1 Gaps** | High-priority gaps | < 5 |
| **Gap Velocity** | Gaps closed per week | > Gaps discovered |
| **Gap Age** | Avg days since discovery | < 30 days for P0/P1 |
| **Gap Discovery Rate** | New gaps per session | Stable or decreasing |

**Healthy Pattern:**
- Early: High discovery rate (you're learning the system)
- Mid: Discovery rate plateaus (system is well-understood)
- Late: Discovery rate low (system is mature)

**Unhealthy Pattern:**
- Discovery rate keeps increasing (system is accumulating debt)
- P0 gaps not decreasing (not prioritizing correctly)
- Old gaps (>90 days) accumulating (execution problem)

---

## Example: Complete Gap Hunt Session

**Technique Used:** Dependency Walk + Error Path Analysis

**Module Examined:** Module G (QA & Status)

**Dependencies:**
- Module B (Models) - ✅ Complete
- Module F (Storage) - ⚠️ Partial (file-only)
- Module E (Orchestrator) - ✅ Complete

**Error Paths:**
1. QC blocks article → ✅ Handled (status: BLOCKED)
2. QC system crashes → ❌ Not handled (no try/catch in quality_controller.py)
3. QC thresholds invalid → ❌ No validation of config/thresholds.yaml
4. Multiple QC runs on same article → ❌ No idempotency check

**Gaps Found:**

1. **Process Gap: QC Error Handling**
   - Current: QC failures crash entire job
   - Gap: No error recovery in QC system
   - Risk: Jobs fail silently, users see generic error
   - Impact: Medium
   - Priority: P2
   - Effort: 1 day
   - Mitigation: Add try/catch, return QCReport with error state

2. **Quality Gap: No Config Validation**
   - Current: thresholds.yaml loaded without validation
   - Gap: Invalid config can crash system
   - Risk: Typo in YAML crashes all jobs
   - Impact: High
   - Priority: P1
   - Effort: 0.5 days
   - Mitigation: Add JSON schema validation for config files

3. **Feature Gap: No QC Audit Trail**
   - Current: Only latest QC report is kept
   - Gap: Can't see QC history for an article
   - Risk: Can't debug "why did QC pass yesterday but fail today?"
   - Impact: Low
   - Priority: P3
   - Effort: 1 day
   - Mitigation: Store QC reports with timestamp in DB (needs F2)

**Action Items:**
- [ ] Add to vision doc Gap Analysis
- [ ] Create GitHub issues for P1/P2 gaps
- [ ] Add P3 gap to future.md Backlog

**Time Taken:** 45 minutes

**Gaps Per Hour:** 4 gaps (good productivity)

---

## Gap Hunting Checklist

Use this before ending a gap hunt session:

- [ ] I used at least 2 different techniques
- [ ] I documented all gaps using the template
- [ ] I prioritized gaps (P0-P4)
- [ ] I estimated effort for each gap
- [ ] I assigned owner modules
- [ ] I updated vision doc Gap Analysis
- [ ] I updated Risk Prioritization Matrix
- [ ] I created action items for P0/P1 gaps
- [ ] I added P2-P4 gaps to future.md if appropriate
- [ ] I committed changes to vision doc

---

**End of Gap Hunting Methodology**

Remember: **Finding gaps is not failure - it's progress toward a more complete system.**

*"The eye sees only what the mind is prepared to comprehend."* — Robertson Davies

Use this methodology to prepare your mind to see what's missing.
