"""
Unified Writer Engine - Consolidated multi-provider LLM support

This module consolidates the duplicate writer implementations found in:
- src/writer/production_writer.py
- src/writer/writer_engine.py  
- api/app/services/writer_engine.py

Provides a single, unified interface for content generation with:
- Multi-provider LLM support (OpenAI, Anthropic, Google Gemini)
- Multiple generation strategies (multi-stage, single-shot, mock)
- Bridge type implementation (strong/pivot/wrapper)
- LSI term injection
- Cost tracking and metrics
- Automatic fallback between providers
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"


class BridgeType(Enum):
    """Bridge types for backlink content"""
    STRONG = "strong"      # Direct connection, target is main focus
    PIVOT = "pivot"        # Informational context leading to target
    WRAPPER = "wrapper"    # Extensive context, target is one of several options


@dataclass
class GenerationMetrics:
    """Metrics for tracking generation performance"""
    provider: str
    model: str
    strategy: str = "mock"
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    duration_seconds: float = 0.0
    stages_completed: int = 0
    retries: int = 0
    success: bool = True


class UnifiedWriterEngine:
    """
    Unified production-grade writer engine with multi-provider LLM support.

    This class consolidates three previous duplicate implementations into a
    single, unified interface that provides all features.

    Features:
    - Multiple LLM providers (Anthropic Claude, OpenAI GPT, Google Gemini)
    - Multiple generation strategies (multi-stage, single-shot, mock)
    - Bridge type implementation (strong/pivot/wrapper)
    - LSI term injection (6-10 terms within ±2 sentences)
    - Context-aware content generation
    - Automatic fallback between providers
    - Cost tracking and performance metrics
    """

    # Pricing per 1M tokens (approximate, update as needed)
    PRICING = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-5': {'input': 5.00, 'output': 15.00},  # Estimated
        'claude-3-5-sonnet-20240620': {'input': 3.00, 'output': 15.00},
        'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00},
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        'gemini-2.5-pro': {'input': 1.25, 'output': 5.00},  # Estimated
        'gemini-2.0-flash-exp': {'input': 0.075, 'output': 0.30},  # Estimated
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
    }

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

    # LSI terms library
    LSI_LIBRARY = {
        'sv': {
            'generic': [
                'kvalitet', 'fördelar', 'nackdelar', 'jämförelse', 'alternativ',
                'erfarenheter', 'recension', 'guide', 'tips', 'råd',
                'bästa', 'rekommendation', 'översikt', 'test', 'utvärdering'
            ]
        },
        'en': {
            'generic': [
                'quality', 'benefits', 'drawbacks', 'comparison', 'alternatives',
                'experience', 'review', 'guide', 'tips', 'advice',
                'best', 'recommendation', 'overview', 'test', 'evaluation'
            ]
        }
    }

    def __init__(
        self,
        llm_provider: Optional[str] = None,
        mock_mode: bool = False,
        auto_fallback: bool = True,
        enable_cost_tracking: bool = True,
        max_retries: int = 3
    ):
        """
        Initialize Unified Writer Engine.

        Args:
            llm_provider: Primary LLM provider ('anthropic', 'openai', 'google')
                         If None, uses first available from environment
            mock_mode: Use mock mode instead of real LLM calls
            auto_fallback: Automatically try fallback providers on failure
            enable_cost_tracking: Track token usage and costs
            max_retries: Maximum retry attempts per provider
        """
        self.mock_mode = mock_mode
        self.auto_fallback = auto_fallback
        self.enable_cost_tracking = enable_cost_tracking
        self.max_retries = max_retries

        # Initialize clients
        self._clients = {}
        
        if not mock_mode:
            self._init_clients()
            
            # Determine primary provider
            if llm_provider:
                self.primary_provider = LLMProvider(llm_provider.lower())
                if self.primary_provider not in self._clients:
                    raise ValueError(f"Provider {llm_provider} not available (no API key found)")
            else:
                # Use first available provider
                if self._clients:
                    self.primary_provider = list(self._clients.keys())[0]
                else:
                    raise ValueError("No LLM API keys found in environment variables")
        else:
            self.primary_provider = None

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
                logger.warning("anthropic package not installed, skipping Anthropic provider")

        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                import openai
                self._clients[LLMProvider.OPENAI] = openai.OpenAI(
                    api_key=os.getenv('OPENAI_API_KEY')
                )
            except ImportError:
                logger.warning("openai package not installed, skipping OpenAI provider")

        # Google Gemini
        if os.getenv('GOOGLE_API_KEY'):
            try:
                import google.generativeai as genai
                genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
                self._clients[LLMProvider.GOOGLE] = genai
            except ImportError:
                logger.warning("google-generativeai package not installed, skipping Google provider")

    def generate(
        self,
        job_package: Dict[str, Any],
        strategy: str = 'single_shot'
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate article from job package.

        This is the main interface that supports both old and new callers.

        Args:
            job_package: Complete BacklinkJobPackage dict
            strategy: Generation strategy
                     - 'mock': Generate mock article for testing
                     - 'single_shot': Single comprehensive prompt
                     - 'multi_stage': Multi-stage generation (outline → content → polish)

        Returns:
            Tuple of (article_markdown, metrics_dict)
        """
        if self.mock_mode or strategy == 'mock':
            article = self._generate_mock_article(job_package)
            metrics = GenerationMetrics(
                provider="mock",
                model="mock",
                strategy="mock",
                success=True
            )
            return article, metrics.__dict__

        if strategy == 'multi_stage':
            return self._generate_multi_stage(job_package)
        else:  # single_shot
            return self._generate_single_shot(job_package)

    def generate_article(
        self,
        context: Dict[str, Any],
        strategy: str = 'expert'
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate article from job context.

        This method provides compatibility with the API service interface.

        Args:
            context: Complete job package with all profiles and research
            strategy: Generation strategy - maps to generate() strategies:
                - 'expert': multi_stage
                - 'balanced': single_shot
                - 'fast': single_shot
                - 'mock': mock

        Returns:
            Tuple of (article_markdown, metrics_dict)
        """
        if strategy == 'expert':
            return self.generate(context, 'multi_stage')
        elif strategy == 'mock':
            return self.generate(context, 'mock')
        else:
            return self.generate(context, 'single_shot')

    def _generate_mock_article(self, job_package: Dict[str, Any]) -> str:
        """
        Generate mock article for testing.

        Args:
            job_package: Job package

        Returns:
            Mock article in markdown format
        """
        # Extract key data
        input_minimal = job_package.get('input_minimal', {})
        publisher = input_minimal.get('publisher_domain', 'Unknown')
        target_url = input_minimal.get('target_url', 'Unknown')
        anchor_text = input_minimal.get('anchor_text', 'Unknown')
        
        constraints = job_package.get('generation_constraints', {})
        language = constraints.get('language', 'sv')
        
        target_profile = job_package.get('target_profile', {})
        entities = target_profile.get('core_entities', ['topic'])
        entity = entities[0] if entities else 'topic'

        intent_extension = job_package.get('intent_extension', {})
        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')

        # Get LSI terms
        lsi_terms = self._select_lsi_terms(job_package, 8)

        if language == 'sv':
            return f"""# Komplett guide om {entity}

När man söker information om {entity} är det viktigt att förstå de grundläggande aspekterna. I denna guide går vi igenom allt du behöver veta.

## Vad är {entity}?

{entity} är ett centralt begrepp inom området. För att förstå värdet av {lsi_terms[0]} och {lsi_terms[1]} måste vi först etablera grunderna.

## Viktiga faktorer att överväga

När du utvärderar olika {lsi_terms[2]} finns det flera nyckelfaktorer:

1. **Kvalitet och {lsi_terms[3]}** - Detta är grundläggande för att uppnå goda resultat
2. **{lsi_terms[4].capitalize()}** - Jämför olika alternativ noggrant
3. **Långsiktigt värde** - Tänk på hållbarhet och framtida behov

### Rekommenderad resurs

För den som vill ha en komplett översikt rekommenderar vi [{anchor_text}]({target_url}) som erbjuder detaljerad information och praktiska {lsi_terms[5]}.

## Vanliga frågor och {lsi_terms[6]}

Många funderar över hur man bäst använder dessa verktyg. Baserat på {lsi_terms[7]} från användare kan vi dra flera slutsatser om vad som fungerar bäst i praktiken.

## Sammanfattning

Att förstå {entity} kräver att man beaktar flera dimensioner. Med rätt information och verktyg kan du fatta välgrundade beslut.

### Källor

- Expertanalys från branschkällor
- Användardokumentation
- Oberoende tester

---

*Cirka 250 ord (mock-version - produktion genererar 900+ ord med fullständig analys)*
*Bridge type: {bridge_type}*
"""
        else:  # English
            return f"""# Complete Guide to {entity}

When seeking information about {entity}, understanding the fundamentals is crucial. This guide covers everything you need to know.

## What is {entity}?

{entity} is a central concept in this field. To understand the value of {lsi_terms[0]} and {lsi_terms[1]}, we must first establish the basics.

## Key Factors to Consider

When evaluating different {lsi_terms[2]}, several key factors matter:

1. **Quality and {lsi_terms[3]}** - Essential for good results
2. **{lsi_terms[4].capitalize()}** - Compare options carefully
3. **Long-term value** - Consider sustainability and future needs

### Recommended Resource

For those seeking a complete overview, we recommend [{anchor_text}]({target_url}), which offers detailed information and practical {lsi_terms[5]}.

## Common Questions and {lsi_terms[6]}

Many wonder about the best way to use these tools. Based on {lsi_terms[7]} from users, we can draw several conclusions about what works best in practice.

## Summary

Understanding {entity} requires considering multiple dimensions. With the right information and tools, you can make informed decisions.

### Sources

- Expert analysis from industry sources
- User documentation
- Independent testing

---

*Approximately 250 words (mock version - production generates 900+ words with full analysis)*
*Bridge type: {bridge_type}*
"""

    def _select_lsi_terms(self, job_package: Dict[str, Any], count: int = 8) -> List[str]:
        """Select LSI terms for injection"""
        constraints = job_package.get('generation_constraints', {})
        language = constraints.get('language', 'sv')
        
        # Get language-specific terms
        terms = self.LSI_LIBRARY.get(language, {}).get('generic', [])
        
        # Return requested number of terms
        return terms[:count] if len(terms) >= count else terms

    def _generate_single_shot(
        self,
        job_package: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Single-shot generation for faster results.

        Generates article with a single comprehensive prompt.
        """
        metrics = GenerationMetrics(
            provider="",
            model="",
            strategy="single_shot"
        )

        start_time = time.time()

        # Build comprehensive prompt
        prompt = self._build_comprehensive_prompt(job_package)

        # Try generation with primary provider
        try:
            article = self._call_llm(
                self.primary_provider,
                prompt,
                max_tokens=4000
            )

            config = self.MODEL_CONFIGS[self.primary_provider]
            metrics.provider = self.primary_provider.value
            metrics.model = config['default_model']
            metrics.duration_seconds = time.time() - start_time
            metrics.success = True
            metrics.stages_completed = 1

            return article, metrics.__dict__

        except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
            logger.error(f"Generation failed with {self.primary_provider.value}: {e}", exc_info=True)

            # Try fallback providers if enabled
            if self.auto_fallback:
                for fallback_provider in [LLMProvider.ANTHROPIC, LLMProvider.OPENAI, LLMProvider.GOOGLE]:
                    if fallback_provider == self.primary_provider or fallback_provider not in self._clients:
                        continue

                    try:
                        article = self._call_llm(fallback_provider, prompt, max_tokens=4000)

                        config = self.MODEL_CONFIGS[fallback_provider]
                        metrics.provider = fallback_provider.value
                        metrics.model = config['default_model']
                        metrics.duration_seconds = time.time() - start_time
                        metrics.success = True
                        metrics.stages_completed = 1

                        return article, metrics.__dict__

                    except (ConnectionError, TimeoutError, ValueError, KeyError):
                        logger.debug(f"Fallback provider {fallback_provider.value} also failed")
                        continue

            # All providers failed
            metrics.success = False
            metrics.duration_seconds = time.time() - start_time
            raise RuntimeError(f"All LLM providers failed. Last error: {e}")

    def _generate_multi_stage(
        self,
        job_package: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Multi-stage generation for optimal quality.

        Stages:
        1. Generate detailed outline
        2. Write full content from outline
        3. Polish and inject LSI terms
        """
        metrics = GenerationMetrics(
            provider="",
            model="",
            strategy="multi_stage"
        )

        start_time = time.time()

        # Try generation with available providers
        for provider in [self.primary_provider] + ([p for p in self._clients.keys() if p != self.primary_provider] if self.auto_fallback else []):
            if provider not in self._clients:
                continue

            try:
                # Stage 1: Outline
                outline_prompt = self._build_outline_prompt(job_package)
                outline = self._call_llm(provider, outline_prompt, max_tokens=1000)
                metrics.stages_completed = 1

                # Stage 2: Content
                content_prompt = self._build_content_prompt(job_package, outline)
                content = self._call_llm(provider, content_prompt, max_tokens=3000)
                metrics.stages_completed = 2

                # Stage 3: Polish
                polish_prompt = self._build_polish_prompt(job_package, content)
                article = self._call_llm(provider, polish_prompt, max_tokens=3500)
                metrics.stages_completed = 3

                # Success!
                config = self.MODEL_CONFIGS[provider]
                metrics.provider = provider.value
                metrics.model = config['default_model']
                metrics.duration_seconds = time.time() - start_time
                metrics.success = True

                return article, metrics.__dict__

            except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
                logger.error(f"Multi-stage generation failed with {provider.value}: {e}", exc_info=True)
                if not self.auto_fallback:
                    raise
                logger.debug(f"Trying next provider due to error: {e}")
                continue

        # All providers failed
        metrics.success = False
        metrics.duration_seconds = time.time() - start_time
        raise RuntimeError("All LLM providers failed to generate article")

    def _build_comprehensive_prompt(self, job_package: Dict[str, Any]) -> str:
        """Build single comprehensive prompt for single-shot generation"""
        # Extract context
        input_minimal = job_package.get('input_minimal', {})
        target_profile = job_package.get('target_profile', {})
        publisher_profile = job_package.get('publisher_profile', {})
        intent_extension = job_package.get('intent_extension', {})
        serp_research = job_package.get('serp_research_extension', {})
        constraints = job_package.get('generation_constraints', {})

        language = constraints.get('language', 'sv')
        language_name = 'Swedish' if language == 'sv' else 'English'
        min_words = constraints.get('min_word_count', 900)
        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')

        prompt = f"""You are a professional SEO content writer specializing in high-quality backlink articles.

Write a {min_words}+ word article in {language_name} that naturally links to the target URL.

PUBLISHER: {publisher_profile.get('domain', 'N/A')}
Tone: {publisher_profile.get('tone_class', 'professional')}

TARGET: {target_profile.get('url', 'N/A')}
Title: {target_profile.get('title', 'N/A')}
Topics: {', '.join(target_profile.get('core_topics', [])[:3])}

ANCHOR TEXT: "{input_minimal.get('anchor_text', '')}"
BRIDGE TYPE: {bridge_type}

REQUIREMENTS:
- Natural, engaging writing in {language_name}
- Match publisher's tone ({publisher_profile.get('tone_class', 'professional')})
- Place link naturally in middle section (NOT in headings)
- Include 4-6 main sections with proper structure
- Minimum {min_words} words

Generate the complete article now:"""

        return prompt

    def _build_outline_prompt(self, job_package: Dict[str, Any]) -> str:
        """Build prompt for outline generation (multi-stage)"""
        input_minimal = job_package.get('input_minimal', {})
        target_profile = job_package.get('target_profile', {})
        constraints = job_package.get('generation_constraints', {})
        intent_extension = job_package.get('intent_extension', {})

        language = constraints.get('language', 'sv')
        bridge_type = intent_extension.get('recommended_bridge_type', 'pivot')

        return f"""Create a detailed article outline for a {constraints.get('min_word_count', 900)}+ word article.

Topic: {', '.join(target_profile.get('core_entities', []))}
Language: {language}
Bridge Type: {bridge_type}
Anchor: "{input_minimal.get('anchor_text', '')}"

Create a structured outline with H1, H2, and H3 headings."""

    def _build_content_prompt(self, job_package: Dict[str, Any], outline: str) -> str:
        """Build prompt for content generation from outline"""
        constraints = job_package.get('generation_constraints', {})
        language = constraints.get('language', 'sv')

        return f"""Write the full article based on this outline:

{outline}

Language: {language}
Minimum words: {constraints.get('min_word_count', 900)}

Write the complete article now:"""

    def _build_polish_prompt(self, job_package: Dict[str, Any], content: str) -> str:
        """Build prompt for polishing and LSI injection"""
        input_minimal = job_package.get('input_minimal', {})
        lsi_terms = self._select_lsi_terms(job_package, 10)

        return f"""Polish this article and naturally incorporate these LSI terms near the anchor link:

LSI Terms: {', '.join(lsi_terms)}
Anchor: "{input_minimal.get('anchor_text', '')}"
Link: {input_minimal.get('target_url', '')}

Article:
{content}

Return the polished article:"""

    def _call_llm(
        self,
        provider: LLMProvider,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """
        Call LLM API with given prompt.

        Args:
            provider: LLM provider to use
            prompt: Prompt text
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        if provider not in self._clients:
            raise ValueError(f"Provider {provider.value} not initialized")

        client = self._clients[provider]
        config = self.MODEL_CONFIGS[provider]

        if provider == LLMProvider.ANTHROPIC:
            response = client.messages.create(
                model=config['default_model'],
                max_tokens=max_tokens,
                temperature=config['temperature'],
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        elif provider == LLMProvider.OPENAI:
            response = client.chat.completions.create(
                model=config['default_model'],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=config['temperature']
            )
            return response.choices[0].message.content

        elif provider == LLMProvider.GOOGLE:
            model = client.GenerativeModel(config['default_model'])
            response = model.generate_content(
                prompt,
                generation_config={
                    'max_output_tokens': max_tokens,
                    'temperature': config['temperature']
                }
            )
            return response.text

        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Legacy class names for backward compatibility
WriterEngine = UnifiedWriterEngine
ProductionWriter = UnifiedWriterEngine
