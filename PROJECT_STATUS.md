# PROJECT STATUS - BACOWR
## "Save Game" - Projektöversikt & Nuläge

**Datum:** 2025-11-12
**Status:** SPECIFICATION COMPLETE - READY FOR IMPLEMENTATION
**Nästa steg:** Bygg systemet med Claude Code (browser)

---

## VAD ÄR BACOWR?

Ett komplett Python-system för att generera högkvalitativa backlänksartiklar baserat på **endast 3 inputs**:
- **Publisher domain** (publiceringsdomän)
- **Target URL** (målsida som ska länkas)
- **Anchor text** (ankartext för länken)

Systemet **automatiskt**:
1. Analyserar målsidan och publiceringsdomänen
2. Gör SERP-research för att förstå sökintention
3. Modellerar intent och väljer rätt bryggstrategi (strong/pivot/wrapper)
4. Genererar semantiskt korrekt artikel (900+ ord)
5. Validerar output mot kvalitetskriterier (QC)
6. Levererar färdig artikel + metadata i JSON-format

**Kärn-konceptet:** VARIABELGIFTERMÅLET
- Gifta samman: Publisher, Ankare, Målsida, **Intention**
- Intention härledas från SERP-data (ej gissningar!)
- Följer Next-A1 specifikationen exakt

---

## VAD HAR SKAPATS? (Dokumentation)

### ✅ 1. IMPLEMENTATION_SPEC.md
**~1000 rader komplett specifikation**

Innehåller:
- Projektöversikt och variabelgiftermålet
- Systemarkitektur (Input → Processing → Output)
- Detaljerade komponenter:
  - Fetch & Profile (target, publisher, anchor)
  - SERP Research (topp-10 resultat per query)
  - Intent Modeling (alignment, bridge type)
  - Content Generation (900+ ord enligt publisher voice)
  - QC & AutoFix (kvalitetskontroll + en automatisk fix)
- State Machine (RECEIVE → PREFLIGHT → WRITE → QC → DELIVER/ABORT)
- Output-struktur (JSON + Markdown)
- Filstruktur
- Tekniska krav (Python dependencies, LLM integration, SERP APIs)
- Acceptance criteria (när är systemet klart?)

**Användning:** Referensdokument för vad systemet ska göra

---

### ✅ 2. BUILDER_PROMPT.md
**~1200 rader steg-för-steg byggguide för Claude Code**

Innehåller:
- 13 konkreta byggsteg (STEG 0-13)
- Exakt filstruktur att skapa
- Kodskelett för varje komponent med funktionssignaturer
- **Färdiga LLM-prompts** för varje analyssteg
- Testinstruktioner för varje steg
- Checklist för när systemet är klart
- Exempel på testkörning

**Användning:** Systemprompt för Claude Code i browser att bygga från

**Stegen i detalj:**
- STEG 0: Setup & struktur
- STEG 1: Utils & LLM client
- STEG 2: Target profiler
- STEG 3: Publisher profiler
- STEG 4: Anchor profiler
- STEG 5: SERP research
- STEG 6: Intent modeler
- STEG 7: Content generation (writer)
- STEG 8: QC controller
- STEG 9: AutoFix
- STEG 10: State machine
- STEG 11: API & CLI
- STEG 12: Schema & validation tests
- STEG 13: README & documentation

---

### ✅ 3. API_INTEGRATION_GUIDE.md
**~800 rader integration-guide för ChatGPT:s API-förslag**

Innehåller:
- Analys av ChatGPT:s API-förslag (`utkast-till-api-lösning`)
- **Två integration-strategier:**
  - **Strategi A (Hybrid):** FastAPI microservices + Core pipeline
  - **Strategi B (Monolitisk):** Importera moduler direkt i pipeline
- Jämförelse mellan strategierna
- Komplett implementation av `app/main.py` för FastAPI-endpoints
- Refactored profilers som använder ChatGPT:s moduler
- Deployment-instruktioner
- Rekommendation: Börja med Strategi B, bygg A senare om API behövs

