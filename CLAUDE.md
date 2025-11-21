# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BACOWR (BacklinkContent Orchestration With Refinement) is a production-ready backlink content generation engine implementing the Next-A1 SEO framework. The system takes three inputs (publisher domain, target URL, anchor text) and generates publication-ready backlink articles with full QC validation, traceability, and SERP-driven content strategy.

## Essential Commands

### Python Backend & Core Engine

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests - ALL tests must pass before committing
pytest                                    # All tests
python tests/test_schema_validation.py    # Schema validation
python tests/test_qc_system.py            # QC system (7 tests)
python tests/test_e2e_mock.py             # E2E pipeline (7 tests)
python tests/test_intent_analyzer.py      # Intent analyzer (26 tests)
pytest tests/ -v                          # Verbose output

# Generate single article (mock mode - no API keys needed)
python main.py --publisher example.com --target https://target.com --anchor "text" --mock

# Generate single article (production mode - requires API keys)
python production_main.py \
  --publisher example.com \
  --target https://target.com \
  --anchor "text" \
  --llm anthropic \
  --strategy multi_stage

# Batch processing
python batch_runner.py --input jobs.csv --parallel 3
python batch_monitor.py --watch storage/batch_output/

# Interactive quick start
python quickstart.py

# Code quality
black src/ tests/                         # Format code
flake8 src/ tests/                        # Lint
mypy src/                                 # Type check
```

### FastAPI Backend

```bash
# Run API server
cd api
uvicorn app.main:app --reload             # Development
uvicorn app.main:app --host 0.0.0.0 --port 8000  # Production

# Database migrations
alembic upgrade head                      # Apply migrations
alembic revision --autogenerate -m "msg" # Create migration

# API docs available at http://localhost:8000/docs
```

### Next.js Frontend

```bash
cd frontend
npm install                               # Install dependencies
npm run dev                               # Development server (port 3000)
npm run build                             # Production build
npm start                                 # Production server
npm run lint                              # Lint
npm run type-check                        # TypeScript check
```

### Docker Deployment

```bash
# Start all services (API + PostgreSQL + pgAdmin)
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop all services
docker-compose down
```

## Architecture

### System Components

**Three-Tier Architecture:**
1. **Core Engine** (`src/`) - Python modules for content generation
2. **API Layer** (`api/`) - FastAPI REST API with PostgreSQL
3. **Frontend** (`frontend/`) - Next.js 14 web interface

### Core Engine Pipeline (src/)

The engine follows a deterministic state machine pattern:

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                        ↓      ↓
                     ABORT  RESCUE (AutoFixOnce, max 1 attempt)
```

**Key Modules:**

