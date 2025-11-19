# How to Read BACOWR (For New LLMs & Humans)

**Version:** 1.0.0
**Last Updated:** 2025-11-19
**Audience:** New LLM sessions, human developers, contributors
**Reading Time:** 10-15 minutes

---

## Purpose

This guide teaches you how to **efficiently orient yourself** in the BACOWR codebase and documentation system when starting a new session.

**The Problem:**
- BACOWR has 15+ modules, 80+ files, 1500+ lines of documentation
- Without a reading strategy, you'll waste time reading irrelevant files
- Different tasks require different knowledge subsets

**The Solution:**
- Follow task-specific reading paths
- Read in the right order (big picture → specifics)
- Know what to skim vs. read deeply

---

## The 3-Tier Reading System

### Tier 1: Essential Context (5-10 min) - READ THIS EVERY SESSION

**Required reading** regardless of your task:

1. **`docs/bacowr_vision_and_quality.md`** (sections to read):
   - Overview & Purpose (2 min)
   - Quality Charter relevant to your task (3 min)
   - Gap Analysis - scan for related gaps (2 min)
   - Appendix B: Module Reference (1 min) - know where things live

2. **`bacowr_master_orchestration_checklist.json`** (5 min):
   - Find your module (A-Q)
   - Check its status (present/partial/missing)
   - Note dependencies
   - Read task descriptions

**Why Tier 1 is essential:**
- Prevents duplicate work
- Aligns you with project vision
- Shows what already exists
- Identifies dependencies

**Skip if:** You're doing a trivial bug fix in a file you already know

---

### Tier 2: Task-Specific Context (10-30 min) - READ BASED ON TASK

**Choose your path:**

#### Path A: Implementing a Feature
1. Read `docs/playbooks/llm_session_types.md` → "Feature Implementation Session"
2. Read module code you're extending (e.g., `src/qc/quality_controller.py`)
3. Read related tests (e.g., `tests/test_qc_system.py`)
4. Read module guide if exists (e.g., `PRODUCTION_GUIDE.md`)
5. Check `docs/future.md` → Is this idea already evaluated?

#### Path B: Fixing a Bug
1. Read `docs/playbooks/llm_session_types.md` → "Bug Fix Session"
2. Read error message/bug report carefully
3. Read execution logs: `storage/output/{job_id}_execution_log.json`
4. Read QC report if relevant: `storage/output/{job_id}_qc_report.json`
5. Read the specific file with the bug
6. Check `docs/guides/gap_hunting_methodology.md` → Known gaps?

