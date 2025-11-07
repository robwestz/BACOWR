"""
IntentAndClusterModeler Module

Models intent profile by solving the variable marriage problem:
Publisher × Anchor × Target × Intent
"""

from typing import Dict, Any, List
from .base import BaseModule


class IntentAndClusterModeler(BaseModule):
    """
    Models intent profile.

    Input:
        - target_profile
        - publisher_profile
        - anchor_profile
        - serp_research_extension

    Output:
        - intent_extension: Dict
    """

    def run(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Model intent profile

        Returns:
            intent_extension dict
        """
        self.log_step("Modeling intent profile")

        # Extract SERP intent
        serp_intent_primary, serp_intent_secondary = self._extract_serp_intent(serp_research_extension)

        # Model target page intent
        target_page_intent = self._model_target_intent(target_profile)

        # Anchor implied intent
        anchor_implied_intent = anchor_profile.get('llm_intent_hint', 'info_primary')

        # Publisher role intent
        publisher_role_intent = self._model_publisher_intent(publisher_profile)

        # Calculate alignment
        intent_alignment = self._calculate_alignment(
            anchor_implied_intent,
            target_page_intent,
            publisher_role_intent,
            serp_intent_primary
        )

        # Recommend bridge type
        recommended_bridge_type = self._recommend_bridge_type(intent_alignment, publisher_profile, target_profile)

        # Recommend article angle
        recommended_article_angle = self._recommend_article_angle(
            target_profile,
            publisher_profile,
            anchor_profile,
            recommended_bridge_type
        )

        # Merge required subtopics
        required_subtopics = self._merge_required_subtopics(serp_research_extension)

        # Define forbidden angles
        forbidden_angles = self._define_forbidden_angles(publisher_profile, intent_alignment)

        # Build rationale
        rationale = self._build_rationale(
            target_profile,
            publisher_profile,
            serp_intent_primary,
            intent_alignment,
            recommended_bridge_type
        )

        # Data confidence
        data_confidence = serp_research_extension['derived_links'].get('data_confidence', 'medium')

        intent_extension = {
            "serp_intent_primary": serp_intent_primary,
            "serp_intent_secondary": serp_intent_secondary,
            "target_page_intent": target_page_intent,
            "anchor_implied_intent": anchor_implied_intent,
            "publisher_role_intent": publisher_role_intent,
            "intent_alignment": intent_alignment,
            "recommended_bridge_type": recommended_bridge_type,
            "recommended_article_angle": recommended_article_angle,
            "required_subtopics": required_subtopics,
            "forbidden_angles": forbidden_angles,
            "notes": {
                "rationale": rationale,
                "data_confidence": data_confidence
            }
        }

        self.log_step(
            f"Intent modeled: bridge_type={recommended_bridge_type}, "
            f"alignment={intent_alignment['overall']}"
        )

        return intent_extension

    def _extract_serp_intent(self, serp_research: Dict[str, Any]) -> tuple:
        """Extract primary and secondary intents from SERP research"""
        serp_sets = serp_research.get('serp_sets', [])

        if not serp_sets:
            return "info_primary", []

        # Use main query's intent as primary
        main_set = serp_sets[0]
        primary = main_set.get('dominant_intent', 'info_primary')

        # Collect secondary from cluster queries
        secondary = []
        for serp_set in serp_sets[1:]:
            intent = serp_set.get('dominant_intent')
            if intent and intent != primary and intent not in secondary:
                secondary.append(intent)

        return primary, secondary

    def _model_target_intent(self, target_profile: Dict[str, Any]) -> str:
        """
        Model target page intent
        Simplified heuristic – in production, use LLM
        """
        core_offer = target_profile.get('core_offer', '').lower()
        title = target_profile.get('title', '').lower()

        # Transactional signals
        if any(kw in core_offer or kw in title for kw in ['köp', 'beställ', 'shop', 'buy', 'pris', 'price']):
            return "transactional_with_info_support"

        # Support signals
        if any(kw in core_offer or kw in title for kw in ['hjälp', 'support', 'kundtjänst', 'faq', 'customer service']):
            return "support"

        # Commercial research
        if any(kw in core_offer or kw in title for kw in ['jämför', 'bästa', 'compare', 'best', 'review']):
            return "commercial_research"

        # Default: info
        return "info_primary"

    def _model_publisher_intent(self, publisher_profile: Dict[str, Any]) -> str:
        """Model publisher's role intent"""
        tone_class = publisher_profile.get('tone_class', 'consumer_magazine')
        allowed_commerciality = publisher_profile.get('allowed_commerciality', 'medium')

        if tone_class in ['academic', 'authority_public']:
            return "info_primary"
        elif allowed_commerciality == 'high':
            return "commercial_research_with_transactional"
        elif allowed_commerciality == 'medium':
            return "info_primary_with_commercial_context"
        else:
            return "info_primary"

    def _calculate_alignment(
        self,
        anchor_intent: str,
        target_intent: str,
        publisher_intent: str,
        serp_intent: str
    ) -> Dict[str, str]:
        """
        Calculate intent alignment

        Returns:
            alignment dict with anchor_vs_serp, target_vs_serp, publisher_vs_serp, overall
        """
        # Alignment mapping (simplified)
        def align(a: str, b: str) -> str:
            if a == b:
                return "aligned"

            # Compatible intents
            compatible = {
                ('info_primary', 'commercial_research'),
                ('commercial_research', 'transactional'),
                ('commercial_research', 'info_primary'),
                ('support', 'info_primary')
            }

            if (a, b) in compatible or (b, a) in compatible:
                return "partial"

            # Check if one contains the other (e.g., "info_primary_with_commercial_context")
            if 'info_primary' in a and 'info_primary' in b:
                return "partial"
            if 'commercial' in a and 'commercial' in b:
                return "partial"
            if 'transactional' in a and 'commercial' in b:
                return "partial"

            return "off"

        anchor_vs_serp = align(anchor_intent, serp_intent)
        target_vs_serp = align(target_intent, serp_intent)
        publisher_vs_serp = align(publisher_intent, serp_intent)

        # Overall alignment
        if all(x == "aligned" for x in [anchor_vs_serp, target_vs_serp, publisher_vs_serp]):
            overall = "aligned"
        elif "off" in [anchor_vs_serp, target_vs_serp, publisher_vs_serp]:
            overall = "partial" if [anchor_vs_serp, target_vs_serp, publisher_vs_serp].count("off") == 1 else "off"
        else:
            overall = "partial"

        return {
            "anchor_vs_serp": anchor_vs_serp,
            "target_vs_serp": target_vs_serp,
            "publisher_vs_serp": publisher_vs_serp,
            "overall": overall
        }

    def _recommend_bridge_type(
        self,
        alignment: Dict[str, str],
        publisher_profile: Dict[str, Any],
        target_profile: Dict[str, Any]
    ) -> str:
        """
        Recommend bridge type based on alignment

        Rules (from Next-A1-2):
        - strong: If no component is 'off'
        - pivot: If at least one is 'partial' but can be bridged
        - wrapper: If overall is 'off'
        """
        overall = alignment['overall']

        if overall == "off":
            return "wrapper"
        elif overall == "aligned" and alignment['anchor_vs_serp'] == "aligned":
            return "strong"
        else:
            return "pivot"

    def _recommend_article_angle(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        bridge_type: str
    ) -> str:
        """Recommend article angle"""
        anchor_text = anchor_profile.get('proposed_text', '')
        target_offer = target_profile.get('core_offer', '')
        publisher_tone = publisher_profile.get('tone_class', '')

        if bridge_type == "strong":
            return f"Direct article about '{anchor_text}' with target as primary example."
        elif bridge_type == "pivot":
            return f"Broader article about related theme, introducing target naturally within context."
        else:  # wrapper
            return f"Meta-frame article (methodology/risk/ethics) where target is mentioned as one case/tool."

    def _merge_required_subtopics(self, serp_research: Dict[str, Any]) -> List[str]:
        """Merge required subtopics from all SERP sets"""
        all_subtopics = []

        for serp_set in serp_research.get('serp_sets', []):
            all_subtopics.extend(serp_set.get('required_subtopics', []))

        # Deduplicate and return
        unique = list(set(all_subtopics))

        return unique[:10]

    def _define_forbidden_angles(
        self,
        publisher_profile: Dict[str, Any],
        alignment: Dict[str, str]
    ) -> List[str]:
        """Define forbidden angles based on publisher and alignment"""
        forbidden = []

        # Check publisher tone
        tone_class = publisher_profile.get('tone_class')
        allowed_commerciality = publisher_profile.get('allowed_commerciality')

        if tone_class in ['academic', 'authority_public'] or allowed_commerciality == 'low':
            forbidden.append("Aggressiv säljcopy eller hård CTA")

        # Check brand safety
        brand_safety = publisher_profile.get('brand_safety_notes', '')
        if 'gambling' in brand_safety.lower() or 'spelbolag' in brand_safety.lower():
            forbidden.append("Innehåll relaterat till gambling/spel")

        # Check alignment
        if alignment['overall'] == 'off':
            forbidden.append("Direkt påstående om att target är 'bäst' eller 'rekommenderad'")

        return forbidden

    def _build_rationale(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        serp_intent: str,
        alignment: Dict[str, str],
        bridge_type: str
    ) -> str:
        """Build rationale for intent profile"""
        publisher_tone = publisher_profile.get('tone_class', 'unknown')
        target_intent = target_profile.get('core_offer', 'unknown')

        rationale = (
            f"SERP intent is '{serp_intent}'. "
            f"Publisher is '{publisher_tone}' with alignment '{alignment['publisher_vs_serp']}'. "
            f"Target offers '{target_intent[:50]}...' with alignment '{alignment['target_vs_serp']}'. "
            f"Overall alignment: '{alignment['overall']}'. "
            f"Recommended bridge type: '{bridge_type}'."
        )

        return rationale
