"""
Unified LLM Interface for BACOWR HyperPreflight

Provides standard request/response format for any LLM.
Works with ChatGPT, Claude, and direct API access.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from ..apex.bacowr_domain import run_apex_preflight
from ..preflight_v2.hyper_preflight_engine import HyperHandoffContract


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
    handoff_contract: Optional[Any] = None  # HyperHandoffContract
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
                        'apex_metrics': {
                            'wall_time_seconds': result.metrics.wall_time_seconds,
                            'pattern_selected': result.metrics.pattern_selected
                        }
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
            # Run without APEX (deterministic mode)
            from ..preflight_v2.hyper_preflight_engine import HyperPreflightEngine
            from ..preflight_v2.trustlink_engine import get_default_trustlink_engine

            engine = HyperPreflightEngine(
                trustlink_engine=get_default_trustlink_engine()
            )

            job = {
                'job_id': f'preflight-{request.publisher_domain[:20]}',
                'vertical': request.vertical,
                'anchor_text': request.anchor_text,
                'anchor_url': request.target_url,
                'query': request.anchor_text,
                'publisher_profile': {'domain': request.publisher_domain},
                'target_profile': {'primary_topic': request.anchor_text}
            }

            contract = engine.run(job)

            # Build job package
            from ..apex.bacowr_domain import BACOWRGenerator
            generator = BACOWRGenerator()
            job_package = generator._convert_to_backlink_package(contract)

            return PreflightResponse(
                success=True,
                job_id=contract.job_id,
                handoff_contract=contract,
                job_package=job_package,
                decision=contract.decision.level.value,
                quality_score=0.8,  # Estimated
                metrics={'mode': 'deterministic'},
                errors=[]
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
