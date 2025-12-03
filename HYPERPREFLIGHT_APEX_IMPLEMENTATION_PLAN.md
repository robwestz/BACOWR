# HyperPreflight + APEX Framework Implementation Plan

## Executive Summary

Integration av en förbättrad preflight engine (`HyperPreflightEngine`) med APEX Framework orkestrering i BACOWR-projektet. Målet är att skapa en production-ready, LLM-driven preflight som kan köras via ChatGPT eller Claude med full Next-A1 compliance.

## Nulägesanalys

### Befintlig Arkitektur

**Current Preflight (job_assembler.py)**:
```
1. Profile Target → TargetProfile
2. Profile Publisher → PublisherProfile
3. Classify Anchor → AnchorProfile
4. Select Queries → QuerySet
5. Fetch SERP → SerpResults
6. Analyze SERP → SerpResearchExtension
7. Model Intent → IntentExtension
8. Assemble Package → BacklinkJobPackage
9. Validate → Schema validation
```

**State Machine**:
```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                        ↓      ↓
                     ABORT  RESCUE (max 1)
```

### Gap Analysis

| Feature | Current | HyperPreflight | Impact |
|---------|---------|----------------|--------|
| Trust Source Selection | Basic | T1-T5 hierarchy + matching | HIGH |
| Intent Path Planning | Simple | Multi-step compact path | HIGH |
| Variable Marriage | Basic overlap | Fidelity scores + bridge logic | HIGH |
| Token Budget Management | None | Built-in trimming | MEDIUM |
| SERP Topology | Linear | Clustered with subtopics | HIGH |
| Planned Claims | None | Evidence-backed claims | HIGH |
| Writer Plan | Basic | Section-level with LSI | HIGH |
| Guardrails | Config-based | Priority-based with blocking | MEDIUM |

---

## Implementation Strategy

### Phase 1: Core Integration (Vecka 1)

#### 1.1 Module Structure

```
src/
├── preflight_v2/
│   ├── __init__.py
│   ├── hyper_preflight_engine.py      # Core engine
│   ├── trustlink_engine.py             # T1-T5 source management
│   ├── serp_topology_builder.py        # Cluster analysis
│   ├── intent_path_builder.py          # Multi-step intent
│   ├── variable_marriage_v2.py         # Enhanced alignment
│   ├── writer_plan_builder.py          # Section planning
│   ├── guardrails_engine.py            # Policy enforcement
│   └── config/
│       ├── trustlink_sources.yaml      # Preconfigured sources
│       └── guardrails_policies.yaml    # Guardrail rules
│
├── apex/
│   ├── __init__.py
│   ├── apex_framework.py               # Core APEX implementation
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── direct.py                   # Direct pattern
│   │   ├── adversarial_refinement.py   # Iterative improvement
│   │   └── capability_cascade.py       # Probe → escalate
│   ├── critics/
│   │   ├── __init__.py
│   │   ├── schema_critic.py            # JSON schema validation
│   │   ├── next_a1_critic.py           # Next-A1 compliance
│   │   └── trust_critic.py             # Trust source validation
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── llm_generator.py            # Multi-LLM generator
│   │   └── hybrid_generator.py         # Deterministic + LLM
│   └── routers/
│       ├── __init__.py
│       └── complexity_router.py        # Route by complexity
│
└── integrations/
    ├── __init__.py
    ├── chatgpt_interface.py            # ChatGPT API adapter
    └── claude_interface.py             # Claude API adapter
```

#### 1.2 Integration Points

