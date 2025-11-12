#!/usr/bin/env python3
"""
Tests for SERP Researcher

Comprehensive test suite for SERP research functionality including:
- Query generation (main and cluster queries)
- SERP fetching (mock and API modes)
- Intent classification (query and SERP level)
- Subtopic extraction
- Complete research workflow

Part of Del 3B: Content Generation Pipeline
Per BUILDER_PROMPT.md STEG 5
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.research.serp_researcher import SERPResearcher


class TestSERPResearcherInitialization:
    """Test suite for SERP Researcher initialization."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        researcher = SERPResearcher()
        assert researcher.mock_mode is True
        assert researcher.api_key is None
        assert hasattr(researcher, 'INTENT_PATTERNS')

    def test_initialization_with_api_key(self):
        """Test initialization with API key."""
        researcher = SERPResearcher(api_key='test_key', mock_mode=False)
        assert researcher.api_key == 'test_key'
        assert researcher.mock_mode is False

    def test_initialization_mock_mode(self):
        """Test initialization in mock mode."""
        researcher = SERPResearcher(mock_mode=True)
        assert researcher.mock_mode is True
        assert researcher.api_key is None

    def test_intent_patterns_exist(self):
        """Test that intent patterns are defined correctly."""
        researcher = SERPResearcher()
        assert hasattr(researcher, 'INTENT_PATTERNS')
        assert 'commercial_research' in researcher.INTENT_PATTERNS
        assert 'transactional' in researcher.INTENT_PATTERNS
        assert 'info_primary' in researcher.INTENT_PATTERNS
        assert 'navigational_brand' in researcher.INTENT_PATTERNS

        # Check that patterns have content
        assert len(researcher.INTENT_PATTERNS['commercial_research']) > 0
        assert len(researcher.INTENT_PATTERNS['transactional']) > 0


class TestQueryGeneration:
    """Test suite for query generation."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.researcher = SERPResearcher(mock_mode=True)
        self.target_profile = {
            'url': 'https://example.com/product-x',
            'title': 'Product X - Best Solution for Your Needs',
            'core_entities': ['Product X', 'Solutions'],
            'core_topics': ['comparison', 'features', 'benefits'],
            'candidate_main_queries': ['product x comparison', 'product x review']
        }

    def test_generate_queries_complete(self):
        """Test complete query generation."""
        main_query, cluster_queries, rationale = self.researcher.generate_queries(
            self.target_profile,
            'best product x'
        )

        assert isinstance(main_query, str)
        assert len(main_query) > 0
        assert isinstance(cluster_queries, list)
        assert len(cluster_queries) > 0
        assert isinstance(rationale, str)
        assert len(rationale) > 0

    def test_generate_main_query_from_candidates(self):
        """Test main query generation from candidate queries."""
        main_query = self.researcher._generate_main_query(
            ['Product X'],
            ['comparison'],
            'Product X Review',
            ['product x comparison', 'product x test']
        )

        # Should use first candidate
        assert main_query == 'product x comparison'

    def test_generate_main_query_from_entities_topics(self):
        """Test main query generation from entities and topics."""
        main_query = self.researcher._generate_main_query(
            ['Product X'],
            ['comparison'],
            'Product X Review',
            []  # No candidates
        )

        assert 'product x' in main_query.lower()
        assert 'comparison' in main_query.lower()

    def test_generate_main_query_from_title_only(self):
        """Test main query generation with only title."""
        main_query = self.researcher._generate_main_query(
            [],  # No entities
            [],  # No topics
            'Product X Review Guide Tips',
            []  # No candidates
        )

        assert isinstance(main_query, str)
        assert len(main_query) > 0

    def test_generate_main_query_fallback(self):
        """Test main query generation fallback."""
        main_query = self.researcher._generate_main_query(
            [],
            [],
            '',
            []
        )

        assert main_query == "relevant information"

    def test_generate_cluster_queries(self):
        """Test cluster query generation."""
        cluster_queries = self.researcher._generate_cluster_queries(
            ['Product X'],
            ['features', 'benefits'],
            'best product x',
            max_queries=3
        )

        assert isinstance(cluster_queries, list)
        assert len(cluster_queries) <= 3
        assert all(isinstance(q, str) for q in cluster_queries)
        # Should contain product x in at least one query
        assert any('product x' in q.lower() for q in cluster_queries)

    def test_generate_cluster_queries_max_limit(self):
        """Test cluster query max limit enforcement."""
        cluster_queries = self.researcher._generate_cluster_queries(
            ['Product X', 'Product Y'],
            ['features', 'benefits', 'price', 'quality'],
            'product comparison',
            max_queries=2
        )

        assert len(cluster_queries) == 2

    def test_generate_cluster_queries_empty_inputs(self):
        """Test cluster query generation with empty inputs."""
        cluster_queries = self.researcher._generate_cluster_queries(
            [],
            [],
            'anchor text',
            max_queries=3
        )

        # Should return empty list when no entities or topics
        assert isinstance(cluster_queries, list)


class TestIntentClassification:
    """Test suite for intent classification."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.researcher = SERPResearcher(mock_mode=True)

    def test_classify_query_intent_commercial_research(self):
        """Test query intent classification - commercial research."""
        intent = self.researcher._classify_query_intent('product x jämförelse test')
        assert intent == 'commercial_research'

    def test_classify_query_intent_transactional(self):
        """Test query intent classification - transactional."""
        intent = self.researcher._classify_query_intent('köp product x bästa pris')
        assert intent == 'transactional'

    def test_classify_query_intent_informational(self):
        """Test query intent classification - informational."""
        intent = self.researcher._classify_query_intent('vad är product x')
        assert intent == 'info_primary'

    def test_classify_query_intent_navigational(self):
        """Test query intent classification - navigational."""
        intent = self.researcher._classify_query_intent('product x login official website')
        assert intent == 'navigational_brand'

    def test_classify_query_intent_default(self):
        """Test query intent classification defaults to info_primary."""
        intent = self.researcher._classify_query_intent('random text without keywords')
        assert intent == 'info_primary'

    def test_classify_serp_intent(self):
        """Test SERP intent classification from results."""
        # Mock SERP results
        serp_results = [
            {
                'title': 'Product X Review and Comparison',
                'snippet': 'Compare the best options for Product X',
                'type': 'review'
            },
            {
                'title': 'Product X Guide',
                'snippet': 'Learn how to use Product X effectively',
                'type': 'informational'
            },
            {
                'title': 'Buy Product X - Best Price',
                'snippet': 'Shop now for Product X with great deals',
                'type': 'commercial'
            }
        ]

        primary, secondary = self.researcher.classify_serp_intent(serp_results)

        assert isinstance(primary, str)
        assert isinstance(secondary, list)
        assert primary in ['transactional', 'commercial_research', 'info_primary', 'navigational_brand']

    def test_classify_serp_intent_empty_results(self):
        """Test SERP intent classification with empty results."""
        primary, secondary = self.researcher.classify_serp_intent([])

        assert isinstance(primary, str)
        assert isinstance(secondary, list)


