# BUILDER PROMPT - BACOWR System
## Systemprompt för Claude Code att bygga Backlink Content Writer

---

## DIN UPPGIFT

Du ska bygga ett komplett Python-system för att generera högkvalitativa backlänksartiklar.

**Input (3 enkla fält):**
- `publisher_domain` (t.ex. "example-publisher.com")
- `target_url` (t.ex. "https://client.com/product-x")
- `anchor_text` (t.ex. "bästa valet för X")

**Output:**
- Komplett artikel (900+ ord) i Markdown/HTML
- JSON-paket med all metadata och extensions
- QC-rapport
- Execution log

**Fullständig specifikation finns i:** `IMPLEMENTATION_SPEC.md` (läs denna först!)

---

## BYGGORDNING - STEG FÖR STEG

Följ denna ordning exakt. Testa varje komponent innan du går vidare.

### STEG 0: SETUP & STRUKTUR

1. **Skapa filstruktur:**
```
BACOWR/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
├── src/
│   ├── __init__.py
│   ├── api.py
│   ├── profile/
│   │   ├── __init__.py
│   │   ├── target_profiler.py
│   │   ├── publisher_profiler.py
│   │   └── anchor_profiler.py
│   ├── serp/
│   │   ├── __init__.py
│   │   ├── research.py
│   │   └── serp_api.py
│   ├── intent/
│   │   ├── __init__.py
│   │   └── modeler.py
│   ├── generation/
│   │   ├── __init__.py
│   │   └── writer.py
│   ├── qc/
│   │   ├── __init__.py
│   │   ├── controller.py
│   │   └── autofix.py
│   ├── state/
│   │   ├── __init__.py
│   │   └── machine.py
│   └── utils/
│       ├── __init__.py
│       ├── llm.py
│       └── helpers.py
├── config/
│   ├── thresholds.yaml
│   ├── policies.yaml
│   └── publisher_voices.yaml
├── schemas/
│   └── backlink_job_package.schema.json
├── storage/
│   └── output/
│       └── .gitkeep
├── tests/
│   ├── __init__.py
│   ├── test_schema_validation.py
│   └── test_live_validation.py
└── examples/
    └── example_job_package.json
```

2. **Skapa requirements.txt:**
```
requests>=2.31.0
httpx>=0.25.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
anthropic>=0.8.0
jsonschema>=4.20.0
pyyaml>=6.0.0
pydantic>=2.5.0
python-dotenv>=1.0.0
```

3. **Skapa .env.example:**
```
ANTHROPIC_API_KEY=your_key_here
SERP_API_KEY=your_key_here_if_using_api
DEFAULT_LANGUAGE=sv
OUTPUT_DIR=./storage/output
```

---

### STEG 1: UTILS & LLM CLIENT

**Fil:** `src/utils/llm.py`

**Vad den ska göra:**
- Wrapper för Anthropic API (Claude)
- Stödja structured output (JSON mode)
- Hantera retries och rate limits
- Logga API-calls

**Nyckelfunktioner:**
```python
class LLMClient:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4")

    def generate_structured(
        self,
        prompt: str,
        schema: dict,
        max_tokens: int = 4000
    ) -> dict:
        """Generera strukturerad JSON enligt schema"""

    def generate_text(
        self,
        prompt: str,
        max_tokens: int = 4000
    ) -> str:
        """Generera fritext"""
```

**Fil:** `src/utils/helpers.py`

**Nyckelfunktioner:**
```python
def generate_job_id() -> str:
    """Generera unikt job ID (timestamp + random)"""

def sanitize_filename(name: str) -> str:
    """Rensa filnamn från ogiltiga tecken"""

def truncate_text(text: str, max_chars: int) -> str:
    """Trunkera text till max_chars"""

def extract_domain(url: str) -> str:
    """Extrahera domän från URL"""
```

**Test:** Kör `python -c "from src.utils.llm import LLMClient; print('OK')"` ska fungera.

---

### STEG 2: TARGET PROFILER

**Fil:** `src/profile/target_profiler.py`

**Vad den ska göra:**
1. Fetch HTML från target_url
2. Parse metadata (title, meta description, H1, H2-H3)
3. Extrahera main content (exkludera nav/footer/sidebar)
4. Använd LLM för att analysera:
   - Core entities
   - Core topics
   - Core offer (vad hjälper sidan användaren med?)
   - Candidate main queries (2-3 förslag)