**Replace Current Preflight**:
```python
# Old: src/pipeline/job_assembler.py
# New: src/preflight_v2/hyper_preflight_engine.py

# Adapter pattern to maintain backward compatibility
class PreflightV2Adapter:
    """Adapts HyperPreflight to existing pipeline."""

    def __init__(self):
        self.hyper_engine = HyperPreflightEngine(
            trustlink_engine=TrustLinkEngine(),
            token_budget=TokenBudget(total_preflight=2000)
        )

    def assemble_job_package(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        **kwargs
    ) -> Tuple[Dict, bool, str]:
        """
        Backward-compatible wrapper for HyperPreflight.

        Returns:
            (job_package, is_valid, error_msg)
        """
        # Build job dict for HyperPreflight
        job = {
            'job_id': str(uuid.uuid4()),
            'vertical': kwargs.get('vertical', 'general'),
            'anchor_text': anchor_text,
            'anchor_url': target_url,
            'query': kwargs.get('query', ''),
            'publisher_profile': self._profile_publisher(publisher_domain),
            'target_profile': self._profile_target(target_url),
        }

        # Run HyperPreflight
        contract = self.hyper_engine.run(job)

        # Convert to BacklinkJobPackage format
        job_package = self._convert_to_backlink_package(contract)

        # Validate
        is_valid = contract.decision.level == DecisionLevel.AUTO_OK
        error_msg = None if is_valid else contract.decision.reason

        return job_package, is_valid, error_msg
```

### Phase 2: APEX Orchestration (Vecka 2)

#### 2.1 APEX Domain Specialization

```python
# src/apex/bacowr_domain.py

from pydantic import BaseModel
from typing import List

class BACOWROutput(BaseModel):
    """APEX output schema for BACOWR."""
    handoff_contract: HyperHandoffContract
    job_package: Dict[str, Any]
    validation_status: str
    quality_score: float


def bacowr_quality_function(
    output: BACOWROutput,
    context: Context
) -> float:
    """
    Domain-specific quality function.

    Criteria:
    - Decision level (AUTO_OK = 1.0, NEEDS_HUMAN = 0.5, AUTO_BLOCK = 0.0)
    - Trust plan completeness (mode: full=1.0, minimal=0.5, none=0.0)
    - Variable marriage status (PERFECT=1.0, MINOR_FIX=0.8, NEEDS_PIVOT=0.6, NEEDS_WRAPPER=0.4)
    - Schema validation (valid=1.0, invalid=0.0)
    """
    weights = {
        'decision': 0.3,
        'trust': 0.2,
        'marriage': 0.3,
        'schema': 0.2
    }

    # Decision score
    decision_map = {
        DecisionLevel.AUTO_OK: 1.0,
        DecisionLevel.NEEDS_HUMAN: 0.5,
        DecisionLevel.AUTO_BLOCK: 0.0
    }
    decision_score = decision_map[output.handoff_contract.decision.level]

    # Trust score
    trust_map = {'full': 1.0, 'minimal': 0.5, 'none': 0.0}
    trust_score = trust_map[output.handoff_contract.trust_plan.mode]

    # Marriage score
    marriage_map = {
        MarriageStatus.PERFECT: 1.0,
        MarriageStatus.MINOR_FIX: 0.8,
        MarriageStatus.NEEDS_PIVOT: 0.6,
        MarriageStatus.NEEDS_WRAPPER: 0.4
    }
    marriage_score = marriage_map[output.handoff_contract.variable_marriage.status]

    # Schema score
    schema_score = 1.0 if output.validation_status == "valid" else 0.0

    # Weighted sum
    total = (
        weights['decision'] * decision_score +
        weights['trust'] * trust_score +
        weights['marriage'] * marriage_score +
        weights['schema'] * schema_score
    )

    return total


class BACOWRCritic(Critic[BACOWROutput]):
    """Next-A1 compliance critic."""

    dimension = "next_a1_compliance"

    async def evaluate(
        self,
        output: BACOWROutput,
        context: Context
    ) -> List[Critique]:
        critiques = []

        contract = output.handoff_contract

        # Check trust sources
        if contract.trust_plan.mode == "none":
            critiques.append(Critique(
                dimension="trust",
                issue="No trust sources found",
                severity=0.9,
                suggestion="Add preconfigured sources for vertical"
            ))

        # Check intent alignment
        if contract.variable_marriage.status == MarriageStatus.NEEDS_WRAPPER:
            critiques.append(Critique(
                dimension="intent",
                issue="Low alignment requires wrapper strategy",
                severity=0.4,
                suggestion="Consider adjusting target or anchor"
            ))

        # Check guardrails
        hard_blocks = [
            g for g in contract.guardrails
            if g.priority == GuardrailPriority.HARD_BLOCK
        ]
        if hard_blocks:
            critiques.append(Critique(
                dimension="guardrails",
                issue=f"{len(hard_blocks)} hard block guardrails active",
                severity=0.8,
                suggestion="Review vertical-specific requirements"
            ))

        return critiques


class BACOWRGenerator(Generator[BACOWROutput]):
    """Hybrid deterministic + LLM generator."""

    def __init__(self, llm_enhancer: Optional[LLMEnhancer] = None):
        self.hyper_engine = HyperPreflightEngine(
            trustlink_engine=TrustLinkEngine(),
            token_budget=TokenBudget()
        )
        self.llm_enhancer = llm_enhancer

    async def generate(
        self,
        task: str,
        context: Context,
        constraints: Optional[Dict[str, Any]] = None
    ) -> BACOWROutput:
        """Generate BACOWR output."""

        # Extract job parameters from task/context
        job = self._parse_job_from_context(task, context)

        # Run HyperPreflight (deterministic)
        contract = self.hyper_engine.run(job)

        # Optional LLM enhancement
        if self.llm_enhancer and constraints.get('enhance_with_llm'):
            contract = await self.llm_enhancer.enhance_contract(contract)

        # Convert to job package
        job_package = self._convert_to_backlink_package(contract)

        # Validate schema
        validator = get_validator()
        is_valid, error = validator.validate_job_package(job_package)
        validation_status = "valid" if is_valid else f"invalid: {error}"

        # Calculate quality
        output = BACOWROutput(
            handoff_contract=contract,
            job_package=job_package,
            validation_status=validation_status,
            quality_score=0.0  # Will be set by quality function
        )

        return output
```

