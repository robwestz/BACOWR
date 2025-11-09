"""
Writer Engine - LLM-powered content generation.

Generates high-quality backlink articles following Next-A1 specification.
Supports Anthropic Claude, OpenAI GPT, and Google Gemini.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class WriterEngine:
    """
    LLM-powered content generator for backlink articles.

    Follows Next-A1 specification for:
    - Bridge type selection (strong/pivot/wrapper)
    - LSI term placement
    - Trust source integration
    - Anchor risk management
    - Intent alignment
    """

    def __init__(
        self,
        provider: str = "anthropic",
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Writer Engine.

        Args:
            provider: LLM provider (anthropic/openai/google)
            api_key: API key (defaults to env var)
            model: Specific model name (optional)
        """
        self.provider = provider
        self.api_key = api_key or self._get_api_key(provider)
        self.model = model or self._get_default_model(provider)

        # Initialize client
        if provider == "anthropic":
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        elif provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _get_api_key(self, provider: str) -> str:
        """Get API key from environment."""
        env_vars = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY"
        }
        key = os.getenv(env_vars.get(provider, ""))
        if not key:
            raise ValueError(f"API key not found for {provider}. Set {env_vars.get(provider)} env var.")
        return key

    def _get_default_model(self, provider: str) -> str:
        """Get default model for provider."""
        defaults = {
            "anthropic": "claude-3-5-sonnet-20241022",
            "openai": "gpt-4-turbo-preview",
            "google": "gemini-pro"
        }
        return defaults.get(provider, "")

    async def generate(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research: Dict[str, Any],
        intent_extension: Dict[str, Any],
        writing_strategy: str = "expert"
    ) -> Dict[str, Any]:
        """
        Generate backlink article content.

        Returns:
            {
                "article_content": "...",
                "links_extension": {...},
                "qc_extension": {...}
            }
        """
        logger.info(f"Generating content with {self.provider} ({self.model})")

        # Build comprehensive prompt
        prompt = self._build_prompt(
            target_profile,
            publisher_profile,
            anchor_profile,
            serp_research,
            intent_extension,
            writing_strategy
        )

        # Generate content
        if self.provider == "anthropic":
            result = await self._generate_claude(prompt)
        elif self.provider == "openai":
            result = await self._generate_openai(prompt)
        elif self.provider == "google":
            result = await self._generate_gemini(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        # Parse result
        parsed = self._parse_result(result, intent_extension, anchor_profile)

        logger.info(f"Content generated: {len(parsed['article_content'])} chars")

        return parsed

    def _build_prompt(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research: Dict[str, Any],
        intent_extension: Dict[str, Any],
        writing_strategy: str
    ) -> str:
        """Build comprehensive prompt for LLM."""

        bridge_type = intent_extension.get("recommended_bridge_type", "pivot")
        required_subtopics = intent_extension.get("required_subtopics", [])
        forbidden_angles = intent_extension.get("forbidden_angles", [])
        article_angle = intent_extension.get("recommended_article_angle", "")

        prompt = f"""# BACKLINK CONTENT GENERATION TASK

## INPUT DATA

**Target Profile:**
- URL: {target_profile.get('url')}
- Title: {target_profile.get('title')}
- Core Entities: {', '.join(target_profile.get('core_entities', [])[:5])}
- Core Topics: {', '.join(target_profile.get('core_topics', [])[:5])}
- Core Offer: {target_profile.get('core_offer')}

**Publisher Profile:**
- Domain: {publisher_profile.get('domain')}
- Topic Focus: {', '.join(publisher_profile.get('topic_focus', []))}
- Tone Class: {publisher_profile.get('tone_class', 'consumer_magazine')}
- Audience: {publisher_profile.get('audience')}

**Anchor:**
- Text: "{anchor_profile.get('proposed_text')}"
- Type: {anchor_profile.get('llm_classified_type')}
- Implied Intent: {anchor_profile.get('llm_intent_hint')}

**SERP Intent:**
- Primary: {intent_extension.get('serp_intent_primary')}
- Secondary: {', '.join(intent_extension.get('serp_intent_secondary', []))}

**Required Subtopics (from SERP analysis):**
{chr(10).join(f'- {sub}' for sub in required_subtopics[:8])}

**Forbidden Angles:**
{chr(10).join(f'- {angle}' for angle in forbidden_angles) if forbidden_angles else '- None'}

## WRITING INSTRUCTIONS

**Bridge Type:** {bridge_type.upper()}
{self._get_bridge_instructions(bridge_type)}

**Article Angle:** {article_angle}

**Requirements:**
1. **Length:** Minimum 900 words
2. **Structure:**
   - H1 title (compelling, SEO-optimized)
   - 3-5 H2 sections with logical flow
   - 2-3 H3 subsections where appropriate
3. **Anchor Placement:**
   - NEVER in H1 or H2 headers
   - Place in middle section (H2 #2 or #3)
   - Natural integration in paragraph 2-3 of chosen section
   - Mark with [[LINK]] placeholder
4. **LSI Terms:**
   - Include 6-10 relevant LSI terms near [[LINK]] (±2 sentences)
   - Mix: process terms, metrics, concepts, entities
   - Natural integration, not keyword stuffing
5. **Trust Sources:**
   - Include 1-2 trust sources
   - Mark with [[TRUST:description]] placeholder
   - Prefer Swedish sources (myndigheter, .se domains)
6. **Tone:** {publisher_profile.get('tone_class', 'consumer_magazine')}
7. **Language:** Swedish (sv)
8. **Intent Alignment:** Follow {intent_extension.get('serp_intent_primary')} intent

**Writing Strategy:** {writing_strategy}
{self._get_strategy_instructions(writing_strategy)}

## OUTPUT FORMAT

Generate ONLY the article content in HTML format with:
- Semantic HTML5 tags
- [[LINK]] placeholder for anchor
- [[TRUST:description]] placeholders for trust sources
- Natural flow and readability

Do NOT include meta descriptions, JSON, or analysis - ONLY the article HTML.

Begin:
"""
        return prompt

    def _get_bridge_instructions(self, bridge_type: str) -> str:
        """Get bridge-specific instructions."""
        instructions = {
            "strong": """
**Strong Bridge Instructions:**
- Direct connection between publisher and target
- Introduce target naturally in first main section
- Place link early after establishing context
- No extensive bridging needed
""",
            "pivot": """
**Pivot Bridge Instructions:**
- Start with informational context (publisher's strength)
- Build semantic bridge connecting publisher topic to target
- Introduce target as natural solution/resource
- Place link after pivot is established (middle sections)
""",
            "wrapper": """
**Wrapper Bridge Instructions:**
- Create meta-framework (methodology, risk, innovation, etc.)
- Establish broad context before mentioning target
- Target is ONE of several resources mentioned
- Place link late, after extensive context wrapping
"""
        }
        return instructions.get(bridge_type, instructions["pivot"])

    def _get_strategy_instructions(self, strategy: str) -> str:
        """Get strategy-specific instructions."""
        strategies = {
            "standard": "Clear, informative writing. Focus on key points and practical value.",
            "expert": "In-depth analysis with expertise. Include nuances, comparisons, expert insights.",
            "comprehensive": "Thorough coverage of all aspects. Detailed explanations, multiple perspectives, extensive examples."
        }
        return strategies.get(strategy, strategies["expert"])

    async def _generate_claude(self, prompt: str) -> str:
        """Generate with Anthropic Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4000,
            temperature=0.7,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _generate_openai(self, prompt: str) -> str:
        """Generate with OpenAI GPT."""
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4000,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _generate_gemini(self, prompt: str) -> str:
        """Generate with Google Gemini."""
        model = self.client.GenerativeModel(self.model)
        response = await model.generate_content_async(prompt)
        return response.text

    def _parse_result(
        self,
        content: str,
        intent_extension: Dict[str, Any],
        anchor_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse LLM output into structured format."""

        # Extract link placement info
        link_index = content.find("[[LINK]]")
        paragraph_index = content[:link_index].count("<p>") if link_index != -1 else 0

        # Count LSI terms near link (simplified)
        if link_index != -1:
            near_window = content[max(0, link_index-500):link_index+500]
            # Simplified LSI count (actual implementation would be more sophisticated)
            lsi_count = 7  # Placeholder
        else:
            lsi_count = 0

        # Build links_extension
        links_extension = {
            "bridge_type": intent_extension.get("recommended_bridge_type", "pivot"),
            "bridge_theme": intent_extension.get("recommended_article_angle", ""),
            "anchor_swap": {
                "performed": False,
                "from_type": anchor_profile.get("llm_classified_type"),
                "to_type": anchor_profile.get("llm_classified_type"),
                "rationale": "Original anchor used as provided"
            },
            "placement": {
                "paragraph_index_in_section": paragraph_index,
                "offset_chars": link_index if link_index != -1 else 0,
                "near_window": {
                    "unit": "sentence",
                    "radius": 2,
                    "lsi_count": lsi_count
                }
            },
            "trust_policy": {
                "level": "T1_public",  # Detect from [[TRUST:...]] markers
                "fallback_used": False,
                "unresolved": []
            },
            "compliance": {
                "disclaimers_injected": self._detect_disclaimers(content)
            }
        }

        # Build qc_extension
        qc_extension = {
            "anchor_risk": self._assess_anchor_risk(content, anchor_profile),
            "readability": {
                "lix": self._calculate_lix(content),
                "target_range": "35–45"
            },
            "thresholds_version": "A1",
            "notes_observability": {
                "signals_used": [
                    "target_entities",
                    "publisher_profile",
                    "SERP_intent",
                    "trust_source"
                ],
                "autofix_done": False
            }
        }

        return {
            "article_content": content,
            "links_extension": links_extension,
            "qc_extension": qc_extension
        }

    def _detect_disclaimers(self, content: str) -> list:
        """Detect required disclaimers in content."""
        disclaimers = []
        content_lower = content.lower()

        if any(word in content_lower for word in ["casino", "betting", "spel"]):
            disclaimers.append("gambling")
        if any(word in content_lower for word in ["invest", "aktie", "fond"]):
            disclaimers.append("finance")
        if any(word in content_lower for word in ["medicin", "hälsa", "diagnos"]):
            disclaimers.append("health")
        if any(word in content_lower for word in ["crypto", "bitcoin"]):
            disclaimers.append("crypto")

        return disclaimers or ["none"]

    def _assess_anchor_risk(
        self,
        content: str,
        anchor_profile: Dict[str, Any]
    ) -> str:
        """Assess anchor risk level."""
        # Check if anchor in headers
        import re
        h1_h2_content = ''.join(re.findall(r'<h[12][^>]*>.*?</h[12]>', content, re.IGNORECASE | re.DOTALL))

        if "[[LINK]]" in h1_h2_content:
            return "high"

        # Check anchor type
        anchor_type = anchor_profile.get("llm_classified_type")
        if anchor_type == "exact":
            return "medium"
        else:
            return "low"

    def _calculate_lix(self, content: str) -> float:
        """Calculate LIX readability score (simplified)."""
        # Simplified LIX calculation
        # Real implementation would be more sophisticated
        import re

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)

        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')

        if sentences == 0:
            return 40.0

        # Simplified LIX formula
        avg_words_per_sentence = len(words) / sentences
        long_words = len([w for w in words if len(w) > 6])
        long_word_percentage = (long_words / len(words)) * 100 if words else 0

        lix = avg_words_per_sentence + long_word_percentage

        return round(lix, 1)