**Användning:** Guide för hur man integrerar ChatGPT:s kod med kärnpipelinen

---

## VAD FINNS REDAN I PROJEKTET? (Existerande filer)

### Spec-filer (från tidigare arbete):
- ✅ `next-a1-spec.json` - Fullständig Next-A1 specifikation (Punkt 0-8)
- ✅ `NEXT-A1-ENGINE-ADDENDUM.md` - Implementation requirements
- ✅ `backlink_engine_ideal_flow.md` - Idealflöde steg-för-steg
- ✅ `api_system_att_möjligen_bygga_in.md` - API design ideas

### ChatGPT:s API-förslag:
```
utkast-till-api-lösning/
├── app/
│   ├── models.py              ✅ Pydantic models (TargetProfile, etc.)
│   ├── config.py              ✅ Settings & configuration
│   ├── extract.py             ✅ HTML scraping & metadata extraction
│   ├── serp_providers.py      ✅ SERP fetching (mock, SerpAPI, Google CSE)
│   ├── intent_policy.py       ✅ Intent modeling heuristics
│   ├── policy.py              ✅ Extensions builder
│   ├── utils.py               ✅ Helper functions
│   ├── webhooks.py            ✅ Webhook posting with HMAC
│   └── __init__.py            ✅
├── README.md                  ✅ API documentation
└── requirements.txt           ✅ Python dependencies
```

**Status:** Kod finns men saknar `main.py` (FastAPI endpoints)

### Existerande backend/frontend:
- ✅ `api/` - Befintlig API (Flask/FastAPI?)
- ✅ `frontend/` - React/Next.js frontend
- ✅ `main.py` - Någon form av entry point (behöver ses över)

**OBS:** Dessa kan behöva integreras eller ersättas beroende på slutlig arkitektur

---

## VAD SAKNAS? (Behöver byggas)

### 1. Kärnpipeline (enligt BUILDER_PROMPT.md)
```
src/
├── api.py                     ❌ Python API (run_backlink_job function)
├── profile/
│   ├── target_profiler.py     ❌ Fetch & analyze target page
│   ├── publisher_profiler.py  ❌ Fetch & analyze publisher
│   └── anchor_profiler.py     ❌ Classify anchor
├── serp/
│   ├── research.py            ❌ SERP research coordinator
│   └── serp_api.py            ❌ SERP fetching (kan använda ChatGPT:s kod)
├── intent/
│   └── modeler.py             ❌ Intent modeling & bridge recommendation
├── generation/
│   └── writer.py              ❌ Content generation (artikel)
├── qc/
│   ├── controller.py          ❌ QC validation
│   └── autofix.py             ❌ AutoFixOnce implementation
├── state/
│   └── machine.py             ❌ State machine orchestration
└── utils/
    ├── llm.py                 ❌ LLM client wrapper (Claude API)
    └── helpers.py             ❌ Shared utilities
```

### 2. Config-filer
```
config/
├── thresholds.yaml            ❌ QC thresholds (LSI, trust, anchor risk)
├── policies.yaml              ❌ Trust policy, LSI policy, anchor policy
└── publisher_voices.yaml      ❌ Publisher voice profiles
```

### 3. Schema & Examples
```
schemas/
└── backlink_job_package.schema.json  ❌ JSON Schema (source of truth)

examples/
└── example_job_package.json          ❌ Example output
```

### 4. Tests
```
tests/
├── test_schema_validation.py  ❌ Schema validation test
└── test_live_validation.py    ❌ E2E test
```

### 5. Dokumentation
```
README.md                      ❌ User documentation (installation, usage, etc.)
```

### 6. FastAPI endpoints (om Strategi A väljs)
```
utkast-till-api-lösning/app/main.py  ❌ FastAPI app med endpoints
```

---

## TEKNISK STACK