#### 2.2 APEX Execution

```python
# src/apex/bacowr_executor.py

def create_bacowr_apex_executor(
    config: Optional[APEXConfig] = None
) -> APEXExecutor[BACOWROutput]:
    """
    Factory for BACOWR-specific APEX executor.

    Returns:
        Configured APEXExecutor for BACOWR domain
    """
    config = config or APEXConfig(
        quality_threshold=0.8,
        max_iterations=3,
        parallel_generators=2
    )

    # Create critics
    critics = [
        BACOWRCritic(),
        SchemaCritic(),
        TrustCritic()
    ]

    # Create generator factory
    def generator_factory() -> BACOWRGenerator:
        return BACOWRGenerator(
            llm_enhancer=LLMEnhancer() if config.use_llm_enhancement else None
        )

    # Create APEX instance
    executor = create_apex_instance(
        domain="bacowr_preflight",
        output_schema=BACOWROutput,
        quality_fn=bacowr_quality_function,
        generator_factory=generator_factory,
        critics=critics,
        config=config
    )

    return executor


# Usage in pipeline
async def run_apex_preflight(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    **kwargs
) -> APEXResult[BACOWROutput]:
    """
    Run APEX-orchestrated preflight.

    Returns:
        APEXResult with handoff contract and metrics
    """
    executor = create_bacowr_apex_executor()

    task = f"Generate backlink job package for publisher={publisher_domain}, target={target_url}, anchor={anchor_text}"

    context = {
        'publisher_domain': publisher_domain,
        'target_url': target_url,
        'anchor_text': anchor_text,
        'vertical': kwargs.get('vertical', 'general'),
        'language': kwargs.get('language', 'sv')
    }

    result = await executor.execute(task=task, context=context)

    return result
```

### Phase 3: ChatGPT/Claude Interface (Vecka 3)

#### 3.1 Unified API Interface

