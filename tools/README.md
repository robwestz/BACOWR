# BACOWR Live Testing Tool

**Interaktivt testverktyg för att testa och jämföra LLM-modeller i realtid**

## 🎯 Vad verktyget gör

Detta verktyg låter dig:
- ✅ **Testa content generation i realtid** - Se resultat direkt utan att vänta på produktionspipeline
- ✅ **Jämföra olika LLM-modeller** - Testa Claude vs GPT-4 vs Gemini sida vid sida
- ✅ **Mäta prestanda** - Se tid, kostnad, och kvalitet för varje modell
- ✅ **Spara resultat** - Spara tester för senare jämförelse
- ✅ **Anpassade inputs** - Testa med dina egna publisher/target/anchor värden

## 🚀 Snabbstart

### 1. Installera dependencies

```bash
# Om inte redan gjort
pip install anthropic openai google-generativeai
```

### 2. Konfigurera API-nycklar

```bash
# Lägg till i .env eller exportera direkt:
export ANTHROPIC_API_KEY="din-nyckel"
export OPENAI_API_KEY="din-nyckel"
export GOOGLE_API_KEY="din-nyckel"  # Optional
```

Du behöver minst EN av dessa nycklar för att använda verktyget.

### 3. Kör verktyget

```bash
# Interaktivt läge (rekommenderat)
python tools/live_test.py

# Snabbtest med defaults
python tools/live_test.py --quick

# Jämför alla modeller direkt
python tools/live_test.py --compare-models
```

## 📋 Funktioner

### 1. Quick Test (Snabbtest)

Testa EN modell med mock-data för att snabbt se hur den fungerar.

```bash
python tools/live_test.py --quick
```

**Exempel output:**
```
API Keys Status
✓ Anthropic: Available
✓ Openai: Available

Available Models
  1. claude-sonnet - Claude 3.5 Sonnet - Most capable, best quality ($0.0150/1K tokens)
  2. claude-haiku - Claude 3 Haiku - Fast and cheap ($0.0012/1K tokens)
  3. gpt-4o - GPT-4o - Latest OpenAI model ($0.0100/1K tokens)
  4. gpt-4o-mini - GPT-4o Mini - Fast and cheap ($0.0006/1K tokens)

Select model (number): 1

ℹ Generating with claude-sonnet...

Results
✓ Generated in 4.23s
✓ Word count: 1245
✓ Estimated cost: $0.0234
✓ Tokens: 1200 input, 1560 output
```

### 2. Model Comparison (Jämför modeller)

Jämför flera modeller med SAMMA input för att se vilken som är bäst för ditt use case.

```bash
python tools/live_test.py --compare-models
```

**Eller välj i interaktivt läge:**
```
Select models to compare (comma-separated numbers, or 'all'): 1,2,4
```

**Exempel output:**
```
Comparison Results

Model                   Time      Cost    Words   Tokens Out
----------------------------------------------------------------------
claude-sonnet          4.23s  $0.0234     1245         1560
claude-haiku           1.89s  $0.0089      987         1240
gpt-4o-mini            2.14s  $0.0045     1032         1290

Best in Category
✓ Fastest: claude-haiku (1.89s)
✓ Cheapest: gpt-4o-mini ($0.0045)
✓ Most words: claude-sonnet (1245 words)
```

### 3. Custom Input Test (Anpassade värden)

Testa med dina egna publisher, target URL, och anchor text.

**I interaktivt läge:**
```
Choose option: 3

Enter your test parameters
Publisher domain: tekniktips.se
Target URL: https://example.com/product-x
Anchor text: bästa valet för produktkategori

Select model (number): 1

ℹ Generating with claude-sonnet...
✓ Generated in 5.12s
✓ Word count: 1389
✓ Estimated cost: $0.0267
```

### 4. View Saved Results (Visa sparade tester)

Se alla sparade tester och jämförelser.

```
Choose option: 4

Found 5 saved tests:
  1. test_20250109_143022.json - claude-sonnet (2025-01-09T14:30:22)
  2. comparison_20250109_144533.json - Comparison of 3 models (2025-01-09T14:45:33)
  3. custom_tekniktips.json - claude-haiku (2025-01-09T15:12:11)
```

## 🤖 Modeller som stöds

### Anthropic (Claude)

| Modell | Beskrivning | Kostnad (per 1K output tokens) | Användning |
|--------|-------------|-------------------------------|------------|
| **claude-sonnet** | Claude 3.5 Sonnet | $0.015 | Bästa kvalitet, längre artiklar |
| **claude-haiku** | Claude 3 Haiku | $0.00125 | Snabb och billig, bra för tester |

### OpenAI

| Modell | Beskrivning | Kostnad (per 1K output tokens) | Användning |
|--------|-------------|-------------------------------|------------|
| **gpt-4o** | GPT-4o (latest) | $0.010 | Hög kvalitet, snabb |
| **gpt-4o-mini** | GPT-4o Mini | $0.0006 | Mycket billig, bra kvalitet |
| **gpt-4-turbo** | GPT-4 Turbo | $0.030 | Högsta kvalitet (dyr) |

### Google (Gemini)

