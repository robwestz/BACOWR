"""
SERP API Integration Service - BACOWR Demo Environment

Real SERP data integration using SerpAPI for search engine results analysis.
Provides query generation, SERP fetching, and intent classification.

Part of the BACOWR Demo API - Production-ready SERP research service.
"""

import os
import time
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class SerpAPIIntegration:
    """
    SERP API Integration using SerpAPI service.

    Features:
    - Real SERP data from Google, Bing, and other search engines
    - Query generation from target profiles
    - Intent classification (transactional, commercial, informational, navigational)
    - Subtopic extraction from SERP results
    - Supports multiple countries/regions
    - Automatic fallback to mock data if API unavailable

    SerpAPI Documentation: https://serpapi.com/search-api
    """

    # Intent classification patterns
    INTENT_PATTERNS = {
        'transactional': [
            'buy', 'köp', 'purchase', 'beställ', 'order', 'shop',
            'pris', 'price', 'erbjudande', 'deal', 'rabatt', 'discount',
            'billig', 'cheap', 'gratis', 'free'
        ],
        'commercial_research': [
            'jämför', 'compare', 'test', 'recension', 'review',
            'bäst', 'best', 'vs', 'alternativ', 'alternative',
            'guide', 'tips', 'råd', 'advice', 'top'
        ],
        'info_primary': [
            'vad är', 'what is', 'hur', 'how', 'varför', 'why',
            'guide', 'tutorial', 'förklaring', 'explanation',
            'information', 'fakta', 'facts', 'om', 'about'
        ],
        'navigational_brand': [
            'login', 'logga in', 'account', 'konto',
            'official', 'officiell', 'hemsida', 'website',
            'kontakt', 'contact'
        ]
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_api: bool = True,
        fallback_to_mock: bool = True
    ):
        """
        Initialize SERP API Integration.

        Args:
            api_key: SerpAPI key (or set SERPAPI_API_KEY env var)
            enable_api: Enable real API calls (vs. mock mode)
            fallback_to_mock: Use mock data if API fails
        """
        self.api_key = api_key or os.getenv('SERPAPI_API_KEY')
        self.enable_api = enable_api and self.api_key is not None
        self.fallback_to_mock = fallback_to_mock

        # Initialize API client if available
        if self.enable_api:
            try:
                # SerpAPI doesn't require explicit client initialization
                # We'll use requests directly
                import requests
                self.session = requests.Session()
            except ImportError:
                print("Warning: requests package not installed, using mock mode")
                self.enable_api = False

    def fetch_serp_data(
        self,
        query: str,
        country: str = 'se',
        num_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch SERP results for a query using SerpAPI.

        Args:
            query: Search query
            country: Country code (se, us, uk, de, etc.)
            num_results: Number of results to fetch

        Returns:
            List of SERP result dictionaries with:
            - position: int
            - title: str
            - url: str
            - snippet: str
            - domain: str
            - type: str (commercial, review, informational, local)
        """
        if self.enable_api:
            try:
                return self._fetch_from_serpapi(query, country, num_results)
            except Exception as e:
                print(f"SerpAPI fetch failed: {e}")
                if self.fallback_to_mock:
                    print("Falling back to mock SERP data")
                    return self._generate_mock_serp(query, num_results)
                raise
        else:
            return self._generate_mock_serp(query, num_results)

    def _fetch_from_serpapi(
        self,
        query: str,
        country: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch real SERP data from SerpAPI.

        Args:
            query: Search query
            country: Country code
            num_results: Number of results

        Returns:
            List of SERP results
        """
        import requests

        # SerpAPI endpoint
        url = "https://serpapi.com/search"

        # Map country codes to Google domain
        google_domains = {
            'se': 'google.se',
            'us': 'google.com',
            'uk': 'google.co.uk',
            'de': 'google.de',
            'no': 'google.no',
            'dk': 'google.dk',
            'fi': 'google.fi'
        }

        params = {
            'q': query,
            'google_domain': google_domains.get(country, 'google.se'),
            'gl': country,
            'hl': 'sv' if country == 'se' else 'en',
            'num': num_results,
            'api_key': self.api_key
        }

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        # Parse organic results
        results = []
        organic_results = data.get('organic_results', [])

        for idx, result in enumerate(organic_results[:num_results]):
            parsed_result = {
                'position': result.get('position', idx + 1),
                'title': result.get('title', ''),
                'url': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'domain': self._extract_domain(result.get('link', '')),
                'type': self._classify_result_type(result),
                'displayed_link': result.get('displayed_link', ''),
                'cached_page': result.get('cached_page_link', '')
            }
            results.append(parsed_result)

        return results

    def _generate_mock_serp(
        self,
        query: str,
        num_results: int
    ) -> List[Dict[str, Any]]:
        """
        Generate mock SERP results for testing/fallback.

        Args:
            query: Search query
            num_results: Number of results to generate

        Returns:
            List of mock SERP results
        """
        results = []
        intent = self._classify_query_intent_from_text(query)

        for i in range(num_results):
            result_type = self._infer_mock_result_type(i, intent)

            result = {
                'position': i + 1,
                'title': f"{query.title()} - {'Guide' if i % 3 == 0 else 'Information'}",
                'url': f"https://example{i+1}.com/{query.replace(' ', '-').lower()}",
                'snippet': f"Comprehensive information about {query}. Learn about key aspects, "
                          f"benefits, and considerations for {query}.",
                'domain': f"example{i+1}.com",
                'type': result_type,
                'displayed_link': f"example{i+1}.com › {query.replace(' ', '-').lower()}",
                'cached_page': None
            }
            results.append(result)

        return results

    def analyze_serp_results(
        self,
        serp_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze SERP results to extract insights.

        Args:
            serp_data: List of SERP results

        Returns:
            Analysis containing:
            - intent_primary: str
            - intent_secondary: List[str]
            - subtopics: List[str]
            - result_types_distribution: Dict[str, int]
            - top_domains: List[str]
        """
        # Classify intent
        intent_primary, intent_secondary = self._classify_serp_intent(serp_data)

        # Extract subtopics
        subtopics = self._extract_subtopics_from_serp(serp_data)

        # Analyze result types
        result_types = {}
        for result in serp_data:
            result_type = result.get('type', 'informational')
            result_types[result_type] = result_types.get(result_type, 0) + 1

        # Top domains
        top_domains = [result.get('domain', '') for result in serp_data[:5]]

        return {
            'intent_primary': intent_primary,
            'intent_secondary': intent_secondary,
            'subtopics': subtopics,
            'result_types_distribution': result_types,
            'top_domains': top_domains,
            'results_count': len(serp_data)
        }

    def build_serp_research_extension(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str,
        country: str = 'se',
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Build complete SERP research extension for job package.

        This is the main method that orchestrates:
        1. Query generation
        2. SERP data fetching
        3. Intent analysis
        4. Subtopic extraction

        Args:
            target_profile: Target page profile
            anchor_text: Anchor text
            country: Country code for SERP
            num_results: Number of results per query

        Returns:
            Complete serp_research_extension dict
        """
        # Generate queries
        main_query, cluster_queries, rationale = self._generate_queries(
            target_profile,
            anchor_text
        )

        serp_sets = []

        # Fetch main query SERP
        try:
            main_results = self.fetch_serp_data(main_query, country, num_results)
            main_analysis = self.analyze_serp_results(main_results)

            serp_sets.append({
                'query': main_query,
                'query_type': 'main',
                'intent_primary': main_analysis['intent_primary'],
                'intent_secondary': main_analysis['intent_secondary'],
                'results_count': len(main_results),
                'top_results': main_results[:3],
                'subtopics': main_analysis['subtopics'],
                'result_types': main_analysis['result_types_distribution'],
                'fetched_at': datetime.utcnow().isoformat(),
                'data_source': 'serpapi' if self.enable_api else 'mock'
            })
        except Exception as e:
            print(f"Error fetching main query: {e}")

        # Fetch cluster queries
        for cluster_query in cluster_queries[:3]:
            try:
                cluster_results = self.fetch_serp_data(cluster_query, country, num_results)
                cluster_analysis = self.analyze_serp_results(cluster_results)

                serp_sets.append({
                    'query': cluster_query,
                    'query_type': 'cluster',
                    'intent_primary': cluster_analysis['intent_primary'],
                    'intent_secondary': cluster_analysis['intent_secondary'],
                    'results_count': len(cluster_results),
                    'top_results': cluster_results[:3],
                    'subtopics': cluster_analysis['subtopics'],
                    'result_types': cluster_analysis['result_types_distribution'],
                    'fetched_at': datetime.utcnow().isoformat(),
                    'data_source': 'serpapi' if self.enable_api else 'mock'
                })
            except Exception as e:
                print(f"Error fetching cluster query '{cluster_query}': {e}")

        # Determine overall intent (from main query)
        serp_intent_primary = serp_sets[0]['intent_primary'] if serp_sets else 'info_primary'
        serp_intent_secondary = serp_sets[0]['intent_secondary'] if serp_sets else []

        return {
            'main_query': main_query,
            'cluster_queries': cluster_queries,
            'queries_rationale': rationale,
            'serp_sets': serp_sets,
            'serp_intent_primary': serp_intent_primary,
            'serp_intent_secondary': serp_intent_secondary,
            'data_confidence': 'high' if self.enable_api else 'medium'
        }

    def _generate_queries(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str
    ) -> Tuple[str, List[str], str]:
        """
        Generate main and cluster queries from target profile.

        Args:
            target_profile: Target page profile
            anchor_text: Anchor text

        Returns:
            (main_query, cluster_queries, rationale)
        """
        entities = target_profile.get('core_entities', [])
        topics = target_profile.get('core_topics', [])
        title = target_profile.get('title', '')

        # Generate main query
        if entities and topics:
            main_query = f"{entities[0]} {topics[0]}".lower()
        elif entities:
            main_query = entities[0].lower()
        elif topics:
            main_query = topics[0].lower()
        else:
            # Extract from title
            words = title.split()[:3]
            main_query = ' '.join(words).lower()

        # Generate cluster queries with commercial modifiers
        cluster_queries = []
        if entities:
            entity = entities[0]
            modifiers = ['jämförelse', 'test', 'recension', 'guide', 'erfarenheter']
            for modifier in modifiers[:3]:
                cluster_queries.append(f"{entity} {modifier}".lower())

        # Rationale
        rationale = (
            f"Main query derived from target entities ({', '.join(entities[:2])}) "
            f"and topics ({', '.join(topics[:2])}). "
            f"Cluster queries explore commercial research intent variations."
        )

        return main_query, cluster_queries, rationale

    def _classify_query_intent_from_text(self, query: str) -> str:
        """Classify search intent from query text"""
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
            return 'info_primary'

    def _classify_serp_intent(
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
        intent_scores = {
            'transactional': 0,
            'commercial_research': 0,
            'info_primary': 0,
            'navigational_brand': 0
        }

        for result in serp_results[:10]:
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

        # Secondary intents (>30% of primary score)
        threshold = intent_scores[primary] * 0.3
        secondary = [
            intent for intent, score in intent_scores.items()
            if score >= threshold and intent != primary
        ]

        return primary, secondary

    def _extract_subtopics_from_serp(
        self,
        serp_results: List[Dict[str, Any]],
        max_subtopics: int = 8
    ) -> List[str]:
        """
        Extract common subtopics from SERP results.

        Args:
            serp_results: List of SERP results
            max_subtopics: Maximum subtopics to return

        Returns:
            List of subtopic strings
        """
        subtopics = set()

        # Collect text
        all_text = ' '.join([
            f"{r.get('title', '')} {r.get('snippet', '')}"
            for r in serp_results[:10]
        ]).lower()

        # Common subtopic keywords
        subtopic_keywords = {
            'pricing': ['pris', 'price', 'cost', 'kostnad'],
            'reviews': ['recension', 'review', 'test', 'betyg', 'rating'],
            'comparison': ['jämför', 'compar', 'vs', 'versus'],
            'guide': ['guide', 'tutorial', 'tips', 'råd'],
            'benefits': ['fördelar', 'benefit', 'advantage', 'pros'],
            'drawbacks': ['nackdelar', 'drawback', 'disadvantage', 'cons'],
            'features': ['funktioner', 'feature', 'egenskaper'],
            'quality': ['kvalitet', 'quality']
        }

        for subtopic, keywords in subtopic_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                subtopics.add(subtopic)

        return list(subtopics)[:max_subtopics]

    def _classify_result_type(self, result: Dict[str, Any]) -> str:
        """
        Classify SERP result type.

        Args:
            result: SERP result dict

        Returns:
            Result type: 'commercial', 'review', 'informational', 'local'
        """
        url = result.get('link', '').lower()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()

        combined_text = f"{url} {title} {snippet}"

        # Commercial signals
        if any(word in combined_text for word in [
            'buy', 'shop', 'price', 'deal', 'sale', 'köp', 'pris', 'beställ'
        ]):
            return 'commercial'

        # Review signals
        if any(word in combined_text for word in [
            'review', 'test', 'comparison', 'vs', 'recension', 'jämförelse'
        ]):
            return 'review'

        # Local signals
        if any(word in url for word in ['maps.google', 'yelp', 'tripadvisor']):
            return 'local'

        return 'informational'

    def _infer_mock_result_type(self, position: int, intent: str) -> str:
        """Infer result type for mock data based on position and intent"""
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

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc.replace('www.', '')
        except:
            return url.split('/')[2] if len(url.split('/')) > 2 else url