```python
# src/integrations/llm_interface.py

from typing import Literal, Union
from pydantic import BaseModel

class PreflightRequest(BaseModel):
    """Standard request format for any LLM."""
    publisher_domain: str
    target_url: str
    anchor_text: str
    vertical: str = "general"
    language: str = "sv"
    use_apex: bool = True
    apex_config: Optional[Dict[str, Any]] = None


class PreflightResponse(BaseModel):
    """Standard response format."""
    success: bool
    job_id: str
    handoff_contract: Optional[HyperHandoffContract] = None
    job_package: Optional[Dict[str, Any]] = None
    decision: str
    quality_score: float
    metrics: Dict[str, Any]
    errors: List[str] = []


async def run_preflight_unified(
    request: PreflightRequest
) -> PreflightResponse:
    """
    Unified preflight entry point.

    Works with:
    - ChatGPT function calling
    - Claude tool use
    - Direct API calls
    """
    try:
        if request.use_apex:
            # Run with APEX orchestration
            result = await run_apex_preflight(
                publisher_domain=request.publisher_domain,
                target_url=request.target_url,
                anchor_text=request.anchor_text,
                vertical=request.vertical,
                language=request.language
            )

            if result.success:
                output = result.output
                return PreflightResponse(
                    success=True,
                    job_id=output.handoff_contract.job_id,
                    handoff_contract=output.handoff_contract,
                    job_package=output.job_package,
                    decision=output.handoff_contract.decision.level.value,
                    quality_score=result.score,
                    metrics={
                        'iterations': result.iterations,
                        'termination_reason': result.termination_reason.value,
                        'apex_metrics': asdict(result.metrics)
                    }
                )
            else:
                return PreflightResponse(
                    success=False,
                    job_id="",
                    decision="FAILED",
                    quality_score=0.0,
                    metrics={},
                    errors=[result.termination_reason.value]
                )

        else:
            # Run without APEX (legacy mode)
            adapter = PreflightV2Adapter()
            job_package, is_valid, error = adapter.assemble_job_package(
                publisher_domain=request.publisher_domain,
                target_url=request.target_url,
                anchor_text=request.anchor_text,
                vertical=request.vertical,
                language=request.language
            )

            return PreflightResponse(
                success=is_valid,
                job_id=job_package.get('job_meta', {}).get('job_id', ''),
                job_package=job_package,
                decision="AUTO_OK" if is_valid else "AUTO_BLOCK",
                quality_score=1.0 if is_valid else 0.0,
                metrics={'mode': 'legacy'},
                errors=[error] if error else []
            )

    except Exception as e:
        return PreflightResponse(
            success=False,
            job_id="",
            decision="ERROR",
            quality_score=0.0,
            metrics={},
            errors=[str(e)]
        )
```

#### 3.2 ChatGPT Function Definition

```python
# src/integrations/chatgpt_interface.py

CHATGPT_FUNCTION_DEFINITION = {
    "name": "bacowr_preflight",
    "description": "Generate a BACOWR preflight analysis with HyperPreflight + APEX orchestration. Returns a complete HandoffContract with trust plan, intent path, writer plan, and decision.",
    "parameters": {
        "type": "object",
        "properties": {
            "publisher_domain": {
                "type": "string",
                "description": "Domain where content will be published (e.g., 'aftonbladet.se')"
            },
            "target_url": {
                "type": "string",
                "description": "URL that will receive the backlink (e.g., 'https://client.com/product')"
            },
            "anchor_text": {
                "type": "string",
                "description": "Proposed anchor text (e.g., 'bästa valet för produkter')"
            },
            "vertical": {
                "type": "string",
                "description": "Industry vertical: general, finance, health, legal, gambling",
                "enum": ["general", "finance", "health", "legal", "gambling"],
                "default": "general"
            },
            "language": {
                "type": "string",
                "description": "Content language",
                "enum": ["sv", "en"],
                "default": "sv"
            },
            "use_apex": {
                "type": "boolean",
                "description": "Use APEX orchestration for quality improvement",
                "default": True
            }
        },
        "required": ["publisher_domain", "target_url", "anchor_text"]
    }
}


async def chatgpt_function_handler(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    vertical: str = "general",
    language: str = "sv",
    use_apex: bool = True
) -> Dict[str, Any]:
    """
    ChatGPT function call handler.

    Returns:
        Dict suitable for ChatGPT response
    """
    request = PreflightRequest(
        publisher_domain=publisher_domain,
        target_url=target_url,
        anchor_text=anchor_text,
        vertical=vertical,
        language=language,
        use_apex=use_apex
    )

    response = await run_preflight_unified(request)

    # Format for ChatGPT
    return {
        "success": response.success,
        "job_id": response.job_id,
        "decision": response.decision,
        "quality_score": response.quality_score,
        "summary": {
            "bridge_type": response.handoff_contract.variable_marriage.recommended_bridge_type.value if response.handoff_contract else None,
            "article_type": response.handoff_contract.variable_marriage.recommended_article_type.value if response.handoff_contract else None,
            "trust_sources": len(response.handoff_contract.trust_plan.sources) if response.handoff_contract else 0,
            "intent_steps": len(response.handoff_contract.intent_path.primary_path) if response.handoff_contract else 0
        },
        "metrics": response.metrics,
        "errors": response.errors
    }
```

