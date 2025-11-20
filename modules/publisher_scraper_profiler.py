"""
PublisherScraperAndProfiler Module

Profiles the publisher domain to understand tone, voice, and allowed commerciality.
"""

import re
import requests
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from typing import Dict, Any, List

from .base import BaseModule


class PublisherScraperAndProfiler(BaseModule):
    """
    Scrapes and profiles publisher domain.

    Input:
        - publisher_domain: str

    Output:
        - publisher_profile: Dict
    """

    def run(self, publisher_domain: str) -> Dict[str, Any]:
        """
        Profile publisher domain

        Args:
            publisher_domain: Domain to profile (e.g., 'example.com')

        Returns:
            publisher_profile dict
        """
        self.log_step(f"Profiling publisher: {publisher_domain}")

        try:
            # Ensure proper URL format
            if not publisher_domain.startswith('http'):
                base_url = f"https://{publisher_domain}"
            else:
                base_url = publisher_domain

            # Fetch homepage
            homepage_content = self._fetch_page(base_url)
            homepage_soup = BeautifulSoup(homepage_content, 'html.parser')

            # Fetch about page
            about_content = self._fetch_about_page(base_url)
            about_excerpt = self._extract_about_excerpt(about_content) if about_content else ""

            # Sample articles
            sample_urls = self._find_sample_articles(homepage_soup, base_url)

            # Detect language
            detected_language = self._detect_language(homepage_content)

            # Extract topic focus
            topic_focus = self._extract_topic_focus(homepage_soup, sample_urls, base_url)

            # Infer audience
            audience = self._infer_audience(about_excerpt, homepage_content)

            # Classify tone
            tone_class = self._classify_tone(homepage_content, about_excerpt, sample_urls, base_url)

            # Assess commerciality
            allowed_commerciality = self._assess_commerciality(homepage_soup, tone_class)

            # Brand safety notes
            brand_safety_notes = self._identify_brand_safety_notes(about_excerpt, homepage_content)

            profile = {
                "domain": publisher_domain,
                "sample_urls": sample_urls,
                "about_excerpt": about_excerpt[:500] if about_excerpt else "",
                "detected_language": detected_language,
                "topic_focus": topic_focus,
                "audience": audience,
                "tone_class": tone_class,
                "allowed_commerciality": allowed_commerciality,
                "brand_safety_notes": brand_safety_notes
            }

            self.log_step(f"Publisher profiled: tone={tone_class}, commerciality={allowed_commerciality}")
            return profile

        except Exception as e:
            self.logger.error(f"Error profiling publisher {publisher_domain}: {e}")
            return {
                "domain": publisher_domain,
                "sample_urls": [],
                "about_excerpt": "",
                "detected_language": "unknown",
                "topic_focus": [],
                "audience": "unknown",
                "tone_class": "consumer_magazine",  # default
                "allowed_commerciality": "medium",  # default
                "brand_safety_notes": f"Error: {str(e)}"
            }

    def _fetch_page(self, url: str) -> str:
        """Fetch page content"""
        response = requests.get(
            url,
            timeout=self.config.get('timeout', 10),
            headers={'User-Agent': self.config.get('user_agent', 'BacklinkBot/1.0')}
        )
        response.raise_for_status()
        return response.text

    def _fetch_about_page(self, base_url: str) -> str:
        """Try to fetch about page"""
        about_paths = ['/om-oss', '/about', '/about-us', '/om']

        for path in about_paths:
            try:
                url = base_url.rstrip('/') + path
                return self._fetch_page(url)
            except requests.exceptions.RequestException:

        return ""

    def _extract_about_excerpt(self, html: str) -> str:
        """Extract excerpt from about page"""
        soup = BeautifulSoup(html, 'html.parser')

        # Remove nav, footer, etc.
        for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        main = soup.find('main') or soup.find('article') or soup

        text = main.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)

        return text[:800] if text else ""

    def _find_sample_articles(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find 3-5 sample article URLs"""
        # Simple heuristic: find links with /article, /blog, /post, etc.
        article_patterns = re.compile(r'/(article|blog|post|guide|news|tips)/', re.I)

        links = soup.find_all('a', href=True)
        sample_urls = []

        for link in links:
            href = link['href']

            # Make absolute
            if href.startswith('/'):
                href = base_url.rstrip('/') + href
            elif not href.startswith('http'):
                continue

            if article_patterns.search(href) and href not in sample_urls:
                sample_urls.append(href)

            if len(sample_urls) >= 5:
                break

        return sample_urls[:5]

    def _detect_language(self, html: str) -> str:
        """Detect language"""
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)[:500]

        try:
            return detect(text)
        except LangDetectException:
            return "unknown"

    def _extract_topic_focus(self, soup: BeautifulSoup, sample_urls: List[str], base_url: str) -> List[str]:
        """Extract main topic focus (simplified)"""
        # Combine headings from homepage
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'], limit=10)]

        # Analyze sample article titles (if any)
        # For simplicity, just use homepage headings
        text = ' '.join(headings).lower()

        # Simple keyword extraction
        keywords = re.findall(r'\b\w+\b', text)

        from collections import Counter
        common = Counter(keywords).most_common(15)

        stopwords = {'och', 'att', 'det', 'är', 'som', 'för', 'på', 'i', 'en', 'av', 'med', 'till', 'de', 'om', 'har', 'the', 'and', 'to', 'of'}
        topics = [word for word, count in common if word not in stopwords and len(word) > 4]

        return topics[:5]

    def _infer_audience(self, about_text: str, homepage_text: str) -> str:
        """Infer audience (simplified)"""
        text = f"{about_text} {homepage_text}".lower()

        if 'konsument' in text or 'privatperson' in text or 'consumer' in text:
            return "konsumenter/privatpersoner"
        elif 'företag' in text or 'business' in text or 'b2b' in text:
            return "företag/B2B"
        elif 'forskare' in text or 'akademi' in text or 'research' in text:
            return "akademiker/forskare"
        else:
            return "allmänhet"

    def _classify_tone(self, homepage: str, about: str, samples: List[str], base_url: str) -> str:
        """
        Classify tone_class
        Options: academic, authority_public, consumer_magazine, hobby_blog
        Simplified heuristic – in production, use LLM
        """
        text = f"{homepage} {about}".lower()

        # Academic markers
        if 'universitet' in text or 'forskn' in text or 'peer-review' in text or 'citation' in text:
            return "academic"

        # Authority/public
        if 'myndighet' in text or '.gov' in base_url or 'offentlig' in text or 'regelverk' in text:
            return "authority_public"

        # Hobby blog
        if 'jag' in text or 'min' in text or 'personlig' in text or 'blogg' in base_url:
            return "hobby_blog"

        # Default: consumer magazine
        return "consumer_magazine"

    def _assess_commerciality(self, soup: BeautifulSoup, tone_class: str) -> str:
        """
        Assess allowed commerciality
        Options: low, medium, high
        """
        # Check for ads, affiliate links, product listings
        ads = soup.find_all('ins', class_=re.compile('adsbygoogle', re.I))
        affiliate_links = soup.find_all('a', href=re.compile(r'(affiliate|aff|track|ref=)', re.I))
        product_listings = soup.find_all('div', class_=re.compile(r'product|shop|cart', re.I))

        score = 0

        if ads:
            score += 1
        if len(affiliate_links) > 5:
            score += 1
        if product_listings:
            score += 2

        # Adjust by tone
        if tone_class == 'academic' or tone_class == 'authority_public':
            return "low"
        elif score >= 3:
            return "high"
        elif score >= 1:
            return "medium"
        else:
            return "low"

    def _identify_brand_safety_notes(self, about: str, homepage: str) -> str:
        """Identify brand safety restrictions (simplified)"""
        text = f"{about} {homepage}".lower()

        restrictions = []

        if 'inga spelbolag' in text or 'no gambling' in text:
            restrictions.append("Inga spelbolag/gambling")

        if 'inga tveksamma lån' in text or 'no payday loans' in text:
            restrictions.append("Inga tveksamma lån")

        if restrictions:
            return "; ".join(restrictions)
        else:
            return "Inga uppenbara restriktioner identifierade"
