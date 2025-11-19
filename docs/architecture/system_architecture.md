# BACOWR System Architecture

**Version:** 1.0.0
**Last Updated:** 2025-11-19
**Purpose:** Visual architecture documentation for BACOWR system
**Audience:** Developers, LLMs, architects, technical stakeholders

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Module Dependency Graph](#module-dependency-graph)
3. [Data Flow Diagram](#data-flow-diagram)
4. [State Machine](#state-machine)
5. [Component Interaction Map](#component-interaction-map)
6. [Technology Stack](#technology-stack)
7. [Deployment Architecture](#deployment-architecture)

---

## High-Level Architecture

BACOWR follows a **modular, pipeline-based architecture** with clear separation of concerns:

```mermaid
graph TB
    subgraph "User Interface Layer"
        WEB[Web Frontend]
        API[REST API]
        CLI[CLI Interface]
    end

    subgraph "Orchestration Layer"
        ORCH[Orchestrator]
        BATCH[Batch Runner]
        STATE[State Machine]
    end

    subgraph "Processing Layer"
        PRE[Preflight]
        WRITE[Writer]
        QC[Quality Control]
        RESCUE[AutoFix]
    end

    subgraph "Data Layer"
        MODELS[Data Models]
        STORAGE[File Storage]
        CACHE[LLM Cache]
    end

    subgraph "External Services"
        LLM[LLM Providers<br/>Claude/GPT/Gemini]
        SERP[SERP APIs<br/>Ahrefs/Google]
        CMS[CMS APIs<br/>WordPress/Webflow]
    end

    WEB --> API
    CLI --> ORCH
    API --> ORCH
    ORCH --> STATE
    STATE --> PRE
    STATE --> WRITE
    STATE --> QC
    STATE --> RESCUE

    PRE --> MODELS
    WRITE --> MODELS
    QC --> MODELS

    ORCH --> STORAGE
    WRITE --> CACHE

    PRE --> SERP
    WRITE --> LLM
    QC --> CMS

    BATCH --> ORCH

    style WEB fill:#e1f5ff
    style API fill:#e1f5ff
    style CLI fill:#e1f5ff
    style ORCH fill:#fff4e1
    style STATE fill:#fff4e1
    style PRE fill:#e8f5e9
    style WRITE fill:#e8f5e9
    style QC fill:#e8f5e9
    style LLM fill:#fce4ec
    style SERP fill:#fce4ec
```

**Architecture Principles**:
- **Modularity**: Each module (A-Q) has single responsibility
- **Pipeline**: Data flows through stages (PREFLIGHT → WRITE → QC → DELIVER)
- **Stateful**: Jobs tracked through state machine with checkpoints
- **Extensible**: New LLM providers, CMS platforms can be added via adapters
- **Resilient**: Retry logic, RESCUE state, error recovery

---

## Module Dependency Graph

BACOWR has 17 modules (A-Q). This shows their dependencies:

```mermaid
graph LR
    A[A: Project Core]
    B[B: Data Models]
    C[C: Preflight]
    D[D: Writer]
    E[E: Orchestrator]
    F[F: Storage]
    G[G: QC System]
    H[H: API]
    I[I: Input Validation]
    J[J: API Contract]
    K[K: Frontend]
    L[L: Monitoring]
    M[M: Batch]
    N[N: Tests]
    O[O: Deployment]
    P[P: CI/CD]
    Q[Q: Vision & Quality]

    E --> B
    E --> C
    E --> D
    E --> G
    E --> F

    C --> B
    C --> I

    D --> B
    D --> C

    G --> B
    G --> D

    H --> E
    H --> J
    H --> B

    K --> H
    K --> J

    M --> E
    M --> F

    N --> B
    N --> E
    N --> G

    L --> E
    L --> G

    Q --> A
    Q --> E
    Q --> G
    Q --> K
    Q --> L

    style E fill:#ffeb3b
    style B fill:#4caf50
    style G fill:#f44336
    style D fill:#2196f3
    style C fill:#ff9800
```

**Key Modules**:
- **Module E (Orchestrator)**: Central hub, coordinates all modules
- **Module B (Models)**: Foundation, used by almost everyone
- **Module G (QC)**: Quality gatekeeper
- **Module D (Writer)**: LLM integration, content generation
- **Module C (Preflight)**: SERP research and analysis

---

## Data Flow Diagram

End-to-end flow of a single backlink article job:

```mermaid
sequenceDiagram
    participant User
    participant API
    participant Orchestrator
    participant Preflight
    participant Writer
    participant QC
    participant Storage
    participant LLM as LLM Provider
    participant SERP as SERP API

    User->>API: POST /jobs/create<br/>{publisher, target, anchor}
    API->>Orchestrator: create_job(job_package)
    Orchestrator->>Storage: save_job_package()
    Orchestrator->>Orchestrator: state = RECEIVE

    Note over Orchestrator: State: PREFLIGHT
    Orchestrator->>Preflight: run_preflight()
    Preflight->>SERP: fetch_serp_data(target_url)
    SERP-->>Preflight: {top_10_results, intent, LSI}
    Preflight->>Preflight: analyze_anchor_risk()
    Preflight-->>Orchestrator: preflight_package
    Orchestrator->>Storage: save_preflight_data()

    Note over Orchestrator: State: WRITE
    Orchestrator->>Writer: generate_article(preflight_package)
    Writer->>LLM: prompt + context
    LLM-->>Writer: article_text
    Writer->>Writer: inject_backlink(anchor, target)
    Writer-->>Orchestrator: article
    Orchestrator->>Storage: save_article_draft()

    Note over Orchestrator: State: QC
    Orchestrator->>QC: run_qc(article, preflight)
    QC->>QC: check_word_count()
    QC->>QC: check_trust_sources()
    QC->>QC: validate_anchor()

    alt QC PASS
        QC-->>Orchestrator: QCReport(status=PASS)
        Note over Orchestrator: State: DELIVER
        Orchestrator->>Storage: save_final_article()
        Orchestrator->>API: job_complete(SUCCESS)
        API-->>User: 200 OK {article_url}
    else QC FAIL (auto-fixable)
        QC-->>Orchestrator: QCReport(status=FAIL, fixable=true)
        Note over Orchestrator: State: RESCUE
        Orchestrator->>Writer: regenerate_with_fixes(issues)
        Writer->>LLM: prompt + fixes
        LLM-->>Writer: article_v2
        Writer-->>Orchestrator: article_v2
        Orchestrator->>QC: run_qc(article_v2)
        alt QC PASS (after rescue)
            QC-->>Orchestrator: QCReport(status=PASS)
            Note over Orchestrator: State: DELIVER
            Orchestrator->>Storage: save_final_article()
            Orchestrator->>API: job_complete(SUCCESS)
            API-->>User: 200 OK {article_url}
        else QC FAIL (after rescue)
            QC-->>Orchestrator: QCReport(status=FAIL)
            Note over Orchestrator: State: BLOCKED
            Orchestrator->>Storage: save_blocked_job()
            Orchestrator->>API: job_complete(BLOCKED)
            API-->>User: 422 Unprocessable {qc_report}
        end
    else QC FAIL (not fixable)
        QC-->>Orchestrator: QCReport(status=FAIL, fixable=false)
        Note over Orchestrator: State: BLOCKED
        Orchestrator->>Storage: save_blocked_job()
        Orchestrator->>API: job_complete(BLOCKED)
        API-->>User: 422 Unprocessable {qc_report}
    end
```

**Key Flow Points**:
1. **Input Validation** (API layer): Reject malformed requests early
2. **Preflight** (30-90s): Research SERP, assess anchor risk, gather LSI
3. **Write** (20-60s): LLM generates article with context injection
4. **QC** (5-15s): Multi-criteria validation (word count, sources, anchor, intent)
5. **RESCUE** (optional, 20-60s): One retry attempt if issues are auto-fixable
6. **DELIVER or BLOCK**: Final state based on QC outcome

---

## State Machine

The Orchestrator uses a **finite state machine** to track job progress:

```mermaid
stateDiagram-v2
    [*] --> RECEIVE
    RECEIVE --> PREFLIGHT

    PREFLIGHT --> WRITE: Success
    PREFLIGHT --> ERROR: Failure

    WRITE --> QC: Article Generated
    WRITE --> ERROR: LLM Failure

    QC --> DELIVER: PASS
    QC --> RESCUE: FAIL (fixable)
    QC --> BLOCKED: FAIL (not fixable)

    RESCUE --> QC: Retry
    RESCUE --> ERROR: Rescue Failed

    DELIVER --> [*]: Success
    BLOCKED --> [*]: Manual Review Needed
    ERROR --> [*]: System Error

    note right of RECEIVE
        Validate input
        Create job package
    end note

    note right of PREFLIGHT
        Fetch SERP data
        Analyze anchor risk
        Extract LSI terms
        Classify intent
    end note

    note right of WRITE
        Generate article via LLM
        Inject backlink
        Apply tone matching
    end note

    note right of QC
        Word count ≥ 900
        T1 sources ≥ 1
        Anchor naturalness
        Intent alignment
    end note

    note right of RESCUE
        MAX 1 retry per job
        Only if auto-fixable
        Hash check (no duplicates)
    end note
```

**State Definitions**:

| State | Description | Duration | Exit Conditions |
|-------|-------------|----------|-----------------|
| **RECEIVE** | Job created, validated | <1s | Always → PREFLIGHT |
| **PREFLIGHT** | SERP research, anchor analysis | 30-90s | Success → WRITE, Failure → ERROR |
| **WRITE** | LLM article generation | 20-60s | Success → QC, Failure → ERROR |
| **QC** | Quality validation | 5-15s | PASS → DELIVER, FAIL (fixable) → RESCUE, FAIL (not fixable) → BLOCKED |
| **RESCUE** | AutoFix retry (max 1 per job) | 20-60s | Retry → QC, Failure → ERROR |
| **DELIVER** | Article ready for publication | <1s | Terminal state (success) |
| **BLOCKED** | QC failed, manual review needed | - | Terminal state (needs human) |
| **ERROR** | System error occurred | - | Terminal state (failure) |

**State Persistence**: All state transitions logged in `execution_log.json` for debugging and recovery.

---

## Component Interaction Map

How major components communicate:

```mermaid
graph TD
    subgraph "Input Layer"
        USER[User Input]
        VALIDATE[Input Validator]
    end

    subgraph "Core Engine"
        ORCH[Orchestrator]
        SM[State Machine]
        BATCH[Batch Processor]
    end

    subgraph "Processing Modules"
        PRE[Preflight Analyzer]
        WRITER[Production Writer]
        QC[QC System]
        RESCUE[AutoFix Engine]
    end

    subgraph "Data & Storage"
        MODELS[Data Models<br/>JobPackage, Article, QCReport]
        FILES[File Storage<br/>storage/output/]
        CACHE[LLM Cache<br/>Redis/File]
    end

    subgraph "External Integrations"
        LLM_CLAUDE[Claude API]
        LLM_GPT[GPT API]
        LLM_GEMINI[Gemini API]
        AHREFS[Ahrefs SERP API]
        WORDPRESS[WordPress API]
    end

    USER --> VALIDATE
    VALIDATE --> ORCH
    ORCH --> SM
    SM --> PRE
    SM --> WRITER
    SM --> QC
    SM --> RESCUE

    PRE --> MODELS
    WRITER --> MODELS
    QC --> MODELS
    RESCUE --> MODELS

    ORCH --> FILES
    WRITER --> CACHE

    PRE --> AHREFS
    WRITER --> LLM_CLAUDE
    WRITER --> LLM_GPT
    WRITER --> LLM_GEMINI
    QC --> WORDPRESS

    BATCH --> ORCH

    style ORCH fill:#ffeb3b
    style SM fill:#ff9800
    style MODELS fill:#4caf50
```

**Communication Patterns**:

1. **Orchestrator → Modules**: Function calls with job_package parameter
2. **Modules → Storage**: Write to `storage/output/{job_id}_*.json`
3. **Writer → LLM**: HTTP POST with retry logic (3 attempts, exponential backoff)
4. **Cache Layer**: Check cache before LLM call (31% hit rate → 42% cost savings)
5. **Batch → Orchestrator**: Chunked processing (25 jobs/chunk by default)

---

## Technology Stack

```mermaid
graph LR
    subgraph "Backend"
        PYTHON[Python 3.11+]
        PYDANTIC[Pydantic<br/>Data Validation]
        REQUESTS[Requests<br/>HTTP Client]
    end

    subgraph "Storage"
        JSON[JSON Files<br/>Current]
        POSTGRES[PostgreSQL<br/>Planned v1.8]
    end

    subgraph "Frontend"
        HTML[HTML5]
        CSS[CSS3]
        JS[Vanilla JS]
    end

    subgraph "External APIs"
        ANTHROPIC[Anthropic Claude]
        OPENAI[OpenAI GPT]
        GOOGLE[Google Gemini]
        AHREF[Ahrefs]
    end

    subgraph "Deployment"
        DOCKER[Docker<br/>Containerization]
        RAILWAY[Railway<br/>Hosting]
    end

    PYTHON --> PYDANTIC
    PYTHON --> REQUESTS
    PYTHON --> JSON
    PYTHON --> POSTGRES

    HTML --> JS

    REQUESTS --> ANTHROPIC
    REQUESTS --> OPENAI
    REQUESTS --> GOOGLE
    REQUESTS --> AHREF

    DOCKER --> RAILWAY

    style PYTHON fill:#3776ab,color:#fff
    style POSTGRES fill:#336791,color:#fff
    style ANTHROPIC fill:#191919,color:#fff
    style DOCKER fill:#2496ed,color:#fff
```

**Core Technologies**:

| Layer | Technology | Purpose | Status |
|-------|------------|---------|--------|
| **Language** | Python 3.11+ | Backend logic | ✅ Production |
| **Validation** | Pydantic v2 | Schema validation, type safety | ✅ Production |
| **HTTP** | Requests | API calls, retry logic | ✅ Production |
| **Storage (current)** | JSON files | Job data, articles, logs | ✅ Production |
| **Storage (planned)** | PostgreSQL + SQLAlchemy | Multi-user database | 🔄 v1.8 roadmap |
| **LLM** | Claude, GPT, Gemini | Content generation | ✅ Production |
| **SERP** | Ahrefs API | SERP research | ✅ Production |
| **Frontend** | HTML/CSS/JS | Web interface | ✅ Production |
| **Deployment** | Docker + Railway | Hosting | 🔄 v1.7 in progress |

---

## Deployment Architecture

**Current (v1.6 - Local/Development)**:

```mermaid
graph TB
    subgraph "Local Machine"
        CLI[CLI Interface]
        WEB[Web Server<br/>localhost:5000]
        ENGINE[BACOWR Engine]
        STORAGE[File Storage<br/>storage/output/]
    end

    subgraph "External Services"
        CLAUDE[Anthropic Claude API]
        AHREFS[Ahrefs SERP API]
    end

    CLI --> ENGINE
    WEB --> ENGINE
    ENGINE --> STORAGE
    ENGINE --> CLAUDE
    ENGINE --> AHREFS

    style ENGINE fill:#4caf50
```

**Planned (v1.8 - Hosted Multi-User)**:

```mermaid
graph TB
    subgraph "User Devices"
        BROWSER[Web Browser]
    end

    subgraph "Railway Cloud"
        LB[Load Balancer]

        subgraph "App Tier"
            APP1[BACOWR Instance 1]
            APP2[BACOWR Instance 2]
        end

        subgraph "Data Tier"
            POSTGRES[(PostgreSQL<br/>Managed DB)]
            REDIS[Redis Cache]
        end
    end

    subgraph "External Services"
        CLAUDE[Claude API]
        AHREFS[Ahrefs API]
        WORDPRESS[WordPress API]
    end

    BROWSER --> LB
    LB --> APP1
    LB --> APP2

    APP1 --> POSTGRES
    APP2 --> POSTGRES
    APP1 --> REDIS
    APP2 --> REDIS

    APP1 --> CLAUDE
    APP1 --> AHREFS
    APP1 --> WORDPRESS

    style LB fill:#2196f3
    style POSTGRES fill:#336791,color:#fff
    style REDIS fill:#dc382d,color:#fff
```

**Deployment Specifications (v1.8 Planned)**:

| Component | Specification | Cost |
|-----------|---------------|------|
| **Web App** | 2× Railway instances (512MB RAM, 0.5 vCPU) | $10/mo each |
| **Database** | PostgreSQL managed (Railway) - 1GB | $10/mo |
| **Cache** | Redis managed (Railway) - 100MB | $5/mo |
| **Total** | - | **$35/mo** (initial, scales with usage) |

**Scaling Strategy**:
- **Horizontal**: Add more app instances behind load balancer
- **Database**: Upgrade to larger PostgreSQL instance or read replicas
- **Cache**: Increase Redis size for better LLM cache hit rate
- **Batch Processing**: Separate worker instances for large batch jobs

---

## Performance Characteristics

**Latency (Single Job)**:

| Stage | Avg Time | 95th Percentile | Bottleneck |
|-------|----------|-----------------|------------|
| **Input Validation** | 50ms | 100ms | - |
| **Preflight (Light)** | 2s | 5s | SERP API |
| **Preflight (Heavy)** | 45s | 90s | SERP API |
| **Write (Cached)** | 3s | 5s | Cache lookup |
| **Write (Uncached)** | 30s | 60s | LLM API |
| **QC** | 8s | 15s | Multiple checks |
| **RESCUE** | 30s | 60s | LLM API |
| **Total (typical)** | 45s | 120s | - |

**Throughput (Batch)**:

| Batch Size | Parallel Jobs | Total Time | Jobs/Hour |
|------------|---------------|------------|-----------|
| 25 | 5 | 4 min | 375 |
| 100 | 10 | 15 min | 400 |
| 175 | 10 | 26 min | 404 |

**Cost (Per Article)**:

| Item | Cost | Notes |
|------|------|-------|
| **LLM (uncached)** | $0.08-0.15 | Claude/GPT/Gemini |
| **LLM (cached)** | $0.001 | 31% hit rate |
| **SERP API** | $0.02-0.05 | Ahrefs credits |
| **Compute** | $0.001 | Railway hosting |
| **Total (avg)** | **$0.06-0.12** | 42% savings with caching |

---

## Security Architecture

**Authentication & Authorization** (v1.8):

```mermaid
graph LR
    USER[User]
    AUTH[Auth Middleware]
    JWT[JWT Tokens]
    DB[(User DB)]
    API[API Endpoints]

    USER -->|Login| AUTH
    AUTH -->|Verify| DB
    DB -->|Issue| JWT
    JWT -->|Authorize| API

    style AUTH fill:#f44336,color:#fff
    style JWT fill:#4caf50,color:#fff
```

**Security Layers**:

1. **API Authentication**: JWT tokens with 24h expiration
2. **API Keys**: Stored in environment variables (never in code)
3. **Rate Limiting**: 100 requests/hour per user (prevents abuse)
4. **Input Validation**: Pydantic schemas reject malformed data
5. **SQL Injection**: SQLAlchemy ORM (parameterized queries)
6. **XSS Prevention**: HTML escaping in frontend
7. **HTTPS**: Enforced in production (Railway)
8. **Secrets Management**: `.env` files + Railway environment variables

---

## Monitoring & Observability (Planned v2.0)

**Metrics to Track**:

| Metric | Threshold | Alert |
|--------|-----------|-------|
| **Job Success Rate** | <90% | Email |
| **QC Block Rate** | >15% | Slack |
| **LLM API Latency** | >60s p95 | PagerDuty |
| **Cost per Article** | >$0.20 | Email |
| **Cache Hit Rate** | <25% | Slack |
| **Error Rate** | >5% | PagerDuty |

**Logging Strategy**:
- **Structured Logs**: JSON format (timestamp, level, job_id, event, data)
- **Log Aggregation**: Centralized (Datadog or Railway logs)
- **Retention**: 90 days for all logs, 1 year for errors

---

## Future Architecture Evolutions

**v2.0 Roadmap**:
- ✅ PostgreSQL database (replace file storage)
- ✅ User authentication & multi-tenancy
- ✅ LLM output caching (Redis)
- 🔄 Horizontal scaling (multiple app instances)
- 🔄 Background job queue (Celery + Redis)

**v3.0 Vision** (SEO Campaign Manager):
- 🔮 Campaign tracking dashboard
- 🔮 Ranking monitoring integration (Ahrefs API)
- 🔮 Link graph visualization (D3.js)
- 🔮 Team permissions & role-based access
- 🔮 White-label option for agencies

---

## Architecture Decision Records (ADRs)

Key architectural decisions are documented in `/docs/templates/decision_log.md`:

- **D001**: PostgreSQL for production database
- **D002**: Claude as primary LLM (with multi-provider fallback)
- **D004**: RESCUE state (1 retry, not infinite)
- **D005**: Batch chunking (25 jobs/chunk default)

Refer to decision log for full rationale, alternatives considered, and consequences.

---

## How to Use This Document

**For New Developers**:
1. Start with [High-Level Architecture](#high-level-architecture)
2. Understand [Data Flow](#data-flow-diagram)
3. Study [State Machine](#state-machine)
4. Read decision log for "why" behind choices

**For LLMs in New Sessions**:
1. Scan diagrams to understand system structure (5 min)
2. Reference [Module Dependency Graph](#module-dependency-graph) before modifying code
3. Check [Technology Stack](#technology-stack) for available tools
4. Use [Component Interaction Map](#component-interaction-map) to trace data paths

**For Architects**:
1. Review [Deployment Architecture](#deployment-architecture)
2. Assess [Performance Characteristics](#performance-characteristics)
3. Evaluate [Security Architecture](#security-architecture)
4. Plan using [Future Architecture Evolutions](#future-architecture-evolutions)

---

**Document Maintained By**: Module Q (Vision, Gaps & Quality)
**Last Review**: 2025-11-19
**Next Review**: After v1.8 deployment

*"Architecture is the stuff you can't Google."* — Martin Fowler

This document captures BACOWR's architectural decisions and structure. Refer to `docs/bacowr_vision_and_quality.md` for quality standards and `docs/templates/decision_log.md` for decision rationale.
