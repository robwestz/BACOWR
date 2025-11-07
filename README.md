# BacklinkContent Engine - Next-A1 SERP-First Implementation

A **SERP-first, intent-first** backlink content engine that generates publication-ready backlink articles with full traceability, quality control, and strict adherence to the Next-A1 framework.

## Overview

This engine takes **three simple inputs**:
- **Publisher domain** (where content will be published)
- **Target URL** (the page receiving the backlink)
- **Anchor text** (the link text)

...and produces **publication-ready backlink content** with:
- Full SERP analysis and intent modeling
- Strategic bridge type recommendation (strong, pivot, wrapper)
- LSI-optimized content with proper anchor placement
- Trust source integration (T1-T4 hierarchy)
- Comprehensive QC validation
- Complete traceability and explainability

## Key Features

### Next-A1 Framework Implementation
- **Variabelgiftermål** (Variable Marriage): Aligns publisher, anchor, target, and search intent
- **SERP-First Approach**: Drives content strategy from dominant SERP intent
- **Bridge Types**: Intelligent strategy selection (strong, pivot, wrapper)
- **Trust Policy**: T1→T2→T3→T4 source prioritization
- **LSI Quality**: 6-10 relevant terms within ±2 sentence window
- **Autofix-Once**: Single automatic correction attempt with loop protection
- **Quality Control**: Comprehensive validation against Next-A1 requirements

### Modular & Extensible Architecture
All components designed for reusability in other SEO tools:
- **PageProfile**: Reusable web scraping and profiling
- **SERP Analysis**: Intent classification and pattern extraction
- **Intent Modeling**: Publisher-anchor-target-SERP alignment
- **QC System**: Configurable quality validation

### Production-Ready Features
- Deterministic state machine (RECEIVE → PREFLIGHT → WRITE → QC → DELIVER)
- JSON schema validation
- Structured logging with full execution trace
- Mock mode for testing without API costs
- Comprehensive error handling and recovery

## Installation

### Prerequisites
- Python 3.9+
- Anthropic API key (for Writer Engine)
- Optional: SERP API key (for real SERP data)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd BACOWR

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="your-api-key-here"
# Optional:
export SERP_API_KEY="your-serp-api-key"
```

### Configuration

Configuration files in `config/`:
- `thresholds.yaml`: QC thresholds (LSI, readability, trust requirements)
- `policies.yaml`: Autofix policies and industry compliance rules

Schemas in `schemas/`:
- `next-a1-spec.json`: Complete Next-A1 specification
- `backlink_job_package.schema.json`: BacklinkJobPackage JSON schema

## Usage

### Basic Usage

```bash
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product \
  --anchor "bästa valet för produktkategori"
```

### Advanced Options

```bash
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product \
  --anchor "best choice" \
  --anchor-type partial \
  --min-words 1200 \
  --language sv \
  --serp-mode mock \
  --output ./output/ \
  --log-level DEBUG
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `--publisher` | Publisher domain (required) | - |
| `--target` | Target URL (required) | - |
| `--anchor` | Anchor text (required) | - |
| `--anchor-type` | Anchor type hint: exact, partial, brand, generic | Auto-detect |
| `--min-words` | Minimum word count | 900 |
| `--language` | Language override (sv, en, etc.) | Auto-detect |
| `--output` | Output directory | ./storage/output |
| `--serp-mode` | SERP mode: mock or api | mock |
| `--serp-api-key` | SERP API key | $SERP_API_KEY |
| `--writer-api-key` | Anthropic API key | $ANTHROPIC_API_KEY |
| `--writer-model` | Claude model | claude-sonnet-4-5-20250929 |
| `--log-level` | Logging level | INFO |
| `--json-logs` | Output JSON-formatted logs | false |

## Output

The engine generates comprehensive output for each job:

```
storage/output/
└── <job-id>_article.md              # The generated article
└── <job-id>_job_package.json        # Complete job package
└── <job-id>_extensions.json         # Next-A1 extensions
└── <job-id>_qc_report.json          # QC validation results
└── <job-id>_execution_log.json      # State machine trace
```

### Output Files

**Article** (`*_article.md`):
- Publication-ready backlink content in Markdown
- Structured with H1-H3 headings
- Strategic anchor placement
- LSI-optimized near-window
- Trust source integration

