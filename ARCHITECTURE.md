# BacklinkContent Engine – SERP-First Referensarkitektur

## Executive Summary

BacklinkContent Engine är ett SERP-first, intent-first system som automatiskt genererar högkvalitativt backlink-innehåll baserat på endast **tre inputs**:

1. **publisher_domain** – Publiceringssajten
2. **target_url** – Målsidan som länken ska peka till
3. **anchor_text** – Föreslagen ankartext (behandlas som hypotes, ej absolut)

Systemet implementerar Next-A1-ramverket och löser **variabelgiftermålet**: publikationssajt × ankare × målsida × intention.

---

## 1. Systemöversikt

### 1.1 Arkitekturprinciper

1. **SERP-first, inte keyword-first** – All intentanalys baseras på faktiska SERP-data
2. **Målsidan är facit** – Vad länken får representera härleds från målsidans faktiska innehåll
3. **Publisher är filter** – Vad som är rimligt att säga och hur bestäms av publikationssajtens profil
4. **Anchor är hypotes** – Ankartexten är en utgångspunkt, aldrig absolut sanning
5. **Modulär design** – Varje komponent har tydliga in/out-kontrakt i JSON
6. **Agent-vänlig** – Systemet kan drivas av LLM-agenter eller klassisk orkestrering
7. **Spårbarhet** – Alla beslut loggas och motiveras i Next-A1 extensions

### 1.2 Huvudflöde

```
┌─────────────────┐
│  Input Minimal  │  (publisher_domain, target_url, anchor_text)
└────────┬────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│              PROFILERINGSFAS                            │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────┐  ┌──────────────────────┐      │
│ │TargetScraper        │  │PublisherScraper      │      │
│ │& Profiler           │  │& Profiler            │      │
│ └──────────┬──────────┘  └──────────┬───────────┘      │
│            │                        │                   │
│            v                        v                   │
│     target_profile          publisher_profile           │
└─────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│           ANCHOR & QUERY SELECTION                      │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────┐      ┌──────────────────┐          │
│ │AnchorClassifier │      │QuerySelector     │          │
│ └────────┬────────┘      └──────┬───────────┘          │
│          │                      │                       │
│          v                      v                       │
│   anchor_profile      (main_query + cluster_queries)    │
└─────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│              SERP RESEARCH (Kritisk Fas)                │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────┐                                         │
│ │SerpFetcher  │  → Hämtar SERP för main + 2+ cluster    │
│ └──────┬──────┘                                         │
│        │                                                 │
│        v                                                 │
│ ┌─────────────┐                                         │
│ │SerpAnalyzer │  → Analyserar top-10 resultat:          │
│ └──────┬──────┘    - intent, sidtyper, entiteter        │
│        │            - subtopics, why_it_ranks            │
│        v                                                 │
│ serp_research_extension                                 │
└─────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│         INTENT MODELING & PACKAGE ASSEMBLY              │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────┐                               │
│ │IntentAndCluster       │  → Löser variabelgiftermålet  │
│ │Modeler                │    baserat på:                │
│ └──────────┬────────────┘    - target_profile           │
│            │                 - serp_research             │
│            │                 - publisher_profile         │
│            v                 - anchor_profile            │
│     intent_extension                                    │
│            │                                             │
│            v                                             │
│ ┌───────────────────────┐                               │
│ │BacklinkJobAssembler   │  → Bygger komplett package    │
│ └──────────┬────────────┘                               │
│            v                                             │
│  BacklinkJobPackage (JSON)                              │
└─────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│           WRITER ENGINE (LLM-Driven)                    │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────┐                               │
│ │WriterEngineInterface  │  → Kallar LLM med:            │
│ │                       │    - Systemprompt             │
│ └──────────┬────────────┘    - BacklinkJobPackage       │
│            │                                             │
│            v                                             │
│  ┌─────────────────────────────────────────┐            │
│  │ Output:                                 │            │
│  │ - Analysis (varför detta fungerar)      │            │
│  │ - Strategy (bridge_type, trust, LSI)    │            │
│  │ - Content Brief (struktur, sektioner)   │            │
│  │ - Full Text (≥900 ord, backlink-ready)  │            │
│  │ - Next-A1 Extensions (JSON)             │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
         │
         v
┌─────────────────────────────────────────────────────────┐
│              QC & LOGGING                               │
├─────────────────────────────────────────────────────────┤
│ ┌───────────────────────┐                               │
│ │QcAndLogging           │  → Validerar:                 │
│ │                       │    - intent_alignment         │
│ └──────────┬────────────┘    - anchor_risk              │
│            │                 - LSI-kvalitet             │
│            │                 - bridge_type match        │
│            v                 - compliance               │
│  ┌──────────────────┐                                   │
│  │ QC Report        │                                   │
│  │ - Status         │                                   │
│  │ - Flags          │                                   │
│  │ - Rekommendation │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
         │
         v
  ┌────────────────┐
  │ Final Output   │
  │ - HTML/Text    │
  │ - JSON         │
  │ - QC Report    │
  └────────────────┘
```

