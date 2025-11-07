# BacklinkContent Engine

**SERP-First, Intent-First Backlink Content Generation System**

---

## 📋 Översikt

BacklinkContent Engine är ett automatiserat system för att generera högkvalitativt SEO-innehåll för backlink-placeringar. Systemet baseras på **Next-A1-ramverket** och löser **variabelgiftermålet**:

**Publisher × Anchor × Target × Intent**

### Unika Egenskaper

- **SERP-First Approach**: All intentanalys baseras på faktiska SERP-data, inte gissningar
- **Minimal Input**: Endast 3 fält krävs (publisher, target, anchor)
- **Systematisk Kvalitet**: Alla beslut dokumenteras och motiveras
- **Modulär Arkitektur**: Varje komponent kan testas, ersättas eller utökas
- **Next-A1 Compliance**: Rigorösa kvalitetsstandarder med spårbarhet

---

## 🚀 Snabbstart

### Installation

```bash
# Klona repository
git clone <repo-url>
cd BACOWR

# Installera dependencies
pip install -r requirements.txt
```

### Grundläggande Användning

```bash
python main.py \
  --publisher "privatekonomi.se" \
  --target "https://klarna.com/se/kundtjanst/" \
  --anchor "smidig betalningshantering" \
  --output output/
```

### Output

Systemet genererar:
- **BacklinkJobPackage** (JSON): Komplett datapaketet
- **HTML-content**: Publicerbar artikel
- **Markdown-content**: Samma artikel i Markdown
- **QC Report**: Kvalitetsgranskning med flags och scores

---

## 📁 Projektstruktur

```
BACOWR/
├── modules/                    # Kärnmoduler
│   ├── base.py                 # Basklass
│   ├── target_scraper_profiler.py
│   ├── publisher_scraper_profiler.py
│   ├── anchor_classifier.py
│   ├── query_selector.py
│   ├── serp_fetcher.py
│   ├── serp_analyzer.py
│   ├── intent_modeler.py
│   ├── job_assembler.py
│   ├── writer_engine.py
│   └── qc_logging.py
├── config/                     # Konfiguration
│   └── default.json
├── examples/                   # Exempeldata
│   └── example_input.json
├── output/                     # Genererad output (skapas automatiskt)
├── main.py                     # Huvudorkestrering
├── requirements.txt            # Python dependencies
├── ARCHITECTURE.md             # Detaljerad systemarkitektur
├── WRITER_ENGINE_PROMPT.md     # Writer Engine systemprompt
├── backlink_job_package.schema.json
├── serp_research_extension.schema.json
├── next-a1-spec.json
└── README.md
```

---

## 🔧 Konfiguration

Redigera `config/default.json`:

```json
{
  "timeout": 10,
  "user_agent": "BacklinkBot/1.0",
  "min_word_count": 900,
  "max_anchor_usages": 2,
  "rate_limit_delay": 0.5,
  "serp_api_provider": "serpapi",
  "serp_api_key": "YOUR_API_KEY",
  "llm_provider": "anthropic",
  "llm_api_key": "YOUR_ANTHROPIC_KEY",
  "llm_model": "claude-sonnet-4.5"
}
```

### Viktiga Inställningar

- **serp_api_provider**: `serpapi`, `google`, `bing`, eller `mock` (för testning)
- **llm_provider**: `anthropic`, `openai`, eller `mock`
- **min_word_count**: Minimum antal ord för genererat innehåll
- **rate_limit_delay**: Fördröjning mellan SERP-förfrågningar (sekunder)

---

## 🏗️ Systemarkitektur

Se [ARCHITECTURE.md](ARCHITECTURE.md) för detaljerad beskrivning.

### Översikt

1. **Input**: publisher_domain, target_url, anchor_text
2. **Profilering**: Scrape och analysera target + publisher
3. **Anchor & Query**: Klassificera anchor, välj queries
4. **SERP Research**: Hämta och analysera SERP (huvud + kluster)
5. **Intent Modeling**: Lös variabelgiftermålet
6. **Job Assembly**: Bygg BacklinkJobPackage
7. **Writer Engine**: Generera innehåll (LLM-driven)
8. **QC**: Validera kvalitet och flagga risker
9. **Output**: Publicerbar artikel + JSON-extensions

