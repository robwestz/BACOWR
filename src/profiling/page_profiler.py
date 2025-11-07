"""
PageProfiler - Extract structured data from web pages

Part of Del 3B: Content Generation Pipeline
Fetches and analyzes HTML to create publisher_profile and target_profile
"""

import re
import requests
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup


class PageProfiler:
    """
    Profiles web pages to extract structured data for BacklinkJobPackage.

    Supports:
    - HTML fetching and parsing
    - Language detection
    - Entity and topic extraction
    - Publisher and target profiling
    """

    def __init__(self, timeout: int = 10, user_agent: Optional[str] = None):
        """
        Initialize PageProfiler.

        Args:
            timeout: HTTP request timeout in seconds
            user_agent: Custom user agent string (optional)
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            'Mozilla/5.0 (compatible; BACOWR/1.0; +https://github.com/robwestz/BACOWR)'
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def fetch_html(self, url: str) -> Tuple[int, str]:
        """
        Fetch HTML content from URL.

        Args:
            url: Target URL

        Returns:
            (http_status, html_content)

        Raises:
            requests.RequestException: On HTTP errors
        """
        response = self.session.get(url, timeout=self.timeout, allow_redirects=True)
        return response.status_code, response.text

    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML into BeautifulSoup object.

        Args:
            html: Raw HTML string

        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html, 'lxml')

    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML.

        Removes scripts, styles, navigation, footer.

        Args:
            soup: BeautifulSoup object

        Returns:
            Clean text content
        """
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        # Get text
        text = soup.get_text(separator=' ', strip=True)

        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def detect_language(self, text: str) -> str:
        """
        Detect language from text content using simple heuristics.

        Args:
            text: Text to analyze

        Returns:
            ISO 639-1 language code (e.g., 'sv', 'en')
        """
        if not text or len(text) < 10:
            return 'en'

        # Use first 1000 chars for detection (faster and usually sufficient)
        sample = text[:1000].lower() if len(text) > 1000 else text.lower()

        # Swedish indicators
        swedish_words = ['och', 'är', 'för', 'som', 'att', 'till', 'med', 'det', 'kan', 'på', 'av', 'vi', 'att', 'från']
        swedish_chars = ['å', 'ä', 'ö']

        # English indicators
        english_words = ['the', 'and', 'is', 'for', 'that', 'to', 'with', 'it', 'can', 'on', 'of', 'we', 'from', 'this']

        # Count Swedish indicators
        swedish_score = 0
        swedish_score += sum(1 for word in swedish_words if f' {word} ' in f' {sample} ')
        swedish_score += sum(1 for char in swedish_chars if char in sample) * 3  # Weight chars higher

        # Count English indicators
        english_score = sum(1 for word in english_words if f' {word} ' in f' {sample} ')

        # Return based on scores
        if swedish_score > english_score:
            return 'sv'
        else:
            return 'en'

    def extract_entities_and_topics(self, soup: BeautifulSoup, title: str) -> Tuple[List[str], List[str]]:
        """
        Extract entities and topics from page content.

        Simple extraction based on:
        - Title
        - Headings (H1, H2, H3)
        - Meta keywords (if available)
        - Capitalized phrases

        Args:
            soup: BeautifulSoup object
            title: Page title

        Returns:
            (entities, topics)
        """
        entities = set()
        topics = set()

        # Extract from title
        title_words = self._extract_significant_phrases(title)
        entities.update(title_words[:3])  # First 3 as potential entities

        # Extract from headings
        for tag in ['h1', 'h2', 'h3']:
            headings = soup.find_all(tag)
            for h in headings[:10]:  # Limit to first 10 of each type
                text = h.get_text(strip=True)
                phrases = self._extract_significant_phrases(text)
                if tag == 'h1':
                    entities.update(phrases[:2])
                else:
                    topics.update(phrases[:2])

        # Extract from meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            keywords = [k.strip() for k in meta_keywords['content'].split(',')]
            topics.update(keywords[:5])

        return list(entities)[:10], list(topics)[:10]

    def _extract_significant_phrases(self, text: str) -> List[str]:
        """
        Extract significant phrases from text.

        Looks for:
        - Capitalized words (potential entities)
        - Multi-word phrases
        - Filters out common stopwords

        Args:
            text: Input text

        Returns:
            List of significant phrases
        """
        # Remove common Swedish and English stopwords
        stopwords = {
            'och', 'eller', 'är', 'för', 'med', 'till', 'av', 'på', 'som', 'den', 'det',
            'and', 'or', 'is', 'for', 'with', 'to', 'of', 'on', 'the', 'a', 'an', 'in'
        }

        # Extract words
        words = re.findall(r'\b[A-ZÅÄÖ][a-zåäö]+(?:\s+[A-ZÅÄÖ][a-zåäö]+)*\b', text)

        # Filter
        phrases = [w for w in words if w.lower() not in stopwords and len(w) > 2]

        return phrases[:10]

    def profile_target_page(self, url: str) -> Dict[str, Any]:
        """
        Profile a target page (the URL to link to).

        Args:
            url: Target URL

        Returns:
            target_profile dict matching BacklinkJobPackage schema
        """
        # Fetch HTML
        http_status, html = self.fetch_html(url)
        soup = self.parse_html(html)

        # Extract basic elements
        title = soup.find('title')
        title_text = title.get_text(strip=True) if title else 'Untitled'

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_desc['content'] if meta_desc and meta_desc.get('content') else None

        h1 = soup.find('h1')
        h1_text = h1.get_text(strip=True) if h1 else None

        # Get H2/H3 sample
        h2_h3_sample = []
        for tag in ['h2', 'h3']:
            headings = soup.find_all(tag)
            h2_h3_sample.extend([h.get_text(strip=True) for h in headings[:5]])
        h2_h3_sample = h2_h3_sample[:10]  # Max 10 total

        # Extract main content
        text_content = self.extract_text_content(soup)
        main_content_excerpt = text_content[:500] + '...' if len(text_content) > 500 else text_content

        # Detect language
        detected_language = self.detect_language(text_content)

        # Extract entities and topics
        entities, topics = self.extract_entities_and_topics(soup, title_text)

        # Generate core offer (simple heuristic)
        core_offer = self._infer_core_offer(title_text, h1_text, meta_description)

        # Generate candidate queries
        candidate_queries = self._generate_candidate_queries(title_text, entities, topics)

        return {
            'url': url,
            'http_status': http_status,
            'title': title_text,
            'meta_description': meta_description,
            'h1': h1_text,
            'h2_h3_sample': h2_h3_sample,
            'main_content_excerpt': main_content_excerpt,
            'detected_language': detected_language,
            'core_entities': entities,
            'core_topics': topics,
            'core_offer': core_offer,
            'candidate_main_queries': candidate_queries
        }

    def profile_publisher_domain(self, domain: str, sample_urls: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Profile a publisher domain.

        Args:
            domain: Publisher domain (e.g., 'example.com')
            sample_urls: Optional list of sample URLs to analyze

        Returns:
            publisher_profile dict matching BacklinkJobPackage schema
        """
        # If no sample URLs provided, try to fetch homepage
        if not sample_urls:
            sample_urls = [f'https://{domain}']

        # Aggregate data from sample URLs
        all_text = []
        all_topics = set()
        languages = []
        about_excerpt = None

        for url in sample_urls[:3]:  # Max 3 sample URLs
            try:
                http_status, html = self.fetch_html(url)
                soup = self.parse_html(html)

                # Extract text
                text = self.extract_text_content(soup)
                all_text.append(text)

                # Detect language
                lang = self.detect_language(text)
                languages.append(lang)

                # Extract topics
                _, topics = self.extract_entities_and_topics(soup, soup.find('title').get_text() if soup.find('title') else '')
                all_topics.update(topics)

                # Look for "about" content
                if not about_excerpt:
                    about_excerpt = self._find_about_content(soup)

            except Exception as e:
                # Log error but continue with other URLs
                print(f"Warning: Failed to fetch {url}: {e}")
                continue

        # Aggregate results
        detected_language = max(set(languages), key=languages.count) if languages else 'en'
        topic_focus = list(all_topics)[:10]

        # Infer tone class (simplified heuristic)
        tone_class = self._infer_tone_class(' '.join(all_text))

        # Infer allowed commerciality
        allowed_commerciality = self._infer_commerciality(' '.join(all_text))

        return {
            'domain': domain,
            'sample_urls': sample_urls,
            'about_excerpt': about_excerpt,
            'detected_language': detected_language,
            'topic_focus': topic_focus,
            'tone_class': tone_class,
            'allowed_commerciality': allowed_commerciality,
            'brand_safety_notes': 'Auto-generated profile - review recommended'
        }

    def _infer_core_offer(self, title: str, h1: Optional[str], meta_desc: Optional[str]) -> str:
        """
        Infer what the page offers to users.

        Args:
            title: Page title
            h1: H1 heading
            meta_desc: Meta description

        Returns:
            Core offer description
        """
        # Combine available text
        text = ' '.join(filter(None, [title, h1, meta_desc]))

        # Simple heuristic: use meta description if available, else title
        if meta_desc and len(meta_desc) > 20:
            return meta_desc[:200]
        elif title:
            return f"Provides information about: {title}"
        else:
            return "Provides relevant information to users"

    def _generate_candidate_queries(self, title: str, entities: List[str], topics: List[str]) -> List[str]:
        """
        Generate candidate search queries based on page content.

        Args:
            title: Page title
            entities: Extracted entities
            topics: Extracted topics

        Returns:
            List of candidate queries
        """
        queries = []

        # Add top entities + topics combinations
        if entities and topics:
            for entity in entities[:2]:
                for topic in topics[:2]:
                    queries.append(f"{entity} {topic}".lower())

        # Add entity variations
        for entity in entities[:3]:
            queries.append(entity.lower())
            # Add common commercial modifiers
            queries.append(f"{entity.lower()} jämförelse")
            queries.append(f"{entity.lower()} recension")

        # Limit to 5 unique queries
        return list(dict.fromkeys(queries))[:5]

    def _find_about_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Try to find "About us" or similar content.

        Args:
            soup: BeautifulSoup object

        Returns:
            About excerpt or None
        """
        # Look for common about page indicators
        about_patterns = ['about', 'om oss', 'om', 'about us', 'om sidan']

        for pattern in about_patterns:
            # Check links
            link = soup.find('a', text=re.compile(pattern, re.I))
            if link and link.get('href'):
                # Could fetch the about page here, but skip for now
                pass

            # Check headings
            heading = soup.find(['h1', 'h2', 'h3'], text=re.compile(pattern, re.I))
            if heading:
                # Get next paragraph
                next_p = heading.find_next('p')
                if next_p:
                    text = next_p.get_text(strip=True)
                    return text[:300] + '...' if len(text) > 300 else text

        return None

    def _infer_tone_class(self, text: str) -> str:
        """
        Infer tone class from text content.

        Simple heuristic based on vocabulary.

        Args:
            text: Text content

        Returns:
            Tone class string
        """
        text_lower = text.lower()

        # Academic indicators
        if any(word in text_lower for word in ['forskning', 'studie', 'research', 'study', 'vetenskaplig']):
            return 'academic'

        # Authority/public indicators
        if any(word in text_lower for word in ['myndighet', 'regering', 'government', 'official']):
            return 'authority_public'

        # Consumer magazine indicators
        if any(word in text_lower for word in ['test', 'jämför', 'guide', 'tips', 'råd', 'compare', 'review']):
            return 'consumer_magazine'

        # Default to neutral/informational
        return 'consumer_magazine'

    def _infer_commerciality(self, text: str) -> str:
        """
        Infer allowed commerciality level.

        Args:
            text: Text content

        Returns:
            'low' | 'medium' | 'high'
        """
        text_lower = text.lower()

        # High commerciality indicators
        commercial_words = ['köp', 'buy', 'shop', 'pris', 'price', 'erbjudande', 'deal', 'rabatt']
        commercial_count = sum(1 for word in commercial_words if word in text_lower)

        if commercial_count > 5:
            return 'high'
        elif commercial_count > 2:
            return 'medium'
        else:
            return 'low'
