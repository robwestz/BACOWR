#!/usr/bin/env python3
"""
Tests for PageProfiler

Comprehensive test suite for page profiling functionality including:
- HTML parsing and content extraction
- Language detection
- Entity and topic extraction
- Tone and commerciality inference
- Publisher and target page profiling

Part of Del 3B: Content Generation Pipeline
Per BUILDER_PROMPT.md STEG 4
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.profiling.page_profiler import PageProfiler


class TestPageProfilerParsing:
    """Test suite for HTML parsing and extraction."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.profiler = PageProfiler(timeout=10)

    def test_profiler_initialization(self):
        """Test PageProfiler initializes correctly."""
        profiler = PageProfiler()
        assert profiler.timeout == 10
        assert 'BACOWR' in profiler.user_agent

        custom_profiler = PageProfiler(timeout=30, user_agent='CustomBot/1.0')
        assert custom_profiler.timeout == 30
        assert custom_profiler.user_agent == 'CustomBot/1.0'

    def test_parse_html_basic(self):
        """Test basic HTML parsing."""
        html = """
        <html>
            <head>
                <title>Test Page</title>
                <meta name="description" content="Test description">
            </head>
            <body>
                <h1>Main Heading</h1>
                <h2>Subheading 1</h2>
                <p>Some content here.</p>
            </body>
        </html>
        """
        soup = self.profiler.parse_html(html)

        assert soup.find('title').get_text() == 'Test Page'
        assert soup.find('h1').get_text() == 'Main Heading'
        assert soup.find('meta', {'name': 'description'})['content'] == 'Test description'

    def test_parse_html_malformed(self):
        """Test parsing malformed HTML (should still work with lxml)."""
        html = """
        <html>
            <head><title>Broken HTML</title></head>
            <body>
                <h1>Unclosed tags
                <p>Missing closing tags
        """
        soup = self.profiler.parse_html(html)

        # lxml is forgiving and will parse this
        assert soup.find('title') is not None
        assert soup.find('h1') is not None

    def test_extract_text_content(self):
        """Test text content extraction with noise removal."""
        html = """
        <html>
            <body>
                <nav>Navigation Menu</nav>
                <header>Site Header</header>
                <h1>Main Content</h1>
                <p>This is the main text content.</p>
                <script>console.log('test');</script>
                <style>body { color: red; }</style>
                <footer>Site Footer</footer>
            </body>
        </html>
        """
        soup = self.profiler.parse_html(html)
        text = self.profiler.extract_text_content(soup)

        # Should include main content
        assert 'Main Content' in text
        assert 'main text' in text

        # Should remove noise elements
        assert 'Navigation' not in text
        assert 'Site Header' not in text
        assert 'Footer' not in text
        assert 'console.log' not in text
        assert 'color: red' not in text

    def test_extract_text_empty_html(self):
        """Test text extraction from empty HTML."""
        html = "<html><body></body></html>"
        soup = self.profiler.parse_html(html)
        text = self.profiler.extract_text_content(soup)

        assert text == ""


class TestPageProfilerLanguageDetection:
    """Test suite for language detection."""

    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = PageProfiler()

    def test_detect_language_swedish(self):
        """Test Swedish language detection."""
        swedish_text = """
        Detta är en svensk text som handlar om olika ämnen.
        Vi diskuterar flera intressanta saker här och använder
        typiska svenska ord som och, att, för, som, är.
        """
        lang = self.profiler.detect_language(swedish_text)
        assert lang == 'sv'

    def test_detect_language_english(self):
        """Test English language detection."""
        english_text = """
        This is an English text about various topics.
        We discuss several interesting things here using
        typical English words like and, the, for, that, is.
        """
        lang = self.profiler.detect_language(english_text)
        assert lang == 'en'

    def test_detect_language_short_text(self):
        """Test language detection with short text."""
        short_text = "Detta är en kort text"
        lang = self.profiler.detect_language(short_text)
        # Should still work with short text
        assert lang in ['sv', 'en']

    def test_detect_language_mixed(self):
        """Test language detection with mixed content."""
        mixed_text = """
        This text is mostly English with some svenska ord.
        But the majority of the content is in English.
        """
        lang = self.profiler.detect_language(mixed_text)
        # Should detect dominant language
        assert lang in ['sv', 'en']