**Job Package** (`*_job_package.json`):
- Complete input data and analysis
- Publisher, target, and anchor profiles
- SERP research extension
- Intent extension
- Generation constraints

**Extensions** (`*_extensions.json`):
- `links_extension`: Bridge type, anchor placement, LSI, trust, compliance
- `intent_extension`: Intent alignment, recommended bridge, required subtopics
- `qc_extension`: Anchor risk, readability, signals used
- `serp_research_extension`: SERP analysis data

**QC Report** (`*_qc_report.json`):
- Overall status: pass, warning, fail, needs_signoff
- Detailed issues with severity levels
- Autofix recommendations
- Human sign-off triggers

**Execution Log** (`*_execution_log.json`):
- Complete state machine trace
- Timestamps for each transition
- Success/failure indicators
- Debugging data

## Architecture

### Pipeline Flow

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
           ↓           ↓      ↓
         ABORT      ABORT  RESCUE (AutoFixOnce)
```

**States:**
1. **RECEIVE**: Accept input (publisher, target, anchor)
2. **PREFLIGHT**: Assemble BacklinkJobPackage
   - Profile target page
   - Profile publisher site
   - Classify anchor
   - Select SERP queries
   - Fetch and analyze SERP data
   - Model intent alignment
3. **WRITE**: Generate content with Writer Engine
4. **QC**: Validate against Next-A1 requirements
5. **RESCUE**: AutoFixOnce attempt (if fixable issues)
6. **DELIVER**: Output successful result
7. **ABORT**: Terminate on critical failure

### Core Components

**Analysis Pipeline** (`src/modules/`):
- `page_profile.py`: Reusable web scraping and profiling
- `target_profiler.py`: Target page analysis
- `publisher_profiler.py`: Publisher site analysis
- `anchor_classifier.py`: Anchor text classification
- `query_selector.py`: SERP query generation
- `serp_fetcher.py`: SERP data fetching (mock/real)
- `serp_analyzer.py`: SERP intent and pattern analysis
- `intent_modeler.py`: Intent alignment and bridge strategy

**Generation Pipeline** (`src/pipeline/`):
- `job_assembler.py`: BacklinkJobPackage assembly
- `writer_engine.py`: LLM-based content generation
- `state_machine.py`: Pipeline orchestration

**Quality Control** (`src/qc/`):
- `quality_controller.py`: QC validation and AutoFixOnce

**Utilities** (`src/utils/`):
- `logger.py`: Structured logging
- `validation.py`: JSON schema validation

## Next-A1 Framework

### Variabelgiftermål (Variable Marriage)

The core principle: Content must marry four dimensions:
1. **Publisher** (publication site role and voice)
2. **Anchor** (link text and implied intent)
3. **Target** (destination page offer)
4. **Intent** (dominant SERP search intent)

### Bridge Types

**Strong Bridge**:
- Direct, natural connection
- All dimensions aligned
- Publisher niche overlap ≥ 0.7
- Trust requirement: 1 source

**Pivot Bridge**:
- Thematic bridge strategy
- Partial alignment
- Publisher niche overlap 0.4-0.7
- Trust requirement: 1-2 sources

**Wrapper Bridge**:
- Meta-frame strategy
- Low alignment (overall=off acceptable)
- Build neutral frame (methodology, risk, comparison)
- Trust requirement: 2-3 sources for triangulation

### Trust Policy

Source prioritization (T1 → T2 → T3 → T4):
- **T1**: Government, official standards
- **T2**: Academic, peer-reviewed research
- **T3**: Industry organizations, whitepapers
- **T4**: Reputable media (fallback only)

Constraints:
- Never link to direct competitors
- Prefer Swedish sources for SE markets
- Use PLATSFÖRSLAG placeholder if source unknown

### LSI Requirements

- **Count**: 6-10 relevant terms
- **Window**: ±2 sentences around link
- **Quality**: Entity cluster diversity, not just synonyms
- **Sourcing**: From target entities + SERP subtopics

### Anchor Placement

- **Forbidden**: Never in H1 or H2
- **Preferred**: Middle section (H2 section 2-3)
- **Paragraph**: First or second paragraph in section
- **Context**: After establishing theme, before CTA

## Testing

### Run Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_pipeline_smoke.py -v
```

### Mock Mode

For testing without API costs, use `--serp-mode mock`:
- Generates realistic synthetic SERP data
- No Writer Engine calls (requires API key anyway)
- Full pipeline validation

