"""
SERP Fetcher - Fetches and caches SERP results.

Supports both mock (for testing) and real API modes.
Caches results to avoid unnecessary API calls.

EXTENSIBILITY NOTE:
This module is designed for reuse in:
- Rank tracking systems
- Competitive analysis tools
- SERP feature extraction
- Intent analysis platforms
- Historical SERP data warehousing
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from diskcache import Cache

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SerpResult:
    """
    Individual SERP result.

    Rich data structure designed for reusability across SEO tools.
    """
    rank: int
    url: str
    title: str
    snippet: str
    detected_page_type: Optional[str] = None  # guide, comparison, product, etc.
    content_excerpt: Optional[str] = None
    key_entities: List[str] = field(default_factory=list)
    key_subtopics: List[str] = field(default_factory=list)
    why_it_ranks: Optional[str] = None  # Analysis of ranking factors

    # Extensibility: Additional SERP features
    featured_snippet: bool = False
    faq_schema: bool = False
    review_stars: Optional[float] = None
    meta_robots: Optional[str] = None


@dataclass
class SerpSet:
    """
    Complete SERP result set for a single query.

    Contains all results plus metadata and analysis.
    """
    query: str
    language: str
    location: Optional[str]
    results: List[SerpResult]
    fetched_at: str
    result_count: int

    # Analysis fields (populated by SerpAnalyzer)
    dominant_intent: Optional[str] = None
    secondary_intents: List[str] = field(default_factory=list)
    page_archetypes: List[str] = field(default_factory=list)
    required_subtopics: List[str] = field(default_factory=list)


class SerpFetcher:
    """
    Fetches SERP results with caching and mock support.

    Modes:
    - mock: Returns synthetic SERP data for testing
    - api: Uses real SERP API (configurable)
    """

    def __init__(
        self,
        mode: str = "mock",
        api_key: Optional[str] = None,
        cache_dir: Optional[Path] = None,
        cache_ttl: int = 86400,  # 24 hours
        language: str = "sv",
        location: str = "Sweden"
    ):
        """
        Initialize SERP fetcher.

        Args:
            mode: "mock" or "api"
            api_key: API key for SERP service (when mode="api")
            cache_dir: Directory for caching SERP results
            cache_ttl: Cache time-to-live in seconds
            language: Default language for SERP
            location: Default location for SERP
        """
        self.mode = mode
        self.api_key = api_key
        self.language = language
        self.location = location

        # Setup cache
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / "storage" / "serp"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(cache_dir))
        self.cache_ttl = cache_ttl

        logger.info("SERP Fetcher initialized", mode=mode, cache_dir=str(cache_dir))

    def fetch_serp(
        self,
        query: str,
        max_results: int = 10,
        language: Optional[str] = None,
        location: Optional[str] = None
    ) -> SerpSet:
        """
        Fetch SERP results for a query.

        Checks cache first, then fetches if needed.

        Args:
            query: Search query
            max_results: Maximum number of results to fetch (default: 10)
            language: Language override (default: instance language)
            location: Location override (default: instance location)

        Returns:
            SerpSet with results

        EXTENSIBILITY NOTE:
        This method can be extended to:
        - Extract SERP features (PAA, featured snippets, knowledge panels)
        - Capture additional metadata (ads, related searches, etc.)
        - Support different SERP APIs (Google, Bing, etc.)
        """
        lang = language or self.language
        loc = location or self.location

        logger.info("Fetching SERP", query=query, mode=self.mode)

        # Check cache
        cache_key = self._get_cache_key(query, lang, loc)
        cached = self.cache.get(cache_key)

        if cached:
            logger.debug("SERP cache hit", query=query)
            return self._deserialize_serp_set(cached)

        # Fetch based on mode
        if self.mode == "mock":
            serp_set = self._fetch_mock_serp(query, max_results, lang, loc)
        elif self.mode == "api":
            serp_set = self._fetch_api_serp(query, max_results, lang, loc)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        # Cache result
        self.cache.set(cache_key, self._serialize_serp_set(serp_set), expire=self.cache_ttl)

        logger.info("SERP fetched", query=query, results=len(serp_set.results))
        return serp_set

    def _get_cache_key(self, query: str, language: str, location: str) -> str:
        """Generate cache key from query parameters."""
        key_string = f"{query}|{language}|{location}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _fetch_mock_serp(
        self,
        query: str,
        max_results: int,
        language: str,
        location: str
    ) -> SerpSet:
        """
        Fetch mock SERP data for testing.

        Generates realistic-looking SERP results based on query patterns.
        """
        logger.debug("Generating mock SERP", query=query)

        results = []

        # Determine likely intent from query
        query_lower = query.lower()
        if any(word in query_lower for word in ["bäst", "best", "jämför", "compare"]):
            dominant_intent = "commercial_research"
            page_types = ["comparison", "guide", "category"]
        elif any(word in query_lower for word in ["hur", "how", "vad är", "what is"]):
            dominant_intent = "info_primary"
            page_types = ["guide", "article", "faq"]
        elif any(word in query_lower for word in ["köp", "buy", "pris", "price"]):
            dominant_intent = "transactional"
            page_types = ["product", "category", "comparison"]
        else:
            dominant_intent = "mixed"
            page_types = ["guide", "article", "comparison"]

        # Generate mock results
        for i in range(min(max_results, 10)):
            rank = i + 1
            page_type = page_types[i % len(page_types)]

            result = SerpResult(
                rank=rank,
                url=f"https://example-site-{rank}.com/article-{rank}",
                title=f"{query.title()} - {page_type.title()} #{rank}",
                snippet=f"Comprehensive {page_type} covering {query}. "
                       f"Learn about key aspects, comparisons, and recommendations. "
                       f"Updated information with expert analysis.",
                detected_page_type=page_type,
                content_excerpt=f"Mock content excerpt for {query} covering main points...",
                key_entities=[query.split()[0] if query.split() else "Entity"],
                key_subtopics=[f"subtopic_{i+1}", f"aspect_{i+1}"],
                why_it_ranks=f"Ranks due to comprehensive coverage and {page_type} format",
                featured_snippet=(rank == 1 and dominant_intent == "info_primary")
            )
            results.append(result)

        serp_set = SerpSet(
            query=query,
            language=language,
            location=location,
            results=results,
            fetched_at=datetime.utcnow().isoformat(),
            result_count=len(results),
            dominant_intent=dominant_intent,
            page_archetypes=page_types
        )

        return serp_set

    def _fetch_api_serp(
        self,
        query: str,
        max_results: int,
        language: str,
        location: str
    ) -> SerpSet:
        """
        Fetch real SERP data from API.

        EXTENSIBILITY NOTE:
        This is a stub implementation. In production, integrate with:
        - SerpApi, Serper, or similar SERP API
        - Google Custom Search API
        - Bing Search API
        - Your own scraping infrastructure

        Example integration points:
        - Extract featured snippets, PAA boxes
        - Capture SERP features (knowledge panel, local pack, etc.)
        - Track ad positions
        - Monitor SERP changes over time
        """
        if not self.api_key:
            logger.warning("No API key provided, falling back to mock")
            return self._fetch_mock_serp(query, max_results, language, location)

        logger.info("Real API SERP fetch not implemented, using mock")
        # TODO: Implement real API integration
        # Example:
        # import serpapi
        # client = serpapi.Client(api_key=self.api_key)
        # results = client.search({
        #     'q': query,
        #     'location': location,
        #     'hl': language,
        #     'num': max_results
        # })
        # return self._parse_api_response(results)

        return self._fetch_mock_serp(query, max_results, language, location)

    def _serialize_serp_set(self, serp_set: SerpSet) -> Dict:
        """Serialize SerpSet to dict for caching."""
        return {
            'query': serp_set.query,
            'language': serp_set.language,
            'location': serp_set.location,
            'fetched_at': serp_set.fetched_at,
            'result_count': serp_set.result_count,
            'dominant_intent': serp_set.dominant_intent,
            'secondary_intents': serp_set.secondary_intents,
            'page_archetypes': serp_set.page_archetypes,
            'required_subtopics': serp_set.required_subtopics,
            'results': [asdict(r) for r in serp_set.results]
        }

    def _deserialize_serp_set(self, data: Dict) -> SerpSet:
        """Deserialize dict to SerpSet."""
        results = [SerpResult(**r) for r in data['results']]
        return SerpSet(
            query=data['query'],
            language=data['language'],
            location=data['location'],
            results=results,
            fetched_at=data['fetched_at'],
            result_count=data['result_count'],
            dominant_intent=data.get('dominant_intent'),
            secondary_intents=data.get('secondary_intents', []),
            page_archetypes=data.get('page_archetypes', []),
            required_subtopics=data.get('required_subtopics', [])
        )

    def clear_cache(self) -> None:
        """Clear all cached SERP results."""
        self.cache.clear()
        logger.info("SERP cache cleared")
