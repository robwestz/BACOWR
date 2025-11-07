"""
Ahrefs SERP Integration - Real SERP data from Ahrefs API

Ahrefs provides comprehensive SERP data including:
- Organic search results
- Position tracking
- SERP features
- Competitor analysis
"""

import os
import time
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime


class AhrefsSERP:
    """
    Ahrefs SERP API client.

    Ahrefs API docs: https://ahrefs.com/api/documentation
    """

    BASE_URL = "https://api.ahrefs.com/v3"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Ahrefs SERP client.

        Args:
            api_key: Ahrefs API key (or set AHREFS_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('AHREFS_API_KEY')

        if not self.api_key:
            raise ValueError("Ahrefs API key not provided. Set AHREFS_API_KEY environment variable.")

        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        })

    def get_serp(
        self,
        keyword: str,
        country: str = 'se',  # Sweden by default
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get SERP results for a keyword.

        Args:
            keyword: Search query
            country: Country code (se, us, uk, etc)
            limit: Number of results to return

        Returns:
            List of SERP results
        """
        try:
            # Ahrefs SERP Overview endpoint
            endpoint = f"{self.BASE_URL}/serp/overview"

            params = {
                'keyword': keyword,
                'country': country,
                'limit': limit
            }

            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            # Parse results
            results = []
            for item in data.get('organic', [])[:limit]:
                results.append({
                    'position': item.get('position', 0),
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'snippet': item.get('snippet', ''),
                    'domain': item.get('domain', ''),
                    'type': self._classify_result_type(item),
                    'traffic': item.get('traffic', 0),
                    'keywords': item.get('keywords', 0)
                })

            return results

        except requests.exceptions.RequestException as e:
            print(f"Ahrefs API error: {e}")
            raise

    def get_keyword_data(
        self,
        keyword: str,
        country: str = 'se'
    ) -> Dict[str, Any]:
        """
        Get keyword metrics and difficulty.

        Args:
            keyword: Search query
            country: Country code

        Returns:
            Keyword metrics
        """
        try:
            endpoint = f"{self.BASE_URL}/keywords/overview"

            params = {
                'keyword': keyword,
                'country': country
            }

            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            return {
                'keyword': keyword,
                'search_volume': data.get('search_volume', 0),
                'keyword_difficulty': data.get('difficulty', 0),
                'cpc': data.get('cpc', 0.0),
                'clicks': data.get('clicks', 0),
                'parent_topic': data.get('parent_topic', ''),
                'traffic_potential': data.get('traffic_potential', 0)
            }

        except requests.exceptions.RequestException as e:
            print(f"Ahrefs API error: {e}")
            return {
                'keyword': keyword,
                'search_volume': 0,
                'keyword_difficulty': 0
            }

    def get_related_keywords(
        self,
        keyword: str,
        country: str = 'se',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get related keywords suggestions.

        Args:
            keyword: Seed keyword
            country: Country code
            limit: Number of suggestions

        Returns:
            List of related keywords
        """
        try:
            endpoint = f"{self.BASE_URL}/keywords/related"

            params = {
                'keyword': keyword,
                'country': country,
                'limit': limit
            }

            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            related = []
            for item in data.get('keywords', [])[:limit]:
                related.append({
                    'keyword': item.get('keyword', ''),
                    'search_volume': item.get('search_volume', 0),
                    'difficulty': item.get('difficulty', 0)
                })

            return related

        except requests.exceptions.RequestException as e:
            print(f"Ahrefs API error: {e}")
            return []

    def _classify_result_type(self, result: Dict[str, Any]) -> str:
        """
        Classify SERP result type based on URL and content.

        Args:
            result: SERP result from Ahrefs

        Returns:
            Result type: 'commercial', 'review', 'informational', 'local'
        """
        url = result.get('url', '').lower()
        title = result.get('title', '').lower()

        # Commercial signals
        if any(word in url or word in title for word in [
            'buy', 'shop', 'price', 'deal', 'sale', 'köp', 'pris'
        ]):
            return 'commercial'

        # Review signals
        if any(word in url or word in title for word in [
            'review', 'test', 'comparison', 'vs', 'recension', 'jämförelse'
        ]):
            return 'review'

        # Local signals
        if any(word in url for word in ['maps.google', 'yelp', 'tripadvisor']):
            return 'local'

        # Default to informational
        return 'informational'


class AhrefsEnhancedResearcher:
    """
    Enhanced SERP Researcher using Ahrefs data.

    Combines Ahrefs real data with local analysis for optimal results.
    """

    def __init__(
        self,
        ahrefs_client: Optional[AhrefsSERP] = None,
        fallback_to_mock: bool = True
    ):
        """
        Initialize enhanced researcher.

        Args:
            ahrefs_client: Ahrefs client instance
            fallback_to_mock: Use mock data if Ahrefs fails
        """
        self.ahrefs = ahrefs_client or self._init_ahrefs()
        self.fallback_to_mock = fallback_to_mock

    def _init_ahrefs(self) -> Optional[AhrefsSERP]:
        """Initialize Ahrefs client if API key available"""
        try:
            return AhrefsSERP()
        except ValueError:
            print("Warning: Ahrefs API key not found. Will use mock data.")
            return None

    def research(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str,
        country: str = 'se'
    ) -> Dict[str, Any]:
        """
        Perform comprehensive SERP research using Ahrefs.

        Args:
            target_profile: Target page profile
            anchor_text: Anchor text
            country: Country code for SERP

        Returns:
            Complete serp_research_extension
        """
        # Generate queries from target profile
        main_query, cluster_queries = self._generate_queries(target_profile, anchor_text)

        serp_sets = []

        # Fetch main query SERP
        try:
            if self.ahrefs:
                main_results = self.ahrefs.get_serp(main_query, country=country, limit=10)
                main_keyword_data = self.ahrefs.get_keyword_data(main_query, country=country)

                main_serp_set = {
                    'query': main_query,
                    'query_type': 'main',
                    'intent_primary': self._classify_intent(main_results),
                    'intent_secondary': [],
                    'results_count': len(main_results),
                    'top_results': main_results[:3],
                    'subtopics': self._extract_subtopics(main_results),
                    'keyword_metrics': main_keyword_data,
                    'fetched_at': datetime.utcnow().isoformat(),
                    'data_source': 'ahrefs'
                }

                serp_sets.append(main_serp_set)

            else:
                # Fallback to mock
                if self.fallback_to_mock:
                    main_serp_set = self._mock_serp_set(main_query, 'main')
                    serp_sets.append(main_serp_set)

        except Exception as e:
            print(f"Error fetching main query SERP: {e}")
            if self.fallback_to_mock:
                serp_sets.append(self._mock_serp_set(main_query, 'main'))

        # Fetch cluster queries
        for cluster_query in cluster_queries[:3]:
            try:
                if self.ahrefs:
                    cluster_results = self.ahrefs.get_serp(cluster_query, country=country, limit=10)

                    cluster_serp_set = {
                        'query': cluster_query,
                        'query_type': 'cluster',
                        'intent_primary': self._classify_intent(cluster_results),
                        'intent_secondary': [],
                        'results_count': len(cluster_results),
                        'top_results': cluster_results[:3],
                        'subtopics': self._extract_subtopics(cluster_results),
                        'fetched_at': datetime.utcnow().isoformat(),
                        'data_source': 'ahrefs'
                    }

                    serp_sets.append(cluster_serp_set)

                else:
                    if self.fallback_to_mock:
                        serp_sets.append(self._mock_serp_set(cluster_query, 'cluster'))

            except Exception as e:
                print(f"Error fetching cluster query '{cluster_query}': {e}")
                if self.fallback_to_mock:
                    serp_sets.append(self._mock_serp_set(cluster_query, 'cluster'))

        # Build complete research extension
        return {
            'main_query': main_query,
            'cluster_queries': cluster_queries,
            'queries_rationale': self._generate_rationale(target_profile),
            'serp_sets': serp_sets,
            'serp_intent_primary': serp_sets[0]['intent_primary'] if serp_sets else 'info_primary',
            'serp_intent_secondary': [],
            'data_confidence': 'high' if self.ahrefs else 'medium'
        }

    def _generate_queries(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str
    ) -> tuple:
        """Generate main and cluster queries"""

        entities = target_profile.get('core_entities', [])
        topics = target_profile.get('core_topics', [])

        # Main query from entities and topics
        if entities and topics:
            main_query = f"{entities[0]} {topics[0]}".lower()
        elif entities:
            main_query = entities[0].lower()
        else:
            main_query = anchor_text.lower()

        # Cluster queries with commercial modifiers
        cluster_queries = []
        if entities:
            entity = entities[0]
            modifiers = ['jämförelse', 'test', 'recension', 'guide', 'erfarenheter']
            for modifier in modifiers[:3]:
                cluster_queries.append(f"{entity} {modifier}".lower())

        return main_query, cluster_queries

    def _classify_intent(self, results: List[Dict[str, Any]]) -> str:
        """Classify overall SERP intent"""

        intent_scores = {
            'commercial': 0,
            'review': 0,
            'informational': 0,
            'local': 0
        }

        for result in results[:5]:  # Top 5 matter most
            result_type = result.get('type', 'informational')
            intent_scores[result_type] = intent_scores.get(result_type, 0) + 1

        # Map to our intent taxonomy
        max_type = max(intent_scores, key=intent_scores.get)

        if max_type in ['commercial', 'local']:
            return 'transactional'
        elif max_type == 'review':
            return 'commercial_research'
        else:
            return 'info_primary'

    def _extract_subtopics(self, results: List[Dict[str, Any]]) -> List[str]:
        """Extract common subtopics from SERP results"""

        subtopics = set()

        # Extract from titles
        for result in results[:10]:
            title = result.get('title', '').lower()

            # Common subtopic patterns
            if 'pris' in title or 'price' in title:
                subtopics.add('pricing')
            if 'test' in title or 'review' in title:
                subtopics.add('reviews')
            if 'jämför' in title or 'compar' in title:
                subtopics.add('comparison')
            if 'guide' in title:
                subtopics.add('guide')
            if 'fördelar' in title or 'benefit' in title:
                subtopics.add('benefits')
            if 'nackdelar' in title or 'drawback' in title:
                subtopics.add('drawbacks')

        return list(subtopics)[:5]

    def _generate_rationale(self, target_profile: Dict[str, Any]) -> str:
        """Generate rationale for query selection"""

        entities = target_profile.get('core_entities', [])
        topics = target_profile.get('core_topics', [])

        return f"Queries derived from target entities ({', '.join(entities[:2])}) and topics ({', '.join(topics[:2])}). Cluster queries explore commercial research intent variations."

    def _mock_serp_set(self, query: str, query_type: str) -> Dict[str, Any]:
        """Generate mock SERP set for fallback"""

        return {
            'query': query,
            'query_type': query_type,
            'intent_primary': 'commercial_research',
            'intent_secondary': ['info_primary'],
            'results_count': 10,
            'top_results': [
                {
                    'position': i + 1,
                    'title': f"Result {i+1}: {query.title()}",
                    'url': f"https://example{i+1}.com/{query.replace(' ', '-')}",
                    'snippet': f"Information about {query}",
                    'domain': f"example{i+1}.com",
                    'type': 'informational'
                }
                for i in range(3)
            ],
            'subtopics': ['comparison', 'reviews', 'guide'],
            'fetched_at': datetime.utcnow().isoformat(),
            'data_source': 'mock'
        }