## Extensibility

This engine is designed for reuse across multiple SEO tools:

### Reusable Components

**PageProfile Module**:
- Web scraping and content extraction
- Language detection and entity extraction
- Can power: content audits, competitive analysis, link analysis

**SERP Analysis**:
- Intent classification
- Pattern extraction
- Page archetype detection
- Can power: keyword research, content gap analysis, rank tracking

**Intent Modeling**:
- Publisher-target-anchor alignment
- Content strategy recommendation
- Can power: content planning, editorial calendars, topic clustering

**QC System**:
- Configurable quality validation
- Autofix logic framework
- Can power: content QA tools, style checkers

### Integration Points

**As a Library**:
```python
from src.pipeline.job_assembler import BacklinkJobAssembler
from src.pipeline.writer_engine import WriterEngine

# Assemble job package
assembler = BacklinkJobAssembler(serp_mode="api")
job_package, valid, error = assembler.assemble_job_package(
    publisher_domain="example.com",
    target_url="https://target.com",
    anchor_text="best solution"
)

# Generate content
writer = WriterEngine(api_key="...")
article, extensions, success, error = writer.generate_content(job_package)
```

**As a Service**:
- The state machine can be wrapped in a REST API
- Job packages can be queued for async processing
- Results can be stored in a database for analytics

## Roadmap

### Current Status: MVP/Beta
- ✅ Complete Next-A1 implementation
- ✅ Full pipeline (RECEIVE → DELIVER)
- ✅ QC validation
- ✅ Mock SERP support
- ✅ CLI interface
- ✅ Comprehensive documentation

### Next Steps
1. **Real SERP Integration**: Connect to SerpApi/Serper
2. **AutoFix Implementation**: Complete autofix logic for all issue types
3. **Enhanced LLM Prompts**: Refine writer prompts for better output
4. **Testing**: Expand test coverage
5. **Web UI**: Build frontend interface with Figma
6. **Analytics Dashboard**: Track job success rates, QC patterns
7. **Database Integration**: Store results for historical analysis
8. **MCP Integration**: Build MCP server for external tool integration

### Future Enhancements
- Advanced NER for better entity extraction
- ML-based intent classification
- Semantic clustering for topic modeling
- SERP feature extraction (PAA, featured snippets)
- Historical SERP tracking
- Multi-language optimization
- A/B testing framework for content variants

## Troubleshooting

### Common Issues

**Import Errors**:
```bash
# Make sure you're in the project root and venv is activated
source venv/bin/activate
pip install -r requirements.txt
```

**API Key Errors**:
```bash
# Set environment variable
export ANTHROPIC_API_KEY="your-key-here"

# Or pass as argument
python main.py --writer-api-key "your-key-here" ...
```

**SERP Fetch Failures**:
- Use `--serp-mode mock` for testing
- Check SERP API key if using `--serp-mode api`
- Review logs with `--log-level DEBUG`

**QC Failures**:
- Check `*_qc_report.json` for detailed issues
- Review recommendations for fixes
- Adjust thresholds in `config/thresholds.yaml` if needed

## Contributing

This is a standalone project designed for production use and extensibility.

Guidelines:
- Follow existing code style (Black formatting)
- Add tests for new features
- Update documentation
- Keep modules focused and reusable
- Maintain Next-A1 compliance

## License

[To be determined]

## Contact

For questions, issues, or collaboration:
- Open an issue on GitHub
- [Contact information]

---

**Built with Next-A1 Framework**
*SERP-First. Intent-First. Production-Ready.*
# BACOWR – BacklinkContent Engine (Next-A1)

**B**acklink **A**rticle **C**ontent **O**rchestration **W**ith **R**efinement

Ett ramverk för automatiserad, SERP-driven länkinnehållsproduktion baserat på Next-A1 specifikationen.

## 📋 Översikt

BACOWR är en produktionsklar motor för att skapa högkvalitativa backlink-artiklar som:

- ✅ **Analyserar SERP** för intent och toppresultat
- ✅ **Profilerar** målsida och publisher automatiskt
- ✅ **Genererar** backlink-innehåll som naturligt passar SERP-landskapet
- ✅ **Validerar** kvalitet med inbyggd QC (Quality Control)
- ✅ **Loggar** hela processen för spårbarhet