**Huvudfunktion:**
```python
def profile_target(url: str, llm_client: LLMClient) -> dict:
    """
    Returnerar target_profile enligt schema:
    {
      "url": str,
      "http_status": int,
      "title": str,
      "meta_description": str,
      "h1": str,
      "h2_h3_sample": [str],
      "main_content_excerpt": str,  # första 500 tecken
      "detected_language": str,
      "core_entities": [str],
      "core_topics": [str],
      "core_offer": str,
      "candidate_main_queries": [str]
    }
    """
```

**LLM Prompt (ungefär):**
```
Analysera följande webbsida och extrahera:

TITLE: {title}
META: {meta_description}
H1: {h1}
HEADINGS: {h2_h3_sample}
CONTENT (första 1000 tecken): {content_excerpt}

Svara i JSON:
{
  "core_entities": ["huvudsakliga namngivna entiteter"],
  "core_topics": ["huvudteman"],
  "core_offer": "vad hjälper sidan användaren med? (1 mening)",
  "candidate_main_queries": ["2-3 sökqueries som denna sida vill ranka för"]
}
```

**Test:** Kör på en känd URL och verifiera att output ser rimlig ut.

---

### STEG 3: PUBLISHER PROFILER

**Fil:** `src/profile/publisher_profiler.py`

**Vad den ska göra:**
1. Fetch homepage från publisher_domain
2. Försök hitta "Om oss"-sida
3. Fetch 2-3 sample articles (för ton/röst-analys)
4. Använd LLM för att analysera:
   - Topic focus (ämnesfokus)
   - Audience (målgrupp)
   - Tone class (academic, authority_public, consumer_magazine, hobby_blog)
   - Allowed commerciality (low, medium, high)
   - Brand safety notes

**Huvudfunktion:**
```python
def profile_publisher(domain: str, llm_client: LLMClient) -> dict:
    """
    Returnerar publisher_profile enligt schema:
    {
      "domain": str,
      "sample_urls": [str],
      "about_excerpt": str,
      "detected_language": str,
      "topic_focus": [str],
      "audience": str,
      "tone_class": str,  # academic | authority_public | consumer_magazine | hobby_blog
      "allowed_commerciality": str,  # low | medium | high
      "brand_safety_notes": str
    }
    """
```

**LLM Prompt (ungefär):**
```
Analysera följande publiceringsdomän:

HOMEPAGE CONTENT: {homepage_excerpt}
ABOUT PAGE: {about_excerpt}
SAMPLE ARTICLE 1: {article1_excerpt}
SAMPLE ARTICLE 2: {article2_excerpt}

Bestäm:
1. Topic focus - vilka ämnen täcker sajten?
2. Audience - vilken målgrupp?
3. Tone class - academic, authority_public, consumer_magazine, eller hobby_blog?
4. Allowed commerciality - hur kommersiellt innehåll kan sajten ha? (low/medium/high)
5. Brand safety notes - några restriktioner? (gambling, lån, etc.)

Svara i JSON enligt ovanstående struktur.
```

**Test:** Kör på en känd publisher-domän.

---

### STEG 4: ANCHOR PROFILER

**Fil:** `src/profile/anchor_profiler.py`

**Vad den ska göra:**
Klassificera ankartexten enligt:
- **Type:** exact, partial, brand, generic
- **Intent hint:** info_primary, commercial_research, transactional, navigational_brand

**Huvudfunktion:**
```python
def profile_anchor(anchor_text: str, target_context: dict, llm_client: LLMClient) -> dict:
    """
    Returnerar anchor_profile:
    {
      "proposed_text": str,
      "type_hint": str | None,
      "llm_classified_type": str,  # exact | partial | brand | generic
      "llm_intent_hint": str  # info_primary | commercial_research | transactional | navigational_brand
    }
    """
```

**LLM Prompt:**
```
Klassificera följande ankartext:

ANCHOR TEXT: "{anchor_text}"
TARGET PAGE CONTEXT:
- Title: {target_title}
- Core entities: {target_entities}
- Core offer: {target_offer}

Klassificera ankaret:

TYPE (välj en):
- exact: Exakt match mot target's huvudkeyword/offer
- partial: Delvis match, relaterad
- brand: Varumärkets namn
- generic: Generisk text ("läs mer", "klicka här", etc.)

INTENT (välj en):
- info_primary: Informationssökande
- commercial_research: Researchar före köp
- transactional: Redo att köpa/handla
- navigational_brand: Söker specifikt varumärke

Svara i JSON:
{
  "llm_classified_type": "...",
  "llm_intent_hint": "..."
}
```

