"""
Tests for SERP Researcher

Del 3B: Content Generation Pipeline
"""

import pytest
from src.research.serp_researcher import SERPResearcher


class TestSERPResearcher:
    """Test suite for SERP Researcher"""

    def setup_method(self):
        """Setup test fixtures"""
        self.researcher = SERPResearcher(mock_mode=True)

        # Sample target profile
        self.target_profile = {
            'url': 'https://example.com/product-x',
            'title': 'Product X - Best Solution for Your Needs',
            'core_entities': ['Product X', 'Solutions'],
            'core_topics': ['comparison', 'features', 'benefits'],
            'candidate_main_queries': ['product x comparison', 'product x review']
        }

    def test_generate_queries(self):
        """Test query generation"""
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
        """Test main query generation from candidate queries"""
        main_query = self.researcher._generate_main_query(
            ['Product X'],
            ['comparison'],
            'Product X Review',
            ['product x comparison', 'product x test']
        )

        # Should use first candidate
        assert main_query == 'product x comparison'

    def test_generate_main_query_from_entities_topics(self):
        """Test main query generation from entities and topics"""
        main_query = self.researcher._generate_main_query(
            ['Product X'],
            ['comparison'],
            'Product X Review',
            []  # No candidates
        )

        assert 'product x' in main_query.lower()
        assert 'comparison' in main_query.lower()

    def test_generate_cluster_queries(self):
        """Test cluster query generation"""
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

    def test_fetch_serp_mock_mode(self):
        """Test SERP fetching in mock mode"""
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

    def test_classify_query_intent_commercial(self):
        """Test query intent classification - commercial"""
        intent = self.researcher._classify_query_intent('product x jämförelse test')
        assert intent == 'commercial_research'

    def test_classify_query_intent_transactional(self):
        """Test query intent classification - transactional"""
        intent = self.researcher._classify_query_intent('köp product x bästa pris')
        assert intent == 'transactional'

    def test_classify_query_intent_informational(self):
        """Test query intent classification - informational"""
        intent = self.researcher._classify_query_intent('vad är product x')
        assert intent == 'info_primary'

    def test_classify_serp_intent(self):
        """Test SERP intent classification"""
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

    def test_extract_subtopics(self):
        """Test subtopic extraction"""
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

    def test_research_complete_flow(self):
        """Test complete research flow"""
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

    def test_infer_result_type(self):
        """Test result type inference"""
        # Transactional intent
        result_type = self.researcher._infer_result_type(1, 'transactional')
        assert result_type in ['commercial', 'informational']

        # Commercial research intent
        result_type = self.researcher._infer_result_type(3, 'commercial_research')
        assert result_type in ['review', 'informational']

        # Informational intent
        result_type = self.researcher._infer_result_type(0, 'info_primary')
        assert result_type == 'informational'


def test_researcher_initialization():
    """Test SERP Researcher initialization"""
    researcher = SERPResearcher(mock_mode=True)
    assert researcher.mock_mode is True
    assert researcher.api_key is None

    researcher_with_key = SERPResearcher(api_key='test_key', mock_mode=False)
    assert researcher_with_key.api_key == 'test_key'
    assert researcher_with_key.mock_mode is False


def test_intent_patterns_exist():
    """Test that intent patterns are defined"""
    researcher = SERPResearcher()
    assert hasattr(researcher, 'INTENT_PATTERNS')
    assert 'commercial_research' in researcher.INTENT_PATTERNS
    assert 'transactional' in researcher.INTENT_PATTERNS
    assert 'info_primary' in researcher.INTENT_PATTERNS


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