### Tre-input-paradigm

Motorn kräver endast tre inputs:

```json
{
  "publisher_domain": "example-publisher.com",
  "target_url": "https://client.com/product-x",
  "anchor_text": "bästa valet för [tema]"
}
```

Därifrån sker allt annat automatiskt.

## 🏗️ Arkitektur

### Komponenter

```
BACOWR/
├── backlink_job_package.schema.json    # JSON Schema (single source of truth)
├── BacklinkJobPackage.json             # Exempel-jobb
├── backlink_engine_ideal_flow.md       # Idealflöde dokumentation
├── next-a1-spec.json                   # Next-A1 specifikation
├── NEXT-A1-ENGINE-ADDENDUM.md          # Del 2 tillägg och krav
├── examples/
│   └── example_job_package.json        # Exempel på komplett job package
├── tests/
│   ├── test_schema_validation.py       # Schema-validering med jsonschema
│   └── test_live_validation.py         # Live E2E-validering
└── README.md                           # Denna fil
```

### Output (planerad produktion)

När motorn körs produceras:

1. **BacklinkJobPackage** (JSON) – Komplett kontext och instruktioner
2. **Backlink-artikel** (MD/HTML) – Typiskt ≥900 ord
3. **Next-A1 extensions** (JSON) – Intent, SERP-research, QC, LSI-data
4. **QC-rapport** (JSON) – Kvalitetsbedömning och AutoFix-historik
5. **Execution log** (JSON) – State machine-spårning

## 📦 Installation

### Krav

- Python 3.8+
- pip

### Setup

```bash
# Klona repot
git clone https://github.com/robwestz/BACOWR.git
cd BACOWR

# Installera beroenden
pip install -r requirements.txt
```

## 🧪 Tester

Projektet har två nivåer av validering enligt NEXT-A1-ENGINE-ADDENDUM.md:

### 1. Schema-validering (obligatorisk)

Validerar att exempel-JSON följer schemat:

```bash
python tests/test_schema_validation.py
```

**Vad testet gör:**
- Läser `backlink_job_package.schema.json`
- Läser `examples/example_job_package.json`
- Validerar med `jsonschema.validate()`
- Säkerställer att alla obligatoriska fält finns

**Förväntat resultat:**
```
[INFO] 🔍 Starting JSON Schema Validation
[SUCCESS] ✅ Schema loaded: BacklinkJobPackage
[SUCCESS] ✅ Example loaded: Job ID = example-job-001
[INFO] 🔬 Validating against schema...
[SUCCESS] ✅ VALIDATION PASSED!
[SUCCESS] ✅ TEST PASSED
```

### 2. Live validering (E2E light)

Validerar datakvalitet och konsistens:

```bash
python tests/test_live_validation.py
```

**Vad testet gör:**
- Läser schema och job package
- Validerar alla obligatoriska fält finns
- Kontrollerar språk-konsistens (sv/en/etc)
- Verifierar intent alignment
- Kontrollerar generation constraints (ordkrav, etc)

**Förväntat resultat:**
```
[INFO] 🚀 Startar BACOWR Live Test
[SUCCESS] ✅ Alla obligatoriska fält finns!
[CHECK] ✅ Språk konsistent: sv
[CHECK] ✅ Intent alignment: aligned
[CHECK] ✅ Ordkrav uppfyllt: 900 ord
[SUCCESS] 🎉 Alla tester godkända!
```

### Köra alla tester

```bash
# Från projektroten
python tests/test_schema_validation.py && python tests/test_live_validation.py
```

## 📖 Dokumentation

### Specifikationer

1. **[backlink_engine_ideal_flow.md](backlink_engine_ideal_flow.md)**
   - Detaljerat idealflöde från input till output
   - Beskriver alla profileringar och extensions

2. **[NEXT-A1-ENGINE-ADDENDUM.md](NEXT-A1-ENGINE-ADDENDUM.md)**
   - Formella krav för Del 2
   - QC & AutoFixOnce specifikation
   - State machine krav
   - Acceptance-kriterier

3. **[next-a1-spec.json](next-a1-spec.json)**
   - Komplett Next-A1 specifikation
   - Intent-klassificering
   - Bridge-typer
   - Länkplacering och ankarpolicies

### JSON Schema

**Single Source of Truth:** `backlink_job_package.schema.json`

