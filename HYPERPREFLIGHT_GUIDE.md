# HyperPreflight Engine v2 - Complete Guide

## Overview

HyperPreflight är en förbättrad preflight engine för BACOWR som ger:

- **TrustLink T1-T5 hierarchy** - Automatisk source selection baserad på tier/topic/industry
- **SERP Topology med clustering** - Strukturerad SERP-analys med intent clusters
- **Compact Intent Paths** - Multi-step user journey mapping
- **Variable Marriage v2** - Enhanced relevansscoring med fidelity metrics
- **Token-Budget Aware Contracts** - Automatisk trimning för LLM context
- **Planned Claims with Evidence** - Kopplar påståenden till trust sources
- **Priority-Based Guardrails** - HARD_BLOCK → STRONG → SOFT enforcement

## Architecture

```
HyperPreflightEngine
    ├── TrustLinkEngine          # T1-T5 source management
    ├── SERP Topology Builder    # Cluster analysis
    ├── Intent Path Builder      # Multi-step journeys
    ├── Variable Marriage v2     # Fidelity scoring
    ├── Writer Plan Builder      # Section-level planning
    ├── Guardrails Engine        # Policy enforcement
    └── Preflight Decision       # AUTO_OK | NEEDS_HUMAN | AUTO_BLOCK
```

## Quick Start

### 1. Basic Usage (Deterministic)

```python
from src.preflight_v2.hyper_preflight_engine import HyperPreflightEngine
from src.preflight_v2.trustlink_engine import get_default_trustlink_engine

# Create engine
engine = HyperPreflightEngine(
    trustlink_engine=get_default_trustlink_engine()
)

# Build job
job = {
    'job_id': 'my-job-001',
    'vertical': 'finance',
    'anchor_text': 'bästa lånet',
    'anchor_url': 'https://bank.com/loan',
    'query': 'bästa lånet',
    'publisher_profile': {
        'domain': 'finans.se',
        'primary_topic': 'finans'
    },
    'target_profile': {
        'primary_topic': 'lån',
        'core_topics': ['lån', 'bank']
    }
}

# Run preflight
contract = engine.run(job)

# Check decision
print(f"Decision: {contract.decision.level.value}")
print(f"Trust sources: {len(contract.trust_plan.sources)}")
print(f"Sections: {len(contract.writer_plan.sections)}")
```

### 2. With APEX Orchestration

```python
from src.apex.bacowr_domain import run_apex_preflight
import asyncio

# Run with APEX
result = asyncio.run(run_apex_preflight(
    publisher_domain='finans.se',
    target_url='https://bank.com/loan',
    anchor_text='bästa lånet',
    vertical='finance'
))

if result.success:
    output = result.output
    print(f"Quality score: {result.score:.2f}")
    print(f"Decision: {output.handoff_contract.decision.level.value}")
```

### 3. Backward Compatible (Drop-in Replacement)

```python
from src.preflight_v2.adapter import PreflightV2Adapter

# Replaces old job_assembler.py
adapter = PreflightV2Adapter()

job_package, is_valid, error = adapter.assemble_job_package(
    publisher_domain='finans.se',
    target_url='https://bank.com/loan',
    anchor_text='bästa lånet',
    vertical='finance'
)

if is_valid:
    print("Job package ready for writer!")
else:
    print(f"Error: {error}")
```

## Trust Source Configuration

### Preconfigured Sources (YAML)

Trust sources finns i `src/preflight_v2/config/trustlink_sources.yaml`:

```yaml
scb.se:
  tier: DATA_PORTAL
  title: "Statistiska centralbyrån"
  authority: 98
  topics:
    - statistik
    - ekonomi
    - befolkning
  industries:
    - statistics
    - economics

regeringen.se:
  tier: T1_GOVERNMENT
  title: "Regeringen"
  authority: 99
  topics:
    - politik
    - ekonomi
    - juridik
```

### Adding Custom Sources

```python
from src.preflight_v2.trustlink_engine import create_trustlink_engine, TrustSource, SourceTier

# Define custom source
custom_sources = {
    'mycompany.com': {
        'tier': 'T5_BRAND',
        'title': 'My Company',
        'authority': 60,
        'topics': ['tech', 'innovation'],
        'industries': ['technology']
    }
}

# Create engine with custom sources
engine = create_trustlink_engine(custom_sources=custom_sources)
```

## Guardrails System

Guardrails definieras i `src/preflight_v2/config/guardrails_policies.yaml`:

### Priority Levels

1. **HARD_BLOCK** - Måste uppfyllas, blockerar leverans
2. **STRONG** - Bör uppfyllas, triggar human review
3. **SOFT** - Önskvärt, loggar varning

### Vertical-Specific Rules

**Finance**:
- ✅ Required disclaimer
- ✅ Min 1 T1/T2 trust source
- ✅ No unbacked financial claims

**Health**:
- ✅ Medical disclaimer
- ✅ Min 1 T1/T2 source (myndighet/forskning)
- ✅ Zero tolerance för pseudovetenskap

**Gambling**:
- ✅ Responsible gaming disclaimer + Stödlinjen
- ✅ Max 15% commercial density (stricter than default)
- ✅ No win promises

## Variable Marriage v2

Enhanced relevance scoring med två fidelity metrics:

### Anchor Fidelity

Hur väl anchor text matchar target:

- **1.0** - Exact match
- **0.8** - Partial match
- **0.5** - Branded/LSI
- **0.2** - Generic/Unknown

### Context Fidelity

Hur väl publisher-anchor-target-SERP alignment:

- **1.0** - Perfect alignment
- **0.8** - Minor fix needed
- **0.6** - Needs pivot
- **0.4** - Needs wrapper

