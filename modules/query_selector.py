"""
QuerySelector Module

Selects main query + 2-4 cluster queries based on target and anchor profiles.
"""

from typing import Dict, Any, List
from .base import BaseModule


class QuerySelector(BaseModule):
    """
    Selects queries for SERP research.

    Input:
        - target_profile: Dict
        - anchor_profile: Dict

    Output:
        - main_query: str
        - cluster_queries: List[str]
        - queries_rationale: str
    """

    def run(self, target_profile: Dict[str, Any], anchor_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Select main and cluster queries

        Args:
            target_profile: From TargetScraperAndProfiler
            anchor_profile: From AnchorClassifier

        Returns:
            Dict with main_query, cluster_queries, queries_rationale
        """
        self.log_step("Selecting queries for SERP research")

        # Select main query
        main_query = self._select_main_query(target_profile, anchor_profile)

        # Generate cluster queries
        cluster_queries = self._generate_cluster_queries(target_profile, anchor_profile, main_query)

        # Rationale
        rationale = self._build_rationale(target_profile, anchor_profile, main_query, cluster_queries)

        result = {
            "main_query": main_query,
            "cluster_queries": cluster_queries,
            "queries_rationale": rationale
        }

        self.log_step(f"Queries selected: main='{main_query}', clusters={len(cluster_queries)}")
        return result

    def _select_main_query(self, target_profile: Dict[str, Any], anchor_profile: Dict[str, Any]) -> str:
        """
        Select main query

        Priority:
        1. If anchor is exact/partial, use anchor text
        2. Use first candidate_main_query from target
        3. Combine core_entities
        """
        anchor_text = anchor_profile.get('proposed_text', '')
        anchor_type = anchor_profile.get('llm_classified_type', '')

        # If anchor is exact or partial, consider it
        if anchor_type in ['exact', 'partial']:
            return anchor_text.lower()

        # Use candidate queries from target
        candidates = target_profile.get('candidate_main_queries', [])
        if candidates:
            return candidates[0]

        # Fallback: combine entities
        entities = target_profile.get('core_entities', [])
        if len(entities) >= 2:
            return f"{entities[0]} {entities[1]}".lower()
        elif len(entities) == 1:
            return entities[0].lower()
        else:
            # Last resort: use title
            return target_profile.get('title', 'unknown').lower()

    def _generate_cluster_queries(
        self,
        target_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        main_query: str
    ) -> List[str]:
        """
        Generate 2-4 cluster queries

        Strategy:
        - Cluster 1: Broader context (category/general)
        - Cluster 2: Deeper detail (how it works, conditions, etc.)
        - Cluster 3 (optional): Related/comparative
        """
        clusters = []

        entities = target_profile.get('core_entities', [])
        topics = target_profile.get('core_topics', [])

        # Cluster 1: Broader category
        if len(entities) > 0:
            broader = f"{entities[0]} guide".lower()
            if broader != main_query:
                clusters.append(broader)

        # Cluster 2: How it works / details
        if len(topics) > 0:
            detail = f"{main_query} hur fungerar det"
            clusters.append(detail)

        # Cluster 3: Comparative/alternative
        if len(entities) >= 2:
            comparative = f"{entities[0]} jämförelse"
            if comparative not in clusters and comparative != main_query:
                clusters.append(comparative)

        # Ensure 2-4 clusters
        if len(clusters) < 2:
            # Add generic variations
            clusters.append(f"{main_query} test")

        return clusters[:4]

    def _build_rationale(
        self,
        target_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        main_query: str,
        cluster_queries: List[str]
    ) -> str:
        """Build rationale for query selection"""
        anchor_type = anchor_profile.get('llm_classified_type', 'unknown')
        entities = target_profile.get('core_entities', [])

        rationale = (
            f"Main query '{main_query}' selected based on "
            f"anchor type ({anchor_type}) and target entities ({', '.join(entities[:2])}). "
            f"Cluster queries explore broader context, detailed aspects, and comparative angles."
        )

        return rationale
