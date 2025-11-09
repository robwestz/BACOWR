"""
Intent Analysis API routes.

Endpoints for intent alignment analysis and bridge type recommendation.
Part of core BacklinkContent Engine - follows Next-A1 specification.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.database import User
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS

router = APIRouter(prefix="/intent", tags=["intent-analysis"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class IntentAlignmentDict(BaseModel):
    """Intent alignment results."""

    anchor_vs_serp: str = Field(..., pattern="^(aligned|partial|off)$")
    target_vs_serp: str = Field(..., pattern="^(aligned|partial|off)$")
    publisher_vs_serp: str = Field(..., pattern="^(aligned|partial|off)$")
    overall: str = Field(..., pattern="^(aligned|partial|off)$")


class IntentAnalysisRequest(BaseModel):
    """Request for intent analysis."""

    # Profiles
    target_profile: Dict[str, Any]
    publisher_profile: Dict[str, Any]
    anchor_profile: Dict[str, Any]
    serp_research: Dict[str, Any]


class IntentAnalysisResponse(BaseModel):
    """Response for intent analysis (Next-A1 intent_extension)."""

    # Intents
    serp_intent_primary: str
    serp_intent_secondary: List[str]
    target_page_intent: str
    anchor_implied_intent: str
    publisher_role_intent: str

    # Alignment
    intent_alignment: IntentAlignmentDict

    # Recommendations
    recommended_bridge_type: str = Field(..., pattern="^(strong|pivot|wrapper)$")
    recommended_article_angle: str
    required_subtopics: List[str]
    forbidden_angles: List[str]

    # Notes
    notes: Dict[str, str]


class BridgeTypeRequest(BaseModel):
    """Quick bridge type recommendation without full analysis."""

    serp_intent: str
    target_intent: str
    publisher_intent: str
    anchor_intent: str


class BridgeTypeResponse(BaseModel):
    """Bridge type recommendation."""

    recommended_bridge_type: str
    confidence: str
    rationale: str
    considerations: List[str]


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=IntentAnalysisResponse)
@limiter.limit(RATE_LIMITS["analytics"])
async def analyze_intent(
    request: Request,
    req: IntentAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform complete intent analysis.

    Returns Next-A1 compatible intent_extension with:
    - Intent classification for all components
    - Alignment analysis (anchor vs SERP vs target vs publisher)
    - Bridge type recommendation (strong/pivot/wrapper)
    - Required subtopics and forbidden angles
    """
    # Use existing IntentAnalyzer
    from ...src.analysis.intent_analyzer import IntentAnalyzer

    analyzer = IntentAnalyzer()

    try:
        result = analyzer.analyze(
            target_profile=req.target_profile,
            publisher_profile=req.publisher_profile,
            anchor_profile=req.anchor_profile,
            serp_research=req.serp_research
        )

        return IntentAnalysisResponse(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent analysis failed: {str(e)}"
        )