### Python Dependencies (förväntade):
```
fastapi>=0.115.2           # (om API byggs)
uvicorn>=0.32.0            # (om API byggs)
requests>=2.31.0           # HTTP fetching
httpx>=0.27.2              # Async HTTP
beautifulsoup4>=4.12.3     # HTML parsing
lxml>=5.3.0                # XML/HTML parser
anthropic>=0.8.0           # Claude API client
openai                     # (om OpenAI används istället)
jsonschema>=4.20.0         # JSON schema validation
pyyaml>=6.0.0              # Config files
pydantic>=2.9.2            # Data validation
python-dotenv>=1.0.1       # Environment variables
```

### LLM Provider:
- **Primärt:** Claude (Anthropic API) - Sonnet för analyser, Haiku för klassificering
- **Alternativ:** OpenAI GPT-4

### SERP Data:
- **Rekommenderat:** SERP API (ValueSERP, SerpApi, DataForSEO)
- **Fallback:** Web scraping (playwright/selenium)
- **Dev/Test:** Mock provider (redan implementerad)

---

## ARKITEKTUR-BESLUT

### Val att göra:

**1. API-strategi:**
- [ ] **Strategi A (Hybrid):** FastAPI microservices + Core pipeline
  - Fördelar: Testbarhet, flexibilitet, kan använda Hoppscotch
  - Nackdelar: Mer komplext, HTTP overhead
- [ ] **Strategi B (Monolitisk):** Importera moduler direkt
  - Fördelar: Enkelhet, snabbare, lättare deployment
  - Nackdelar: Mindre testbart steg-för-steg

**Rekommendation:** Börja med B, bygg A senare om behov finns

**2. SERP Provider:**
- [ ] Mock (för utveckling)
- [ ] SerpAPI (stabilt, kostar pengar)
- [ ] Google Custom Search (gratis tier finns)
- [ ] Web scraping (gratis men instabilt)

**Rekommendation:** Mock först, sedan SerpAPI eller Google CSE

**3. LLM Provider:**
- [ ] Claude (Anthropic) - Bäst för svenska, structured output
- [ ] OpenAI GPT-4 - Bra alternativ

**Rekommendation:** Claude (du har credits i browser)

---

## HUR BYGGER JAG DET? (Konkret plan)

### Option 1: Claude Code i Browser (Rekommenderat)

**Steg:**
1. Öppna Claude Code i browser
2. Kopiera innehållet från `BUILDER_PROMPT.md` som systemprompt
3. Säg: "Bygg detta system enligt BUILDER_PROMPT.md. Följ stegen i ordning."
4. Claude Code bygger hela systemet steg-för-steg
5. Testa varje komponent löpande

**Fördel:** Claude Code har credits, kan skriva all kod åt dig

---

### Option 2: Manuell implementation

**Steg:**
1. Läs `IMPLEMENTATION_SPEC.md` för att förstå systemet
2. Följ `BUILDER_PROMPT.md` steg-för-steg
3. Använd `API_INTEGRATION_GUIDE.md` för att integrera ChatGPT:s kod
4. Testa löpande

**Fördel:** Mer kontroll, bättre förståelse

---

## ACCEPTANCE CRITERIA (När är det klart?)

Systemet är klart när följande är sant:

### Must-have:
- [ ] CLI fungerar: `python main.py --publisher X --target Y --anchor Z`
- [ ] Target profiler fungerar (fetch + LLM analysis)
- [ ] Publisher profiler fungerar
- [ ] Anchor profiler fungerar
- [ ] SERP research fungerar (hämta topp-10)
- [ ] Intent modeler fungerar (alignment + bridge type)
- [ ] Writer fungerar (genererar 900+ ord artikel)
- [ ] QC fungerar (validerar artikel)
- [ ] Output genereras korrekt:
  - [ ] `{job_id}_article.md`
  - [ ] `{job_id}_job_package.json`
  - [ ] `{job_id}_qc_report.json`
  - [ ] `{job_id}_execution_log.json`