---

## 2. Modulspecifikationer

### 2.1 TargetScraperAndProfiler

**Syfte**: Hämta och profilera målsidan för att förstå vad länken får representera.

**Input**:
```json
{
  "target_url": "https://client.com/product-x"
}
```

**Output**: `target_profile` (enligt `backlink_job_package.schema.json`)

**Logik**:
1. Fetch HTML från target_url (timeout 10s, follow redirects max 3)
2. Extrahera strukturerade element:
   - title, meta_description, h1
   - h2/h3-sample (första 5-7)
   - main_content_excerpt (600-1000 tecken, filtrerad från nav/footer)
3. Språkdetektering (svenska prioriteras)
4. Entitetsextraktion:
   - Använd NER eller LLM för att identifiera core_entities (3-6 st)
   - Extrahera core_topics från innehåll och rubriker
5. Härled core_offer: "Vad hjälper sidan användaren med?"
6. Generera candidate_main_queries (2-4 st) baserat på titel, h1 och core_entities

**Dependencies**: requests, beautifulsoup4, langdetect

**Caching**: Cache target_profile per URL i 24h (Redis/filesystem)

---

### 2.2 PublisherScraperAndProfiler

**Syfte**: Profilera publiceringssajten för att förstå ton, röst och tillåten kommersialitet.

**Input**:
```json
{
  "publisher_domain": "example-publisher.com"
}
```

**Output**: `publisher_profile` (enligt schema)

**Logik**:
1. Fetch homepage och /om-oss (eller /about)
2. Sample 3-5 artiklar från olika sektioner (blogg, nyheter, guider)
3. Extrahera:
   - about_excerpt från om-oss-sidan
   - topic_focus: identifiera återkommande teman i artikeltitlar/h1
   - audience: inferera från ton och ämnen (t.ex. "konsumenter", "B2B-proffs")
4. Klassificera tone_class:
   - academic: källhänvisningar, formell struktur
   - authority_public: myndighetsnära, klarspråk
   - consumer_magazine: nytta först, lättillgänglig
   - hobby_blog: personlig, berättande
5. Bedöm allowed_commerciality:
   - low: primärt info/utbildning
   - medium: accepterar produktrekommendationer med disclaimer
   - high: e-handel, affiliate
6. brand_safety_notes: flagga restriktioner (t.ex. inga casinon, tveksamma lån)

**Dependencies**: requests, beautifulsoup4, langdetect, LLM (för klassificering)

**Caching**: Cache publisher_profile per domain i 7 dagar

---

### 2.3 AnchorClassifier

**Syfte**: Tolka föreslagen ankartext och klassificera typ + implicit intent.

**Input**:
```json
{
  "anchor_text": "bästa valet för [tema]",
  "type_hint": null
}
```

**Output**: `anchor_profile`

