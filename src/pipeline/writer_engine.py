"""
Writer Engine - Generates backlink content from BacklinkJobPackage.

Uses LLM (Claude or similar) to generate content strictly according to
Next-A1 specifications and the assembled job package.

This is a CRITICAL component - it must follow Next-A1 constraints precisely.
"""

import json
import os
from typing import Dict, Optional, Tuple

from anthropic import Anthropic

from ..utils.logger import get_logger

logger = get_logger(__name__)


class WriterEngine:
    """
    Generates backlink content following Next-A1 specifications.

    Takes a BacklinkJobPackage and produces:
    - Article text (HTML/Markdown)
    - links_extension
    - qc_extension (preliminary)
    - intent_extension (already in package, but can refine)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize Writer Engine.

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
            model: Claude model to use
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            logger.warning("No API key provided - WriterEngine will fail at runtime")

        self.model = model
        self.client = None

        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
            logger.info("WriterEngine initialized", model=model)
        else:
            logger.warning("WriterEngine initialized without API key")

    def generate_content(
        self,
        job_package: Dict
    ) -> Tuple[str, Dict, bool, str]:
        """
        Generate backlink content from job package.

        Args:
            job_package: Complete BacklinkJobPackage dict

        Returns:
            Tuple of (article_text, extensions_dict, success, error_message)

        Extensions dict contains:
        - links_extension
        - intent_extension (from package, may be refined)
        - qc_extension (preliminary)
        - serp_research_extension (from package)
        """
        if not self.client:
            return "", {}, False, "No API key configured for WriterEngine"

        logger.info(
            "Generating content",
            job_id=job_package["job_meta"]["job_id"],
            bridge_type=job_package["intent_extension"]["recommended_bridge_type"]
        )

        try:
            # Build system prompt (Next-A1 constraints)
            system_prompt = self._build_system_prompt()

            # Build user prompt (job package + instructions)
            user_prompt = self._build_user_prompt(job_package)

            # Call LLM
            logger.debug("Calling LLM for content generation")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.7,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )

            # Parse response
            response_text = response.content[0].text

            # Extract article and extensions
            article_text, extensions = self._parse_response(response_text, job_package)

            logger.info(
                "Content generation successful",
                article_length=len(article_text),
                has_extensions=bool(extensions)
            )

            return article_text, extensions, True, None

        except Exception as e:
            error_msg = f"Content generation failed: {str(e)}"
            logger.error("Content generation error", error=error_msg, exc_info=True)
            return "", {}, False, error_msg

    def _build_system_prompt(self) -> str:
        """
        Build system prompt with Next-A1 specifications.

        This defines the LLM's role and constraints.
        """
        return """Du är en expert-innehållsgenerator för backlink-artiklar enligt Next-A1-ramverket.

DIN UPPGIFT:
Generera högkvalitativa backlink-artiklar som STRIKT följer Next-A1-specifikationen och det medföljande BacklinkJobPackage.

KRITISKA PRINCIPER (Next-A1):

1. VARIABELGIFTERMÅL - Allt ska gifta sig:
   - Publisher (publikationssajt) + Anchor (ankare) + Target (målsida) + Intent (avsikt)
   - Detta är KÄRNAN i allt du gör. Om något inte gifter sig, använd rätt bridge-strategi.

2. SERP-FIRST APPROACH:
   - SERP-data styr vad du skriver
   - Följ dominant intent från serp_research_extension
   - Täck required_subtopics som SERP-resultaten visar
   - Matcha page_archetypes och content_signals

3. BRIDGE TYPES (strong, pivot, wrapper):
   - strong: Direkt, naturlig koppling när allt är alignat
   - pivot: Tematisk brygga när partial alignment
   - wrapper: Meta-ram (metodik, risk, jämförelse) när low alignment

4. ANCHOR-REGLER:
   - ALDRIG i H1 eller H2
   - Placera i mittsektion (andra eller tredje H2-sektionen)
   - 6-10 LSI-termer inom ±2 meningar runt länken
   - Naturlig integration, inte påklistrad

