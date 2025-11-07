"""
SerpAnalyzer Module

Analyzes SERP results to extract intent, page types, entities, and subtopics.
NOTE: Simplified implementation. In production, fetch actual pages and use LLM for deep analysis.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List
from collections import Counter

from .base import BaseModule


class SerpAnalyzer(BaseModule):
    """
    Analyzes SERP results.

    Input:
        - serp_fetcher_output: From SerpFetcher
        - query_selection: From QuerySelector (for context)

    Output:
        - serp_research_extension: Dict (according to schema)
    """

    def run(
        self,
        serp_fetcher_output: Dict[str, Any],
        query_selection: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze SERP results

        Args:
            serp_fetcher_output: Output from SerpFetcher
            query_selection: Output from QuerySelector

        Returns:
            serp_research_extension dict
        """
        self.log_step("Analyzing SERP results")

        main_query = query_selection['main_query']
        cluster_queries = query_selection['cluster_queries']
        queries_rationale = query_selection['queries_rationale']

        serp_results = serp_fetcher_output['results']

        # Build serp_sets
        serp_sets = []

        for serp_result in serp_results:
            query = serp_result['query']
            serp_items = serp_result['serp_items']

            # Analyze this SERP set
            serp_set = self._analyze_serp_set(query, serp_items)
            serp_sets.append(serp_set)

        # Derive links and confidence
        derived_links = self._derive_links(serp_sets)

        result = {
            "main_query": main_query,
            "cluster_queries": cluster_queries,
            "queries_rationale": queries_rationale,
            "serp_sets": serp_sets,
            "derived_links": derived_links
        }

        self.log_step(f"SERP analysis complete: {len(serp_sets)} sets analyzed")
        return result

    def _analyze_serp_set(self, query: str, serp_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze a single SERP set

        Returns dict with:
        - query
        - dominant_intent
        - secondary_intents
        - page_archetypes
        - required_subtopics
        - top_results_sample
        """
        self.log_step(f"Analyzing SERP for query: '{query}'", level="debug")

        # Infer intent from snippets/titles
        dominant_intent = self._infer_dominant_intent(serp_items)

        # Detect page archetypes
        page_archetypes = self._detect_page_archetypes(serp_items)

        # Analyze top results (fetch content for top 3-5)
        top_results_sample = self._analyze_top_results(serp_items[:5])

        # Extract required subtopics (from all results)
        required_subtopics = self._extract_required_subtopics(top_results_sample)

        return {
            "query": query,
            "dominant_intent": dominant_intent,
            "secondary_intents": [],  # Simplified
            "page_archetypes": page_archetypes,
            "required_subtopics": required_subtopics,
            "top_results_sample": top_results_sample
        }

    def _infer_dominant_intent(self, serp_items: List[Dict[str, Any]]) -> str:
        """
        Infer dominant search intent from SERP items
        Simplified heuristic – in production, use LLM
        """
        # Combine titles and snippets
        text = ' '.join([
            f"{item.get('title', '')} {item.get('snippet', '')}"
            for item in serp_items
        ]).lower()

        # Intent signals
        if any(kw in text for kw in ['köp', 'pris', 'beställ', 'buy', 'price', 'shop']):
            if any(kw in text for kw in ['jämför', 'bästa', 'compare', 'best', 'review']):
                return "commercial_research"
            else:
                return "transactional"

        if any(kw in text for kw in ['hur', 'vad', 'guide', 'how', 'what', 'tutorial']):
            return "info_primary"

        if any(kw in text for kw in ['hjälp', 'support', 'kontakt', 'frågor', 'help', 'contact']):
            return "support"

        # Default
        return "info_primary"

    def _detect_page_archetypes(self, serp_items: List[Dict[str, Any]]) -> List[str]:
        """
        Detect common page types in SERP
        """
        archetypes = []

        for item in serp_items:
            url = item.get('url', '')
            title = item.get('title', '').lower()

            detected = "other"

            if '/guide' in url or 'guide' in title:
                detected = "guide"
            elif '/comparison' in url or 'jämför' in title or 'compare' in title:
                detected = "comparison"
            elif '/product' in url or '/produkt' in url:
                detected = "product"
            elif '/review' in title or 'recension' in title or 'test' in title:
                detected = "review"
            elif '/faq' in url or 'frågor' in title:
                detected = "faq"
            elif '/news' in url or 'nyheter' in title:
                detected = "news"

            archetypes.append(detected)

        # Return unique archetypes
        counter = Counter(archetypes)
        return [arch for arch, count in counter.most_common(5)]

    def _analyze_top_results(self, top_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Deep analyze top 3-5 results
        In production: fetch actual content, use LLM for analysis

        For now: simplified placeholder
        """
        analyzed = []

        for item in top_items:
            rank = item['rank']
            url = item['url']
            title = item['title']
            snippet = item['snippet']

            # Attempt to fetch content (with error handling)
            content_excerpt = ""
            key_entities = []
            key_subtopics = []

            try:
                # Fetch page (with timeout)
                response = requests.get(url, timeout=5, headers={'User-Agent': 'BacklinkBot/1.0'})
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Extract excerpt
                    for tag in soup(['script', 'style', 'nav', 'footer']):
                        tag.decompose()

                    text = soup.get_text(separator=' ', strip=True)[:400]
                    content_excerpt = re.sub(r'\s+', ' ', text)

                    # Extract entities (very simplified)
                    key_entities = self._extract_entities_simple(text)

                    # Extract subtopics (headings)
                    headings = [h.get_text(strip=True) for h in soup.find_all(['h2', 'h3'], limit=5)]
                    key_subtopics = [h.lower() for h in headings if len(h) > 5]

            except Exception as e:
                self.logger.debug(f"Could not fetch {url}: {e}")

            # Detect page type
            detected_page_type = self._detect_page_type_single(url, title)

            # Why it ranks (simplified)
            why_it_ranks = f"Ranks due to {detected_page_type} format covering {', '.join(key_subtopics[:2]) if key_subtopics else 'relevant topics'}."

            analyzed.append({
                "rank": rank,
                "url": url,
                "title": title,
                "snippet": snippet,
                "detected_page_type": detected_page_type,
                "content_excerpt": content_excerpt,
                "content_signals": [],  # Placeholder
                "key_entities": key_entities[:6],
                "key_subtopics": key_subtopics[:5],
                "why_it_ranks": why_it_ranks
            })

        return analyzed

    def _detect_page_type_single(self, url: str, title: str) -> str:
        """Detect page type for a single result"""
        url_lower = url.lower()
        title_lower = title.lower()

        if 'guide' in url_lower or 'guide' in title_lower:
            return "guide"
        elif 'comparison' in url_lower or 'jämför' in title_lower or 'compare' in title_lower:
            return "comparison"
        elif 'product' in url_lower or 'produkt' in url_lower:
            return "product"
        elif 'review' in title_lower or 'recension' in title_lower:
            return "review"
        elif 'faq' in url_lower:
            return "faq"
        elif 'news' in url_lower or 'nyheter' in url_lower:
            return "news"
        else:
            return "other"

    def _extract_entities_simple(self, text: str) -> List[str]:
        """Simple entity extraction (capitalized words)"""
        words = text.split()
        entities = []

        for word in words:
            if word and len(word) > 3 and word[0].isupper():
                if word not in entities:
                    entities.append(word)

        return entities[:10]

    def _extract_required_subtopics(self, top_results: List[Dict[str, Any]]) -> List[str]:
        """
        Extract subtopics that appear in ≥60% of top results
        """
        all_subtopics = []

        for result in top_results:
            all_subtopics.extend(result.get('key_subtopics', []))

        # Count frequency
        counter = Counter(all_subtopics)

        threshold = len(top_results) * 0.6

        required = [subtopic for subtopic, count in counter.items() if count >= threshold]

        return required[:10]

    def _derive_links(self, serp_sets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Derive links and confidence

        Returns derived_links object
        """
        # Check if all queries succeeded
        if all(len(s.get('top_results_sample', [])) >= 3 for s in serp_sets):
            confidence = "high"
        elif any(len(s.get('top_results_sample', [])) >= 3 for s in serp_sets):
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "intent_profile_ref": "Kopplas till intent_extension.serp_intent_primary/secondary",
            "required_subtopics_merged_ref": "Kopplas till intent_extension.required_subtopics",
            "data_confidence": confidence,
            "notes": f"Analyzed {len(serp_sets)} SERP sets with {confidence} confidence."
        }