**Logik**:
1. Om type_hint finns: använd den som utgångspunkt
2. Annars, klassificera via LLM:
   - exact: exakt match mot huvudquery
   - partial: delvis match eller bredare
   - brand: varumärkesnamn
   - generic: "klicka här", "läs mer"
3. Inferera llm_intent_hint:
   - Analysera språket: köp-signaler → transactional
   - Jämförelse/forskning → commercial_research
   - Hur-frågor → info_primary
4. Returnera anchor_profile

**Dependencies**: LLM (för klassificering)

**Caching**: Nej (snabb operation)

---

### 2.4 QuerySelector

**Syfte**: Välja huvudquery + 2-4 klusterqueries baserat på target_profile och anchor_profile.

**Input**:
```json
{
  "target_profile": { ... },
  "anchor_profile": { ... }
}
```

**Output**:
```json
{
  "main_query": "huvudquery",
  "cluster_queries": ["kluster1", "kluster2"],
  "queries_rationale": "Kort motivering"
}
```

**Logik**:
1. Välj main_query:
   - Primärt från target_profile.candidate_main_queries
   - Om anchor är exact/partial: överväg ankartext som query
   - Om osäkerhet: välj den query som bäst representerar core_offer
2. Generera cluster_queries:
   - Kluster 1: Bredare kontext (t.ex. kategori-query)
   - Kluster 2: Djupare detalj (t.ex. villkor, risker, jämförelse)
   - Kluster 3 (valfritt): Relaterad supportquery
3. Motivera valen i queries_rationale

**Dependencies**: LLM (för query generation)

**Caching**: Nej (baserat på unik kombination)

---

### 2.5 SerpFetcher

**Syfte**: Hämta SERP-resultat för varje query via API.

**Input**:
```json
{
  "queries": ["query1", "query2", "query3"],
  "market": "se",
  "language": "sv",
  "top_n": 10
}
```

**Output**:
```json
{
  "results": [
    {
      "query": "query1",
      "serp_items": [
        {
          "rank": 1,
          "url": "https://...",
          "title": "...",
          "snippet": "...",
          "meta": { ... }
        }
      ]
    }
  ]
}
```

**Logik**:
1. Anropa SERP API (t.ex. Google Custom Search, Bing API, ValueSERP, SerpAPI)
2. Extrahera top-N resultat (default: 10)
3. För varje resultat:
   - rank, url, title, snippet
   - meta-info (datum, domain authority om tillgängligt)
4. Returnera strukturerad data

**Dependencies**: SERP API-klient, requests

**Caching**: Cache SERP-resultat per query i 6-12h (SERP kan förändras, men inte varje minut)

**Error Handling**:
- Vid API-fel: logga, returnera tom serp_items med confidence: "low"
- Vid rate limiting: retry med exponential backoff

---

### 2.6 SerpAnalyzer

**Syfte**: Djupanalys av SERP-resultat för att extrahera intent, sidtyper, entiteter och subtopics.

**Input**: Output från SerpFetcher + (optionellt) fetch av faktiska sidinnehåll

**Output**: `serp_research_extension` (enligt schema)

**Logik**:
1. För varje query:
   a. **Intent-klassificering**:
      - Analysera snippets, titles och URL-mönster
      - Dominant intent: info_primary | commercial_research | transactional | etc.
      - Secondary intents

   b. **Page archetypes**:
      - Identifiera vanliga sidtyper i top-10:
        - guide, comparison, category, product, review, tool, faq, news, official

   c. **Top results sample** (för 3-5 toppresultat):
      - Fetch faktisk HTML (optional, men rekommenderat)
      - Extrahera:
        - detected_page_type
        - content_excerpt (200-300 tecken)
        - key_entities (3-5 st från sidans innehåll)
        - key_subtopics (2-4 st)
        - why_it_ranks: LLM-genererad 1-3 meningsförklaring

   d. **Required subtopics**:
      - Identifiera subtopics som förekommer i ≥60% av top-10
      - Dessa är "obligatoriska" för att vara relevant i detta SERP

2. Sammanställ serp_sets per query

