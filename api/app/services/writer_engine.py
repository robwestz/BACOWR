"""
Writer Engine Service - BACOWR Demo Environment

Multi-provider LLM content generation with intelligent prompting strategies.
Supports bridge types (strong/pivot/wrapper) and LSI term injection.

Part of the BACOWR Demo API - Production-ready content generation service.
"""

import os
import time
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = 'anthropic'
    OPENAI = 'openai'
    GOOGLE = 'google'


class BridgeType(Enum):
    """Bridge types for backlink content"""
    STRONG = 'strong'      # Direct connection, target is main focus
    PIVOT = 'pivot'        # Informational context leading to target
    WRAPPER = 'wrapper'    # Extensive context, target is one of several options


@dataclass
class GenerationMetrics:
    """Metrics for tracking generation performance"""
    provider: str
    model: str
    strategy: str
    duration_seconds: float = 0.0
    total_tokens: int = 0
    cost_usd: float = 0.0
    retries: int = 0
    success: bool = True


class WriterEngine:
    """
    Production-grade writer engine with multi-provider LLM support.

    Features:
    - Multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini)
    - Intelligent prompting strategies (expert, balanced, fast)
    - Bridge type implementation (strong/pivot/wrapper)
    - LSI term injection (6-10 terms within ±2 sentences)
    - Context-aware content generation
    - Automatic fallback between providers

    This is a clean, production-ready service designed for the BACOWR demo environment.
    """

    # Model configurations
    MODEL_CONFIGS = {
        LLMProvider.ANTHROPIC: {
            'default_model': 'claude-3-5-sonnet-20240620',
            'fallback_model': 'claude-3-haiku-20240307',
            'max_tokens': 4000,
            'temperature': 0.7
        },
        LLMProvider.OPENAI: {
            'default_model': 'gpt-4o',
            'fallback_model': 'gpt-4o-mini',
            'max_tokens': 4000,
            'temperature': 0.7
        },
        LLMProvider.GOOGLE: {
            'default_model': 'gemini-2.0-flash-exp',
            'fallback_model': 'gemini-1.5-flash',
            'max_tokens': 4000,
            'temperature': 0.7
        }
    }

    def __init__(
        self,
        llm_provider: str = 'anthropic',
        auto_fallback: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize Writer Engine.

        Args:
            llm_provider: Primary LLM provider ('anthropic', 'openai', 'google')
            auto_fallback: Automatically try fallback providers on failure
            max_retries: Maximum retry attempts per provider
        """
        self.primary_provider = LLMProvider(llm_provider.lower())
        self.auto_fallback = auto_fallback
        self.max_retries = max_retries

        # Initialize clients
        self._clients = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients for available providers"""
        # Anthropic
        if os.getenv('ANTHROPIC_API_KEY'):
            try:
                import anthropic
                self._clients[LLMProvider.ANTHROPIC] = anthropic.Anthropic(
                    api_key=os.getenv('ANTHROPIC_API_KEY')
                )
            except ImportError:
                print("Warning: anthropic package not installed")

        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                self._clients[LLMProvider.OPENAI] = openai.OpenAI(
                    api_key=os.getenv('OPENAI_API_KEY')
                )
            except ImportError:
                print("Warning: openai package not installed")

        # Google
        if os.getenv('GOOGLE_API_KEY'):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                self._clients[LLMProvider.GOOGLE] = genai
            except ImportError:
                print("Warning: google-generativeai package not installed")

    def generate_article(
        self,
        context: Dict[str, Any],
        strategy: str = 'expert'
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate article from job context.

        Args:
            context: Complete job package with all profiles and research
            strategy: Generation strategy - 'expert', 'balanced', or 'fast'
                - expert: Multi-stage generation with refinement
                - balanced: Single comprehensive prompt
                - fast: Quick generation with minimal prompting

        Returns:
            (article_markdown, generation_metrics)
        """
        start_time = time.time()

        metrics = GenerationMetrics(
            provider=self.primary_provider.value,
            model='',
            strategy=strategy
        )

        try:
            # Build prompt based on strategy
            prompt = self._build_prompt(context, strategy)

            # Generate with primary provider
            article = self._call_llm(
                provider=self.primary_provider,
                prompt=prompt,
                max_tokens=4000
            )

            # Update metrics
            config = self.MODEL_CONFIGS[self.primary_provider]
            metrics.model = config['default_model']
            metrics.duration_seconds = time.time() - start_time
            metrics.success = True

            return article, metrics.__dict__

        except Exception as e:
            print(f"Generation failed with {self.primary_provider.value}: {e}")

            # Try fallback providers if enabled
            if self.auto_fallback:
                for fallback_provider in [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GOOGLE]:
                    if fallback_provider == self.primary_provider:
                        continue

                    if fallback_provider not in self._clients:
                        continue

                    try:
                        print(f"Trying fallback provider: {fallback_provider.value}")
                        prompt = self._build_prompt(context, strategy)
                        article = self._call_llm(fallback_provider, prompt, 4000)

                        # Update metrics
                        config = self.MODEL_CONFIGS[fallback_provider]
                        metrics.provider = fallback_provider.value
                        metrics.model = config['default_model']
                        metrics.duration_seconds = time.time() - start_time
                        metrics.success = True

                        return article, metrics.__dict__

                    except Exception as fallback_error:
                        print(f"Fallback {fallback_provider.value} also failed: {fallback_error}")
                        continue

            # All providers failed
            metrics.success = False
            metrics.duration_seconds = time.time() - start_time
            raise RuntimeError(f"All LLM providers failed. Last error: {e}")

    def _build_prompt(self, context: Dict[str, Any], strategy: str) -> str:
        """
        Build generation prompt based on strategy.

        Args:
            context: Job package context
            strategy: Generation strategy

        Returns:
            Complete prompt string
        """
        if strategy == 'expert':
            return self._build_expert_prompt(context)
        elif strategy == 'balanced':
            return self._build_balanced_prompt(context)
        else:  # fast
            return self._build_fast_prompt(context)

    def _build_expert_prompt(self, context: Dict[str, Any]) -> str:
        """Build comprehensive expert-level prompt"""

        # Extract key context
        input_minimal = context.get('input_minimal', {})
        target_profile = context.get('target_profile', {})
        publisher_profile = context.get('publisher_profile', {})
        intent_extension = context.get('intent_extension', {})
        serp_research = context.get('serp_research_extension', {})
        constraints = context.get('generation_constraints', {})

        # Determine bridge type
        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')
        bridge_description = self._get_bridge_description(bridge_type)

        # Extract LSI terms
        lsi_terms = self._extract_lsi_terms(context)

        # Build language
        language = constraints.get('language', 'sv')
        language_name = 'Swedish' if language == 'sv' else 'English'

        # Build comprehensive prompt
        prompt = f"""You are a professional SEO content writer specializing in high-quality backlink articles.

ASSIGNMENT:
Write a {constraints.get('min_word_count', 900)}+ word article in {language_name} that naturally links to the target URL.

PUBLISHER CONTEXT:
- Domain: {publisher_profile.get('domain', 'N/A')}
- Editorial Tone: {publisher_profile.get('tone_class', 'professional')}
- Writing Style: Match the publisher's {publisher_profile.get('tone_class', 'professional')} voice
- Commerciality Level: {publisher_profile.get('allowed_commerciality', 'medium')}

TARGET CONTEXT:
- URL: {target_profile.get('url', 'N/A')}
- Page Title: {target_profile.get('title', 'N/A')}
- Core Entities: {', '.join(target_profile.get('core_entities', [])[:3])}
- Core Topics: {', '.join(target_profile.get('core_topics', [])[:3])}
- Main Offer: {target_profile.get('core_offer', 'N/A')}

ANCHOR & LINK:
- Anchor Text: "{input_minimal.get('anchor_text', '')}"
- Link URL: {input_minimal.get('target_url', '')}
- Bridge Type: {bridge_type} - {bridge_description}

BRIDGE TYPE REQUIREMENTS:
{self._get_bridge_requirements(bridge_type)}

SERP RESEARCH INSIGHTS:
- Primary Search Intent: {serp_research.get('serp_intent_primary', 'informational')}
- Recommended Angle: {intent_extension.get('recommended_article_angle', 'Informative overview')}
- Required Subtopics: {', '.join(intent_extension.get('required_subtopics', [])[:5])}
- Forbidden Angles: {', '.join(intent_extension.get('forbidden_angles', [])[:3])}

LSI TERM REQUIREMENTS:
Naturally incorporate 6-10 of these LSI terms within ±2 sentences of the anchor link:
{', '.join(lsi_terms[:10])}

STRUCTURAL REQUIREMENTS:
1. Compelling H1 title (do NOT include the link here)
2. Introduction (100-150 words) - hook the reader
3. 4-6 main sections with H2 headings
4. 2-3 H3 subsections per H2
5. Place anchor link in MIDDLE section (NOT in H1, NOT in H2 headings)
6. Link should flow naturally in paragraph text
7. Conclusion (100-150 words)

LINK PLACEMENT RULES (CRITICAL):
- NEVER place link in H1 title
- NEVER place link in H2 or H3 headings
- Place link in middle section paragraph text
- Make link contextually relevant and natural
- Use markdown format: [{input_minimal.get('anchor_text', '')}]({input_minimal.get('target_url', '')})

QUALITY STANDARDS:
- Minimum {constraints.get('min_word_count', 900)} words
- Natural, engaging writing (not robotic)
- Match publisher tone: {publisher_profile.get('tone_class', 'professional')}
- Inject LSI terms naturally (no keyword stuffing)
- Proper markdown formatting
- Swedish/English as specified

CONTENT GUIDELINES:
✓ DO: Write informative, valuable content
✓ DO: Make the link feel natural and helpful
✓ DO: Cover required subtopics comprehensively
✓ DO: Match the publisher's editorial voice

✗ DON'T: Place link in headings
✗ DON'T: Use these forbidden angles: {', '.join(intent_extension.get('forbidden_angles', [])[:3])}
✗ DON'T: Write promotional or salesy content (unless bridge type is 'strong')
✗ DON'T: Force LSI terms awkwardly

Write the complete article now in markdown format. Start with the H1 title (# Title)."""

        return prompt

    def _build_balanced_prompt(self, context: Dict[str, Any]) -> str:
        """Build balanced prompt (shorter but still comprehensive)"""

        input_minimal = context.get('input_minimal', {})
        target_profile = context.get('target_profile', {})
        publisher_profile = context.get('publisher_profile', {})
        intent_extension = context.get('intent_extension', {})
        constraints = context.get('generation_constraints', {})

        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')
        lsi_terms = self._extract_lsi_terms(context)
        language = 'Swedish' if constraints.get('language', 'sv') == 'sv' else 'English'

        prompt = f"""Write a {constraints.get('min_word_count', 900)}+ word article in {language}.

Publisher: {publisher_profile.get('domain', 'N/A')} (Tone: {publisher_profile.get('tone_class', 'professional')})
Target: {target_profile.get('title', 'N/A')}
Bridge Type: {bridge_type}

Article Angle: {intent_extension.get('recommended_article_angle', 'Informative overview')}
Required Topics: {', '.join(intent_extension.get('required_subtopics', [])[:5])}

CRITICAL LINK PLACEMENT:
- Anchor: [{input_minimal.get('anchor_text', '')}]({input_minimal.get('target_url', '')})
- Place in MIDDLE section paragraph (NOT in H1/H2)
- Inject these LSI terms near link: {', '.join(lsi_terms[:8])}

Structure: H1 title, intro, 4-6 H2 sections, conclusion. Natural, engaging writing."""

        return prompt

    def _build_fast_prompt(self, context: Dict[str, Any]) -> str:
        """Build fast prompt (minimal but functional)"""

        input_minimal = context.get('input_minimal', {})
        target_profile = context.get('target_profile', {})
        constraints = context.get('generation_constraints', {})

        prompt = f"""Write a {constraints.get('min_word_count', 900)} word article about {target_profile.get('title', 'the topic')}.

Include this link in the middle: [{input_minimal.get('anchor_text', '')}]({input_minimal.get('target_url', '')})

Language: {constraints.get('language', 'sv')}
Format: Markdown with H1, H2, H3 headings."""

        return prompt

    def _get_bridge_description(self, bridge_type: str) -> str:
        """Get description of bridge type"""
        descriptions = {
            'strong': 'Direct connection where target is the main focus',
            'pivot': 'Informational context that naturally leads to target',
            'wrapper': 'Extensive context where target is one of several options'
        }
        return descriptions.get(bridge_type, descriptions['pivot'])

    def _get_bridge_requirements(self, bridge_type: str) -> str:
        """Get specific requirements for bridge type"""
        requirements = {
            'strong': """- Target should be prominently featured (30-40% of content)
- Link early (within first 2-3 sections)
- Present target as primary solution/option
- More promotional tone is acceptable""",

            'pivot': """- Build informational context first (50-60% of content)
- Link in middle sections naturally
- Target is helpful resource, not sales pitch
- Maintain editorial, informative tone""",

            'wrapper': """- Extensive educational content (70-80% of content)
- Target is one of several options mentioned
- Link later in article naturally
- Strong editorial, neutral tone required"""
        }
        return requirements.get(bridge_type, requirements['pivot'])

    def _extract_lsi_terms(self, context: Dict[str, Any]) -> List[str]:
        """Extract LSI terms from context"""
        lsi_terms = []

        # From SERP subtopics
        serp_research = context.get('serp_research_extension', {})
        for serp_set in serp_research.get('serp_sets', [])[:2]:
            lsi_terms.extend(serp_set.get('subtopics', [])[:3])

        # From required subtopics
        intent_extension = context.get('intent_extension', {})
        lsi_terms.extend(intent_extension.get('required_subtopics', [])[:5])

        # From target topics
        target_profile = context.get('target_profile', {})
        lsi_terms.extend(target_profile.get('core_topics', [])[:3])

        # Deduplicate and limit to 10
        return list(dict.fromkeys(lsi_terms))[:10]

    def _call_llm(
        self,
        provider: LLMProvider,
        prompt: str,
        max_tokens: int
    ) -> str:
        """
        Call LLM provider with retry logic.

        Args:
            provider: LLM provider to use
            prompt: Prompt text
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        for attempt in range(self.max_retries):
            try:
                if provider == LLMProvider.ANTHROPIC:
                    return self._call_anthropic(prompt, max_tokens)
                elif provider == LLMProvider.OPENAI:
                    return self._call_openai(prompt, max_tokens)
                elif provider == LLMProvider.GOOGLE:
                    return self._call_google(prompt, max_tokens)
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def _call_anthropic(self, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        client = self._clients[LLMProvider.ANTHROPIC]
        config = self.MODEL_CONFIGS[LLMProvider.ANTHROPIC]

        response = client.messages.create(
            model=config['default_model'],
            max_tokens=max_tokens,
            temperature=config['temperature'],
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text

    def _call_openai(self, prompt: str, max_tokens: int) -> str:
        """Call OpenAI GPT API"""
        client = self._clients[LLMProvider.OPENAI]
        config = self.MODEL_CONFIGS[LLMProvider.OPENAI]

        response = client.chat.completions.create(
            model=config['default_model'],
            messages=[
                {"role": "system", "content": "You are a professional SEO content writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=config['temperature']
        )

        return response.choices[0].message.content

    def _call_google(self, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini API"""
        genai = self._clients[LLMProvider.GOOGLE]
        config = self.MODEL_CONFIGS[LLMProvider.GOOGLE]

        model = genai.GenerativeModel(config['default_model'])
        response = model.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': max_tokens,
                'temperature': config['temperature']
            }
        )

        return response.text
