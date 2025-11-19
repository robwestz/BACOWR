"""
Query Selector - Generates SERP queries for intent analysis.

Creates main query and cluster queries based on:
- Target page analysis
- Anchor text
- Entity and topic extraction

EXTENSIBILITY NOTE:
This module can be reused for:
- Keyword research tools
- Content gap analysis
- Competitive intelligence systems
- Query clustering for SEO analytics
"""

from dataclasses import dataclass
from typing import Dict, List, Set, Optional

from .target_profiler import TargetProfile
from .anchor_classifier import AnchorProfile
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QuerySet:
    """
    Set of queries for SERP research.

    Contains main query and cluster queries for comprehensive intent analysis.
    """
    main_query: str
    cluster_queries: List[str]
    rationale: str


class QuerySelector:
    """
    Selects and generates queries for SERP research.

    Creates a main query plus 2-4 cluster queries to understand
    the SERP landscape and user intent.
    """

    def __init__(self, min_cluster_queries: int = 2, max_cluster_queries: int = 4):
        """
        Initialize query selector.

        Args:
            min_cluster_queries: Minimum number of cluster queries (default: 2)
            max_cluster_queries: Maximum number of cluster queries (default: 4)
        """
        self.min_cluster_queries = min_cluster_queries
        self.max_cluster_queries = max_cluster_queries

    def select_queries(
        self,
        target_profile: TargetProfile,
        anchor_profile: AnchorProfile
    ) -> QuerySet:
        """
        Select main and cluster queries for SERP research.

        Args:
            target_profile: Analyzed target page
            anchor_profile: Classified anchor text

        Returns:
            QuerySet with main query and cluster queries

        EXTENSIBILITY NOTE:
        This logic can be enhanced with:
        - Query expansion using related terms APIs
        - Historical search volume data
        - Query clustering algorithms
        - Seasonal/trending query detection
        """
        logger.info("Selecting queries", target=target_profile.url[:50])

        # Generate main query
        main_query = self._generate_main_query(target_profile, anchor_profile)

        # Generate cluster queries
        cluster_queries = self._generate_cluster_queries(
            target_profile,
            anchor_profile,
            main_query
        )

        # Build rationale
        rationale = self._build_rationale(
            main_query,
            cluster_queries,
            target_profile,
            anchor_profile
        )

        query_set = QuerySet(
            main_query=main_query,
            cluster_queries=cluster_queries,
            rationale=rationale
        )

        logger.info(
            "Queries selected",
            main=main_query,
            clusters=len(cluster_queries)
        )

        return query_set

    def _generate_main_query(
        self,
        target: TargetProfile,
        anchor: AnchorProfile
    ) -> str:
        """
        Generate the main query based on target and anchor.

        Priority:
        1. Use target's candidate_main_queries if available
        2. Combine core entities + topics
        3. Fall back to cleaned title
        """
        # Use first candidate query if available
        if target.candidate_main_queries:
            return target.candidate_main_queries[0]

        # Combine top entity with top topic
        if target.core_entities and target.core_topics:
            entity = target.core_entities[0].lower()
            topic = target.core_topics[0].lower()
            return f"{entity} {topic}"

        # Use title without brand suffix
        title = target.title.lower()
        for separator in [" | ", " - ", " – "]:
            if separator in title:
                title = title.split(separator)[0].strip()

        return title[:100]  # Limit length

    def _generate_cluster_queries(
        self,
        target: TargetProfile,
        anchor: AnchorProfile,
        main_query: str
    ) -> List[str]:
        """
        Generate cluster queries to explore adjacent intent spaces.

        Strategies:
        1. Intent modifiers (best, how to, compare, etc.)
        2. Entity variations
        3. Related topics
        4. Question forms
        """
        cluster_queries: Set[str] = set()

        # Strategy 1: Intent modifiers based on anchor intent
        intent_modifiers = self._get_intent_modifiers(anchor.llm_intent_hint, target.detected_language)
        for modifier in intent_modifiers[:2]:
            cluster_queries.add(f"{modifier} {main_query}")

        # Strategy 2: Entity + topic combinations
        if len(target.core_entities) > 1 and len(target.core_topics) > 1:
            # Try alternative entity-topic pairs
            for i in range(1, min(3, len(target.core_entities))):
                if i < len(target.core_topics):
                    entity = target.core_entities[i].lower()
                    topic = target.core_topics[i].lower()
                    cluster_queries.add(f"{entity} {topic}")

        # Strategy 3: Add content-type specific queries
        if target.content_type:
            type_query = self._add_content_type_query(main_query, target.content_type, target.detected_language)
            if type_query:
                cluster_queries.add(type_query)

        # Strategy 4: Use alternative candidate queries
        if len(target.candidate_main_queries) > 1:
            for query in target.candidate_main_queries[1:3]:
                cluster_queries.add(query)

        # Convert to list and ensure we meet min/max requirements
        cluster_list = list(cluster_queries)

        # Remove main query if it accidentally got added
        cluster_list = [q for q in cluster_list if q != main_query]

        # Ensure minimum queries
        if len(cluster_list) < self.min_cluster_queries:
            # Add generic variations
            additional = self._generate_fallback_queries(main_query, target.detected_language)
            cluster_list.extend(additional)

        # Limit to max
        cluster_list = cluster_list[:self.max_cluster_queries]

        return cluster_list

    def _get_intent_modifiers(self, intent: str, language: str) -> List[str]:
        """
        Get query modifiers based on intent and language.

        Returns modifiers that match the intent type.
        """
        if language == "sv":
            modifiers = {
                "info_primary": ["vad är", "hur fungerar", "guide till"],
                "commercial_research": ["bästa", "jämför", "test av"],
                "transactional": ["köp", "pris", "erbjudande"],
                "navigational_brand": ["officiell", "webbplats"],
                "support": ["hjälp med", "problem med"],
                "mixed": ["guide", "tips"],
            }
        else:
            modifiers = {
                "info_primary": ["what is", "how does", "guide to"],
                "commercial_research": ["best", "compare", "review"],
                "transactional": ["buy", "price", "deal"],
                "navigational_brand": ["official", "website"],
                "support": ["help with", "problem with"],
                "mixed": ["guide", "tips"],
            }

        return modifiers.get(intent, modifiers.get("info_primary", []))

    def _add_content_type_query(self, main_query: str, content_type: str, language: str) -> Optional[str]:
        """
        Add a content-type specific query variant.

        E.g., if content_type is "comparison", add "vs" or "eller" query.
        """
        if language == "sv":
            type_modifiers = {
                "comparison": f"{main_query} alternativ",
                "guide": f"{main_query} guide",
                "product": f"{main_query} recension",
                "service": f"{main_query} erfarenheter",
                "tool": f"{main_query} verktyg",
            }
        else:
            type_modifiers = {
                "comparison": f"{main_query} alternatives",
                "guide": f"{main_query} guide",
                "product": f"{main_query} review",
                "service": f"{main_query} experiences",
                "tool": f"{main_query} tool",
            }

        return type_modifiers.get(content_type)

    def _generate_fallback_queries(self, main_query: str, language: str) -> List[str]:
        """
        Generate fallback queries if we don't have enough cluster queries.

        Uses simple transformations of the main query.
        """
        fallback = []

        if language == "sv":
            fallback.append(f"bästa {main_query}")
            fallback.append(f"{main_query} guide")
            fallback.append(f"{main_query} tips")
        else:
            fallback.append(f"best {main_query}")
            fallback.append(f"{main_query} guide")
            fallback.append(f"{main_query} tips")

        return fallback

    def _build_rationale(
        self,
        main_query: str,
        cluster_queries: List[str],
        target: TargetProfile,
        anchor: AnchorProfile
    ) -> str:
        """
        Build rationale explaining query selection.

        This provides transparency and helps with debugging.
        """
        parts = []

        parts.append(f"Main query '{main_query}' selected based on target page analysis.")

        if target.candidate_main_queries:
            parts.append(f"Used target's candidate query from title/content.")
        elif target.core_entities:
            parts.append(f"Combined core entity '{target.core_entities[0]}' with topic context.")

        parts.append(
            f"Cluster queries explore {anchor.llm_intent_hint} intent "
            f"and adjacent topic spaces."
        )

        if target.content_type:
            parts.append(f"Queries adapted for {target.content_type} content type.")

        return " ".join(parts)