**Test:** Testa med olika ankartexter.

---

### STEG 5: SERP RESEARCH

**Fil:** `src/serp/serp_api.py`

**Vad den ska göra:**
- Anropa SERP API (t.ex. ValueSERP, SerpApi)
- Alternativt: basic Google search scraping (enklare första version)
- Hämta topp-10 resultat för en query
- Returnera strukturerad data

**Huvudfunktion:**
```python
def fetch_serp_results(query: str, location: str = "Sweden", language: str = "sv") -> list:
    """
    Returnerar lista med topp-10 resultat:
    [
      {
        "rank": 1,
        "url": "https://...",
        "title": "...",
        "snippet": "..."
      },
      ...
    ]
    """
```

**VIKTIGT:** För första versionen - använd basic requests + BeautifulSoup för Google scraping ELLER använd en SERP API om du har nyckel. Scraping är enklast att börja med.

**Fil:** `src/serp/research.py`

**Vad den ska göra:**
1. Ta emot target_profile och anchor_profile
2. Bestäm main_query + 1-2 cluster_queries baserat på candidate_main_queries
3. För varje query:
   - Fetch topp-10 SERP resultat
   - Fetch varje URL (begränsa till 1000 tecken för snabbhet)
   - Använd LLM för att analysera varje resultat:
     - Page type (guide, comparison, product, review, faq, news, official, other)
     - Key entities
     - Key subtopics
   - Använd LLM för att analysera hela SERP-set:
     - Dominant intent
     - Secondary intents
     - Required subtopics (vad alla täcker)
     - Page archetypes

**Huvudfunktion:**
```python
def conduct_serp_research(
    target_profile: dict,
    anchor_profile: dict,
    llm_client: LLMClient
) -> dict:
    """
    Returnerar serp_research_extension enligt schema (se IMPLEMENTATION_SPEC.md).
    """
```

**LLM Prompts:**

**Per resultat:**
```
Analysera denna SERP-listning och innehållet:

RANK: {rank}
URL: {url}
TITLE: {title}
SNIPPET: {snippet}
CONTENT (första 1000 tecken): {content_excerpt}

Bestäm:
1. Page type: guide, comparison, category, product, review, tool, faq, news, official, other
2. Key entities (3-5 st): viktiga namngivna entiteter
3. Key subtopics (2-4 st): huvudteman som täcks

Svara i JSON:
{
  "detected_page_type": "...",
  "key_entities": [...],
  "key_subtopics": [...]
}
```

**Per SERP-set:**
```
Analysera dessa topp-10 SERP-resultat för query: "{query}"

RESULTAT:
{json.dumps(results_with_analysis, indent=2)}

Bestäm:
1. Dominant intent (välj en):
   - info_primary: Användaren vill lära sig
   - commercial_research: Researchar före köp
   - transactional: Redo att köpa
   - navigational_brand: Söker specifikt varumärke
   - support: Söker hjälp/support
   - local: Lokalt fokus
   - mixed: Blandad intent

2. Secondary intents (kan vara tom)

3. Required subtopics: Subtopics som nästan ALLA topp-resultat täcker (dessa MÅSTE vår artikel täcka)

4. Page archetypes: Vilka sidtyper dominerar? (guide, comparison, product, etc.)

Svara i JSON:
{
  "dominant_intent": "...",
  "secondary_intents": [...],
  "required_subtopics": [...],
  "page_archetypes": [...]
}
```

**Test:** Kör med en query och verifiera strukturen.

---

### STEG 6: INTENT MODELER

**Fil:** `src/intent/modeler.py`

**Vad den ska göra:**
Ta emot:
- target_profile
- publisher_profile
- anchor_profile
- serp_research

Härled:
- serp_intent_primary/secondary (från SERP research)
- target_page_intent (från target_profile)
- anchor_implied_intent (från anchor_profile)
- publisher_role_intent (från publisher_profile)

Jämför alignment:
- anchor_vs_serp
- target_vs_serp
- publisher_vs_serp
- overall

Rekommendera:
- bridge_type (strong, pivot, wrapper) baserat på alignment
- article_angle
- required_subtopics (merged från alla SERP-sets)
- forbidden_angles

**Huvudfunktion:**
```python
def model_intent(
    target_profile: dict,
    publisher_profile: dict,
    anchor_profile: dict,
    serp_research: dict,
    llm_client: LLMClient
) -> dict:
    """
    Returnerar intent_extension enligt schema (se IMPLEMENTATION_SPEC.md).
    """
```

