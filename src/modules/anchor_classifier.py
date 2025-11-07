"""
Anchor Classifier - Classifies anchor text types and implied intent.

Classifies anchors according to Next-A1 categories:
- exact: Exact match keywords
- partial: Partial match with variations
- brand: Brand/company names
- generic: Generic CTAs or descriptive text

Also infers the intent implied by the anchor text.
"""

from dataclasses import dataclass
from typing import Dict, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AnchorProfile:
    """
    Profile of anchor text with classification and intent inference.

    Based on BacklinkJobPackage schema's anchor_profile requirements.
    """
    proposed_text: str
    type_hint: Optional[str]  # User-provided hint
    llm_classified_type: str  # System classification: exact, partial, brand, generic
    llm_intent_hint: str  # Implied intent


class AnchorClassifier:
    """
    Classifies anchor text and infers implied search intent.

    Uses heuristics and patterns to determine anchor type without LLM dependency
    (though can be enhanced with LLM in production).
    """

    # Intent keywords mapping
    INTENT_KEYWORDS = {
        "info_primary": [
            "vad är", "what is", "hur fungerar", "how does", "guide",
            "förklaring", "explanation", "läs mer", "read more", "information"
        ],
        "commercial_research": [
            "bäst", "best", "jämför", "compare", "vs", "versus", "test",
            "recension", "review", "alternativ", "alternatives", "rätt", "right choice"
        ],
        "transactional": [
            "köp", "buy", "beställ", "order", "pris", "price", "erbjudande",
            "deal", "rabatt", "discount", "köpguide", "buying guide"
        ],
        "navigational_brand": [
            "webbplats", "website", "officiell", "official", "sida", "site"
        ],
        "support": [
            "hjälp", "help", "support", "kontakt", "contact", "frågor", "faq"
        ],
    }

    def classify_anchor(
        self,
        anchor_text: str,
        target_title: Optional[str] = None,
        target_entities: Optional[list] = None,
        type_hint: Optional[str] = None
    ) -> AnchorProfile:
        """
        Classify anchor text and infer intent.

        Args:
            anchor_text: The proposed anchor text
            target_title: Optional target page title for comparison
            target_entities: Optional target page entities for comparison
            type_hint: Optional user-provided type hint

        Returns:
            AnchorProfile with classification and intent
        """
        logger.info("Classifying anchor", anchor=anchor_text[:50])

        anchor_lower = anchor_text.lower().strip()

        # Classify type
        classified_type = self._classify_type(
            anchor_lower,
            target_title,
            target_entities,
            type_hint
        )

        # Infer intent
        intent_hint = self._infer_intent(anchor_lower, classified_type)

        profile = AnchorProfile(
            proposed_text=anchor_text,
            type_hint=type_hint,
            llm_classified_type=classified_type,
            llm_intent_hint=intent_hint
        )

        logger.info(
            "Anchor classified",
            type=classified_type,
            intent=intent_hint
        )

        return profile

    def _classify_type(
        self,
        anchor_lower: str,
        target_title: Optional[str],
        target_entities: Optional[list],
        type_hint: Optional[str]
    ) -> str:
        """
        Classify anchor type: exact, partial, brand, or generic.

        Next-A1 definitions:
        - exact: Exact match with target keywords
        - partial: Partial match with variations
        - brand: Brand/company name
        - generic: Generic descriptive text or CTA
        """
        # If user provided valid hint, respect it
        if type_hint in ["exact", "partial", "brand", "generic"]:
            logger.debug("Using user type hint", type=type_hint)
            return type_hint

        # Check for generic CTAs first
        generic_patterns = [
            "klicka här", "click here", "läs mer", "read more",
            "här", "here", "denna", "this", "länk", "link",
            "se mer", "see more", "fortsätt", "continue"
        ]
        if any(pattern in anchor_lower for pattern in generic_patterns):
            return "generic"

        # Check for brand indicators
        if target_entities:
            entities_lower = [e.lower() for e in target_entities]
            # If anchor contains a recognized entity/brand name
            for entity in entities_lower:
                if entity in anchor_lower and len(entity) > 3:
                    return "brand"

        # Check for exact match with title
        if target_title:
            title_lower = target_title.lower().strip()
            # Remove common suffixes
            for suffix in [" | ", " - ", " – "]:
                if suffix in title_lower:
                    title_lower = title_lower.split(suffix)[0].strip()

            # Exact match
            if anchor_lower == title_lower or anchor_lower in title_lower:
                return "exact"

            # Partial match (significant overlap)
            anchor_words = set(anchor_lower.split())
            title_words = set(title_lower.split())
            # Remove stop words
            stop_words = {"i", "och", "att", "det", "som", "en", "på", "är", "för", "med",
                         "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
            anchor_words -= stop_words
            title_words -= stop_words

            if anchor_words and title_words:
                overlap = len(anchor_words & title_words) / len(anchor_words)
                if overlap > 0.5:
                    return "partial"

        # Check for descriptive/navigational patterns
        descriptive_patterns = [
            "guide", "information", "fakta", "om", "about", "tips"
        ]
        if any(pattern in anchor_lower for pattern in descriptive_patterns):
            return "partial"

        # Default: if contains multiple words and isn't clearly generic, assume partial
        word_count = len(anchor_lower.split())
        if word_count >= 3:
            return "partial"

        # Very short anchors without context
        return "generic"

    def _infer_intent(self, anchor_lower: str, anchor_type: str) -> str:
        """
        Infer search intent implied by the anchor text.

        Returns intent category: info_primary, commercial_research,
        transactional, navigational_brand, support, or mixed
        """
        # Check each intent category
        intent_scores = {}

        for intent, keywords in self.INTENT_KEYWORDS.items():
            matches = sum(1 for kw in keywords if kw in anchor_lower)
            if matches > 0:
                intent_scores[intent] = matches

        # If we have clear winner
        if intent_scores:
            max_score = max(intent_scores.values())
            # Get all intents with max score
            top_intents = [i for i, s in intent_scores.items() if s == max_score]

            if len(top_intents) == 1:
                return top_intents[0]
            else:
                # Multiple intents matched equally
                # Prioritize based on anchor type
                if anchor_type == "brand":
                    return "navigational_brand"
                elif anchor_type in ["exact", "partial"]:
                    return "commercial_research"

                return "mixed"

        # No keyword matches - infer from anchor type
        type_to_intent = {
            "brand": "navigational_brand",
            "exact": "commercial_research",
            "partial": "info_primary",
            "generic": "info_primary",
        }

        return type_to_intent.get(anchor_type, "info_primary")

    def to_job_package_format(self, anchor_profile: AnchorProfile) -> Dict:
        """
        Convert AnchorProfile to BacklinkJobPackage schema format.

        Returns:
            Dictionary matching the anchor_profile section of BacklinkJobPackage
        """
        return {
            "proposed_text": anchor_profile.proposed_text,
            "type_hint": anchor_profile.type_hint,
            "llm_classified_type": anchor_profile.llm_classified_type,
            "llm_intent_hint": anchor_profile.llm_intent_hint,
        }