#### Path C: Quality Audit
1. Read `docs/playbooks/llm_session_types.md` → "Quality Audit Session"
2. Read `docs/templates/quality_audit_checklist.md`
3. Read `docs/guides/gap_hunting_methodology.md`
4. Read Gap Analysis in vision doc (know what's already found)
5. Read 3-5 key modules systematically

#### Path D: Idea Generation
1. Read `docs/playbooks/llm_session_types.md` → "Idea Generation Session"
2. Read `docs/future.md` in full (30 min)
   - Understand what's already proposed
   - Learn from rejected ideas
   - See meta-learnings
3. Read Gap Analysis (gaps = idea opportunities)
4. Read recent Git history: `git log --oneline -20`

#### Path E: Documentation
1. Read `README.md` to see current state
2. Read module guides (PRODUCTION_GUIDE, BATCH_GUIDE, etc.)
3. Identify documentation gaps
4. Read code to understand what to document

#### Path F: Refactoring
1. Read the code being refactored
2. Read tests for that code
3. Read dependent code (what calls this?)
4. Read Quality Charter → Code Quality Principles
5. Read `docs/templates/decision_log.md` → Past architectural decisions

---

### Tier 3: Deep Dive (30-120 min) - READ FOR COMPREHENSIVE UNDERSTANDING

**Only read when:**
- You're new to BACOWR entirely
- You're doing major architectural work
- You're writing comprehensive documentation
- You're mentoring a new team member

**Full reading list:**

1. **Vision & Strategy**
   - `docs/bacowr_vision_and_quality.md` (full document, 45 min)
   - `docs/future.md` (full document, 30 min)
   - `docs/templates/decision_log.md` (20 min)

2. **Architecture**
   - `README.md` (15 min)
   - `bacowr_master_orchestration_checklist.json` (20 min)
   - `next-a1-spec.json` (30 min)
   - `NEXT-A1-ENGINE-ADDENDUM.md` (20 min)

3. **Operational Guides**
   - `PRODUCTION_GUIDE.md` (20 min)
   - `BATCH_GUIDE.md` (15 min)
   - `API_GUIDE.md` (15 min)
   - `FRONTEND_OVERVIEW.md` (10 min)

4. **Code**
   - Read all modules in dependency order:
     - Module B (Models) → C (Preflight) → D (Writer) → G (QC) → E (Orchestrator)
   - Read all tests
   - Total: 2-4 hours

5. **Tools & Processes**
   - `docs/playbooks/` (all playbooks, 45 min)
   - `docs/guides/` (all guides, 30 min)
   - `docs/templates/` (skim all, 15 min)

**Total Tier 3 time:** 6-8 hours

**Why you might skip Tier 3:**
- You're working on a small, isolated task
- You're already familiar with BACOWR
- Time constraints

---

## Reading Order Matters

### ❌ Wrong Order (Common Mistake)
1. Start reading code
2. Get confused by architecture
3. Read README
4. Still confused about vision
5. Finally read vision doc
6. Realize you misunderstood the entire system

**Result:** Wasted time, wrong mental model

### ✅ Right Order
1. Vision doc (big picture)
2. Checklist (structure)
3. Module guide (specifics)
4. Code (implementation)

**Result:** Efficient understanding, correct mental model

---

## How to Read Different File Types

### Reading Code Files

**Strategy: Skim → Identify → Deep Read**

1. **Skim (2 min):**
   - Read module docstring
   - Scan function names
   - Note imports (dependencies)
   - Find TODOs/FIXMEs

2. **Identify (3 min):**
   - Which functions are public APIs?
   - Which are internal helpers?
   - What's the main entry point?

3. **Deep Read (10-30 min):**
   - Read public functions thoroughly
   - Trace one execution path end-to-end
   - Note edge cases in comments
   - Check error handling

**Example:**
```python
# 1. Skim: "This module does QC on articles"
"""Quality control system for generated articles."""

# 2. Identify: "Main API is run_qc()"
def run_qc(article: str, job_package: dict) -> QCReport:
    """Public API - this is what I need to understand"""
    ...

# 3. Deep Read: Trace through run_qc() logic
```

---

### Reading JSON Schema/Config

**Strategy: Purpose → Structure → Rules**

1. **Purpose (1 min):**
   - What is this schema for?
   - Who uses it?

2. **Structure (3 min):**
   - What are the top-level keys?
   - What's required vs. optional?

3. **Rules (5 min):**
   - What are the constraints?
   - What are valid values?

**Example: `backlink_job_package.schema.json`**
```
Purpose: Defines contract for job data
Structure: 8 top-level objects (job_meta, input_minimal, ...)
Rules: All fields required, specific formats for dates/URLs
```

---

### Reading Documentation

**Strategy: Scan headings → Read relevant sections**

1. **Scan TOC (1 min):**
   - What sections exist?
   - Which are relevant to my task?

2. **Read intro (2 min):**
   - What problem does this solve?
   - Who is the audience?

3. **Deep dive relevant sections (5-20 min):**
   - Skip irrelevant sections
   - Take notes on key points

4. **Skim examples (2 min):**
   - Examples often clarify better than prose

---

### Reading Tests

**Strategy: Understand what's tested, not how**

1. **Read test names (2 min):**
   - `test_qc_blocks_on_low_word_count` → Aha, word count is validated
   - `test_qc_passes_with_t1_sources` → T1 sources are required

2. **Read one test in detail (5 min):**
   - Understand the pattern
   - See how mocks are used

3. **Scan assertion messages (2 min):**
   - Often contain key requirements

**Don't:**
- Read every test line-by-line
- Worry about test implementation details
- Spend more than 10 min on tests unless writing new ones

---

## Task-Based Reading Checklists

### Checklist: Before Writing Any Code

- [ ] I've read vision doc (at least Overview & relevant Quality principles)
- [ ] I've checked checklist for module status and dependencies
- [ ] I've read existing code in the module I'm modifying
- [ ] I've checked future.md to see if this idea is already evaluated
- [ ] I understand the user/LLM who will use this code

### Checklist: Before Fixing a Bug

- [ ] I can reproduce the bug locally
- [ ] I've read the error message/logs carefully
- [ ] I've identified the root cause (not just symptoms)
- [ ] I've checked if this is a known gap in vision doc
- [ ] I've read tests to see if this should have been caught

### Checklist: Before a Quality Audit

- [ ] I've read the Quality Audit Checklist
- [ ] I've read Gap Hunting Methodology
- [ ] I've read the Gap Analysis section (know existing gaps)
- [ ] I've prepared to take notes (gaps/ideas/decisions)

### Checklist: Before Generating Ideas

- [ ] I've read future.md in full
- [ ] I've read meta-learnings (what works/doesn't work)
- [ ] I've read recent user feedback (if available)
- [ ] I've read Gap Analysis (gaps = opportunities)

---

## Reading Speed Guidelines

### Skim (100-300 words/min)
**Use for:**
- Files you've read before
- Sections not relevant to current task
- Initial orientation

**How:**
- Read headings and first sentences
- Scan for keywords
- Skip examples

### Read (50-100 words/min)
**Use for:**
- New documentation
- Code you need to understand
- Quality principles

**How:**
- Read every sentence
- Take notes on key points
- Ask "why?" and "how?"