- **profiling/** - URL scraping and profiling (PageProfiler, LLM enhancer)
- **research/** - SERP data fetching (Ahrefs API + mock mode)
- **analysis/** - Intent modeling and alignment scoring
- **writer/** - Multi-LLM content generation (Anthropic, OpenAI, Google)
- **qc/** - Quality control validation and AutoFixOnce system
- **engine/** - State machine orchestration and execution logging
- **export/** - Google Sheets/Docs integration

**Critical Flow:**
1. **Profiling** extracts entities, language, tone from publisher and target URLs
2. **SERP Research** fetches top results and identifies dominant intent
3. **Intent Analysis** aligns publisher-anchor-target-SERP and recommends bridge type
4. **Writer Engine** generates content using multi-stage or single-shot strategy
5. **QC System** validates against Next-A1 requirements, triggers AutoFixOnce if needed
6. **State Machine** orchestrates flow with loop protection and full logging

### Multi-LLM Support

The system supports three LLM providers with automatic fallback:
- **Anthropic Claude**: Haiku (fast/cheap), Sonnet (balanced), Opus (best quality)
- **OpenAI GPT**: GPT-4o, GPT-4o-mini, GPT-4-turbo
- **Google Gemini**: Flash (fast), Pro 1.5, Pro 1.0

Set `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY` environment variables.

### API Backend (api/)

FastAPI application with:
- **Authentication**: API key-based auth
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite
- **Models**: Jobs, Users, Batches, Backlinks, Analytics, Audit logs
- **WebSocket**: Real-time job progress updates
- **Middleware**: Rate limiting, quota management, Prometheus metrics

### Frontend (frontend/)

Next.js 14 App Router application:
- **State**: Zustand stores + TanStack Query for server state
- **Real-time**: Socket.io client for WebSocket updates
- **Routing**: App Router with dynamic routes for jobs/batches
- **Styling**: Tailwind CSS + Radix UI components

## Next-A1 Framework Implementation

**Critical Concept - Variabelgiftermål (Variable Marriage):**
Content must align four dimensions: Publisher role, Anchor intent, Target offer, and SERP intent.

**Bridge Types** (selected automatically by intent analyzer):
- **Strong**: Direct connection, high alignment, needs 1 trust source
- **Pivot**: Thematic bridge, partial alignment, needs 1-2 trust sources
- **Wrapper**: Meta-frame strategy, low alignment acceptable, needs 2-3 trust sources

**Trust Policy (T1→T2→T3→T4):**
- T1: Government, official standards (highest priority)
- T2: Academic, peer-reviewed
- T3: Industry organizations
- T4: Reputable media (fallback only)

**QC Requirements** (enforced in `config/thresholds.yaml`):
- LSI: 6-10 relevant terms within ±2 sentences of link
- Anchor placement: NEVER in H1/H2, preferred in middle sections
- Trust sources: Minimum 1 T1-T3 source, never link competitors
- Compliance: Disclaimers required for regulated verticals (gambling, finance, health, legal)

**AutoFixOnce** (defined in `config/policies.yaml`):
- Exactly ONE automatic fix attempt allowed per job
- Fixes: Link placement adjustment, LSI injection, anchor type adjustment, compliance additions
- Blocking conditions trigger human signoff: intent="off", zero trust sources, high anchor risk

## Configuration & Schema

**Single Source of Truth:**
- `backlink_job_package.schema.json` - Defines BacklinkJobPackage contract
- All code must validate against this schema

**Critical Config Files:**
- `config/thresholds.yaml` - QC validation rules and thresholds
- `config/policies.yaml` - AutoFixOnce policies and blocking conditions
- `.env` - API keys and runtime configuration (see `.env.example`)

**Required Environment Variables:**
- At least one: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GOOGLE_API_KEY`
- Optional: `AHREFS_API_KEY` (for real SERP data), `GOOGLE_CREDENTIALS_PATH` (for export)

## Output Structure

All jobs generate to `storage/output/{job_id}_*`:
- `*_job_package.json` - Complete BacklinkJobPackage (must validate against schema)
- `*_article.md` - Generated markdown article (≥900 words)
- `*_qc_report.json` - QC validation with issues and autofix logs
- `*_execution_log.json` - State machine trace with timestamps
- `*_metrics.json` - Cost tracking and performance data

## Testing Philosophy

**Schema Validation is Critical:**
- `test_schema_validation.py` validates all job packages against JSON schema
- `test_live_validation.py` runs end-to-end with schema validation
- Schema violations block commits - this ensures contract stability

**Test Coverage:**
- 80+ tests covering all components
- Mock mode allows testing without API costs
- E2E tests validate full pipeline determinism

**Before Committing:**
Run full test suite: `pytest` - ALL tests must pass.

## Important Patterns & Conventions

**State Machine Loop Protection:**
The engine hashes payloads after WRITE and RESCUE. If identical, it aborts to prevent infinite loops. This is critical - never bypass this check.

**LLM-Enhanced Profiling:**
PageProfiler can use LLM to extract tone, style, and better entities. Toggle with `enable_llm_profiling` flag. Adds cost but improves quality significantly.

**Bridge Type Selection:**
Intent analyzer calculates publisher-target niche overlap and alignment scores to automatically recommend strong/pivot/wrapper bridge. Trust the algorithm - it implements Next-A1 spec.

**Cost Tracking:**
All LLM calls are tracked with token counts and costs. Use `cost_calculator.py` to estimate batch jobs before running.

**Batch Processing:**
- Sequential: `batch_runner.py --input jobs.csv`
- Parallel: `batch_runner.py --input jobs.csv --parallel 3 --rate-limit 10`
- Scheduled: `batch_scheduler.py --time 23:00 --chunk-size 25`

## Development Workflow

1. **Make changes** to source code
2. **Run tests**: `pytest` (all must pass)
3. **Test locally**: `python production_main.py --publisher test.com --target https://example.com --anchor "test"`
4. **Validate output**: Check `storage/output/` for job package, article, QC report
5. **Format code**: `black src/ tests/`
6. **Commit** with descriptive message

## Key Documentation Files

- **README.md** - Complete project overview and quick start
- **PRODUCTION_GUIDE.md** - Production deployment and usage patterns
- **BATCH_GUIDE.md** - Comprehensive batch processing documentation
- **NEXT-A1-ENGINE-ADDENDUM.md** - Formal Next-A1 requirements and acceptance criteria
- **backlink_engine_ideal_flow.md** - Detailed ideal flow documentation
- **api/README.md** - API documentation and endpoints
- **frontend/README.md** - Frontend features and development

## Common Issues

**"No LLM API keys found"**: Set at least one of ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY

**QC keeps blocking**: Check `*_qc_report.json` for specific issues. Common causes: missing trust sources, poor intent alignment, forbidden link placement. May need to adjust thresholds in `config/thresholds.yaml` but be cautious - thresholds enforce Next-A1 compliance.

**Schema validation fails**: The schema is the contract. If code generates job packages that fail validation, the code is wrong, not the schema. Fix the generation logic.

**State machine loops**: Should never happen due to hash-based loop detection. If it does, check execution_log.json for the failure point.

## Git Branch Strategy

- `main` - Production-ready code
- `claude/*` - Feature branches created by Claude Code
- Always develop on feature branches starting with `claude/`
- Push with: `git push -u origin <branch-name>`
