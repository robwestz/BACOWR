# CLAUDE CODE PROMPT - BACOWR System Build
## Kopiera denna prompt till Claude Code i browser för att bygga hela systemet

---

## DIN UPPGIFT

Du ska bygga ett komplett Python-system för att generera högkvalitativa backlänksartiklar.

**System:** BACOWR (Backlink Content Writer)

**Input (endast 3 fält):**
- `publisher_domain` (t.ex. "example-publisher.com")
- `target_url` (t.ex. "https://client.com/product-x")
- `anchor_text` (t.ex. "bästa valet för X")

**Output:**
- Komplett artikel (900+ ord) i Markdown
- JSON-paket med all metadata (job_package, extensions)
- QC-rapport
- Execution log

---

## VÄGLEDANDE DOKUMENT

Du har tillgång till följande dokument i projektet:

1. **`IMPLEMENTATION_SPEC.md`** - Komplett specifikation (vad systemet ska göra)
2. **`BUILDER_PROMPT.md`** - Steg-för-steg guide (hur man bygger det)
3. **`API_INTEGRATION_GUIDE.md`** - Hur man integrerar ChatGPT:s API-kod
4. **`PROJECT_STATUS.md`** - Nuläge och översikt
5. **`utkast-till-api-lösning/`** - Befintlig kod från ChatGPT (SERP, metadata extraction)
6. **`next-a1-spec.json`** - Next-A1 ramverkets fullständiga spec

**Läs dessa filer först innan du börjar!**

---

## ARKITEKTUR-BESLUT

### Integration-strategi: STRATEGI B (Monolitisk)

Använd **Strategi B** från `API_INTEGRATION_GUIDE.md`:
- Importera moduler från `utkast-till-api-lösning/app/` direkt i pipeline
- Allt körs i samma process (no HTTP calls)
- Enklare deployment, snabbare exekvering

**Konkret:**
1. Kopiera `utkast-till-api-lösning/app/` → `src/preflight/`
2. Importera och använd modulerna direkt i profilers och SERP research
3. Förstärk med LLM-analys där heuristiker inte räcker

### LLM Provider: Claude (Anthropic)

Använd Claude API (Anthropic):
- Sonnet för djupare analyser (intent modeling, content generation)
- Haiku för snabbare klassificeringar (anchor type, page type)
- Structured output (JSON mode) där möjligt

### SERP Provider: Mock först, sedan riktig

Börja med mock-provider (redan implementerad i ChatGPT:s kod).
Byt till riktig SERP API (SerpAPI eller Google CSE) senare.

---

## BYGGORDNING (Följ exakt)

### STEG 0: SETUP & STRUKTUR