3. Bedöm data_confidence:
   - high: Alla queries lyckades, minst 8/10 resultat per query
   - medium: Någon query misslyckades delvis
   - low: Flera misslyckanden

**Dependencies**: SerpFetcher output, requests, beautifulsoup4, LLM (för analys)

**Caching**: Piggyback på SerpFetcher cache

**Note**: Detta är den mest compute-intensiva modulen. För produktion: överväg parallell fetch av top-results.

---

### 2.7 IntentAndClusterModeler

**Syfte**: Modellera intentprofilen genom att lösa variabelgiftermålet.

**Input**:
```json
{
  "target_profile": { ... },
  "publisher_profile": { ... },
  "anchor_profile": { ... },
  "serp_research_extension": { ... }
}
```

**Output**: `intent_extension` (enligt schema)

**Logik**:
1. **Extrahera primär SERP-intent**:
   - Ta dominant_intent från main_query i serp_research
   - Om cluster queries har divergerande intents: logga som secondary

2. **Modellera target_page_intent**:
   - Analysera target_profile.core_offer
   - Klassificera: t.ex. "transactional_with_info_support"

3. **Modellera anchor_implied_intent**:
   - Från anchor_profile.llm_intent_hint

4. **Modellera publisher_role_intent**:
   - Från publisher_profile.tone_class och topic_focus
   - T.ex. consumer_magazine → "info_primary med låg-medium kommersialitet"

5. **Beräkna intent_alignment**:
   - anchor_vs_serp: Jämför anchor_implied_intent med serp_intent_primary
     - aligned: samma eller kompatibel
     - partial: relaterad men bredare/smalare
     - off: orelaterad
   - target_vs_serp: Jämför target_page_intent med serp_intent_primary
   - publisher_vs_serp: Jämför publisher_role_intent med serp_intent_primary
   - overall: Om alla är aligned/partial → aligned; annars partial/off

6. **Rekommendera bridge_type**:
   - strong: Om overall = aligned och anchor_vs_serp = aligned
   - pivot: Om overall = aligned eller partial, men behöver semantisk brygga
   - wrapper: Om overall = off eller flera komponenter är off

7. **Härled required_subtopics**:
   - Sammanfoga required_subtopics från alla serp_sets
   - Dedupliera och prioritera (de som förekommer i flera queries)

8. **Definiera forbidden_angles**:
   - Baserat på publisher_profile.brand_safety_notes
   - Om publisher_role_intent är info_primary: förbjud aggressiv CTA
   - Om target och SERP har hög diskrepans: förbjud överdrivna claims

9. **Motivera i notes.rationale**

**Dependencies**: LLM (för alignment-bedömning och rationale)

**Caching**: Nej (baserat på unika kombinationer)

---

### 2.8 BacklinkJobAssembler

**Syfte**: Sammanställa alla komponenter till ett komplett BacklinkJobPackage.

**Input**:
```json
{
  "input_minimal": { ... },
  "target_profile": { ... },
  "publisher_profile": { ... },
  "anchor_profile": { ... },
  "serp_research_extension": { ... },
  "intent_extension": { ... }
}
```

**Output**: `BacklinkJobPackage` (enligt `backlink_job_package.schema.json`)

**Logik**:
1. Generera job_meta:
   - job_id: UUID
   - created_at: ISO 8601 timestamp
   - spec_version: "Next-A1-SERP-First-v1"

2. Sätt generation_constraints:
   - language: från target_profile.detected_language eller publisher_profile.detected_language
   - min_word_count: 900 (eller konfigurerbart)
   - max_anchor_usages: 2
   - anchor_policy: "Ingen anchor i H1/H2, placera i första relevanta stycke i mittsektionen"
   - tone_override: null (använd publisher_profile.tone_class)

3. Validera:
   - Alla required fields finns
   - intent_extension.overall inte är null
   - serp_research_extension.data_confidence är satt

4. Returnera komplett BacklinkJobPackage som JSON

**Dependencies**: uuid, datetime

**Caching**: Nej (final assembly)

