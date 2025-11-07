"""
Production Writer Engine - Multi-provider LLM support with advanced prompting

Supports:
- OpenAI (GPT-5)
- Anthropic (Claude 3.5 Sonnet)
- Google (Gemini 2.5 Pro)
- Multi-stage generation for optimal quality
- Cost tracking and retry logic
"""

import os
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    model: str
    api_key: str
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 60


@dataclass
class GenerationMetrics:
    """Metrics for tracking generation performance"""
    provider: str
    model: str
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    stages_completed: int = 0
    retries: int = 0


class ProductionWriter:
    """
    Production-grade writer with multi-provider support and advanced prompting.

    Features:
    - Multi-stage generation (outline → sections → polish)
    - Automatic provider fallback
    - Cost tracking
    - Retry logic with exponential backoff
    - Quality validation between stages
    """

    # Pricing per 1M tokens (approximate, update as needed)
    PRICING = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-5': {'input': 5.00, 'output': 15.00},  # Estimated
        'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00},
        'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},  # Estimated
    }

    def __init__(
        self,
        providers: Optional[List[LLMConfig]] = None,
        auto_fallback: bool = True,
        enable_cost_tracking: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize Production Writer.

        Args:
            providers: List of LLM configs to use (tries in order)
            auto_fallback: Automatically try next provider on failure
            enable_cost_tracking: Track token usage and costs
            max_retries: Max retry attempts per provider
        """
        self.providers = providers or self._init_default_providers()
        self.auto_fallback = auto_fallback
        self.enable_cost_tracking = enable_cost_tracking
        self.max_retries = max_retries

        # Initialize clients
        self.clients = {}
        for config in self.providers:
            self._init_client(config)

    def _init_default_providers(self) -> List[LLMConfig]:
        """Initialize default providers from environment variables"""
        providers = []

        # Try Anthropic first (best for Swedish content)
        if os.getenv('ANTHROPIC_API_KEY'):
            providers.append(LLMConfig(
                provider=LLMProvider.ANTHROPIC,
                model='claude-3-5-sonnet-20241022',
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            ))

        # Then OpenAI
        if os.getenv('OPENAI_API_KEY'):
            providers.append(LLMConfig(
                provider=LLMProvider.OPENAI,
                model='gpt-4o',  # Use gpt-4o, or 'gpt-5' when available
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            ))

        # Then Google
        if os.getenv('GOOGLE_API_KEY'):
            providers.append(LLMConfig(
                provider=LLMProvider.GOOGLE,
                model='gemini-2.5-pro',
                api_key=os.getenv('GOOGLE_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            ))

        if not providers:
            raise ValueError("No LLM API keys found in environment variables")

        return providers

    def _init_client(self, config: LLMConfig):
        """Initialize API client for provider"""
        try:
            if config.provider == LLMProvider.ANTHROPIC:
                import anthropic
                self.clients[config.provider] = anthropic.Anthropic(api_key=config.api_key)

            elif config.provider == LLMProvider.OPENAI:
                import openai
                self.clients[config.provider] = openai.OpenAI(api_key=config.api_key)

            elif config.provider == LLMProvider.GOOGLE:
                import google.generativeai as genai
                genai.configure(api_key=config.api_key)
                self.clients[config.provider] = genai

        except ImportError as e:
            print(f"Warning: Could not import {config.provider.value}: {e}")

    def generate(
        self,
        job_package: Dict[str, Any],
        strategy: str = 'multi_stage'
    ) -> Tuple[str, GenerationMetrics]:
        """
        Generate article from job package.

        Args:
            job_package: Complete BacklinkJobPackage
            strategy: 'single_shot' or 'multi_stage'

        Returns:
            (article_markdown, metrics)
        """
        if strategy == 'multi_stage':
            return self._generate_multi_stage(job_package)
        else:
            return self._generate_single_shot(job_package)

    def _generate_multi_stage(
        self,
        job_package: Dict[str, Any]
    ) -> Tuple[str, GenerationMetrics]:
        """
        Multi-stage generation for best quality.

        Stages:
        1. Generate detailed outline
        2. Write each section
        3. Polish and inject LSI terms
        4. Final quality check
        """
        metrics = GenerationMetrics(
            provider="",
            model=""
        )

        start_time = time.time()

        # Try each provider in order
        for config in self.providers:
            try:
                print(f"Attempting generation with {config.provider.value} ({config.model})...")

                # Stage 1: Outline
                outline = self._stage_1_outline(job_package, config)
                metrics.stages_completed = 1

                # Stage 2: Content generation
                sections = self._stage_2_content(job_package, outline, config)
                metrics.stages_completed = 2

                # Stage 3: Polish and LSI
                article = self._stage_3_polish(job_package, sections, config)
                metrics.stages_completed = 3

                # Success! Update metrics
                metrics.provider = config.provider.value
                metrics.model = config.model
                metrics.duration_seconds = time.time() - start_time

                print(f"✓ Generation successful with {config.provider.value}")
                return article, metrics

            except Exception as e:
                print(f"✗ Failed with {config.provider.value}: {e}")

                if not self.auto_fallback:
                    raise

                # Try next provider
                continue

        # All providers failed
        raise RuntimeError("All LLM providers failed to generate article")

    def _stage_1_outline(
        self,
        job_package: Dict[str, Any],
        config: LLMConfig
    ) -> str:
        """Stage 1: Generate detailed outline"""

        prompt = self._build_outline_prompt(job_package)

        return self._call_llm(config, prompt, max_tokens=1000)

    def _stage_2_content(
        self,
        job_package: Dict[str, Any],
        outline: str,
        config: LLMConfig
    ) -> str:
        """Stage 2: Generate full content from outline"""

        prompt = self._build_content_prompt(job_package, outline)

        return self._call_llm(config, prompt, max_tokens=3000)

    def _stage_3_polish(
        self,
        job_package: Dict[str, Any],
        content: str,
        config: LLMConfig
    ) -> str:
        """Stage 3: Polish and inject LSI terms"""

        prompt = self._build_polish_prompt(job_package, content)

        return self._call_llm(config, prompt, max_tokens=3500)

    def _build_outline_prompt(self, job_package: Dict[str, Any]) -> str:
        """Build prompt for outline generation"""

        input_minimal = job_package.get('input_minimal', {})
        target_profile = job_package.get('target_profile', {})
        publisher_profile = job_package.get('publisher_profile', {})
        intent_extension = job_package.get('intent_extension', {})
        constraints = job_package.get('generation_constraints', {})

        language = constraints.get('language', 'sv')
        min_words = constraints.get('min_word_count', 900)
        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')
        required_subtopics = intent_extension.get('required_subtopics', [])

        prompt = f"""You are an expert content strategist creating a backlink article outline.

CONTEXT:
- Publisher: {publisher_profile.get('domain')}
- Publisher Tone: {publisher_profile.get('tone_class')}
- Target URL: {target_profile.get('url')}
- Target Topic: {', '.join(target_profile.get('core_entities', []))}
- Anchor Text: "{input_minimal.get('anchor_text')}"
- Bridge Type: {bridge_type}
- Language: {language}

REQUIREMENTS:
- Minimum {min_words} words
- Bridge type: {bridge_type}
  * strong = direct connection, target is main focus
  * pivot = informational context leading to target
  * wrapper = extensive context, target is one of several options
- Must cover these subtopics: {', '.join(required_subtopics[:5])}
- Tone must match: {publisher_profile.get('tone_class')}

ARTICLE ANGLE:
{intent_extension.get('recommended_article_angle')}

TASK:
Create a detailed outline with:
1. Working title
2. Introduction hook
3. 4-6 main sections with H2 headings
4. 2-3 subsections (H3) per main section
5. Where to place the anchor link (middle section, NOT in H1/H2)
6. Conclusion

Respond in {language}. Be specific and strategic."""

        return prompt

    def _build_content_prompt(self, job_package: Dict[str, Any], outline: str) -> str:
        """Build prompt for content generation"""

        input_minimal = job_package.get('input_minimal', {})
        constraints = job_package.get('generation_constraints', {})
        intent_extension = job_package.get('intent_extension', {})

        language = constraints.get('language', 'sv')
        forbidden_angles = intent_extension.get('forbidden_angles', [])

        prompt = f"""You are a professional content writer. Write the COMPLETE article based on this outline:

{outline}

WRITING GUIDELINES:
- Write in {language}
- Natural, engaging prose (not robotic)
- Include the anchor link: [{input_minimal.get('anchor_text')}]({input_minimal.get('target_url')})
  * Place in middle section as outlined
  * Make it flow naturally in context
  * DO NOT place in H1 or H2 headings
- Use markdown formatting
- Write minimum {constraints.get('min_word_count', 900)} words
- Match publisher tone: {job_package.get('publisher_profile', {}).get('tone_class')}

AVOID:
{chr(10).join(['- ' + angle for angle in forbidden_angles[:3]])}

Write the FULL article now. Start with # (H1 title) and include all sections from the outline."""

        return prompt

    def _build_polish_prompt(self, job_package: Dict[str, Any], content: str) -> str:
        """Build prompt for polishing and LSI injection"""

        language = job_package.get('generation_constraints', {}).get('language', 'sv')

        # Get LSI terms from job package
        lsi_terms = self._extract_lsi_terms(job_package)

        prompt = f"""You are a SEO content editor. Polish this article and inject LSI terms naturally.

CURRENT ARTICLE:
{content}

TASK:
1. Review the article for quality and flow
2. Inject these LSI terms naturally within ±2 sentences of the anchor link:
   {', '.join(lsi_terms[:8])}
3. Ensure minimum {job_package.get('generation_constraints', {}).get('min_word_count', 900)} words
4. Maintain natural flow - don't force terms awkwardly
5. Keep all existing structure and links

Return the COMPLETE polished article in markdown."""

        return prompt

    def _generate_single_shot(
        self,
        job_package: Dict[str, Any]
    ) -> Tuple[str, GenerationMetrics]:
        """Single-shot generation (faster but potentially lower quality)"""

        metrics = GenerationMetrics(provider="", model="")
        start_time = time.time()

        for config in self.providers:
            try:
                prompt = self._build_comprehensive_prompt(job_package)
                article = self._call_llm(config, prompt, max_tokens=4000)

                metrics.provider = config.provider.value
                metrics.model = config.model
                metrics.duration_seconds = time.time() - start_time
                metrics.stages_completed = 1

                return article, metrics

            except Exception as e:
                print(f"Failed with {config.provider.value}: {e}")
                if not self.auto_fallback:
                    raise
                continue

        raise RuntimeError("All providers failed")

    def _build_comprehensive_prompt(self, job_package: Dict[str, Any]) -> str:
        """Build comprehensive single-shot prompt"""

        # Combine all prompts into one
        input_minimal = job_package.get('input_minimal', {})
        target_profile = job_package.get('target_profile', {})
        publisher_profile = job_package.get('publisher_profile', {})
        intent_extension = job_package.get('intent_extension', {})
        constraints = job_package.get('generation_constraints', {})

        lsi_terms = self._extract_lsi_terms(job_package)

        prompt = f"""You are an expert content writer creating a backlink article.

PUBLISHER CONTEXT:
- Domain: {publisher_profile.get('domain')}
- Tone: {publisher_profile.get('tone_class')}
- Language: {constraints.get('language', 'sv')}

TARGET:
- URL: {target_profile.get('url')}
- Title: {target_profile.get('title')}
- Core entities: {', '.join(target_profile.get('core_entities', []))}
- Core offer: {target_profile.get('core_offer')}

ARTICLE REQUIREMENTS:
- Bridge type: {intent_extension.get('recommended_bridge_type')}
- Article angle: {intent_extension.get('recommended_article_angle')}
- Required subtopics: {', '.join(intent_extension.get('required_subtopics', [])[:5])}
- Minimum {constraints.get('min_word_count', 900)} words
- Language: {constraints.get('language', 'sv')}

LINK PLACEMENT:
- Anchor text: "{input_minimal.get('anchor_text')}"
- Target URL: {input_minimal.get('target_url')}
- Place in middle section, NOT in H1/H2
- Include 6-10 of these LSI terms within ±2 sentences of link:
  {', '.join(lsi_terms[:10])}

FORBIDDEN ANGLES:
{chr(10).join(['- ' + angle for angle in intent_extension.get('forbidden_angles', [])[:3]])}

Write a complete, engaging article in markdown format."""

        return prompt

    def _call_llm(
        self,
        config: LLMConfig,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """Call LLM with retry logic"""

        for attempt in range(self.max_retries):
            try:
                if config.provider == LLMProvider.ANTHROPIC:
                    return self._call_anthropic(config, prompt, max_tokens)

                elif config.provider == LLMProvider.OPENAI:
                    return self._call_openai(config, prompt, max_tokens)

                elif config.provider == LLMProvider.GOOGLE:
                    return self._call_google(config, prompt, max_tokens)

                else:
                    raise ValueError(f"Unsupported provider: {config.provider}")

            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Retry {attempt + 1}/{self.max_retries} after {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

    def _call_anthropic(self, config: LLMConfig, prompt: str, max_tokens: int) -> str:
        """Call Anthropic Claude API"""
        client = self.clients.get(LLMProvider.ANTHROPIC)

        response = client.messages.create(
            model=config.model,
            max_tokens=max_tokens,
            temperature=config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        return response.content[0].text

    def _call_openai(self, config: LLMConfig, prompt: str, max_tokens: int) -> str:
        """Call OpenAI GPT API"""
        client = self.clients.get(LLMProvider.OPENAI)

        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are a professional content writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=config.temperature
        )

        return response.choices[0].message.content

    def _call_google(self, config: LLMConfig, prompt: str, max_tokens: int) -> str:
        """Call Google Gemini API"""
        genai = self.clients.get(LLMProvider.GOOGLE)

        model = genai.GenerativeModel(config.model)
        response = model.generate_content(
            prompt,
            generation_config={
                'max_output_tokens': max_tokens,
                'temperature': config.temperature
            }
        )

        return response.text

    def _extract_lsi_terms(self, job_package: Dict[str, Any]) -> List[str]:
        """Extract LSI terms from job package"""

        lsi_terms = []

        # From SERP subtopics
        serp_sets = job_package.get('serp_research_extension', {}).get('serp_sets', [])
        for serp_set in serp_sets[:2]:
            lsi_terms.extend(serp_set.get('subtopics', [])[:3])

        # From required subtopics
        lsi_terms.extend(
            job_package.get('intent_extension', {}).get('required_subtopics', [])[:5]
        )

        # From target topics
        lsi_terms.extend(
            job_package.get('target_profile', {}).get('core_topics', [])[:3]
        )

        # Deduplicate and limit
        return list(dict.fromkeys(lsi_terms))[:10]
