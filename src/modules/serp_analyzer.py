"""
SERP Analyzer - Analyzes SERP results to extract intent and content patterns.

Creates the serp_research_extension for BacklinkJobPackage.

This is a CORE component of Next-A1's SERP-first approach.

EXTENSIBILITY NOTE:
This analyzer can be enhanced and reused for:
- Intent classification systems
- Content gap analysis tools
- Competitive intelligence platforms
- SERP feature tracking
- Historical intent shift analysis
- Machine learning training data generation
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .serp_fetcher import SerpSet, SerpResult
from .query_selector import QuerySet
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SerpResearchExtension:
    """
    Complete SERP research data for BacklinkJobPackage.

    Maps to serp_research_extension in Next-A1 spec.
    """
    main_query: str
    cluster_queries: List[str]
    queries_rationale: str
    serp_sets: List[Dict]  # Processed SERP data per query
    derived_links: Dict  # Links to intent_extension
    data_confidence: str  # high, medium, low


class SerpAnalyzer:
    """
    Analyzes SERP results to extract intent, patterns, and requirements.

    This analyzer is designed to be deterministic and explainable, with clear
    heuristics for all classifications. In production, can be enhanced with LLM
    for deeper semantic analysis.
    """

    # Intent classification keywords (extensible)
    INTENT_SIGNALS = {
        "info_primary": {
            "title_patterns": ["vad är", "what is", "hur", "how", "varför", "why", "guide", "förklaring"],
            "url_patterns": ["/guide", "/how-to", "/what-is", "/forklaring"],
            "snippet_patterns": ["definition", "explanation", "learn", "understand", "lär dig"]
        },
        "commercial_research": {
            "title_patterns": ["bäst", "best", "top", "jämför", "compare", "vs", "test", "recension", "review"],
            "url_patterns": ["/best-", "/compare", "/review", "/test", "/vs"],
            "snippet_patterns": ["comparison", "jämförelse", "pros and cons", "fördelar", "nackdelar"]
        },
        "transactional": {
            "title_patterns": ["köp", "buy", "pris", "price", "erbjudande", "deal", "billig", "cheap"],
            "url_patterns": ["/buy", "/shop", "/product", "/kop", "/pris"],
            "snippet_patterns": ["köp", "buy", "from", "från", "price starting"]
        },
        "navigational_brand": {
            "title_patterns": ["officiell", "official", "hemsida", "website", "login"],
            "url_patterns": ["/login", "/signin", "/about", "/om-oss"],
            "snippet_patterns": ["officiell", "official", "main website"]
        }
    }

    def __init__(self):
        """Initialize SERP analyzer."""
        pass

    def analyze_serp_set(self, serp_set: SerpSet) -> Dict:
        """
        Analyze a single SERP set and extract patterns.

        Args:
            serp_set: SERP results for one query

        Returns:
            Processed SERP data matching serp_research_extension.serp_sets schema

        LLM ENHANCEMENT OPPORTUNITY:
        In production, this method could leverage LLM to:
        - Extract more nuanced intent signals
        - Identify semantic patterns across results
        - Detect emerging content formats
        - Understand context-dependent meanings
        """
        logger.debug("Analyzing SERP set", query=serp_set.query)

        # Detect dominant intent
        dominant_intent, secondary_intents = self._detect_intent(serp_set)

        # Extract page archetypes
        page_archetypes = self._extract_page_archetypes(serp_set)

        # Identify required subtopics (what all top results cover)
        required_subtopics = self._extract_required_subtopics(serp_set)

        # Build top results sample
        top_results_sample = []
        for result in serp_set.results[:10]:
            result_data = {
                "rank": result.rank,
                "url": result.url,
                "title": result.title,
                "detected_page_type": result.detected_page_type or self._detect_page_type(result),
                "snippet": result.snippet,
                "content_signals": self._extract_content_signals(result),
                "key_entities": result.key_entities,
                "key_subtopics": result.key_subtopics
            }
            top_results_sample.append(result_data)

        return {
            "query": serp_set.query,
            "dominant_intent": dominant_intent,
            "secondary_intents": secondary_intents,
            "page_archetypes": page_archetypes,
            "required_subtopics": required_subtopics,
            "top_results_sample": top_results_sample
        }

    def analyze_full_research(
        self,
        query_set: QuerySet,
        serp_sets: List[SerpSet]
    ) -> SerpResearchExtension:
        """
        Analyze complete SERP research (main + cluster queries).

        Args:
            query_set: Selected queries
            serp_sets: SERP results for all queries

        Returns:
            Complete serp_research_extension for BacklinkJobPackage
        """
        logger.info("Analyzing full SERP research", queries=len(serp_sets))

        # Analyze each SERP set
        analyzed_serp_sets = []
        for serp_set in serp_sets:
            analyzed = self.analyze_serp_set(serp_set)
            analyzed_serp_sets.append(analyzed)

        # Derive aggregate insights
        merged_subtopics = self._merge_subtopics(analyzed_serp_sets)
        primary_intent = self._determine_primary_intent(analyzed_serp_sets)
        data_confidence = self._assess_data_confidence(serp_sets)

        # Build derived_links (references for intent_extension)
        derived_links = {
            "intent_profile_ref": f"Primary intent: {primary_intent}",
            "required_subtopics_merged_ref": f"{len(merged_subtopics)} subtopics identified",
            "data_confidence": data_confidence
        }

        extension = SerpResearchExtension(
            main_query=query_set.main_query,
            cluster_queries=query_set.cluster_queries,
            queries_rationale=query_set.rationale,
            serp_sets=analyzed_serp_sets,
            derived_links=derived_links,
            data_confidence=data_confidence
        )

        logger.info(
            "SERP analysis complete",
            primary_intent=primary_intent,
            subtopics=len(merged_subtopics),
            confidence=data_confidence
        )

        return extension

    def _detect_intent(self, serp_set: SerpSet) -> Tuple[str, List[str]]:
        """
        Detect dominant and secondary intents from SERP results.

        Uses heuristics on titles, URLs, and snippets.

        LLM ENHANCEMENT OPPORTUNITY:
        An LLM could provide more nuanced intent detection by:
        - Understanding semantic similarity
        - Detecting intent from snippet context
        - Identifying mixed-intent scenarios
        - Considering user journey stages
        """
        intent_scores = Counter()

        # Analyze top 10 results
        for result in serp_set.results[:10]:
            # Weight by rank (top results = more signal)
            weight = 1.0 / result.rank

            title_lower = result.title.lower()
            url_lower = result.url.lower()
            snippet_lower = result.snippet.lower()

            # Check each intent's signals
            for intent, signals in self.INTENT_SIGNALS.items():
                score = 0

                # Title signals (strongest)
                for pattern in signals["title_patterns"]:
                    if pattern in title_lower:
                        score += 3 * weight

                # URL signals (medium)
                for pattern in signals["url_patterns"]:
                    if pattern in url_lower:
                        score += 2 * weight

                # Snippet signals (weakest but still valuable)
                for pattern in signals["snippet_patterns"]:
                    if pattern in snippet_lower:
                        score += 1 * weight

                if score > 0:
                    intent_scores[intent] += score

        # Determine dominant and secondary
        if not intent_scores:
            return "mixed", []

        sorted_intents = intent_scores.most_common()
        dominant = sorted_intents[0][0]

        # Secondary: any intent with >30% of dominant score
        dominant_score = sorted_intents[0][1]
        secondary = [
            intent for intent, score in sorted_intents[1:]
            if score > dominant_score * 0.3
        ]

        return dominant, secondary

    def _extract_page_archetypes(self, serp_set: SerpSet) -> List[str]:
        """
        Extract common page archetypes from SERP results.

        Archetypes: guide, comparison, category, product, review, tool, faq, news, official
        """
        archetypes = Counter()

        for result in serp_set.results[:10]:
            page_type = result.detected_page_type or self._detect_page_type(result)
            if page_type:
                archetypes[page_type] += 1

        # Return archetypes that appear in at least 2 results
        return [arch for arch, count in archetypes.most_common() if count >= 2]

    def _detect_page_type(self, result: SerpResult) -> str:
        """
        Detect page type from result metadata.

        Returns: guide, comparison, product, review, tool, article, etc.
        """
        title_lower = result.title.lower()
        url_lower = result.url.lower()

        # Pattern matching
        if any(word in title_lower for word in ["guide", "how to", "hur", "så här"]):
            return "guide"
        if any(word in title_lower for word in ["vs", "versus", "jämför", "compare", "bäst", "best"]):
            return "comparison"
        if any(word in title_lower for word in ["review", "recension", "test"]):
            return "review"
        if any(word in title_lower for word in ["kategori", "category"]):
            return "category"
        if any(word in url_lower for word in ["/product/", "/produkt/"]):
            return "product"
        if any(word in title_lower for word in ["faq", "frågor", "questions"]):
            return "faq"
        if any(word in title_lower for word in ["verktyg", "tool", "calculator", "kalkylator"]):
            return "tool"

        return "article"

    def _extract_content_signals(self, result: SerpResult) -> List[str]:
        """
        Extract content signals (what the page emphasizes).

        E.g., "comparison", "transparency", "risks", "benefits"

        LLM ENHANCEMENT OPPORTUNITY:
        An LLM could extract more sophisticated content signals:
        - Sentiment and tone
        - Expertise indicators (E-E-A-T)
        - Unique angles or perspectives
        - Content depth indicators
        """
        signals = []

        snippet_lower = result.snippet.lower()
        title_lower = result.title.lower()

        # Comparison signals
        if any(word in snippet_lower for word in ["jämför", "compare", "vs", "alternativ"]):
            signals.append("comparison")

        # Transparency/trust signals
        if any(word in snippet_lower for word in ["transparent", "opartisk", "unbiased", "honest"]):
            signals.append("transparency")

        # Risk/caution signals
        if any(word in snippet_lower for word in ["risk", "varning", "warning", "nackdel", "cons"]):
            signals.append("risks")

        # Benefit signals
        if any(word in snippet_lower for word in ["fördelar", "benefits", "pros", "advantage"]):
            signals.append("benefits")

        # How-to/guide signals
        if any(word in snippet_lower for word in ["steg", "steps", "guide", "how to"]):
            signals.append("step-by-step")

        # Expert/authority signals
        if any(word in snippet_lower for word in ["expert", "specialist", "professionell", "research"]):
            signals.append("expertise")

        return signals if signals else ["general_information"]

    def _extract_required_subtopics(self, serp_set: SerpSet) -> List[str]:
        """
        Extract subtopics that appear across multiple top results.

        These are "table stakes" - things the content should cover to compete.

        LLM ENHANCEMENT OPPORTUNITY:
        An LLM could:
        - Group semantically similar subtopics
        - Identify implicit subtopics from context
        - Rank subtopics by importance
        - Detect emerging subtopics
        """
        subtopic_counter = Counter()

        # Collect subtopics from top 5 results
        for result in serp_set.results[:5]:
            for subtopic in result.key_subtopics:
                subtopic_counter[subtopic.lower()] += 1

        # Return subtopics appearing in at least 2 of top 5
        required = [
            subtopic for subtopic, count in subtopic_counter.most_common()
            if count >= 2
        ]

        # If we don't have enough, extract from snippets
        if len(required) < 3:
            required.extend(self._extract_subtopics_from_snippets(serp_set))

        return required[:8]  # Limit to 8 most important

    def _extract_subtopics_from_snippets(self, serp_set: SerpSet) -> List[str]:
        """
        Extract subtopics from result snippets using heuristics.

        Fallback when structured subtopics aren't available.
        """
        subtopics = []

        # Look for numbered lists, bullets, or topic indicators
        for result in serp_set.results[:5]:
            snippet = result.snippet

            # Look for "including X, Y, and Z" patterns
            if "including" in snippet.lower():
                parts = snippet.lower().split("including")
                if len(parts) > 1:
                    items = parts[1].split(",")
                    subtopics.extend(item.strip() for item in items[:2])

            # Look for "such as X and Y" patterns
            if "such as" in snippet.lower():
                parts = snippet.lower().split("such as")
                if len(parts) > 1:
                    items = parts[1].split("and")
                    subtopics.extend(item.strip() for item in items[:2])

        return subtopics[:5]

    def _merge_subtopics(self, analyzed_serp_sets: List[Dict]) -> List[str]:
        """
        Merge subtopics from all SERP sets into a consolidated list.

        Returns subtopics that appear across multiple queries.
        """
        all_subtopics = Counter()

        for serp_set in analyzed_serp_sets:
            for subtopic in serp_set["required_subtopics"]:
                all_subtopics[subtopic.lower()] += 1

        # Return subtopics appearing in multiple queries
        merged = [
            subtopic for subtopic, count in all_subtopics.most_common()
            if count >= 2 or len(analyzed_serp_sets) == 1
        ]

        return merged[:10]  # Top 10

    def _determine_primary_intent(self, analyzed_serp_sets: List[Dict]) -> str:
        """
        Determine primary intent across all analyzed SERP sets.

        Uses majority voting weighted by main vs cluster queries.
        """
        intent_scores = Counter()

        for i, serp_set in enumerate(analyzed_serp_sets):
            dominant = serp_set["dominant_intent"]
            # Weight main query (first) higher
            weight = 2.0 if i == 0 else 1.0
            intent_scores[dominant] += weight

        if not intent_scores:
            return "mixed"

        return intent_scores.most_common(1)[0][0]

    def _assess_data_confidence(self, serp_sets: List[SerpSet]) -> str:
        """
        Assess confidence in SERP data quality.

        Returns: "high", "medium", or "low"

        Factors:
        - Number of results per query
        - Consistency across queries
        - Freshness of data
        """
        if not serp_sets:
            return "low"

        # Check result counts
        avg_results = sum(len(s.results) for s in serp_sets) / len(serp_sets)
        if avg_results < 5:
            return "low"
        elif avg_results >= 8:
            confidence = "high"
        else:
            confidence = "medium"

        # Check consistency (do queries show similar intents?)
        intents = [s.dominant_intent for s in serp_sets if s.dominant_intent]
        if intents:
            most_common_count = Counter(intents).most_common(1)[0][1]
            consistency = most_common_count / len(intents)
            if consistency < 0.5:
                confidence = "medium" if confidence == "high" else "low"

        return confidence

    def to_job_package_format(self, extension: SerpResearchExtension) -> Dict:
        """
        Convert SerpResearchExtension to BacklinkJobPackage format.

        Returns:
            Dictionary matching serp_research_extension schema
        """
        return {
            "main_query": extension.main_query,
            "cluster_queries": extension.cluster_queries,
            "queries_rationale": extension.queries_rationale,
            "serp_sets": extension.serp_sets,
            "derived_links": extension.derived_links
        }