---

### 2.9 WriterEngineInterface

**Syfte**: Anropa LLM Writer Engine med BacklinkJobPackage och systemprompt.

**Input**: `BacklinkJobPackage`

**Output**:
```json
{
  "analysis": "Textanalys av variabelgiftermålet...",
  "strategy": "Vald bridge_type, trust-källor, LSI-plan...",
  "content_brief": "Strukturerad brief med sektioner...",
  "full_text_html": "<article>...</article>",
  "full_text_markdown": "# Title\n\n...",
  "backlink_article_output_v2": {
    "links_extension": { ... },
    "intent_extension": { ... },
    "qc_extension": { ... },
    "serp_research_extension": { ... }
  }
}
```

**Logik**:
1. Ladda Writer Engine systemprompt (se `writer_engine_prompt.md`)
2. Konstruera LLM-request:
   - System: Writer Engine systemprompt
   - User: BacklinkJobPackage (JSON)
3. Anropa LLM (t.ex. Claude Sonnet 4.5, GPT-4, etc.)
4. Parsera output:
   - Extrahera sections: analysis, strategy, brief, full_text
   - Extrahera JSON-block för backlink_article_output_v2
5. Validera:
   - full_text har minst generation_constraints.min_word_count ord
   - Ankare är placerad enligt anchor_policy
   - links_extension, intent_extension, qc_extension finns

**Dependencies**: LLM API-klient (Anthropic, OpenAI, etc.)

**Caching**: Nej (varje körning är unik)

**Error Handling**:
- Vid LLM-fel: retry upp till 3 gånger med exponential backoff
- Vid parsing-fel: logga, returnera partial output med flag

---

### 2.10 QcAndLogging

**Syfte**: Validera output från Writer Engine och flagga risker.

**Input**:
```json
{
  "backlink_job_package": { ... },
  "writer_output": { ... }
}
```

**Output**:
```json
{
  "qc_status": "pass | warning | fail",
  "flags": [
    {
      "severity": "error | warning | info",
      "category": "intent_mismatch | anchor_risk | lsi_missing | trust_missing | compliance",
      "message": "Beskrivning av problemet"
    }
  ],
  "scores": {
    "intent_alignment_score": 0.85,
    "anchor_risk_score": "low",
    "lsi_quality_score": 0.90,
    "trust_quality_score": 0.80
  },
  "recommendations": [
    "Överväg att lägga till fler trustkällor i Resources-sektionen"
  ]
}
```

**Logik**:
1. **Intent-validering**:
   - Jämför intent_extension.recommended_bridge_type med links_extension.bridge_type
   - Om mismatch: flagga som error
   - Om intent_extension.overall = "off": flagga som error

2. **Anchor-riskvärdering**:
   - Kontrollera qc_extension.anchor_risk
   - Om "high": flagga som warning
   - Verifiera att ankare inte är i H1/H2 (parsing av full_text)

3. **LSI-kvalitet**:
   - Räkna LSI-termer i närfönster kring ankaret
   - Om < 6: flagga som warning
   - Om > 10 och många är repetitioner: flagga som info

4. **Trust-kvalitet**:
   - Kontrollera att minst 1 trust-källa används
   - Verifiera att trust_policy.level matchar publisher_profile
   - Om fallback_used: flagga som info
   - Om unresolved har element: flagga som warning

5. **Compliance**:
   - Om target_profile eller publisher_profile kräver disclaimers:
     - Verifiera att compliance.disclaimers_injected innehåller relevanta
   - Om saknas: flagga som error

6. **Ordräkning**:
   - Räkna ord i full_text
   - Om < generation_constraints.min_word_count: flagga som error

7. **Sätt qc_status**:
   - fail: Om någon error-flag finns
   - warning: Om endast warning/info-flags finns
   - pass: Om inga flags eller endast info

**Dependencies**: BeautifulSoup (för HTML-parsing), LLM (optional, för djupare analys)

**Caching**: Nej

---

## 3. Data Flow & JSON Contracts

