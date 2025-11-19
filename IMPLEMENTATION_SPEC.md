# BACOWR Implementation Specification
## Backlink Content Writer - Komplett Implementeringsspecifikation

---

## PROJEKTÖVERSIKT

Detta är ett system för att generera högkvalitativa backlänksartiklar baserat på **tre enkla inputs**:
- **Publiceringsdomän** (publisher_domain)
- **Målsida** (target_url)
- **Ankartext** (anchor_text)

Systemet ska automatiskt:
1. Analysera målsidan och publiceringsdomänen
2. Göra SERP-research för att förstå sökintention
3. Modellera intent och välja rätt bryggstrategi
4. Generera semantiskt korrekt artikel med optimal länkplacering
5. Validera output mot kvalitetskriterier (QC)

---

## KÄRN-KONCEPTET: VARIABELGIFTERMÅLET

Allt utgår från att **gifta samman fyra variabler**:
1. **Publikationssajt** - Var ska artikeln publiceras?
2. **Ankare** - Vilken ankartext ska användas?
3. **Målsida** - Vilken sida ska länkas?
4. **Intention** - Vilken sökintenation ska matchas?

**Kritiskt:** Intention är lika viktig som de andra tre. Den får INTE gissas, utan måste härledas från:
- Målsidans faktiska innehåll
- SERP-signaler (vad rankar topp-10?)
- Publikationssajtens naturliga roll och trovärdighet

---

## SYSTEMARKITEKTUR

### Input → Processing → Output

```
INPUT (3 fält)
    ↓
[1. FETCH & PROFILE]
    - Target Profile (målsidans innehåll, struktur, entiteter)
    - Publisher Profile (sajtens ton, röst, ämnesfokus)
    - Anchor Profile (klassning av ankartyp och intent)
    ↓
[2. SERP RESEARCH]
    - Huvudquery + 1-2 klusterqueries
    - Hämta topp-10 resultat per query
    - Analysera dominant intent, sidtyper, subtopics
    ↓
[3. INTENT MODELING]
    - Härled serp_intent_primary/secondary
    - Jämför anchor vs SERP, target vs SERP, publisher vs SERP
    - Bestäm alignment (aligned/partial/off)
    - Rekommendera bridge_type (strong/pivot/wrapper)
    ↓
[4. CONTENT GENERATION]
    - Välj bryggstrategi baserat på intent
    - Generera 900+ ord artikel
    - Placera länk enligt regler (ej H1/H2, mittsektion)
    - Injicera 6-10 LSI-termer i närfönster (±2 meningar)
    - Lägg till trust-källor (T1-T4 prioritet)
    ↓
[5. QC & AUTOFIX]
    - Validera mot kvalitetströsklar
    - En automatisk fix tillåten (AutoFixOnce)
    - Flagga för manuell granskning vid allvarliga brott
    ↓
OUTPUT
    - BacklinkJobPackage (JSON)
    - Artikel (MD/HTML)
    - Links Extension (JSON)
    - Intent Extension (JSON)
    - QC Extension (JSON)
    - SERP Research Extension (JSON)
    - Execution Log (JSON)
```

---

## DETALJERADE KOMPONENTER

### 1. FETCH & PROFILE

#### Target Profile
Hämta och analysera målsidan:
```json
{
  "url": "https://client.com/product-x",
  "http_status": 200,
  "title": "extracted title",
  "meta_description": "extracted meta",
  "h1": "main heading",
  "h2_h3_sample": ["heading 2", "heading 3"],
  "main_content_excerpt": "first 500 chars of body",
  "detected_language": "sv",
  "core_entities": ["Product X", "category Y", "problem Z"],
  "core_topics": ["theme1", "theme2"],
  "core_offer": "what the page helps user achieve",
  "candidate_main_queries": ["query 1", "query 2"]
}
```

**Implementation:**
- Fetch HTML med requests/httpx
- Parse med BeautifulSoup/lxml
- Extrahera metadata (title, meta, headings)
- Identifiera main content (exkludera nav, footer, sidebar)
- LLM-analys för entiteter, topics, offer, queries

#### Publisher Profile
Analysera publiceringsdomänen:
```json
{
  "domain": "example-publisher.com",
  "sample_urls": ["url1", "url2", "url3"],
  "about_excerpt": "truncated about page text",
  "detected_language": "sv",
  "topic_focus": ["personal finance", "consumer advice"],
  "audience": "brief audience description",
  "tone_class": "consumer_magazine | academic | authority_public | hobby_blog",
  "allowed_commerciality": "low | medium | high",
  "brand_safety_notes": "restrictions/warnings"
}
```