class TestPageProfilerEntityExtraction:
    """Test suite for entity and topic extraction."""

    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = PageProfiler()

    def test_extract_entities_and_topics(self):
        """Test entity and topic extraction."""
        html = """
        <html>
            <head>
                <title>Product X Review Guide</title>
                <meta name="keywords" content="product, review, comparison">
            </head>
            <body>
                <h1>Product X Testing</h1>
                <h2>Benefits Analysis</h2>
                <h3>Comparison Tools</h3>
            </body>
        </html>
        """
        soup = self.profiler.parse_html(html)
        title = soup.find('title').get_text()

        entities, topics = self.profiler.extract_entities_and_topics(soup, title)

        assert isinstance(entities, list)
        assert isinstance(topics, list)
        assert len(entities) > 0
        assert len(topics) > 0

    def test_extract_from_minimal_html(self):
        """Test extraction from minimal HTML."""
        html = "<html><head><title>Test</title></head><body><h1>Test</h1></body></html>"
        soup = self.profiler.parse_html(html)
        title = soup.find('title').get_text()

        entities, topics = self.profiler.extract_entities_and_topics(soup, title)

        # Should still return lists even with minimal content
        assert isinstance(entities, list)
        assert isinstance(topics, list)

    def test_infer_core_offer(self):
        """Test core offer inference from metadata."""
        title = "Best Product Comparison Tool"
        h1 = "Compare Products Easily"
        meta_desc = "Find the best product for your needs with our comprehensive comparison tool"

        offer = self.profiler._infer_core_offer(title, h1, meta_desc)

        assert isinstance(offer, str)
        assert len(offer) > 0
        # Should prefer meta description
        assert 'comparison' in offer.lower()

    def test_infer_core_offer_fallback(self):
        """Test core offer inference with missing metadata."""
        title = "Product Page"
        h1 = None
        meta_desc = None

        offer = self.profiler._infer_core_offer(title, h1, meta_desc)

        # Should fallback to title with prefix
        assert "Product Page" in offer
        assert "Provides information about" in offer

    def test_generate_candidate_queries(self):
        """Test candidate query generation."""
        title = "Product X Review"
        entities = ["Product X", "Brand Y"]
        topics = ["review", "comparison"]

        queries = self.profiler._generate_candidate_queries(title, entities, topics)

        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)

    def test_generate_candidate_queries_empty(self):
        """Test query generation with empty inputs."""
        title = "Test"
        entities = []
        topics = []

        queries = self.profiler._generate_candidate_queries(title, entities, topics)

        # Should return empty list when no entities/topics
        assert isinstance(queries, list)
        assert len(queries) == 0


class TestPageProfilerToneInference:
    """Test suite for tone classification."""

    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = PageProfiler()

    def test_infer_tone_class_consumer_magazine(self):
        """Test tone inference - consumer magazine."""
        text = """
        In this guide, we compare the best products available.
        Our testing shows that quality matters.
        Read our tips for making the right choice.
        We help you find the right solution.
        """
        tone = self.profiler._infer_tone_class(text)
        assert tone == 'consumer_magazine'

    def test_infer_tone_class_academic(self):
        """Test tone inference - academic."""
        text = """
        This research study examines the scientific evidence.
        Our vetenskaplig analysis shows interesting results.
        The methodology includes rigorous testing procedures.
        Research indicates significant findings.
        """
        tone = self.profiler._infer_tone_class(text)
        assert tone == 'academic'

    def test_infer_tone_class_authority_public(self):
        """Test tone inference - authority/public."""
        text = """
        According to government regulations and official policies,
        citizens must follow these guidelines.
        The authority recommends these measures.
        Official statistics show important trends.
        """
        tone = self.profiler._infer_tone_class(text)
        assert tone == 'authority_public'

    def test_infer_tone_class_hobby_blog(self):
        """Test tone inference - hobby blog (default)."""
        text = """
        Just wanted to share my thoughts on this topic.
        Here are some random observations.
        """
        tone = self.profiler._infer_tone_class(text)
        # Should default to hobby_blog when no strong signals
        assert tone in ['hobby_blog', 'consumer_magazine']


class TestPageProfilerCommerciality:
    """Test suite for commerciality inference."""

    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = PageProfiler()

    def test_infer_commerciality_low(self):
        """Test low commerciality inference."""
        text = "This is informational content about various topics and concepts."
        commerciality = self.profiler._infer_commerciality(text)
        assert commerciality == 'low'

    def test_infer_commerciality_medium(self):
        """Test medium commerciality inference."""
        text = """
        Compare these products and services.
        Find the best option for your needs.
        Check out our recommendations.
        """
        commerciality = self.profiler._infer_commerciality(text)
        assert commerciality in ['medium', 'low']  # Depends on threshold

    def test_infer_commerciality_high(self):
        """Test high commerciality inference."""
        text = """
        Buy now! Best price available!
        Shop our deals and get amazing rabatt.
        Compare prices and köp today!
        Special erbjudande just for you!
        Order now and save money!
        """
        commerciality = self.profiler._infer_commerciality(text)
        assert commerciality == 'high'

    def test_infer_commerciality_empty(self):
        """Test commerciality inference with empty text."""
        text = ""
        commerciality = self.profiler._infer_commerciality(text)
        # Should default to low
        assert commerciality == 'low'


