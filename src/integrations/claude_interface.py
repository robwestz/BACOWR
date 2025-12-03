"""
Claude Tool Use Interface for BACOWR HyperPreflight

Provides:
- Anthropic tool definition
- Tool use handler
- Comprehensive response formatting for Claude
"""

from typing import Any, Dict

from .llm_interface import PreflightRequest, run_preflight_unified


CLAUDE_TOOL_DEFINITION = {
    "name": "bacowr_preflight",
    "description": "Generate complete BACOWR preflight analysis using HyperPreflight engine with APEX orchestration. Returns HandoffContract with SERP topology, intent path, variable marriage analysis, trust plan, planned claims, writer plan, and guardrails. Suitable for Next-A1 compliant backlink content generation.",
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
            "anchor_fidelity": round(contract.variable_marriage.anchor_fidelity, 3),
            "context_fidelity": round(contract.variable_marriage.context_fidelity, 3),
            "recommended_bridge": contract.variable_marriage.recommended_bridge_type.value,
            "recommended_article": contract.variable_marriage.recommended_article_type.value,
            "implementation_notes": contract.variable_marriage.implementation_notes,
            "forbidden_angles": contract.variable_marriage.forbidden_angles
        },
        "trust_plan": {
            "mode": contract.trust_plan.mode,
            "sources_count": len(contract.trust_plan.sources),
            "tier_mix": {k.value: v for k, v in contract.trust_plan.tier_mix.items()},
            "top_sources": [
                {
                    "url": s.url,
                    "title": s.title,
                    "tier": s.source_type.value,
                    "authority": s.authority_score,
                    "topics": s.topics
                }
                for s in contract.trust_plan.sources[:3]
            ]
        },
        "intent_path": {
            "steps": [
                {
                    "id": step.id,
                    "label": step.label,
                    "description": step.description,
                    "importance": step.importance
                }
                for step in contract.intent_path.primary_path
            ]
        },
        "serp_topology": {
            "query": contract.serp_topology.query,
            "primary_intent": contract.serp_topology.primary_intent,
            "source": contract.serp_topology.source,
            "clusters": [
                {
                    "id": c.id,
                    "label": c.label,
                    "intent": c.primary_intent,
                    "subtopics": c.subtopics[:5]
                }
                for c in contract.serp_topology.clusters
            ]
        },
        "writer_plan": {
            "article_type": contract.writer_plan.article_type.value,
            "thesis": contract.writer_plan.thesis,
            "angle": contract.writer_plan.angle,
            "sections_count": len(contract.writer_plan.sections),
            "sections": [
                {
                    "section_id": sec.section_id,
                    "heading": sec.heading,
                    "required_points_count": len(sec.required_points),
                    "lsi_terms": sec.lsi_terms[:5]
                }
                for sec in contract.writer_plan.sections
            ],
            "link_plan": contract.writer_plan.link_plan
        },
        "risk_profile": {
            "level": contract.risk_profile.risk_level.value,
            "editorial_risks": contract.risk_profile.editorial_risks,
            "brand_risks": contract.risk_profile.brand_risks,
            "legal_risks": contract.risk_profile.legal_risks
        },
        "guardrails": {
            "total": len(contract.guardrails),
            "hard_blocks": len([g for g in contract.guardrails if g.priority.name == "HARD_BLOCK"]),
            "rules": [
                {
                    "type": g.type.value,
                    "priority": g.priority.name,
                    "notes": g.notes
                }
                for g in contract.guardrails
            ]
        },
        "planned_claims": {
            "total": len(contract.planned_claims),
            "required": len([c for c in contract.planned_claims if c.required]),
            "samples": [
                {
                    "claim_id": c.claim_id,
                    "text": c.claim_text[:100],
                    "evidence_count": len(c.evidence_urls),
                    "confidence": c.confidence
                }
                for c in contract.planned_claims[:3]
            ]
        },
        "metrics": {
            "quality_score": response.quality_score,
            **response.metrics
        }
    }
