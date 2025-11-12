#!/usr/bin/env python3
"""
Tests for Unified Writer Engine

Comprehensive test suite for the unified writer engine that consolidates
duplicate implementations and provides multi-provider LLM support.

Features tested:
- Mock mode article generation
- Multiple bridge types (strong/pivot/wrapper)
- Multi-language support (Swedish/English)
- LSI term injection
- Metrics tracking
- Backward compatibility
- Provider fallback

Per BUILDER_PROMPT.md STEG 7
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.writer.unified_writer import UnifiedWriterEngine, WriterEngine, ProductionWriter
from src.writer.unified_writer import LLMProvider, BridgeType, GenerationMetrics


class TestUnifiedWriterInitialization:
    """Test suite for UnifiedWriterEngine initialization."""

    def test_initialization_mock_mode(self):
        """Test that engine can be instantiated in mock mode."""
        engine = UnifiedWriterEngine(mock_mode=True)
        assert engine is not None
        assert engine.mock_mode is True

    def test_initialization_with_options(self):
        """Test initialization with custom options."""
        engine = UnifiedWriterEngine(
            mock_mode=True,
            auto_fallback=False,
            enable_cost_tracking=True,
            max_retries=5
        )
        assert engine.mock_mode is True
        assert engine.auto_fallback is False
        assert engine.enable_cost_tracking is True
        assert engine.max_retries == 5

    def test_class_aliases(self):
        """Test that class aliases are properly set up for backward compatibility."""
        assert WriterEngine is UnifiedWriterEngine
        assert ProductionWriter is UnifiedWriterEngine

    def test_backward_compatibility_writer_engine(self):
        """Test backward compatibility with WriterEngine import."""
        from src.writer.writer_engine import WriterEngine as ImportedWriterEngine

        engine = ImportedWriterEngine(mock_mode=True)
        assert isinstance(engine, UnifiedWriterEngine)

    def test_backward_compatibility_production_writer(self):
        """Test backward compatibility with ProductionWriter import."""
        from src.writer.production_writer import ProductionWriter as ImportedProductionWriter

        engine = ImportedProductionWriter(mock_mode=True)
        assert isinstance(engine, UnifiedWriterEngine)


class TestEnumsAndConstants:
    """Test suite for enums and constants."""

    def test_llm_provider_enum(self):
        """Test LLM provider enum values."""
        assert LLMProvider.ANTHROPIC.value == 'anthropic'
        assert LLMProvider.OPENAI.value == 'openai'
        assert LLMProvider.GOOGLE.value == 'google'

    def test_bridge_type_enum(self):
        """Test bridge type enum values."""
        assert BridgeType.STRONG.value == 'strong'
        assert BridgeType.PIVOT.value == 'pivot'
        assert BridgeType.WRAPPER.value == 'wrapper'

    def test_lsi_library_exists(self):
        """Test that LSI library is defined for supported languages."""
        engine = UnifiedWriterEngine(mock_mode=True)

        assert 'sv' in engine.LSI_LIBRARY
        assert 'en' in engine.LSI_LIBRARY
        assert 'generic' in engine.LSI_LIBRARY['sv']
        assert 'generic' in engine.LSI_LIBRARY['en']
        assert len(engine.LSI_LIBRARY['sv']['generic']) > 0
        assert len(engine.LSI_LIBRARY['en']['generic']) > 0

    def test_pricing_defined(self):
        """Test that pricing is defined for supported models."""
        assert 'gpt-4o' in UnifiedWriterEngine.PRICING
        assert 'claude-3-5-sonnet-20240620' in UnifiedWriterEngine.PRICING
        assert 'gemini-2.0-flash-exp' in UnifiedWriterEngine.PRICING

        # Check pricing structure
        assert 'input' in UnifiedWriterEngine.PRICING['gpt-4o']
        assert 'output' in UnifiedWriterEngine.PRICING['gpt-4o']

    def test_model_configs_defined(self):
        """Test that model configurations are defined."""
        configs = UnifiedWriterEngine.MODEL_CONFIGS

        assert LLMProvider.ANTHROPIC in configs
        assert LLMProvider.OPENAI in configs
        assert LLMProvider.GOOGLE in configs

        # Check config structure
        for provider in configs.values():
            assert 'default_model' in provider
            assert 'fallback_model' in provider
            assert 'max_tokens' in provider
            assert 'temperature' in provider


class TestMockArticleGeneration:
    """Test suite for mock article generation."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.engine = UnifiedWriterEngine(mock_mode=True)
        self.base_job_package = {
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

    def test_generate_mock_article_basic(self):
        """Test basic mock article generation."""
        article, metrics = self.engine.generate(self.base_job_package, 'mock')

        assert article is not None
        assert len(article) > 0
        assert isinstance(metrics, dict)
        assert metrics['provider'] == 'mock'
        assert metrics['strategy'] == 'mock'
        assert metrics['success'] is True

    def test_generate_strong_bridge(self):
        """Test mock article generation with strong bridge type."""
        job = self.base_job_package.copy()
        job['intent_extension'] = {'recommended_bridge_type': 'strong'}

        article, metrics = self.engine.generate(job, 'mock')

        assert article is not None
        assert 'https://example.com/product' in article
        assert 'best solution' in article
        # Strong bridge should have direct connection
        assert 'comprehensive' in article.lower() or 'guide' in article.lower()

    def test_generate_pivot_bridge(self):
        """Test mock article generation with pivot bridge type."""
        job = self.base_job_package.copy()
        job['intent_extension'] = {'recommended_bridge_type': 'pivot'}

        article, metrics = self.engine.generate(job, 'mock')

        assert article is not None
        assert 'https://example.com/product' in article
        # Pivot bridge should have informational context
        assert 'context' in article.lower() or 'information' in article.lower()

    def test_generate_wrapper_bridge(self):
        """Test mock article generation with wrapper bridge type."""
        job = self.base_job_package.copy()
        job['intent_extension'] = {'recommended_bridge_type': 'wrapper'}

        article, metrics = self.engine.generate(job, 'mock')

        assert article is not None
        assert 'https://example.com/product' in article
        # Wrapper bridge should have multiple options mentioned
        assert 'alternative' in article.lower() or 'option' in article.lower()

    def test_generate_swedish_article(self):
        """Test Swedish mock article generation."""
        job = {
            'input_minimal': {
                'publisher_domain': 'test.se',
                'target_url': 'https://example.se/produkt',
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

        article, metrics = self.engine.generate(job, 'mock')

        assert article is not None
        # Should contain Swedish content
        assert 'guide' in article.lower() or 'komplett' in article.lower()
        assert 'https://example.se/produkt' in article
        assert 'bästa valet' in article

    def test_generate_english_article(self):
        """Test English mock article generation."""
        article, metrics = self.engine.generate(self.base_job_package, 'mock')

        assert article is not None
        assert 'guide' in article.lower() or 'comprehensive' in article.lower()
        assert 'best solution' in article

    def test_generate_article_interface(self):
        """Test generate_article interface for API compatibility."""
        context = {
            'input_minimal': {
                'publisher_domain': 'api-test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'learn more'
            },
            'generation_constraints': {'language': 'en'},
            'target_profile': {'core_entities': ['API']},
            'intent_extension': {'recommended_bridge_type': 'pivot'}
        }

        article, metrics = self.engine.generate_article(context, 'mock')

        assert article is not None
        assert len(article) > 0
        assert isinstance(metrics, dict)
        assert 'learn more' in article

    def test_generate_minimal_job_package(self):
        """Test generation with minimal job package."""
        minimal_job = {
            'input_minimal': {
                'publisher_domain': 'minimal.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'generation_constraints': {'language': 'en'}
        }

        article, metrics = self.engine.generate(minimal_job, 'mock')

        assert article is not None
        assert len(article) > 0
        assert 'https://example.com' in article


class TestLSITerms:
    """Test suite for LSI term selection and handling."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.engine = UnifiedWriterEngine(mock_mode=True)

    def test_select_lsi_terms_english(self):
        """Test LSI term selection for English."""
        job_package = {
            'generation_constraints': {'language': 'en'}
        }

        lsi_terms = self.engine._select_lsi_terms(job_package, 5)

        assert len(lsi_terms) == 5
        assert all(isinstance(term, str) for term in lsi_terms)
        # Should be English terms
        assert any(term in self.engine.LSI_LIBRARY['en']['generic'] for term in lsi_terms)

    def test_select_lsi_terms_swedish(self):
        """Test LSI term selection for Swedish."""
        job_package = {
            'generation_constraints': {'language': 'sv'}
        }

        lsi_terms = self.engine._select_lsi_terms(job_package, 5)

        assert len(lsi_terms) == 5
        assert all(isinstance(term, str) for term in lsi_terms)
        # Should be Swedish terms
        assert any(term in self.engine.LSI_LIBRARY['sv']['generic'] for term in lsi_terms)

    def test_select_lsi_terms_custom_count(self):
        """Test LSI term selection with custom count."""
        job_package = {
            'generation_constraints': {'language': 'en'}
        }

        # Test different counts
        for count in [3, 6, 10]:
            lsi_terms = self.engine._select_lsi_terms(job_package, count)
            assert len(lsi_terms) == count

    def test_select_lsi_terms_default_language(self):
        """Test LSI term selection with empty package."""
        job_package = {}

        lsi_terms = self.engine._select_lsi_terms(job_package, 5)

        assert len(lsi_terms) == 5
        assert all(isinstance(term, str) for term in lsi_terms)
        # Should return terms from either language library
        all_lsi_terms = self.engine.LSI_LIBRARY['en']['generic'] + self.engine.LSI_LIBRARY['sv']['generic']
        assert any(term in all_lsi_terms for term in lsi_terms)

    def test_lsi_terms_are_unique(self):
        """Test that selected LSI terms are unique."""
        job_package = {
            'generation_constraints': {'language': 'en'}
        }

        lsi_terms = self.engine._select_lsi_terms(job_package, 10)

        # Should not have duplicates
        assert len(lsi_terms) == len(set(lsi_terms))


class TestMetricsTracking:
    """Test suite for generation metrics tracking."""

    def test_metrics_dataclass_structure(self):
        """Test that GenerationMetrics has correct structure."""
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
        assert metrics.retries == 0
        assert metrics.duration_seconds == 0.0

    def test_metrics_with_custom_values(self):
        """Test GenerationMetrics with custom values."""
        metrics = GenerationMetrics(
            provider='anthropic',
            model='claude-3-5-sonnet-20240620',
            strategy='single_shot',
            total_tokens=1500,
            prompt_tokens=500,
            completion_tokens=1000,
            cost_usd=0.045,
            duration_seconds=3.5,
            stages_completed=1,
            retries=0,
            success=True
        )

        assert metrics.provider == 'anthropic'
        assert metrics.model == 'claude-3-5-sonnet-20240620'
        assert metrics.total_tokens == 1500
        assert metrics.prompt_tokens == 500
        assert metrics.completion_tokens == 1000
        assert metrics.cost_usd == 0.045
        assert metrics.duration_seconds == 3.5

    def test_mock_generation_returns_metrics(self):
        """Test that mock generation returns proper metrics."""
        engine = UnifiedWriterEngine(mock_mode=True)
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'generation_constraints': {'language': 'en'},
            'target_profile': {},
            'intent_extension': {'recommended_bridge_type': 'strong'}
        }

        article, metrics = engine.generate(job_package, 'mock')

        assert isinstance(metrics, dict)
        assert 'provider' in metrics
        assert 'model' in metrics
        assert 'strategy' in metrics
        assert 'success' in metrics
        assert metrics['provider'] == 'mock'
        assert metrics['success'] is True

    def test_metrics_dict_conversion(self):
        """Test that metrics can be converted to dict."""
        metrics = GenerationMetrics(
            provider='test',
            model='test-model',
            strategy='test-strategy'
        )

        metrics_dict = metrics.__dict__

        assert isinstance(metrics_dict, dict)
        assert 'provider' in metrics_dict
        assert 'model' in metrics_dict
        assert metrics_dict['provider'] == 'test'


class TestStrategySupport:
    """Test suite for different generation strategies."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.engine = UnifiedWriterEngine(mock_mode=True)
        self.job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test link'
            },
            'generation_constraints': {'language': 'en'},
            'target_profile': {'core_entities': ['Test']},
            'intent_extension': {'recommended_bridge_type': 'pivot'}
        }

    def test_mock_strategy(self):
        """Test mock generation strategy."""
        article, metrics = self.engine.generate(self.job_package, 'mock')

        assert article is not None
        assert metrics['strategy'] == 'mock'
        assert metrics['provider'] == 'mock'

    def test_generate_with_strategy_mapping(self):
        """Test that generate_article maps strategies correctly."""
        # Test 'mock' strategy
        article, metrics = self.engine.generate_article(self.job_package, 'mock')
        assert article is not None
        assert metrics['strategy'] == 'mock'


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.engine = UnifiedWriterEngine(mock_mode=True)

    def test_missing_intent_extension(self):
        """Test handling of missing intent_extension."""
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'generation_constraints': {'language': 'en'}
        }

        article, metrics = self.engine.generate(job_package, 'mock')

        # Should still generate article with default bridge type
        assert article is not None
        assert len(article) > 0

    def test_missing_generation_constraints(self):
        """Test handling of missing generation_constraints."""
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            }
        }

        article, metrics = self.engine.generate(job_package, 'mock')

        # Should still generate with defaults
        assert article is not None
        assert len(article) > 0

    def test_empty_target_profile(self):
        """Test handling of empty target profile."""
        job_package = {
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'generation_constraints': {'language': 'en'},
            'target_profile': {}
        }

        article, metrics = self.engine.generate(job_package, 'mock')

        assert article is not None
        assert 'https://example.com' in article


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR Unified Writer Engine Tests")
    log("Per BUILDER_PROMPT.md STEG 7\n")
    log("=" * 60)

    try:
        # Test initialization
        log("\n🔍 Testing UnifiedWriterEngine initialization...")
        engine = UnifiedWriterEngine(mock_mode=True)
        log(f"✅ Engine initialized in mock mode")

        # Test mock article generation
        log("\n🔍 Testing mock article generation...")
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
                'core_entities': ['Testing'],
                'core_topics': ['review']
            },
            'intent_extension': {
                'recommended_bridge_type': 'pivot'
            }
        }

        article, metrics = engine.generate(job_package, 'mock')
        log(f"✅ Article generation working:")
        log(f"   Length: {len(article)} characters")
        log(f"   Provider: {metrics['provider']}")
        log(f"   Strategy: {metrics['strategy']}")

        # Test LSI terms
        log("\n🔍 Testing LSI term selection...")
        lsi_terms = engine._select_lsi_terms({'generation_constraints': {'language': 'en'}}, 5)
        log(f"✅ LSI term selection working: {len(lsi_terms)} terms")

        # Test backward compatibility
        log("\n🔍 Testing backward compatibility...")
        from src.writer.writer_engine import WriterEngine as Legacy
        legacy_engine = Legacy(mock_mode=True)
        assert isinstance(legacy_engine, UnifiedWriterEngine)
        log(f"✅ Backward compatibility verified")

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
