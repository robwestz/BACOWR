"""
BACOWR Domain Specialization for APEX Framework

Provides:
- BACOWROutput schema for APEX
- Domain-specific quality function
- Next-A1 compliance critics
- Hybrid generators (deterministic + LLM)
- BACOWR-specific APEX executor factory
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .apex_framework import (
    APEXConfig,
    APEXExecutor,
    Critic,
    Critique,
    Generator,
    Context,
    create_apex_instance
)

from ..preflight_v2.hyper_preflight_engine import (
    HyperPreflightEngine,
    HyperHandoffContract,
    DecisionLevel,
    MarriageStatus,
    GuardrailPriority
)
from ..preflight_v2.trustlink_engine import get_default_trustlink_engine
from ..utils.validation import get_validator


# ============================================================================
# OUTPUT SCHEMA
# ============================================================================


class BACOWROutput(BaseModel):
    """APEX output schema for BACOWR preflight."""
    handoff_contract: Any = Field(..., description="HyperHandoffContract instance")
    job_package: Dict[str, Any] = Field(..., description="BacklinkJobPackage dict")
    validation_status: str = Field(..., description="Schema validation status")
    quality_score: float = Field(0.0, description="Computed quality score")


# ============================================================================
# QUALITY FUNCTION
# ============================================================================


def bacowr_quality_function(
    output: BACOWROutput,
    context: Context
) -> float:
    """
    Domain-specific quality function for BACOWR preflight.

    Criteria (weighted):
    - Decision level (30%): AUTO_OK=1.0, NEEDS_HUMAN=0.5, AUTO_BLOCK=0.0
    - Trust completeness (20%): full=1.0, minimal=0.5, none=0.0
    - Variable marriage (30%): PERFECT=1.0, MINOR_FIX=0.8, NEEDS_PIVOT=0.6, NEEDS_WRAPPER=0.4
    - Schema validation (20%): valid=1.0, invalid=0.0

    Returns:
        Quality score 0.0-1.0
    """
    weights = {
        'decision': 0.3,
        'trust': 0.2,
        'marriage': 0.3,
        'schema': 0.2
    }

    contract = output.handoff_contract

    # Decision score
    decision_map = {
        DecisionLevel.AUTO_OK: 1.0,
        DecisionLevel.NEEDS_HUMAN: 0.5,
        DecisionLevel.AUTO_BLOCK: 0.0
    }
    decision_score = decision_map.get(contract.decision.level, 0.0)

    # Trust score
    trust_map = {'full': 1.0, 'minimal': 0.5, 'none': 0.0}
    trust_score = trust_map.get(contract.trust_plan.mode, 0.0)

    # Marriage score
    marriage_map = {
        MarriageStatus.PERFECT: 1.0,
        MarriageStatus.MINOR_FIX: 0.8,
        MarriageStatus.NEEDS_PIVOT: 0.6,
        MarriageStatus.NEEDS_WRAPPER: 0.4
    }
    marriage_score = marriage_map.get(contract.variable_marriage.status, 0.0)

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


# ============================================================================
# CRITICS
# ============================================================================


class BACOWRTrustCritic(Critic[BACOWROutput]):
    """Critic för trust source validation."""

    dimension = "trust"

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
        elif contract.trust_plan.mode == "minimal":
            critiques.append(Critique(
                dimension="trust",
                issue="Minimal trust sources (< min_required)",
                severity=0.5,
                suggestion="Expand trustlink pool for vertical/topic"
            ))

        return critiques


class BACOWRIntentCritic(Critic[BACOWROutput]):
    """Critic för intent alignment."""

    dimension = "intent"

    async def evaluate(
        self,
        output: BACOWROutput,
        context: Context
    ) -> List[Critique]:
        critiques = []
        contract = output.handoff_contract

        # Check marriage status
        if contract.variable_marriage.status == MarriageStatus.NEEDS_WRAPPER:
            critiques.append(Critique(
                dimension="intent",
                issue="Low alignment requires wrapper strategy",
                severity=0.4,
                suggestion="Consider adjusting target or anchor for better fit"
            ))

        # Check anchor fidelity
        if contract.variable_marriage.anchor_fidelity < 0.5:
            critiques.append(Critique(
                dimension="intent",
                issue=f"Low anchor fidelity: {contract.variable_marriage.anchor_fidelity:.2f}",
                severity=0.6,
                suggestion="Review anchor text relevance"
            ))

        return critiques


class BACOWRGuardrailCritic(Critic[BACOWROutput]):
    """Critic för guardrail compliance."""

    dimension = "guardrails"

    async def evaluate(
        self,
        output: BACOWROutput,
        context: Context
    ) -> List[Critique]:
        critiques = []
        contract = output.handoff_contract

        # Check for hard block guardrails
        hard_blocks = [
            g for g in contract.guardrails
            if g.priority == GuardrailPriority.HARD_BLOCK
        ]
        if hard_blocks:
            critiques.append(Critique(
                dimension="guardrails",
                issue=f"{len(hard_blocks)} hard block guardrails active",
                severity=0.8,
                suggestion="Review vertical-specific requirements and compliance"
            ))

        return critiques


# ============================================================================
# GENERATOR
# ============================================================================


class BACOWRGenerator(Generator[BACOWROutput]):
    """Hybrid deterministic + LLM generator for BACOWR preflight."""

    def __init__(self):
        # Create HyperPreflight engine with default trustlink
        trustlink_engine = get_default_trustlink_engine()
        self.hyper_engine = HyperPreflightEngine(
            trustlink_engine=trustlink_engine,
            logger=None
        )
        self.validator = get_validator()

    async def generate(
        self,
        task: str,
        context: Context,
        constraints: Optional[Dict[str, Any]] = None
    ) -> BACOWROutput:
        """Generate BACOWR preflight output."""

        # Extract job parameters from context
        job = {
            'job_id': context.get('job_id', 'apex-job'),
            'vertical': context.get('vertical', 'general'),
            'anchor_text': context.get('anchor_text', ''),
            'anchor_url': context.get('target_url', ''),
            'query': context.get('query', context.get('anchor_text', '')),
            'publisher_profile': context.get('publisher_profile', {'domain': context.get('publisher_domain', '')}),
            'target_profile': context.get('target_profile', {'primary_topic': context.get('query', '')})
        }

        # Run HyperPreflight (deterministic)
        contract = self.hyper_engine.run(job)

        # Convert to job package format
        job_package = self._convert_to_backlink_package(contract)

        # Validate schema
        is_valid, error = self.validator.validate_job_package(job_package)
        validation_status = "valid" if is_valid else f"invalid: {error}"

        # Create output
        output = BACOWROutput(
            handoff_contract=contract,
            job_package=job_package,
            validation_status=validation_status,
            quality_score=0.0  # Will be set by quality function
        )

        return output

    def _convert_to_backlink_package(self, contract: HyperHandoffContract) -> Dict[str, Any]:
        """Convert HyperHandoffContract to BacklinkJobPackage format."""
        from dataclasses import asdict

        # Build job package matching BACOWR schema
        job_package = {
            "job_meta": {
                "job_id": contract.job_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "spec_version": "Next-A1-SERP-First-v2",
                "notes": "Generated by HyperPreflight Engine v2"
            },
            "input_minimal": {
                "publisher_domain": contract.publisher_profile.get('domain', ''),
                "target_url": contract.anchor_url,
                "anchor_text": contract.anchor_text
            },
            "publisher_profile": contract.publisher_profile,
            "target_profile": contract.target_profile,
            "anchor_profile": {
                "proposed_text": contract.anchor_text,
                "classified_type": contract.anchor_type.value
            },
            "serp_research_extension": {
                "main_query": contract.serp_topology.query,
                "primary_intent": contract.serp_topology.primary_intent,
                "clusters": [
                    {
                        "id": c.id,
                        "label": c.label,
                        "primary_intent": c.primary_intent,
                        "subtopics": c.subtopics
                    }
                    for c in contract.serp_topology.clusters
                ]
            },
            "intent_extension": {
                "intent_path": [
                    {
                        "id": step.id,
                        "label": step.label,
                        "description": step.description,
                        "importance": step.importance
                    }
                    for step in contract.intent_path.primary_path
                ],
                "variable_marriage": {
                    "status": contract.variable_marriage.status.value,
                    "anchor_fidelity": contract.variable_marriage.anchor_fidelity,
                    "context_fidelity": contract.variable_marriage.context_fidelity,
                    "recommended_bridge": contract.variable_marriage.recommended_bridge_type.value,
                    "recommended_article": contract.variable_marriage.recommended_article_type.value
                },
                "forbidden_angles": contract.variable_marriage.forbidden_angles
            },
            "generation_constraints": {
                "language": "sv",
                "min_word_count": 900,
                "max_anchor_usages": 2,
                "anchor_policy": "Ingen anchor i H1/H2"
            },
            "trust_plan": {
                "mode": contract.trust_plan.mode,
                "sources": contract.trust_plan.to_contract_dict()
            },
            "writer_plan": {
                "article_type": contract.writer_plan.article_type.value,
                "thesis": contract.writer_plan.thesis,
                "angle": contract.writer_plan.angle,
                "sections": [
                    {
                        "section_id": sec.section_id,
                        "heading": sec.heading,
                        "required_points": sec.required_points,
                        "optional_points": sec.optional_points
                    }
                    for sec in contract.writer_plan.sections
                ]
            }
        }

        return job_package


# ============================================================================
# EXECUTOR FACTORY
# ============================================================================


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
        BACOWRTrustCritic(),
        BACOWRIntentCritic(),
        BACOWRGuardrailCritic()
    ]

    # Create generator factory
    def generator_factory() -> BACOWRGenerator:
        return BACOWRGenerator()

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


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================


async def run_apex_preflight(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    **kwargs
) -> Any:  # APEXResult[BACOWROutput]
    """
    Run APEX-orchestrated preflight for BACOWR.

    Args:
        publisher_domain: Publisher domain
        target_url: Target URL
        anchor_text: Anchor text
        **kwargs: Additional parameters (vertical, language, etc.)

    Returns:
        APEXResult with handoff contract and metrics
    """
    executor = create_bacowr_apex_executor()

    task = f"Generate backlink preflight for publisher={publisher_domain}, target={target_url}, anchor={anchor_text}"

    context = {
        'publisher_domain': publisher_domain,
        'target_url': target_url,
        'anchor_text': anchor_text,
        'vertical': kwargs.get('vertical', 'general'),
        'language': kwargs.get('language', 'sv'),
        'query': kwargs.get('query', anchor_text)
    }

    result = await executor.execute(task=task, context=context)

    return result


# Import datetime for timestamp
from datetime import datetime