---

## 📊 Moduler

### 1. TargetScraperAndProfiler
Scraper målsidan och extraherar:
- Strukturerade element (title, h1, headings)
- Entiteter och topics
- Kandidat-queries

### 2. PublisherScraperAndProfiler
Profilerar publiceringssajten:
- Ton och röst (academic, consumer_magazine, etc.)
- Tillåten kommersialitet
- Brand safety-restriktioner

### 3. AnchorClassifier
Klassificerar ankartext:
- Typ: exact, partial, brand, generic
- Implicit intent: info_primary, commercial_research, etc.

### 4. QuerySelector
Väljer main query + 2-4 klusterqueries baserat på:
- Target entities
- Anchor type
- Intent hints

### 5. SerpFetcher
Hämtar SERP via API (Google, Bing, SerpAPI, etc.)

### 6. SerpAnalyzer
Djupanalyserar SERP:
- Intent-klassificering
- Page archetypes (guide, comparison, product, etc.)
- Required subtopics (vad top-10 täcker)
- Entity extraction från top-results

### 7. IntentAndClusterModeler
Modellerar intentprofil:
- Beräknar intent_alignment (anchor vs SERP, target vs SERP, etc.)
- Rekommenderar bridge_type (strong, pivot, wrapper)
- Definierar required_subtopics och forbidden_angles

### 8. BacklinkJobAssembler
Sammanställer komplett BacklinkJobPackage med alla komponenter.

### 9. WriterEngineInterface
Anropar LLM med:
- Writer Engine systemprompt
- BacklinkJobPackage

Genererar:
- Analysis, Strategy, Content Brief
- Full Text (HTML + Markdown)
- Next-A1 Extensions (JSON)

### 10. QcAndLogging
Validerar output:
- Intent alignment
- Anchor risk
- LSI-kvalitet
- Trust-källor
- Compliance
- Ordräkning

Returnerar QC-rapport med status och flags.

---

## 🎯 Bridge Types (Next-A1-2)

### Strong Bridge
- **När**: Anchor ≈ Target, Publisher nisch överlappar ≥70%
- **Metod**: Direktkoppling tidigt i texten
- **Exempel**: Om publisher är privatekonomi, target är Klarna betalningar, anchor är "smidiga betalningar" → artikel om "Smidiga betalningar" med Klarna som naturligt exempel.

### Pivot Bridge
- **När**: Anchor är bredare/angränsande, overlap 40-70%
- **Metod**: Etablera övergripande problemformulering, använd pivot-tema
- **Exempel**: Publisher är teknikblogg, target är e-handelscheckout, anchor är "optimera e-handel" → artikel om "5 sätt att optimera e-handel" där checkout är ett sätt.

### Wrapper Bridge
- **När**: Overlap <40%, generisk/omaka koppling
- **Metod**: Bygg neutral metaram (metodik, risk, etik, innovation)
- **Exempel**: Publisher är hälsoblogg, target är projektverktyg, anchor är "effektiv projektledning" → artikel om "Projektledning och teamhälsa" där verktyget nämns som ett verktyg.

---

## 🔍 SERP-First Methodology

### Principer

1. **SERP är facit**: Vad användare faktiskt söker efter (ej vad vi tror)
2. **Dominant intent styr**: Om SERP vill ha jämförelse → ge jämförelse
3. **Required subtopics är obligatoriska**: Subtopics som ≥60% av top-10 täcker måste inkluderas
4. **Page archetypes informerar struktur**: Om SERP domineras av guides → använd guide-format

### SERP Analysis

För varje query:
- Hämta top-10 resultat
- Klassificera dominant intent
- Identifiera page archetypes
- Extrahera required subtopics (från faktiskt innehåll i top-results)
- Analysera "why it ranks" för top 3-5

---

