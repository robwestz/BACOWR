"""
LLM-Enhanced Profiling Components

Uses LLM to improve:
- Anchor classification
- Entity extraction
- Publisher tone analysis
- Intent inference

Provides much better accuracy than regex-based approaches.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum


class LLMProvider(Enum):
    """Supported providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class LLMEnhancer:
    """
    LLM-based enhancements for profiling.

    Uses whichever LLM provider is available to enhance:
    - Anchor text classification
    - Entity and topic extraction
    - Publisher tone detection
    - Intent inference
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize LLM Enhancer.

        Args:
            provider: 'anthropic', 'openai', or 'google' (auto-detect if None)
            model: Specific model to use (uses default if None)
        """
        self.provider, self.client = self._init_provider(provider)
        self.model = model or self._get_default_model()

    def _init_provider(self, preferred: Optional[str]) -> Tuple[str, Any]:
        """Initialize LLM provider"""

        # Try preferred first
        if preferred:
            if preferred == 'anthropic' and os.getenv('ANTHROPIC_API_KEY'):
                import anthropic
                return 'anthropic', anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

            elif preferred == 'openai' and os.getenv('OPENAI_API_KEY'):
                import openai
                return 'openai', openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            elif preferred == 'google' and os.getenv('GOOGLE_API_KEY'):
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                return 'google', genai

        # Auto-detect
        if os.getenv('ANTHROPIC_API_KEY'):
            import anthropic
            return 'anthropic', anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        if os.getenv('OPENAI_API_KEY'):
            import openai
            return 'openai', openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        if os.getenv('GOOGLE_API_KEY'):
            import google.generativeai as genai
            genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
            return 'google', genai

        raise ValueError("No LLM API key found. Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")

    def _get_default_model(self) -> str:
        """Get default model for provider"""
        models = {
            'anthropic': 'claude-3-haiku-20240307',  # Fast, cheap, works with all API keys
            'openai': 'gpt-4o-mini',  # Fast and cheap
            'google': 'gemini-1.5-flash'  # Fast and cheap
        }
        return models.get(self.provider, 'claude-3-haiku-20240307')

    def classify_anchor(
        self,
        anchor_text: str,
        target_title: Optional[str] = None,
        context: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Classify anchor text with LLM.

        Args:
            anchor_text: The anchor text to classify
            target_title: Optional target page title for context
            context: Optional additional context

        Returns:
            {
                'type': 'exact' | 'partial' | 'brand' | 'generic',
                'intent': 'info_primary' | 'commercial_research' | 'transactional' | ...,
                'confidence': 'high' | 'medium' | 'low',
                'reasoning': 'explanation'
            }
        """
        prompt = f"""Classify this anchor text for SEO purposes.

Anchor text: "{anchor_text}"
{f'Target page title: "{target_title}"' if target_title else ''}
{f'Context: {context}' if context else ''}

Classify the anchor into:

1. TYPE (choose one):
- exact: Contains exact target keyword/phrase
- partial: Contains part of target keyword
- brand: Contains brand name
- generic: Generic phrase (e.g., "click here", "read more")

2. INTENT (choose one):
- info_primary: Seeking general information
- commercial_research: Researching before purchase
- transactional: Ready to buy/convert
- navigational_brand: Looking for specific brand
- support: Seeking help/guidance

3. CONFIDENCE: high, medium, or low

Respond in JSON format:
{{
  "type": "...",
  "intent": "...",
  "confidence": "...",
  "reasoning": "brief explanation"
}}"""

        response = self._call_llm(prompt, max_tokens=200)

        # Parse JSON response
        import json
        try:
            result = json.loads(response.strip().replace('```json', '').replace('```', ''))
            return result
        except:
            # Fallback
            return {
                'type': 'partial',
                'intent': 'commercial_research',
                'confidence': 'low',
                'reasoning': 'Failed to parse LLM response'
            }

    def extract_entities_and_topics(
        self,
        title: str,
        content_excerpt: str,
        headings: List[str]
    ) -> Dict[str, List[str]]:
        """
        Extract entities and topics using LLM.

        Args:
            title: Page title
            content_excerpt: First ~500 chars of content
            headings: List of H1, H2, H3 headings

        Returns:
            {
                'entities': [list of key entities],
                'topics': [list of main topics],
                'categories': [list of content categories]
            }
        """
        headings_str = '\n'.join([f"- {h}" for h in headings[:10]])

        prompt = f"""Extract key entities and topics from this web page content.

Title: {title}

Headings:
{headings_str}

Content excerpt:
{content_excerpt[:500]}

Extract:
1. ENTITIES: Specific names, products, brands, organizations (max 5)
2. TOPICS: Main themes and subjects discussed (max 5)
3. CATEGORIES: Broad content categories (max 3)

Respond in JSON format:
{{
  "entities": ["Entity 1", "Entity 2", ...],
  "topics": ["Topic 1", "Topic 2", ...],
  "categories": ["Category 1", "Category 2", ...]
}}"""

        response = self._call_llm(prompt, max_tokens=300)

        # Parse JSON
        import json
        try:
            result = json.loads(response.strip().replace('```json', '').replace('```', ''))
            return result
        except:
            # Fallback to empty lists
            return {
                'entities': [],
                'topics': [],
                'categories': []
            }

    def analyze_publisher_tone(
        self,
        content_samples: List[str],
        about_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze publisher tone and voice using LLM.

        Args:
            content_samples: List of content excerpts from site
            about_text: Optional "About Us" text

        Returns:
            {
                'tone_class': 'academic' | 'authority_public' | 'consumer_magazine' | 'hobby_blog',
                'voice_characteristics': [list of traits],
                'target_audience': 'description',
                'commerciality': 'low' | 'medium' | 'high',
                'confidence': 'high' | 'medium' | 'low'
            }
        """
        samples_text = '\n\n---\n\n'.join(content_samples[:3])

        prompt = f"""Analyze the tone and voice of this publisher/website.

Content samples:
{samples_text}

{f'About section: {about_text}' if about_text else ''}

Determine:

1. TONE CLASS (choose one):
- academic: Scholarly, research-focused, formal citations
- authority_public: Government, official institutions, authoritative
- consumer_magazine: Consumer-focused, reviews, comparisons, advice
- hobby_blog: Personal, enthusiast-driven, casual

2. VOICE CHARACTERISTICS: List 3-5 traits (e.g., "professional", "friendly", "data-driven")

3. TARGET AUDIENCE: Describe who this is written for

4. COMMERCIALITY: low, medium, or high (how commercial/sales-oriented)

5. CONFIDENCE: high, medium, or low

Respond in JSON format:
{{
  "tone_class": "...",
  "voice_characteristics": ["trait1", "trait2", ...],
  "target_audience": "description",
  "commerciality": "...",
  "confidence": "..."
}}"""

        response = self._call_llm(prompt, max_tokens=400)

        # Parse JSON
        import json
        try:
            result = json.loads(response.strip().replace('```json', '').replace('```', ''))
            return result
        except:
            return {
                'tone_class': 'consumer_magazine',
                'voice_characteristics': [],
                'target_audience': 'general public',
                'commerciality': 'medium',
                'confidence': 'low'
            }

    def infer_page_intent(
        self,
        title: str,
        url: str,
        content_excerpt: str,
        cta_elements: List[str]
    ) -> Dict[str, str]:
        """
        Infer primary intent of a page using LLM.

        Args:
            title: Page title
            url: Page URL
            content_excerpt: Content sample
            cta_elements: List of call-to-action texts found

        Returns:
            {
                'primary_intent': 'info_primary' | 'commercial_research' | 'transactional' | ...,
                'intent_confidence': 'high' | 'medium' | 'low',
                'secondary_intents': [list],
                'reasoning': 'explanation'
            }
        """
        cta_str = ', '.join([f'"{cta}"' for cta in cta_elements[:5]]) if cta_elements else 'None'

        prompt = f"""Determine the primary intent of this web page.

URL: {url}
Title: {title}
CTAs found: {cta_str}

Content excerpt:
{content_excerpt[:400]}

Classify PRIMARY INTENT (choose one):
- info_primary: Purely informational, educational
- commercial_research: Helping users compare/research before buying
- transactional: Focused on conversion/purchase
- transactional_with_info_support: Sells but provides info too
- navigational_brand: Brand homepage/about page
- support: Customer support/help content

Also identify any SECONDARY INTENTS present.

Respond in JSON format:
{{
  "primary_intent": "...",
  "intent_confidence": "high|medium|low",
  "secondary_intents": ["...", "..."],
  "reasoning": "brief explanation"
}}"""

        response = self._call_llm(prompt, max_tokens=250)

        # Parse JSON
        import json
        try:
            result = json.loads(response.strip().replace('```json', '').replace('```', ''))
            return result
        except:
            return {
                'primary_intent': 'info_primary',
                'intent_confidence': 'low',
                'secondary_intents': [],
                'reasoning': 'Failed to parse'
            }

    def _call_llm(self, prompt: str, max_tokens: int = 500) -> str:
        """Call LLM with appropriate provider"""

        if self.provider == 'anthropic':
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temp for classification tasks
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif self.provider == 'openai':
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SEO and content analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.3
            )
            return response.choices[0].message.content

        elif self.provider == 'google':
            model = self.client.GenerativeModel(self.model)
            response = model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': 0.3
                }
            )
            return response.text

        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