### 3.1 Central Payload: BacklinkJobPackage

Se `backlink_job_package.schema.json` för fullständigt schema.

**Nyckelprinciper**:
- Detta är den **enda payload** som Writer Engine behöver
- Alla upstream-moduler bidrar till att bygga detta paket
- Paketet är **självdokumenterande**: allt som behövs för att förstå kontexten finns med

### 3.2 Writer Output: BacklinkArticleOutputV2

Inkluderar:
- **Läsbar output**: analysis, strategy, brief, full_text
- **Strukturerad JSON**: backlink_article_output_v2 med extensions enligt Next-A1

---

## 4. Orkestrering

### 4.1 Sekvensiell Orkestrering (Enklast)

```python
# main_orchestrator.py
from modules import (
    TargetScraperAndProfiler,
    PublisherScraperAndProfiler,
    AnchorClassifier,
    QuerySelector,
    SerpFetcher,
    SerpAnalyzer,
    IntentAndClusterModeler,
    BacklinkJobAssembler,
    WriterEngineInterface,
    QcAndLogging
)

def generate_backlink_content(publisher_domain, target_url, anchor_text):
    # 1. Profilering (parallellt)
    target_profile = TargetScraperAndProfiler().run(target_url)
    publisher_profile = PublisherScraperAndProfiler().run(publisher_domain)

    # 2. Anchor & Query
    anchor_profile = AnchorClassifier().run(anchor_text)
    query_selection = QuerySelector().run(target_profile, anchor_profile)

    # 3. SERP Research
    serp_raw = SerpFetcher().run(query_selection['queries'])
    serp_research_extension = SerpAnalyzer().run(serp_raw, query_selection)

    # 4. Intent Modeling
    intent_extension = IntentAndClusterModeler().run(
        target_profile, publisher_profile, anchor_profile, serp_research_extension
    )

    # 5. Assemble Package
    job_package = BacklinkJobAssembler().run(
        input_minimal={'publisher_domain': publisher_domain, 'target_url': target_url, 'anchor_text': anchor_text},
        target_profile=target_profile,
        publisher_profile=publisher_profile,
        anchor_profile=anchor_profile,
        serp_research_extension=serp_research_extension,
        intent_extension=intent_extension
    )

    # 6. Writer Engine
    writer_output = WriterEngineInterface().run(job_package)

    # 7. QC
    qc_report = QcAndLogging().run(job_package, writer_output)

    return {
        'job_package': job_package,
        'content': writer_output,
        'qc_report': qc_report
    }
```

### 4.2 Agent-Baserad Orkestrering (MCP-liknande)

I en agent-miljö:
- Varje modul exponeras som ett **tool/command**
- En Architect-agent anropar modulerna i rätt ordning
- Writer-agenten tar emot BacklinkJobPackage och levererar output
- QC-agenten validerar

**Exempel (pseudo-MCP)**:
```json
{
  "tools": [
    {"name": "profile_target", "module": "TargetScraperAndProfiler"},
    {"name": "profile_publisher", "module": "PublisherScraperAndProfiler"},
    {"name": "classify_anchor", "module": "AnchorClassifier"},
    {"name": "select_queries", "module": "QuerySelector"},
    {"name": "fetch_serp", "module": "SerpFetcher"},
    {"name": "analyze_serp", "module": "SerpAnalyzer"},
    {"name": "model_intent", "module": "IntentAndClusterModeler"},
    {"name": "assemble_job_package", "module": "BacklinkJobAssembler"},
    {"name": "generate_content", "module": "WriterEngineInterface"},
    {"name": "run_qc", "module": "QcAndLogging"}
  ]
}
```

Architect-agent får uppdraget:
```
Input: publisher_domain="X", target_url="Y", anchor_text="Z"
Task: Generate backlink content using SERP-first methodology.
```