**Implementation:**
- Crawl homepage + /om-oss + 2-3 sample articles
- LLM-analys för ton, röst, ämnesfokus
- Klassificera enligt PublisherVoice-profiler

#### Anchor Profile
Klassificera ankaret:
```json
{
  "proposed_text": "bästa valet för X",
  "type_hint": null,
  "llm_classified_type": "exact | partial | brand | generic",
  "llm_intent_hint": "info_primary | commercial_research | transactional"
}
```

---

### 2. SERP RESEARCH

**Kritiskt:** Detta är hjärtat av intentmodelleringen.

För varje query (huvud + kluster):
1. Hämta topp-10 SERP-resultat
2. För varje resultat, analysera:
   - URL, title, snippet
   - Sidtyp (guide, comparison, product, review, etc.)
   - Key entities & subtopics
   - Varför den rankar

**SERP Research Extension Schema:**
```json
{
  "main_query": "primary query based on target",
  "cluster_queries": ["related query 1", "related query 2"],
  "queries_rationale": "why these queries were chosen",
  "serp_sets": [
    {
      "query": "specific query string",
      "dominant_intent": "info_primary | commercial_research | transactional | navigational_brand | support | local | mixed",
      "secondary_intents": ["intent2"],
      "page_archetypes": ["guide", "comparison", "product"],
      "required_subtopics": ["subtopic all top results cover"],
      "top_results_sample": [
        {
          "rank": 1,
          "url": "https://...",
          "title": "...",
          "detected_page_type": "guide",
          "snippet": "...",
          "content_signals": ["what the page emphasizes"],
          "key_entities": ["entity1", "entity2"],
          "key_subtopics": ["subtopic1", "subtopic2"]
        }
        // ... up to rank 10
      ]
    }
  ],
  "derived_links": {
    "intent_profile_ref": "maps to intent_extension",
    "required_subtopics_merged_ref": "all required subtopics",
    "data_confidence": "high | medium | low"
  }
}
```

**Implementation Options:**
1. **SERP API** (ValueSERP, SerpApi, DataForSEO) - Rekommenderat för stabilitet
2. **Web scraping** (playwright/selenium) - Fallback
3. **Hybrid** - API först, scraping som backup

---

### 3. INTENT MODELING

Härled intent-profil från alla källor:

```json
{
  "serp_intent_primary": "commercial_research",
  "serp_intent_secondary": ["info_primary"],
  "target_page_intent": "transactional_with_info_support",
  "anchor_implied_intent": "commercial_research",
  "publisher_role_intent": "info_primary",

  "intent_alignment": {
    "anchor_vs_serp": "aligned | partial | off",
    "target_vs_serp": "aligned | partial | off",
    "publisher_vs_serp": "aligned | partial | off",
    "overall": "aligned | partial | off"
  },

  "recommended_bridge_type": "strong | pivot | wrapper",
  "recommended_article_angle": "suggested angle",

  "required_subtopics": ["must cover these topics"],
  "forbidden_angles": ["do not use these angles"],

  "notes": {
    "rationale": "why this bridge type",
    "data_confidence": "high | medium | low"
  }
}
```

**Bridge Type Decision Logic:**

- **STRONG** (direktlänkning):
  - Endast om anchor, target, publisher alla är aligned/partial mot SERP
  - Publisher niche overlap ≥ 0.7
  - Placera tidigt i relevant huvudsektion

- **PIVOT** (tematisk brygga):
  - När minst en är partial men kan lösas via tematiskt brobyggande
  - Publisher niche overlap 0.4-0.7
  - Etablera semantisk pivot först

- **WRAPPER** (metaram):
  - När overall är 'off' utan legitim direktkoppling
  - Publisher niche overlap < 0.4
  - Bygg neutral temaram (metodik, risk, innovation, etik)
  - Placera länk EFTER att ramen är etablerad

---

### 4. CONTENT GENERATION

Med allt ovanstående som input, generera artikel enligt:

**Generation Constraints:**
```json
{
  "language": "sv",
  "min_word_count": 900,
  "max_word_count": 1500,
  "max_anchor_usages": 2,
  "anchor_policy": "no anchor in H1/H2, natural placement in mid-section",
  "tone_profile": "from publisher_profile.tone_class"
}
```

**Struktur beroende på Publisher Voice:**

- **Academic**: Inledning → Metod → Resultat/Implikation → Källor
- **Authority/Public**: Sammanhang → Rekommendation → Hur-gör-man → Källor
- **Consumer Magazine**: Hook → Mittpunkt → Fördjupning → Call-to-value → Källor
- **Hobby Blog**: Bakgrund → Case → Tips → Källor

