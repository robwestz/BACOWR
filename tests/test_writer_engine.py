"""
Tests for Writer Engine

Del 3B: Content Generation Pipeline
"""

import pytest
from src.writer.writer_engine import WriterEngine


class TestWriterEngine:
    """Test suite for Writer Engine"""

    def setup_method(self):
        """Setup test fixtures"""
        self.engine = WriterEngine(mock_mode=True)

        # Sample job package
        self.job_package = {
            'job_meta': {
                'job_id': 'test-job-001',
                'created_at': '2025-11-07T12:00:00Z',
                'spec_version': 'Next-A1-SERP-First-v1'
            },
            'input_minimal': {
                'publisher_domain': 'example-publisher.com',
                'target_url': 'https://client.com/product-x',
                'anchor_text': 'bästa valet för tema'
            },
            'publisher_profile': {
                'domain': 'example-publisher.com',
                'tone_class': 'consumer_magazine',
                'detected_language': 'sv'
            },
            'target_profile': {
                'url': 'https://client.com/product-x',
                'title': 'Product X - Best Solution',
                'core_entities': ['Product X', 'Solutions'],
                'core_topics': ['comparison', 'features'],
                'core_offer': 'Complete solution for your needs'
            },
            'anchor_profile': {
                'proposed_text': 'bästa valet för tema',
                'llm_classified_type': 'partial'
            },
            'serp_research_extension': {
                'main_query': 'product x comparison',
                'cluster_queries': ['product x review'],
                'serp_sets': [
                    {
                        'query': 'product x comparison',
                        'subtopics': ['features', 'pricing', 'quality']
                    }
                ],
                'data_confidence': 'medium'
            },
            'intent_extension': {
                'serp_intent_primary': 'commercial_research',
                'target_page_intent': 'transactional',
                'publisher_role_intent': 'commercial_research',
                'recommended_bridge_type': 'pivot',
                'recommended_article_angle': 'Informational guide',
                'required_subtopics': ['features', 'benefits', 'comparison'],
                'forbidden_angles': ['aggressive sales']
            },
            'generation_constraints': {
                'language': 'sv',
                'min_word_count': 900,
                'max_anchor_usages': 2,
                'anchor_policy': 'No anchor in H1/H2, middle section'
            }
        }

    def test_initialization_mock_mode(self):
        """Test initialization in mock mode"""
        engine = WriterEngine(mock_mode=True)
        assert engine.mock_mode is True
        assert engine.llm_provider == 'anthropic'

    def test_initialization_with_provider(self):
        """Test initialization with specific provider"""
        engine = WriterEngine(mock_mode=True, llm_provider='openai')
        assert engine.llm_provider == 'openai'

    def test_generate_mock_article(self):
        """Test mock article generation"""
        article = self.engine.generate(self.job_package)

        assert isinstance(article, str)
        assert len(article) > 100
        assert '# ' in article  # Has markdown heading
        assert 'Product X' in article or 'topic' in article
        # Should contain link
        assert self.job_package['input_minimal']['target_url'] in article

    def test_generate_strong_bridge_mock(self):
        """Test strong bridge article generation"""
        job_package = self.job_package.copy()
        job_package['intent_extension']['recommended_bridge_type'] = 'strong'

        article = self.engine._generate_strong_bridge_mock(
            job_package,
            job_package['input_minimal']['target_url'],
            job_package['input_minimal']['anchor_text'],
            ['kvalitet', 'fördelar', 'jämförelse', 'alternativ', 'guide', 'tips', 'råd', 'erfarenheter'],
            'sv'
        )

        assert isinstance(article, str)
        assert len(article) > 100
        assert 'Product X' in article
        assert 'kvalitet' in article  # LSI term
        assert job_package['input_minimal']['target_url'] in article

    def test_generate_pivot_bridge_mock(self):
        """Test pivot bridge article generation"""
        job_package = self.job_package.copy()

        article = self.engine._generate_pivot_bridge_mock(
            job_package,
            job_package['input_minimal']['target_url'],
            job_package['input_minimal']['anchor_text'],
            ['kvalitet', 'fördelar', 'jämförelse', 'alternativ', 'guide', 'tips', 'råd', 'erfarenheter'],
            'sv'
        )

        assert isinstance(article, str)
        assert len(article) > 100
        assert 'Product X' in article
        assert job_package['input_minimal']['target_url'] in article

    def test_generate_wrapper_bridge_mock(self):
        """Test wrapper bridge article generation"""
        job_package = self.job_package.copy()

        article = self.engine._generate_wrapper_bridge_mock(
            job_package,
            job_package['input_minimal']['target_url'],
            job_package['input_minimal']['anchor_text'],
            ['kvalitet', 'fördelar', 'jämförelse', 'alternativ', 'guide', 'tips', 'råd', 'erfarenheter'],
            'sv'
        )

        assert isinstance(article, str)
        assert len(article) > 100

    def test_select_lsi_terms_swedish(self):
        """Test LSI term selection for Swedish"""
        job_package = self.job_package.copy()
        job_package['generation_constraints']['language'] = 'sv'

        lsi_terms = self.engine._select_lsi_terms(job_package, num_terms=8)

        assert isinstance(lsi_terms, list)
        assert len(lsi_terms) <= 8
        assert all(isinstance(term, str) for term in lsi_terms)

    def test_select_lsi_terms_english(self):
        """Test LSI term selection for English"""
        job_package = self.job_package.copy()
        job_package['generation_constraints']['language'] = 'en'

        lsi_terms = self.engine._select_lsi_terms(job_package, num_terms=8)

        assert isinstance(lsi_terms, list)
        assert len(lsi_terms) <= 8
        # Should have English terms
        assert any(term in ['quality', 'benefits', 'comparison'] for term in lsi_terms)

    def test_build_llm_prompt(self):
        """Test LLM prompt building"""
        prompt = self.engine._build_llm_prompt(self.job_package)

        assert isinstance(prompt, str)
        assert len(prompt) > 100
        assert 'Product X' in prompt
        assert 'pivot' in prompt.lower()
        assert 'sv' in prompt or 'swedish' in prompt.lower()
        assert str(self.job_package['generation_constraints']['min_word_count']) in prompt

    def test_lsi_library_exists(self):
        """Test that LSI library is defined"""
        assert hasattr(WriterEngine, 'LSI_LIBRARY')
        assert 'sv' in WriterEngine.LSI_LIBRARY
        assert 'en' in WriterEngine.LSI_LIBRARY
        assert isinstance(WriterEngine.LSI_LIBRARY['sv']['generic'], list)
        assert isinstance(WriterEngine.LSI_LIBRARY['en']['generic'], list)

    def test_generate_english_article(self):
        """Test English article generation"""
        job_package = self.job_package.copy()
        job_package['generation_constraints']['language'] = 'en'
        job_package['intent_extension']['recommended_bridge_type'] = 'strong'

        article = self.engine.generate(job_package)

        assert isinstance(article, str)
        assert len(article) > 100
        # Should be in English (check for English words)
        assert any(word in article.lower() for word in ['the', 'and', 'is', 'guide'])


def test_writer_engine_has_required_methods():
    """Test that Writer Engine has all required methods"""
    engine = WriterEngine(mock_mode=True)

    assert hasattr(engine, 'generate')
    assert hasattr(engine, '_generate_mock_article')
    assert hasattr(engine, '_generate_llm_article')
    assert hasattr(engine, '_build_llm_prompt')
    assert hasattr(engine, '_select_lsi_terms')
    assert hasattr(engine, '_generate_strong_bridge_mock')
    assert hasattr(engine, '_generate_pivot_bridge_mock')
    assert hasattr(engine, '_generate_wrapper_bridge_mock')


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
