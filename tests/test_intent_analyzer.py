"""
Tests for Intent Analyzer

Del 3B: Content Generation Pipeline
"""

import pytest
from src.analysis.intent_analyzer import IntentAnalyzer


class TestIntentAnalyzer:
    """Test suite for Intent Analyzer"""

    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = IntentAnalyzer()

        # Sample profiles
        self.target_profile = {
            'url': 'https://example.com/product-x',
            'title': 'Product X - Buy Now',
            'core_entities': ['Product X'],
            'core_topics': ['pricing', 'features'],
            'core_offer': 'Buy Product X at best price'
        }

        self.publisher_profile = {
            'domain': 'example-publisher.com',
            'tone_class': 'consumer_magazine',
            'allowed_commerciality': 'medium',
            'brand_safety_notes': 'Auto-generated profile'
        }

        self.anchor_profile = {
            'proposed_text': 'best product x',
            'llm_classified_type': 'partial',
            'llm_intent_hint': 'commercial_research'
        }

        self.serp_research = {
            'serp_intent_primary': 'commercial_research',
            'serp_intent_secondary': ['info_primary'],
            'serp_sets': [
                {
                    'query': 'product x comparison',
                    'subtopics': ['features', 'pricing', 'reviews']
                }
            ],
            'data_confidence': 'medium'
        }

    def test_infer_target_intent_transactional(self):
        """Test target intent inference - transactional"""
        profile = {
            'core_offer': 'Buy now and save 20%',
            'core_topics': ['pricing', 'order']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'transactional_with_info_support'

    def test_infer_target_intent_commercial_research(self):
        """Test target intent inference - commercial research"""
        profile = {
            'core_offer': 'Compare different options',
            'core_topics': ['comparison', 'review']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'commercial_research'

    def test_infer_target_intent_informational(self):
        """Test target intent inference - informational"""
        profile = {
            'core_offer': 'Learn about the topic',
            'core_topics': ['information', 'guide']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'info_primary'

    def test_infer_anchor_intent_transactional(self):
        """Test anchor intent inference - transactional"""
        intent = self.analyzer._infer_anchor_intent('buy product x now')
        assert intent == 'transactional'

    def test_infer_anchor_intent_commercial(self):
        """Test anchor intent inference - commercial research"""
        intent = self.analyzer._infer_anchor_intent('best product x comparison')
        assert intent == 'commercial_research'

    def test_infer_anchor_intent_informational(self):
        """Test anchor intent inference - informational"""
        intent = self.analyzer._infer_anchor_intent('information about product')
        assert intent == 'info_primary'

    def test_infer_publisher_intent_consumer_magazine(self):
        """Test publisher intent inference - consumer magazine"""
        profile = {'tone_class': 'consumer_magazine', 'allowed_commerciality': 'medium'}
        intent = self.analyzer._infer_publisher_intent(profile)
        assert intent == 'commercial_research'

    def test_infer_publisher_intent_academic(self):
        """Test publisher intent inference - academic"""
        profile = {'tone_class': 'academic', 'allowed_commerciality': 'low'}
        intent = self.analyzer._infer_publisher_intent(profile)
        assert intent == 'info_primary'

    def test_check_alignment_exact_match(self):
        """Test alignment check - exact match"""
        alignment = self.analyzer._check_alignment('info_primary', 'info_primary')
        assert alignment == 'aligned'

    def test_check_alignment_compatible(self):
        """Test alignment check - compatible"""
        alignment = self.analyzer._check_alignment('commercial_research', 'info_primary')
        assert alignment in ['aligned', 'partial']

    def test_check_alignment_incompatible(self):
        """Test alignment check - incompatible"""
        alignment = self.analyzer._check_alignment('navigational_brand', 'transactional')
        assert alignment in ['partial', 'off']

    def test_analyze_alignment_all_aligned(self):
        """Test alignment analysis - all aligned"""
        alignment = self.analyzer._analyze_alignment(
            'info_primary',
            'info_primary',
            'info_primary',
            'info_primary'
        )

        assert alignment['anchor_vs_serp'] == 'aligned'
        assert alignment['target_vs_serp'] == 'aligned'
        assert alignment['publisher_vs_serp'] == 'aligned'
        assert alignment['overall'] == 'aligned'

    def test_analyze_alignment_partial(self):
        """Test alignment analysis - partial"""
        alignment = self.analyzer._analyze_alignment(
            'commercial_research',
            'transactional_with_info_support',
            'commercial_research',
            'info_primary'
        )

        assert alignment['overall'] in ['partial', 'aligned']

    def test_recommend_bridge_type_strong(self):
        """Test bridge type recommendation - strong"""
        alignment = {
            'anchor_vs_serp': 'aligned',
            'target_vs_serp': 'aligned',
            'publisher_vs_serp': 'aligned',
            'overall': 'aligned'
        }
        bridge = self.analyzer._recommend_bridge_type(
            alignment,
            'info_primary',
            'info_primary',
            'info_primary'
        )
        assert bridge == 'strong'

    def test_recommend_bridge_type_pivot(self):
        """Test bridge type recommendation - pivot"""
        alignment = {
            'anchor_vs_serp': 'partial',
            'target_vs_serp': 'partial',
            'publisher_vs_serp': 'aligned',
            'overall': 'partial'
        }
        bridge = self.analyzer._recommend_bridge_type(
            alignment,
            'transactional_with_info_support',
            'info_primary',
            'commercial_research'
        )
        assert bridge == 'pivot'

    def test_recommend_bridge_type_wrapper(self):
        """Test bridge type recommendation - wrapper"""
        alignment = {
            'anchor_vs_serp': 'off',
            'target_vs_serp': 'off',
            'publisher_vs_serp': 'off',
            'overall': 'off'
        }
        bridge = self.analyzer._recommend_bridge_type(
            alignment,
            'transactional',
            'info_primary',
            'navigational_brand'
        )
        assert bridge == 'wrapper'

    def test_generate_article_angle_strong(self):
        """Test article angle generation - strong bridge"""
        angle = self.analyzer._generate_article_angle(
            'strong',
            'info_primary',
            'info_primary',
            'info_primary',
            self.target_profile,
            self.publisher_profile
        )
        assert isinstance(angle, str)
        assert len(angle) > 0
        assert 'direct' in angle.lower()

    def test_generate_article_angle_pivot(self):
        """Test article angle generation - pivot bridge"""
        angle = self.analyzer._generate_article_angle(
            'pivot',
            'commercial_research',
            'transactional',
            'info_primary',
            self.target_profile,
            self.publisher_profile
        )
        assert isinstance(angle, str)
        assert 'informational' in angle.lower() or 'context' in angle.lower()

    def test_identify_required_subtopics(self):
        """Test required subtopics identification"""
        subtopics = self.analyzer._identify_required_subtopics(
            self.serp_research,
            self.target_profile,
            'pivot'
        )

        assert isinstance(subtopics, list)
        assert len(subtopics) > 0
        assert all(isinstance(s, str) for s in subtopics)

    def test_identify_forbidden_angles_academic(self):
        """Test forbidden angles - academic publisher"""
        publisher = {
            'tone_class': 'academic',
            'allowed_commerciality': 'low',
            'brand_safety_notes': ''
        }
        alignment = {'overall': 'aligned'}

        forbidden = self.analyzer._identify_forbidden_angles(
            self.target_profile,
            publisher,
            alignment
        )

        assert isinstance(forbidden, list)
        assert any('sales' in f.lower() or 'claim' in f.lower() for f in forbidden)

    def test_identify_forbidden_angles_low_commerciality(self):
        """Test forbidden angles - low commerciality"""
        publisher = {
            'tone_class': 'consumer_magazine',
            'allowed_commerciality': 'low',
            'brand_safety_notes': ''
        }
        alignment = {'overall': 'aligned'}

        forbidden = self.analyzer._identify_forbidden_angles(
            self.target_profile,
            publisher,
            alignment
        )

        assert isinstance(forbidden, list)
        assert any('promotion' in f.lower() or 'action' in f.lower() for f in forbidden)

    def test_generate_rationale(self):
        """Test rationale generation"""
        alignment = {'overall': 'partial'}
        rationale = self.analyzer._generate_rationale(
            'commercial_research',
            'transactional',
            'info_primary',
            alignment,
            'pivot'
        )

        assert isinstance(rationale, str)
        assert len(rationale) > 0
        assert 'SERP' in rationale
        assert 'pivot' in rationale.lower()

    def test_determine_confidence_high(self):
        """Test confidence determination - high"""
        alignment = {'overall': 'aligned'}
        confidence = self.analyzer._determine_confidence('high', alignment)
        assert confidence == 'high'

    def test_determine_confidence_degraded(self):
        """Test confidence determination - degraded"""
        alignment = {'overall': 'off'}
        confidence = self.analyzer._determine_confidence('high', alignment)
        assert confidence == 'low'

    def test_analyze_complete_flow(self):
        """Test complete analysis flow"""
        result = self.analyzer.analyze(
            self.target_profile,
            self.publisher_profile,
            self.anchor_profile,
            self.serp_research
        )

        # Check structure
        assert 'serp_intent_primary' in result
        assert 'serp_intent_secondary' in result
        assert 'target_page_intent' in result
        assert 'anchor_implied_intent' in result
        assert 'publisher_role_intent' in result
        assert 'intent_alignment' in result
        assert 'recommended_bridge_type' in result
        assert 'recommended_article_angle' in result
        assert 'required_subtopics' in result
        assert 'forbidden_angles' in result
        assert 'notes' in result

        # Check types
        assert isinstance(result['serp_intent_primary'], str)
        assert isinstance(result['serp_intent_secondary'], list)
        assert isinstance(result['intent_alignment'], dict)
        assert result['recommended_bridge_type'] in ['strong', 'pivot', 'wrapper']
        assert isinstance(result['required_subtopics'], list)
        assert isinstance(result['forbidden_angles'], list)

        # Check notes structure
        assert 'rationale' in result['notes']
        assert 'data_confidence' in result['notes']


def test_analyzer_initialization():
    """Test Intent Analyzer initialization"""
    analyzer = IntentAnalyzer()
    assert hasattr(analyzer, 'INTENT_COMPATIBILITY')
    assert hasattr(analyzer, 'BRIDGE_TYPE_RULES')


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