5. TRUST-KÄLLOR:
   - Prioritet: T1 (myndighet) → T2 (akademi) → T3 (bransch) → T4 (media)
   - Använd PLATSFÖRSLAG om källa inte är känd
   - Aldrig länka till konkurrenter

6. PUBLISHER VOICE:
   - Följ publisher_profile.tone_class:
     * academic: saklig, källhänvisande
     * authority_public: klarspråk, myndighetston
     * consumer_magazine: tillgänglig, nytta först
     * hobby_blog: personlig expert
   - Matcha publikationssajtens naturliga röst

7. COMPLIANCE:
   - Lägg till bransch-specifika disclaimers vid behov
   - Gambling, finans, hälsa, legal, crypto = kräver disclaimer

OUTPUT-FORMAT:
Din output ska innehålla TVÅ delar:

PART 1: ARTICLE
[Här skriver du den fullständiga artikeln i Markdown-format]

PART 2: EXTENSIONS
```json
{
  "links_extension": { ... },
  "intent_extension": { ... },
  "qc_extension": { ... }
}
```

VIKTIGT:
- Skriv ALLTID på det språk som anges i job package
- Följ min_word_count
- Var STRIKT med Next-A1-reglerna
- Förklara dina val i extensions"""

    def _build_user_prompt(self, job_package: Dict) -> str:
        """
        Build user prompt with job package data.

        This provides all context needed for generation.
        """
        # Format job package nicely for LLM
        job_json = json.dumps(job_package, ensure_ascii=False, indent=2)

        prompt = f"""GENERERA BACKLINK-ARTIKEL enligt följande BacklinkJobPackage:

{job_json}

INSTRUKTIONER:

1. ANALYSERA job package noggrant:
   - Förstå variabelgiftermålet: publisher + anchor + target + intent
   - Identifiera recommended_bridge_type och använd rätt strategi
   - Läs required_subtopics från SERP-analysen
   - Notera forbidden_angles att undvika

2. PLANERA artikelstrukturen:
   - Skapa H1 (titel)
   - 3-5 H2-sektioner
   - Placera länk i H2-sektion 2 eller 3
   - Bygg LSI-fönster runt länken
   - Integrera trust-källor naturligt

3. SKRIV artikeln:
   - Använd language från generation_constraints
   - Nå min_word_count
   - Följ publisher tone_class
   - Täck required_subtopics
   - Följ dominant SERP intent
   - Integrera target naturligt enligt bridge_type

4. SKAPA extensions:
   - links_extension: Dokumentera bridge_type, anchor placement, LSI, trust, compliance
   - intent_extension: Kan återanvända från package eller förfina
   - qc_extension: Preliminary self-assessment

BÖRJA NU med PART 1: ARTICLE"""

        return prompt

    def _parse_response(
        self,
        response_text: str,
        job_package: Dict
    ) -> Tuple[str, Dict]:
        """
        Parse LLM response into article and extensions.

        Args:
            response_text: Raw LLM response
            job_package: Original package (for fallback data)

        Returns:
            Tuple of (article_text, extensions_dict)
        """
        # Split on "PART 2: EXTENSIONS" or similar marker
        parts = response_text.split("PART 2:")
        if len(parts) == 1:
            # Try alternate split
            parts = response_text.split("```json")

        article_text = parts[0].strip()

        # Clean up article (remove "PART 1: ARTICLE" header if present)
        if article_text.startswith("PART 1:"):
            lines = article_text.split("\n", 1)
            if len(lines) > 1:
                article_text = lines[1].strip()

        # Extract JSON extensions
        extensions = {}
        if len(parts) > 1:
            json_part = parts[1]

            # Find JSON block
            if "```json" in response_text:
                json_start = json_part.find("{")
                json_end = json_part.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = json_part[json_start:json_end]
                    try:
                        extensions = json.loads(json_str)
                    except json.JSONDecodeError as e:
                        logger.warning("Failed to parse extensions JSON", error=str(e))

        # Fallback: use intent_extension from package if not in response
        if "intent_extension" not in extensions:
            extensions["intent_extension"] = job_package.get("intent_extension", {})

        # Add serp_research_extension from package
        extensions["serp_research_extension"] = job_package.get("serp_research_extension", {})

        return article_text, extensions
