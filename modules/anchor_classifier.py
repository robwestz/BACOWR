"""
AnchorClassifier Module

Classifies anchor text type and infers implied intent.
"""

from typing import Dict, Any, Optional
from .base import BaseModule


class AnchorClassifier(BaseModule):
    """
    Classifies anchor text.

    Input:
        - anchor_text: str
        - type_hint: Optional[str]

    Output:
        - anchor_profile: Dict
    """

    def run(self, anchor_text: str, type_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify anchor text

        Args:
            anchor_text: Proposed anchor text
            type_hint: Optional user hint (exact, partial, brand, generic)

        Returns:
            anchor_profile dict
        """
        self.log_step(f"Classifying anchor: '{anchor_text}'")

        # Use type_hint if provided, otherwise classify
        if type_hint:
            classified_type = type_hint
        else:
            classified_type = self._classify_type(anchor_text)

        # Infer intent
        intent_hint = self._infer_intent(anchor_text, classified_type)

        profile = {
            "proposed_text": anchor_text,
            "type_hint": type_hint,
            "llm_classified_type": classified_type,
            "llm_intent_hint": intent_hint
        }

        self.log_step(f"Anchor classified: type={classified_type}, intent={intent_hint}")
        return profile

    def _classify_type(self, anchor_text: str) -> str:
        """
        Classify anchor type
        Simplified heuristic – in production, use LLM

        Types: exact, partial, brand, generic
        """
        text_lower = anchor_text.lower()

        # Generic anchors
        generic_patterns = [
            'klicka här', 'läs mer', 'click here', 'read more',
            'här', 'here', 'den här', 'this', 'denna sida'
        ]

        if any(pattern in text_lower for pattern in generic_patterns):
            return "generic"

        # Brand detection (very simplistic – check for capitalization)
        words = anchor_text.split()
        if len(words) <= 2 and any(w[0].isupper() for w in words if w):
            return "brand"

        # Exact vs Partial (heuristic: length and specificity)
        # Exact: typically product/service names, 1-3 words
        # Partial: broader, 3+ words, includes modifiers

        if len(words) <= 3 and not any(mod in text_lower for mod in ['bästa', 'bra', 'hur', 'vad', 'guide']):
            return "exact"
        else:
            return "partial"

    def _infer_intent(self, anchor_text: str, anchor_type: str) -> str:
        """
        Infer implied intent from anchor text

        Intents: info_primary, commercial_research, transactional,
                 navigational_brand, support, local, mixed
        """
        text_lower = anchor_text.lower()

        # Navigational brand
        if anchor_type == "brand":
            return "navigational_brand"

        # Transactional signals
        transactional_keywords = ['köp', 'beställ', 'priser', 'erbjudande', 'kampanj', 'buy', 'order', 'price']
        if any(kw in text_lower for kw in transactional_keywords):
            return "transactional"

        # Commercial research
        research_keywords = ['bästa', 'jämför', 'recensioner', 'test', 'guide till', 'compare', 'review', 'best']
        if any(kw in text_lower for kw in research_keywords):
            return "commercial_research"

        # Support
        support_keywords = ['hjälp', 'support', 'kundtjänst', 'kontakt', 'frågor', 'help', 'customer service']
        if any(kw in text_lower for kw in support_keywords):
            return "support"

        # Local
        if 'nära' in text_lower or 'lokal' in text_lower or 'nearby' in text_lower:
            return "local"

        # Default: info_primary
        return "info_primary"