#### 3.3 Claude Tool Definition

```python
# src/integrations/claude_interface.py

CLAUDE_TOOL_DEFINITION = {
    "name": "bacowr_preflight",
    "description": "Generate a complete BACOWR preflight analysis using HyperPreflight engine with APEX orchestration. Returns HandoffContract with SERP topology, intent path, variable marriage analysis, trust plan, planned claims, writer plan, and guardrails. Suitable for Next-A1 compliant backlink content generation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "publisher_domain": {
                "type": "string",
                "description": "Domain where content will be published (e.g., 'aftonbladet.se')"
            },
            "target_url": {
                "type": "string",
                "description": "URL that will receive the backlink"
            },
            "anchor_text": {
                "type": "string",
                "description": "Proposed anchor text for the backlink"
            },
            "vertical": {
                "type": "string",
                "description": "Industry vertical (affects guardrails and trust requirements)",
                "enum": ["general", "finance", "health", "legal", "gambling"]
            },
            "language": {
                "type": "string",
                "description": "Content language (affects trust source selection)",
                "enum": ["sv", "en"]
            },
            "use_apex": {
                "type": "boolean",
                "description": "Enable APEX orchestration for iterative quality improvement"
            }
        },
        "required": ["publisher_domain", "target_url", "anchor_text"]
    }
}


async def claude_tool_handler(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    vertical: str = "general",
    language: str = "sv",
    use_apex: bool = True
) -> Dict[str, Any]:
    """
    Claude tool use handler.

    Returns:
        Dict suitable for Claude response
    """
    request = PreflightRequest(
        publisher_domain=publisher_domain,
        target_url=target_url,
        anchor_text=anchor_text,
        vertical=vertical,
        language=language,
        use_apex=use_apex
    )

    response = await run_preflight_unified(request)

    if not response.success:
        return {
            "error": True,
            "message": f"Preflight failed: {', '.join(response.errors)}",
            "decision": response.decision
        }

    # Compact HandoffContract for Claude
    contract = response.handoff_contract

    return {
        "success": True,
        "job_id": response.job_id,
        "decision": {
            "level": response.decision,
            "reason": contract.decision.reason,
            "confidence": contract.decision.confidence
        },
        "variable_marriage": {
            "status": contract.variable_marriage.status.value,
            "anchor_fidelity": contract.variable_marriage.anchor_fidelity,
            "context_fidelity": contract.variable_marriage.context_fidelity,
            "recommended_bridge": contract.variable_marriage.recommended_bridge_type.value,
            "recommended_article": contract.variable_marriage.recommended_article_type.value,
            "implementation_notes": contract.variable_marriage.implementation_notes
        },
        "trust_plan": {
            "mode": contract.trust_plan.mode,
            "sources_count": len(contract.trust_plan.sources),
            "tier_mix": {k.value: v for k, v in contract.trust_plan.tier_mix.items()},
            "top_sources": [
                {"url": s.url, "title": s.title, "tier": s.source_type.value}
                for s in contract.trust_plan.sources[:3]
            ]
        },
        "intent_path": {
            "steps": [
                {
                    "id": step.id,
                    "label": step.label,
                    "importance": step.importance
                }
                for step in contract.intent_path.primary_path
            ]
        },
        "writer_plan": {
            "article_type": contract.writer_plan.article_type.value,
            "thesis": contract.writer_plan.thesis,
            "angle": contract.writer_plan.angle,
            "sections_count": len(contract.writer_plan.sections),
            "link_plan": contract.writer_plan.link_plan
        },
        "guardrails": {
            "total": len(contract.guardrails),
            "hard_blocks": len([g for g in contract.guardrails if g.priority == GuardrailPriority.HARD_BLOCK]),
            "rules": [
                {
                    "type": g.type.value,
                    "priority": g.priority.name,
                    "notes": g.notes
                }
                for g in contract.guardrails
            ]
        },
        "metrics": {
            "quality_score": response.quality_score,
            **response.metrics
        }
    }
```

