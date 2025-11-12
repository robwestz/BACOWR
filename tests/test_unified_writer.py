"""
Tests for Unified Writer Engine

This test validates the consolidation of duplicate writer implementations
that were causing Gemini-related conflicts.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pytest
from writer.unified_writer import UnifiedWriterEngine, WriterEngine, ProductionWriter
from writer.unified_writer import LLMProvider, BridgeType, GenerationMetrics


class TestUnifiedWriter:
    """Test suite for unified writer engine"""

    def test_class_aliases(self):
        """Test that class aliases are properly set up"""
        assert WriterEngine is UnifiedWriterEngine
        assert ProductionWriter is UnifiedWriterEngine

    def test_instantiation_mock_mode(self):
        """Test that engine can be instantiated in mock mode"""
        engine = UnifiedWriterEngine(mock_mode=True)
        assert engine is not None
        assert engine.mock_mode is True

    def test_generate_mock_article(self):
        """Test mock article generation"""
        engine = UnifiedWriterEngine(mock_mode=True)
        
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com/product',
                'anchor_text': 'best solution'
            },
            'generation_constraints': {
                'language': 'en',
                'min_word_count': 900
            },
            'target_profile': {
                'core_entities': ['Testing', 'Quality'],
                'core_topics': ['comparison', 'review']
            },
            'intent_extension': {
                'recommended_bridge_type': 'pivot'
            }
        }

        article, metrics = engine.generate(job_package, 'mock')
        
        assert article is not None
        assert len(article) > 0
        assert isinstance(metrics, dict)
        assert metrics['provider'] == 'mock'
        assert metrics['strategy'] == 'mock'
        assert metrics['success'] is True

    def test_generate_swedish_article(self):
        """Test Swedish mock article generation"""
        engine = UnifiedWriterEngine(mock_mode=True)
        
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.se',
                'target_url': 'https://example.com/product',
                'anchor_text': 'bästa valet'
            },
            'generation_constraints': {
                'language': 'sv',
                'min_word_count': 900
            },
            'target_profile': {
                'core_entities': ['Test', 'Kvalitet']
            },
            'intent_extension': {
                'recommended_bridge_type': 'strong'
            }
        }

        article, metrics = engine.generate(job_package, 'mock')
        
        assert article is not None
        assert 'guide' in article.lower() or 'komplett' in article.lower()
        assert 'https://example.com/product' in article
        assert 'bästa valet' in article

    def test_generate_article_interface(self):
        """Test generate_article interface (API compatibility)"""
        engine = UnifiedWriterEngine(mock_mode=True)
        
        context = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'learn more'
            },
            'generation_constraints': {'language': 'en'},
            'target_profile': {'core_entities': ['API']},
            'intent_extension': {'recommended_bridge_type': 'pivot'}
        }

        article, metrics = engine.generate_article(context, 'mock')
        
        assert article is not None
        assert len(article) > 0
        assert isinstance(metrics, dict)

    def test_backward_compatibility_writer_engine(self):
        """Test backward compatibility with WriterEngine import"""
        # This simulates: from writer.writer_engine import WriterEngine
        from writer.writer_engine import WriterEngine as ImportedWriterEngine
        
        engine = ImportedWriterEngine(mock_mode=True)
        assert isinstance(engine, UnifiedWriterEngine)

    def test_backward_compatibility_production_writer(self):
        """Test backward compatibility with ProductionWriter import"""
        # This simulates: from writer.production_writer import ProductionWriter
        from writer.production_writer import ProductionWriter as ImportedProductionWriter
        
        engine = ImportedProductionWriter(mock_mode=True)
        assert isinstance(engine, UnifiedWriterEngine)

    def test_llm_provider_enum(self):
        """Test LLM provider enum"""
        assert LLMProvider.ANTHROPIC.value == 'anthropic'
        assert LLMProvider.OPENAI.value == 'openai'
        assert LLMProvider.GOOGLE.value == 'google'

    def test_bridge_type_enum(self):
        """Test bridge type enum"""
        assert BridgeType.STRONG.value == 'strong'
        assert BridgeType.PIVOT.value == 'pivot'
        assert BridgeType.WRAPPER.value == 'wrapper'

    def test_lsi_terms_selection(self):
        """Test LSI term selection"""
        engine = UnifiedWriterEngine(mock_mode=True)
        
        job_package = {
            'generation_constraints': {'language': 'en'}
        }
        
        lsi_terms = engine._select_lsi_terms(job_package, 5)
        
        assert len(lsi_terms) == 5
        assert all(isinstance(term, str) for term in lsi_terms)

    def test_metrics_structure(self):
        """Test that metrics have correct structure"""
        metrics = GenerationMetrics(
            provider='mock',
            model='mock',
            strategy='mock'
        )
        
        assert metrics.provider == 'mock'
        assert metrics.model == 'mock'
        assert metrics.strategy == 'mock'
        assert metrics.total_tokens == 0
        assert metrics.cost_usd == 0.0
        assert metrics.success is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