- [ ] Schema validation test passerar
- [ ] README är komplett

### Nice-to-have:
- [ ] AutoFix fungerar (en automatisk korrigering vid WARNING)
- [ ] FastAPI endpoints fungerar (om Strategi A)
- [ ] E2E test passerar
- [ ] Webhook support fungerar

### Manual validation:
- [ ] Kör ett riktigt case (t.ex. publisher: konsumenternas.se, target: någon produkt/tjänst)
- [ ] Artikeln är 900+ ord
- [ ] Länken är placerad korrekt (ej i H1/H2, mittsektion)
- [ ] 6-10 LSI-termer finns i närfönster
- [ ] Minst 1 trust-källa finns
- [ ] QC-rapporten är rimlig
- [ ] Execution log visar alla state transitions

---

## NÄSTA STEG (Prioriterat)

### 1. BYGG GRUNDSYSTEMET (Följ BUILDER_PROMPT.md)
**Tidsbedömning:** 4-8 timmar med Claude Code

**Action items:**
- [ ] Skapa filstruktur
- [ ] Implementera LLM client wrapper
- [ ] Implementera profilers (target, publisher, anchor)
- [ ] Implementera SERP research
- [ ] Implementera intent modeler
- [ ] Implementera writer (content generation)
- [ ] Implementera QC
- [ ] Implementera state machine
- [ ] Skapa CLI

### 2. TESTA GRUNDSYSTEMET
**Tidsbedömning:** 1-2 timmar

**Action items:**
- [ ] Testa varje komponent isolerat
- [ ] Kör en fullständig pipeline
- [ ] Inspektera output
- [ ] Justera LLM-prompts om nödvändigt

### 3. INTEGRERA CHATGPT:S API-KOD (Om önskat)
**Tidsbedömning:** 1-2 timmar

**Action items:**
- [ ] Välj strategi (A eller B)
- [ ] Följ `API_INTEGRATION_GUIDE.md`
- [ ] Testa integration

### 4. BYGG API-LAGER (Om Strategi A)
**Tidsbedömning:** 2-3 timmar

**Action items:**
- [ ] Skapa `app/main.py` med FastAPI endpoints
- [ ] Testa med Hoppscotch
- [ ] Integrera med core pipeline

### 5. POLISH & DOCUMENTATION
**Tidsbedömning:** 1-2 timmar

**Action items:**
- [ ] Skriv README.md
- [ ] Skapa exempel
- [ ] Skriva tests (schema validation, E2E)
- [ ] Deployment guide

---

## VANLIGA FRÅGOR

### Q: Var börjar jag?
**A:** Öppna Claude Code i browser, kopiera `BUILDER_PROMPT.md` och be Claude bygga systemet.

### Q: Måste jag använda ChatGPT:s API-kod?
**A:** Nej! Du kan bygga allt från scratch enligt `BUILDER_PROMPT.md`. ChatGPT:s kod är en **optional** förbättring som ger färdig SERP-hämtning och metadata extraction.

### Q: Kan jag testa utan SERP API?
**A:** Ja! Använd mock-provider i utveckling. Byt till riktig SERP API senare.

### Q: Måste jag bygga FastAPI endpoints?
**A:** Nej! Börja med CLI (enklare). Bygg API senare om du behöver det.

### Q: Hur stor är den färdiga koden?
**A:** Uppskattningsvis ~3000-4000 rader Python-kod + config-filer. Med Claude Code bör det gå snabbt.

### Q: Vad kostar det att köra?
**A:**
- Claude API: ~$0.01-0.05 per artikel (beroende på modell och längd)
- SERP API: ~$0.002-0.005 per query (eller gratis med Google CSE free tier)

### Q: Kan jag använda svenska texter?
**A:** Ja! Systemet är designat för svenska. Claude Sonnet är excellent på svenska.

---

## FILER ATT GE CLAUDE CODE

När du startar Claude Code i browser, ge följande filer som kontext:

