"""
Tests for PageProfiler

Del 3B: Content Generation Pipeline
"""

import pytest
from src.profiling.page_profiler import PageProfiler


class TestPageProfiler:
    """Test suite for PageProfiler"""

    def setup_method(self):
        """Setup test fixtures"""
        self.profiler = PageProfiler(timeout=10)

    def test_parse_html_basic(self):
        """Test basic HTML parsing"""
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

    def test_extract_text_content(self):
        """Test text content extraction"""
        html = """
        <html>
            <body>
                <nav>Navigation</nav>
                <h1>Main Content</h1>
                <p>This is the main text.</p>
                <script>console.log('test');</script>
                <footer>Footer</footer>
            </body>
        </html>
        """
        soup = self.profiler.parse_html(html)
        text = self.profiler.extract_text_content(soup)

        assert 'Main Content' in text
        assert 'main text' in text
        assert 'Navigation' not in text  # nav removed
        assert 'Footer' not in text  # footer removed
        assert 'console.log' not in text  # script removed

    def test_detect_language_swedish(self):
        """Test language detection for Swedish"""
        swedish_text = """
        Detta är en svensk text som handlar om olika ämnen.
        Vi diskuterar flera intressanta saker här.
        """
        lang = self.profiler.detect_language(swedish_text)
        assert lang == 'sv'

    def test_detect_language_english(self):
        """Test language detection for English"""
        english_text = """
        This is an English text about various topics.
        We discuss several interesting things here.
        """
        lang = self.profiler.detect_language(english_text)
        assert lang == 'en'

    def test_extract_entities_and_topics(self):
        """Test entity and topic extraction"""
        html = """
        <html>
            <head><title>Product X Review Guide</title></head>
            <body>
                <h1>Product X Testing</h1>
                <h2>Benefits Analysis</h2>
                <h3>Comparison Tools</h3>
                <meta name="keywords" content="product, review, comparison">
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

    def test_infer_core_offer(self):
        """Test core offer inference"""
        title = "Best Product Comparison Tool"
        h1 = "Compare Products Easily"
        meta_desc = "Find the best product for your needs with our comprehensive comparison tool"

        offer = self.profiler._infer_core_offer(title, h1, meta_desc)

        assert isinstance(offer, str)
        assert len(offer) > 0
        # Should prefer meta description
        assert 'comparison' in offer.lower()

    def test_generate_candidate_queries(self):
        """Test candidate query generation"""
        title = "Product X Review"
        entities = ["Product X", "Brand Y"]
        topics = ["review", "comparison"]

        queries = self.profiler._generate_candidate_queries(title, entities, topics)

        assert isinstance(queries, list)
        assert len(queries) > 0
        assert all(isinstance(q, str) for q in queries)

    def test_infer_tone_class_consumer_magazine(self):
        """Test tone class inference - consumer magazine"""
        text = """
        In this guide, we compare the best products available.
        Our testing shows that quality matters.
        Read our tips for making the right choice.
        """
        tone = self.profiler._infer_tone_class(text)
        assert tone == 'consumer_magazine'

    def test_infer_tone_class_academic(self):
        """Test tone class inference - academic"""
        text = """
        This research study examines the scientific evidence.
        Our vetenskaplig analysis shows interesting results.
        """
        tone = self.profiler._infer_tone_class(text)
        assert tone == 'academic'

    def test_infer_commerciality_low(self):
        """Test commerciality inference - low"""
        text = "This is informational content about various topics."
        commerciality = self.profiler._infer_commerciality(text)
        assert commerciality == 'low'

    def test_infer_commerciality_high(self):
        """Test commerciality inference - high"""
        text = """
        Buy now! Best price available!
        Shop our deals and get amazing rabatt.
        Compare prices and köp today!
        Special erbjudande just for you!
        """
        commerciality = self.profiler._infer_commerciality(text)
        assert commerciality == 'high'

    def test_profile_target_page_structure(self):
        """Test that profile_target_page returns correct structure"""
        # Mock profile (we'll test with real URLs separately)
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

        # We can't easily mock the HTTP request in this test,
        # so we'll test the structure with a manual parse
        soup = self.profiler.parse_html(html)
        title = soup.find('title').get_text(strip=True)
        text_content = self.profiler.extract_text_content(soup)
        entities, topics = self.profiler.extract_entities_and_topics(soup, title)

        # Verify we can extract the needed components
        assert title == "Test Product Page"
        assert len(text_content) > 0
        assert isinstance(entities, list)
        assert isinstance(topics, list)

    def test_profile_publisher_structure(self):
        """Test that profile_publisher_domain returns correct structure"""
        # Similar to above, we test components rather than full HTTP flow
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

        assert tone in ['consumer_magazine', 'academic', 'authority_public', 'hobby_blog']
        assert commerciality in ['low', 'medium', 'high']
        assert isinstance(lang, str)
        assert len(lang) == 2  # ISO 639-1 code


def test_profiler_initialization():
    """Test PageProfiler initialization"""
    profiler = PageProfiler()
    assert profiler.timeout == 10
    assert 'BACOWR' in profiler.user_agent

    custom_profiler = PageProfiler(timeout=30, user_agent='CustomBot/1.0')
    assert custom_profiler.timeout == 30
    assert custom_profiler.user_agent == 'CustomBot/1.0'


if __name__ == '__main__':
    # Run tests
    pytest.main([__file__, '-v'])
