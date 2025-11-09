"""
SERP Research API routes.

Endpoints for SERP analysis following Next-A1 specification.
Part of core BacklinkContent Engine.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field

from ..database import get_db
from ..models.database import User
from ..auth import get_current_user
from ..rate_limit import limiter, RATE_LIMITS
from ..services.serp_api import SerpAPIIntegration

router = APIRouter(prefix="/serp", tags=["serp-research"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class SERPResearchRequest(BaseModel):
    """Request for SERP research."""

    main_query: str = Field(..., min_length=1, max_length=200)
    cluster_queries: List[str] = Field(default=[], max_items=5)
    country: str = Field(default="se", pattern="^[a-z]{2}$")
    language: str = Field(default="sv", pattern="^[a-z]{2}$")


class SERPResultItem(BaseModel):
    """Single SERP result."""

    rank: int
    url: str
    title: str
    snippet: str
    detected_page_type: str
    content_signals: List[str]
    key_entities: List[str]
    key_subtopics: List[str]


class SERPSet(BaseModel):
    """SERP set for one query (Next-A1 format)."""

    query: str
    dominant_intent: str
    secondary_intents: List[str]
    page_archetypes: List[str]
    required_subtopics: List[str]
    top_results_sample: List[SERPResultItem]


class SERPResearchResponse(BaseModel):
    """Response for SERP research (Next-A1 serp_research_extension)."""

    main_query: str
    cluster_queries: List[str]
    queries_rationale: str
    serp_sets: List[SERPSet]
    derived_links: dict


class QueryGenerationRequest(BaseModel):
    """Request for query generation."""

    target_url: str = Field(..., min_length=1)
    anchor_text: str = Field(..., min_length=1, max_length=200)
    target_profile: Optional[dict] = None  # If already have profile
    max_cluster_queries: int = Field(default=3, ge=1, le=5)


class QueryGenerationResponse(BaseModel):
    """Response for query generation."""

    main_query: str
    cluster_queries: List[str]
    rationale: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/research", response_model=SERPResearchResponse)
@limiter.limit("20/hour")  # SERP API calls are expensive
async def perform_serp_research(
    request: Request,
    req: SERPResearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform SERP research for main + cluster queries.

    Returns Next-A1 compatible serp_research_extension.

    **Rate Limited:** 20 requests/hour (SERP API costs)

    **Required:** SERPAPI_KEY environment variable
    """
    serp_service = SerpAPIIntegration()

    try:
        result = await serp_service.research(
            main_query=req.main_query,
            cluster_queries=req.cluster_queries,
            country=req.country,
            language=req.language
        )

        return SERPResearchResponse(**result)

    except ValueError as e:
        if "SERPAPI_KEY" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SERP API not configured. Set SERPAPI_KEY environment variable."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SERP research failed: {str(e)}"
        )


@router.post("/generate-queries", response_model=QueryGenerationResponse)
@limiter.limit(RATE_LIMITS["create_job"])
async def generate_queries(
    request: Request,
    req: QueryGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generate main + cluster queries from target URL and anchor.

    Used before SERP research to determine what queries to search.
    """
    # Use existing SERPResearcher for query generation
    from ...src.research.serp_researcher import SERPResearcher

    researcher = SERPResearcher(mock_mode=True)

    # If no profile provided, create minimal one
    target_profile = req.target_profile or {
        "url": req.target_url,
        "core_entities": [req.anchor_text],
        "core_topics": [],
        "title": "",
        "candidate_main_queries": []
    }

    main_query, cluster_queries, rationale = researcher.generate_queries(
        target_profile=target_profile,
        anchor_text=req.anchor_text,
        max_cluster_queries=req.max_cluster_queries
    )

    return QueryGenerationResponse(
        main_query=main_query,
        cluster_queries=cluster_queries,
        rationale=rationale
    )


@router.get("/intents", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_intent_types(request: Request):
    """
    Get available intent types (Next-A1 specification).

    Returns all valid intent values for classification.
    """
    return {
        "intent_types": [
            "info_primary",
            "commercial_research",
            "transactional",
            "navigational_brand",
            "support",
            "local",
            "mixed"
        ],
        "description": {
            "info_primary": "Informational content - guides, explanations, how-to",
            "commercial_research": "Research before purchase - comparisons, reviews, best X",
            "transactional": "Ready to buy - product pages, pricing, order",
            "navigational_brand": "Looking for specific brand/website",
            "support": "Customer support, help, FAQ",
            "local": "Local business search",
            "mixed": "Multiple intents present"
        }
    }


@router.get("/page-types", response_model=dict)
@limiter.limit(RATE_LIMITS["get_job"])
def get_page_types(request: Request):
    """
    Get available page types (Next-A1 specification).

    Returns all valid page type values for classification.
    """
    return {
        "page_types": [
            "guide",
            "comparison",
            "category",
            "product",
            "review",
            "tool",
            "faq",
            "news",
            "official",
            "other"
        ],
        "description": {
            "guide": "How-to guides, tutorials",
            "comparison": "A vs B comparisons",
            "category": "Category/listing pages",
            "product": "Product detail pages",
            "review": "Reviews, ratings",
            "tool": "Interactive tools, calculators",
            "faq": "FAQ pages",
            "news": "News articles",
            "official": "Official government/authority pages",
            "other": "Other page types"
        }
    }