**Primärt:**
1. `BUILDER_PROMPT.md` - Huvudinstruktion (använd som systemprompt)
2. `IMPLEMENTATION_SPEC.md` - Referens för detaljer

**Sekundärt (om Claude behöver mer info):**
3. `API_INTEGRATION_GUIDE.md` - Om du vill integrera ChatGPT:s kod
4. `next-a1-spec.json` - För Next-A1 detaljer
5. `backlink_engine_ideal_flow.md` - För flödesförståelse

**Kommando till Claude Code:**
```
Jag vill att du bygger ett komplett Python-system för backlink content generation.

Använd BUILDER_PROMPT.md som din guide. Följ stegen exakt i ordning (STEG 0-13).

För varje steg:
1. Skapa filerna
2. Implementera koden
3. Förklara vad du gjort
4. Vänta på min bekräftelse innan du går vidare

Börja med STEG 0: Setup & struktur.
```

---

## BACKUP & VERSION CONTROL

### Rekommenderat:
- [ ] Committa alla spec-filer till Git
- [ ] Skapa en branch för implementation
- [ ] Committa efter varje fungerande steg

### Git Commands:
```bash
git add IMPLEMENTATION_SPEC.md BUILDER_PROMPT.md API_INTEGRATION_GUIDE.md PROJECT_STATUS.md
git commit -m "Add complete specifications for BACOWR system"
git push origin main

# Skapa implementation branch
git checkout -b implementation/core-pipeline
```

---

## SAMMANFATTNING

**Du har nu:**
- ✅ Komplett specifikation (IMPLEMENTATION_SPEC.md)
- ✅ Steg-för-steg byggguide (BUILDER_PROMPT.md)
- ✅ Integration-guide för ChatGPT:s kod (API_INTEGRATION_GUIDE.md)
- ✅ Existerande API-kod från ChatGPT (utkast-till-api-lösning/)
- ✅ Denna status-fil (PROJECT_STATUS.md)

**Du behöver:**
- 🔨 Bygga kärnpipelinen (3000-4000 LOC)
- 🔧 Config-filer (YAML)
- 📋 Schema & tests
- 📖 README

**Nästa action:**
1. Öppna Claude Code i browser
2. Ge den BUILDER_PROMPT.md
3. Säg "Bygg detta system steg-för-steg"
4. Följ med och testa löpande

**Estimated time to working system:** 6-10 timmar med Claude Code

---

**Status:** READY TO BUILD 🚀

**Senast uppdaterad:** 2025-11-12
**Av:** Claude (Sonnet 4.5)
**För:** Robin

---

## APPENDIX: KEY CONCEPTS

### Variabelgiftermålet
Gifta samman fyra variabler så de blir semantiskt motiverade:
- Publisher (var publiceras?)
- Ankare (vilken text?)
- Målsida (vart länkar vi?)
- **Intention** (vilken sökintenation ska matchas?) ← MÅSTE härledas från SERP!

### Bridge Types
- **Strong:** Direktlänkning (när allt är aligned)
- **Pivot:** Tematisk brygga (när partial alignment, behöver semantisk pivot)
- **Wrapper:** Metaram (när off alignment, behöver neutral ram först)

### Intent Alignment
Jämför tre dimensioner:
- anchor_vs_serp (aligned/partial/off)
- target_vs_serp (aligned/partial/off)
- publisher_vs_serp (aligned/partial/off)
- **overall** (sammanvägning)

### QC Dimensions
- Anchor risk (low/medium/high)
- Readability (LIX 35-45)
- LSI quality (6-10 termer i närfönster)
- Trust sources (minst 1, T1-T4)
- Compliance (disclaimers för gambling/finance/health/crypto)

### AutoFixOnce
- En automatisk korrigering tillåten per jobb
- Vid WARNING: fixa och försök igen
- Vid BLOCKED: ingen autofix, flagga för manuell granskning

---

**END OF PROJECT STATUS**
