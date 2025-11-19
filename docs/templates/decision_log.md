# BACOWR Decision Log

**Purpose:** Record significant architectural, design, and strategic decisions
**Format:** ADR (Architecture Decision Record) inspired

---

## How to Use This Log

1. **When to log a decision:**
   - Chose technology A over B
   - Decided on architecture pattern
   - Rejected a feature/approach
   - Changed direction on something significant

2. **When NOT to log:**
   - Routine implementation details
   - Obvious choices
   - Reversible decisions with no long-term impact

3. **Template:**
   ```markdown
   ## [ID] [Short Title]

   **Date:** YYYY-MM-DD
   **Status:** Accepted | Deprecated | Superseded
   **Deciders:** [Who made this decision]
   **Context:** [Session/module/feature being worked on]

   ### Problem
   [What decision needed to be made and why]

   ### Options Considered
   1. **Option A**: [description]
      - Pros: ...
      - Cons: ...
      - Cost: ...
   2. **Option B**: [description]
      - Pros: ...
      - Cons: ...
      - Cost: ...

   ### Decision
   [What was chosen and why]

   ### Consequences
   - **Positive**: ...
   - **Negative**: ...
   - **Neutral**: ...

   ### Follow-Up
   - [ ] Action item 1
   - [ ] Action item 2
   ```

---

## Decisions

### D001: Use PostgreSQL for Production Database

**Date:** 2025-11-19
**Status:** Planned (not yet implemented)
**Deciders:** Team Q, Module F
**Context:** Module F2 - Database integration needed for v1.5 hosted app

#### Problem
File-based storage (`storage/output/`) cannot support multi-user scenarios. Need persistent database for:
- User accounts
- Job history
- Backlink library (3000+ records)
- QC reports
- Execution logs

#### Options Considered

1. **PostgreSQL**
   - Pros: Industry standard, excellent Python support (SQLAlchemy), JSONB for flexible schemas, strong ACID guarantees
   - Cons: Ops overhead (hosting, backups), learning curve for deployment
   - Cost: $7-25/month (managed hosting)

2. **SQLite**
   - Pros: Zero ops, built into Python, perfect for dev/test, file-based simplicity
   - Cons: No multi-user concurrency, no network access, limited production scalability
   - Cost: Free

3. **MongoDB**
   - Pros: Flexible schema, good for JSON data, horizontal scaling
   - Cons: Overkill for our use case, less mature Python ecosystem, eventual consistency issues
   - Cost: $9-25/month

4. **Airtable** (API-based)
   - Pros: No-code GUI for manual edits, built-in API, visual spreadsheet interface
   - Cons: API rate limits, vendor lock-in, not a real database
   - Cost: $20+/month

#### Decision
**Chose PostgreSQL** because:
- Best balance of power and ops simplicity (managed hosting exists)
- SQLAlchemy ORM makes migrations easy
- JSONB perfect for storing job packages and QC reports
- Can start with SQLite in dev, migrate to Postgres in prod (same ORM)

#### Consequences
- **Positive:**
  - Proper multi-user support
  - Fast queries with indexes
  - Data integrity with foreign keys
  - Can use managed hosting (Heroku, Railway, Render)

- **Negative:**
  - Need migration scripts
  - Deployment complexity increases
  - Monthly hosting cost

- **Neutral:**
  - Need to learn SQLAlchemy (good skill anyway)
  - Need backup strategy

#### Follow-Up
- [ ] Design schema (jobs, users, backlinks, qc_reports, execution_logs)
- [ ] Add SQLAlchemy to requirements.txt
- [ ] Create database.py with models
- [ ] Create alembic migrations
- [ ] Update storage interfaces to use DB
- [ ] Document deployment (DATABASE_URL env var)

---

### D002: Use Anthropic Claude as Primary LLM for Swedish Content

**Date:** 2025-11-19
**Status:** Accepted
**Deciders:** Team Q, Module D
**Context:** Module D - LLM client implementation

#### Problem
Need to choose primary LLM provider for content generation. Requirements:
- Excellent Swedish language support
- Reliable API
- Cost-effective for production
- Good content quality

#### Options Considered

