# BACOWR Vision & Quality Charter

**Version:** 1.0.0
**Last Updated:** 2025-11-19
**Status:** Active
**Purpose:** Central vision document and quality blueprint for BACOWR development

---

## Table of Contents

1. [Overview & Purpose](#overview--purpose)
2. [User Story: A SEO Professional Using BACOWR](#user-story-a-seo-professional-using-bacowr)
3. [System Vision](#system-vision)
4. [Gap Analysis & Risk Areas](#gap-analysis--risk-areas)
5. [Quality Charter](#quality-charter)
6. [Improvement Loop for Future LLMs](#improvement-loop-for-future-llms)
7. [Future Loop & Idea Incubator](#future-loop--idea-incubator)
8. [How to Use This Document in a New Session](#how-to-use-this-document-in-a-new-session)
9. [Concrete Checklist for LLMs](#concrete-checklist-for-llms)

---

## Overview & Purpose

### What is BACOWR?

**BACOWR** (**B**acklink **A**rticle **C**ontent **O**rchestration **W**ith **R**efinement) is a production-ready engine for creating high-quality backlink articles that:

- **Analyzes SERP** for search intent and top-ranking content
- **Profiles** target pages and publisher sites automatically
- **Generates** contextually appropriate backlink content that fits naturally into the SERP landscape
- **Validates** quality through automated QC (Quality Control) with AutoFix capability
- **Logs** the entire process for full traceability

### Why BACOWR Exists

Traditional backlink article creation is:
- **Manual and time-consuming**: Writers spend hours researching SERP, understanding intent, and crafting contextually appropriate content
- **Inconsistent quality**: Different writers produce different quality levels
- **Risky**: Poor anchor placement, intent misalignment, or low trust can harm SEO
- **Not scalable**: Creating 100+ articles manually is prohibitively expensive

BACOWR solves these problems by:
- **Automating research**: SERP analysis, intent detection, publisher/target profiling
- **Ensuring quality**: Built-in QC system with blocking conditions and AutoFix
- **Scaling efficiently**: Batch processing of 175+ articles with parallel execution
- **Maintaining traceability**: Every decision is logged and auditable

### Core Value Proposition

**"From three inputs to publication-ready article in 30-60 seconds"**

Input:
```json
{
  "publisher_domain": "example-publisher.com",
  "target_url": "https://client.com/product",
  "anchor_text": "best solution for [topic]"
}
```

Output:
- ✅ 900+ word markdown article
- ✅ QC report with quality validation
- ✅ Complete job package with profiling data
- ✅ Execution log for debugging

---

## User Story: A SEO Professional Using BACOWR

### The User: Anna, SEO Specialist

Anna manages backlink campaigns for 15 clients. She needs to create 175 backlink articles per month across various Swedish publishers.

### Before BACOWR

**Monday morning** (2-3 hours per article):
1. Opens Google, searches for target keyword
2. Manually reviews top 10 results, takes notes on intent
3. Visits publisher site, reads recent articles to understand tone
4. Opens Word, starts writing from scratch
5. Tries to remember SEO best practices (LSI terms, trust sources, anchor placement)
6. Sends to editor for QA review
7. Editor finds issues, sends back for revision
8. Final article ready after 2-3 hours

**Weekly output**: ~10-15 articles
**Monthly output**: 40-60 articles (far below the 175 needed)
**Quality**: Inconsistent, depends on Anna's energy and knowledge

### After BACOWR

**Monday morning** (using hosted BACOWR app):

**Option 1: Quick Single Article (60 seconds)**
1. Opens BACOWR dashboard in browser
2. Sees "Quick Start" widget, enters 3 fields:
   - Publisher: `aftonbladet.se`
   - Target URL: `https://client.com/product-x`
   - Anchor: `bästa lösningen för X`
3. Clicks "Generate Article"
4. Watches real-time progress bar (SERP research → Profiling → Writing → QC)
5. After 30-60 seconds: Article is ready
6. Reviews article in built-in editor
7. Checks QC report: ✅ PASS (9.5/10 score)
8. Downloads as Markdown or exports to CMS

**Option 2: Batch Processing (175 articles overnight)**
1. Creates CSV file with 175 publisher/target/anchor combinations
2. Uploads to BACOWR batch processor
3. Configures: `anthropic`, `multi_stage`, `parallel=3`, `rate-limit=10`
4. Schedules batch to run at 23:00 (off-peak API pricing)
5. Goes home
6. Next morning: 170/175 articles delivered, 5 blocked for manual review
7. Reviews the 5 blocked articles (intent issues), makes adjustments
8. Exports all 170 articles to CMS

**Weekly output**: 200+ articles
**Monthly output**: 800+ articles (exceeds target by 4.5x)
**Quality**: Consistent, validated by QC system

### The "Aha!" Moments

1. **"I don't need to be a Python expert"** - The GUI handles everything
2. **"It understands SEO better than I do"** - Intent alignment, LSI, trust sources are automatic
3. **"I can focus on strategy, not execution"** - Time freed up for campaign planning
4. **"Quality is consistent"** - No more "tired Friday afternoon" low-quality articles
5. **"I can finally scale"** - 175 articles is no longer intimidating

---

## System Vision

### Short-Term Vision (Current: v1.0 - Production Ready)

**Status**: ✅ Achieved

- [x] Core engine operational (preflight, LLM, QC, state machine)
- [x] Multi-LLM support (Claude, GPT, Gemini)
- [x] Ahrefs SERP integration
- [x] Batch processing (CSV/JSON input, parallel execution, rate limiting)
- [x] Full test coverage (80/80 tests passing)
- [x] Production guides and documentation
- [x] CLI and Python API

### Medium-Term Vision (v1.5 - Hosted Application)

**Target**: Q1-Q2 2025

**The Hosted App**:
- ✅ Frontend webapp (Next.js) - **COMPLETE**
  - Dashboard with quick start widget
  - Job creation wizard (4-step flow)
  - Real-time monitoring via WebSocket
  - Backlinks library (browse, search, analytics)
  - Settings management (API keys, defaults, cost limits)
- [ ] Backend API (FastAPI) - **IN PROGRESS**
  - REST endpoints for job CRUD
  - WebSocket for real-time updates
  - User management with API keys
  - Cost tracking and analytics
- [ ] Database layer (PostgreSQL)
  - Job persistence
  - Backlink history (3000+ records)
  - User accounts and settings
- [ ] Deployment
  - Docker containers
  - Vercel for frontend
  - VPS or cloud for backend
  - SSL/HTTPS
  - Monitoring and logging

**Success Metrics for v1.5**:
- 📊 **Time-to-first-article**: ≤ 60 seconds from landing to download
- 📊 **User onboarding**: 90%+ complete first article without support
- 📊 **Batch success rate**: ≥ 95% jobs delivered without human intervention
- 📊 **QC accuracy**: ≤ 5% false positives (good articles blocked)
- 📊 **Cost per article**: $0.03-0.15 depending on LLM/strategy
- 📊 **Uptime**: 99.5%+ availability

**User Experience Goal**:
> "A copywriter with no coding knowledge can log in, enter 3 fields, and get a publication-ready article in 60 seconds."

### Long-Term Vision (v2.0+ - SEO Content Platform)

**Target**: 2025+

**Beyond Backlink Articles**:
- **Heavy Preflight**: Advanced SERP analysis with intent extensions, trust policies, anchor risk modeling
- **Day 2 QA Workflow**: Batch QA tools for reviewing 175-article batches efficiently
- **Scraper Integration**: Automated publisher tone/style scraping
- **Semantic Tools**: Entity extraction, topic modeling, content gap analysis
- **Multi-Modal Content**: Images, infographics, video scripts
- **Campaign Management**: Track backlinks across clients, monitor rankings, measure ROI
- **MCP Integrations**: Connect to external tools (Airtable, Notion, WordPress, etc.)

**Ultimate Goal**:
> "A complete SEO content platform where BACOWR is the core engine, but it can orchestrate entire campaigns from research to publication to analysis."

---

## Gap Analysis & Risk Areas

### Current Gaps (Identified as of 2025-11-19)

#### 1. Architecture Gaps

**Database Integration**
- **Current**: File-based storage (`storage/output/`)
- **Gap**: No persistent database for multi-user scenarios
- **Risk**: Cannot scale beyond single-user/single-session usage
- **Impact**: High (blocks hosted app deployment)
- **Mitigation**: Implement PostgreSQL layer (Module F2 in checklist)

**API Backend for Frontend**
- **Current**: Frontend exists but backend API is incomplete
- **Gap**: Missing endpoints for user management, batch CRUD, analytics
- **Risk**: Frontend cannot connect to real backend
- **Impact**: High (blocks v1.5 hosted app)
- **Mitigation**: Complete Module H in checklist

**Heavy Preflight**
- **Current**: Light preflight only (basic HTML extraction)
- **Gap**: No advanced intent modeling, LSI window analysis, trust policy enforcement
- **Risk**: Content quality ceiling - cannot handle complex verticals (finance, health, legal)
- **Impact**: Medium (limits market reach)
- **Mitigation**: Implement Module M (Heavy Preflight stubs exist)

#### 2. SEO Logic Gaps

**Intent Alignment Edge Cases**
- **Current**: Intent analyzer works well for common patterns
- **Gap**: Ambiguous queries (mixed informational/commercial) can confuse the system
- **Risk**: QC blocks articles unnecessarily OR allows misaligned content
- **Impact**: Medium (5-10% of jobs affected)
- **Mitigation**: Expand intent test coverage, add "unsure" state for human review

**Anchor Risk Modeling**
- **Current**: Pattern-based risk detection (exact match, branded, generic)
- **Gap**: No context-aware anchor risk (e.g., exact match can be safe if editorial context is strong)
- **Risk**: Over-blocking safe anchors OR under-blocking risky ones
- **Impact**: Low-Medium
- **Mitigation**: Implement context-aware anchor scoring (Heavy Preflight feature)

**LSI Term Quality**
- **Current**: LLM generates LSI terms, QC checks for presence
- **Gap**: No validation that LSI terms are semantically related to topic
- **Risk**: Low-quality "keyword stuffing" behavior
- **Impact**: Low (LLMs generally good at this)
- **Mitigation**: Add semantic similarity scoring for LSI terms

#### 3. Operational Gaps

**Multi-User Isolation**
- **Current**: Single-user mode (local file storage, no auth)
- **Gap**: No user accounts, API keys, or job isolation
- **Risk**: Cannot deploy as multi-tenant SaaS
- **Impact**: High (blocks business model)
- **Mitigation**: Implement user management (Module H, API endpoints)

**Cost Monitoring & Limits**
- **Current**: Cost calculation exists, no enforcement
- **Gap**: Users can accidentally spend thousands on large batches
- **Risk**: Budget overruns, unhappy users
- **Impact**: Medium
- **Mitigation**: Implement cost limits in batch runner, pre-batch cost estimation with approval step

**Error Recovery in Batches**
- **Current**: Basic retry logic, progress checkpointing
- **Gap**: No intelligent retry (e.g., retry with cheaper model, skip permanently failed jobs)
- **Risk**: Batches stall on edge cases
- **Impact**: Low-Medium
- **Mitigation**: Add smarter retry strategies, dead-letter queue for failed jobs

**Observability**
- **Current**: JSON logs, execution logs per job
- **Gap**: No centralized logging, metrics, alerting
- **Risk**: Cannot debug production issues quickly
- **Impact**: Medium (operational burden)
- **Mitigation**: Integrate structured logging (e.g., Sentry, LogDNA)

#### 4. UX Gaps

**Batch QA Workflow**
- **Current**: No Day 2 QA UI for reviewing 175-article batches
- **Gap**: Users must manually review articles one by one
- **Risk**: QA bottleneck, batches unused
- **Impact**: High for batch users
- **Mitigation**: Build batch QA dashboard (Module G3, G4)

**Content Editing**
- **Current**: Markdown download, external editing
- **Gap**: No in-app editor with SEO guidance (LSI, anchor, trust sources highlighted)
- **Risk**: Users make edits that break SEO compliance
- **Impact**: Medium
- **Mitigation**: Add rich markdown editor with QC re-validation on edit

**Publisher/Target Scraping**
- **Current**: Basic HTML extraction
- **Gap**: No visual scraper tool for users to add custom publishers
- **Risk**: Limited to sites BACOWR can parse automatically
- **Impact**: Medium
- **Mitigation**: Add scraper configurator UI (future roadmap)

#### 5. Compliance & Legal Gaps

**Content Rights**
- **Current**: No license/attribution tracking
- **Gap**: Unclear who owns generated content (user, BACOWR, LLM provider?)
- **Risk**: Legal disputes
- **Impact**: Low (standard ToS can address)
- **Mitigation**: Clear ToS, user-owns-output policy

**GDPR/Privacy**
- **Current**: No PII handling (yet)
- **Gap**: Future user accounts will store emails, API usage data
- **Risk**: GDPR non-compliance
- **Impact**: Medium (EU users)
- **Mitigation**: Privacy policy, data retention policies, GDPR compliance audit

**Regulated Verticals**
- **Current**: QC checks for disclaimers (gambling, finance, health, legal)
- **Gap**: No legal review of compliance wording
- **Risk**: Users violate regulations using BACOWR content
- **Impact**: Medium
- **Mitigation**: Add "Legal Review Required" flag for regulated verticals, partner with legal experts

### Risk Prioritization Matrix

| Risk Area | Impact | Likelihood | Priority | Owner (Module) | Estimated Effort |
|-----------|--------|------------|----------|----------------|------------------|
| Database integration | High | High | **P0** | F2 | 2-3 days |
| API backend | High | High | **P0** | H | 3-5 days |
| Multi-user isolation | High | High | **P0** | H, N | 2-3 days |
| Batch QA workflow | High | Medium | **P1** | G3, G4 | 3-4 days |
| Cost enforcement | Medium | Medium | **P2** | E2, K | 1-2 days |
| Intent edge cases | Medium | Low | **P2** | C, D | 2-3 days |
| Heavy preflight | Medium | Low | **P3** | M | 5-7 days |
| Observability | Medium | Low | **P3** | L2 | 2-3 days |
| LSI quality | Low | Low | **P4** | C, D | 1-2 days |

**Total P0/P1 effort estimate**: 10-15 days of focused development

**LLM Instruction Box:**
```
🤖 LLM: When prioritizing what to work on:
1. Always tackle P0 items first (unless explicitly told otherwise)
2. Only work on P1+ if all P0 items are complete
3. Add newly discovered risks to this matrix with honest estimates
4. Update priority/status as items are completed
```

---

## Quality Charter

> **Core Principle**: Every decision—code, prompt, SEO logic, UX—must optimize for **quality, transparency, and user trust**. Speed is important, but never at the expense of correctness.

### Code Quality Principles

#### 1. Modularity & Separation of Concerns
**Rule**: Each module has a single, well-defined responsibility.

✅ **Good**:
```python
# Separate modules for distinct concerns
from src.profiling.page_profiler import PageProfiler
from src.research.serp_researcher import SERPResearcher
from src.analysis.intent_analyzer import IntentAnalyzer
```

❌ **Bad**:
```python
# God object that does everything
class BacklinkEngine:
    def profile_and_research_and_analyze_and_write(...):
        # 500 lines of mixed logic
```

**Why**: Modularity enables testing, reuse, and parallel development by multiple LLM sessions.

#### 2. No Hard-Coded Secrets or Configuration
**Rule**: All secrets and config come from environment variables or config files.

✅ **Good**:
```python
from src.config import get_settings
settings = get_settings()
api_key = settings.anthropic_api_key
```

❌ **Bad**:
```python
api_key = "sk-ant-1234567890"  # NEVER
```

**Why**: Security, portability, and production readiness.

#### 3. Explicit Interfaces & Type Hints
**Rule**: All public functions have type-hinted signatures and docstrings.

✅ **Good**:
```python
def run_light_preflight(job: JobInput) -> PreflightResult:
    """
    Execute light preflight analysis for a backlink job.

    Args:
        job: Input containing publisher, target, anchor

    Returns:
        PreflightResult with profiles and research prompt
    """
    ...
```

❌ **Bad**:
```python
def preflight(j):  # What is j? What does this return?
    ...
```

**Why**: Type hints enable IDE autocomplete, catch bugs at dev time, and serve as documentation.

#### 4. Error Handling & Logging
**Rule**: Anticipate failures, log errors with context, never fail silently.

✅ **Good**:
```python
try:
    html = fetch_url(url, timeout=10)
except requests.Timeout:
    logger.warning(f"Timeout fetching {url}, using fallback")
    html = get_cached_html(url)
except requests.RequestException as e:
    logger.error(f"Failed to fetch {url}: {e}")
    raise PreflightError(f"Cannot fetch {url}")
```

❌ **Bad**:
```python
try:
    html = fetch_url(url)
except:
    pass  # Silently ignore errors
```

**Why**: Logs enable debugging in production. Explicit error types enable graceful degradation.

#### 5. Testability First
**Rule**: Write code that is easy to test. Pure functions, dependency injection, mocks.

✅ **Good**:
```python
def analyze_intent(serp_data: SERPData, target_profile: TargetProfile) -> IntentAlignment:
    # Pure function, easy to test
    ...
```

❌ **Bad**:
```python
def analyze_intent():
    serp_data = fetch_from_global_cache()  # Hard to mock
    target = load_from_database()  # Hard to test
    ...
```

**Why**: Tests prevent regressions. Untested code will break in production.

---

### Prompt Quality Principles

#### 1. Clarity Over Cleverness
**Rule**: Prompts should be straightforward, not "clever" or overly verbose.

✅ **Good**:
```
Write a 900-word article for {publisher} that links to {target} using anchor "{anchor}".

Requirements:
- Match publisher tone: {tone}
- Include these LSI terms: {lsi_terms}
- Place link in paragraph 3-5
- Cite at least one T1 trust source

Publisher context:
{publisher_profile}

Target context:
{target_profile}

SERP intent:
{intent_summary}
```

❌ **Bad**:
```
You are an expert SEO writer with 20 years of experience. Your task, should you choose to accept it, is to craft a masterpiece of digital content that seamlessly integrates a backlink while maintaining the highest standards of editorial excellence... [300 more words of fluff]
```

**Why**: LLMs respond better to clear instructions than to "role-playing" preambles. Shorter prompts = lower cost.

#### 2. Explicit Constraints
**Rule**: State requirements as concrete constraints, not suggestions.

✅ **Good**:
```
REQUIRED:
- Word count: 900-1200 words (not less, not more)
- Anchor text: Use EXACTLY "{anchor}" (no modifications)
- Trust sources: Cite at least 1 T1 source from: {t1_sources}

FORBIDDEN:
- Do not mention competitors: {forbidden_brands}
- Do not use exact-match anchor more than once
```

❌ **Bad**:
```
Try to write around 900 words or so. The anchor should be something like "{anchor}", feel free to adjust. It would be nice if you could include a trustworthy source or two.
```

**Why**: LLMs interpret "try to" as optional. Explicit constraints reduce QC failures.

#### 3. Context Before Task
**Rule**: Provide context (publisher, target, SERP) BEFORE asking LLM to write.

✅ **Good**:
```
Context:
Publisher: Aftonbladet (Swedish tabloid, sensational tone, 8th grade reading level)
Target: SaaS tool for project management
SERP Intent: Informational (users want guides, not product pitches)

Task:
Write an article that...
```

❌ **Bad**:
```
Write an article about project management tools for Aftonbladet.
[No context about tone, intent, or target]
```

**Why**: Context-first prompts improve alignment and reduce hallucinations.

#### 4. No Unnecessary Meta-Text
**Rule**: Remove filler, preambles, and politeness. Get to the point.

✅ **Good**:
```
Write article. Format: Markdown. Output only the article, no meta-commentary.
```

❌ **Bad**:
```
Hello! I hope you're having a great day. I would be so grateful if you could perhaps help me by writing an article. If it's not too much trouble, could you format it in Markdown? And please, when you're done, I'd prefer if you didn't add any extra commentary. Thank you so much!
```

**Why**: Meta-text adds tokens (cost) without improving output. LLMs don't need politeness.

#### 5. Output Format Specification
**Rule**: Always specify the exact output format. Use examples if needed.

✅ **Good**:
```
Output format:
# [Headline with keyword]

[Introduction paragraph]

## [Subheading 1]
[Content with link in paragraph 3-5]

## [Subheading 2]
[Content]

[Conclusion]

Example:
# Så väljer du rätt projektverktyg 2025

I dagens digitala arbetsmiljö...
```

❌ **Bad**:
```
Write the article however you think is best.
```

**Why**: Format specification prevents "creative" outputs that break parsers.

---

### SEO Quality Principles

#### 1. Intent First, Keywords Second
**Rule**: Align content with search intent BEFORE optimizing for keywords.

**Intent Types**:
- **Informational**: User wants to learn → Guides, how-tos, explanations
- **Commercial Research**: User is comparing options → Reviews, comparisons, "best X for Y"
- **Transactional**: User is ready to buy → Product pages, pricing, signup
- **Navigational**: User wants a specific site → Brand pages, login pages

**Quality Check**:
- ✅ Article intent matches SERP intent
- ❌ Informational article linking to a transactional page (misalignment)

**Why**: Google ranks based on intent satisfaction. Keyword-stuffed but intent-misaligned content won't rank.

#### 2. Natural Language Over Keyword Density
**Rule**: Write for humans, not keyword density algorithms.

✅ **Good**:
> "When choosing a project management tool, consider your team size, budget, and workflow complexity. Popular options include Asana, Monday, and Trello."

❌ **Bad**:
> "Project management tools are essential. The best project management tools help teams. Our recommended project management tool is [link]. Project management tools should be chosen carefully."

**Why**: Modern search engines detect and penalize keyword stuffing. Natural language ranks better.

#### 3. Trust Sources Are Mandatory
**Rule**: Every article must cite at least one T1 (Tier 1) trust source.

**Trust Tiers**:
- **T1**: Government sites (.gov), universities (.edu), Wikipedia, major news (BBC, Reuters)
- **T2**: Industry publications, well-known blogs, established companies
- **T3**: Smaller blogs, forums, user-generated content
- **T4**: Unknown or low-authority sites

**Requirement**:
- Minimum 1 T1 source per article
- Preference: 2-3 trust sources total (mix of T1/T2)

**Why**: Trust signals improve E-A-T (Expertise, Authoritativeness, Trustworthiness), which Google values.

#### 4. Anchor Text Naturalness
**Rule**: Anchor text must read naturally in context. Avoid forced insertions.

✅ **Good**:
> "For teams looking to streamline workflows, tools like [best project management software for startups] can make a significant difference."

❌ **Bad**:
> "In conclusion, we recommend [best project management software for startups 2025 cheap affordable pricing] for your team."

**Anchor Risk Levels**:
- **High**: Exact commercial match in unrelated context
- **Medium**: Partial match in related context
- **Low**: Branded or generic anchor in editorial context

**QC Action**: High-risk anchors → BLOCKED (human review required)

#### 5. Length Matters (But Not More Than Depth)
**Rule**: Meet minimum word count (900), but prioritize depth over filler.

**Quality Hierarchy**:
1. **Best**: 1000 words of deep, well-researched content with examples
2. **Good**: 900 words of solid content, some depth
3. **Acceptable**: 900 words, basic coverage
4. **Bad**: 1200 words of fluff to hit a count

**QC Check**: Word count ≥ 900 AND no repetitive filler detected

**Why**: Google rewards comprehensive content, not just long content.

---

### UX Quality Principles

#### 1. Zero-to-Value in 60 Seconds
**Rule**: A new user should generate their first article within 60 seconds of landing.

**Quick Start Flow**:
1. Dashboard loads (1 sec)
2. User sees "Quick Start" widget (0 sec - visible immediately)
3. User enters 3 fields (10 sec)
4. User clicks "Generate" (1 sec)
5. Article generates (30-45 sec)
6. User sees article + download button (0 sec)

**Total**: ~45-60 seconds

**Anti-Pattern**:
- Multi-page onboarding tutorials
- Required account setup before trial
- Complex configuration screens

**Why**: Fast time-to-value drives adoption. Users commit after seeing results, not before.

#### 2. No Technical Jargon (Unless Necessary)
**Rule**: UI copy should be understandable by a non-technical SEO professional.

✅ **Good**:
- "Generate Article" (not "Execute Job Pipeline")
- "Quality Check Failed" (not "QC Status: BLOCKED")
- "3 articles in progress" (not "3 jobs in PROCESSING state")

❌ **Bad**:
- "Preflight execution timeout"
- "State machine transition error"
- "LLM API rate limit exceeded"

**Exception**: Technical users can access "Advanced" mode with detailed logs and error codes.

**Why**: Users care about outcomes (articles), not implementation details.

#### 3. Progressive Disclosure
**Rule**: Show simple options first, advanced options on demand.

**Quick Start Widget** (Simple):
- 3 fields: Publisher, Target, Anchor
- 1 button: "Generate Article"

**Job Creation Wizard** (Advanced):
- Step 1: Basic inputs
- Step 2: LLM provider selection
- Step 3: Strategy (multi-stage vs single-shot)
- Step 4: Advanced options (country, Ahrefs, LLM profiling)

**Why**: Reduces cognitive load for beginners, power users can still access all features.

#### 4. Real-Time Feedback
**Rule**: Never leave users waiting without feedback.

**Loading States**:
- Job submitted → "Starting..." (0-2 sec)
- SERP research → "Analyzing search results..." (5-10 sec)
- Profiling → "Understanding publisher tone..." (5-10 sec)
- Writing → "Generating article..." (15-30 sec)
- QC → "Quality check..." (2-5 sec)

**Progress Bar**: Shows % complete (0% → 10% → 50% → 90% → 100%)

**Why**: Users tolerate 60-second waits if they see progress. 10-second black-box waits feel like failures.

#### 5. Error Messages Are Actionable
**Rule**: Error messages must explain WHAT went wrong and HOW to fix it.

✅ **Good**:
> "Quality Check Failed: Article is only 750 words (minimum 900). This usually happens when the target page has little content. Try a different target URL or contact support."

❌ **Bad**:
> "Error: QC_WORD_COUNT_BELOW_THRESHOLD"

**Error Template**:
1. **What happened**: "Article generation failed"
2. **Why**: "Target URL could not be accessed (timeout)"
3. **How to fix**: "Check that the URL is correct and publicly accessible, or try again in a few minutes"

**Why**: Users can self-serve fixes instead of contacting support.

---

### Operational Quality Principles

#### 1. Logging Is Not Optional
**Rule**: Every state transition, API call, and error must be logged.

**Minimum Log Data**:
- Timestamp (ISO 8601)
- Job ID
- Module/function name
- Event type (state_transition, api_call, error)
- Relevant context (model name, token count, error message)

**Log Levels**:
- **DEBUG**: Detailed execution traces (dev only)
- **INFO**: State transitions, normal operations
- **WARNING**: Recoverable issues (timeouts with retry)
- **ERROR**: Failures requiring attention

**Why**: Production debugging is impossible without logs.

#### 2. Secrets Are Rotated Regularly
**Rule**: API keys, database passwords, and tokens must be rotatable without code changes.

**Best Practices**:
- Store secrets in environment variables or secret managers (AWS Secrets Manager, HashiCorp Vault)
- Set calendar reminders to rotate keys every 90 days
- Monitor API usage for unauthorized access

**Why**: Security incidents (key leaks) are recoverable if rotation is easy.

#### 3. Costs Are Visible & Controllable
**Rule**: Users must see costs BEFORE and AFTER every operation.

**Cost Visibility**:
- Pre-job: "Estimated cost: $0.06"
- Post-job: "Actual cost: $0.058"
- Batch: "Estimated total: $10.50 (175 jobs × $0.06)"

**Cost Controls**:
- Daily spending limit: "Stop if daily cost > $50"
- Per-job limit: "Block jobs estimated > $1.00"
- Budget alerts: "You've spent $40 today (80% of limit)"

**Why**: Unexpected bills destroy user trust.

#### 4. Failures Are Recoverable
**Rule**: Transient failures (network, rate limits) should auto-retry. Persistent failures should save state for manual review.

**Retry Strategy**:
- Transient errors: Exponential backoff (2s, 4s, 8s, 16s), max 4 retries
- Rate limits: Wait + retry (respect Retry-After header)
- Persistent errors: Save job to dead-letter queue, alert user

**State Checkpointing** (for batches):
- Save progress every 10 jobs
- On crash, resume from last checkpoint
- Don't lose 100 jobs because job 101 failed

**Why**: Resilience prevents wasted time and money.

#### 5. Multi-Tenancy Is Isolated
**Rule**: User A cannot access User B's jobs, articles, or settings.

**Isolation Requirements**:
- Database: Row-level security (user_id foreign key)
- API: JWT or API key authentication on every request
- Storage: User-specific directories or database records
- Logs: Scrub PII before logging

**Why**: Security and compliance (GDPR, SOC 2).

---

## Improvement Loop for Future LLMs

> **Purpose**: This section defines a repeatable process for future LLM sessions to systematically improve BACOWR without breaking existing functionality.

### The 5-Step Improvement Loop

#### Step 1: Read & Understand Context
**Before touching ANY code**, read these files in order:

1. **This document** (`docs/bacowr_vision_and_quality.md`)
   - Understand the vision, quality principles, and known gaps
2. **Master orchestration checklist** (`bacowr_master_orchestration_checklist.json`)
   - See what modules exist, their status, and dependencies
3. **README.md**
   - Understand current features and how to run the system
4. **Relevant module docs** (e.g., `PRODUCTION_GUIDE.md`, `BATCH_GUIDE.md`, `API_GUIDE.md`)
   - Deep dive into the specific area you're working on

**LLM Instruction Box:**
```
🤖 LLM: Before writing ANY code in a BACOWR session, you MUST:
1. Read this vision document (you are reading it now - good!)
2. Read bacowr_master_orchestration_checklist.json to see system structure
3. Identify which module (A-N) your task belongs to
4. Read that module's existing code in src/ to understand what's already there

NEVER create parallel implementations. ALWAYS extend existing modules.
```

#### Step 2: Identify Gaps
**Systematically search for gaps in the area you're working on.**

**Questions to Ask**:
- **Architecture**: Are there TODOs, stubs, or placeholder functions?
- **Error handling**: What happens if API calls fail? Timeouts? Invalid input?
- **Edge cases**: What if the publisher site is down? Target URL is a PDF? Anchor is 200 characters?
- **Performance**: Will this work with 1000 jobs? 10,000?
- **Security**: Can a malicious user exploit this?
- **UX**: Will a non-technical user understand this error message?
- **Tests**: Are there tests for this code? Do they cover edge cases?

**Gap Documentation**:
When you find a gap, add it to the "Gap Analysis & Risk Areas" section of this document:
```markdown
### [Area Name]
- **Current**: [What exists today]
- **Gap**: [What is missing or incomplete]
- **Risk**: [What could go wrong]
- **Impact**: [High/Medium/Low]
- **Mitigation**: [How to fix it - be specific]
```

#### Step 3: Prioritize Improvements
**Not all gaps are equal. Use the priority matrix:**

| Priority | Impact | Urgency | Examples |
|----------|--------|---------|----------|
| **P0** | High | High | Database integration, multi-user auth, API backend |
| **P1** | High | Medium | Batch QA workflow, cost enforcement |
| **P2** | Medium | Medium | Intent edge cases, Heavy Preflight |
| **P3** | Medium | Low | Observability, advanced analytics |
| **P4** | Low | Low | Nice-to-have features, polish |

**Rule**: Only work on P0/P1 items unless explicitly told otherwise. P2+ goes into `future.md` (see next section).

#### Step 4: Implement & Test
**Make the improvement, following the Quality Charter.**

**Implementation Checklist**:
- [ ] Code follows Quality Charter principles (modularity, type hints, logging, error handling)
- [ ] Prompts follow Prompt Quality Principles (clarity, explicit constraints, no fluff)
- [ ] Tests are written or updated (run `python tests/test_*.py`)
- [ ] Documentation is updated (README, module docs, docstrings)
- [ ] Checklist status is updated (`bacowr_master_orchestration_checklist.json`)

**LLM Instruction Box:**
```
🤖 LLM: After implementing a change:
1. Run relevant tests: python tests/test_[module].py
2. Update status in bacowr_master_orchestration_checklist.json
3. Update this vision doc if you've closed a gap or found new ones
4. Commit with a clear message: "feat(module): description of change"
```

#### Step 5: Update This Document
**Keep the vision document accurate and up-to-date.**

**What to Update**:
- **Gap Analysis**: Remove closed gaps, add newly discovered gaps
- **System Vision**: Update status checkboxes if features are complete
- **Quality Charter**: Add new principles if you've learned something important
- **Improvement Loop**: Refine this loop itself if you found it unclear

**Anti-Pattern**:
- ❌ Make code changes but don't update docs
- ❌ Close a gap but leave it listed as "Open"
- ❌ Find a new gap but don't document it

**Why**: Future LLM sessions depend on this document being accurate. Stale docs = wasted effort.

---

### When to Run the Improvement Loop

**Trigger Events**:
1. **User reports a bug**: Run loop to fix + find related gaps
2. **New feature request**: Run loop to design + implement + test
3. **Periodic quality audit**: Every 10-20 sessions, run full loop on all modules
4. **Before major version bump**: Run loop to close all P0/P1 gaps

**Ownership**:
Each LLM session owns ONE module at a time. Don't try to fix everything in one session—focus, finish, then move to next module.

---

## Future Loop & Idea Incubator

> **Purpose**: Separate creative ideation from production development. Keep the main roadmap focused while allowing free exploration of new possibilities.

### The Problem This Solves

**Without an idea loop**:
- Good ideas get lost (mentioned in a session, never captured)
- Experimental features creep into production code (instability)
- No clear place to capture "future nice-to-haves"
- LLMs feel pressure to implement everything immediately (scope creep)

**With an idea loop**:
- ✅ Ideas are captured in `future.md`
- ✅ Production code stays stable
- ✅ Humans can cherry-pick ideas when ready
- ✅ LLMs can freely brainstorm without breaking things

### The Idea Loop Workflow

```
┌─────────────────────────────────────────┐
│  1. Read Context                        │
│  - bacowr_vision_and_quality.md         │
│  - bacowr_master_orchestration_...json  │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  2. Generate Ideas (3-10 new ideas)     │
│  - Simplify existing flows              │
│  - Improve SEO quality/QA/UX            │
│  - New related projects                 │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  3. Evaluate Each Idea                  │
│  - Impact: Low/Medium/High              │
│  - Effort: Low/Medium/High              │
│  - Risk: Low/Medium/High                │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  4. Save to future.md                   │
│  - Backlog (short term)                 │
│  - Incubator (future projects)          │
│  - Archived/Rejected                    │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  5. NO direct changes to main code      │
│  - Ideas stay in future.md              │
│  - Humans decide when to implement      │
└─────────────────────────────────────────┘
```

### File: `future.md`

**Location**: `docs/future.md`

**Structure**:
```markdown
# BACOWR Future Ideas & Incubator

## Backlog (Short Term)
Ideas that can realistically be added to the current roadmap.

### Idea: [Title]
- **Description**: [What it is]
- **Impact**: [Low/Medium/High - how much value]
- **Effort**: [Low/Medium/High - how complex]
- **Risk**: [Low/Medium/High - technical/business risk]
- **Depends On**: [Modules or features that must exist first]
- **Proposed By**: [LLM session ID or human]
- **Date**: [ISO date]

## Incubator (Future Projects)
Larger or more experimental ideas that may become separate projects.

### Idea: [Title]
...

## Archived / Rejected
Ideas that have been considered but are not being pursued.

### Idea: [Title]
- **Reason for rejection**: [Why we decided not to do this]
...
```

### Example Ideas (for illustration)

**Backlog (Short Term)**:
1. **Smart Anchor Rewriting**
   - **Description**: If QC detects high-risk anchor, suggest safer alternatives (exact → branded, commercial → generic)
   - **Impact**: Medium (reduces QC blocks)
   - **Effort**: Medium (requires anchor risk logic extension)
   - **Risk**: Low
   - **Depends On**: Module C (Preflight), QC system

2. **Cost Budget Dashboard**
   - **Description**: Frontend widget showing daily/weekly/monthly spend, with alerts when approaching limits
   - **Impact**: Medium (improves user trust)
   - **Effort**: Low (frontend only, data already tracked)
   - **Risk**: Low

**Incubator (Future Projects)**:
1. **BACOWR Scraper Studio**
   - **Description**: Visual tool to configure custom scrapers for new publishers (drag-drop CSS selectors, test on live pages)
   - **Impact**: High (expands publisher coverage massively)
   - **Effort**: High (new project, separate UI)
   - **Risk**: Medium (complex UX, maintenance)

2. **SEO Campaign Manager**
   - **Description**: Track backlinks across clients, monitor rankings, measure ROI, alert on rank drops
   - **Impact**: High (turns BACOWR into a platform)
   - **Effort**: Very High (database redesign, new APIs, separate frontend)
   - **Risk**: High (scope creep, market fit uncertain)

**Archived / Rejected**:
1. **AI-Generated Images for Articles**
   - **Description**: Use DALL-E/Midjourney to generate featured images
   - **Reason for rejection**: Copyright risk, quality inconsistency, adds cost without clear SEO benefit

### Rules for LLMs Working with future.md

**DO**:
- ✅ Add new ideas freely when asked to "think creatively" or "find improvements"
- ✅ Categorize ideas clearly (Backlog vs Incubator)
- ✅ Be honest about Impact/Effort/Risk (don't oversell ideas)
- ✅ Link ideas to existing modules in the checklist

**DON'T**:
- ❌ Implement ideas from future.md without explicit human approval
- ❌ Move ideas from future.md to the main checklist on your own
- ❌ Change main codebase while "exploring ideas"
- ❌ Reject ideas prematurely—when in doubt, add to Incubator

**Human Gatekeeping**:
Only a human can:
- Move an idea from future.md to the main roadmap
- Approve implementation of an idea
- Reject ideas permanently

LLMs propose, humans decide.

---

## How to Use This Document in a New Session

> **Audience**: You, the LLM reading this in a future BACOWR session.

### You Are Reading This Because...

One of these scenarios applies:
1. **User asked you to improve BACOWR**: They want you to fix a bug, add a feature, or refactor code.
2. **User asked you to review quality**: They want you to audit BACOWR and suggest improvements.
3. **User asked you to brainstorm**: They want new ideas for features or spin-off projects.
4. **User sent you this doc as context**: They want you to understand BACOWR before starting work.

### What to Do Next (By Scenario)

#### Scenario 1: Implementing a Feature or Fix

**Your workflow**:
1. ✅ **You are here**: You've read this vision doc (good!)
2. **Next**: Read `bacowr_master_orchestration_checklist.json`
   - Find the module (A-N) your task belongs to
   - Check its status and dependencies
3. **Then**: Read existing code in `src/[module]/`
   - Understand what's already implemented
   - Look for TODOs, stubs, or areas to extend
4. **Implement**: Follow the [Quality Charter](#quality-charter)
   - Write modular, typed, well-logged code
   - Write or update tests
   - Update docs
5. **Update**: Modify checklist status, update this vision doc if you closed a gap

**Example**:
> User: "Add API endpoint for listing all jobs for a user"

You:
1. Read this doc ✅
2. Read checklist → This is **Module H** (API Gateway)
3. Read `src/api/server.py` → See existing `/jobs/full-run` endpoint
4. Add new `GET /jobs` endpoint with pagination
5. Write tests in `tests/test_api.py`
6. Update `API_GUIDE.md` with new endpoint docs
7. Update checklist: H1 status → `present` (if it was `partial`)

#### Scenario 2: Quality Audit

**Your workflow**:
1. ✅ **You are here**: You've read this vision doc
2. **Next**: Read the [Gap Analysis & Risk Areas](#gap-analysis--risk-areas) section
   - Understand what gaps are already known
3. **Then**: Run the [Improvement Loop](#improvement-loop-for-future-llms)
   - Step 1: Read all context docs
   - Step 2: Identify new gaps (architecture, SEO, ops, UX)
   - Step 3: Prioritize gaps (P0-P4)
   - Step 4: Implement fixes for P0/P1 gaps (if time allows)
   - Step 5: Update this doc with findings
4. **Report**: Summarize what you found and what you fixed

**Example**:
> User: "Audit BACOWR for quality issues"

You:
1. Read this doc ✅
2. Review Gap Analysis → See "Database Integration" is a known P0 gap
3. Check `src/` → Confirm storage is still file-based
4. Scan `src/api/` → Find missing user management endpoints
5. Add to Gap Analysis: "API user management incomplete"
6. Prioritize: P0 (blocks hosted app)
7. (If time) Implement user endpoints or create design doc
8. Report: "Found 3 P0 gaps, implemented 1, documented 2 for next session"

#### Scenario 3: Idea Generation

**Your workflow**:
1. ✅ **You are here**: You've read this vision doc
2. **Next**: Read [Future Loop & Idea Incubator](#future-loop--idea-incubator)
   - Understand the idea loop process
3. **Then**: Brainstorm 5-10 new ideas
   - Focus on: simplifying flows, improving quality, new tools, spin-off projects
4. **Evaluate**: For each idea, assess Impact/Effort/Risk
5. **Save**: Add ideas to `docs/future.md` (don't implement!)
6. **Report**: Summarize ideas and ask user which to prioritize

**Example**:
> User: "What are some ideas to make BACOWR better?"

You:
1. Read this doc ✅
2. Read Future Loop section ✅
3. Generate ideas:
   - "Smart anchor rewriting" (Medium impact, Medium effort)
   - "Visual scraper config tool" (High impact, High effort)
   - "A/B test two article versions" (Low impact, Medium effort)
4. Add to `docs/future.md` under "Backlog" or "Incubator"
5. Report: "Added 3 ideas to future.md. Which would you like me to design in detail?"

#### Scenario 4: Starting Fresh (No Specific Task)

**Your workflow**:
1. ✅ **You are here**: You've read this vision doc
2. **Ask the user**: "What would you like me to work on?"
3. **Suggest**: Based on Gap Analysis, recommend P0/P1 items
4. **Wait for direction**: Don't start coding randomly

**Example**:
> User: "Here's the BACOWR repo, I've shared the vision doc as context"

You:
1. Read this doc ✅
2. Say: "I've reviewed the BACOWR vision doc. I can see there are several high-priority gaps:
   - P0: Database integration (Module F2)
   - P0: API backend completion (Module H)
   - P1: Batch QA workflow (Module G3)

   Which would you like me to focus on? Or is there a specific task you have in mind?"

---

## Concrete Checklist for LLMs

> **Use this checklist at the START of every BACOWR session.**

### Pre-Work Checklist

Before writing ANY code:

- [ ] I have read `docs/bacowr_vision_and_quality.md` (this document)
- [ ] I have read `bacowr_master_orchestration_checklist.json`
- [ ] I have identified which module (A-N, Q) my task belongs to
- [ ] I have checked the module's `status` and `dependencies` in the checklist
- [ ] I have read the existing code in `src/[module]/` to understand what's already there
- [ ] I have read relevant docs (`PRODUCTION_GUIDE.md`, `BATCH_GUIDE.md`, `API_GUIDE.md`, etc.)
- [ ] I understand the user's request and can map it to a specific task in the checklist

### During Work Checklist

While implementing:

- [ ] My code follows the **Code Quality Principles** (modularity, type hints, no hardcoded secrets, error handling, testability)
- [ ] My prompts follow the **Prompt Quality Principles** (clarity, explicit constraints, context-first, no fluff, output format)
- [ ] My implementation respects the **SEO Quality Principles** (intent first, natural language, trust sources, anchor naturalness, depth over length)
- [ ] My UX follows the **UX Quality Principles** (zero-to-value in 60s, no jargon, progressive disclosure, real-time feedback, actionable errors)
- [ ] My deployment/ops follows the **Operational Quality Principles** (logging, secret rotation, cost visibility, failure recovery, multi-tenancy isolation)
- [ ] I have written or updated tests in `tests/`
- [ ] I have updated documentation (README, module guides, docstrings)
- [ ] I have run existing tests to ensure I didn't break anything

### Post-Work Checklist

After completing work:

- [ ] I have updated `bacowr_master_orchestration_checklist.json` with new statuses
- [ ] I have updated `docs/bacowr_vision_and_quality.md` if I:
  - Closed a gap (remove from Gap Analysis)
  - Discovered a new gap (add to Gap Analysis)
  - Learned a new quality principle (add to Quality Charter)
- [ ] If I generated ideas, I have added them to `docs/future.md` (not to main codebase)
- [ ] I have committed changes with a clear commit message format:
  - `feat(module): description` for new features
  - `fix(module): description` for bug fixes
  - `docs(module): description` for documentation
  - `refactor(module): description` for refactoring
  - `test(module): description` for tests
- [ ] I have summarized my work for the user in plain language

### Emergency Checklist (If Things Go Wrong)

If you encounter unexpected issues:

- [ ] I have checked the execution logs: `storage/output/{job_id}_execution_log.json`
- [ ] I have checked the QC report: `storage/output/{job_id}_qc_report.json`
- [ ] I have checked relevant module logs (if logging is implemented)
- [ ] I have read error messages carefully and looked for root causes
- [ ] I have checked the Gap Analysis to see if this is a known issue
- [ ] I have documented the issue in Gap Analysis if it's new
- [ ] I have asked the user for clarification instead of guessing

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0.0 | 2025-11-19 | Initial vision document created with all core sections: Overview, User Story, System Vision, Gap Analysis, Quality Charter, Improvement Loop, Future Loop, LLM Instructions, Checklist | Claude (Team Q) |

---

## Appendix A: Key Terminology

**For LLMs and humans new to BACOWR:**

### Core Concepts
- **Preflight**: The research phase before article generation (fetching HTML, profiling publisher/target, SERP research)
- **Light Preflight**: Basic HTML extraction and profiling (current implementation - Module C)
- **Heavy Preflight**: Advanced SERP analysis with intent modeling, trust policies, LSI windows (future feature - Module M)
- **QC (Quality Control)**: Automated validation of generated articles against SEO and content quality rules
- **AutoFix**: Automatic correction of minor QC issues (e.g., moving link placement, injecting LSI terms)
- **State Machine**: The job execution flow (RECEIVE → PREFLIGHT → WRITE → QC → DELIVER, with RESCUE for retries)
- **RESCUE**: One-time retry if QC fails but issue is auto-fixable
- **Job Package**: Complete data structure containing all inputs, profiles, research, and generated content for a job (see `backlink_job_package.schema.json`)

### SEO Concepts
- **Intent Alignment**: Matching article intent (informational/commercial/transactional) to SERP intent
- **LSI (Latent Semantic Indexing) Terms**: Related keywords that support topic relevance (e.g., for "project management": "team collaboration", "task tracking", "workflow")
- **Trust Sources**: Citations from authoritative sites (gov, edu, major news) to improve E-A-T (Expertise, Authoritativeness, Trustworthiness)
- **Anchor Risk**: Likelihood that an anchor text pattern will be flagged as manipulative by search engines
  - **High risk**: Exact commercial match in unrelated context ("buy viagra online" in cooking blog)
  - **Medium risk**: Partial match in related context ("best CRM software" in productivity article)
  - **Low risk**: Branded or generic anchor ("read more", "Company X", "this guide")
- **Bridge Type**: The connection style between publisher content and target
  - **Strong**: Direct topic match (article about CRM tools → CRM product page)
  - **Pivot**: Related topic (article about productivity → CRM product page)
  - **Wrapper**: Tangential connection (article about remote work → CRM product page)
- **T1/T2/T3/T4 Sources**: Trust tier classification
  - **T1**: .gov, .edu, Wikipedia, major news (BBC, Reuters, NY Times)
  - **T2**: Industry publications, well-known blogs, established companies
  - **T3**: Smaller blogs, forums, user-generated content
  - **T4**: Unknown or low-authority sites

### Technical Terms
- **Batch Processing**: Running multiple jobs (e.g., 175 articles) in one orchestrated session
- **Rate Limiting**: Controlling API call frequency to respect provider limits (e.g., 10 calls/minute)
- **Multi-Stage Strategy**: 3-step LLM generation (outline → content → polish) for highest quality
- **Single-Shot Strategy**: 1-step LLM generation for speed
- **Job Status**: PENDING → PROCESSING → DELIVERED / BLOCKED / ABORTED
- **Execution Log**: JSON trace of all state transitions and events for a job

## Appendix B: Module Reference (Quick Lookup)

**Use this to quickly find which module owns what:**

| Module | Name | Primary Responsibility | Key Files |
|--------|------|------------------------|-----------|
| **A** | Repository & Core Docs | Project structure, architecture docs | `README.md`, `BACOWR_ARCHITECTURE.md` |
| **B** | Domain Models & Config | Data models, settings, configuration | `src/qc/models.py`, config files |
| **C** | Preflight Engine (Light) | HTML fetching, basic profiling | `src/profiling/page_profiler.py` |
| **D** | LLM Client | Article generation via Claude/GPT/Gemini | `src/writer/production_writer.py` |
| **E** | Orchestrator | Single job & batch orchestration | `src/production_api.py`, `batch_runner.py` |
| **F** | Storage Layer | File-based storage, future DB integration | `storage/output/`, future DB layer |
| **G** | QA & Status | QC system, Day 2 QA workflow | `src/qc/quality_controller.py` |
| **H** | API Gateway | FastAPI backend, REST endpoints | `src/api/` (future) |
| **I** | CLI / Research Export | Command-line tools, keyless mode | `main.py`, `production_main.py` |
| **J** | API Contract | Frontend-backend contract docs | `docs/frontend_and_api_contract.md` (future) |
| **K** | Frontend Webapp | Next.js web application | `frontend/` |
| **L** | Deployment & Ops | Docker, logging, monitoring | `Dockerfile`, logging config |
| **M** | Heavy Preflight Stubs | Advanced SERP analysis (future) | `docs/preflight_heavy.md` |
| **N** | Tests & Sanity Checks | Test suite, smoke tests | `tests/` |
| **Q** | Vision & Quality Charter | This document, future.md | `docs/bacowr_vision_and_quality.md`, `docs/future.md` |

**LLM Quick Reference:**
- Working on profiling? → **Module C**
- Working on LLM prompts? → **Module D**
- Working on QC rules? → **Module G**
- Working on batch processing? → **Module E**
- Working on API endpoints? → **Module H**
- Working on frontend? → **Module K**
- Adding new ideas? → **Module Q** (`future.md`)

## Appendix C: File Locations (Quick Navigation)

**Core system files:**
```
bacowr_master_orchestration_checklist.json    # Master task checklist (modules A-N)
backlink_job_package.schema.json              # JSON schema (single source of truth)
next-a1-spec.json                              # Next-A1 specification
NEXT-A1-ENGINE-ADDENDUM.md                     # Del 2 & 3 requirements

docs/
├── bacowr_vision_and_quality.md               # This document (Module Q)
├── future.md                                   # Idea incubator (Module Q)
└── (other guides as needed)

src/
├── api.py                                      # Main API (mock mode)
├── production_api.py                           # Production API with LLM
├── qc/
│   ├── models.py                              # QC models (QCReport, QCIssue, AutoFixLog)
│   └── quality_controller.py                  # QC system
├── engine/
│   ├── state_machine.py                       # State machine with loop protection
│   └── execution_logger.py                    # Execution logging
├── profiling/
│   ├── page_profiler.py                       # URL profiling
│   └── llm_enhancer.py                        # LLM-enhanced profiling
├── research/
│   ├── serp_researcher.py                     # Mock SERP
│   └── ahrefs_serp.py                         # Ahrefs API integration
├── analysis/
│   └── intent_analyzer.py                     # Intent alignment
└── writer/
    ├── writer_engine.py                       # Mock writer
    └── production_writer.py                   # Multi-LLM writer

tests/
├── test_schema_validation.py
├── test_live_validation.py
├── test_qc_system.py
├── test_e2e_mock.py
└── (other tests)

config/
├── thresholds.yaml                            # QC thresholds
└── policies.yaml                              # AutoFix policies

storage/
├── output/                                     # Single job outputs
├── batch_output/                               # Batch outputs
└── batch_chunks/                               # Scheduled batch chunks
```

---

**End of Document**

This vision document is a living blueprint. Update it whenever you learn something new about BACOWR, its gaps, or its quality standards. Future LLM sessions depend on its accuracy.

*"Quality is not an act, it is a habit."* — Aristotle
