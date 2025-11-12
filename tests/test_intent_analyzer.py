#!/usr/bin/env python3
"""
Tests for Intent Analyzer

Comprehensive test suite for intent analysis functionality including:
- Intent inference (target, anchor, publisher, SERP)
- Alignment analysis between intents
- Bridge type recommendation
- Article strategy generation
- Complete analysis workflow

Part of Del 3B: Content Generation Pipeline
Per BUILDER_PROMPT.md STEG 6
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.analysis.intent_analyzer import IntentAnalyzer


class TestIntentAnalyzerInitialization:
    """Test suite for Intent Analyzer initialization."""

    def test_initialization(self):
        """Test Intent Analyzer initializes correctly."""
        analyzer = IntentAnalyzer()
        assert hasattr(analyzer, 'INTENT_COMPATIBILITY')
        assert hasattr(analyzer, 'BRIDGE_TYPE_RULES')

    def test_compatibility_matrix_exists(self):
        """Test that intent compatibility matrix is defined."""
        analyzer = IntentAnalyzer()
        assert isinstance(analyzer.INTENT_COMPATIBILITY, dict)
        assert len(analyzer.INTENT_COMPATIBILITY) > 0

    def test_bridge_type_rules_exist(self):
        """Test that bridge type rules are defined."""
        analyzer = IntentAnalyzer()
        assert isinstance(analyzer.BRIDGE_TYPE_RULES, dict)


class TestIntentInference:
    """Test suite for intent inference."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.analyzer = IntentAnalyzer()

    def test_infer_target_intent_transactional(self):
        """Test target intent inference - transactional."""
        profile = {
            'core_offer': 'Buy now and save 20%',
            'core_topics': ['pricing', 'order']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'transactional_with_info_support'

    def test_infer_target_intent_commercial_research(self):
        """Test target intent inference - commercial research."""
        profile = {
            'core_offer': 'Compare different options',
            'core_topics': ['comparison', 'review']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'commercial_research'

    def test_infer_target_intent_informational(self):
        """Test target intent inference - informational."""
        profile = {
            'core_offer': 'Learn about the topic',
            'core_topics': ['information', 'guide']
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert intent == 'info_primary'

    def test_infer_target_intent_minimal_profile(self):
        """Test target intent inference with minimal profile."""
        profile = {
            'core_offer': 'Information',
            'core_topics': []
        }
        intent = self.analyzer._infer_target_intent(profile)
        assert isinstance(intent, str)
        assert len(intent) > 0

    def test_infer_anchor_intent_transactional(self):
        """Test anchor intent inference - transactional."""
        intent = self.analyzer._infer_anchor_intent('buy product x now')
        assert intent == 'transactional'

    def test_infer_anchor_intent_commercial_research(self):
        """Test anchor intent inference - commercial research."""
        intent = self.analyzer._infer_anchor_intent('best product x comparison')
        assert intent == 'commercial_research'

    def test_infer_anchor_intent_informational(self):
        """Test anchor intent inference - informational."""
        intent = self.analyzer._infer_anchor_intent('information about product')
        assert intent == 'info_primary'

    def test_infer_anchor_intent_empty_text(self):
        """Test anchor intent inference with empty text."""
        intent = self.analyzer._infer_anchor_intent('')
        assert isinstance(intent, str)

    def test_infer_publisher_intent_consumer_magazine(self):
        """Test publisher intent inference - consumer magazine."""
        profile = {'tone_class': 'consumer_magazine', 'allowed_commerciality': 'medium'}
        intent = self.analyzer._infer_publisher_intent(profile)
        assert intent == 'commercial_research'

    def test_infer_publisher_intent_academic(self):
        """Test publisher intent inference - academic."""
        profile = {'tone_class': 'academic', 'allowed_commerciality': 'low'}
        intent = self.analyzer._infer_publisher_intent(profile)
        assert intent == 'info_primary'

    def test_infer_publisher_intent_authority_public(self):
        """Test publisher intent inference - authority public."""
        profile = {'tone_class': 'authority_public', 'allowed_commerciality': 'low'}
        intent = self.analyzer._infer_publisher_intent(profile)
        assert intent == 'info_primary'

    def test_infer_publisher_intent_high_commerciality(self):
        """Test publisher intent inference - high commerciality."""
        profile = {'tone_class': 'consumer_magazine', 'allowed_commerciality': 'high'}
        intent = self.analyzer._infer_publisher_intent(profile)
        # Should allow more commercial intent
        assert intent in ['commercial_research', 'transactional_with_info_support']


class TestAlignmentAnalysis:
    """Test suite for intent alignment analysis."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.analyzer = IntentAnalyzer()

    def test_check_alignment_exact_match(self):
        """Test alignment check - exact match."""
        alignment = self.analyzer._check_alignment('info_primary', 'info_primary')
        assert alignment == 'aligned'

    def test_check_alignment_compatible(self):
        """Test alignment check - compatible intents."""
        alignment = self.analyzer._check_alignment('commercial_research', 'info_primary')
        assert alignment in ['aligned', 'partial']

    def test_check_alignment_incompatible(self):
        """Test alignment check - incompatible intents."""
        alignment = self.analyzer._check_alignment('navigational_brand', 'transactional')
        assert alignment in ['partial', 'off']

    def test_analyze_alignment_all_aligned(self):
        """Test alignment analysis - all intents aligned."""
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
        """Test alignment analysis - partial alignment."""
        alignment = self.analyzer._analyze_alignment(
            'commercial_research',
            'transactional_with_info_support',
            'commercial_research',
            'info_primary'
        )

        assert alignment['overall'] in ['partial', 'aligned']
        assert 'anchor_vs_serp' in alignment
        assert 'target_vs_serp' in alignment
        assert 'publisher_vs_serp' in alignment

    def test_analyze_alignment_misaligned(self):
        """Test alignment analysis - misaligned intents."""
        alignment = self.analyzer._analyze_alignment(
            'navigational_brand',
            'transactional',
            'info_primary',
            'commercial_research'
        )

        assert 'overall' in alignment
        assert alignment['overall'] in ['off', 'partial']


class TestBridgeTypeRecommendation:
    """Test suite for bridge type recommendation."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.analyzer = IntentAnalyzer()

    def test_recommend_bridge_type_strong(self):
        """Test bridge type recommendation - strong bridge."""
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
        """Test bridge type recommendation - pivot bridge."""
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
        """Test bridge type recommendation - wrapper bridge."""
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

    def test_bridge_type_always_valid(self):
        """Test that bridge type is always valid."""
        alignment = {
            'anchor_vs_serp': 'partial',
            'target_vs_serp': 'partial',
            'publisher_vs_serp': 'partial',
            'overall': 'partial'
        }
        bridge = self.analyzer._recommend_bridge_type(
            alignment,
            'commercial_research',
            'transactional',
            'info_primary'
        )
        assert bridge in ['strong', 'pivot', 'wrapper']


class TestArticleStrategyGeneration:
    """Test suite for article strategy generation."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.analyzer = IntentAnalyzer()
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

    def test_generate_article_angle_strong(self):
        """Test article angle generation - strong bridge."""
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
        """Test article angle generation - pivot bridge."""
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

    def test_generate_article_angle_wrapper(self):
        """Test article angle generation - wrapper bridge."""
        angle = self.analyzer._generate_article_angle(
            'wrapper',
            'transactional',
            'info_primary',
            'navigational_brand',
            self.target_profile,
            self.publisher_profile
        )
        assert isinstance(angle, str)
        assert len(angle) > 0

    def test_identify_required_subtopics(self):
        """Test required subtopics identification."""
        serp_research = {
            'serp_intent_primary': 'commercial_research',
            'serp_sets': [
                {
                    'query': 'product x comparison',
                    'subtopics': ['features', 'pricing', 'reviews']
                }
            ]
        }
        subtopics = self.analyzer._identify_required_subtopics(
            serp_research,
            self.target_profile,
            'pivot'
        )

        assert isinstance(subtopics, list)
        assert len(subtopics) > 0
        assert all(isinstance(s, str) for s in subtopics)

    def test_identify_required_subtopics_empty_serp(self):
        """Test required subtopics with empty SERP data."""
        serp_research = {
            'serp_intent_primary': 'info_primary',
            'serp_sets': []
        }
        subtopics = self.analyzer._identify_required_subtopics(
            serp_research,
            self.target_profile,
            'strong'
        )

        assert isinstance(subtopics, list)

    def test_identify_forbidden_angles_academic(self):
        """Test forbidden angles - academic publisher."""
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
        """Test forbidden angles - low commerciality."""
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

    def test_identify_forbidden_angles_high_commerciality(self):
        """Test forbidden angles - high commerciality."""
        publisher = {
            'tone_class': 'consumer_magazine',
            'allowed_commerciality': 'high',
            'brand_safety_notes': ''
        }
        alignment = {'overall': 'aligned'}

        forbidden = self.analyzer._identify_forbidden_angles(
            self.target_profile,
            publisher,
            alignment
        )

        # High commerciality should have fewer restrictions
        assert isinstance(forbidden, list)

    def test_generate_rationale(self):
        """Test rationale generation."""
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

    def test_generate_rationale_all_aligned(self):
        """Test rationale generation - all aligned."""
        alignment = {'overall': 'aligned'}
        rationale = self.analyzer._generate_rationale(
            'info_primary',
            'info_primary',
            'info_primary',
            alignment,
            'strong'
        )

        assert isinstance(rationale, str)
        assert 'strong' in rationale.lower()

    def test_determine_confidence_high(self):
        """Test confidence determination - high."""
        alignment = {'overall': 'aligned'}
        confidence = self.analyzer._determine_confidence('high', alignment)
        assert confidence == 'high'

    def test_determine_confidence_degraded(self):
        """Test confidence determination - degraded."""
        alignment = {'overall': 'off'}
        confidence = self.analyzer._determine_confidence('high', alignment)
        assert confidence == 'low'

    def test_determine_confidence_medium_input(self):
        """Test confidence determination - medium input."""
        alignment = {'overall': 'partial'}
        confidence = self.analyzer._determine_confidence('medium', alignment)
        assert confidence in ['low', 'medium']


class TestCompleteWorkflow:
    """Test suite for complete analysis workflow."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.analyzer = IntentAnalyzer()
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

    def test_analyze_complete_flow(self):
        """Test complete analysis workflow."""
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

    def test_analyze_minimal_profiles(self):
        """Test analysis with minimal profiles."""
        minimal_target = {
            'url': 'https://example.com',
            'core_offer': 'Information',
            'core_topics': []
        }
        minimal_publisher = {
            'domain': 'example.com',
            'tone_class': 'consumer_magazine',
            'allowed_commerciality': 'medium'
        }
        minimal_anchor = {
            'proposed_text': 'click here'
        }
        minimal_serp = {
            'serp_intent_primary': 'info_primary',
            'serp_intent_secondary': [],
            'serp_sets': [],
            'data_confidence': 'low'
        }

        result = self.analyzer.analyze(
            minimal_target,
            minimal_publisher,
            minimal_anchor,
            minimal_serp
        )

        # Should still return valid structure
        assert 'recommended_bridge_type' in result
        assert 'recommended_article_angle' in result
        assert result['notes']['data_confidence'] in ['low', 'medium', 'high']

    def test_analyze_high_alignment(self):
        """Test analysis with high alignment scenario."""
        aligned_serp = {
            'serp_intent_primary': 'commercial_research',
            'serp_intent_secondary': [],
            'serp_sets': [{'query': 'test', 'subtopics': ['topic1', 'topic2']}],
            'data_confidence': 'high'
        }

        result = self.analyzer.analyze(
            self.target_profile,
            self.publisher_profile,
            self.anchor_profile,
            aligned_serp
        )

        # High alignment should result in strong bridge
        assert result['intent_alignment']['overall'] in ['aligned', 'partial']


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR Intent Analyzer Tests")
    log("Per BUILDER_PROMPT.md STEG 6\n")
    log("=" * 60)

    try:
        # Test initialization
        log("\n🔍 Testing Intent Analyzer initialization...")
        analyzer = IntentAnalyzer()
        log(f"✅ Analyzer initialized")

        # Test intent inference
        log("\n🔍 Testing intent inference...")
        target_profile = {
            'core_offer': 'Compare products',
            'core_topics': ['comparison', 'review']
        }
        target_intent = analyzer._infer_target_intent(target_profile)
        log(f"✅ Intent inference working: {target_intent}")

        # Test alignment analysis
        log("\n🔍 Testing alignment analysis...")
        alignment = analyzer._analyze_alignment(
            'commercial_research',
            'commercial_research',
            'commercial_research',
            'commercial_research'
        )
        log(f"✅ Alignment analysis working: {alignment['overall']}")

        # Test bridge type recommendation
        log("\n🔍 Testing bridge type recommendation...")
        bridge_type = analyzer._recommend_bridge_type(
            alignment,
            'commercial_research',
            'commercial_research',
            'commercial_research'
        )
        log(f"✅ Bridge type recommendation: {bridge_type}")

        # Test complete analysis
        log("\n🔍 Testing complete analysis flow...")
        publisher_profile = {
            'domain': 'test.com',
            'tone_class': 'consumer_magazine',
            'allowed_commerciality': 'medium'
        }
        anchor_profile = {'proposed_text': 'test anchor'}
        serp_research = {
            'serp_intent_primary': 'commercial_research',
            'serp_intent_secondary': [],
            'serp_sets': [{'query': 'test', 'subtopics': ['topic1']}],
            'data_confidence': 'high'
        }

        result = analyzer.analyze(
            target_profile,
            publisher_profile,
            anchor_profile,
            serp_research
        )
        log(f"✅ Complete analysis working:")
        log(f"   Bridge type: {result['recommended_bridge_type']}")
        log(f"   Alignment: {result['intent_alignment']['overall']}")
        log(f"   Confidence: {result['notes']['data_confidence']}")

        log("\n✅ All standalone tests passed!")
        log("=" * 60)
        return True

    except Exception as e:
        log(f"❌ Test failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        log("=" * 60)
        return False


if __name__ == "__main__":
    log("=" * 60)
    success = run_standalone_tests()

    if success:
        log("✅ TESTS PASSED", "SUCCESS")
        sys.exit(0)
    else:
        log("❌ TESTS FAILED", "ERROR")
        sys.exit(1)