**LLM Prompt (stort och viktigt):**
```
Du är en SEO-expert som analyserar intent-alignment för backlänksplacering.

SERP RESEARCH:
Main Query: {main_query}
Dominant Intent: {serp_intent_primary}
Secondary Intents: {serp_intent_secondary}
Required Subtopics (från alla SERP-sets): {merged_required_subtopics}
Page Archetypes: {merged_archetypes}

TARGET PAGE:
Title: {target_title}
Core Offer: {target_core_offer}
Core Entities: {target_core_entities}
Core Topics: {target_core_topics}

ANCHOR TEXT: "{anchor_text}"
Anchor Classified Type: {anchor_type}
Anchor Intent Hint: {anchor_intent_hint}

PUBLISHER:
Domain: {publisher_domain}
Topic Focus: {publisher_topic_focus}
Tone Class: {publisher_tone_class}
Allowed Commerciality: {publisher_allowed_commerciality}

UPPGIFT:
1. Bestäm target_page_intent (vilken intent har målsidan?)
2. Bestäm publisher_role_intent (vilken roll spelar publisher naturligt?)
3. Bedöm alignment (aligned/partial/off) för:
   - anchor_vs_serp
   - target_vs_serp
   - publisher_vs_serp
   - overall (helhetsbedömning)

4. Rekommendera bridge_type:
   - STRONG: Om alla är aligned/partial och publisher niche overlap hög
   - PIVOT: Om minst en är partial men kan lösas med tematisk brygga
   - WRAPPER: Om overall är off, behöver meta-ram (metodik/risk/innovation/etik)

5. Rekommendera article_angle (vilken vinkel ska artikeln ha?)

6. Required subtopics (vad MÅSTE artikeln täcka?)

7. Forbidden angles (vad ska artikeln INTE göra?)

Svara i JSON enligt intent_extension schema (se IMPLEMENTATION_SPEC.md).
```

**Test:** Kör med kompletta profiler och verifiera alignment-logiken.

---

### STEG 7: CONTENT GENERATION (WRITER)

**Fil:** `src/generation/writer.py`

**Vad den ska göra:**
Ta emot allt ovanstående och generera:
1. Artikel (900+ ord) enligt publisher voice
2. Korrekt bridge type-strategi
3. Optimal länkplacering (ej i H1/H2, mittsektion)
4. 6-10 LSI-termer i närfönster (±2 meningar)
5. Trust-källor (T1-T4)
6. links_extension (JSON)

**Huvudfunktion:**
```python
def generate_article(
    target_profile: dict,
    publisher_profile: dict,
    anchor_profile: dict,
    serp_research: dict,
    intent_profile: dict,
    llm_client: LLMClient
) -> tuple[str, dict]:
    """
    Returnerar:
    - article_text (str): Markdown-formaterad artikel
    - links_extension (dict): Metadata om länkplacering
    """
```

**LLM Prompt (stor och komplex):**

