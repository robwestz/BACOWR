"""
Next-A1 QC Validation API routes.

Endpoints for validating BacklinkArticle output against Next-A1 specification.
Part of core BacklinkContent Engine quality control.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.database import User
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS
from ..services.qc_validator import NextA1QCValidator, QCStatus

router = APIRouter(prefix="/qc", tags=["qc-validation"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class QCValidationRequest(BaseModel):
    """Request for QC validation."""

    article_content: str = Field(..., min_length=100)
    links_extension: Dict[str, Any]
    intent_extension: Dict[str, Any]
    qc_extension: Dict[str, Any]
    serp_research_extension: Dict[str, Any]


class QCCriterionResult(BaseModel):
    """Result for single QC criterion."""

    status: str
    score: float
    issues: List[str]
    metadata: Dict[str, Any] = {}


class QCValidationResponse(BaseModel):
    """Response for QC validation."""

    status: str
    overall_score: float
    scores: Dict[str, float]
    results: Dict[str, QCCriterionResult]
    issues: List[str]
    recommendations: List[str]
    thresholds_version: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/validate", response_model=QCValidationResponse)
@limiter.limit(RATE_LIMITS["analytics"])
async def validate_content(
    request: Request,
    req: QCValidationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Validate content against all 8 Next-A1 QC criteria.

    **QC Criteria:**
    1. **Preflight**: Correct variabelgifte and bridge_type
    2. **Draft**: Flow, structure, and narrative
    3. **Anchor**: Natural placement and acceptable risk
    4. **Trust**: Source quality and triangulation
    5. **Intent**: Alignment with dominant SERP intent
    6. **LSI**: 6-10 relevant terms in near-window
    7. **Fit**: Voice and tone match publisher
    8. **Compliance**: Disclaimers and policy requirements

    **Status Values:**
    - **PASS**: Meets all criteria
    - **WARNING**: Has minor issues but acceptable
    - **BLOCKED**: Critical issues - content not publishable

    Returns detailed QC report with scores, issues, and recommendations.
    """
    validator = NextA1QCValidator()

    try:
        result = validator.validate(
            article_content=req.article_content,
            links_extension=req.links_extension,
            intent_extension=req.intent_extension,
            qc_extension=req.qc_extension,
            serp_research_extension=req.serp_research_extension
        )

        # Convert results to response format
        formatted_results = {}
        for criterion, criterion_result in result["results"].items():
            formatted_results[criterion] = QCCriterionResult(**criterion_result)

        return QCValidationResponse(
            status=result["status"],
            overall_score=result["overall_score"],
            scores=result["scores"],
            results=formatted_results,
            issues=result["issues"],
            recommendations=result["recommendations"],
            thresholds_version=result["thresholds_version"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"QC validation failed: {str(e)}"
        )


@router.get("/criteria", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_qc_criteria(request: Request):
    """
    Get QC criteria definitions (Next-A1 specification).

    Returns all 8 QC criteria with descriptions and evaluation rules.
    """
    return {
        "criteria": {
            "preflight": {
                "name": "Preflight",
                "description": "Korrekt variabelgifte och rimligt vald bridge_type",
                "checks": [
                    "Bridge type matches intent_extension.recommended_bridge_type",
                    "Bridge type is valid for intent_alignment.overall",
                    "Strong bridge only if no 'off' alignments",
                    "Wrapper bridge only if overall='off'"
                ],
                "weight": "Critical"
            },
            "draft": {
                "name": "Draft Quality",
                "description": "Flyt, struktur och tydlig röd tråd",
                "checks": [
                    "≥900 words",
                    "≥2 H2 sections",
                    "≥60% required subtopics covered",
                    "Clear narrative flow"
                ],
                "weight": "High"
            },
            "anchor": {
                "name": "Anchor Placement",
                "description": "Naturlig placering och ankarrisk låg/medel",
                "checks": [
                    "Anchor NOT in H1 or H2",
                    "Anchor risk: low or medium (not high)",
                    "Natural placement in middle sections",
                    "Not in first paragraph of section"
                ],
                "weight": "Critical"
            },
            "trust": {
                "name": "Trust Sources",
                "description": "Källkvalitet och rimlig triangulering Publisher ↔ TRUST ↔ Target",
                "checks": [
                    "Trust level specified (T1-T4)",
                    "Prefer T1-T3 over T4",
                    "No unresolved trust sources",
                    "No competitive links"
                ],
                "weight": "High"
            },
            "intent": {
                "name": "Intent Alignment",
                "description": "Giftemålet följer dominant SERP-intent",
                "checks": [
                    "intent_alignment.overall NOT 'off'",
                    "No individual alignment 'off' (critical)",
                    "Data confidence: high or medium"
                ],
                "weight": "Critical"
            },
            "lsi": {
                "name": "LSI Quality",
                "description": "6–10 relevanta LSI-termer i närfönster",
                "checks": [
                    "6-10 LSI terms in near-window",
                    "Near-window radius ≥2 sentences",
                    "Required subtopics covered",
                    "Good entity cluster diversity"
                ],
                "weight": "Medium"
            },
            "fit": {
                "name": "Publisher Fit",
                "description": "Röst och ton matchar publikationssajten",
                "checks": [
                    "LIX score within target range",
                    "Publisher profile signals used",
                    "SERP intent signals used",
                    "Tone matches publisher.tone_class"
                ],
                "weight": "Medium"
            },
            "compliance": {
                "name": "Compliance",
                "description": "Disclaimers, policykrav och PII-hantering",
                "checks": [
                    "Gambling content → gambling disclaimer",
                    "Finance content → finance disclaimer",
                    "Health content → health disclaimer",
                    "Crypto content → crypto disclaimer",
                    "Legal content → legal disclaimer"
                ],
                "weight": "Critical"
            }
        },
        "evaluation_rules": [
            "QC läser links_extension, intent_extension och qc_extension tillsammans",
            "Vid konflikt mellan intent_extension.recommended_bridge_type och links_extension.bridge_type: flagga för manuell granskning",
            "Vid intent_extension.overall = 'off': flagga för omarbetning eller wrapper/pivot-lösning"
        ],
        "score_ranges": {
            "PASS": "Score ≥ 80 for all criteria",
            "WARNING": "Score 50-79 for any criterion",
            "BLOCKED": "Score < 50 for any criterion"
        }
    }


@router.get("/thresholds", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_qc_thresholds(request: Request):
    """
    Get QC score thresholds (Next-A1 A1 version).

    Returns threshold definitions for PASS/WARNING/BLOCKED statuses.
    """
    return {
        "version": "A1",
        "thresholds": {
            "overall_score": {
                "PASS": 80,
                "WARNING": 50,
                "BLOCKED": 0
            },
            "criterion_score": {
                "PASS": 80,
                "WARNING": 50,
                "BLOCKED": 0
            }
        },
        "blocking_criteria": [
            "preflight",
            "anchor",
            "intent",
            "compliance"
        ],
        "description": {
            "PASS": "Content meets quality standards and is publishable",
            "WARNING": "Content has minor issues but may be acceptable with review",
            "BLOCKED": "Content has critical issues and requires revision before publishing"
        }
    }


@router.post("/quick-check", response_model=dict)
@limiter.limit(RATE_LIMITS["analytics"])
async def quick_qc_check(
    request: Request,
    bridge_type: str = Field(..., pattern="^(strong|pivot|wrapper)$"),
    recommended_bridge_type: str = Field(..., pattern="^(strong|pivot|wrapper)$"),
    intent_alignment_overall: str = Field(..., pattern="^(aligned|partial|off)$"),
    anchor_risk: str = Field(..., pattern="^(low|medium|high)$"),
    lsi_count: int = Field(..., ge=0, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Quick QC check for key criteria without full validation.

    Useful for real-time validation during content creation.
    """
    issues = []
    status = "PASS"

    # Check bridge type match
    if bridge_type != recommended_bridge_type:
        issues.append(f"Bridge type mismatch: using '{bridge_type}' but '{recommended_bridge_type}' recommended")
        status = "WARNING"

    # Check intent alignment
    if intent_alignment_overall == "off":
        issues.append("Critical: Overall intent alignment is 'off'")
        status = "BLOCKED"

    # Check anchor risk
    if anchor_risk == "high":
        issues.append("Critical: High anchor risk detected")
        status = "BLOCKED"
    elif anchor_risk == "medium" and status == "PASS":
        status = "WARNING"

    # Check LSI count
    if lsi_count < 6:
        issues.append(f"Insufficient LSI terms: {lsi_count} (need 6-10)")
        if status == "PASS":
            status = "WARNING"
    elif lsi_count > 10:
        issues.append(f"Too many LSI terms: {lsi_count} (max 10)")

    return {
        "status": status,
        "issues": issues,
        "passed_checks": len(issues) == 0,
        "recommendation": (
            "Content passes quick checks" if status == "PASS"
            else "Review issues before full QC validation"
        )
    }
