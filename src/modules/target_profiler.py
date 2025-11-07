"""
Target Page Profiler - Analyzes target URLs for backlink placement.

Extends PageProfile with target-specific analysis including:
- Core offer identification
- Candidate query generation
- Commercial intent detection
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .page_profile import PageProfile, PageProfiler
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TargetProfile:
    """
    Extended profile for target pages (the URL receiving the backlink).

    Based on BacklinkJobPackage schema's target_profile requirements.
    """
    url: str
    http_status: int
    title: str
    meta_description: Optional[str]
    h1: Optional[str]
    h2_h3_sample: List[str]
    main_content_excerpt: Optional[str]
    detected_language: str
    core_entities: List[str]
    core_topics: List[str]
    core_offer: str
    candidate_main_queries: List[str]

    # Additional analysis
    commercial_signals: List[str] = None
    content_type: Optional[str] = None  # e.g., "product", "service", "guide", "comparison"


class TargetProfiler:
    """
    Profiles target pages for backlink content generation.

    Uses the reusable PageProfiler and adds target-specific analysis.
    """

    def __init__(self):
        """Initialize target profiler with page profiler."""
        self.page_profiler = PageProfiler()

    def profile_target(self, target_url: str) -> TargetProfile:
        """
        Profile a target URL and extract backlink-relevant information.

        Args:
            target_url: The URL that will receive the backlink

        Returns:
            TargetProfile with comprehensive analysis
        """
        logger.info("Profiling target URL", url=target_url)

        # Get base page profile
        page_profile = self.page_profiler.profile_page(target_url)

        # Analyze commercial signals
        commercial_signals = self._detect_commercial_signals(page_profile)

        # Detect content type
        content_type = self._detect_content_type(page_profile)

        # Generate candidate queries
        candidate_queries = self._generate_candidate_queries(page_profile)

        # Identify core offer
        core_offer = self._identify_core_offer(page_profile, content_type)

        # Build target profile
        target_profile = TargetProfile(
            url=page_profile.url,
            http_status=page_profile.http_status,
            title=page_profile.title or "",
            meta_description=page_profile.meta_description,
            h1=page_profile.h1,
            h2_h3_sample=page_profile.h2_h3_sample,
            main_content_excerpt=page_profile.main_content_excerpt,
            detected_language=page_profile.detected_language or "unknown",
            core_entities=page_profile.core_entities,
            core_topics=page_profile.core_topics,
            core_offer=core_offer,
            candidate_main_queries=candidate_queries,
            commercial_signals=commercial_signals,
            content_type=content_type
        )

        logger.info(
            "Target profiling complete",
            url=target_url,
            content_type=content_type,
            query_candidates=len(candidate_queries)
        )

        return target_profile

    def _detect_commercial_signals(self, page_profile: PageProfile) -> List[str]:
        """
        Detect commercial intent signals on the page.

        Signals include pricing, CTAs, product features, etc.
        """
        signals = []

        # Check content for commercial keywords
        content = (page_profile.main_content_excerpt or "").lower()
        title = (page_profile.title or "").lower()

        commercial_keywords = {
            "price": ["pris", "price", "kostnad", "cost", "betala", "pay"],
            "purchase": ["köp", "buy", "purchase", "beställ", "order"],
            "comparison": ["jämför", "compare", "bäst", "best", "vs", "versus"],
            "features": ["funktioner", "features", "fördelar", "benefits"],
            "trial": ["prova", "trial", "demo", "test"],
            "guarantee": ["garanti", "guarantee", "refund", "återbetalning"],
        }

        for signal_type, keywords in commercial_keywords.items():
            if any(kw in content or kw in title for kw in keywords):
                signals.append(signal_type)

        return signals

    def _detect_content_type(self, page_profile: PageProfile) -> str:
        """
        Classify the content type of the target page.

        Types: product, service, guide, comparison, category, tool, article
        """
        title = (page_profile.title or "").lower()
        headings = " ".join(page_profile.h2_h3_sample).lower()

        # Check schema types
        if page_profile.schema_types:
            schema_lower = [s.lower() for s in page_profile.schema_types]
            if any('product' in s for s in schema_lower):
                return "product"
            if any('article' in s for s in schema_lower):
                return "article"

        # Keyword-based detection
        if any(word in title for word in ["jämför", "compare", "vs", "versus", "bäst", "best"]):
            return "comparison"
        if any(word in title for word in ["guide", "how to", "hur", "så här"]):
            return "guide"
        if any(word in title for word in ["tool", "verktyg", "calculator", "kalkylator"]):
            return "tool"
        if "kategori" in title or "category" in title:
            return "category"

        # Check for product/service indicators
        if any(signal in ["price", "purchase", "features"] for signal in
               self._detect_commercial_signals(page_profile)):
            # Distinguish product vs service
            if any(word in headings for word in ["leverans", "delivery", "shipping", "frakt"]):
                return "product"
            return "service"

        return "article"

    def _generate_candidate_queries(self, page_profile: PageProfile) -> List[str]:
        """
        Generate candidate main queries based on page content.

        These queries represent what users might search to find this page.
        """
        queries = []

        # Extract from title (most important)
        if page_profile.title:
            title_clean = page_profile.title.lower()
            # Remove brand/site name (often after | or -)
            title_parts = title_clean.split("|")[0].split("-")[0].strip()
            if len(title_parts) > 5:
                queries.append(title_parts)

        # Extract from H1
        if page_profile.h1 and page_profile.h1 != page_profile.title:
            h1_clean = page_profile.h1.lower().strip()
            if len(h1_clean) > 5 and h1_clean not in queries:
                queries.append(h1_clean)

        # Combine entities with topics
        if page_profile.core_entities and page_profile.core_topics:
            for entity in page_profile.core_entities[:2]:
                for topic in page_profile.core_topics[:2]:
                    combined = f"{entity.lower()} {topic.lower()}"
                    if combined not in queries:
                        queries.append(combined)

        # Limit to reasonable number
        return queries[:5]

    def _identify_core_offer(self, page_profile: PageProfile, content_type: str) -> str:
        """
        Identify the core offer/value proposition of the target page.

        This answers: "What does this page help the user with?"
        """
        # Start with meta description if available (often contains value prop)
        if page_profile.meta_description and len(page_profile.meta_description) > 20:
            return page_profile.meta_description

        # Build from title and content type
        title = page_profile.title or "this page"

        offer_templates = {
            "product": f"Provides information about and access to {title.lower()}",
            "service": f"Offers {title.lower()} to help users",
            "guide": f"Guides users on {title.lower()}",
            "comparison": f"Helps users compare and choose {title.lower()}",
            "tool": f"Provides tools for {title.lower()}",
            "category": f"Overview and options for {title.lower()}",
            "article": f"Informerar om {title.lower()}" if page_profile.detected_language == "sv"
                      else f"Informs about {title.lower()}",
        }

        # If we have a clear H1, use it
        if page_profile.h1 and len(page_profile.h1) > len(title):
            base_offer = offer_templates.get(content_type, "Provides information about {}")
            return base_offer.replace(title.lower(), page_profile.h1.lower())

        return offer_templates.get(content_type, f"Provides information about {title.lower()}")

    def to_job_package_format(self, target_profile: TargetProfile) -> Dict:
        """
        Convert TargetProfile to BacklinkJobPackage schema format.

        Returns:
            Dictionary matching the target_profile section of BacklinkJobPackage
        """
        return {
            "url": target_profile.url,
            "http_status": target_profile.http_status,
            "title": target_profile.title,
            "meta_description": target_profile.meta_description,
            "h1": target_profile.h1,
            "h2_h3_sample": target_profile.h2_h3_sample,
            "main_content_excerpt": target_profile.main_content_excerpt,
            "detected_language": target_profile.detected_language,
            "core_entities": target_profile.core_entities,
            "core_topics": target_profile.core_topics,
            "core_offer": target_profile.core_offer,
            "candidate_main_queries": target_profile.candidate_main_queries,
        }