```
Du är en expert content writer för backlänksartiklar.

KONTEXT & KRAV:
==============

TARGET PAGE:
- URL: {target_url}
- Title: {target_title}
- Core Offer: {target_core_offer}
- Core Entities: {target_core_entities}

PUBLISHER:
- Domain: {publisher_domain}
- Tone Class: {publisher_tone_class}
- Topic Focus: {publisher_topic_focus}
- Allowed Commerciality: {publisher_allowed_commerciality}

ANCHOR: "{anchor_text}"
- Type: {anchor_type}
- Intent: {anchor_intent_hint}

INTENT ANALYSIS:
- SERP Primary Intent: {serp_intent_primary}
- Bridge Type: {recommended_bridge_type}
- Recommended Angle: {recommended_article_angle}
- Required Subtopics: {required_subtopics}
- Forbidden Angles: {forbidden_angles}

GENERATION CONSTRAINTS:
- Language: {language}
- Min Word Count: 900
- Max Word Count: 1500
- Tone: {publisher_tone_class} (se strukturguide nedan)
- Max Anchor Usages: 2
- Anchor Policy: Aldrig i H1 eller H2. Placera i mittsektion, stycke 1-2 efter kontext är etablerad.

STRUKTURGUIDE BASERAT PÅ TONE CLASS:
{publisher_voice_structure}

BRIDGE TYPE STRATEGI:
- STRONG: Direktlänkning tidigt i relevant sektion
- PIVOT: Etablera tematisk pivot först, länka sedan
- WRAPPER: Bygg neutral meta-ram (metodik/risk/innovation), länka efter ram är etablerad

LSI-KRAV (KRITISKT):
- Placera 6-10 relevanta LSI-termer i närfönster (±2 meningar från anchor)
- Termer att använda (baserat på SERP + target): {lsi_candidates}
- Blanda begreppstyper: processer, mått, teorier, felkällor
- Undvik bara synonymer

TRUST-KÄLLOR:
- Inkludera 1-3 trust-källor (T1_public > T2_academic > T3_industry > T4_media)
- Prioritera svenska myndigheter/källor
- Aldrig direkta konkurrenter
- Placera i Resources-sektion eller diskret i bryggstycke

UPPGIFT:
========
Skriv en komplett artikel enligt ovan.

FORMAT:
Returnera JSON:
{
  "article": {
    "title": "...",
    "meta_description": "...",
    "content": "... (full markdown-formaterad artikel) ...",
    "word_count": 0
  },
  "links_extension": {
    "bridge_type": "{bridge_type}",
    "bridge_theme": "... (om pivot/wrapper)",
    "anchor_swap": {
      "performed": false,
      "from_type": null,
      "to_type": null,
      "rationale": ""
    },
    "placement": {
      "paragraph_index_in_section": 0,
      "offset_chars": 0,
      "near_window": {
        "unit": "sentence",
        "radius": 2,
        "lsi_count": 0
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
  "lsi_terms_used": ["term1", "term2", ...],
  "trust_sources": [
    {"url": "...", "level": "T1_public", "context": "..."},
    ...
  ]
}

VIKTIGA MARKERINGAR I CONTENT:
- Markera target-länken med: [[LINK:{anchor_text}|{target_url}]]
- Markera trust-källor med: [[TRUST:{källa_beskrivning}|{url_eller_PLATSFÖRSLAG}]]

Exempel:
"... enligt undersökningen [[LINK:bästa valet för privatlån|https://client.com/privatlan]] visar att ..."
"... som Konsumentverket [[TRUST:Konsumentverket om lån|https://www.konsumentverket.se/lan]] påpekar ..."
```

**Publisher Voice Structures:**

I `config/publisher_voices.yaml`:
```yaml
academic:
  structure: "Inledning → Metod → Resultat/Implikation → Referenser"
  tone: "Saklig, källförande, låg värdeladdning"
  citation_style: "Kort källhänvisning i text, trust i slutet"

authority_public:
  structure: "Sammanhang → Rekommendation → Hur-gör-man → Källor"
  tone: "Myndighetsnära klarspråk"

consumer_magazine:
  structure: "Hook → Mittpunkt → Fördjupning → Call-to-value → Resurser"
  tone: "Lättillgänglig, nytta först, konkreta exempel"

hobby_blog:
  structure: "Bakgrund → Case → Tips → Resurser"
  tone: "Personligt sakkunnig, berättande med praktiska tips"
```

**Test:** Generera en artikel och inspektera manuellt.

---

### STEG 8: QC CONTROLLER

**Fil:** `src/qc/controller.py`

**Vad den ska göra:**
Validera genererad artikel + links_extension mot:
1. **Anchor risk** (high/medium/low)
2. **Readability** (LIX-score om möjligt, annars basic word/sentence count)
3. **LSI quality** (räkna LSI-termer i närfönster)
4. **Trust sources** (minst 1 godkänd)
5. **Compliance** (disclaimers för reglerade vertikaler)
6. **Intent alignment** (från intent_profile)

**Huvudfunktion:**
```python
def run_qc(
    article_text: str,
    links_extension: dict,
    intent_profile: dict,
    target_profile: dict,
    publisher_profile: dict,
    policies: dict
) -> dict:
    """
    Returnerar qc_extension:
    {
      "anchor_risk": "low | medium | high",
      "readability": {
        "lix": 42,  # eller null
        "target_range": "35-45"
      },
      "thresholds_version": "A1",
      "notes_observability": {
        "signals_used": [...],
        "autofix_done": false
      },
      "validation_results": {
        "lsi_check": {"passed": true, "count": 8},
        "trust_check": {"passed": true, "count": 2},
        "placement_check": {"passed": true},
        "compliance_check": {"passed": true}
      },
      "overall_status": "PASS | WARNING | BLOCKED",
      "human_signoff_required": false,
      "issues": []
    }
    """
```

