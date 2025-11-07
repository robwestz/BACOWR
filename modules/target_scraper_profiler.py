"""
TargetScraperAndProfiler Module

Fetches and profiles the target URL to understand what the link can represent.
"""

import re
import requests
from bs4 import BeautifulSoup
from langdetect import detect, LangDetectException
from typing import Dict, Any, List
from urllib.parse import urlparse

from .base import BaseModule


class TargetScraperAndProfiler(BaseModule):
    """
    Scrapes and profiles target URL.

    Input:
        - target_url: str

    Output:
        - target_profile: Dict (according to backlink_job_package.schema.json)
    """

    def run(self, target_url: str) -> Dict[str, Any]:
        """
        Fetch and profile target URL

        Args:
            target_url: URL to profile

        Returns:
            target_profile dict
        """
        self.log_step(f"Scraping target: {target_url}")

        try:
            # Fetch HTML
            response = requests.get(
                target_url,
                timeout=self.config.get('timeout', 10),
                headers={'User-Agent': self.config.get('user_agent', 'BacklinkBot/1.0')},
                allow_redirects=True,
                max_redirects=3
            )
            response.raise_for_status()

            html = response.text
            http_status = response.status_code

            # Parse
            soup = BeautifulSoup(html, 'html.parser')

            # Extract structured elements
            title = self._extract_title(soup)
            meta_description = self._extract_meta_description(soup)
            h1 = self._extract_h1(soup)
            h2_h3_sample = self._extract_headings_sample(soup)
            main_content_excerpt = self._extract_main_content(soup)

            # Language detection
            detected_language = self._detect_language(main_content_excerpt or title)

            # Entity extraction (simplified – would use NER or LLM in production)
            core_entities = self._extract_entities(title, h1, h2_h3_sample)

            # Topic extraction
            core_topics = self._extract_topics(h2_h3_sample, main_content_excerpt)

            # Core offer
            core_offer = self._infer_core_offer(title, meta_description, main_content_excerpt)

            # Candidate main queries
            candidate_main_queries = self._generate_candidate_queries(title, h1, core_entities)

            profile = {
                "url": target_url,
                "http_status": http_status,
                "title": title,
                "meta_description": meta_description,
                "h1": h1,
                "h2_h3_sample": h2_h3_sample,
                "main_content_excerpt": main_content_excerpt[:1000] if main_content_excerpt else "",
                "detected_language": detected_language,
                "core_entities": core_entities,
                "core_topics": core_topics,
                "core_offer": core_offer,
                "candidate_main_queries": candidate_main_queries
            }

            self.log_step(f"Target profiled: {len(core_entities)} entities, lang={detected_language}")
            return profile

        except Exception as e:
            self.logger.error(f"Error scraping target {target_url}: {e}")
            # Return minimal profile with error
            return {
                "url": target_url,
                "http_status": 0,
                "title": "",
                "meta_description": "",
                "h1": "",
                "h2_h3_sample": [],
                "main_content_excerpt": "",
                "detected_language": "unknown",
                "core_entities": [],
                "core_topics": [],
                "core_offer": f"Error: {str(e)}",
                "candidate_main_queries": []
            }

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else ""

    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description"""
        meta = soup.find('meta', attrs={'name': 'description'})
        return meta.get('content', '') if meta else ""

    def _extract_h1(self, soup: BeautifulSoup) -> str:
        """Extract first H1"""
        h1 = soup.find('h1')
        return h1.get_text(strip=True) if h1 else ""

    def _extract_headings_sample(self, soup: BeautifulSoup) -> List[str]:
        """Extract sample of H2/H3 headings (first 5-7)"""
        headings = []
        for tag in soup.find_all(['h2', 'h3'], limit=7):
            text = tag.get_text(strip=True)
            if text:
                headings.append(text)
        return headings

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content excerpt (600-1000 chars)"""
        # Remove scripts, styles, nav, footer
        for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            tag.decompose()

        # Try to find main content
        main = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile('content|main'))

        if main:
            text = main.get_text(separator=' ', strip=True)
        else:
            text = soup.get_text(separator=' ', strip=True)

        # Clean whitespace
        text = re.sub(r'\s+', ' ', text)

        return text[:1000] if text else ""

    def _detect_language(self, text: str) -> str:
        """Detect language using langdetect"""
        if not text or len(text) < 20:
            return "unknown"

        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return "unknown"

    def _extract_entities(self, title: str, h1: str, headings: List[str]) -> List[str]:
        """
        Extract core entities (simplified)
        In production: use NER (spaCy, Stanza) or LLM
        """
        # Combine text
        text = f"{title} {h1} {' '.join(headings)}"

        # Simple heuristic: capitalized phrases, brands
        # This is a placeholder – real implementation would use NER
        words = text.split()
        entities = []

        # Capitalized words (very naive)
        for word in words:
            if word and word[0].isupper() and len(word) > 3 and word not in ['Detta', 'Här', 'Alla']:
                if word not in entities:
                    entities.append(word)

        return entities[:6]  # Top 6

    def _extract_topics(self, headings: List[str], content: str) -> List[str]:
        """
        Extract core topics
        Simplified: keywords from headings + content
        """
        # Placeholder: In production, use topic modeling or LLM
        text = f"{' '.join(headings)} {content}"
        words = re.findall(r'\b\w+\b', text.lower())

        # Frequency-based (very simple)
        from collections import Counter
        common = Counter(words).most_common(10)

        # Filter out stopwords (simplified)
        stopwords = {'och', 'att', 'det', 'är', 'som', 'för', 'på', 'i', 'en', 'av', 'med', 'till', 'de', 'om', 'har'}
        topics = [word for word, count in common if word not in stopwords and len(word) > 4]

        return topics[:5]

    def _infer_core_offer(self, title: str, meta_desc: str, content: str) -> str:
        """
        Infer what the page offers
        Simplified: concatenate and truncate
        In production: use LLM to summarize
        """
        text = f"{title}. {meta_desc}. {content[:200]}"
        return text[:250] if text else "Unknown offer"

    def _generate_candidate_queries(self, title: str, h1: str, entities: List[str]) -> List[str]:
        """
        Generate candidate main queries
        Simplified: variations of title/h1 + entities
        In production: use LLM or query expansion
        """
        queries = []

        if title:
            queries.append(title.lower())

        if h1 and h1 != title:
            queries.append(h1.lower())

        # Combine entities
        if len(entities) >= 2:
            queries.append(f"{entities[0]} {entities[1]}".lower())

        return queries[:4]