**Skapa filstruktur:**
```
BACOWR/
├── main.py                    # CLI entrypoint
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables example
├── README.md                 # User documentation
├── src/
│   ├── __init__.py
│   ├── api.py                # Python API (run_backlink_job)
│   ├── preflight/            # <-- Kopierad från utkast-till-api-lösning/app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── extract.py
│   │   ├── serp_providers.py
│   │   ├── intent_policy.py
│   │   ├── policy.py
│   │   ├── utils.py
│   │   └── webhooks.py
│   ├── profile/
│   │   ├── __init__.py
│   │   ├── target_profiler.py
│   │   ├── publisher_profiler.py
│   │   └── anchor_profiler.py
│   ├── serp/
│   │   ├── __init__.py
│   │   └── research.py
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

**Action:**
1. Skapa alla mappar och `__init__.py` filer
2. Kopiera `utkast-till-api-lösning/app/*` → `src/preflight/`
3. Skapa `requirements.txt` (se nedan)
4. Skapa `.env.example` (se nedan)

**requirements.txt:**
```
requests>=2.31.0
httpx>=0.27.2
beautifulsoup4>=4.12.3
lxml>=5.3.0
anthropic>=0.8.0
jsonschema>=4.20.0
pyyaml>=6.0.0
pydantic>=2.9.2
pydantic-settings>=2.5.2
python-dotenv>=1.0.1
```

**.env.example:**
```
ANTHROPIC_API_KEY=your_key_here
SERP_PROVIDER=mock
SERPAPI_KEY=
DEFAULT_LANGUAGE=sv
OUTPUT_DIR=./storage/output
```

---

### STEG 1: UTILS & LLM CLIENT

**Fil:** `src/utils/llm.py`

Implementera LLM client wrapper för Anthropic Claude API:
- `generate_structured(prompt, schema)` - För JSON output
- `generate_text(prompt)` - För fritext
- Hantera retries och errors
- Logga API-calls

**Referens:** Se `BUILDER_PROMPT.md` STEG 1 för kodskelett

**Fil:** `src/utils/helpers.py`

Implementera hjälpfunktioner:
- `generate_job_id()` - Unikt ID per jobb
- `sanitize_filename(name)` - Säkra filnamn
- `truncate_text(text, max_chars)` - Trunkera text
- `extract_domain(url)` - Extrahera domän från URL

**Test:** Kör `python -c "from src.utils.llm import LLMClient; print('OK')"`

---

### STEG 2: TARGET PROFILER

**Fil:** `src/profile/target_profiler.py`

**Använd:** `src/preflight/extract.py` för HTML-hämtning + BeautifulSoup parsing

**Förstärk med:** LLM-analys för:
- `core_entities` - Extrahera viktiga namngivna entiteter
- `core_topics` - Identifiera huvudteman
- `core_offer` - Vad hjälper sidan användaren med?
- `candidate_main_queries` - 2-3 sökqueries sidan vill ranka för

**Huvudfunktion:**
```python
async def profile_target(url: str, llm_client: LLMClient) -> dict:
    """Returns target_profile according to schema"""
```

**LLM Prompt exempel:** Se `BUILDER_PROMPT.md` STEG 2

**Test:** Kör på en känd URL (t.ex. "https://www.ica.se/recept/")

---

### STEG 3: PUBLISHER PROFILER

**Fil:** `src/profile/publisher_profiler.py`

**Använd:** `src/preflight/extract.py` för att fetch homepage + about page + sample articles

**Förstärk med:** LLM-analys för:
- `topic_focus` - Vilka ämnen täcker sajten?
- `audience` - Vilken målgrupp?
- `tone_class` - academic | authority_public | consumer_magazine | hobby_blog
- `allowed_commerciality` - low | medium | high
- `brand_safety_notes` - Restriktioner (gambling, lån, etc.)

**Huvudfunktion:**
```python
async def profile_publisher(domain: str, llm_client: LLMClient) -> dict:
    """Returns publisher_profile according to schema"""
```

**LLM Prompt exempel:** Se `BUILDER_PROMPT.md` STEG 3

**Test:** Kör på en känd publisher (t.ex. "konsumenternas.se")

---

### STEG 4: ANCHOR PROFILER

**Fil:** `src/profile/anchor_profiler.py`

**Använd:** `src/preflight/intent_policy.py` för basic heuristics

**Förstärk med:** LLM-klassificering:
- `llm_classified_type` - exact | partial | brand | generic
- `llm_intent_hint` - info_primary | commercial_research | transactional | navigational_brand

**Huvudfunktion:**
```python
def profile_anchor(anchor_text: str, target_context: dict, llm_client: LLMClient) -> dict:
    """Returns anchor_profile"""
```

**LLM Prompt exempel:** Se `BUILDER_PROMPT.md` STEG 4

**Test:** Testa med olika ankartexter

---

### STEG 5: SERP RESEARCH

**Fil:** `src/serp/research.py`

**Använd:** `src/preflight/serp_providers.py` för SERP-hämtning (börja med mock)

**Förstärk med:** LLM-analys på två nivåer:

1. **Per SERP-resultat:**
   - Klassificera page type (guide, comparison, product, etc.)
   - Extrahera key entities (3-5 st)
   - Extrahera key subtopics (2-4 st)

2. **Per SERP-set (hela topp-10):**
   - Bestäm dominant_intent
   - Bestäm secondary_intents
   - Identifiera required_subtopics (vad ALLA täcker)
   - Identifiera page_archetypes

**Huvudfunktion:**
```python
async def conduct_serp_research(
    target_profile: dict,
    anchor_profile: dict,
    llm_client: LLMClient
) -> dict:
    """Returns serp_research_extension"""
```

**LLM Prompts exempel:** Se `BUILDER_PROMPT.md` STEG 5

**Test:** Kör med mock-queries och inspektera strukturen

---

### STEG 6: INTENT MODELER

**Fil:** `src/intent/modeler.py`

**Använd:** `src/preflight/intent_policy.py` för basic alignment logic

**Förstärk med:** LLM-analys för:
- `target_page_intent` - Vilken intent har målsidan?
- `publisher_role_intent` - Vilken roll spelar publisher naturligt?
- `intent_alignment` - Jämför anchor/target/publisher vs SERP
- `recommended_bridge_type` - strong | pivot | wrapper
- `recommended_article_angle` - Vilken vinkel ska artikeln ha?
- `required_subtopics` - Merged från alla SERP-sets
- `forbidden_angles` - Vad ska artikeln INTE göra?

**Huvudfunktion:**
```python
def model_intent(
    target_profile: dict,
    publisher_profile: dict,
    anchor_profile: dict,
    serp_research: dict,
    llm_client: LLMClient
) -> dict:
    """Returns intent_extension"""
```

**Bridge Type Logic (VIKTIGT):**
- **STRONG:** Om anchor_vs_serp, target_vs_serp, publisher_vs_serp alla är aligned/partial
- **PIVOT:** Om minst en är partial men kan lösas med tematisk brygga
- **WRAPPER:** Om overall är off, behöver meta-ram

**LLM Prompt exempel:** Se `BUILDER_PROMPT.md` STEG 6 (stor och viktig prompt!)

**Test:** Kör med kompletta profiler och verifiera alignment-logiken

---

### STEG 7: CONTENT GENERATION (WRITER)

**Fil:** `src/generation/writer.py`

Detta är den **viktigaste** komponenten! Generera komplett artikel enligt:

**Inputs:**
- target_profile
- publisher_profile
- anchor_profile
- serp_research
- intent_profile

**Outputs:**
- article_text (Markdown, 900+ ord)
- links_extension (JSON med metadata om länkplacering)

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
    """Returns (article_text, links_extension)"""
```

**Artikel-struktur beroende på publisher tone_class:**

Läs från `config/publisher_voices.yaml`:
```yaml
academic:
  structure: "Inledning → Metod → Resultat/Implikation → Referenser"
  tone: "Saklig, källförande, låg värdeladdning"

authority_public:
  structure: "Sammanhang → Rekommendation → Hur-gör-man → Källor"
  tone: "Myndighetsnära klarspråk"

consumer_magazine:
  structure: "Hook → Mittpunkt → Fördjupning → Call-to-value → Resurser"
  tone: "Lättillgänglig, nytta först, konkreta exempel"

hobby_blog:
  structure: "Bakgrund → Case → Tips → Resurser"
  tone: "Personligt sakkunnig, berättande"
```

**Kritiska krav:**
1. **Bridge type-strategi:**
   - STRONG: Direktlänkning tidigt i relevant sektion
   - PIVOT: Etablera tematisk pivot först, länka sedan
   - WRAPPER: Bygg neutral meta-ram, länka efter ram är etablerad

2. **Länkplacering:**
   - ALDRIG i H1 eller H2
   - I mittsektion (stycke 1-2 efter kontext etablerats)
   - Markera som: `[[LINK:{anchor_text}|{target_url}]]`

3. **LSI-termer:**
   - 6-10 relevanta termer i närfönster (±2 meningar från anchor)
   - Blanda begreppstyper: processer, mått, teorier, felkällor
   - Använd entiteter från SERP research + target profile

4. **Trust-källor:**
   - 1-3 källor (T1_public > T2_academic > T3_industry > T4_media)
   - Prioritera svenska myndigheter
   - Markera som: `[[TRUST:{beskrivning}|{url}]]`

5. **Compliance:**
   - Lägg till disclaimer för reglerade vertikaler (gambling, finance, health, crypto)

**LLM Prompt:** Se `BUILDER_PROMPT.md` STEG 7 (mycket stor och komplex prompt!)

**Test:** Generera en artikel och inspektera manuellt

---

### STEG 8: QC CONTROLLER

**Fil:** `src/qc/controller.py`

Validera genererad artikel mot kvalitetskriterier:

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
    """Returns qc_extension"""
```

**Validera:**
1. **Anchor risk** (high/medium/low) - Se `config/thresholds.yaml`
2. **LSI quality** - Räkna LSI-termer i närfönster (6-10 krav)
3. **Trust sources** - Minst 1 godkänd källa
4. **Placement** - Länk EJ i H1/H2
5. **Compliance** - Disclaimers för reglerade vertikaler
6. **Intent alignment** - Från intent_profile

**Status-logik:**
- **PASS:** Allt OK
- **WARNING:** Mindre brister (kan fixas med AutoFix)
- **BLOCKED:** Allvarliga brister (kräver manuell granskning)

**Flagga för manuell granskning när:**
- anchor_risk == "high"
- Inga trust-källor hittades
- Compliance-disclaimers saknas i reglerad vertikal
- intent_alignment.overall == "off"

**Config:** `config/thresholds.yaml` - Se `BUILDER_PROMPT.md` STEG 8

**Test:** Kör på genererad artikel

---

### STEG 9: AUTOFIX

**Fil:** `src/qc/autofix.py`

Om QC hittar mindre brister (WARNING), gör EN automatisk fix:

**Huvudfunktion:**
```python
def apply_autofix_once(
    article_text: str,
    links_extension: dict,
    qc_report: dict,
    policies: dict,
    llm_client: LLMClient
) -> tuple[str, dict, dict]:
    """Returns (fixed_article, updated_links_extension, autofix_log)"""
```

**Tillåtna fixes (välj EN):**
- Flytta länk inom sektion
- Byta ankartyp (exact → generic)
- Injicera saknade LSI-termer
- Lägga till disclaimer

**Aldrig:**
- Ändra H1, titel
- Ta bort sektioner
- Fabricera citat

**Logga:** Vad som fixades i `autofix_log`

**Test:** Skapa en artikel med känt problem, verifiera att autofix fixar det

---

### STEG 10: STATE MACHINE

**Fil:** `src/state/machine.py`

Orkestrera hela flödet:

**States:**
```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
             ↓ (vid WARNING)
          RESCUE (AutoFixOnce)
             ↓
         QC → DELIVER
             ↓ (vid BLOCKED)
          ABORT
```

**Huvudklass:**
```python
class BacklinkJobStateMachine:
    def __init__(self, job_id: str, llm_client: LLMClient, config: dict)

    def run(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str
    ) -> dict:
        """Kör hela pipelinen"""
```

**State transitions:** Se `BUILDER_PROMPT.md` STEG 10

**Execution log:** Logga varje state transition med timestamp + data

**Loop-skydd:** Om RESCUE inte ändrar något → ABORT

**Test:** Kör en fullständig pipeline och inspektera execution_log

---

### STEG 11: API & CLI

**Fil:** `src/api.py`

Public API-funktion:
```python
def run_backlink_job(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    config: dict = None
) -> dict:
    """
    Returns:
    {
      "job_id": str,
      "status": "DELIVERED | ABORTED",
      "output_dir": str,
      "job_package": dict,
      "article": str,
      "qc_report": dict,
      "execution_log": list
    }
    """
```

**Fil:** `main.py`

CLI med argparse:
```python
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product-x \
  --anchor "bästa valet för X" \
  --output ./storage/output
```

**Test:** Kör CLI och verifiera output

---

### STEG 12: SCHEMA & VALIDATION TESTS

**Fil:** `schemas/backlink_job_package.schema.json`

Skapa JSON Schema enligt Next-A1 spec.

**Fil:** `tests/test_schema_validation.py`

Testa att exempel validerar mot schema.

**Fil:** `tests/test_live_validation.py`

E2E test som kör full pipeline och validerar output.

**Test:** `pytest tests/ -v`

---

### STEG 13: CONFIG & DOCUMENTATION

**Fil:** `config/thresholds.yaml`

Se `BUILDER_PROMPT.md` STEG 8 för exempel.

**Fil:** `config/policies.yaml`

Trust policy, anchor policy, compliance rules.

**Fil:** `config/publisher_voices.yaml`

Se STEG 7 ovan för exempel.

**Fil:** `README.md`

Innehåll:
1. Projektöversikt
2. Installation
3. Snabbstart
4. Användning (CLI + Python API)
5. Output-förklaring
6. Konfiguration
7. Tester
8. Felsökning

**Fil:** `examples/example_job_package.json`

Exempel på komplett output.

---

## VIKTIGA PRINCIPER

### 1. BYGG INKREMENTELLT
- Implementera ett steg i taget
- Testa varje komponent isolerat
- Få något att fungera end-to-end tidigt, förfina sedan

### 2. LLM PROMPTS ÄR KRITISKA
- Var extremt tydlig i prompts
- Begär strukturerad JSON när möjligt
- Inkludera exempel i prompts
- Testa prompts iterativt

### 3. ÅTERANVÄND CHATGPT:S KOD
- `src/preflight/extract.py` - HTML parsing (redan bra!)
- `src/preflight/serp_providers.py` - SERP fetching (redan bra!)
- `src/preflight/intent_policy.py` - Heuristiker (förstärk med LLM)
- `src/preflight/policy.py` - Extensions builder (använd direkt)

### 4. FELHANTERING
- Logga allt (API-calls, state transitions, beslut)
- Fånga exceptions gracefully
- Ge meningsfulla felmeddelanden

### 5. CONFIGURATION ÖVER HARDCODING
- Använd YAML-config för policies, thresholds, voices
- Gör det lätt att justera utan kodändringar

---

## ACCEPTANCE CRITERIA

Systemet är klart när:

- [ ] CLI fungerar
- [ ] Alla profilers fungerar
- [ ] SERP research fungerar
- [ ] Intent modeler fungerar
- [ ] Writer genererar 900+ ord artikel
- [ ] QC validerar artikel
- [ ] Output genereras korrekt (JSON + MD)
- [ ] Schema validation test passerar
- [ ] README är komplett
- [ ] Manuell test: Kör ett riktigt case och inspektera output

---

## EXEMPEL PÅ TESTKÖRNING

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

## ARBETSSÄTT

**För varje steg:**
1. Läs relevant sektion i `BUILDER_PROMPT.md`
2. Implementera koden
3. Förklara kort vad du gjort
4. Testa komponenten isolerat
5. Visa testresultat
6. Vänta på min bekräftelse innan nästa steg

**Fråga mig om:**
- Design-beslut som är oklara
- Implementationsdetaljer som saknas
- Val mellan alternativ
- Test-resultat som ser konstiga ut

**Viktigt:**
- Skriv ren, läsbar kod med kommentarer
- Följ Python best practices (PEP 8)
- Hantera errors gracefully
- Logga viktiga beslut

---

## STARTKOMMANDO

**Börja med:**

"Jag har läst alla dokument. Jag börjar nu med STEG 0: Setup & struktur.

Jag kommer att:
1. Skapa filstrukturen enligt specifikationen
2. Kopiera `utkast-till-api-lösning/app/` till `src/preflight/`
3. Skapa `requirements.txt` och `.env.example`
4. Skapa alla `__init__.py` filer

Väntar på din bekräftelse innan jag kör."

---

**LYCKA TILL! 🚀**

**Du har all information du behöver. Följ stegen metodiskt, testa inkrementellt, och du kommer ha ett fungerande system.**

---

**END OF PROMPT**