### Study (20-50 words/min)
**Use for:**
- Complex algorithms
- Critical architecture decisions
- Specs you must implement exactly

**How:**
- Read multiple times
- Draw diagrams
- Write examples
- Test understanding

---

## Common Reading Mistakes

### Mistake 1: Reading Everything
**Problem:** Wastes time, information overload
**Solution:** Use tier system, read what you need

### Mistake 2: Reading Code First
**Problem:** Miss big picture, misunderstand purpose
**Solution:** Always read docs before code

### Mistake 3: Not Reading Tests
**Problem:** Miss edge cases, break existing functionality
**Solution:** Skim tests before modifying code

### Mistake 4: Reading Out of Order
**Problem:** Confusion, wrong mental model
**Solution:** Follow Vision → Checklist → Module → Code order

### Mistake 5: Reading Without Purpose
**Problem:** Passive consumption, nothing retained
**Solution:** Have a specific question you're answering

### Mistake 6: Not Taking Notes
**Problem:** Forget what you read, have to re-read
**Solution:** Write down key insights as you read

### Mistake 7: Trusting Stale Docs
**Problem:** Implement based on outdated information
**Solution:** Check Git history, verify code matches docs

---

## Quick Reference Cards

### Card 1: "I'm new to BACOWR, where do I start?"

**Total time:** 1 hour

1. Read vision doc: Overview & Purpose (5 min)
2. Read vision doc: User Story (10 min)
3. Read vision doc: System Vision (5 min)
4. Read vision doc: Quality Charter (skim all, read relevant, 15 min)
5. Read README.md (15 min)
6. Read checklist: scan all modules (10 min)

**You now know:**
- What BACOWR is and why it exists
- How to use it
- How code should be written
- Where everything lives

---

### Card 2: "I'm implementing feature X, what do I read?"

**Total time:** 20-30 min

1. Vision doc: Quality Charter section for X (5 min)
2. Checklist: Module X status and dependencies (2 min)
3. Code: Module X existing files (10 min)
4. Tests: Module X tests (5 min)
5. Future.md: Search for related ideas (5 min)

---

### Card 3: "I'm doing a quality audit, what do I read?"

**Total time:** 30-40 min

1. Quality Audit Checklist template (5 min)
2. Gap Hunting Methodology (20 min)
3. Vision doc: Gap Analysis (current gaps, 5 min)
4. Vision doc: Quality Charter (refresh standards, 10 min)

---

### Card 4: "I have 5 minutes, what's most important?"

**Read this:**
1. Vision doc: Overview & Purpose (3 min)
2. Checklist: Your module's status (2 min)

**Why:**
- You'll know if your work is aligned
- You'll know what already exists
- You won't duplicate effort

---

## The "Context Loading" Mental Model

Think of reading BACOWR docs like **loading a large program into RAM**:

1. **Boot sector** (Tier 1): Essential context, always load
2. **Kernel** (Tier 2): Task-specific modules, load as needed
3. **User space** (Tier 3): Full system knowledge, rarely needed

**Memory management:**
- You can't keep everything in memory
- Load what you need, unload the rest
- Re-load when needed (docs don't change fast)

**Paging strategy:**
- Keep vision doc in "hot cache" (re-read often)
- Keep playbooks in "warm cache" (re-read per session type)
- Keep deep specs in "cold cache" (read once, reference as needed)

---

## Reading for Different Roles

### As an LLM in a New Session
**Your goal:** Understand enough to be helpful without wasting tokens

**Minimal reading:**
- Vision doc: Overview, Quality Charter (relevant section), Gap Analysis
- Checklist: Your module
- **Total:** 10-15 min

**Why minimal works:**
- You can ask user for clarification
- You can read more files as needed (Read tool)
- Context window is limited

---

### As a Human Developer
**Your goal:** Build comprehensive mental model

**Recommended:**
- Tier 1 (always)
- Tier 2 (based on tasks)
- Tier 3 (first week, then reference)

**Why comprehensive helps:**
- You'll work on BACOWR repeatedly
- You can't ask clarifying questions easily
- You benefit from deep understanding

---

### As a Code Reviewer
**Your goal:** Verify changes align with quality standards

**Focused reading:**
- Vision doc: Quality Charter
- Code being changed
- Tests for that code
- Decision log (recent decisions)

**Why focused works:**
- You're validating, not creating
- You need to spot violations quickly
- Deep knowledge less critical

---

## End of Guide

**Remember:**
- **Read with purpose** (know why you're reading)
- **Read in order** (big picture → specifics)
- **Read what you need** (use tier system)
- **Take notes** (capture insights)
- **Verify code matches docs** (check Git history)

**When in doubt:**
1. Read vision doc
2. Read checklist
3. Ask user

*"Reading furnishes the mind only with materials of knowledge; it is thinking that makes what we read ours."* — John Locke

Make what you read yours by **applying** it to your task.