1. **Anthropic Claude**
   - Pros: Excellent multilingual (incl. Swedish), reliable API, good quality, reasonable cost (~$3-15/M tokens)
   - Cons: Newer player, smaller model selection
   - Cost: $0.06-0.15 per article (estimated)

2. **OpenAI GPT**
   - Pros: Market leader, excellent API, good Swedish support, wide model range
   - Cons: Slightly more expensive, occasional outages
   - Cost: $0.08-0.20 per article (estimated)

3. **Google Gemini**
   - Pros: Cheapest option, good multilingual, Google infrastructure
   - Cons: Newer, less proven for production, API still evolving
   - Cost: $0.03-0.10 per article (estimated)

4. **Open-source (Llama, Mistral)**
   - Pros: Free inference (self-hosted), full control
   - Cons: Ops burden, GPU costs, quality varies
   - Cost: GPU hosting ~$100-500/month

#### Decision
**Chose Claude as primary, with multi-provider fallback**:
- Claude for Swedish content (best quality)
- GPT/Gemini as fallbacks
- Strategy pattern in code allows easy provider switching

#### Consequences
- **Positive:**
  - Excellent Swedish article quality
  - Reliable uptime
  - Reasonable costs
  - Can A/B test providers

- **Negative:**
  - Vendor dependency (mitigated by multi-provider support)
  - Cost higher than Gemini

- **Neutral:**
  - Need API keys for multiple providers

#### Follow-Up
- [x] Implement multi-provider support in production_writer.py
- [x] Test all providers with Swedish content
- [ ] Add cost comparison dashboard
- [ ] Document provider selection strategy in README

---

### D003: Reject Real-Time Collaborative Editing (for now)

**Date:** 2025-11-19
**Status:** Rejected
**Deciders:** Team Q, Module K
**Context:** future.md - Idea evaluation

#### Problem
Should BACOWR support real-time collaborative editing (Google Docs style) for team workflows?

#### Options Considered

1. **Implement with OT/CRDT**
   - Pros: Great UX for teams, modern feature, competitive advantage
   - Cons: Very complex engineering (10-15 days), performance concerns, conflict resolution hard
   - Cost: High dev time, ongoing maintenance

2. **Use third-party service** (e.g., Yjs, ShareDB)
   - Pros: Less dev time, proven tech
   - Cons: Vendor dependency, integration complexity, cost
   - Cost: $50-200/month + integration time

3. **Delay until v2.0**
   - Pros: Focus on core value prop (generation, not editing), can validate demand first
   - Cons: Agencies may want this feature
   - Cost: Opportunity cost (potential users)

4. **Don't implement** (CMS integration instead)
   - Pros: Users already have editing tools (WordPress, Google Docs), we shouldn't rebuild
   - Cons: Requires users to leave BACOWR for edits
   - Cost: None

#### Decision
**Rejected for v1.x**, will revisit for v2.0 if demand is proven

Reasoning:
- v1.x focus is on **generation quality**, not post-generation editing
- Users can export to their preferred editors (WordPress, Google Docs, Notion)
- Complex feature distracts from core value prop
- No user demand yet (0 requests)
- Better ROI: Invest in CMS integrations (WordPress export, etc.)

#### Consequences
- **Positive:**
  - Team focused on core features
  - Simpler architecture
  - Faster v1.x delivery

- **Negative:**
  - May lose agency users who need collaboration
  - Competitive disadvantage vs tools with collaboration

- **Neutral:**
  - Can revisit if demand emerges

#### Follow-Up
- [x] Document in future.md (Incubator → On Hold)
- [ ] Prioritize CMS export instead (WordPress, Webflow)
- [ ] Survey users in v1.5 beta about editing needs
- [ ] Revisit decision in v2.0 planning

---

### D004: State Machine with RESCUE (not infinite retry)

**Date:** 2025-11-19
**Status:** Accepted
**Deciders:** Team Q, Module E
**Context:** Module E - Orchestrator state machine design

#### Problem
How should the system handle QC failures? Retry forever? Once? Not at all?

#### Options Considered

1. **No retry** (fail immediately)
   - Pros: Simple, predictable
   - Cons: Wastes LLM call if minor fixable issue
   - Cost: Higher failure rate