| Modell | Beskrivning | Kostnad (per 1K output tokens) | Användning |
|--------|-------------|-------------------------------|------------|
| **gemini-flash** | Gemini 1.5 Flash | $0.0004 | Billigast, snabb |
| **gemini-pro** | Gemini 1.5 Pro | $0.005 | Hög kvalitet |

> **Note**: Google-stöd är under utveckling i WriterEngine. Använd Anthropic eller OpenAI för nu.

## 💰 Kostnadsuppskattningar

För en typisk backlink-artikel (900-1200 ord):

| Modell | Estimerad kostnad | Tid (ca) | Kvalitet |
|--------|-------------------|----------|----------|
| **claude-haiku** | $0.008-0.012 | 1-2s | God |
| **gpt-4o-mini** | $0.004-0.007 | 2-3s | God |
| **gemini-flash** | $0.003-0.005 | 1-2s | God |
| **claude-sonnet** | $0.020-0.030 | 3-5s | Utmärkt |
| **gpt-4o** | $0.015-0.025 | 2-4s | Utmärkt |
| **gpt-4-turbo** | $0.040-0.060 | 3-5s | Utmärkt |

**Rekommendation:**
- **För produktion (volym)**: `claude-haiku` eller `gpt-4o-mini` (bästa pris/kvalitet)
- **För bästa kvalitet**: `claude-sonnet` eller `gpt-4o`
- **För testing**: `gemini-flash` eller `claude-haiku` (billigast)

## 📊 Hur man jämför modeller effektivt

### Scenario 1: Hitta bästa "budget-modell"

```bash
# Jämför de billiga modellerna
python tools/live_test.py

# Välj option 2 (Compare models)
# Välj: claude-haiku, gpt-4o-mini, gemini-flash

# Se vilken som ger bäst kvalitet för lägsta pris
```

### Scenario 2: Testa för specifik publisher

```bash
# Custom test
python tools/live_test.py

# Välj option 3 (Custom input)
# Ange din publisher, target, anchor
# Testa med olika modeller

# Spara resultaten och jämför artikelkvalitet manuellt
```

### Scenario 3: Prestanda-test

```bash
# Jämför alla modeller för att se prestanda
python tools/live_test.py --compare-models

# Kör flera gånger för att få genomsnitt
# Spara resultaten och analysera
```

## 🎓 Användningsexempel

### Exempel 1: Snabbtest med Haiku

```bash
$ python tools/live_test.py --quick

Choose option: 1
Select model: 2  # claude-haiku

ℹ Loading mock job package...
ℹ Publisher: tech-review-se.example
ℹ Target: https://clientsite.com/product-premium
ℹ Anchor: bästa valet för premiumlösningar

ℹ Generating with claude-haiku...

Results
✓ Generated in 1.89s
✓ Word count: 987
✓ Estimated cost: $0.0089
✓ Tokens: 1150 input, 1240 output

Article Preview (first 500 chars)
# Guide: Hitta bästa lösningen för dina behov inom premiumlösningar

När man utvärderar olika alternativ inom premiumlösningar finns det...

Save this test? (y/n): y
Test name (optional): haiku_quick_test
✓ Saved to: storage/test_results/haiku_quick_test.json
```

### Exempel 2: Jämför Claude vs GPT-4o

```bash
$ python tools/live_test.py

Choose option: 2  # Compare models
Select models: 1,3  # claude-sonnet, gpt-4o

ℹ Will compare 2 models: claude-sonnet, gpt-4o
ℹ Using mock data: tech-review-se.example

ℹ Generating with claude-sonnet...
✓ claude-sonnet: Done (4.23s, $0.0234)

ℹ Generating with gpt-4o...
✓ gpt-4o: Done (3.87s, $0.0198)

Comparison Results

Model                   Time      Cost    Words   Tokens Out
----------------------------------------------------------------------
claude-sonnet          4.23s  $0.0234     1245         1560
gpt-4o                 3.87s  $0.0198     1189         1485

Best in Category
✓ Fastest: gpt-4o (3.87s)
✓ Cheapest: gpt-4o ($0.0198)
✓ Most words: claude-sonnet (1245 words)

Save comparison? (y/n): y
Test name: claude_vs_gpt4o
✓ Saved to: storage/test_results/claude_vs_gpt4o.json
```

### Exempel 3: Anpassad test för specifik publisher

```bash
$ python tools/live_test.py

Choose option: 3  # Custom input

Enter your test parameters
Publisher domain: hemblogg.se
Target URL: https://premiumverktyg.se/produkt-x
Anchor text: rekommenderat verktyg för hemmabruk

Select model: 1  # claude-sonnet

ℹ Generating with claude-sonnet...

Results
✓ Generated in 5.34s
✓ Word count: 1432
✓ Estimated cost: $0.0289

Article Preview (first 800 chars)
# Komplett guide: Hitta rätt verktyg för hemmabruk

När man planerar hemprojekt är det viktigt att ha rätt verktyg...
[specifik, relevant content för hemmabruk-nischen]

View full article? (y/n): y

[Full article visas här]

Save this test? (y/n): y
Test name: hemblogg_produkt_x
✓ Saved to: storage/test_results/hemblogg_produkt_x.json
```