## 📝 Writer Engine

Se [WRITER_ENGINE_PROMPT.md](WRITER_ENGINE_PROMPT.md) för komplett systemprompt.

### Output Format

Writer Engine producerar:

1. **Analysis** (100-200 ord): Varför detta variabelgifte fungerar
2. **Strategy** (150-250 ord): Bridge type, trust-källor, LSI-plan, struktur
3. **Content Brief**: Strukturerad brief med sektioner
4. **Full Text HTML**: Publicerbar artikel (≥900 ord)
5. **Full Text Markdown**: Samma artikel i Markdown
6. **backlink_article_output_v2**: JSON med Next-A1 extensions
   - links_extension
   - intent_extension
   - qc_extension
   - serp_research_extension

---

## 🛡️ Quality Control (QC)

### QC Scores

- **intent_alignment_score**: 0.0-1.0
- **anchor_risk_score**: low | medium | high
- **lsi_quality_score**: 0.0-1.0
- **trust_quality_score**: 0.0-1.0

### QC Flags

Severity:
- **error**: Blocker, måste åtgärdas
- **warning**: Bör åtgärdas
- **info**: FYI

Categories:
- **intent_mismatch**: Bridge type ≠ recommended, eller overall alignment = off
- **anchor_risk**: Anchor i H1/H2, eller high risk
- **lsi_missing**: <6 LSI-termer
- **trust_missing**: Saknade trust-källor
- **compliance**: Saknade disclaimers
- **wordcount**: Under min_word_count

### QC Status

- **pass**: Inga errors, inga warnings (eller endast info)
- **warning**: Warnings men inga errors
- **fail**: Minst en error

---

## 🚀 Production Deployment

### Mock → Real APIs

**Current**: Systemet använder MOCK-data för SERP och LLM.

**For Production**:

1. **SERP API**: Integrera med SerpAPI, Google Custom Search, eller Bing
   - Uppdatera `modules/serp_fetcher.py`
   - Sätt `serp_api_key` i config

2. **LLM API**: Integrera med Anthropic Claude eller OpenAI
   - Uppdatera `modules/writer_engine.py`
   - Sätt `llm_api_key` i config

### Caching

För produktion, implementera caching:
- **Target profiles**: Cache i 24h
- **Publisher profiles**: Cache i 7 dagar
- **SERP results**: Cache i 6-12h

Använd Redis, Memcached, eller filbaserad cache.

### Skalning

- **Background workers**: Använd Celery för async jobs
- **Database**: PostgreSQL eller MongoDB för persistent lagring
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK stack eller Loki

---

## 📚 Next-A1 Spec

Systemet följer **Next-A1-specifikationen** (se `next-a1-spec.json`):

- **Punkt 0**: Variabelgiftermålet som stomme
- **Punkt 1**: JSON-schema för extensions
- **Punkt 2**: Bridge type & intent-koppling
- **Punkt 3**: Trustkällor (T1-T4 prioritering)
- **Punkt 4**: LSI-kvalitet & närfönster
- **Punkt 5**: Publisher-fit (röstprofiler)
- **Punkt 6**: Ankarrisk & placering
- **Punkt 7**: Autofix-policy
- **Punkt 8**: QC-definitioner & trösklar

---

## 🤝 Bidra

### Development Workflow

1. Fork repository
2. Skapa feature branch
3. Implementera + testa
4. Skicka pull request

### Testing

```bash
# Kör med mock data
python main.py \
  --publisher "example.com" \
  --target "https://example.com/product" \
  --anchor "best solution" \
  --output output/test/

# Inspektera output
cat output/test/*_qc_report.json
```

---

## 📄 Licens

[Ange licens här]

---

## 📧 Kontakt

För frågor eller support, kontakta [ditt team/email].

---

## 🎉 Tack till

- **SEO-teamet** som definierade Next-A1-ramverket
- **Content-teamet** som testade systemet
- **Dev-teamet** som byggde första versionen

---

**BacklinkContent Engine** – *From Three Inputs to Perfect Content*