**Config:** `config/thresholds.yaml`
```yaml
lsi:
  min_count: 6
  max_count: 10
  window_radius: 2  # sentences

trust:
  min_sources: 1
  priority_order:
    - T1_public
    - T2_academic
    - T3_industry
    - T4_media

anchor:
  forbidden_in: ["H1", "H2"]
  preferred_section: "mid-section"
  risk_rules:
    high:
      - "exact match + strong commercial intent in weak context"
      - "repetition 2+ times in same section"
    medium:
      - "generic in weak context without trust"
      - "partial with questionable semantic fit"
    low:
      - "brand/generic in natural context with LSI and trust nearby"

compliance:
  regulated_verticals:
    gambling:
      disclaimer_required: true
      template: "Spela ansvarsfullt. 18+. Stödlinjen.se"
    finance:
      disclaimer_required: true
      template: "Tänk på att alla lån kostar pengar."
    health:
      disclaimer_required: true
      template: "Konsultera alltid läkare vid hälsofrågor."
    legal:
      disclaimer_required: false
    crypto:
      disclaimer_required: true
      template: "Kryptovalutor är högriskplaceringar."
```

**Test:** Kör QC på genererad artikel.

---

### STEG 9: AUTOFIX

**Fil:** `src/qc/autofix.py`

**Vad den ska göra:**
Om QC hittar mindre brister, gör EN automatisk fix:
- Flytta länk inom sektion
- Byta ankartyp (exact → generic)
- Injicera saknade LSI-termer
- Lägga till disclaimer

**Huvudfunktion:**
```python
def apply_autofix_once(
    article_text: str,
    links_extension: dict,
    qc_report: dict,
    policies: dict,
    llm_client: LLMClient
) -> tuple[str, dict, dict]:
    """
    Returnerar:
    - fixed_article_text (str)
    - updated_links_extension (dict)
    - autofix_log (dict)
    """
```

**Logik:**
1. Om `qc_report["overall_status"] == "BLOCKED"` → ingen autofix, returnera som är
2. Om `qc_report["overall_status"] == "WARNING"`:
   - Identifiera största problemet
   - Applicera EN fix via LLM
   - Logga i `autofix_log`
   - Sätt `qc_extension.notes_observability.autofix_done = true`

**Test:** Skapa en artikel med känt problem, verifiera att autofix fixar det.

---

### STEG 10: STATE MACHINE

**Fil:** `src/state/machine.py`

**Vad den ska göra:**
Orkestrera hela flödet:
```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
            ↓ (vid WARNING)
          RESCUE (AutoFixOnce)
            ↓
        QC → DELIVER
            ↓ (vid BLOCKED)
          ABORT
```

**Huvudfunktion:**
```python
class BacklinkJobStateMachine:
    def __init__(self, job_id: str, llm_client: LLMClient, config: dict):
        self.job_id = job_id
        self.state = "RECEIVE"
        self.execution_log = []
        # ...

    def run(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str
    ) -> dict:
        """
        Kör hela pipelinen.
        Returnerar:
        {
          "job_id": str,
          "status": "DELIVERED | ABORTED",
          "job_package": dict,
          "article": str,
          "qc_report": dict,
          "execution_log": list
        }
        """
```

**State Transitions:**
```python
def _state_receive(self, ...):
    # Validera input
    # Log transition
    self.state = "PREFLIGHT"

def _state_preflight(self, ...):
    # Kör profilers + SERP research
    # Log transition
    self.state = "WRITE"

def _state_write(self, ...):
    # Generera artikel
    # Log transition
    self.state = "QC"

def _state_qc(self, ...):
    # Kör QC
    # Om PASS → DELIVER
    # Om WARNING → RESCUE
    # Om BLOCKED → ABORT

def _state_rescue(self, ...):
    # Kör AutoFixOnce
    # Log transition
    # Gå tillbaka till QC
    # Om samma problem → ABORT (loop protection)

def _state_deliver(self, ...):
    # Spara alla output-filer
    # Return success

def _state_abort(self, ...):
    # Spara partial output + error log
    # Return failure
```

**Execution Log Format:**
```python
{
  "timestamp": "2025-11-12T10:30:00",
  "state": "PREFLIGHT",
  "action": "Completed target profiling",
  "data": {...}  # relevant data snapshot
}
```

**Test:** Kör en fullständig pipeline och inspektera execution_log.

---

### STEG 11: API & CLI

**Fil:** `src/api.py`

