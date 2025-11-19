"""
PageProfile Module - Reusable web page scraping and profiling.

EXTENSIBILITY NOTE:
This module is designed to be reusable across multiple SEO tools including:
- Advanced scrapers with semantic analysis
- Content audit systems
- Competitive analysis tools
- Link analysis platforms
- Database systems for SEO data warehousing

It provides rich, structured page data that can be consumed by various downstream systems.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Optional language detection
try:
    from langdetect import detect, LangDetectException
    HAS_LANGDETECT = True
except ImportError:
    HAS_LANGDETECT = False
    LangDetectException = Exception  # Fallback

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PageProfile:
    """
    Structured profile of a web page.

    This is a rich data structure designed for reusability across SEO tools.
    """
    url: str
    http_status: int
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2_h3_sample: List[str] = field(default_factory=list)
    main_content_excerpt: Optional[str] = None
    detected_language: Optional[str] = None
    core_entities: List[str] = field(default_factory=list)
    core_topics: List[str] = field(default_factory=list)
    internal_links_count: int = 0
    external_links_count: int = 0
    images_count: int = 0
    word_count: int = 0
    # Extensibility: Additional fields for future analytics
    meta_robots: Optional[str] = None
    canonical_url: Optional[str] = None
    schema_types: List[str] = field(default_factory=list)
    og_type: Optional[str] = None
    error_message: Optional[str] = None


class PageProfiler:
    """
    Scrapes and profiles web pages to extract structured information.

    This is a foundational component designed for reuse across multiple SEO tools.
    """

    def __init__(
        self,
        timeout: int = 15,
        user_agent: str = None,
        max_content_length: int = 50000
    ):
        """
        Initialize the page profiler.

        Args:
            timeout: Request timeout in seconds
            user_agent: Custom user agent string
            max_content_length: Maximum content excerpt length in characters
        """
        self.timeout = timeout
        self.user_agent = user_agent or (
            "Mozilla/5.0 (compatible; BacklinkEngine/1.0; +https://example.com/bot)"
        )
        self.max_content_length = max_content_length

    def profile_page(self, url: str) -> PageProfile:
        """
        Profile a web page and extract structured information.

        Args:
            url: URL to profile

        Returns:
            PageProfile with extracted data

        EXTENSIBILITY NOTE:
        This method can be extended to extract additional data points for:
        - Technical SEO audits (page speed hints, resource counts)
        - Content analysis (readability scores, sentiment)
        - Link analysis (link context, anchor text distribution)
        - Schema extraction (JSON-LD parsing)
        """
        logger.info("Profiling page", url=url)

        try:
            # Fetch the page
            response = requests.get(
                url,
                timeout=self.timeout,
                headers={"User-Agent": self.user_agent},
                allow_redirects=True
            )

            profile = PageProfile(url=url, http_status=response.status_code)

            if response.status_code != 200:
                logger.warning("Non-200 status code", url=url, status=response.status_code)
                profile.error_message = f"HTTP {response.status_code}"
                return profile

            # Parse HTML
            soup = BeautifulSoup(response.content, 'lxml')

            # Extract basic metadata
            profile.title = self._extract_title(soup)
            profile.meta_description = self._extract_meta_description(soup)
            profile.h1 = self._extract_h1(soup)
            profile.h2_h3_sample = self._extract_h2_h3_sample(soup)

            # Extract main content
            profile.main_content_excerpt = self._extract_main_content(soup)
            profile.word_count = len(profile.main_content_excerpt.split()) if profile.main_content_excerpt else 0

            # Detect language
            profile.detected_language = self._detect_language(
                profile.title,
                profile.meta_description,
                profile.main_content_excerpt
            )

            # Extract entities and topics (basic implementation)
            profile.core_entities = self._extract_entities(soup, profile.main_content_excerpt)
            profile.core_topics = self._extract_topics(soup, profile.main_content_excerpt)

            # Count links and images
            profile.internal_links_count, profile.external_links_count = self._count_links(soup, url)
            profile.images_count = len(soup.find_all('img'))

            # Extract additional SEO metadata (for extensibility)
            profile.meta_robots = self._extract_meta_robots(soup)
            profile.canonical_url = self._extract_canonical(soup)
            profile.schema_types = self._extract_schema_types(soup)
            profile.og_type = self._extract_og_type(soup)

            logger.info(
                "Page profiling successful",
                url=url,
                language=profile.detected_language,
                word_count=profile.word_count
            )

            return profile

        except requests.RequestException as e:
            logger.error("Request failed", url=url, error=str(e))
            return PageProfile(
                url=url,
                http_status=0,
                error_message=f"Request error: {str(e)}"
            )
        except Exception as e:
            logger.error("Profiling failed", url=url, error=str(e))
            return PageProfile(
                url=url,
                http_status=0,
                error_message=f"Profiling error: {str(e)}"
            )

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else None

    def _extract_meta_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if not meta_desc:
            meta_desc = soup.find('meta', attrs={'property': 'og:description'})
        return meta_desc.get('content', '').strip() if meta_desc else None

    def _extract_h1(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract first H1."""
        h1_tag = soup.find('h1')
        return h1_tag.get_text(strip=True) if h1_tag else None

    def _extract_h2_h3_sample(self, soup: BeautifulSoup, max_count: int = 10) -> List[str]:
        """Extract sample of H2 and H3 headings."""
        headings = []
        for tag in soup.find_all(['h2', 'h3']):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
            if len(headings) >= max_count:
                break
        return headings

    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract main content body text.

        EXTENSIBILITY NOTE:
        This can be enhanced with:
        - Better boilerplate removal algorithms
        - Content block scoring (like Readability)
        - Paragraph-level analysis
        """
        # Remove script, style, nav, footer, header
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            tag.decompose()

        # Try to find main content container
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article|post', re.I)) or
            soup.find('body')
        )

        if not main_content:
            return None

        # Extract text from paragraphs
        paragraphs = main_content.find_all('p')
        text = ' '.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))

        # Truncate if too long
        if len(text) > self.max_content_length:
            text = text[:self.max_content_length] + "..."

        return text if text else None

    def _detect_language(
        self,
        title: Optional[str],
        description: Optional[str],
        content: Optional[str]
    ) -> Optional[str]:
        """Detect page language from text."""
        # Combine available text
        text_parts = [t for t in [title, description, content] if t]
        if not text_parts:
            return None

        combined_text = ' '.join(text_parts)[:1000]  # Use first 1000 chars

        if not HAS_LANGDETECT:
            logger.debug("langdetect not available, using fallback")
            return "en"  # Default fallback

        try:
            return detect(combined_text)
        except LangDetectException:
            logger.debug("Language detection failed")
            return None

    def _extract_entities(self, soup: BeautifulSoup, content: Optional[str]) -> List[str]:
        """
        Extract key entities from the page.

        EXTENSIBILITY NOTE:
        This is a basic implementation. For production or advanced SEO tools, consider:
        - NER with spaCy or similar
        - Entity linking to knowledge bases
        - Sentiment analysis per entity
        - Entity co-occurrence analysis
        """
        entities: Set[str] = set()

        # Extract from title and headings (likely to contain key entities)
        title = soup.find('title')
        if title:
            # Simple heuristic: capitalized words likely entities
            words = title.get_text().split()
            entities.update(w for w in words if w and w[0].isupper() and len(w) > 2)

        for heading in soup.find_all(['h1', 'h2', 'h3']):
            words = heading.get_text().split()
            entities.update(w for w in words if w and w[0].isupper() and len(w) > 2)

        # Extract from strong/bold text (often emphasizes key terms)
        for tag in soup.find_all(['strong', 'b']):
            text = tag.get_text(strip=True)
            if text and len(text) > 2:
                entities.add(text)

        # Limit to top entities (by frequency would be better, but this is simple)
        return sorted(list(entities))[:15]

    def _extract_topics(self, soup: BeautifulSoup, content: Optional[str]) -> List[str]:
        """
        Extract core topics/themes from the page.

        EXTENSIBILITY NOTE:
        Basic implementation. Can be enhanced with:
        - Topic modeling (LDA, NMF)
        - Keyword extraction (RAKE, YAKE, TextRank)
        - Category classification
        - Semantic clustering
        """
        topics: Set[str] = set()

        # Extract from headings (good topic indicators)
        for heading in soup.find_all(['h2', 'h3']):
            text = heading.get_text(strip=True).lower()
            # Split on common separators and take meaningful phrases
            parts = re.split(r'[:\-–—]', text)
            topics.update(p.strip() for p in parts if p.strip() and len(p.strip()) > 3)

        return sorted(list(topics))[:10]

    def _count_links(self, soup: BeautifulSoup, base_url: str) -> Tuple[int, int]:
        """Count internal vs external links."""
        base_domain = urlparse(base_url).netloc
        internal = 0
        external = 0

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith(('http://', 'https://')):
                link_domain = urlparse(href).netloc
                if link_domain == base_domain:
                    internal += 1
                else:
                    external += 1
            elif href.startswith('/'):
                internal += 1

        return internal, external

    def _extract_meta_robots(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract meta robots directive."""
        meta = soup.find('meta', attrs={'name': 'robots'})
        return meta.get('content', '').strip() if meta else None

    def _extract_canonical(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract canonical URL."""
        link = soup.find('link', attrs={'rel': 'canonical'})
        return link.get('href', '').strip() if link else None

    def _extract_schema_types(self, soup: BeautifulSoup) -> List[str]:
        """Extract schema.org types from JSON-LD or microdata."""
        types: Set[str] = set()

        # Check JSON-LD
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                import json
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    types.add(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            types.add(item['@type'])
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse JSON-LD", error=str(e))

        return sorted(list(types))

    def _extract_og_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract Open Graph type."""
        meta = soup.find('meta', attrs={'property': 'og:type'})
        return meta.get('content', '').strip() if meta else None
