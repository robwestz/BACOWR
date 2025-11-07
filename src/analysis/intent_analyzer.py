"""
Intent Analyzer - Analyze intent alignment and recommend bridge type

Part of Del 3B: Content Generation Pipeline
Matches SERP intent vs target vs publisher vs anchor
"""

from typing import Dict, Any, List, Tuple


class IntentAnalyzer:
    """
    Analyzes intent alignment across all components.

    Supports:
    - Intent alignment analysis (anchor vs SERP vs target vs publisher)
    - Bridge type recommendation (strong/pivot/wrapper)
    - Required subtopics identification
    - Forbidden angles detection
    """

    # Intent compatibility matrix
    INTENT_COMPATIBILITY = {
        'info_primary': ['info_primary', 'commercial_research'],
        'commercial_research': ['info_primary', 'commercial_research', 'transactional'],
        'transactional': ['commercial_research', 'transactional'],
        'navigational_brand': ['navigational_brand'],
        'support': ['support', 'info_primary'],
        'local': ['local', 'info_primary']
    }

    # Bridge type rules
    BRIDGE_TYPE_RULES = {
        'strong': {
            'description': 'Direct match - all intents aligned',
            'conditions': ['all_aligned']
        },
        'pivot': {
            'description': 'Needs informational bridge to connect commercial target',
            'conditions': ['partial_alignment', 'publisher_informational', 'target_commercial']
        },
        'wrapper': {
            'description': 'Weak connection - needs extensive context wrapping',
            'conditions': ['low_alignment', 'intent_mismatch']
        }
    }

    def __init__(self):
        """Initialize Intent Analyzer"""
        pass

    def analyze(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform complete intent analysis.

        Args:
            target_profile: Target page profile
            publisher_profile: Publisher profile
            anchor_profile: Anchor profile
            serp_research: SERP research results

        Returns:
            intent_extension dict
        """
        # Determine intents
        serp_intent_primary = serp_research.get('serp_intent_primary', 'info_primary')
        serp_intent_secondary = serp_research.get('serp_intent_secondary', [])

        target_page_intent = self._infer_target_intent(target_profile)
        anchor_implied_intent = anchor_profile.get('llm_intent_hint') or self._infer_anchor_intent(
            anchor_profile.get('proposed_text', '')
        )
        publisher_role_intent = self._infer_publisher_intent(publisher_profile)

        # Analyze alignments
        intent_alignment = self._analyze_alignment(
            serp_intent_primary,
            target_page_intent,
            anchor_implied_intent,
            publisher_role_intent
        )

        # Recommend bridge type
        bridge_type = self._recommend_bridge_type(
            intent_alignment,
            target_page_intent,
            publisher_role_intent,
            serp_intent_primary
        )

        # Generate article angle
        article_angle = self._generate_article_angle(
            bridge_type,
            serp_intent_primary,
            target_page_intent,
            publisher_role_intent,
            target_profile,
            publisher_profile
        )

        # Identify required subtopics
        required_subtopics = self._identify_required_subtopics(
            serp_research,
            target_profile,
            bridge_type
        )

        # Identify forbidden angles
        forbidden_angles = self._identify_forbidden_angles(
            target_profile,
            publisher_profile,
            intent_alignment
        )

        # Generate rationale
        rationale = self._generate_rationale(
            serp_intent_primary,
            target_page_intent,
            publisher_role_intent,
            intent_alignment,
            bridge_type
        )

        # Determine data confidence
        data_confidence = self._determine_confidence(
            serp_research.get('data_confidence', 'medium'),
            intent_alignment
        )

        return {
            'serp_intent_primary': serp_intent_primary,
            'serp_intent_secondary': serp_intent_secondary,
            'target_page_intent': target_page_intent,
            'anchor_implied_intent': anchor_implied_intent,
            'publisher_role_intent': publisher_role_intent,
            'intent_alignment': intent_alignment,
            'recommended_bridge_type': bridge_type,
            'recommended_article_angle': article_angle,
            'required_subtopics': required_subtopics,
            'forbidden_angles': forbidden_angles,
            'notes': {
                'rationale': rationale,
                'data_confidence': data_confidence
            }
        }

    def _infer_target_intent(self, target_profile: Dict[str, Any]) -> str:
        """
        Infer target page intent from profile.

        Args:
            target_profile: Target profile

        Returns:
            Intent string
        """
        # Look at core offer and topics
        core_offer = target_profile.get('core_offer', '').lower()
        topics = [t.lower() for t in target_profile.get('core_topics', [])]

        # Check for commercial/transactional signals (strongest)
        commercial_signals = ['buy', 'purchase', 'order', 'pricing', 'price', 'deal', 'offer']
        if any(signal in core_offer for signal in commercial_signals):
            return 'transactional_with_info_support'

        # Check for comparison/research signals in topics
        research_signals = ['compare', 'jämför', 'review', 'test']
        if any(signal in topic for topic in topics for signal in research_signals):
            return 'commercial_research'

        # Check for comparison/research in core_offer (but not 'guide' alone which can be informational)
        if any(signal in core_offer for signal in research_signals):
            return 'commercial_research'

        # Default to informational
        return 'info_primary'

    def _infer_anchor_intent(self, anchor_text: str) -> str:
        """
        Infer intent from anchor text.

        Args:
            anchor_text: Anchor text

        Returns:
            Intent string
        """
        anchor_lower = anchor_text.lower()

        # Transactional signals
        if any(word in anchor_lower for word in ['buy', 'köp', 'order', 'beställ', 'shop']):
            return 'transactional'

        # Commercial research signals
        if any(word in anchor_lower for word in ['best', 'bäst', 'top', 'compare', 'jämför', 'review']):
            return 'commercial_research'

        # Navigational signals
        if any(word in anchor_lower for word in ['official', 'officiell', 'website', 'hemsida']):
            return 'navigational_brand'

        # Default to informational
        return 'info_primary'

    def _infer_publisher_intent(self, publisher_profile: Dict[str, Any]) -> str:
        """
        Infer publisher's natural role/intent.

        Args:
            publisher_profile: Publisher profile

        Returns:
            Intent string
        """
        tone_class = publisher_profile.get('tone_class', 'consumer_magazine')
        commerciality = publisher_profile.get('allowed_commerciality', 'medium')

        # Map tone class to intent
        tone_intent_map = {
            'academic': 'info_primary',
            'authority_public': 'info_primary',
            'consumer_magazine': 'commercial_research',
            'hobby_blog': 'info_primary',
            'news': 'info_primary'
        }

        return tone_intent_map.get(tone_class, 'info_primary')

    def _analyze_alignment(
        self,
        serp_intent: str,
        target_intent: str,
        anchor_intent: str,
        publisher_intent: str
    ) -> Dict[str, str]:
        """
        Analyze alignment between all intents.

        Args:
            serp_intent: SERP primary intent
            target_intent: Target page intent
            anchor_intent: Anchor implied intent
            publisher_intent: Publisher role intent

        Returns:
            Alignment dict
        """
        # Check each pair
        anchor_vs_serp = self._check_alignment(anchor_intent, serp_intent)
        target_vs_serp = self._check_alignment(target_intent, serp_intent)
        publisher_vs_serp = self._check_alignment(publisher_intent, serp_intent)

        # Determine overall alignment
        alignments = [anchor_vs_serp, target_vs_serp, publisher_vs_serp]
        if all(a == 'aligned' for a in alignments):
            overall = 'aligned'
        elif any(a == 'off' for a in alignments):
            overall = 'off'
        else:
            overall = 'partial'

        return {
            'anchor_vs_serp': anchor_vs_serp,
            'target_vs_serp': target_vs_serp,
            'publisher_vs_serp': publisher_vs_serp,
            'overall': overall
        }

    def _check_alignment(self, intent1: str, intent2: str) -> str:
        """
        Check alignment between two intents.

        Args:
            intent1: First intent
            intent2: Second intent

        Returns:
            'aligned' | 'partial' | 'off'
        """
        # Exact match
        if intent1 == intent2:
            return 'aligned'

        # Get base intent (first part before underscore)
        intent1_base = intent1.split('_')[0]
        intent2_base = intent2.split('_')[0]

        # Check if base parts match
        if intent1_base == intent2_base:
            return 'aligned'

        # Check compatibility using full intent first, then base
        # Check intent1 -> intent2
        for key in [intent1, intent1_base]:
            compatible = self.INTENT_COMPATIBILITY.get(key, [])
            if intent2 in compatible or intent2_base in compatible:
                return 'partial'

        # Check intent2 -> intent1
        for key in [intent2, intent2_base]:
            compatible = self.INTENT_COMPATIBILITY.get(key, [])
            if intent1 in compatible or intent1_base in compatible:
                return 'partial'

        # No alignment
        return 'off'

    def _recommend_bridge_type(
        self,
        alignment: Dict[str, str],
        target_intent: str,
        publisher_intent: str,
        serp_intent: str
    ) -> str:
        """
        Recommend bridge type based on alignment.

        Args:
            alignment: Intent alignment dict
            target_intent: Target page intent
            publisher_intent: Publisher intent
            serp_intent: SERP intent

        Returns:
            'strong' | 'pivot' | 'wrapper'
        """
        overall = alignment['overall']
        target_vs_serp = alignment['target_vs_serp']

        # Strong bridge: everything aligned
        if overall == 'aligned':
            return 'strong'

        # Wrapper: severe misalignment
        if overall == 'off':
            return 'wrapper'

        # Pivot: partial alignment, especially publisher = info, target = commercial
        if overall == 'partial':
            # Check if publisher is informational and target is commercial
            publisher_is_info = 'info' in publisher_intent
            target_is_commercial = 'transactional' in target_intent or 'commercial' in target_intent

            if publisher_is_info and target_is_commercial:
                return 'pivot'

        # Default to pivot for partial alignment
        return 'pivot'

    def _generate_article_angle(
        self,
        bridge_type: str,
        serp_intent: str,
        target_intent: str,
        publisher_intent: str,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any]
    ) -> str:
        """
        Generate recommended article angle.

        Args:
            bridge_type: Recommended bridge type
            serp_intent: SERP intent
            target_intent: Target intent
            publisher_intent: Publisher intent
            target_profile: Target profile
            publisher_profile: Publisher profile

        Returns:
            Article angle description
        """
        entities = target_profile.get('core_entities', ['the topic'])
        entity = entities[0] if entities else 'the topic'

        if bridge_type == 'strong':
            return f"Direct guide about {entity} that naturally integrates the target as primary resource."

        elif bridge_type == 'pivot':
            return (
                f"Informational guide about {entity} that establishes context and "
                f"naturally introduces the target as a relevant solution."
            )

        else:  # wrapper
            return (
                f"Comprehensive resource about {entity} where the target is one of "
                f"several mentioned options, requiring extensive contextual wrapping."
            )

    def _identify_required_subtopics(
        self,
        serp_research: Dict[str, Any],
        target_profile: Dict[str, Any],
        bridge_type: str
    ) -> List[str]:
        """
        Identify required subtopics to cover.

        Args:
            serp_research: SERP research results
            target_profile: Target profile
            bridge_type: Bridge type

        Returns:
            List of required subtopics
        """
        subtopics = set()

        # Add subtopics from SERP
        for serp_set in serp_research.get('serp_sets', []):
            serp_subtopics = serp_set.get('subtopics', [])
            subtopics.update(serp_subtopics[:3])  # Top 3 from each set

        # Add core topics from target
        target_topics = target_profile.get('core_topics', [])
        subtopics.update(target_topics[:3])

        # For pivot/wrapper, add more context subtopics
        if bridge_type in ['pivot', 'wrapper']:
            subtopics.add('background information')
            subtopics.add('context and overview')

        return list(subtopics)[:10]  # Max 10

    def _identify_forbidden_angles(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        alignment: Dict[str, str]
    ) -> List[str]:
        """
        Identify forbidden angles/approaches.

        Args:
            target_profile: Target profile
            publisher_profile: Publisher profile
            alignment: Intent alignment

        Returns:
            List of forbidden angles
        """
        forbidden = []

        # Check publisher tone
        tone = publisher_profile.get('tone_class', '')
        if tone in ['academic', 'authority_public']:
            forbidden.append('aggressive sales copy')
            forbidden.append('unsubstantiated claims')

        # Check commerciality
        commerciality = publisher_profile.get('allowed_commerciality', 'medium')
        if commerciality == 'low':
            forbidden.append('direct product promotion')
            forbidden.append('call-to-action language')

        # Check alignment issues
        if alignment['overall'] == 'off':
            forbidden.append('forced connections to target')

        # Add brand safety notes
        brand_safety = publisher_profile.get('brand_safety_notes', '')
        if brand_safety and 'auto-generated' not in brand_safety.lower():
            forbidden.append(f"violating: {brand_safety}")

        return forbidden

    def _generate_rationale(
        self,
        serp_intent: str,
        target_intent: str,
        publisher_intent: str,
        alignment: Dict[str, str],
        bridge_type: str
    ) -> str:
        """
        Generate rationale for intent analysis.

        Args:
            serp_intent: SERP intent
            target_intent: Target intent
            publisher_intent: Publisher intent
            alignment: Alignment dict
            bridge_type: Bridge type

        Returns:
            Rationale string
        """
        return (
            f"SERP shows {serp_intent} intent, target is {target_intent}, "
            f"publisher role is {publisher_intent}. "
            f"Overall alignment: {alignment['overall']}. "
            f"Recommended {bridge_type} bridge to connect all elements naturally."
        )

    def _determine_confidence(
        self,
        serp_confidence: str,
        alignment: Dict[str, str]
    ) -> str:
        """
        Determine overall data confidence.

        Args:
            serp_confidence: SERP data confidence
            alignment: Intent alignment

        Returns:
            'high' | 'medium' | 'low'
        """
        # Start with SERP confidence
        if serp_confidence == 'low':
            return 'low'

        # Reduce if alignment is poor
        if alignment['overall'] == 'off':
            return 'low'
        elif alignment['overall'] == 'partial':
            return 'medium'
        else:
            return serp_confidence