class TestSERPFetching:
    """Test suite for SERP fetching."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.researcher = SERPResearcher(mock_mode=True)

    def test_fetch_serp_mock_mode(self):
        """Test SERP fetching in mock mode."""
        results = self.researcher.fetch_serp('product x review', num_results=10)

        assert isinstance(results, list)
        assert len(results) == 10

        # Check structure of first result
        result = results[0]
        assert 'position' in result
        assert 'title' in result
        assert 'url' in result
        assert 'snippet' in result
        assert 'domain' in result
        assert 'type' in result

    def test_fetch_serp_custom_num_results(self):
        """Test SERP fetching with custom number of results."""
        results = self.researcher.fetch_serp('test query', num_results=5)

        assert len(results) == 5

    def test_fetch_serp_real_mode_not_implemented(self):
        """Test that real API mode raises NotImplementedError."""
        researcher = SERPResearcher(api_key='test', mock_mode=False)

        with pytest.raises(NotImplementedError):
            researcher.fetch_serp('query')

    def test_mock_serp_results_structure(self):
        """Test mock SERP results have correct structure."""
        results = self.researcher._mock_serp_results('test query', 3)

        assert len(results) == 3

        for i, result in enumerate(results):
            assert result['position'] == i + 1
            assert 'test query' in result['title'].lower()
            assert 'https://' in result['url']
            assert len(result['snippet']) > 0
            assert len(result['domain']) > 0
            assert result['type'] in ['commercial', 'review', 'informational']

    def test_infer_result_type_transactional(self):
        """Test result type inference for transactional queries."""
        # Top positions should be commercial
        result_type = self.researcher._infer_result_type(1, 'transactional')
        assert result_type == 'commercial'

        # Lower positions should be informational
        result_type = self.researcher._infer_result_type(5, 'transactional')
        assert result_type == 'informational'

    def test_infer_result_type_commercial_research(self):
        """Test result type inference for commercial research queries."""
        # Top positions should be review
        result_type = self.researcher._infer_result_type(2, 'commercial_research')
        assert result_type == 'review'

        # Lower positions should be informational
        result_type = self.researcher._infer_result_type(8, 'commercial_research')
        assert result_type == 'informational'

    def test_infer_result_type_informational(self):
        """Test result type inference for informational queries."""
        result_type = self.researcher._infer_result_type(0, 'info_primary')
        assert result_type == 'informational'


class TestSubtopicExtraction:
    """Test suite for subtopic extraction."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.researcher = SERPResearcher(mock_mode=True)

    def test_extract_subtopics(self):
        """Test subtopic extraction from SERP results."""
        serp_results = [
            {
                'title': 'Product X Features and Benefits',
                'snippet': 'Explore the key features and benefits of Product X'
            },
            {
                'title': 'Product X Price Comparison',
                'snippet': 'Compare prices and find the best deal for Product X'
            },
            {
                'title': 'Product X Quality Guide',
                'snippet': 'Understanding quality factors in Product X'
            }
        ]

        subtopics = self.researcher.extract_subtopics(serp_results)

        assert isinstance(subtopics, list)
        assert len(subtopics) > 0
        assert all(isinstance(s, str) for s in subtopics)

    def test_extract_subtopics_max_limit(self):
        """Test subtopic extraction respects max limit."""
        serp_results = [
            {'title': f'Topic {i}', 'snippet': f'Content about topic {i}'}
            for i in range(20)
        ]

        subtopics = self.researcher.extract_subtopics(serp_results, max_subtopics=3)

        assert len(subtopics) <= 3

    def test_extract_subtopics_empty_results(self):
        """Test subtopic extraction with empty results."""
        subtopics = self.researcher.extract_subtopics([])

        assert isinstance(subtopics, list)