**Huvudfunktion:**
```python
def run_backlink_job(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    config: dict = None
) -> dict:
    """
    Public API för att köra ett backlink-jobb.

    Returns:
    {
      "job_id": str,
      "status": "DELIVERED | ABORTED",
      "output_dir": str,  # path to output directory
      "job_package": dict,
      "article": str,
      "qc_report": dict,
      "execution_log": list
    }
    """
    # Load config
    # Initialize LLM client
    # Create StateMachine
    # Run
    # Save output files
    # Return result
```

**Fil:** `main.py`

**CLI:**
```python
import argparse
from src.api import run_backlink_job

def main():
    parser = argparse.ArgumentParser(description="BACOWR - Backlink Content Writer")
    parser.add_argument("--publisher", required=True, help="Publisher domain")
    parser.add_argument("--target", required=True, help="Target URL")
    parser.add_argument("--anchor", required=True, help="Anchor text")
    parser.add_argument("--output", default="./storage/output", help="Output directory")

    args = parser.parse_args()

    result = run_backlink_job(
        publisher_domain=args.publisher,
        target_url=args.target,
        anchor_text=args.anchor
    )

    print(f"Job ID: {result['job_id']}")
    print(f"Status: {result['status']}")
    print(f"Output: {result['output_dir']}")

    if result['status'] == 'DELIVERED':
        print("\n✅ SUCCESS - Article generated!")
        print(f"   - Article: {result['output_dir']}/{result['job_id']}_article.md")
        print(f"   - Job Package: {result['output_dir']}/{result['job_id']}_job_package.json")
        print(f"   - QC Report: {result['output_dir']}/{result['job_id']}_qc_report.json")
    else:
        print("\n❌ FAILED - Check execution log for details")
        print(f"   - Log: {result['output_dir']}/{result['job_id']}_execution_log.json")

if __name__ == "__main__":
    main()
```

**Test:**
```bash
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product-x \
  --anchor "bästa valet för X" \
  --output ./storage/output
```

---

### STEG 12: SCHEMA & VALIDATION TESTS

**Fil:** `schemas/backlink_job_package.schema.json`

Kopiera från existerande `backlink_job_package.schema.json` (om den finns) eller skapa enligt spec.

**Fil:** `tests/test_schema_validation.py`

```python
import json
import jsonschema
import pytest

def test_example_job_package_validates():
    """Test that example job package validates against schema"""
    with open("schemas/backlink_job_package.schema.json") as f:
        schema = json.load(f)

    with open("examples/example_job_package.json") as f:
        example = json.load(f)

    # Should not raise exception
    jsonschema.validate(instance=example, schema=schema)

def test_minimal_job_package_validates():
    """Test that minimal job package validates"""
    with open("schemas/backlink_job_package.schema.json") as f:
        schema = json.load(f)

    minimal = {
        "job_meta": {
            "job_id": "test-001",
            "created_at": "2025-11-12T10:00:00",
            "version": "1.0"
        },
        "input_minimal": {
            "publisher_domain": "example.com",
            "target_url": "https://target.com",
            "anchor_text": "test anchor"
        },
        # ... (add minimal required fields)
    }

    jsonschema.validate(instance=minimal, schema=schema)
```

**Fil:** `tests/test_live_validation.py`

```python
from src.api import run_backlink_job
import json
import jsonschema

def test_live_job_generates_valid_package():
    """Test that a real job generates schema-valid output"""
    result = run_backlink_job(
        publisher_domain="test-publisher.com",
        target_url="https://test-target.com/page",
        anchor_text="test anchor text"
    )

    assert result["status"] in ["DELIVERED", "ABORTED"]

    # Load schema
    with open("schemas/backlink_job_package.schema.json") as f:
        schema = json.load(f)

    # Validate generated job package
    jsonschema.validate(instance=result["job_package"], schema=schema)
```

**Test:**
```bash
pytest tests/ -v
```

---

### STEG 13: README & DOCUMENTATION

**Fil:** `README.md`

Innehåll:
1. **Projektöversikt** - Vad gör systemet?
2. **Installation**
   ```bash
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   ```
3. **Snabbstart**
   ```bash
   python main.py --publisher example.com --target https://... --anchor "..."
   ```
4. **Användning**
   - CLI
   - Python API
5. **Output-förklaring**
   - Vad finns i job_package.json?
   - Hur tolka QC-rapporten?
6. **Konfiguration**
   - config/thresholds.yaml
   - config/policies.yaml
   - config/publisher_voices.yaml
7. **Tester**
   ```bash
   pytest tests/
   ```
8. **Felsökning**
   - Vanliga problem
   - Hur läsa execution_log

---

## VIKTIGA PRINIPER UNDER BYGGANDET