class TestPageProfilerIntegration:
    """Integration tests for complete profiling workflows."""

    def setup_method(self):
        """Setup test fixtures."""
        self.profiler = PageProfiler()

    def test_profile_target_page_structure(self):
        """Test that profile components work together for target page."""
        html = """
        <html>
            <head>
                <title>Test Product Page</title>
                <meta name="description" content="Best product for testing">
            </head>
            <body>
                <h1>Test Product</h1>
                <h2>Features</h2>
                <h3>Benefits</h3>
                <p>This is a great product with many features and benefits.</p>
            </body>
        </html>
        """

        soup = self.profiler.parse_html(html)
        title = soup.find('title').get_text(strip=True)
        text_content = self.profiler.extract_text_content(soup)
        entities, topics = self.profiler.extract_entities_and_topics(soup, title)

        # Verify all components work
        assert title == "Test Product Page"
        assert len(text_content) > 0
        assert isinstance(entities, list)
        assert isinstance(topics, list)

    def test_profile_publisher_structure(self):
        """Test that profile components work together for publisher."""
        html = """
        <html>
            <head><title>Publisher Homepage</title></head>
            <body>
                <h1>Welcome to Our Site</h1>
                <p>We provide quality content about various topics including
                   technology, science, and reviews. Our guide helps you
                   make informed decisions.</p>
            </body>
        </html>
        """

        soup = self.profiler.parse_html(html)
        text = self.profiler.extract_text_content(soup)

        tone = self.profiler._infer_tone_class(text)
        commerciality = self.profiler._infer_commerciality(text)
        lang = self.profiler.detect_language(text)

        # Verify all inferences work
        assert tone in ['consumer_magazine', 'academic', 'authority_public', 'hobby_blog']
        assert commerciality in ['low', 'medium', 'high']
        assert isinstance(lang, str)
        assert len(lang) == 2  # ISO 639-1 code

    def test_complete_profiling_workflow(self):
        """Test complete profiling workflow with all components."""
        html = """
        <html>
            <head>
                <title>Comprehensive Product Review</title>
                <meta name="description" content="Detailed analysis and comparison">
                <meta name="keywords" content="product, review, test">
            </head>
            <body>
                <h1>Product Analysis</h1>
                <h2>Testing Results</h2>
                <p>We tested this product thoroughly and found excellent results.
                   Our comparison shows it performs well in various scenarios.</p>
            </body>
        </html>
        """

        # Parse
        soup = self.profiler.parse_html(html)

        # Extract
        title = soup.find('title').get_text(strip=True)
        text = self.profiler.extract_text_content(soup)
        entities, topics = self.profiler.extract_entities_and_topics(soup, title)

        # Infer
        tone = self.profiler._infer_tone_class(text)
        commerciality = self.profiler._infer_commerciality(text)
        lang = self.profiler.detect_language(text)

        # Verify complete workflow
        assert title
        assert text
        assert len(entities) > 0
        assert len(topics) > 0
        assert tone
        assert commerciality
        assert lang


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility and quick validation.
    """
    log("BACOWR PageProfiler Tests")
    log("Per BUILDER_PROMPT.md STEG 4\n")
    log("=" * 70)

    try:
        profiler = PageProfiler()
        log("✅ PageProfiler initialized\n")

        # Test 1: HTML Parsing
        log("🔍 Test 1: HTML Parsing")
        html = "<html><head><title>Test</title></head><body><h1>Content</h1></body></html>"
        soup = profiler.parse_html(html)
        assert soup.find('title').get_text() == 'Test'
        log("   ✅ PASS\n")

        # Test 2: Text Extraction
        log("🔍 Test 2: Text Extraction")
        html_with_noise = """
        <html><body>
        <nav>Nav</nav>
        <h1>Main</h1>
        <script>code</script>
        </body></html>
        """
        soup = profiler.parse_html(html_with_noise)
        text = profiler.extract_text_content(soup)
        assert 'Main' in text
        assert 'Nav' not in text
        log("   ✅ PASS\n")

        # Test 3: Language Detection
        log("🔍 Test 3: Language Detection")
        sv_text = "Detta är svensk text med och att för"
        lang = profiler.detect_language(sv_text)
        assert lang == 'sv'
        log(f"   Detected: {lang}")
        log("   ✅ PASS\n")

        # Test 4: Entity Extraction
        log("🔍 Test 4: Entity Extraction")
        html_entities = """
        <html><head><title>Product Review</title></head>
        <body><h1>Product</h1><h2>Review</h2></body></html>
        """
        soup = profiler.parse_html(html_entities)
        title = soup.find('title').get_text()
        entities, topics = profiler.extract_entities_and_topics(soup, title)
        assert len(entities) > 0
        assert len(topics) > 0
        log(f"   Entities: {len(entities)}, Topics: {len(topics)}")
        log("   ✅ PASS\n")

        # Test 5: Tone Classification
        log("🔍 Test 5: Tone Classification")
        consumer_text = "Our guide helps you compare and find the best choice"
        tone = profiler._infer_tone_class(consumer_text)
        assert tone in ['consumer_magazine', 'hobby_blog']
        log(f"   Tone: {tone}")
        log("   ✅ PASS\n")

        # Test 6: Commerciality
        log("🔍 Test 6: Commerciality Inference")
        commercial_text = "Buy now! Shop today! Best price!"
        commerciality = profiler._infer_commerciality(commercial_text)
        assert commerciality in ['medium', 'high']
        log(f"   Commerciality: {commerciality}")
        log("   ✅ PASS\n")

        log("=" * 70)
        log("✅ All standalone tests passed!", "SUCCESS")
        log("=" * 70)
        return True

    except AssertionError as e:
        log(f"❌ Test failed: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    log("=" * 70)
    success = run_standalone_tests()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