---

## Phase 4: Testing & Documentation (Vecka 4)

### 4.1 Test Suite

```python
# tests/test_hyperpreflight_apex.py

import pytest
from src.preflight_v2.hyper_preflight_engine import HyperPreflightEngine
from src.apex.bacowr_executor import create_bacowr_apex_executor
from src.integrations.llm_interface import run_preflight_unified, PreflightRequest

@pytest.mark.asyncio
async def test_hyperpreflight_basic():
    """Test basic HyperPreflight execution."""
    engine = HyperPreflightEngine(
        trustlink_engine=TrustLinkEngine(),
        token_budget=TokenBudget()
    )

    job = {
        'job_id': 'test-001',
        'vertical': 'general',
        'anchor_text': 'test anchor',
        'anchor_url': 'https://target.com',
        'query': 'test query',
        'publisher_profile': {'domain': 'publisher.com'},
        'target_profile': {'primary_topic': 'test'}
    }

    contract = engine.run(job)

    assert contract.job_id == 'test-001'
    assert contract.decision.level in [DecisionLevel.AUTO_OK, DecisionLevel.NEEDS_HUMAN, DecisionLevel.AUTO_BLOCK]
    assert isinstance(contract.trust_plan.sources, list)
    assert isinstance(contract.writer_plan.sections, list)


@pytest.mark.asyncio
async def test_apex_orchestration():
    """Test APEX orchestration."""
    executor = create_bacowr_apex_executor()

    task = "Generate preflight for test job"
    context = {
        'publisher_domain': 'test.com',
        'target_url': 'https://target.com',
        'anchor_text': 'test anchor',
        'vertical': 'general'
    }

    result = await executor.execute(task=task, context=context)

    assert result is not None
    assert result.score >= 0.0
    assert result.iterations >= 1
    assert result.termination_reason in list(TerminationReason)


@pytest.mark.asyncio
async def test_unified_interface():
    """Test unified LLM interface."""
    request = PreflightRequest(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor'
    )

    response = await run_preflight_unified(request)

    assert isinstance(response.success, bool)
    assert response.job_id
    assert response.decision
    assert 0.0 <= response.quality_score <= 1.0


@pytest.mark.asyncio
async def test_chatgpt_function():
    """Test ChatGPT function handler."""
    from src.integrations.chatgpt_interface import chatgpt_function_handler

    result = await chatgpt_function_handler(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor'
    )

    assert 'success' in result
    assert 'job_id' in result
    assert 'summary' in result


@pytest.mark.asyncio
async def test_claude_tool():
    """Test Claude tool handler."""
    from src.integrations.claude_interface import claude_tool_handler

    result = await claude_tool_handler(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor'
    )

    assert 'success' in result or 'error' in result
    if result.get('success'):
        assert 'variable_marriage' in result
        assert 'trust_plan' in result
        assert 'writer_plan' in result
```