### Marriage Status

Baserat på fidelity scores:

```python
if anchor_fidelity >= 0.8 and context_fidelity >= 0.8:
    status = MarriageStatus.PERFECT
    bridge = BridgeType.DIRECT
elif anchor_fidelity >= 0.6 and context_fidelity >= 0.7:
    status = MarriageStatus.MINOR_FIX
    bridge = BridgeType.CONTEXTUAL
elif anchor_fidelity >= 0.4 and context_fidelity >= 0.6:
    status = MarriageStatus.NEEDS_PIVOT
    bridge = BridgeType.COMPARISON
else:
    status = MarriageStatus.NEEDS_WRAPPER
    bridge = BridgeType.WRAPPER
```

## Writer Plan

HyperPreflight genererar en komplett writer plan:

### Section Structure

```python
# För COMPARISON article
sections = [
    ("intro", "Introduktion & läsarens problem"),
    ("criteria", "Så väljer du rätt"),
    ("compare", "Jämförelse mellan alternativ"),
    ("target_fit", "När passar target vs alternativ"),
    ("summary", "Sammanfattning & nästa steg")
]

# För EDUCATIONAL article
sections = [
    ("intro", "Vad är X?"),
    ("basics", "Grunderna och nyckelbegreppen"),
    ("deep_dive", "Fördjupning & vanliga frågor"),
    ("application", "Hur du använder kunskapen i praktiken"),
    ("summary", "Sammanfattning")
]
```

### LSI Injection

Varje sektion får:
- **Global LSI terms** (från target profile)
- **Section-specific LSI** (baserat på intent step)
- **Trustlink candidates** (för evidens)

## Token Budget Management

HyperHandoffContract trimmar automatiskt för att hålla inom budget:

```python
token_budget = TokenBudget(
    total_preflight=1500,
    intent=300,
    planned_claims=250,
    guardrails=150,
    writer_plan=350
)
```

### Automatic Trimming

1. Trim planned_claims till max 7 (prioritera required)
2. Trim sections.optional_points till max 4
3. Trim guardrails till 8 hårdaste
4. Trim SERP clusters till 3
5. Trim intent_path till 3 steg

## Decision Logic

Preflight fattar beslut baserat på:

### AUTO_OK

- Anchor fidelity ≥ 0.7
- Context fidelity ≥ 0.7
- Trust plan mode = "full"
- Risk level = LOW

### NEEDS_HUMAN

- Moderate fidelity (0.4-0.7)
- Regulated vertical med medium risk
- Degraded fallback + minimal trust
- Standard catch-all

### AUTO_BLOCK

- Extremely low fidelity (< 0.25) med risky anchor
- Regulated vertical MED zero trust sources
- Hard block guardrail violations

## ChatGPT/Claude Integration

### ChatGPT Function

```python
from src.integrations.chatgpt_interface import chatgpt_function_handler

result = await chatgpt_function_handler(
    publisher_domain='test.com',
    target_url='https://target.com',
    anchor_text='test anchor'
)

# Returns compact summary for ChatGPT
{
    'success': True,
    'decision': 'AUTO_OK',
    'summary': {
        'bridge_type': 'DIRECT',
        'trust_sources': 3,
        'quality_score': 0.85
    }
}
```

### Claude Tool

```python
from src.integrations.claude_interface import claude_tool_handler

result = await claude_tool_handler(
    publisher_domain='test.com',
    target_url='https://target.com',
    anchor_text='test anchor'
)

# Returns comprehensive analysis for Claude
{
    'success': True,
    'variable_marriage': {...},
    'trust_plan': {...},
    'writer_plan': {...},
    'guardrails': {...}
}
```

## Testing

```bash
# Run full test suite
python tests/test_hyperpreflight_apex.py

# Run specific test
pytest tests/test_hyperpreflight_apex.py::test_hyperpreflight_basic -v

# Manual testing
python -c "from tests.test_hyperpreflight_apex import *; test_hyperpreflight_basic()"
```

## Performance

**Deterministic Mode** (no LLM):
- Execution time: < 2s
- Token cost: $0.00
- Reliability: 100%

**APEX Mode** (with LLM enhancement):
- Execution time: 5-15s (3 iterations avg)
- Token cost: ~$0.05-0.15
- Quality improvement: +10-20% avg

## Migration from V1

### Before (job_assembler.py)

```python
from src.pipeline.job_assembler import BacklinkJobAssembler

assembler = BacklinkJobAssembler()
job_package, is_valid, error = assembler.assemble_job_package(...)
```

### After (PreflightV2Adapter)

```python
from src.preflight_v2.adapter import PreflightV2Adapter

adapter = PreflightV2Adapter()
job_package, is_valid, error = adapter.assemble_job_package(...)
```

**Zero code changes needed!**

## Troubleshooting

### No Trust Sources Found

**Problem**: `trust_plan.mode == "none"`

**Solution**:
1. Check topics match in `trustlink_sources.yaml`
2. Add custom sources for vertical
3. Adjust language filter (sv/en)

### Guardrails Blocking

**Problem**: Hard block guardrail triggered

**Solution**:
1. Check `guardrails_policies.yaml` for rules
2. Add required disclaimer for vertical
3. Ensure T1/T2 sources available
4. Review forbidden angles

### Low Marriage Scores

**Problem**: Anchor/context fidelity < 0.5

**Solution**:
1. Adjust anchor text för better relevance
2. Choose different target page
3. Accept WRAPPER/PIVOT strategy

---

**Version**: 2.0.0
**Created**: 2025-12-03
**Status**: Production Ready
