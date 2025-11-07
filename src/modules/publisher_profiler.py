"""
Publisher Profiler - Analyzes publisher sites for content tone and audience fit.

Profiles the publication domain to understand:
- Editorial voice and tone
- Topic focus and niche
- Audience characteristics
- Commerciality tolerance
- Brand safety considerations
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urljoin

from .page_profile import PageProfile, PageProfiler
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PublisherProfile:
    """
    Profile of a publisher/publication site.

    Based on BacklinkJobPackage schema's publisher_profile requirements.
    """
    domain: str
    sample_urls: List[str]
    about_excerpt: Optional[str]
    detected_language: str
    topic_focus: List[str]
    audience: str
    tone_class: str  # Next-A1: academic, authority_public, consumer_magazine, hobby_blog
    allowed_commerciality: str  # low, medium, high
    brand_safety_notes: Optional[str] = None


class PublisherProfiler:
    """
    Profiles publisher sites to understand their voice, audience, and constraints.

    Uses the reusable PageProfiler and adds publisher-specific analysis.
    """

    def __init__(self, sample_article_count: int = 3):
        """
        Initialize publisher profiler.

        Args:
            sample_article_count: Number of sample articles to analyze
        """
        self.page_profiler = PageProfiler()
        self.sample_article_count = sample_article_count

    def profile_publisher(self, domain: str) -> PublisherProfile:
        """
        Profile a publisher domain to understand editorial guidelines and constraints.

        Args:
            domain: Publisher domain (e.g., "example-publisher.com")

        Returns:
            PublisherProfile with comprehensive analysis
        """
        logger.info("Profiling publisher", domain=domain)

        # Ensure proper URL format
        if not domain.startswith(('http://', 'https://')):
            base_url = f"https://{domain}"
        else:
            base_url = domain

        # Profile homepage
        homepage_profile = self.page_profiler.profile_page(base_url)

        # Try to find and profile "About" page
        about_profile = self._find_and_profile_about_page(base_url)

        # Sample articles (in production, would crawl/discover articles)
        # For now, we'll work primarily with homepage + about
        sample_urls = [base_url]
        if about_profile:
            sample_urls.append(about_profile.url)

        # Extract topic focus
        topic_focus = self._determine_topic_focus(homepage_profile, about_profile)

        # Classify tone
        tone_class = self._classify_tone(homepage_profile, about_profile)

        # Determine audience
        audience = self._determine_audience(homepage_profile, about_profile, tone_class)

        # Assess commerciality tolerance
        commerciality = self._assess_commerciality(homepage_profile, tone_class)

        # Extract about excerpt
        about_excerpt = None
        if about_profile and about_profile.main_content_excerpt:
            about_excerpt = about_profile.main_content_excerpt[:500]
        elif homepage_profile.meta_description:
            about_excerpt = homepage_profile.meta_description

        # Brand safety notes
        brand_safety = self._assess_brand_safety(tone_class, topic_focus)

        publisher_profile = PublisherProfile(
            domain=domain,
            sample_urls=sample_urls,
            about_excerpt=about_excerpt,
            detected_language=homepage_profile.detected_language or "unknown",
            topic_focus=topic_focus,
            audience=audience,
            tone_class=tone_class,
            allowed_commerciality=commerciality,
            brand_safety_notes=brand_safety
        )

        logger.info(
            "Publisher profiling complete",
            domain=domain,
            tone_class=tone_class,
            topics=len(topic_focus)
        )

        return publisher_profile

    def _find_and_profile_about_page(self, base_url: str) -> Optional[PageProfile]:
        """
        Attempt to find and profile an About/Om Oss page.

        Tries common about page patterns.
        """
        about_paths = [
            "/om-oss", "/about", "/om", "/about-us",
            "/om-oss/", "/about/", "/om/", "/about-us/"
        ]

        for path in about_paths:
            about_url = urljoin(base_url, path)
            try:
                profile = self.page_profiler.profile_page(about_url)
                if profile.http_status == 200:
                    logger.debug("Found about page", url=about_url)
                    return profile
            except Exception as e:
                logger.debug("About page not found", path=path, error=str(e))
                continue

        logger.debug("No about page found", base_url=base_url)
        return None

    def _determine_topic_focus(
        self,
        homepage: PageProfile,
        about: Optional[PageProfile]
    ) -> List[str]:
        """
        Determine the main topic focus areas of the publisher.

        Combines signals from homepage, about page, and meta information.
        """
        topics = set()

        # Extract from homepage topics and entities
        topics.update(homepage.core_topics[:5])

        # Extract from about page if available
        if about:
            topics.update(about.core_topics[:5])

        # Parse from title and description
        title = (homepage.title or "").lower()
        desc = (homepage.meta_description or "").lower()

        # Common Swedish topic keywords
        topic_keywords = {
            "ekonomi": ["ekonomi", "finans", "sparande", "lån", "privatekonomi"],
            "teknik": ["teknik", "tech", "teknologi", "digital"],
            "hälsa": ["hälsa", "health", "välmående", "träning", "kost"],
            "boende": ["boende", "hem", "inredning", "fastighet"],
            "konsument": ["konsument", "köpguide", "test", "recension", "jämförelse"],
            "nyheter": ["nyheter", "news", "aktuellt"],
            "hobby": ["hobby", "fritid", "intresse"],
        }

        for category, keywords in topic_keywords.items():
            if any(kw in title or kw in desc for kw in keywords):
                topics.add(category)

        topics_list = list(topics)
        return topics_list if topics_list else ["allmänt"]

    def _classify_tone(
        self,
        homepage: PageProfile,
        about: Optional[PageProfile]
    ) -> str:
        """
        Classify publisher tone according to Next-A1 PublisherVoice categories.

        Categories:
        - academic: saklig, källförande, låg värdeladdning
        - authority_public: myndighetsnära klarspråk
        - consumer_magazine: lättillgänglig, nytta först
        - hobby_blog: personligt sakkunnig, berättande
        """
        # Check domain and content signals
        domain = homepage.url.lower()
        content = (homepage.main_content_excerpt or "").lower()
        title = (homepage.title or "").lower()

        # Academic signals
        if any(indicator in domain for indicator in [".edu", ".ac.", "universitet", "högskola"]):
            return "academic"
        if homepage.schema_types and any("scholar" in s.lower() for s in homepage.schema_types):
            return "academic"

        # Authority/public signals
        if any(indicator in domain for indicator in [".gov", ".se/myndighet"]):
            return "authority_public"
        if any(word in title for word in ["myndighet", "government", "official"]):
            return "authority_public"

        # Magazine/consumer signals
        magazine_indicators = ["guide", "tips", "råd", "advice", "köpguide", "bäst", "test"]
        if any(indicator in content or indicator in title for indicator in magazine_indicators):
            return "consumer_magazine"

        # Blog/hobby signals
        blog_indicators = ["blogg", "blog", "min", "my", "personlig"]
        if any(indicator in domain or indicator in title for indicator in blog_indicators):
            return "hobby_blog"

        # Default based on formality
        # Check for first-person language (blog-like)
        if any(pronoun in content[:500] for pronoun in [" jag ", " min ", " mig "]):
            return "hobby_blog"

        # Default to consumer magazine (most common for content sites)
        return "consumer_magazine"

    def _determine_audience(
        self,
        homepage: PageProfile,
        about: Optional[PageProfile],
        tone_class: str
    ) -> str:
        """
        Determine primary audience/target demographic.

        Returns a descriptive string about the audience.
        """
        audience_templates = {
            "academic": "Akademiker, forskare och studenter med specialist-intresse",
            "authority_public": "Allmänheten som söker officiell information och vägledning",
            "consumer_magazine": "Konsumenter som söker råd, jämförelser och köpguider",
            "hobby_blog": "Entusiaster med personligt intresse för ämnet",
        }

        base_audience = audience_templates.get(tone_class, "Allmän läsare")

        # Refine based on topic focus if we have that info
        if about and about.main_content_excerpt:
            excerpt_lower = about.main_content_excerpt[:300].lower()
            if "konsument" in excerpt_lower or "consumer" in excerpt_lower:
                return "Konsumenter som söker opartisk information och rådgivning"
            if "profession" in excerpt_lower or "yrkesverksam" in excerpt_lower:
                return "Yrkesverksamma inom branschen"

        return base_audience

    def _assess_commerciality(self, homepage: PageProfile, tone_class: str) -> str:
        """
        Assess tolerance for commercial content.

        Returns: "low", "medium", or "high"
        """
        # Academic and authority = low commerciality
        if tone_class in ["academic", "authority_public"]:
            return "low"

        # Check for affiliate/commercial indicators
        content = (homepage.main_content_excerpt or "").lower()

        high_commercial_indicators = [
            "annons", "advertisement", "partner", "affiliate",
            "bästa erbjudanden", "best deals"
        ]
        if any(indicator in content for indicator in high_commercial_indicators):
            return "high"

        # Blogs tend to be medium, magazines can be high
        if tone_class == "hobby_blog":
            return "medium"

        return "medium"  # Default

    def _assess_brand_safety(self, tone_class: str, topic_focus: List[str]) -> str:
        """
        Determine brand safety guidelines and restrictions.

        Returns notes about what content to avoid.
        """
        restrictions = []

        # Academic/authority sites: strict
        if tone_class in ["academic", "authority_public"]:
            restrictions.append("Inga aggressiva kommersiella erbjudanden")
            restrictions.append("Inga olicensierade gambling- eller låneprodukter")
            restrictions.append("Endast väldokumenterade påståenden")

        # Consumer-focused: moderate
        elif tone_class == "consumer_magazine":
            restrictions.append("Undvik olicensierade finansprodukter")
            restrictions.append("Tydlig disclosure vid partnerskap")

        # Check topic-specific restrictions
        if "ekonomi" in topic_focus or "finans" in topic_focus:
            restrictions.append("Kräver källhänvisningar för finansiella råd")

        if "hälsa" in topic_focus:
            restrictions.append("Medicinska påståenden måste källbeläggas")

        return "; ".join(restrictions) if restrictions else None

    def to_job_package_format(self, publisher_profile: PublisherProfile) -> Dict:
        """
        Convert PublisherProfile to BacklinkJobPackage schema format.

        Returns:
            Dictionary matching the publisher_profile section of BacklinkJobPackage
        """
        return {
            "domain": publisher_profile.domain,
            "sample_urls": publisher_profile.sample_urls,
            "about_excerpt": publisher_profile.about_excerpt,
            "detected_language": publisher_profile.detected_language,
            "topic_focus": publisher_profile.topic_focus,
            "audience": publisher_profile.audience,
            "tone_class": publisher_profile.tone_class,
            "allowed_commerciality": publisher_profile.allowed_commerciality,
            "brand_safety_notes": publisher_profile.brand_safety_notes,
        }