Detta schema definierar det bindande kontraktet för BacklinkJobPackage.

**Obligatoriska toppnivå-fält:**

- `job_meta` – Metadata (job_id, created_at, spec_version)
- `input_minimal` – Tre inputs (publisher, target, anchor)
- `publisher_profile` – Profilerad publishersida
- `target_profile` – Profilerad målsida
- `anchor_profile` – Ankaranalys
- `serp_research_extension` – SERP-research (main + cluster queries)
- `intent_extension` – Intent-modellering och alignment
- `generation_constraints` – Generationspolicies (språk, ordkrav, etc)

## 🎯 Acceptance-kriterier

Motorn anses stabil när (per NEXT-A1-ENGINE-ADDENDUM.md § 7):

- [x] `test_schema_validation.py` passerar
- [x] `test_live_validation.py` passerar
- [ ] QC-system implementerat med AutoFixOnce
- [ ] State machine loggar till `execution_log`
- [ ] Minst 1–2 manuella produktionskörningar genomförda
- [ ] README beskriver hur man kör och tolkar output

### Nuvarande status

**✅ Specifikation:** Komplett
**🚧 Implementation:** Pågående
**✅ Tester:** Schema-validering klar

## 🔧 Användning (planerad)

### CLI

```bash
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product-x \
  --anchor "bästa valet för [tema]" \
  --output ./storage/output/
```

### Python API

```python
from bacowr import run_backlink_job

result = run_backlink_job(
    publisher_domain="example-publisher.com",
    target_url="https://client.com/product-x",
    anchor_text="bästa valet för [tema]"
)

# result innehåller:
# - job_package (dict)
# - article (str)
# - qc_report (dict)
```

## 🛡️ QC & AutoFixOnce (planerad)

Quality Control-systemet har två nivåer:

### 1. Automatisk korrigering (AutoFixOnce)

Vid **mindre avvikelser** görs exakt en automatisk fix:

- Flytta länk inom samma sektion
- Justera ankartyp (exact → brand/generic)
- Injicera saknade LSI
- Lägga till compliance-disclaimers

Alla ändringar loggas i `qc_extension`.

### 2. Manuell signoff

Vid **allvarliga avvikelser** blockeras automatisk fix:

- Intent alignment: "off"
- Trust-källor: 0 godkända
- Konkurrent-detektion i content
- Reglerad vertikal utan disclaimers
- Ankar-risk: "high"

Sätter `human_signoff_required: true` i output.

## 📊 State Machine (planerad)

Varje körning går genom:

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                                ↓
                              RESCUE (max 1 gång)
                                ↓
                              ABORT (vid loop/deadlock)
```

**Loop-skydd:** Om RESCUE inte ändrar payload → ABORT

**Spårbarhet:** Alla state-övergångar loggas i `execution_log.json`

## 🤝 Integration

Motorn är utformad för att vara **integrationsklar utan hårda beroenden**.

### Användningsfall

- **MCP-verktyg** (Model Context Protocol)
- **Batch-processer** för stora uppdrag
- **GUI/Dashboard** för manuell körning
- **CI/CD pipelines** för automatisk content-generering

Inga antaganden görs om externa orchestrators.

## 📝 Exempel

Se `examples/example_job_package.json` för ett komplett exempel på BacklinkJobPackage.

Exempel visar:
- Svensk publisher (consumer_magazine tone)
- Kommersiell målsida (Product X)
- Partial anchor med commercial_research intent
- Aligned intent mellan SERP, target och publisher
- Pivot bridge-type rekommenderad

## 🔬 Utveckling

### Lägg till nya tester

```bash
# Skapa ny testfil i tests/
touch tests/test_my_feature.py

# Kör alla tester
python -m pytest tests/
```

### Validera schema-ändringar

När du ändrar `backlink_job_package.schema.json`:

1. Uppdatera exempel i `examples/`
2. Kör `test_schema_validation.py`
3. Kör `test_live_validation.py`
4. Verifiera att båda passerar

## 📄 Licens

(Lägg till din licens här)

## 👥 Bidrag

(Lägg till bidragsinstruktioner här)

## 📞 Support

För frågor eller buggrapporter, öppna en issue i GitHub-repot.

---

**Version:** 1.0
**Status:** Specification Complete, Implementation In Progress
**Last Updated:** 2025-11-07