**Links Extension:**
```json
{
  "bridge_type": "strong | pivot | wrapper",
  "bridge_theme": "theme if pivot/wrapper",

  "anchor_swap": {
    "performed": true/false,
    "from_type": "exact | partial | brand | generic",
    "to_type": "exact | partial | brand | generic",
    "rationale": "why swap was done"
  },

  "placement": {
    "paragraph_index_in_section": 1,
    "offset_chars": 250,
    "near_window": {
      "unit": "sentence",
      "radius": 2,
      "lsi_count": 8
    }
  },

  "trust_policy": {
    "level": "T1_public | T2_academic | T3_industry | T4_media",
    "fallback_used": false,
    "unresolved": []
  },

  "compliance": {
    "disclaimers_injected": ["gambling", "finance", "health", "legal", "crypto", "none"]
  }
}
```

**LSI (Latent Semantic Indexing) Krav:**
- 6-10 relevanta termer i närfönster (±2 meningar från anchor)
- Blanda begreppstyper: processer, mått/teorier, felkällor
- Undvik bara synonymer; sträva efter entitetskluster
- Spegla required_subtopics från intent_extension

**Trust-källor:**
- **T1_public**: Myndigheter, standardiseringsorgan (prioritera svenska)
- **T2_academic**: Universitet, forskningsdatabaser, peer-review
- **T3_industry**: Branschorganisationer, whitepapers, tekniska standarder
- **T4_media**: Respekterade nyhetshus (endast om T1-T3 saknas)

**Aldrig:**
- Länka till direkta konkurrenter till target_url
- User-generated content som primär trust
- Fabricera siffror eller citat

**Placering av trust-källor:**
- Samla i Resources/Avslut-sektion när naturligt
- Om i bryggstycke: 1-2 diskreta omnämnanden, inte listform
- Använd "PLATSFÖRSLAG" om källa saknas, med motivering

---

### 5. QC & AUTOFIX

**QC Scoring Dimensions:**
```json
{
  "anchor_risk": "low | medium | high",
  "readability": {
    "lix": 42,
    "target_range": "35-45"
  },
  "thresholds_version": "A1",
  "notes_observability": {
    "signals_used": ["target_entities", "publisher_profile", "SERP_intent", "trust_source", "blueprint"],
    "autofix_done": true/false
  }
}
```

**Anchor Risk Heuristics:**
- **High**: Exact match + stark kommersiell intent i svag kontext, eller upprepning 2+ gånger i samma sektion
- **Medium**: Generic i svag kontext utan trust, eller partial med tveksam semantisk passform
- **Low**: Brand/generic i naturlig kontext med LSI och trust i närheten

**AutoFixOnce Policy:**

**Tillåtet (en gång per jobb):**
- Flytta [[LINK]] inom relevant huvudsektion
- Byta ankartyp (exact→generic etc.) för naturlighet
- Lägga till/byta [[TRUST]]; använd PLATSFÖRSLAG vid behov
- Injicera 6-10 LSI-termer i närfönster
- Infoga branschdisclaimer
- Justera mikrocopy enligt intent

**Kräver sign-off:**
- Ändra H1, titel, metatitel
- Byta huvudtema eller grundstruktur
- Ta bort hela sektioner

**Aldrig:**
- Fabricera siffror eller citat
- Länka till konkurrerande målsidor
- Ändra intent på vilseledande sätt

**Flagga för manuell granskning när:**
- `anchor_risk == "high"`
- Inga godkända trust-källor hittas
- Compliance-disclaimers saknas i reglerad vertikal (gambling, finance, health, legal, crypto)
- `intent_alignment.overall == "off"`

---

## STATE MACHINE

Systemet kör genom dessa stater:

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                ↓ (vid mindre fel)
              RESCUE (AutoFixOnce)
                ↓
            QC → DELIVER
                ↓ (vid allvarliga fel)
              ABORT