2. **Infinite retry** (until pass)
   - Pros: Eventually succeeds
   - Cons: Infinite loops possible, cost explosion, no escape hatch
   - Cost: Potentially unbounded

3. **Fixed retry (N times)**
   - Pros: Bounded, configurable
   - Cons: Arbitrary limit, doesn't differentiate fixable vs unfixable
   - Cost: Moderate

4. **RESCUE once with AutoFix**
   - Pros: Tries to fix, bounded (max 2 attempts), smart (only if auto-fixable)
   - Cons: Slightly more complex logic
   - Cost: Max 2x LLM calls per job

#### Decision
**Chose RESCUE (Option 4)** - One automatic fix attempt if QC fails with auto-fixable issues

Flow:
```
WRITE → QC (fail) → RESCUE (autofix) → QC (pass/fail) → DELIVER/BLOCK
```

Rules:
- Max 1 RESCUE per job
- Only if QC issues are auto-fixable (not "human_signoff_required")
- If RESCUE produces identical output (hash check), ABORT (no infinite loops)

#### Consequences
- **Positive:**
  - Saves many jobs from unnecessary failures
  - Bounded cost (never >2 LLM calls)
  - Smart differentiation (fixable vs unfixable)

- **Negative:**
  - Slightly more complex state machine
  - Edge case handling needed (hash collisions, etc.)

- **Neutral:**
  - Need to log RESCUE attempts for debugging

#### Follow-Up
- [x] Implement in state_machine.py
- [x] Add tests for RESCUE logic
- [x] Document in execution_log
- [x] Add "rescue_count" to job metadata

---

### D005: Batch Processing with Chunking (not monolithic)

**Date:** 2025-11-19
**Status:** Accepted
**Deciders:** Team Q, Module E
**Context:** Module E2 - Batch orchestrator

#### Problem
How to process large batches (e.g., 175 articles)?
- All at once? (memory issues)
- One at a time? (slow)
- In chunks? (how big?)

#### Options Considered

1. **Monolithic** (load all 175 jobs, process in memory)
   - Pros: Simple
   - Cons: Memory explosion, crashes on large batches
   - Cost: High memory, crashes

2. **Streaming** (process one at a time)
   - Pros: Low memory
   - Cons: No parallelism, very slow (175 jobs × 45 sec = 2+ hours)
   - Cost: Slow

3. **Fixed chunks** (e.g., 25 jobs per chunk)
   - Pros: Bounded memory, parallelizable, resumable
   - Cons: Need to manage chunks
   - Cost: Moderate complexity

4. **Dynamic chunks** (adjust based on system resources)
   - Pros: Optimal resource usage
   - Cons: Complex logic, hard to predict
   - Cost: High complexity

#### Decision
**Chose Fixed chunks (Option 3)** with configurable chunk size (default 25)

Implementation:
- Split batch into chunks of 25 jobs
- Process each chunk sequentially or in parallel (configurable)
- Save checkpoint after each chunk
- On failure, resume from last checkpoint

#### Consequences
- **Positive:**
  - Predictable memory usage
  - Resumable on failure
  - Can parallelize within chunks
  - User can configure chunk size

- **Negative:**
  - Need chunking logic
  - Need checkpoint/resume logic

- **Neutral:**
  - Chunk size is a tunable parameter

#### Follow-Up
- [x] Implement chunking in batch_runner.py
- [x] Add --chunk-size CLI flag
- [x] Implement checkpoint/resume
- [x] Document in BATCH_GUIDE.md

---

## Decision Review Schedule

- **Quarterly**: Review all "Accepted" decisions - are they still valid?
- **Annually**: Review all "Deprecated" decisions - can they be removed?
- **On major version**: Review all decisions - update or supersede

## Superseded Decisions

_(When a decision is superseded, move it here)_

### D000: [Example Superseded Decision]

**Original Decision:** Use X for Y
**Date Superseded:** YYYY-MM-DD
**Superseded By:** D00X
**Reason:** Context changed, better option emerged

---

**End of Decision Log**

Keep this updated. Future you (and future LLMs) will thank you.
