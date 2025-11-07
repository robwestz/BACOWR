"""
Writer Engine - Generate articles with LLM integration

Part of Del 3B: Content Generation Pipeline
Generates backlink articles based on job_package using Claude or OpenAI
"""

import os
import re
from typing import Dict, Any, List, Optional, Tuple


class WriterEngine:
    """
    Writer Engine for generating backlink articles.

    Supports:
    - LLM integration (Anthropic Claude, OpenAI)
    - Bridge types (strong/pivot/wrapper)
    - LSI injection (6-10 terms near link)
    - Link placement policy
    - Mock mode for testing
    """

    # LSI terms library (can be expanded)
    LSI_LIBRARY = {
        'sv': {
            'generic': [
                'kvalitet', 'fördelar', 'nackdelar', 'jämförelse', 'alternativ',
                'erfarenheter', 'recension', 'guide', 'tips', 'råd'
            ]
        },
        'en': {
            'generic': [
                'quality', 'benefits', 'drawbacks', 'comparison', 'alternatives',
                'experience', 'review', 'guide', 'tips', 'advice'
            ]
        }
    }

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        mock_mode: bool = True,
        llm_provider: str = 'anthropic'
    ):
        """
        Initialize Writer Engine.

        Args:
            anthropic_api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            openai_api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            mock_mode: Use mock mode instead of real LLM
            llm_provider: 'anthropic' or 'openai'
        """
        self.mock_mode = mock_mode
        self.llm_provider = llm_provider

        # Get API keys from params or environment
        self.anthropic_api_key = anthropic_api_key or os.getenv('ANTHROPIC_API_KEY')
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

        # Initialize LLM client if not in mock mode
        if not mock_mode:
            if llm_provider == 'anthropic' and self.anthropic_api_key:
                try:
                    import anthropic
                    self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)
                except ImportError:
                    raise ImportError("anthropic package not installed. Run: pip install anthropic")
            elif llm_provider == 'openai' and self.openai_api_key:
                try:
                    import openai
                    self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                except ImportError:
                    raise ImportError("openai package not installed. Run: pip install openai")
            else:
                raise ValueError(f"No API key provided for {llm_provider}")

    def generate(self, job_package: Dict[str, Any]) -> str:
        """
        Generate article from job package.

        Args:
            job_package: Complete BacklinkJobPackage

        Returns:
            Generated article (markdown)
        """
        if self.mock_mode:
            return self._generate_mock_article(job_package)
        else:
            return self._generate_llm_article(job_package)

    def _generate_mock_article(self, job_package: Dict[str, Any]) -> str:
        """
        Generate mock article for testing.

        Args:
            job_package: Job package

        Returns:
            Mock article
        """
        # Extract key data
        publisher = job_package.get('input_minimal', {}).get('publisher_domain', 'Unknown')
        target_url = job_package.get('input_minimal', {}).get('target_url', 'Unknown')
        anchor_text = job_package.get('input_minimal', {}).get('anchor_text', 'Unknown')
        language = job_package.get('generation_constraints', {}).get('language', 'sv')
        min_words = job_package.get('generation_constraints', {}).get('min_word_count', 900)
        bridge_type = job_package.get('intent_extension', {}).get('recommended_bridge_type', 'pivot')

        # Get LSI terms
        lsi_terms = self._select_lsi_terms(job_package, 8)

        # Generate based on bridge type
        if bridge_type == 'strong':
            article = self._generate_strong_bridge_mock(
                job_package, target_url, anchor_text, lsi_terms, language
            )
        elif bridge_type == 'pivot':
            article = self._generate_pivot_bridge_mock(
                job_package, target_url, anchor_text, lsi_terms, language
            )
        else:  # wrapper
            article = self._generate_wrapper_bridge_mock(
                job_package, target_url, anchor_text, lsi_terms, language
            )

        return article

    def _generate_strong_bridge_mock(
        self,
        job_package: Dict[str, Any],
        target_url: str,
        anchor_text: str,
        lsi_terms: List[str],
        language: str
    ) -> str:
        """Generate mock article with strong bridge"""
        entities = job_package.get('target_profile', {}).get('core_entities', ['topic'])
        entity = entities[0] if entities else 'topic'

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

For a complete overview, we recommend [{anchor_text}]({target_url}) which provides detailed information and practical {lsi_terms[5]}.

## Common Questions and {lsi_terms[6]}

Many wonder about best practices. Based on {lsi_terms[7]} from users, we can draw conclusions about what works best.

## Summary

Understanding {entity} requires considering multiple dimensions. With the right information and tools, you can make well-informed decisions.

*Mock version - production generates 900+ words with full analysis*
"""

    def _generate_pivot_bridge_mock(
        self,
        job_package: Dict[str, Any],
        target_url: str,
        anchor_text: str,
        lsi_terms: List[str],
        language: str
    ) -> str:
        """Generate mock article with pivot bridge"""
        entities = job_package.get('target_profile', {}).get('core_entities', ['topic'])
        entity = entities[0] if entities else 'topic'

        if language == 'sv':
            return f"""# Guide: Hitta bästa lösningen för dina behov inom {entity}

När man utvärderar olika alternativ inom {entity} finns det mycket att ta hänsyn till. Denna guide hjälper dig navigera valen.

## Bakgrund och kontext

För att göra ett informerat val behöver du först förstå grunderna kring {lsi_terms[0]} och {lsi_terms[1]}. Marknaden erbjuder många alternativ, var och en med sina fördelar.

## Faktorer som påverkar ditt val

