
from typing import Dict, Any
from .models import LinksExtension, QCExtension, IntentExtension, IntentProfile, SERPResearch, PublisherProfile, TargetProfile, AnchorProfile

def estimate_anchor_risk(anchor_type: str, context_strength: str = "medium") -> str:
    # Heuristic: exact in weak context is high, exact in medium is medium, others are low/medium
    if anchor_type == "exact":
        return "high" if context_strength == "weak" else "medium"
    if anchor_type == "partial":
        return "medium"
    return "low"

def build_extensions(intent_profile: IntentProfile,
                     target_profile: TargetProfile,
                     publisher_profile: PublisherProfile,
                     anchor_profile: AnchorProfile,
                     serp_research: SERPResearch) -> Dict[str, Any]:
    links_ext = LinksExtension(
        bridge_type=intent_profile.recommended_bridge_type,
        bridge_theme="intent-aligned",
        anchor_policy_used="no H1/H2 anchors; natural placement mid-section",
        trust_policy_level="T2_academic"  # placeholder default
    )

    qc_ext = QCExtension(
        anchor_risk=estimate_anchor_risk(anchor_profile.llm_classified_type or (anchor_profile.type_hint or "generic")),
        thresholds_version="A1",
        notes_observability={
            "signals_used": ["target_entities","publisher_profile","SERP_intent","trust_source","blueprint"],
            "autofix_done": False
        },
    )

    intent_ext = IntentExtension(
        serp_intent_primary=intent_profile.serp_intent_primary,
        serp_intent_secondary=intent_profile.serp_intent_secondary,
        target_page_intent=intent_profile.target_page_intent,
        anchor_implied_intent=intent_profile.anchor_implied_intent,
        publisher_role_intent=intent_profile.publisher_role_intent,
        intent_alignment=intent_profile.alignment,
        recommended_bridge_type=intent_profile.recommended_bridge_type,
        recommended_article_angle=intent_profile.recommended_article_angle,
        required_subtopics=intent_profile.required_subtopics_merged,
        forbidden_angles=intent_profile.forbidden_angles,
        notes={"rationale": intent_profile.rationale or "", "data_confidence": "high"}
    )

    return dict(links_extension=links_ext, qc_extension=qc_ext, intent_extension=intent_ext)