## 🔍 Analysera resultat

### Vad du bör titta på:

1. **Innehållskvalitet**
   - Är artikeln relevant för publisher/target/anchor?
   - Naturlig integration av länken?
   - Rätt ton och språk?
   - LSI-termer inkluderade?

2. **Teknisk kvalitet**
   - Rätt ordlängd (900+ ord)?
   - Bra struktur (H1, H2, osv)?
   - Markdown-formatering korrekt?

3. **Pris/prestanda**
   - Kostnad per artikel?
   - Generationstid acceptable?
   - Kvalitet värd kostnaden?

4. **Jämförelse mellan modeller**
   - Vilken ger bäst kvalitet?
   - Vilken är snabbast?
   - Vilken är billigast?
   - Bästa pris/kvalitet-balans?

### Tips för jämförelse:

```bash
# 1. Spara alla tester med beskrivande namn
Test name: claude_haiku_tech_niche
Test name: gpt4o_mini_tech_niche
Test name: claude_sonnet_tech_niche

# 2. Jämför SAMMA input med olika modeller
# 3. Kör flera gånger för att få genomsnitt
# 4. Testa olika typer av publishers/niches
# 5. Dokumentera dina findings
```

## 📁 Var sparas resultaten?

Alla testresultat sparas i:
```
storage/test_results/
├── test_20250109_143022.json
├── comparison_20250109_144533.json
├── claude_vs_gpt4o.json
└── custom_tekniktips.json
```

Varje fil innehåller:
```json
{
  "type": "single|comparison|custom",
  "job_package": { /* complete job package */ },
  "result": {
    "article": "...",
    "time": 4.23,
    "estimated_cost": 0.0234,
    "tokens_input": 1200,
    "tokens_output": 1560,
    "word_count": 1245,
    "model": "claude-sonnet",
    "provider": "anthropic"
  },
  "timestamp": "2025-01-09T14:30:22"
}
```

## 🛠️ Troubleshooting

### Problem: "No API keys configured"

**Lösning:**
```bash
# Sätt API-nyckel i .env
echo 'ANTHROPIC_API_KEY=din-nyckel' >> .env

# Eller exportera direkt
export ANTHROPIC_API_KEY="din-nyckel"
```

### Problem: "ImportError: anthropic package not installed"

**Lösning:**
```bash
pip install anthropic openai google-generativeai
```

### Problem: Verktyget kraschar vid generation

**Lösning:**
1. Kontrollera att API-nyckel är giltig
2. Kolla internet-anslutning
3. Testa med `--quick` för att verifiera setup
4. Kolla logs för specifikt felmeddelande

### Problem: Kostar för mycket

**Lösning:**
- Använd billigare modeller: `claude-haiku`, `gpt-4o-mini`, `gemini-flash`
- Testa med mock mode först: `python main.py --mock`
- Övervaka kostnad med verktygets estimeringar

## 🎯 Nästa steg

Efter att du testat och hittat bästa modellen:

1. **Uppdatera production config**
   ```python
   # I src/writer/writer_engine.py, ändra default model
   DEFAULT_MODEL = 'claude-haiku'  # Din valda modell
   ```

2. **Kör production test**
   ```bash
   python main.py --publisher example.com --target https://target.com --anchor "text"
   ```

3. **Integrera i batch pipeline**
   ```bash
   # Kör flera jobb
   for i in {1..10}; do
     python main.py --publisher "pub$i.com" --target "https://target.com" --anchor "anchor $i"
   done
   ```

4. **Submit till validation queue**
   ```bash
   # Se .validation/README.md för workflow
   cp .validation/templates/queue-item-template.md .validation/queue/content-generation.md
   # Fyll i template och committa
   ```

## 📚 Relaterade filer

- `main.py` - Huvudsakliga CLI för produktion
- `src/writer/writer_engine.py` - Content generation engine
- `src/profiling/llm_enhancer.py` - LLM-baserad profiling
- `.validation/` - Validation workflow system

## 💡 Tips & Best Practices

1. **Testa ofta** - Kör quick tests regelbundet för att verifiera kvalitet
2. **Spara resultat** - Spara alla jämförelser för dokumentation
3. **Jämför systematiskt** - Testa samma input med olika modeller
4. **Optimera för use case** - Olika niches kan kräva olika modeller
5. **Balansera kostnad/kvalitet** - Dyra modeller inte alltid nödvändiga
6. **Använd mock mode** - Testa logik utan API-kostnader först

## 🚀 Quick Reference

```bash
# Interaktivt läge (rekommenderat för första gången)
python tools/live_test.py

# Snabbtest
python tools/live_test.py --quick

# Jämför alla modeller
python tools/live_test.py --compare-models

# Huvudsakliga CLI (produktion)
python main.py --publisher example.com --target https://target.com --anchor "text"

# Mock mode (ingen kostnad)
python main.py --publisher example.com --target https://target.com --anchor "text" --mock
```

---

**Skapat**: 2025-01-09
**Version**: 1.0
**Support**: Se `.validation/README.md` för feedback-process