@router.post("/bridge-type", response_model=BridgeTypeResponse)
@limiter.limit(RATE_LIMITS["analytics"])
async def recommend_bridge_type(
    request: Request,
    req: BridgeTypeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quick bridge type recommendation.

    Given intents, returns recommended bridge type (strong/pivot/wrapper)
    without full intent analysis.

    **Bridge Types:**
    - **strong**: Direct match, all intents aligned
    - **pivot**: Partial alignment, needs informational bridge
    - **wrapper**: Weak connection, needs extensive context
    """
    from ...src.analysis.intent_analyzer import IntentAnalyzer

    analyzer = IntentAnalyzer()

    # Create minimal alignment dict
    alignment = analyzer._analyze_alignment(
        serp_intent=req.serp_intent,
        target_intent=req.target_intent,
        anchor_intent=req.anchor_intent,
        publisher_intent=req.publisher_intent
    )

    # Recommend bridge type
    bridge_type = analyzer._recommend_bridge_type(
        alignment=alignment,
        target_intent=req.target_intent,
        publisher_intent=req.publisher_intent,
        serp_intent=req.serp_intent
    )

    # Generate rationale
    rationale = analyzer._generate_rationale(
        serp_intent=req.serp_intent,
        target_intent=req.target_intent,
        publisher_intent=req.publisher_intent,
        alignment=alignment,
        bridge_type=bridge_type
    )

    # Determine confidence
    confidence = "high" if alignment["overall"] == "aligned" else \
                 "medium" if alignment["overall"] == "partial" else "low"

    # Generate considerations
    considerations = []
    if alignment["overall"] == "off":
        considerations.append("Severe misalignment - wrapper bridge required")
    if alignment["publisher_vs_serp"] == "off":
        considerations.append("Publisher not natural fit for SERP intent")
    if alignment["target_vs_serp"] == "off":
        considerations.append("Target page not aligned with SERP intent")
    if bridge_type == "pivot":
        considerations.append("Needs informational bridge to connect commercial target")
    if bridge_type == "strong":
        considerations.append("Direct placement possible - all intents aligned")

    return BridgeTypeResponse(
        recommended_bridge_type=bridge_type,
        confidence=confidence,
        rationale=rationale,
        considerations=considerations
    )


@router.get("/bridge-types", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_bridge_types(request: Request):
    """
    Get bridge type definitions (Next-A1 specification).

    Returns all valid bridge types with descriptions and usage rules.
    """
    return {
        "bridge_types": {
            "strong": {
                "description": "Direct match - all intents aligned",
                "triggers": [
                    "anchor semantics ≈ target page focus",
                    "publisher niche overlap ≥ 0.7"
                ],
                "placement_rule": "Placera länken i den första tydligt relevanta huvudsektionen (ofta en H2), tidigt men efter att kontexten etablerats",
                "trust_requirement": "Minst 1 standard/auktoritet (T1/T2/T3 beroende på ämne)",
                "use_when": [
                    "All alignment scores are 'aligned'",
                    "Publisher naturally covers target topic",
                    "Anchor directly matches target focus"
                ]
            },
            "pivot": {
                "description": "Needs informational bridge to connect commercial target",
                "triggers": [
                    "Anchor is broader or adjacent to target",
                    "publisher niche overlap 0.4–0.7"
                ],
                "method": "Formulera en övergripande problemformulering eller fråga; etablera en semantisk pivot som knyter ihop publisher och target",
                "trust_requirement": "1–2 källor som stödjer pivot-vinkeln",
                "use_when": [
                    "Overall alignment is 'partial'",
                    "Publisher is informational, target is commercial",
                    "Need to establish context before linking"
                ]
            },
            "wrapper": {
                "description": "Weak connection - needs extensive context wrapping",
                "triggers": [
                    "publisher niche overlap < 0.4",
                    "Anchor appears generic or unrelated"
                ],
                "method": "Bygg en neutral temaram kring metodik, risk, statistik, innovation, etik, hållbarhet eller säkerhet",
                "trust_requirement": "2–3 källor; triangulering Publisher ↔ TRUST ↔ Target",
                "placement_rule": "Placera länken först efter att bryggan/metaramen är etablerad",
                "use_when": [
                    "Overall alignment is 'off'",
                    "No direct connection between publisher and target",
                    "Requires meta-framework to justify link"
                ]
            }
        },
        "selection_flow": {
            "1": "Check intent_alignment.overall",
            "2_if_aligned": "Use 'strong' bridge",
            "2_if_partial": "Check if publisher=info AND target=commercial → 'pivot', else 'pivot'",
            "2_if_off": "Use 'wrapper' bridge"
        }
    }


@router.get("/alignment-guide", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_alignment_guide(request: Request):
    """
    Get intent alignment interpretation guide.

    Explains what 'aligned', 'partial', and 'off' mean.
    """
    return {
        "alignment_values": {
            "aligned": {
                "description": "Intents match or are highly compatible",
                "examples": [
                    "info_primary vs info_primary",
                    "commercial_research vs commercial_research",
                    "transactional_with_info_support vs transactional"
                ],
                "action": "Direct connection possible"
            },
            "partial": {
                "description": "Intents are compatible but not perfect match",
                "examples": [
                    "info_primary vs commercial_research",
                    "commercial_research vs transactional",
                    "info_primary vs support"
                ],
                "action": "Bridge required (usually pivot)"
            },
            "off": {
                "description": "Intents are incompatible",
                "examples": [
                    "info_primary vs transactional (direct)",
                    "navigational_brand vs commercial_research",
                    "support vs transactional"
                ],
                "action": "Wrapper bridge required or reconsider placement"
            }
        },
        "compatibility_matrix": {
            "info_primary": ["info_primary", "commercial_research"],
            "commercial_research": ["info_primary", "commercial_research", "transactional"],
            "transactional": ["commercial_research", "transactional"],
            "navigational_brand": ["navigational_brand"],
            "support": ["support", "info_primary"],
            "local": ["local", "info_primary"]
        }
    }


@router.post("/validate-alignment", response_model=dict)
@limiter.limit(RATE_LIMITS["analytics"])
async def validate_alignment(
    request: Request,
    alignment: IntentAlignmentDict,
    bridge_type: str = Field(..., pattern="^(strong|pivot|wrapper)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate if bridge_type matches alignment.

    Next-A1 Rule: "Val av bridge_type ska alltid valideras mot intent_extension.overall"
    """
    issues = []

    # Validation rules from Next-A1-2
    if bridge_type == "strong":
        # Strong only if no component is 'off'
        if any(val == "off" for val in [
            alignment.anchor_vs_serp,
            alignment.target_vs_serp,
            alignment.publisher_vs_serp
        ]):
            issues.append("Strong bridge requires no 'off' alignments")

    elif bridge_type == "pivot":
        # Pivot when partial alignment
        if alignment.overall == "off":
            issues.append("Pivot bridge not suitable for 'off' overall alignment - use wrapper")
        elif alignment.overall == "aligned":
            issues.append("Pivot bridge unnecessary - use strong for full alignment")

    elif bridge_type == "wrapper":
        # Wrapper when overall is 'off'
        if alignment.overall != "off":
            issues.append("Wrapper bridge only needed when overall alignment is 'off'")

    is_valid = len(issues) == 0

    return {
        "is_valid": is_valid,
        "issues": issues,
        "recommendation": (
            f"Bridge type '{bridge_type}' is correct for this alignment" if is_valid
            else f"Consider different bridge type: {_suggest_bridge_type(alignment)}"
        )
    }


def _suggest_bridge_type(alignment: IntentAlignmentDict) -> str:
    """Suggest correct bridge type based on alignment."""
    if alignment.overall == "aligned":
        return "strong"
    elif alignment.overall == "off":
        return "wrapper"
    else:
        return "pivot"
