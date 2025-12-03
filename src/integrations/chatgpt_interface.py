"""
ChatGPT Function Calling Interface for BACOWR HyperPreflight

Provides:
- OpenAI function definition
- Function call handler
- Response formatting for ChatGPT
"""

from typing import Any, Dict

from .llm_interface import PreflightRequest, run_preflight_unified


CHATGPT_FUNCTION_DEFINITION = {
    "name": "bacowr_preflight",
    "description": "Generate BACOWR preflight analysis with HyperPreflight + APEX. Returns HandoffContract with trust plan, intent path, writer plan, and decision for Next-A1 compliant backlink content.",
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
    if not response.success:
        return {
            "success": False,
            "error": ", ".join(response.errors),
            "decision": response.decision
        }

    contract = response.handoff_contract

    return {
        "success": True,
        "job_id": response.job_id,
        "decision": response.decision,
        "quality_score": response.quality_score,
        "summary": {
            "bridge_type": contract.variable_marriage.recommended_bridge_type.value,
            "article_type": contract.variable_marriage.recommended_article_type.value,
            "anchor_fidelity": round(contract.variable_marriage.anchor_fidelity, 2),
            "context_fidelity": round(contract.variable_marriage.context_fidelity, 2),
            "trust_sources": len(contract.trust_plan.sources),
            "trust_mode": contract.trust_plan.mode,
            "intent_steps": len(contract.intent_path.primary_path),
            "sections_planned": len(contract.writer_plan.sections),
            "guardrails_active": len(contract.guardrails)
        },
        "recommendations": contract.variable_marriage.implementation_notes,
        "risks": {
            "level": contract.risk_profile.risk_level.value,
            "editorial": contract.risk_profile.editorial_risks,
            "brand": contract.risk_profile.brand_risks
        },
        "metrics": response.metrics
    }