### 4.2 Documentation

**Files to Create/Update**:

1. `HYPERPREFLIGHT_GUIDE.md` - Complete guide to HyperPreflight
2. `APEX_INTEGRATION.md` - APEX framework usage in BACOWR
3. `LLM_INTERFACE_GUIDE.md` - ChatGPT/Claude integration guide
4. `TRUSTLINK_CONFIG.md` - Trust source configuration
5. Update `CLAUDE.md` with new preflight instructions
6. Update `README.md` with APEX/HyperPreflight features

---

## Deployment Strategy

### Migration Path

**Phase 1: Parallel Running (Vecka 5)**
- Keep existing preflight as fallback
- Add `--preflight-version` flag: `v1` | `v2` | `apex`
- Log both outputs for comparison
- Quality metrics comparison

**Phase 2: Soft Launch (Vecka 6)**
- Default to HyperPreflight v2
- APEX optional via flag
- Monitor production metrics
- Collect user feedback

**Phase 3: Full Migration (Vecka 7)**
- Deprecate v1 preflight
- APEX as default for complex jobs
- Remove legacy code
- Update all documentation

### Configuration

```yaml
# config/hyperpreflight.yaml

engine:
  token_budget:
    total_preflight: 2000
    intent: 300
    seo_opportunities: 250
    planned_claims: 250
    guardrails: 150
    writer_plan: 350
    misc_metadata: 200

trustlink:
  mode: full  # none | minimal | full
  min_required: 2
  max_total: 5
  prefer_tiers: [T1_GOVERNMENT, T2_ACADEMIC, DATA_PORTAL]

apex:
  enabled: true
  quality_threshold: 0.8
  max_iterations: 3
  parallel_generators: 2
  convergence_strategy: voting  # voting | synthesis | debate

guardrails:
  priority_enforcement: true
  auto_block_on_hard_violations: true
```

---

## Success Metrics

### Technical Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Schema Validation Rate | >95% | Automated tests |
| Quality Score | >0.8 | APEX quality function |
| AUTO_OK Decision Rate | >70% | Production logs |
| Trust Source Coverage | >80% | Job analysis |
| Token Budget Compliance | >90% | Contract trimming stats |

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Preflight Execution Time | <5s (deterministic), <15s (APEX) | Timing logs |
| API Response Time | <30s end-to-end | API metrics |
| APEX Convergence Rate | >85% within 3 iterations | APEX metrics |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Next-A1 Compliance | 100% | Automated validation |
| Trust Source Quality | >0.9 avg authority | Source scoring |
| Intent Alignment | >0.7 avg fidelity | Marriage scores |

---

## Risk Mitigation

### Risk 1: Breaking Changes
**Mitigation**: Adapter pattern maintains backward compatibility

### Risk 2: Performance Degradation
**Mitigation**: Parallel running, fallback to v1, caching

### Risk 3: LLM API Costs
**Mitigation**: Token budgets, deterministic fallback, caching

### Risk 4: Schema Evolution
**Mitigation**: Versioned schemas, migration scripts

### Risk 5: Complex Debugging
**Mitigation**: Comprehensive logging, execution traces, metrics

---

## Timeline Summary

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Core Integration | HyperPreflight + adapters |
| 2 | APEX Orchestration | APEX domain specialization |
| 3 | LLM Interfaces | ChatGPT + Claude handlers |
| 4 | Testing & Docs | Test suite + documentation |
| 5 | Parallel Running | Comparison metrics |
| 6 | Soft Launch | Production deployment |
| 7 | Full Migration | Legacy removal |

---

## Next Steps

1. **Review & Approve Plan** - Stakeholder sign-off
2. **Setup Development Environment** - Branch, dependencies
3. **Implement Phase 1** - Core integration
4. **Iterate Based on Feedback** - Adjust as needed

---

**Created**: 2025-12-03
**Author**: Claude Code
**Status**: Proposal - Awaiting Approval