```

**Krav:**
- Unikt `job_id` per körning
- `execution_log.json` loggar alla state-övergångar
- Loop-skydd: Om RESCUE inte ändrar något → ABORT
- Max en RESCUE-iteration per jobb
- Sätt `human_signoff_required: true` vid kritiska brister

---

## OUTPUT-STRUKTUR

Efter lyckad körning ska följande filer genereras i `storage/output/{job_id}/`:

1. **`{job_id}_job_package.json`** - Fullt BacklinkJobPackage med alla extensions
2. **`{job_id}_article.md`** - Färdig artikel i Markdown
3. **`{job_id}_article.html`** - Artikel i HTML (valfritt)
4. **`{job_id}_qc_report.json`** - QC-resultat
5. **`{job_id}_execution_log.json`** - State machine-logg

---

## FILSTRUKTUR

```
BACOWR/
├── main.py                          # CLI entrypoint
├── src/
│   ├── api.py                       # Python API (run_backlink_job function)
│   ├── profile/
│   │   ├── target_profiler.py      # Fetch & analyze target page
│   │   ├── publisher_profiler.py   # Fetch & analyze publisher
│   │   └── anchor_profiler.py      # Classify anchor
│   ├── serp/
│   │   ├── research.py             # SERP research coordinator
│   │   ├── serp_api.py             # API-based SERP fetching
│   │   └── serp_scraper.py         # Fallback scraping
│   ├── intent/
│   │   └── modeler.py              # Intent modeling & bridge recommendation
│   ├── generation/
│   │   └── writer.py               # Content generation
│   ├── qc/
│   │   ├── controller.py           # QC validation
│   │   └── autofix.py              # AutoFixOnce implementation
│   ├── state/
│   │   └── machine.py              # State machine
│   └── utils/
│       ├── llm.py                  # LLM client wrapper
│       └── helpers.py              # Shared utilities
├── config/
│   ├── thresholds.yaml             # QC thresholds
│   ├── policies.yaml               # Trust, LSI, anchor policies
│   └── publisher_voices.yaml       # Publisher voice profiles
├── schemas/
│   └── backlink_job_package.schema.json  # JSON Schema (source of truth)
├── storage/
│   └── output/                     # Generated output per job_id
├── tests/
│   ├── test_schema_validation.py   # Schema validation test
│   └── test_live_validation.py     # E2E light test
├── examples/
│   └── example_job_package.json    # Example output
└── README.md                        # User documentation
```

---

## TEKNISKA KRAV

### Python Dependencies
```
fastapi          # (om API byggs)
uvicorn          # (om API byggs)
requests         # HTTP fetching
httpx            # Async HTTP
beautifulsoup4   # HTML parsing
lxml             # XML/HTML parser
anthropic        # Claude API client
openai           # (om OpenAI används)
jsonschema       # JSON schema validation
pyyaml           # Config files
pydantic         # Data validation
playwright       # (om scraping behövs)
selenium         # (alternativ till playwright)
```

### LLM Integration
- **Primärt**: Claude (Anthropic API) - Sonnet för analyser, Haiku för klassificering
- **Alternativ**: OpenAI GPT-4
- Använd strukturerad output där möjligt (JSON mode)

### SERP Data
- **Rekommenderat**: SERP API (ValueSERP, SerpApi, DataForSEO)
- **Fallback**: Web scraping (playwright/selenium)

---

## ACCEPTANCE CRITERIA

Systemet är klart när:

1. ✅ **Schema validation test passerar**
   - `tests/test_schema_validation.py` validerar example mot schema

2. ✅ **E2E test passerar**
   - Full pipeline körs med mock/real data
   - Genererar alla output-filer
   - Output valideras mot schema

3. ✅ **QC fungerar**
   - Flaggar tydliga brott mot Next-A1
   - Gör max en AutoFixOnce
   - Loggar beslut i QC + execution_log

4. ✅ **Manuella körningar fungerar**
   - 1-2 skarpa men säkra case
   - Rimlig intent-modellering
   - Korrekt bridge_type-val
   - Naturlig länkplacering
   - Relevanta LSI-termer
   - Inga uppenbara policybrott

5. ✅ **CLI fungerar**
   ```bash
   python main.py \
     --publisher example-publisher.com \
     --target https://client.com/product-x \
     --anchor "bästa valet för X" \
     --output ./storage/output/
   ```

6. ✅ **README är komplett**
   - Installation
   - Konfiguration
   - Användning (CLI + Python API)
   - Output-förklaring
   - QC-tolkning

---

## FRAMTIDA UTBYGGNAD (EJ FOKUS NU)

När kärnan fungerar kan följande övervägas:
- REST API med FastAPI
- Web UI för input/output
- Batch-processing
- MCP-integration
- Dashboard för QC-statistik
- A/B-testing av bridge strategies

Men **FÖRST**: Få kärnan att fungera med CLI + Python API.

---

## REFERENSER

- `next-a1-spec.json` - Fullständig specifikation av ramverket
- `NEXT-A1-ENGINE-ADDENDUM.md` - Implementation requirements
- `backlink_engine_ideal_flow.md` - Idealflöde step-by-step
- `api_system_att_möjligen_bygga_in.md` - API design ideas
- `backlink_job_package.schema.json` - JSON Schema (source of truth)

---

**Version:** 1.0
**Datum:** 2025-11-12
**Status:** SPECIFICATION COMPLETE - READY FOR IMPLEMENTATION