class TestCompleteResearchFlow:
    """Test suite for complete research workflow."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.researcher = SERPResearcher(mock_mode=True)
        self.target_profile = {
            'url': 'https://example.com/product-x',
            'title': 'Product X - Best Solution for Your Needs',
            'core_entities': ['Product X', 'Solutions'],
            'core_topics': ['comparison', 'features', 'benefits'],
            'candidate_main_queries': ['product x comparison', 'product x review']
        }

    def test_research_complete_flow(self):
        """Test complete research workflow."""
        result = self.researcher.research(
            self.target_profile,
            'best product x solution'
        )

        # Check structure
        assert 'main_query' in result
        assert 'cluster_queries' in result
        assert 'queries_rationale' in result
        assert 'serp_sets' in result
        assert 'serp_intent_primary' in result
        assert 'serp_intent_secondary' in result
        assert 'data_confidence' in result

        # Check content
        assert isinstance(result['main_query'], str)
        assert isinstance(result['cluster_queries'], list)
        assert isinstance(result['serp_sets'], list)
        assert len(result['serp_sets']) > 0

        # Check SERP set structure
        serp_set = result['serp_sets'][0]
        assert 'query' in serp_set
        assert 'query_type' in serp_set
        assert 'intent_primary' in serp_set
        assert 'intent_secondary' in serp_set
        assert 'results_count' in serp_set
        assert 'top_results' in serp_set
        assert 'subtopics' in serp_set
        assert 'fetched_at' in serp_set

        # Main query should be first
        assert result['serp_sets'][0]['query_type'] == 'main'

    def test_research_data_confidence(self):
        """Test data confidence reporting."""
        result = self.researcher.research(
            self.target_profile,
            'anchor text'
        )

        # Mock mode should report medium confidence
        assert result['data_confidence'] == 'medium'

    def test_research_serp_sets_structure(self):
        """Test SERP sets have correct structure."""
        result = self.researcher.research(
            self.target_profile,
            'anchor text',
            num_results=5
        )

        # Should have at least 1 SERP set (main query)
        assert len(result['serp_sets']) >= 1

        # Each SERP set should have top results
        for serp_set in result['serp_sets']:
            assert len(serp_set['top_results']) <= 3  # Top 3 stored
            assert serp_set['results_count'] == 5  # Total results requested

    def test_research_minimal_profile(self):
        """Test research with minimal target profile."""
        minimal_profile = {
            'url': 'https://example.com',
            'title': 'Example Page'
        }

        result = self.researcher.research(
            minimal_profile,
            'test anchor'
        )

        # Should still work with minimal data
        assert 'main_query' in result
        assert 'serp_sets' in result
        assert len(result['serp_sets']) > 0


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR SERP Researcher Tests")
    log("Per BUILDER_PROMPT.md STEG 5\n")
    log("=" * 60)

    try:
        # Test initialization
        log("\n🔍 Testing SERP Researcher initialization...")
        researcher = SERPResearcher(mock_mode=True)
        log(f"✅ Researcher initialized in mock mode")

        # Test query generation
        log("\n🔍 Testing query generation...")
        target_profile = {
            'title': 'Product X Review',
            'core_entities': ['Product X'],
            'core_topics': ['review', 'comparison'],
            'candidate_main_queries': ['product x review']
        }

        main_query, cluster_queries, rationale = researcher.generate_queries(
            target_profile, 'best product x'
        )
        log(f"✅ Query generation working:")
        log(f"   Main query: {main_query}")
        log(f"   Cluster queries: {len(cluster_queries)}")

        # Test SERP fetching
        log("\n🔍 Testing SERP fetching...")
        results = researcher.fetch_serp(main_query, num_results=10)
        log(f"✅ SERP fetching working: {len(results)} results")

        # Test complete research
        log("\n🔍 Testing complete research flow...")
        research_result = researcher.research(target_profile, 'anchor text')
        log(f"✅ Research flow working:")
        log(f"   Main query: {research_result['main_query']}")
        log(f"   SERP sets: {len(research_result['serp_sets'])}")
        log(f"   Intent: {research_result['serp_intent_primary']}")
        log(f"   Confidence: {research_result['data_confidence']}")

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