Agenten:
1. Anropar `profile_target` och `profile_publisher` parallellt
2. Anropar `classify_anchor`
3. Anropar `select_queries`
4. Anropar `fetch_serp` → `analyze_serp`
5. Anropar `model_intent`
6. Anropar `assemble_job_package`
7. Anropar `generate_content`
8. Anropar `run_qc`
9. Returnerar final output

---

## 5. Skalbarhet & Vidareutveckling

### 5.1 Utökade SERP-källor

**Nuvarande**: Google via API

**Framtida**:
- Bing SERP
- Baidu (för kinesiska marknader)
- Yandex (för ryska marknader)
- Niche search engines (t.ex. DuckDuckGo, Ecosia)

**Implementering**:
- SerpFetcher: pluggbar arkitektur med provider-adapter
- Varje provider implementerar samma interface
- Konfiguration: välj primary + fallback providers

### 5.2 Pre-Scraping & Crawling

**Problem**: Scraping i realtid kan vara långsamt.

**Lösning**:
- **Publisher Library**: Pre-crawla och cache publishers (uppdatera varje vecka)
- **Target Library**: Om samma klient har många targets, pre-scrapa alla
- **SERP Cache**: Aggressive caching med smart invalidation (baserat på query volatility)

**Implementering**:
- Background worker (Celery, RQ) som kontinuerligt uppdaterar cache
- Redis/Memcached för snabb access
- PostgreSQL/MongoDB för långtidslagring

### 5.3 Multi-Language & Multi-Market

**Nuvarande**: Fokus på svenska (SE)

**Framtida**:
- Support för EN, NO, DK, FI, DE, etc.
- Market-specifika SERP-källor
- Tone_class-anpassning per kultur

**Implementering**:
- Language detection i alla moduler
- Market-parameter i SerpFetcher
- Lokaliserade systemprompts för Writer Engine

### 5.4 Feedback Loop & Learning

**Problem**: Hur vet vi vad som fungerar?

**Lösning**:
- Logga alla jobb med metadata
- Spåra metrics (om möjligt):
  - Indexering
  - Rankningar
  - CTR
  - Bounce rate
- Feedback från content-team: thumbs up/down
- Periodisk analys av vad som korrelerar med framgång

**Implementering**:
- Logging-modul som sparar job_package + output + metrics
- Analytics dashboard
- Optional: Fine-tune LLM Writer Engine på framgångsrika exempel

### 5.5 A/B Testing av Bridge Types

**Experiment**:
- För samma input: generera 2-3 varianter (strong, pivot, wrapper)
- Låt content-team välja
- Spåra vilka som presterar bäst i vilka scenarion

**Implementering**:
- WriterEngineInterface får parameter `bridge_type_override`
- Generera flera jobb parallellt
- UI för val

---

## 6. Teknisk Stack (Rekommenderad)

### 6.1 Backend
- **Språk**: Python 3.11+
- **Framework**: FastAPI (för API) eller Click (för CLI)
- **Scraping**: requests, httpx, beautifulsoup4, playwright (för JS-tunga sidor)
- **SERP API**: SerpAPI, ValueSERP, Google Custom Search
- **LLM**: Anthropic Claude (via Anthropic SDK), OpenAI GPT-4 (via OpenAI SDK)
- **Caching**: Redis (för temporär data), PostgreSQL (för persistent data)
- **Task Queue**: Celery + Redis (för async jobs)
- **Logging**: structlog, Sentry (för error tracking)

### 6.2 Data
- **Schemas**: JSON Schema (validation), Pydantic (models)
- **Storage**: PostgreSQL (relational), MongoDB (document store, optional)

### 6.3 Deployment
- **Containerization**: Docker + Docker Compose
- **Orchestration**: Kubernetes (för större scale) eller enkel VPS (för start)
- **CI/CD**: GitHub Actions, GitLab CI

### 6.4 Observability
- **Monitoring**: Prometheus + Grafana
- **Logging**: Elasticsearch + Kibana (ELK stack) eller Loki
- **Tracing**: OpenTelemetry (optional, för distributed tracing)

---

## 7. Exempel: End-to-End Körning