### {lsi_terms[2].capitalize()} och prestanda

Olika lösningar erbjuder olika nivåer av {lsi_terms[3]}. Det är viktigt att jämföra baserat på dina specifika behov.

### Pris kontra värde

En {lsi_terms[4]} visar att prisbilden varierar betydligt. Fokusera på långsiktigt värde snarare än enbart initial kostnad.

## Rekommenderade resurser

Ett utmärkt sätt att börja din research är att utforska [{anchor_text}]({target_url}), som ger en strukturerad översikt med praktiska {lsi_terms[5]}.

### Vad experter säger

Enligt oberoende {lsi_terms[6]} och {lsi_terms[7]} från verkliga användare är det viktigt att:

- Jämföra flera alternativ innan beslut
- Läsa oberoende recensioner
- Testa om möjligt innan köp
- Säkerställa god support och dokumentation

## Nästa steg

Med denna information kan du nu göra en mer informerad bedömning av vilken lösning som passar dina behov bäst.

### Ytterligare läsning

- Konsumentguider om ämnet
- Expertanalyser och tester
- Använderforum och communities

---

*Mock-artikel cirka 280 ord - produktion 900+*
"""
        else:
            return self._generate_strong_bridge_mock(
                job_package, target_url, anchor_text, lsi_terms, 'en'
            )

    def _generate_wrapper_bridge_mock(
        self,
        job_package: Dict[str, Any],
        target_url: str,
        anchor_text: str,
        lsi_terms: List[str],
        language: str
    ) -> str:
        """Generate mock article with wrapper bridge"""
        # Wrapper requires extensive context - use pivot as base
        return self._generate_pivot_bridge_mock(
            job_package, target_url, anchor_text, lsi_terms, language
        )

    def _generate_llm_article(self, job_package: Dict[str, Any]) -> str:
        """
        Generate article using LLM.

        Args:
            job_package: Job package

        Returns:
            Generated article
        """
        # Build prompt
        prompt = self._build_llm_prompt(job_package)

        # Call LLM
        if self.llm_provider == 'anthropic':
            return self._generate_with_anthropic(prompt)
        else:
            return self._generate_with_openai(prompt)

    def _build_llm_prompt(self, job_package: Dict[str, Any]) -> str:
        """Build prompt for LLM"""
        # Extract key info
        input_minimal = job_package.get('input_minimal', {})
        target_profile = job_package.get('target_profile', {})
        publisher_profile = job_package.get('publisher_profile', {})
        intent_extension = job_package.get('intent_extension', {})
        constraints = job_package.get('generation_constraints', {})

        # Build structured prompt
        prompt = f"""You are a professional content writer creating a backlink article.

PUBLISHER CONTEXT:
- Domain: {publisher_profile.get('domain')}
- Tone: {publisher_profile.get('tone_class')}
- Language: {constraints.get('language', 'sv')}

TARGET PAGE:
- URL: {target_profile.get('url')}
- Title: {target_profile.get('title')}
- Core entities: {', '.join(target_profile.get('core_entities', []))}
- Core offer: {target_profile.get('core_offer')}

ARTICLE REQUIREMENTS:
- Bridge type: {intent_extension.get('recommended_bridge_type')}
- Recommended angle: {intent_extension.get('recommended_article_angle')}
- Required subtopics: {', '.join(intent_extension.get('required_subtopics', [])[:5])}
- Minimum words: {constraints.get('min_word_count', 900)}
- Language: {constraints.get('language', 'sv')}

LINK PLACEMENT:
- Anchor text: "{input_minimal.get('anchor_text')}"
- Target URL: {input_minimal.get('target_url')}
- Policy: {constraints.get('anchor_policy', 'Place in middle section, not in H1/H2')}
- Include 6-10 LSI terms within ±2 sentences of the link

FORBIDDEN ANGLES:
{chr(10).join(['- ' + angle for angle in intent_extension.get('forbidden_angles', [])[:3]])}

Generate a complete, well-structured article in markdown format that follows these requirements.
The article should be informative, natural, and align with the publisher's tone and intent."""

        return prompt

    def _generate_with_anthropic(self, prompt: str) -> str:
        """Generate with Anthropic Claude"""
        response = self.anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return response.content[0].text

    def _generate_with_openai(self, prompt: str) -> str:
        """Generate with OpenAI"""
        response = self.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional content writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000
        )
        return response.choices[0].message.content

    def _select_lsi_terms(
        self,
        job_package: Dict[str, Any],
        num_terms: int = 8
    ) -> List[str]:
        """
        Select LSI terms for injection.

        Args:
            job_package: Job package
            num_terms: Number of terms to select

        Returns:
            List of LSI terms (guaranteed to have num_terms elements)
        """
        language = job_package.get('generation_constraints', {}).get('language', 'sv')

        # Get generic LSI terms for language
        generic_terms = self.LSI_LIBRARY.get(language, {}).get('generic', [])

        # Add topic-specific terms from SERP
        serp_sets = job_package.get('serp_research_extension', {}).get('serp_sets', [])
        serp_subtopics = []
        for serp_set in serp_sets[:2]:  # First 2 SERP sets
            serp_subtopics.extend(serp_set.get('subtopics', []))

        # Combine and select
        all_terms = generic_terms[:4] + serp_subtopics[:4]

        # Ensure we have enough terms by cycling through generic_terms if needed
        while len(all_terms) < num_terms and generic_terms:
            all_terms.extend(generic_terms)

        return all_terms[:num_terms]