### 1. BYGG INKREMENTELLT
- Testa varje komponent isolerat innan du går vidare
- Använd mock data i början om external APIs saknas
- Få något att fungera end-to-end tidigt, förfina sedan

### 2. LLM PROMPTS ÄR KRITISKA
- Var extremt tydlig i prompts
- Begär strukturerad JSON när möjligt
- Inkludera exempel i prompts
- Testa prompts iterativt

### 3. FELHANTERING
- Logga allt (API-calls, state transitions, beslut)
- Fånga exceptions gracefully
- Ge meningsfulla felmeddelanden

### 4. CONFIGURATION ÖVER HARDCODING
- Använd YAML-config för policies, thresholds, voices
- Gör det lätt att justera utan kodändringar

### 5. OUTPUT-SPÅRBARHET
- Spara execution_log för varje jobb
- Dokumentera varje beslut (varför denna bridge_type? varför denna alignment?)
- QC-rapporten ska vara läsbar för människor

---

## CHECKLIST - NÄR ÄR DU KLAR?

- [ ] Alla filer i filstrukturen skapade
- [ ] requirements.txt och .env.example finns
- [ ] LLM client fungerar (kan göra API-calls)
- [ ] Target profiler fungerar (kan fetch + analysera målsida)
- [ ] Publisher profiler fungerar
- [ ] Anchor profiler fungerar
- [ ] SERP research fungerar (fetch + analysera topp-10)
- [ ] Intent modeler fungerar (härledning + alignment + bridge recommendation)
- [ ] Content generation fungerar (genererar artikel enligt spec)
- [ ] QC controller fungerar (validerar artikel)
- [ ] AutoFix fungerar (en fix vid WARNING)
- [ ] State machine fungerar (fullständig pipeline)
- [ ] API-funktion fungerar (`src/api.py::run_backlink_job`)
- [ ] CLI fungerar (`python main.py ...`)
- [ ] Schema validation test passerar
- [ ] Live validation test passerar
- [ ] README är komplett
- [ ] Manuell test: Kör ett riktigt case och inspektera output

---

## EXEMPEL PÅ MANUELL TESTKÖRNING

```bash
# Setup
pip install -r requirements.txt
cp .env.example .env
# Lägg till ANTHROPIC_API_KEY i .env

# Testkörning
python main.py \
  --publisher konsumenternas.se \
  --target https://www.ica.se/recept/ \
  --anchor "hitta goda recept" \
  --output ./storage/output

# Inspektera output
ls storage/output/  # Se job_id directory
cat storage/output/{job_id}/{job_id}_article.md
cat storage/output/{job_id}/{job_id}_qc_report.json
```

**Verifiera:**
1. Artikeln är 900+ ord
2. Artikeln matchar publisher tone (konsumenternas.se → consumer_magazine style)
3. Länken är placerad korrekt (ej i H1/H2, mittsektion)
4. 6-10 LSI-termer finns i närfönster
5. Minst 1 trust-källa finns
6. QC-rapporten visar PASS eller rimliga WARNINGs
7. Execution log visar alla state transitions

---

## SUPPORT & REFERENSER

**Specifikation:** `IMPLEMENTATION_SPEC.md` (läs denna för detaljer!)

**JSON Schema:** `schemas/backlink_job_package.schema.json`

**Config:**
- `config/thresholds.yaml`
- `config/policies.yaml`
- `config/publisher_voices.yaml`

**Existerande spec-filer:**
- `next-a1-spec.json`
- `NEXT-A1-ENGINE-ADDENDUM.md`
- `backlink_engine_ideal_flow.md`

---

## FRAMGÅNG = ETT FUNGERANDE SYSTEM SOM:

1. ✅ Tar 3 inputs (publisher, target, anchor)
2. ✅ Genererar komplett artikel (900+ ord)
3. ✅ Med korrekt länkplacering (semantiskt motiverad)
4. ✅ Med intent-alignment (ej gissa, härled från SERP)
5. ✅ Med QC-validering
6. ✅ Med spårbar execution log
7. ✅ Som går att köra via CLI
8. ✅ Som valideras mot JSON schema

**LYCKA TILL!** 🚀

Du har all information du behöver. Följ stegen metodiskt, testa inkrementellt, och du kommer ha ett fungerande system.

Om något är oklart - referera tillbaka till `IMPLEMENTATION_SPEC.md` för detaljer.

---

**Version:** 1.0
**Datum:** 2025-11-12
**För:** Claude Code (Browser Edition)