### Input
```json
{
  "publisher_domain": "exempelguiden.se",
  "target_url": "https://klarna.com/se/kundtjanst/",
  "anchor_text": "bästa sättet att hantera dina betalningar"
}
```

### Flow
1. **Target Profiling**:
   - Scrapa klarna.com/se/kundtjanst
   - Extrahera: "Klarnas kundtjänst – få hjälp med dina betalningar"
   - core_entities: ["Klarna", "betalningar", "kundtjänst"]
   - core_offer: "Kundtjänst för Klarnas betaltjänster"

2. **Publisher Profiling**:
   - Scrapa exempelguiden.se
   - tone_class: "consumer_magazine"
   - topic_focus: ["privatekonomi", "smarta köp"]
   - allowed_commerciality: "medium"

3. **Anchor Classification**:
   - llm_classified_type: "partial"
   - llm_intent_hint: "commercial_research"

4. **Query Selection**:
   - main_query: "hantera betalningar online"
   - cluster_queries: ["klarna betalning hur funkar det", "kundtjänst betalningar"]

5. **SERP Research**:
   - Hämta SERP för alla 3 queries
   - Analysera top-10:
     - Dominant intent: commercial_research + info_primary
     - Page types: guide, faq, product, review
     - Required subtopics: "säkerhet", "hur det fungerar", "kostnader", "kontakt"

6. **Intent Modeling**:
   - serp_intent_primary: "commercial_research"
   - target_page_intent: "support"
   - publisher_role_intent: "info_primary"
   - intent_alignment.overall: "partial" (support ≠ research, men related)
   - recommended_bridge_type: "pivot"

7. **Job Assembly**:
   - BacklinkJobPackage skapas med alla komponenter

8. **Writer Engine**:
   - Tar emot package
   - Genererar:
     - Vinkel: "Guide till smidiga betalningslösningar – med Klarna som exempel"
     - Bridge: Pivot via "hur man hanterar betalningar online"
     - Struktur: Intro → Vad är smidiga betalningar → Hur Klarna fungerar (med länk) → Andra alternativ → Resurser
     - Full text: 950 ord
     - LSI-termer: "säkerhet", "kryptering", "köpskydd", "avbetalning", "kundtjänst", "transparens"
     - Trust: 2 källor (Konsumentverket, Wikipedia om betalningslösningar)

9. **QC**:
   - intent_alignment: OK (pivot-lösning är valid)
   - anchor_risk: low (partial-ankare i naturlig kontext)
   - lsi_quality: 8 termer i närfönster ✓
   - trust_quality: 2 T1-källor ✓
   - compliance: Ingen disclaimer krävs ✓
   - word_count: 950 ✓
   - qc_status: **pass**

### Output
- **Content**: Publicerbar artikel (HTML + Markdown)
- **JSON**: Komplett backlink_article_output_v2 med extensions
- **QC Report**: pass, inga flags

---

## 8. Sammanfattning

BacklinkContent Engine löser det ambitiösa målet att automatisera högkvalitativ backlink-innehållsproduktion genom:

1. **SERP-First Approach**: Basera allt på faktiska SERP-signaler, inte gissningar
2. **Variabelgiftermålet**: Systematiskt lösa publisher × anchor × target × intent
3. **Modulär Arkitektur**: Varje komponent har tydliga kontrakt, kan testas och ersättas
4. **Next-A1 Compliance**: Alla outputs följer rigorösa kvalitetsstandarder
5. **Skalbarhet**: Designad för att växa från MVP till produktionsskala

**Nästa Steg**:
1. Implementera core modules i Python
2. Skapa Writer Engine systemprompt
3. Bygga CLI/API för input
4. Testa med riktiga exempel
5. Iterera baserat på feedback

**För Ditt Content-Team**:
- Input: 3 fält (publisher, target, anchor)
- Output: Publicerbar artikel + QC-rapport
- Tid: Från manuell research (4-8h) → automatisk (5-10 min)
- Kvalitet: Systematisk, spårbar, reproducerbar
