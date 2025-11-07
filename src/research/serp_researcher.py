"""
SERP Researcher - Fetch and analyze search engine results

Part of Del 3B: Content Generation Pipeline
Generates queries and analyzes SERP to inform content strategy
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class SERPResearcher:
    """
    SERP Researcher for analyzing search intent and top results.

    Supports:
    - Query generation from target_profile
    - SERP fetching (mock mode and API mode)
    - Intent classification
    - Subtopic extraction
    """

    # Intent patterns for classification
    INTENT_PATTERNS = {
        'transactional': [
            'buy', 'köp', 'purchase', 'beställ', 'order', 'shop',
            'pris', 'price', 'erbjudande', 'deal', 'rabatt', 'discount'
        ],
        'commercial_research': [
            'jämför', 'compare', 'test', 'recension', 'review',
            'bäst', 'best', 'vs', 'alternativ', 'alternative',
            'guide', 'tips', 'råd', 'advice'
        ],
        'info_primary': [
            'vad är', 'what is', 'hur', 'how', 'varför', 'why',
            'guide', 'tutorial', 'förklaring', 'explanation',
            'information', 'fakta', 'facts'
        ],
        'navigational_brand': [
            'login', 'logga in', 'account', 'konto',
            'official', 'officiell', 'hemsida', 'website'
        ]
    }

    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = True):
        """
        Initialize SERP Researcher.

        Args:
            api_key: API key for SERP service (e.g., Google Custom Search)
            mock_mode: Use mock data instead of real API calls
        """
        self.api_key = api_key
        self.mock_mode = mock_mode

    def generate_queries(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str,
        max_cluster_queries: int = 3
    ) -> Tuple[str, List[str], str]:
        """
        Generate main and cluster queries from target profile.

        Args:
            target_profile: Target page profile
            anchor_text: Anchor text
            max_cluster_queries: Maximum number of cluster queries

        Returns:
            (main_query, cluster_queries, rationale)
        """
        # Extract key elements
        entities = target_profile.get('core_entities', [])
        topics = target_profile.get('core_topics', [])
        title = target_profile.get('title', '')
        candidate_queries = target_profile.get('candidate_main_queries', [])

        # Generate main query
        main_query = self._generate_main_query(entities, topics, title, candidate_queries)

        # Generate cluster queries
        cluster_queries = self._generate_cluster_queries(
            entities, topics, anchor_text, max_cluster_queries
        )

        # Generate rationale
        rationale = (
            f"Main query derived from target entities ({', '.join(entities[:2])}) "
            f"and topics ({', '.join(topics[:2])}). "
            f"Cluster queries explore related aspects and user intent variations."
        )

        return main_query, cluster_queries, rationale

    def _generate_main_query(
        self,
        entities: List[str],
        topics: List[str],
        title: str,
        candidate_queries: List[str]
    ) -> str:
        """
        Generate main search query.

        Args:
            entities: Core entities
            topics: Core topics
            title: Page title
            candidate_queries: Pre-generated candidate queries

        Returns:
            Main query string
        """
        # Use first candidate query if available and good
        if candidate_queries and len(candidate_queries[0]) > 5:
            return candidate_queries[0]

        # Otherwise construct from entities and topics
        if entities and topics:
            return f"{entities[0]} {topics[0]}".lower()
        elif entities:
            return entities[0].lower()
        elif title:
            # Extract first meaningful phrase from title
            words = title.split()[:4]
            return ' '.join(words).lower()
        else:
            return "relevant information"

    def _generate_cluster_queries(
        self,
        entities: List[str],
        topics: List[str],
        anchor_text: str,
        max_queries: int
    ) -> List[str]:
        """
        Generate cluster queries exploring related angles.

        Args:
            entities: Core entities
            topics: Core topics
            anchor_text: Anchor text
            max_queries: Maximum number of queries

        Returns:
            List of cluster queries
        """
        queries = []

        # Add entity + commercial modifier variations
        if entities:
            entity = entities[0]
            modifiers = ['jämförelse', 'recension', 'test', 'guide', 'erfarenheter']
            for modifier in modifiers:
                if len(queries) >= max_queries:
                    break
                queries.append(f"{entity} {modifier}".lower())

        # Add topic variations
        if topics and len(queries) < max_queries:
            for topic in topics[:2]:
                if len(queries) >= max_queries:
                    break
                queries.append(f"{topic}".lower())

        # Ensure we have at least one cluster query
        if not queries and entities:
            queries.append(f"{entities[0]}".lower())

        return queries[:max_queries]

    def fetch_serp(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch SERP results for a query.

        Args:
            query: Search query
            num_results: Number of results to fetch

        Returns:
            List of SERP result dicts
        """
        if self.mock_mode:
            return self._mock_serp_results(query, num_results)
        else:
            # Real API implementation would go here
            raise NotImplementedError("Real SERP API not yet implemented. Use mock_mode=True.")

    def _mock_serp_results(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """
        Generate mock SERP results for testing.

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of mock SERP results
        """
        results = []

        # Determine intent from query
        intent = self._classify_query_intent(query)

        # Generate mock results based on intent
        for i in range(num_results):
            result = {
                'position': i + 1,
                'title': f"Result {i+1}: {query.title()} - Information",
                'url': f"https://example{i+1}.com/{query.replace(' ', '-')}",
                'snippet': f"This page provides detailed information about {query}. "
                          f"Learn more about the key aspects and considerations.",
                'domain': f"example{i+1}.com",
                'type': self._infer_result_type(i, intent)
            }
            results.append(result)

        return results

    def _classify_query_intent(self, query: str) -> str:
        """
        Classify search intent from query.

        Args:
            query: Search query

        Returns:
            Intent classification
        """
        query_lower = query.lower()

        # Count matches for each intent
        scores = {}
        for intent, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in query_lower)
            scores[intent] = score

        # Return intent with highest score
        if max(scores.values()) > 0:
            return max(scores, key=scores.get)
        else:
            return 'info_primary'  # Default

    def _infer_result_type(self, position: int, intent: str) -> str:
        """
        Infer result type based on position and intent.

        Args:
            position: Result position (0-indexed)
            intent: Query intent

        Returns:
            Result type
        """
        if intent == 'transactional':
            if position < 3:
                return 'commercial'
            else:
                return 'informational'
        elif intent == 'commercial_research':
            if position < 5:
                return 'review'
            else:
                return 'informational'
        else:
            return 'informational'

    def classify_serp_intent(
        self,
        serp_results: List[Dict[str, Any]]
    ) -> Tuple[str, List[str]]:
        """
        Classify primary and secondary intent from SERP results.

        Args:
            serp_results: List of SERP results

        Returns:
            (primary_intent, secondary_intents)
        """
        # Analyze result types and titles
        intent_scores = {
            'transactional': 0,
            'commercial_research': 0,
            'info_primary': 0,
            'navigational_brand': 0
        }

        for result in serp_results[:10]:  # Top 10
            title = result.get('title', '').lower()
            snippet = result.get('snippet', '').lower()
            result_type = result.get('type', 'informational')

            # Boost based on result type
            if result_type == 'commercial':
                intent_scores['transactional'] += 2
            elif result_type == 'review':
                intent_scores['commercial_research'] += 2

            # Analyze text
            text = f"{title} {snippet}"
            for intent, patterns in self.INTENT_PATTERNS.items():
                matches = sum(1 for pattern in patterns if pattern in text)
                intent_scores[intent] += matches

        # Determine primary intent
        primary = max(intent_scores, key=intent_scores.get)

        # Determine secondary intents (those with >30% of primary score)
        threshold = intent_scores[primary] * 0.3
        secondary = [
            intent for intent, score in intent_scores.items()
            if score >= threshold and intent != primary
        ]

        return primary, secondary

    def extract_subtopics(
        self,
        serp_results: List[Dict[str, Any]],
        max_subtopics: int = 5
    ) -> List[str]:
        """
        Extract common subtopics from SERP results.

        Args:
            serp_results: List of SERP results
            max_subtopics: Maximum number of subtopics

        Returns:
            List of subtopics
        """
        # Collect all titles and snippets
        text_corpus = []
        for result in serp_results[:10]:
            text_corpus.append(result.get('title', ''))
            text_corpus.append(result.get('snippet', ''))

        # Extract common phrases
        all_text = ' '.join(text_corpus).lower()

        # Look for common multi-word phrases
        subtopics = set()

        # Extract capitalized phrases (likely topics)
        patterns = [
            r'\b([A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)*)\b',  # Capitalized phrases
            r'\b(fördelar|nackdelar|benefits|drawbacks)\b',  # Common subtopics
            r'\b(pris|price|cost|kostnad)\b',
            r'\b(kvalitet|quality)\b',
            r'\b(jämförelse|comparison)\b',
            r'\b(guide|tips|råd|advice)\b'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            subtopics.update(matches[:2])  # Top 2 from each pattern

        # Convert to list and limit
        return list(subtopics)[:max_subtopics]

    def research(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str,
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Perform complete SERP research.

        Args:
            target_profile: Target page profile
            anchor_text: Anchor text
            num_results: Number of SERP results per query

        Returns:
            serp_research_extension dict
        """
        # Generate queries
        main_query, cluster_queries, rationale = self.generate_queries(
            target_profile, anchor_text
        )

        # Fetch SERP results
        serp_sets = []

        # Main query
        main_results = self.fetch_serp(main_query, num_results)
        main_intent_primary, main_intent_secondary = self.classify_serp_intent(main_results)
        main_subtopics = self.extract_subtopics(main_results)

        serp_sets.append({
            'query': main_query,
            'query_type': 'main',
            'intent_primary': main_intent_primary,
            'intent_secondary': main_intent_secondary,
            'results_count': len(main_results),
            'top_results': main_results[:3],  # Store top 3
            'subtopics': main_subtopics,
            'fetched_at': datetime.utcnow().isoformat()
        })

        # Cluster queries
        for cluster_query in cluster_queries:
            cluster_results = self.fetch_serp(cluster_query, num_results)
            cluster_intent_primary, cluster_intent_secondary = self.classify_serp_intent(cluster_results)
            cluster_subtopics = self.extract_subtopics(cluster_results)

            serp_sets.append({
                'query': cluster_query,
                'query_type': 'cluster',
                'intent_primary': cluster_intent_primary,
                'intent_secondary': cluster_intent_secondary,
                'results_count': len(cluster_results),
                'top_results': cluster_results[:3],
                'subtopics': cluster_subtopics,
                'fetched_at': datetime.utcnow().isoformat()
            })

        # Aggregate intent (use main query intent as primary)
        serp_intent_primary = main_intent_primary

        # Determine data confidence
        data_confidence = 'high' if not self.mock_mode else 'medium'

        return {
            'main_query': main_query,
            'cluster_queries': cluster_queries,
            'queries_rationale': rationale,
            'serp_sets': serp_sets,
            'serp_intent_primary': serp_intent_primary,
            'serp_intent_secondary': main_intent_secondary,
            'data_confidence': data_confidence
        }
