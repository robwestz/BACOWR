"""
PreflightV2 Adapter - Backward Compatibility Layer

Adapts HyperPreflight to existing BACOWR pipeline interface.
Allows drop-in replacement of old job_assembler.py
"""

import uuid
from datetime import datetime
from typing import Dict, Tuple, Optional

from .hyper_preflight_engine import HyperPreflightEngine, TokenBudget
from .trustlink_engine import get_default_trustlink_engine
from ..utils.validation import get_validator
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PreflightV2Adapter:
    """
    Adapts HyperPreflight to existing BacklinkJobAssembler interface.

    Provides drop-in compatibility with:
    - src/pipeline/job_assembler.py
    - Existing state machine
    - Existing QC system
    """

    def __init__(
        self,
        token_budget: Optional[TokenBudget] = None,
        enable_apex: bool = False
    ):
        """
        Initialize adapter.

        Args:
            token_budget: Optional custom token budget
            enable_apex: Whether to use APEX orchestration (default: False for compatibility)
        """
        self.hyper_engine = HyperPreflightEngine(
            trustlink_engine=get_default_trustlink_engine(),
            logger=logger,
            token_budget=token_budget
        )
        self.validator = get_validator()
        self.enable_apex = enable_apex

        logger.info("PreflightV2Adapter initialized", enable_apex=enable_apex)

    def assemble_job_package(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        anchor_type_hint: Optional[str] = None,
        min_word_count: int = 900,
        language: Optional[str] = None,
        vertical: str = "general"
    ) -> Tuple[Dict, bool, str]:
        """
        Assemble job package - Backward compatible signature.

        Args:
            publisher_domain: Domain where content will be published
            target_url: URL that will receive the backlink
            anchor_text: Proposed anchor text
            anchor_type_hint: Optional anchor type hint
            min_word_count: Minimum word count
            language: Optional language override
            vertical: Industry vertical

        Returns:
            Tuple of (job_package_dict, is_valid, error_message)
        """
        logger.info(
            "Assembling job package with PreflightV2",
            publisher=publisher_domain,
            target=target_url[:50],
            anchor=anchor_text[:30]
        )

        try:
            # Build job dict for HyperPreflight
            job = {
                'job_id': f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                'vertical': vertical,
                'anchor_text': anchor_text,
                'anchor_url': target_url,
                'query': anchor_text,  # Simplified - real implementation would derive query
                'publisher_profile': self._profile_publisher(publisher_domain),
                'target_profile': self._profile_target(target_url),
            }

            # Run HyperPreflight
            contract = self.hyper_engine.run(job)

            # Convert to BacklinkJobPackage format
            job_package = self._convert_to_backlink_package(
                contract,
                min_word_count,
                language
            )

            # Validate
            is_valid, error_msg = self.validator.validate_job_package(job_package)

            if not is_valid:
                logger.error("Job package validation failed", error=error_msg)
                return job_package, False, error_msg

            logger.info(
                "Job package assembled successfully",
                job_id=job_package["job_meta"]["job_id"],
                decision=contract.decision.level.value
            )

            return job_package, True, None

        except Exception as e:
            error_msg = f"Failed to assemble job package: {str(e)}"
            logger.error("Job assembly failed", error=error_msg, exc_info=True)
            return None, False, error_msg

    def _profile_publisher(self, domain: str) -> Dict:
        """Profile publisher (simplified - real implementation would use PageProfiler)."""
        return {
            "domain": domain,
            "primary_topic": "general",
            "tone_class": "consumer_magazine",
            "language": "sv"
        }

    def _profile_target(self, url: str) -> Dict:
        """Profile target (simplified - real implementation would use PageProfiler)."""
        return {
            "url": url,
            "primary_topic": "product",
            "language": "sv",
            "core_topics": ["general"]
        }

    def _convert_to_backlink_package(
        self,
        contract,
        min_word_count: int,
        language: Optional[str]
    ) -> Dict:
        """Convert HyperHandoffContract to BacklinkJobPackage format."""

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
                "classified_type": contract.anchor_type.value,
                "risk_level": contract.risk_profile.risk_level.value
            },
            "serp_research_extension": {
                "main_query": contract.serp_topology.query,
                "primary_intent": contract.serp_topology.primary_intent,
                "source": contract.serp_topology.source,
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
                "forbidden_angles": contract.variable_marriage.forbidden_angles,
                "implementation_notes": contract.variable_marriage.implementation_notes
            },
            "generation_constraints": {
                "language": language or "sv",
                "min_word_count": min_word_count,
                "max_anchor_usages": 2,
                "anchor_policy": "Ingen anchor i H1/H2, placera i mittsektionens första relevanta stycken"
            },
            "trust_plan_extension": {
                "mode": contract.trust_plan.mode,
                "min_required": contract.trust_plan.min_required,
                "sources": contract.trust_plan.to_contract_dict(),
                "tier_mix": {k.value: v for k, v in contract.trust_plan.tier_mix.items()}
            },
            "writer_plan_extension": {
                "article_type": contract.writer_plan.article_type.value,
                "thesis": contract.writer_plan.thesis,
                "angle": contract.writer_plan.angle,
                "sections": [
                    {
                        "section_id": sec.section_id,
                        "heading": sec.heading,
                        "purpose": sec.purpose,
                        "required_points": sec.required_points,
                        "optional_points": sec.optional_points,
                        "lsi_terms": sec.lsi_terms,
                        "trustlink_candidates": sec.trustlink_candidates
                    }
                    for sec in contract.writer_plan.sections
                ],
                "global_lsi_terms": contract.writer_plan.global_lsi_terms,
                "link_plan": contract.writer_plan.link_plan
            },
            "planned_claims_extension": [
                {
                    "claim_id": c.claim_id,
                    "section_id": c.section_id,
                    "claim_text": c.claim_text,
                    "evidence_urls": c.evidence_urls,
                    "required": c.required,
                    "confidence": c.confidence
                }
                for c in contract.planned_claims
            ],
            "guardrails_extension": [
                {
                    "id": g.id,
                    "type": g.type.value,
                    "priority": g.priority.name,
                    "threshold": g.threshold,
                    "notes": g.notes
                }
                for g in contract.guardrails
            ],
            "preflight_decision": {
                "level": contract.decision.level.value,
                "reason": contract.decision.reason,
                "confidence": contract.decision.confidence
            }
        }

        return job_package


# Convenience function for easy import
def get_preflight_v2_adapter(**kwargs) -> PreflightV2Adapter:
    """Get configured PreflightV2Adapter instance."""
    return PreflightV2Adapter(**kwargs)
