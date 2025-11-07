"""
WriterEngineInterface Module

Calls LLM Writer Engine with BacklinkJobPackage and systemprompt.
"""

import json
from typing import Dict, Any
from pathlib import Path

from .base import BaseModule


class WriterEngineInterface(BaseModule):
    """
    Writer Engine Interface.

    Calls LLM with BacklinkJobPackage to generate content.

    Input:
        - job_package: BacklinkJobPackage dict

    Output:
        - analysis: str
        - strategy: str
        - content_brief: str
        - full_text_html: str
        - full_text_markdown: str
        - backlink_article_output_v2: Dict with extensions
    """

    def run(self, job_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate content using Writer Engine

        Args:
            job_package: Complete BacklinkJobPackage

        Returns:
            Writer output dict
        """
        self.log_step("Calling Writer Engine")

        # Load systemprompt
        systemprompt = self._load_systemprompt()

        # Prepare LLM request
        llm_request = self._prepare_llm_request(systemprompt, job_package)

        # Call LLM (placeholder – integrate with actual LLM API)
        llm_response = self._call_llm(llm_request)

        # Parse output
        output = self._parse_llm_output(llm_response, job_package)

        self.log_step("Writer Engine completed")

        return output

    def _load_systemprompt(self) -> str:
        """Load Writer Engine systemprompt"""
        prompt_path = Path(__file__).parent.parent / "WRITER_ENGINE_PROMPT.md"

        if prompt_path.exists():
            return prompt_path.read_text(encoding='utf-8')
        else:
            self.logger.warning("WRITER_ENGINE_PROMPT.md not found, using fallback")
            return "You are a backlink content writer. Generate high-quality SEO content."

    def _prepare_llm_request(self, systemprompt: str, job_package: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare LLM API request"""
        user_message = f"""
You are receiving a BacklinkJobPackage. Generate the complete output according to the systemprompt.

BacklinkJobPackage:
```json
{json.dumps(job_package, indent=2, ensure_ascii=False)}
```

Please provide:
1. Analysis (100-200 words)
2. Strategy (150-250 words)
3. Content Brief (structured)
4. Full Text HTML (≥900 words)
5. Full Text Markdown
6. backlink_article_output_v2 (JSON with all extensions)
"""

        return {
            "system": systemprompt,
            "user": user_message
        }

    def _call_llm(self, request: Dict[str, Any]) -> str:
        """
        Call LLM API

        PLACEHOLDER: In production, integrate with:
        - Anthropic Claude API
        - OpenAI GPT API
        - Other LLM providers
        """
        # For now, return mock response
        self.logger.warning(
            "Using MOCK LLM response. In production, integrate with real LLM API "
            "(Anthropic Claude, OpenAI, etc.)"
        )

        # Mock response
        mock_response = """
## Analysis

This is a mock analysis of the variable marriage problem. The publisher is a consumer magazine focused on personal finance. The target is a customer service page for a payment solution. The anchor suggests commercial research intent. The SERP analysis shows that users searching for payment solutions want comparisons, safety information, and practical guides.

The perfect intersect is an informative article that positions the target as one example within a broader guide.

## Strategy

**Bridge Type**: pivot

We will create a pivot bridge by establishing a broader discussion about secure and convenient payment solutions. The target (customer service page) will be introduced naturally as a resource for users who choose that particular solution.

**Trust Sources**:
- T1: Konsumentverket (consumer protection)
- T3: Industry report on payment trends

**LSI Plan**: Inject terms like "säkerhet", "kryptering", "köpskydd", "transparens", "kundtjänst", "villkor" in anchor near-window.

**Structure**: Intro → What makes payments convenient → Security considerations → Example: [Target] → Alternatives → Resources

## Content Brief

**Title**: Så väljer du säkra och smidiga betalningslösningar online

**Meta Description**: Guide till säkra betalningslösningar för näthandel. Jämför alternativ, läs om säkerhet och hitta rätt lösning för dina behov.

**Structure**:
1. Inledning (150 ord) – Hook + context
2. Vad gör en betalning smidig? (200 ord)
3. Säkerhetskrav du bör känna till (250 ord) – Anchor placement here
4. Exempel: Klarnas kundtjänst (200 ord)
5. Andra alternativ att överväga (150 ord)
6. Resurser och källor (50 ord)

**Total**: ~1000 ord

## Full Text HTML

<article>
<header>
<h1>Så väljer du säkra och smidiga betalningslösningar online</h1>
</header>

<section class="introduction">
<p>Att handla online har blivit en naturlig del av vardagen för de flesta svenskar. Men med den ökade näthandeln kommer också vikten av att välja rätt betalningslösning – en som är både säker och smidig. I den här guiden går vi igenom vad du bör tänka på när du väljer betalningsmetod, vilka säkerhetskrav som är viktiga, och hur olika lösningar fungerar i praktiken.</p>
</section>

<section>
<h2>Vad gör en betalning smidig?</h2>
<p>En smidig betalningslösning kännetecknas av flera faktorer. För det första ska processen vara snabb och intuitiv – du ska inte behöva fylla i onödigt många fält eller navigera genom krångliga steg. För det andra ska lösningen erbjuda flexibilitet, till exempel möjligheten att dela upp betalningen eller välja olika betalmetoder.</p>

<p>Transparens är också avgörande. Du ska tydligt kunna se kostnader, villkor och leveranstider innan köpet slutförs. Många moderna betalningslösningar erbjuder även köpskydd och enkel hantering av returer, vilket ökar tryggheten för konsumenten.</p>
</section>

<section>
<h2>Säkerhetskrav du bör känna till</h2>
<p>Säkerhet är kanske den viktigaste faktorn när du väljer betalningslösning. Alla seriösa aktörer använder kryptering för att skydda dina uppgifter under transaktionen. Kolla efter att tjänsten använder SSL/TLS-certifikat (du ser det genom hänglåset i webbläsarens adressfält).</p>

<p>Köpskydd är ett annat viktigt skydd. Detta innebär att du kan få pengarna tillbaka om varan inte levereras eller inte motsvarar beskrivningen. Konsumentverket rekommenderar att alltid välja betalningsmetoder som erbjuder köpskydd.</p>

<p>När du letar efter <a href="https://klarna.com/se/kundtjanst/" class="backlink">smidig betalningshantering</a> är det också viktigt att tjänsten har en tydlig och tillgänglig kundtjänst. Problem kan uppstå, och då behöver du kunna nå support snabbt. Transparens kring villkor, avgifter och datahantering är också avgörande för att du ska känna dig trygg.</p>
</section>

<section>
<h2>Exempel: Klarnas kundtjänst</h2>
<p>Ett exempel på en etablerad aktör i Sverige är Klarna, som erbjuder flera olika betalningsalternativ. Deras kundtjänst är tillgänglig via chatt, telefon och e-post, vilket gör det enkelt att få hjälp om du stöter på problem. Klarna erbjuder även köpskydd enligt svensk lag, samt tydlig information om villkor och avgifter på sin webbplats.</p>

<p>Det är dock viktigt att komma ihåg att ingen enskild lösning passar alla. Vad som är smidigt för en person kan vara mindre lämpligt för en annan, beroende på köpvanor och behov.</p>
</section>

<section>
<h2>Andra alternativ att överväga</h2>
<p>Förutom Klarna finns det flera andra betalningslösningar på den svenska marknaden. Swish är populärt för snabba överföringar mellan privatpersoner och allt fler e-handlare. Paypal är ett globalt alternativ med starkt köpskydd. Traditionella kortbetalningar via Visa och Mastercard erbjuder också god säkerhet och bred acceptans.</p>

<p>Jämför alltid alternativen baserat på dina egna behov: vill du ha delbetalning? Hur viktigt är köpskydd? Vilka avgifter tillkommer?</p>
</section>

<section class="resources">
<h2>Källor och resurser</h2>
<ul>
<li><a href="https://www.konsumentverket.se/">Konsumentverket – Råd om säker näthandel</a></li>
<li><a href="https://www.wikipedia.org/wiki/Payment_system">Wikipedia – Payment systems</a></li>
</ul>
</section>

</article>

## Full Text Markdown

# Så väljer du säkra och smidiga betalningslösningar online

Att handla online har blivit en naturlig del av vardagen för de flesta svenskar. Men med den ökade näthandeln kommer också vikten av att välja rätt betalningslösning – en som är både säker och smidig. I den här guiden går vi igenom vad du bör tänka på när du väljer betalningsmetod, vilka säkerhetskrav som är viktiga, och hur olika lösningar fungerar i praktiken.

## Vad gör en betalning smidig?

En smidig betalningslösning kännetecknas av flera faktorer. För det första ska processen vara snabb och intuitiv – du ska inte behöva fylla i onödigt många fält eller navigera genom krångliga steg. För det andra ska lösningen erbjuda flexibilitet, till exempel möjligheten att dela upp betalningen eller välja olika betalmetoder.

Transparens är också avgörande. Du ska tydligt kunna se kostnader, villkor och leveranstider innan köpet slutförs. Många moderna betalningslösningar erbjuder även köpskydd och enkel hantering av returer, vilket ökar tryggheten för konsumenten.

## Säkerhetskrav du bör känna till

Säkerhet är kanske den viktigaste faktorn när du väljer betalningslösning. Alla seriösa aktörer använder kryptering för att skydda dina uppgifter under transaktionen. Kolla efter att tjänsten använder SSL/TLS-certifikat (du ser det genom hänglåset i webbläsarens adressfält).

Köpskydd är ett annat viktigt skydd. Detta innebär att du kan få pengarna tillbaka om varan inte levereras eller inte motsvarar beskrivningen. Konsumentverket rekommenderar att alltid välja betalningsmetoder som erbjuder köpskydd.

När du letar efter [smidig betalningshantering](https://klarna.com/se/kundtjanst/) är det också viktigt att tjänsten har en tydlig och tillgänglig kundtjänst. Problem kan uppstå, och då behöver du kunna nå support snabbt. Transparens kring villkor, avgifter och datahantering är också avgörande för att du ska känna dig trygg.

## Exempel: Klarnas kundtjänst

Ett exempel på en etablerad aktör i Sverige är Klarna, som erbjuder flera olika betalningsalternativ. Deras kundtjänst är tillgänglig via chatt, telefon och e-post, vilket gör det enkelt att få hjälp om du stöter på problem. Klarna erbjuder även köpskydd enligt svensk lag, samt tydlig information om villkor och avgifter på sin webbplats.

Det är dock viktigt att komma ihåg att ingen enskild lösning passar alla. Vad som är smidigt för en person kan vara mindre lämpligt för en annan, beroende på köpvanor och behov.

## Andra alternativ att överväga

Förutom Klarna finns det flera andra betalningslösningar på den svenska marknaden. Swish är populärt för snabba överföringar mellan privatpersoner och allt fler e-handlare. Paypal är ett globalt alternativ med starkt köpskydd. Traditionella kortbetalningar via Visa och Mastercard erbjuder också god säkerhet och bred acceptans.

Jämför alltid alternativen baserat på dina egna behov: vill du ha delbetalning? Hur viktigt är köpskydd? Vilka avgifter tillkommer?

## Källor och resurser

- [Konsumentverket – Råd om säker näthandel](https://www.konsumentverket.se/)
- [Wikipedia – Payment systems](https://www.wikipedia.org/wiki/Payment_system)

## backlink_article_output_v2 (JSON)

```json
{
  "links_extension": {
    "bridge_type": "pivot",
    "bridge_theme": "säkerhet och smidighet i digitala betalningar",
    "anchor_swap": {
      "performed": false,
      "from_type": null,
      "to_type": null,
      "rationale": "Original anchor var optimal för kontexten"
    },
    "placement": {
      "paragraph_index_in_section": 3,
      "offset_chars": 420,
      "near_window": {
        "unit": "sentence",
        "radius": 2,
        "lsi_count": 7
      }
    },
    "trust_policy": {
      "level": "T1_public",
      "fallback_used": false,
      "unresolved": []
    },
    "compliance": {
      "disclaimers_injected": []
    }
  },
  "intent_extension": {
    "serp_intent_primary": "commercial_research",
    "serp_intent_secondary": ["info_primary"],
    "target_page_intent": "support",
    "anchor_implied_intent": "commercial_research",
    "publisher_role_intent": "info_primary",
    "intent_alignment": {
      "anchor_vs_serp": "aligned",
      "target_vs_serp": "partial",
      "publisher_vs_serp": "aligned",
      "overall": "partial"
    },
    "recommended_bridge_type": "pivot",
    "recommended_article_angle": "Informativ guide till säkra betalningar med exempel",
    "required_subtopics": ["säkerhet", "smidighet", "köpskydd", "kundtjänst"],
    "forbidden_angles": [],
    "notes": {
      "rationale": "SERP vill ha jämförande innehåll, publisher är info-first, target är support-orienterad",
      "data_confidence": "high"
    }
  },
  "qc_extension": {
    "anchor_risk": "low",
    "readability": {
      "lix": 43,
      "target_range": "35-45"
    },
    "thresholds_version": "A1",
    "notes_observability": {
      "signals_used": ["target_entities", "publisher_profile", "SERP_intent", "trust_source"],
      "autofix_done": false
    }
  },
  "serp_research_extension": {}
}
```
"""

        return mock_response

    def _parse_llm_output(self, llm_response: str, job_package: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse LLM output into structured format

        In production: use better parsing (JSON mode, structured outputs, etc.)
        """
        # Very simple parsing – look for sections
        import re

        output = {
            "analysis": "",
            "strategy": "",
            "content_brief": "",
            "full_text_html": "",
            "full_text_markdown": "",
            "backlink_article_output_v2": {}
        }

        # Extract Analysis
        analysis_match = re.search(r'## Analysis\s+(.*?)\s+##', llm_response, re.DOTALL)
        if analysis_match:
            output["analysis"] = analysis_match.group(1).strip()

        # Extract Strategy
        strategy_match = re.search(r'## Strategy\s+(.*?)\s+##', llm_response, re.DOTALL)
        if strategy_match:
            output["strategy"] = strategy_match.group(1).strip()

        # Extract Content Brief
        brief_match = re.search(r'## Content Brief\s+(.*?)\s+## Full Text', llm_response, re.DOTALL)
        if brief_match:
            output["content_brief"] = brief_match.group(1).strip()

        # Extract Full Text HTML
        html_match = re.search(r'## Full Text HTML\s+(.*?)\s+## Full Text Markdown', llm_response, re.DOTALL)
        if html_match:
            output["full_text_html"] = html_match.group(1).strip()

        # Extract Full Text Markdown
        md_match = re.search(r'## Full Text Markdown\s+(.*?)\s+## backlink_article_output_v2', llm_response, re.DOTALL)
        if md_match:
            output["full_text_markdown"] = md_match.group(1).strip()

        # Extract JSON
        json_match = re.search(r'```json\s+(.*?)\s+```', llm_response, re.DOTALL)
        if json_match:
            try:
                output["backlink_article_output_v2"] = json.loads(json_match.group(1))
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON: {e}")
                output["backlink_article_output_v2"] = {}

        # Fallback: use job_package extensions if parsing failed
        if not output["backlink_article_output_v2"]:
            output["backlink_article_output_v2"] = {
                "links_extension": {},
                "intent_extension": job_package.get("intent_extension", {}),
                "qc_extension": {},
                "serp_research_extension": job_package.get("serp_research_extension", {})
            }

        return output
