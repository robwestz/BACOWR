"""
SERP API Integration Service.

Integrates with real SERP APIs (SerpAPI, ValueSERP) to fetch actual search results
following Next-A1 specification for serp_research_extension.
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


class SerpAPIIntegration:
    """
    Integration with SerpAPI for real SERP data.

    Supports:
    - Google Search results
    - Multiple queries (main + cluster)
    - Top-10 result analysis
    - Next-A1 compatible output format
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize SERP API integration.

        Args:
            api_key: SerpAPI key (defaults to SERPAPI_KEY env var)
        """
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"

    async def fetch_serp(
        self,
        query: str,
        country: str = "se",
        language: str = "sv",
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Fetch SERP results from SerpAPI.

        Args:
            query: Search query
            country: Country code (e.g., "se", "us")
            language: Language code (e.g., "sv", "en")
            num_results: Number of results to fetch

        Returns:
            SERP results dict
        """
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not configured. Set environment variable or pass api_key.")

        params = {
            "q": query,
            "api_key": self.api_key,
            "gl": country,  # Country
            "hl": language,  # Language
            "num": num_results,
            "engine": "google"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()

    def parse_serp_results(
        self,
        serp_data: Dict[str, Any],
        query: str
    ) -> Dict[str, Any]:
        """
        Parse SerpAPI response into Next-A1 compatible format.

        Args:
            serp_data: Raw SerpAPI response
            query: Original query

        Returns:
            Parsed serp_set for serp_research_extension
        """
        organic_results = serp_data.get("organic_results", [])

        # Parse top results
        top_results_sample = []
        for i, result in enumerate(organic_results[:10], start=1):
            parsed_result = {
                "rank": i,
                "url": result.get("link", ""),
                "title": result.get("title", ""),
                "snippet": result.get("snippet", ""),
                "detected_page_type": self._detect_page_type(result),
                "content_signals": self._extract_content_signals(result),
                "key_entities": self._extract_entities(result),
                "key_subtopics": self._extract_subtopics(result)
            }
            top_results_sample.append(parsed_result)

        # Classify intent
        dominant_intent, secondary_intents = self._classify_intent(organic_results, query)

        # Determine page archetypes
        page_archetypes = self._determine_archetypes(top_results_sample)

        # Extract required subtopics (appear in 60%+ of results)
        required_subtopics = self._extract_required_subtopics(top_results_sample)

        return {
            "query": query,
            "dominant_intent": dominant_intent,
            "secondary_intents": secondary_intents,
            "page_archetypes": page_archetypes,
            "required_subtopics": required_subtopics,
            "top_results_sample": top_results_sample
        }

    def _detect_page_type(self, result: Dict[str, Any]) -> str:
        """
        Detect page type from SERP result.

        Returns: guide | comparison | category | product | review | tool | faq | news | official | other
        """
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        url = result.get("link", "").lower()

        # Patterns for each type
        if any(word in title or word in snippet for word in ["guide", "how to", "hur man"]):
            return "guide"
        elif any(word in title or word in snippet for word in ["vs", "jämför", "compare", "versus"]):
            return "comparison"
        elif any(word in title or word in snippet for word in ["review", "recension", "test"]):
            return "review"
        elif any(word in url for word in ["/category/", "/kategori/", "/products/"]):
            return "category"
        elif any(word in title or word in snippet for word in ["buy", "köp", "product", "produkt"]):
            return "product"
        elif any(word in title or word in snippet for word in ["faq", "vanliga frågor", "questions"]):
            return "faq"
        elif any(word in url for word in ["/tool/", "/calculator/", "/verktyg/"]):
            return "tool"
        elif any(word in url for word in [".gov", ".se/myndighet", "official"]):
            return "official"
        elif any(word in snippet for word in ["news", "nyheter", "today"]):
            return "news"
        else:
            return "other"

    def _extract_content_signals(self, result: Dict[str, Any]) -> List[str]:
        """Extract key content signals from result."""
        signals = []

        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()

        # Detect emphasis signals
        if any(word in snippet for word in ["jämförelse", "comparison", "compare"]):
            signals.append("emphasizes comparison")
        if any(word in snippet for word in ["transparent", "öppenhet", "villkor", "terms"]):
            signals.append("emphasizes transparency")
        if any(word in snippet for word in ["risk", "varning", "warning"]):
            signals.append("mentions risks/warnings")
        if any(word in snippet for word in ["fördelar", "nackdelar", "pros", "cons"]):
            signals.append("pros and cons analysis")
        if any(word in snippet for word in ["guide", "steg", "steps"]):
            signals.append("step-by-step guidance")
        if any(word in snippet for word in ["expert", "specialist", "professional"]):
            signals.append("expert perspective")

        return signals

    def _extract_entities(self, result: Dict[str, Any]) -> List[str]:
        """Extract key entities from result (simplified NER)."""
        title = result.get("title", "")
        snippet = result.get("snippet", "")

        # Simple capitalized word extraction (Swedish + English)
        import re
        text = f"{title} {snippet}"

        # Find capitalized phrases
        entities = set(re.findall(r'\b[A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)*\b', text))

        # Limit to top 5
        return list(entities)[:5]

    def _extract_subtopics(self, result: Dict[str, Any]) -> List[str]:
        """Extract subtopics from result."""
        snippet = result.get("snippet", "").lower()

        subtopics = set()

        # Common subtopic patterns
        patterns = [
            "pris", "price", "cost", "kostnad",
            "kvalitet", "quality",
            "fördelar", "nackdelar", "pros", "cons",
            "jämförelse", "comparison",
            "guide", "tips", "råd",
            "säkerhet", "security", "säker",
            "risker", "risks", "varningar"
        ]

        for pattern in patterns:
            if pattern in snippet:
                subtopics.add(pattern)

        return list(subtopics)[:5]

    def _classify_intent(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> tuple[str, List[str]]:
        """
        Classify dominant and secondary intents.

        Returns: (dominant_intent, secondary_intents)
        """
        intent_scores = {
            "info_primary": 0,
            "commercial_research": 0,
            "transactional": 0,
            "navigational_brand": 0,
            "support": 0,
            "local": 0
        }

        query_lower = query.lower()

        # Analyze query
        if any(word in query_lower for word in ["how", "hur", "what", "vad", "why", "varför"]):
            intent_scores["info_primary"] += 3
        if any(word in query_lower for word in ["best", "bäst", "compare", "jämför", "vs", "review"]):
            intent_scores["commercial_research"] += 3
        if any(word in query_lower for word in ["buy", "köp", "order", "beställ", "price"]):
            intent_scores["transactional"] += 3
        if any(word in query_lower for word in ["brand", "official", "login"]):
            intent_scores["navigational_brand"] += 3

        # Analyze top results
        for result in results[:5]:  # Top 5 results weight more
            title = result.get("title", "").lower()
            snippet = result.get("snippet", "").lower()

            # Info signals
            if any(word in title or word in snippet for word in ["guide", "tutorial", "explanation"]):
                intent_scores["info_primary"] += 1

            # Commercial research signals
            if any(word in title or word in snippet for word in ["review", "comparison", "test", "vs"]):
                intent_scores["commercial_research"] += 2

            # Transactional signals
            if any(word in title or word in snippet for word in ["buy", "price", "shop", "order"]):
                intent_scores["transactional"] += 2

        # Determine dominant intent
        dominant = max(intent_scores, key=intent_scores.get)

        # Secondary intents (>30% of dominant score)
        threshold = intent_scores[dominant] * 0.3
        secondary = [
            intent for intent, score in intent_scores.items()
            if score >= threshold and intent != dominant
        ]

        return dominant, secondary

    def _determine_archetypes(self, results: List[Dict[str, Any]]) -> List[str]:
        """Determine common page archetypes from results."""
        archetype_counts = {}

        for result in results:
            page_type = result.get("detected_page_type", "other")
            archetype_counts[page_type] = archetype_counts.get(page_type, 0) + 1

        # Return archetypes that appear in 20%+ of results
        threshold = len(results) * 0.2
        common_archetypes = [
            archetype for archetype, count in archetype_counts.items()
            if count >= threshold
        ]

        return sorted(common_archetypes, key=lambda x: archetype_counts[x], reverse=True)

    def _extract_required_subtopics(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract subtopics that appear in 60%+ of results."""
        subtopic_counts = {}

        for result in results:
            for subtopic in result.get("key_subtopics", []):
                subtopic_counts[subtopic] = subtopic_counts.get(subtopic, 0) + 1

        # 60% threshold
        threshold = len(results) * 0.6
        required = [
            subtopic for subtopic, count in subtopic_counts.items()
            if count >= threshold
        ]

        return required[:10]  # Max 10

    async def research(
        self,
        main_query: str,
        cluster_queries: List[str],
        country: str = "se",
        language: str = "sv"
    ) -> Dict[str, Any]:
        """
        Perform complete SERP research with main + cluster queries.

        Returns Next-A1 compatible serp_research_extension.
        """
        serp_sets = []

        try:
            # Fetch main query
            main_data = await self.fetch_serp(main_query, country, language)
            main_parsed = self.parse_serp_results(main_data, main_query)
            serp_sets.append(main_parsed)

            # Fetch cluster queries
            for cluster_query in cluster_queries:
                cluster_data = await self.fetch_serp(cluster_query, country, language)
                cluster_parsed = self.parse_serp_results(cluster_data, cluster_query)
                serp_sets.append(cluster_parsed)

            # Aggregate
            all_subtopics = set()
            for serp_set in serp_sets:
                all_subtopics.update(serp_set.get("required_subtopics", []))

            return {
                "main_query": main_query,
                "cluster_queries": cluster_queries,
                "queries_rationale": f"Main query targets primary intent, {len(cluster_queries)} cluster queries explore related angles",
                "serp_sets": serp_sets,
                "derived_links": {
                    "intent_profile_ref": serp_sets[0]["dominant_intent"],
                    "required_subtopics_merged_ref": list(all_subtopics)[:10],
                    "data_confidence": "high"
                }
            }

        except Exception as e:
            logger.error(f"SERP research failed: {e}")
            return {
                "main_query": main_query,
                "cluster_queries": cluster_queries,
                "queries_rationale": "Error fetching SERP data",
                "serp_sets": [],
                "derived_links": {
                    "intent_profile_ref": "info_primary",
                    "required_subtopics_merged_ref": [],
                    "data_confidence": "low"
                }
            }
