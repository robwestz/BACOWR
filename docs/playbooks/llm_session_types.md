# LLM Session Playbooks

**Version:** 1.0.0
**Last Updated:** 2025-11-19
**Purpose:** Concrete step-by-step guides for different types of LLM sessions in BACOWR

---

## Overview

This document provides **tactical playbooks** for LLM sessions. Each playbook is a checklist-driven workflow optimized for specific tasks.

**When to use this document:**
- You're starting a new BACOWR session and need a structured approach
- You want to ensure consistency across sessions
- You need to train a new team member (human or LLM) on BACOWR workflows

**Related documents:**
- `bacowr_vision_and_quality.md` - Strategic vision and quality principles
- `future.md` - Idea incubator
- `bacowr_master_orchestration_checklist.json` - Master task list

---

## Table of Contents

1. [Feature Implementation Session](#feature-implementation-session)
2. [Bug Fix Session](#bug-fix-session)
3. [Quality Audit Session](#quality-audit-session)
4. [Refactoring Session](#refactoring-session)
5. [Documentation Session](#documentation-session)
6. [Idea Generation Session](#idea-generation-session)
7. [Module Integration Session](#module-integration-session)
8. [Performance Optimization Session](#performance-optimization-session)

---

## Feature Implementation Session

**Goal:** Implement a new feature from idea to production-ready code

**Estimated Time:** 2-8 hours depending on complexity

### Pre-Session (5-10 min)

- [ ] Read `bacowr_vision_and_quality.md` sections:
  - Overview & Purpose
  - Quality Charter (relevant section: Code, UX, or SEO)
  - Gap Analysis (check if this feature closes a known gap)
- [ ] Read `bacowr_master_orchestration_checklist.json`
  - Identify which module (A-Q) this feature belongs to
  - Check module status and dependencies
- [ ] Check `future.md`
  - Is this feature already in Backlog or Incubator?
  - If yes, read evaluation notes and POC results

### Planning (10-20 min)

- [ ] **Define scope clearly**
  - What problem does this solve?
  - Who is the user? (SEO professional, developer, admin)
  - What is the minimal viable implementation?

- [ ] **Check dependencies**
  - What modules does this depend on?
  - Are those modules in `present` or `partial` status?
  - If dependencies are missing, implement them first or add stubs

- [ ] **Design considerations**
  - Does this fit the Quality Charter principles?
  - Is the UX intuitive for non-technical users?
  - Is the code modular and testable?

- [ ] **Create TodoWrite plan**
  ```
  1. Read existing code in module X
  2. Design interface/schema
  3. Implement core logic
  4. Write tests
  5. Update documentation
  6. Update checklist status
  ```

### Implementation (1-6 hours)

- [ ] **Read existing code first**
  - NEVER create parallel implementations
  - ALWAYS extend existing modules
  - Look for TODOs, stubs, or extension points

- [ ] **Follow Code Quality Principles**
  - ✅ Type hints on all functions
  - ✅ Docstrings (Google style)
  - ✅ Error handling with logging
  - ✅ No hardcoded secrets
  - ✅ Pure functions where possible

- [ ] **Write tests alongside code**
  - Unit tests for business logic
  - Integration tests for API endpoints
  - E2E tests for critical paths
  - Aim for 80%+ coverage on new code

- [ ] **Implement incrementally**
  - Start with simplest case
  - Add complexity gradually
  - Commit after each working increment
  - Don't try to be perfect on first pass

### Testing (30-60 min)

- [ ] **Run existing tests**
  ```bash
  python -m pytest tests/
  ```
  - Ensure you didn't break anything

- [ ] **Test new feature manually**
  - Happy path
  - Edge cases
  - Error cases
  - Performance with realistic data

- [ ] **Test integration with other modules**
  - Does it work with mock data?
  - Does it work with production LLM?
  - Does it work in batch mode?

### Documentation (20-40 min)

- [ ] **Update code documentation**
  - Docstrings for all new functions/classes
  - Inline comments for complex logic
  - Type hints everywhere

- [ ] **Update module guide**
  - If module has a guide (e.g., `PRODUCTION_GUIDE.md`), update it
  - Add usage examples
  - Add troubleshooting section

- [ ] **Update README if user-facing**
  - Add to features list
  - Add usage example
  - Update CLI help text

- [ ] **Update checklist**
  - Mark task as `present` in `bacowr_master_orchestration_checklist.json`
  - Update module status if complete

### Post-Implementation (10-20 min)

- [ ] **Update vision document**
  - If this closes a gap, remove it from Gap Analysis
  - If you discovered new gaps, add them
  - If you learned a new quality principle, add it to Quality Charter

- [ ] **Update future.md**
  - If this was from Backlog, move to Archived/Implemented
  - Add any new ideas that emerged during implementation
  - Update related ideas (e.g., if you built caching, note opportunities to cache more)

- [ ] **Commit with clear message**
  ```
  feat(module): Short description

  - Bullet point of what changed
  - Why it was needed
  - What impact it has

  Closes gap: [gap description if applicable]
  Implements: future.md idea [name]
  ```

- [ ] **Mark TodoWrite as completed**

### Success Criteria

- ✅ All tests pass (existing + new)
- ✅ Feature works in isolation and integrated
- ✅ Documentation is complete
- ✅ Checklist is updated
- ✅ Vision document reflects new state
- ✅ Code follows Quality Charter

---

## Bug Fix Session

**Goal:** Fix a reported bug or discovered issue

**Estimated Time:** 30 min - 4 hours

### Pre-Session (5 min)

- [ ] Read bug report/error message carefully
- [ ] Check if this is a known gap in `bacowr_vision_and_quality.md`
- [ ] Reproduce the bug locally

### Investigation (15-60 min)

- [ ] **Identify root cause**
  - Read execution logs: `storage/output/{job_id}_execution_log.json`
  - Read QC reports if relevant
  - Check relevant module code
  - Add logging if needed

- [ ] **Determine scope**
  - Is this a simple fix or systemic issue?
  - Does it require refactoring?
  - Are other parts of the system affected?

- [ ] **Check for related issues**
  - Grep for similar patterns: `grep -r "error_pattern" src/`
  - Check if tests already cover this (but are failing)

### Fix Implementation (30 min - 2 hours)

- [ ] **Write a failing test first** (TDD)
  - Reproduce bug in test
  - Confirm test fails
  - Fix the bug
  - Confirm test passes

- [ ] **Make minimal change**
  - Fix the root cause, not symptoms
  - Don't refactor unrelated code (unless critical)
  - Keep the diff small

- [ ] **Add defensive checks**
  - Input validation
  - Error handling
  - Logging for future debugging

### Testing (15-30 min)

- [ ] **Run full test suite**
  ```bash
  python -m pytest tests/ -v
  ```

- [ ] **Test the exact scenario from bug report**
  - Use same inputs
  - Verify error is gone
  - Verify output is correct

- [ ] **Test edge cases**
  - What if input is slightly different?
  - What if system is under load?
  - What if external API fails?

### Documentation (10-20 min)

- [ ] **Update Gap Analysis**
  - If this bug revealed a gap, document it
  - Add mitigation strategy

- [ ] **Add to troubleshooting guide**
  - If this is likely to recur, add to relevant guide
  - Include error message and solution

- [ ] **Update tests**
  - Ensure this bug can't happen again
  - Add regression test

### Post-Fix (5-10 min)

- [ ] **Commit with descriptive message**
  ```
  fix(module): Fix [specific bug]

  - Root cause: [explanation]
  - Solution: [what you did]
  - Impact: [who/what was affected]

  Fixes: #issue_number (if applicable)
  ```

- [ ] **Check for similar bugs**
  - Did you find a pattern?
  - Should you proactively fix similar issues?
  - Add to future.md if it's a systemic issue

### Success Criteria

- ✅ Bug is fixed and verified
- ✅ Tests prevent regression
- ✅ Root cause is documented
- ✅ No new bugs introduced

---

## Quality Audit Session

**Goal:** Systematically review BACOWR for quality issues, gaps, and improvement opportunities

**Estimated Time:** 2-4 hours

### Pre-Session (10 min)

- [ ] Read `bacowr_vision_and_quality.md` in full
  - Focus on Quality Charter
  - Review Gap Analysis for known issues
- [ ] Read recent Git history
  ```bash
  git log --oneline -20
  ```
  - What has changed recently?
  - Are there patterns?

### Architecture Audit (30-60 min)

- [ ] **Module consistency**
  - Read `bacowr_master_orchestration_checklist.json`
  - For each module with status `partial`:
    - What's missing?
    - Is it blocking other modules?
    - What's the priority?

- [ ] **Dependency graph**
  - Draw or visualize module dependencies
  - Are there circular dependencies?
  - Are there bottlenecks?

- [ ] **Code organization**
  - Is code in the right modules?
  - Are there parallel implementations?
  - Is there dead code?

### Code Quality Audit (30-60 min)

- [ ] **Run static analysis**
  ```bash
  # Type checking
  mypy src/ --ignore-missing-imports

  # Linting
  pylint src/

  # Code complexity
  radon cc src/ -a
  ```

- [ ] **Review key modules**
  - Pick 3-5 most critical modules (C, D, E, G)
  - Check against Code Quality Principles:
    - ✅ Type hints?
    - ✅ Docstrings?
    - ✅ Error handling?
    - ✅ No hardcoded secrets?
    - ✅ Testability?

- [ ] **Find code smells**
  - Long functions (>50 lines)
  - Deep nesting (>3 levels)
  - Repeated code
  - God objects
  - Tight coupling

### SEO Logic Audit (30-45 min)

- [ ] **Review intent analyzer**
  - Read `src/analysis/intent_analyzer.py`
  - Check against SEO Quality Principles
  - Are edge cases handled?

- [ ] **Review QC system**
  - Read `src/qc/quality_controller.py`
  - Read `config/thresholds.yaml`
  - Are thresholds reasonable?
  - Are there false positives/negatives?

- [ ] **Review prompt engineering**
  - Read prompts in `src/writer/production_writer.py`
  - Check against Prompt Quality Principles:
    - ✅ Clarity?
    - ✅ Explicit constraints?
    - ✅ Context before task?
    - ✅ No unnecessary meta-text?

### UX Audit (20-30 min)

- [ ] **Test happy path**
  - Generate one article via CLI
  - Time it (should be <60 seconds)
  - Is the output clear?

- [ ] **Test error paths**
  - What if URL is invalid?
  - What if API key is missing?
  - What if LLM API fails?
  - Are error messages actionable?

- [ ] **Check frontend (if exists)**
  - Open `http://localhost:3000`
  - Can a non-technical user navigate?
  - Is feedback immediate?

### Operations Audit (20-30 min)

- [ ] **Logging**
  - Grep for logging statements
  - Are critical paths logged?
  - Are logs structured (JSON)?
  - Are secrets scrubbed from logs?

- [ ] **Cost tracking**
  - Check cost calculation logic
  - Is every LLM call tracked?
  - Are costs visible to users?

- [ ] **Failure recovery**
  - What happens if job fails mid-execution?
  - Is state saved?
  - Can jobs be resumed?

### Gap Documentation (30-45 min)

- [ ] **Update Gap Analysis in vision doc**
  - For each gap found:
    - **Current**: What exists
    - **Gap**: What's missing
    - **Risk**: What could go wrong
    - **Impact**: High/Medium/Low
    - **Mitigation**: How to fix
    - **Owner**: Which module

- [ ] **Prioritize gaps**
  - Add to Risk Prioritization Matrix
  - Assign P0-P4 priority
  - Estimate effort (days)

- [ ] **Create action items**
  - Add P0/P1 gaps to main roadmap
  - Add P2-P4 to future.md Backlog

### Report (20-30 min)

- [ ] **Summarize findings**
  - Total gaps found: X
  - Critical (P0): X
  - High (P1): X
  - Medium (P2): X
  - Low (P3-P4): X

- [ ] **Recommend next steps**
  - Top 3 priorities
  - Quick wins (high impact, low effort)
  - Technical debt to address

- [ ] **Commit updates**
  ```
  docs(Q): Quality audit - found X gaps, updated vision doc

  Critical gaps:
  - [P0 gap 1]
  - [P0 gap 2]

  Quick wins:
  - [P2 gap that's easy to fix]

  Updated:
  - Gap Analysis section
  - Risk Prioritization Matrix
  - future.md Backlog
  ```

### Success Criteria

- ✅ Comprehensive audit of architecture, code, SEO, UX, ops
- ✅ All gaps documented in vision doc
- ✅ Gaps prioritized and assigned owners
- ✅ Action items clear for next sessions

---

## Idea Generation Session

**Goal:** Generate 5-10 high-quality ideas for BACOWR improvements or spin-offs

**Estimated Time:** 1-2 hours

### Pre-Session (15 min)

- [ ] Read `future.md` in full
  - What ideas already exist?
  - What has been rejected and why?
  - What are the meta-learnings?

- [ ] Read recent user feedback (if available)
  - Support tickets
  - Feature requests
  - User interviews

- [ ] Read `bacowr_vision_and_quality.md`
  - Gap Analysis (what's missing?)
  - Quality Charter (what could be better?)

### Idea Generation (30-60 min)

Use **5 lenses** to generate ideas:

#### 1. User Pain Points
- [ ] What frustrates users most?
- [ ] What manual work can we automate?
- [ ] Where do users get stuck?

**Brainstorm 2-3 ideas:**
1. ___
2. ___
3. ___

#### 2. Data-Driven Insights
- [ ] What metrics are underperforming?
- [ ] Where is money being wasted?
- [ ] What patterns emerge from logs?

**Brainstorm 2-3 ideas:**
1. ___
2. ___
3. ___

#### 3. Competitive Analysis
- [ ] What do competitors do better? (Clearscope, MarketMuse, Surfer SEO)
- [ ] What unique strengths does BACOWR have?
- [ ] Where is the market moving?

**Brainstorm 2-3 ideas:**
1. ___
2. ___
3. ___

#### 4. Technical Opportunities
- [ ] What new APIs/models are available?
- [ ] What infrastructure can we leverage?
- [ ] What technical debt should we pay down?

**Brainstorm 2-3 ideas:**
1. ___
2. ___
3. ___

#### 5. Business Model Expansion
- [ ] Who else would pay for BACOWR?
- [ ] What adjacent problems can we solve?
- [ ] What new revenue streams exist?

**Brainstorm 2-3 ideas:**
1. ___
2. ___
3. ___

### Evaluation (20-40 min)

For each idea, use **ICE scoring**:
- **Impact** (1-10): How much value for users?
- **Confidence** (1-10): How sure are we this will work?
- **Effort** (1-10): How easy? (10 = very easy, 1 = very hard)

**ICE Score = (Impact × Confidence × Effort) / 100**

Example:
```
Idea: LLM Output Caching
- Impact: 9 (huge cost savings)
- Confidence: 9 (proven technology)
- Effort: 7 (2-3 days work)
- ICE Score: (9 × 9 × 7) / 100 = 5.67 → HIGH PRIORITY
```

- [ ] Score all ideas
- [ ] Rank by ICE score
- [ ] Top 3 → Backlog
- [ ] Next 5 → Incubator
- [ ] Bottom → Consider rejecting with reasoning

### Categorization (15-20 min)

For each idea, determine:

- [ ] **Type:**
  - Core improvement (enhance existing feature)
  - New feature (additive)
  - Spin-off project (separate tool/service)
  - Platform expansion (v2.0/v3.0 level change)

- [ ] **Section in future.md:**
  - Backlog (1-3 months, ready for implementation)
  - Incubator (3-12+ months, needs POC or validation)
  - Reject (add to Archived with reason)

- [ ] **Dependencies:**
  - What modules must exist first?
  - What external integrations are needed?
  - What user data is needed?

### Documentation (20-30 min)

- [ ] **Add to future.md**
  - Use standard template
  - Be honest about Impact/Effort/Risk
  - Add concrete details (mockups, algorithms, examples)
  - Link to related ideas

- [ ] **Update metrics**
  ```
  Total ideas: 47 → 52
  Backlog: 12 → 15
  Incubator: 11 → 12
  ```

- [ ] **Commit**
  ```
  docs(Q): Idea generation session - added 5 new ideas

  New ideas:
  - [Backlog] Idea 1 (ICE: 5.2)
  - [Backlog] Idea 2 (ICE: 4.8)
  - [Incubator] Idea 3 (ICE: 3.1)

  Evaluation lens: User pain points + Technical opportunities
  ```

### Success Criteria

- ✅ 5-10 quality ideas generated
- ✅ All ideas evaluated with ICE scoring
- ✅ Ideas categorized appropriately
- ✅ future.md updated with details
- ✅ No implementation yet (ideas stay in future.md)

---

## Performance Optimization Session

**Goal:** Identify and fix performance bottlenecks

**Estimated Time:** 2-4 hours

### Pre-Session (10 min)

- [ ] Read recent performance complaints
- [ ] Check metrics if available
- [ ] Review Operational Quality Principles in vision doc

### Profiling (30-60 min)

- [ ] **Measure baseline**
  ```bash
  time python production_main.py \
    --publisher test.com \
    --target https://example.com \
    --anchor "test"
  ```

- [ ] **Profile Python code**
  ```python
  import cProfile
  import pstats

  cProfile.run('run_production_job(...)', 'profile_stats')
  stats = pstats.Stats('profile_stats')
  stats.sort_stats('cumulative')
  stats.print_stats(20)  # Top 20 slowest
  ```

- [ ] **Identify bottlenecks**
  - LLM API calls (expected)
  - SERP fetching (expected)
  - HTML parsing (should be fast)
  - File I/O (should be fast)
  - Regex/string ops (should be fast)

### Optimization (1-2 hours)

- [ ] **Low-hanging fruit**
  - Cache expensive operations
  - Use asyncio for I/O-bound tasks
  - Lazy load heavy dependencies
  - Pre-compile regex patterns

- [ ] **Algorithm improvements**
  - Replace O(n²) with O(n log n) or O(n)
  - Use sets instead of lists for lookups
  - Stream large files instead of loading all

- [ ] **Database optimization** (if applicable)
  - Add indexes
  - Use connection pooling
  - Batch queries

- [ ] **LLM optimization**
  - Cache responses (implement future.md idea!)
  - Use cheaper models for classification
  - Reduce prompt size

### Testing (30-45 min)

- [ ] **Measure improvement**
  ```bash
  time python production_main.py ... # Compare to baseline
  ```

- [ ] **Run benchmarks**
  ```python
  import timeit

  def benchmark():
      # Your optimized function
      pass

  time_taken = timeit.timeit(benchmark, number=100)
  print(f"Average: {time_taken/100:.4f}s")
  ```

- [ ] **Ensure correctness**
  - Run full test suite
  - Verify output is identical
  - Check edge cases still work

### Documentation (15-20 min)

- [ ] **Update docs**
  - Document optimization in code comments
  - Update performance expectations in README
  - Add benchmarks to docs

- [ ] **Update Gap Analysis**
  - Remove "slow performance" gap if fixed
  - Add new insights to future.md

- [ ] **Commit**
  ```
  perf(module): Optimize X - 40% faster

  Before: 45 seconds average
  After: 27 seconds average

  Changes:
  - Cached SERP responses (7 day TTL)
  - Async HTML fetching
  - Pre-compiled regex patterns

  Benchmarked with 100 runs
  ```

### Success Criteria

- ✅ Performance improvement measured and verified
- ✅ No regressions in functionality
- ✅ Benchmarks documented
- ✅ Future optimizations added to future.md

---

## Module Integration Session

**Goal:** Integrate two or more modules into a cohesive workflow

**Estimated Time:** 3-6 hours

### Pre-Session (15-20 min)

- [ ] Read `bacowr_master_orchestration_checklist.json`
  - Identify modules to integrate (e.g., C + D + G)
  - Check their status (both should be at least `partial`)
  - Review dependencies

- [ ] Read each module's code
  - Understand their interfaces
  - Identify integration points
  - Look for existing integration code

### Design (30-60 min)

- [ ] **Define data flow**
  ```
  Module C (Preflight)
    → produces PreflightResult
    → consumed by Module D (Writer)

  Module D (Writer)
    → produces Article
    → consumed by Module G (QC)

  Module G (QC)
    → produces QCReport
    → consumed by Orchestrator
  ```

- [ ] **Design integration layer**
  - Where does integration happen? (Orchestrator? Dedicated service?)
  - What's the error handling strategy?
  - How are partial failures handled?

- [ ] **Check for impedance mismatches**
  - Data format differences (JSON vs dict vs dataclass)
  - Async vs sync
  - Different error types

### Implementation (2-4 hours)

- [ ] **Create integration tests first**
  ```python
  def test_preflight_to_writer_integration():
      # Given: Valid preflight result
      preflight = run_light_preflight(job_input)

      # When: Writer uses it
      article = generate_article(preflight)

      # Then: Article is valid
      assert len(article) >= 900
      assert job_input.anchor_text in article
  ```

- [ ] **Implement integration code**
  - Start with simplest case
  - Add error handling
  - Add logging at integration boundaries
  - Add retry logic if needed

- [ ] **Test incrementally**
  - Test each integration separately
  - Then test full pipeline
  - Test with realistic data

### Error Handling (30-45 min)

- [ ] **Define failure modes**
  - What if Module C fails?
  - What if Module D times out?
  - What if Module G blocks?

- [ ] **Implement graceful degradation**
  - Fallback strategies
  - Partial results
  - User notifications

- [ ] **Add circuit breakers**
  - Don't retry indefinitely
  - Fail fast when appropriate
  - Track failure rates

### Documentation (30-40 min)

- [ ] **Create integration diagram**
  ```
  [User Input]
      ↓
  [Preflight (C)] → [PreflightResult]
      ↓
  [Writer (D)] → [Article]
      ↓
  [QC (G)] → [QCReport]
      ↓
  [Delivery/Block]
  ```

- [ ] **Document data contracts**
  - What does each module expect?
  - What does each module produce?
  - What are valid/invalid states?

- [ ] **Update checklist**
  - Mark integration task as `present`
  - Update dependent modules

### Success Criteria

- ✅ Modules work together seamlessly
- ✅ Error handling is robust
- ✅ Integration tests pass
- ✅ Data contracts are clear
- ✅ Documentation is complete

---

## Quick Reference

**Choose your session type:**

| Goal | Session Type | Duration |
|------|-------------|----------|
| Add new capability | Feature Implementation | 2-8h |
| Fix reported issue | Bug Fix | 0.5-4h |
| Find quality issues | Quality Audit | 2-4h |
| Improve code structure | Refactoring | 1-4h |
| Write/update docs | Documentation | 1-3h |
| Brainstorm improvements | Idea Generation | 1-2h |
| Connect modules | Module Integration | 3-6h |
| Speed up system | Performance Optimization | 2-4h |

**General workflow:**
1. Pre-session: Read context
2. Planning: Define scope and approach
3. Implementation: Build iteratively
4. Testing: Verify thoroughly
5. Documentation: Update all docs
6. Post-session: Update vision/checklist/future

---

**End of Playbooks**

These playbooks are living documents. Update them as you discover better workflows.

*"Plans are worthless, but planning is everything."* — Dwight D. Eisenhower
