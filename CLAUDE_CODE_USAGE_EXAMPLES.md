# BACOWR i Claude Code-format - Användningsexempel

Detta dokument visar hur det ser ut att använda BACOWR med Claude Code för att generera backlink-artiklar.

---

## Scenario 1: Generera en enskild artikel

### Användarförfrågan
```
Användare: Jag behöver en backlink-artikel för Aftonbladet som länkar till Wikipedia-sidan
om Artificiell Intelligens. Ankartexten ska vara "läs mer om AI".
```

### Claude Code-interaktion

**Claude:**
```
Jag hjälper dig att generera en backlink-artikel med BACOWR. Låt mig först kontrollera
miljön och sedan köra genereringen.

Todo-lista:
1. ⏳ Kontrollera API-nycklar och miljö
2. ⏱ Generera artikel med production_main.py
3. ⏱ Granska QC-rapporten
4. ⏱ Visa resultatsammanfattning
```

**Claude kör:**
```bash
# Kontrollera tillgängliga API-nycklar
echo "Kontrollerar API-nycklar..."
test -n "$ANTHROPIC_API_KEY" && echo "✓ ANTHROPIC_API_KEY finns"
test -n "$AHREFS_API_KEY" && echo "✓ AHREFS_API_KEY finns" || echo "ℹ AHREFS_API_KEY saknas (använder mock-data)"
```

**Output:**
```
✓ ANTHROPIC_API_KEY finns
✓ AHREFS_API_KEY finns
```

**Claude:**
```
✓ API-nycklar verifierade

Todo-lista:
1. ✅ Kontrollera API-nycklar och miljö
2. ⏳ Generera artikel med production_main.py
3. ⏱ Granska QC-rapporten
4. ⏱ Visa resultatsammanfattning

Nu kör jag artikelgenereringen:
```

**Claude kör:**
```bash
python production_main.py \
  --publisher aftonbladet.se \
  --target "https://sv.wikipedia.org/wiki/Artificiell_intelligens" \
  --anchor "läs mer om AI" \
  --llm anthropic \
  --strategy multi_stage \
  --verbose
```

**Output (förkortat):**
```
======================================================================
BACOWR Production - BacklinkContent Engine
======================================================================

Available LLM providers: anthropic (Claude)
SERP source: Ahrefs API

Configuration:
  Publisher:  aftonbladet.se
  Target:     https://sv.wikipedia.org/wiki/Artificiell_intelligens
  Anchor:     läs mer om AI
  LLM:        anthropic
  Strategy:   multi_stage
  Country:    se
  Ahrefs:     enabled
  LLM Profile: enabled

----------------------------------------------------------------------

[PREFLIGHT] Profiling publisher domain...
[PREFLIGHT] Publisher profile created: Aftonbladet - Swedish news media
[PREFLIGHT] Profiling target URL...
[PREFLIGHT] Target profile: Wikipedia page about AI
[PREFLIGHT] Fetching SERP data for "artificiell intelligens"...
[PREFLIGHT] Retrieved 10 SERP results from Ahrefs
[PREFLIGHT] Analyzing intent alignment...
[PREFLIGHT] Intent analysis: alignment_score=0.85, bridge_type=strong

[WRITE] Starting multi-stage content generation...
[WRITE] Stage 1/3: Outline generation...
[WRITE] Stage 2/3: Content generation...
[WRITE] Stage 3/3: Polish and refinement...
[WRITE] Article generated (1247 words)

[QC] Running quality control checks...
[QC] ✓ Word count check passed (1247 >= 900)
[QC] ✓ Link placement check passed
[QC] ✓ LSI term check passed (8 terms found)
[QC] ✓ Trust source check passed (2 T1-T2 sources)
[QC] ✓ Intent alignment check passed (0.85)
[QC] No issues found

[DELIVER] Saving output files...
[DELIVER] Job completed successfully

======================================================================
Job ID: job_20251204_143052_a3f9
Status: DELIVERED
======================================================================

✓ Article generated successfully!

Generation metrics:
  Provider:   anthropic
  Model:      claude-sonnet-4-5
  Stages:     3
  Duration:   34.12s

QC Report:
  Status:     approved
  Issues:     0
  AutoFix:    No
  Signoff:    Not required

Output files:
  article: storage/output/job_20251204_143052_a3f9_article.md
  job_package: storage/output/job_20251204_143052_a3f9_job_package.json
  qc_report: storage/output/job_20251204_143052_a3f9_qc_report.json
  execution_log: storage/output/job_20251204_143052_a3f9_execution_log.json
  metrics: storage/output/job_20251204_143052_a3f9_metrics.json
```

**Claude:**
```
✓ Artikel genererad framgångsrikt!

Todo-lista:
1. ✅ Kontrollera API-nycklar och miljö
2. ✅ Generera artikel med production_main.py
3. ⏳ Granska QC-rapporten
4. ⏱ Visa resultatsammanfattning

Låt mig granska QC-rapporten:
```

**Claude läser och sammanfattar:**
```
QC-rapport visar:
- ✓ Status: APPROVED
- ✓ Inga blockerande problem
- ✓ LSI-täckning: 8 relevanta termer nära länken
- ✓ Trust sources: 2 högkvalitativa källor (T1-T2)
- ✓ Intent alignment: 0.85 (stark matchning)
- ✓ Länkplacering: Godkänd position i artikeln
- ✓ Inget AutoFix behövdes
- ✓ Ingen mänsklig granskning krävs

Todo-lista:
1. ✅ Kontrollera API-nycklar och miljö
2. ✅ Generera artikel med production_main.py
3. ✅ Granska QC-rapporten
4. ⏳ Visa resultatsammanfattning

Artikeln är klar och redo för publicering! Här är sammanfattningen:
```

**Claude visar:**
```
📄 RESULTATSAMMANFATTNING
========================

Job ID: job_20251204_143052_a3f9
Status: ✅ DELIVERED (redo för publicering)

Artikel:
- Längd: 1247 ord
- Språk: Svenska
- Typ: Strong bridge (direkt koppling mellan publisher och target)
- Tid: 34 sekunder

Kvalitetskontroll:
- QC Status: APPROVED
- Intent alignment: 0.85/1.00 (utmärkt)
- LSI-termer: 8 (inom rekommenderat spann 6-10)
- Trust sources: 2 (T1-T2 källor)
- Compliance: Godkänd

Filer:
- Artikel: storage/output/job_20251204_143052_a3f9_article.md
- Komplett jobpaket: storage/output/job_20251204_143052_a3f9_job_package.json
- QC-rapport: storage/output/job_20251204_143052_a3f9_qc_report.json

Rekommendation: Artikeln kan publiceras direkt utan ytterligare granskning.
```

---

## Scenario 2: Batch-processing av flera jobb

### Användarförfrågan
```
Användare: Jag har en CSV-fil med 25 backlink-jobb som jag behöver köra. Kör dom med
3 parallella workers och visa progress.
```

### Claude Code-interaktion

**Claude:**
```
Jag hjälper dig köra batch-jobb med BACOWR. Låt mig först inspektera din CSV-fil och
sedan köra batch-processorn.

Todo-lista:
1. ⏳ Inspektera CSV-fil med jobb
2. ⏱ Validera CSV-format
3. ⏱ Starta batch-körning med 3 workers
4. ⏱ Övervaka progress
5. ⏱ Sammanfatta batch-resultat
```

**Claude kör:**
```bash
# Visa de första raderna av CSV-filen
head -5 jobs.csv
```

**Output:**
```
publisher,target,anchor,llm_provider,strategy
aftonbladet.se,https://example.com/product1,bästa produkten,anthropic,multi_stage
dn.se,https://example.com/service1,läs mer här,anthropic,single_shot
svd.se,https://example.com/page1,klicka här,anthropic,multi_stage
expressen.se,https://example.com/article1,mer information,anthropic,multi_stage
```

**Claude:**
```
✓ CSV-filen innehåller 25 jobb med korrekt format

Todo-lista:
1. ✅ Inspektera CSV-fil med jobb
2. ✅ Validera CSV-format
3. ⏳ Starta batch-körning med 3 workers
4. ⏱ Övervaka progress
5. ⏱ Sammanfatta batch-resultat

Startar batch-körning med 3 parallella workers:
```

**Claude kör:**
```bash
python batch_runner.py \
  --input jobs.csv \
  --parallel 3 \
  --rate-limit 10 \
  --output storage/batch_output/batch_20251204_1430
```

**Output (simulerad progress):**
```
======================================================================
BACOWR Batch Runner
======================================================================

Input file: jobs.csv
Jobs found: 25
Parallel workers: 3
Rate limit: 10 calls/minute
Output directory: storage/batch_output/batch_20251204_1430

----------------------------------------------------------------------

Starting batch processing...

[Worker 1] Job 1/25: aftonbladet.se → example.com/product1
[Worker 2] Job 2/25: dn.se → example.com/service1
[Worker 3] Job 3/25: svd.se → example.com/page1

[Worker 1] ✓ Job 1 completed (32.5s) - Status: DELIVERED
[Worker 1] Job 4/25: expressen.se → example.com/article1
[Worker 2] ✓ Job 2 completed (28.1s) - Status: DELIVERED
[Worker 2] Job 5/25: gp.se → example.com/product2
[Worker 3] ✓ Job 3 completed (35.2s) - Status: DELIVERED
[Worker 3] Job 6/25: metro.se → example.com/service2

Progress: [████████░░░░░░░░░░░░] 24% (6/25) - ETA: 8m 15s

[Worker 1] ✓ Job 4 completed (30.8s) - Status: DELIVERED
[Worker 1] Job 7/25: nwt.se → example.com/page2
[Worker 2] ✓ Job 5 completed (27.3s) - Status: DELIVERED
[Worker 2] Job 8/25: vk.se → example.com/article2

...

Progress: [████████████████████] 100% (25/25) - Completed!

======================================================================
BATCH SUMMARY
======================================================================

Total jobs: 25
Completed: 23
Failed: 2
Success rate: 92.0%

Total duration: 12m 34s
Average time per job: 30.2s
Total cost: $4.23

Status breakdown:
  DELIVERED: 23 (92.0%)
  BLOCKED: 1 (4.0%)
  ABORTED: 1 (4.0%)

Failed jobs:
  Job 15: BLOCKED - Low intent alignment (0.42)
  Job 22: ABORTED - Target URL unreachable

Output directory: storage/batch_output/batch_20251204_1430
Batch report: storage/batch_output/batch_20251204_1430/batch_report.json

======================================================================
```

**Claude:**
```
✓ Batch-körning slutförd!

Todo-lista:
1. ✅ Inspektera CSV-fil med jobb
2. ✅ Validera CSV-format
3. ✅ Starta batch-körning med 3 workers
4. ✅ Övervaka progress
5. ⏳ Sammanfatta batch-resultat

Låt mig visa en detaljerad sammanfattning:
```

**Claude sammanfattar:**
```
📊 BATCH-KÖRNING SLUTFÖRD
=========================

Resultat:
- ✅ 23/25 jobb slutförda framgångsrikt (92% success rate)
- ⚠️ 1 jobb blockerat av QC (Job 15)
- ❌ 1 jobb avbrutit (Job 22 - URL ej nåbar)

Prestanda:
- Total tid: 12 minuter 34 sekunder
- Genomsnitt per jobb: 30.2 sekunder
- Total kostnad: $4.23
- Parallellisering: 3 workers (bra effektivitet)

Problem som behöver åtgärdas:
1. Job 15 (BLOCKED): Låg intent alignment (0.42)
   → Publisher: svt.se
   → Target: example.com/offpage-product
   → Rekommendation: Ändra anchor text eller välj annan publisher

2. Job 22 (ABORTED): Target URL ej tillgänglig
   → Target: example.com/broken-link
   → Rekommendation: Fixa URL och kör om jobbet

Nästa steg:
1. Granska de 23 godkända artiklarna i: storage/batch_output/batch_20251204_1430/
2. Åtgärda de 2 misslyckade jobben och kör om dem
3. Se detaljerad rapport: storage/batch_output/batch_20251204_1430/batch_report.json
```

---

## Scenario 3: Resultatgranskning och export

### Användarförfrågan
```
Användare: Visa mig artikeln från det senaste jobbet och exportera den till Google Docs.
```

### Claude Code-interaktion

**Claude:**
```
Jag hämtar den senaste artikeln och exporterar den till Google Docs.

Todo-lista:
1. ⏳ Hitta senaste job-ID
2. ⏱ Läsa och visa artikel
3. ⏱ Visa QC-metadata
4. ⏱ Exportera till Google Docs
```

**Claude kör:**
```bash
# Hitta senaste job-ID baserat på filmodifieringstid
ls -t storage/output/*_article.md | head -1
```

**Output:**
```
storage/output/job_20251204_143052_a3f9_article.md
```

**Claude läser och visar:**
```
✓ Hittade senaste artikel

Todo-lista:
1. ✅ Hitta senaste job-ID
2. ⏳ Läsa och visa artikel
3. ⏱ Visa QC-metadata
4. ⏱ Exportera till Google Docs

Artikelsammanfattning:
```

**Claude visar:**
```
📄 ARTIKEL: job_20251204_143052_a3f9
====================================

Rubrik: AI-revolutionen: Så förändrar artificiell intelligens vårt samhälle

Metadata:
- Publisher: Aftonbladet (aftonbladet.se)
- Target: Wikipedia - Artificiell intelligens
- Anchor: "läs mer om AI"
- Språk: Svenska
- Längd: 1247 ord
- Bridge-typ: Strong (direkt koppling)

Inledning (första 200 ord):
---
Artificiell intelligens har under de senaste åren gått från att vara en
science fiction-fantasi till att bli en allt mer närvarande del av vår vardag.
Från smarta telefoner som förstår våra röster till bilar som kan köra själva –
AI-teknologin utvecklas i rasande fart och påverkar allt fler delar av samhället.

Men vad är egentligen artificiell intelligens, och hur kommer denna teknologi
att forma framtiden? För att förstå fenomenet behöver vi först titta på historien
och utvecklingen av detta fascinerande område inom datavetenskap...
---

Länkplacering: Paragraf 4 (optimal position enligt Next-A1)
LSI-termer nära länk: maskininlärning, neurala nätverk, deep learning,
algoritmer, dataanalys, automation, språkmodeller, datorseende

QC-bedömning: ✅ APPROVED - Redo för publicering
```

**Claude:**
```
Todo-lista:
1. ✅ Hitta senaste job-ID
2. ✅ Läsa och visa artikel
3. ✅ Visa QC-metadata
4. ⏳ Exportera till Google Docs

Nu exporterar jag artikeln till Google Docs:
```

**Claude kör:**
```bash
python -c "
from src.export.google_export import export_to_google_docs
import json

# Läs jobpaket
with open('storage/output/job_20251204_143052_a3f9_job_package.json', 'r') as f:
    job_package = json.load(f)

# Exportera
result = export_to_google_docs(
    job_package=job_package,
    folder_id=None  # Använd root folder
)

print(f'✓ Exporterad till Google Docs')
print(f'Doc ID: {result[\"doc_id\"]}')
print(f'URL: {result[\"doc_url\"]}')
"
```

**Output:**
```
✓ Exporterad till Google Docs
Doc ID: 1abc123xyz789
URL: https://docs.google.com/document/d/1abc123xyz789/edit
```

**Claude:**
```
✓ Export slutförd!

Todo-lista:
1. ✅ Hitta senaste job-ID
2. ✅ Läsa och visa artikel
3. ✅ Visa QC-metadata
4. ✅ Exportera till Google Docs

Artikeln har exporterats till Google Docs:
🔗 https://docs.google.com/document/d/1abc123xyz789/edit

Dokumentet innehåller:
- Formaterad artikel med rubrik och stycken
- Länk med korrekt anchor text
- QC-metadata som kommentar
- Trust sources markerade
- LSI-termer highlightade (för granskning)
```

---

## Scenario 4: Felsökning och AutoFix

### Användarförfrågan
```
Användare: Ett jobb gav status BLOCKED. Vad hände och hur fixar jag det?
```

### Claude Code-interaktion

**Claude:**
```
Låt mig granska det blockerade jobbet och se vad som gick fel.

Todo-lista:
1. ⏳ Hitta blockerat jobb
2. ⏱ Läsa QC-rapport
3. ⏱ Analysera blockeringsorsak
4. ⏱ Ge rekommendationer för fix
```

**Claude kör:**
```bash
# Hitta jobb med status BLOCKED
grep -l '"status": "BLOCKED"' storage/output/*_qc_report.json | head -1
```

**Output:**
```
storage/output/job_20251204_152341_b7k2_qc_report.json
```

**Claude läser och analyserar:**
```
✓ Hittade blockerat jobb: job_20251204_152341_b7k2

Todo-lista:
1. ✅ Hitta blockerat jobb
2. ✅ Läsa QC-rapport
3. ⏳ Analysera blockeringsorsak
4. ⏱ Ge rekommendationer för fix

QC-rapport visar följande problem:
```

**Claude visar:**
```
🚫 BLOCKERAT JOBB: job_20251204_152341_b7k2
==========================================

Status: BLOCKED
Blockeringsorsak: QC validation failed - Human signoff required

Input:
- Publisher: casino-sida.se
- Target: https://spelbolag.com/bonus
- Anchor: "bästa casinobonus"

Problem identifierade:

1. ⚠️ COMPLIANCE VIOLATION (severity: blocking)
   - Gambling-relaterat innehåll saknar required disclaimer
   - Enligt Next-A1: Gambling content kräver ansvarsspel-disclaimer
   - AutoFix försökte: Lade till disclaimer, men human signoff krävs fortfarande

2. ⚠️ LINK PLACEMENT WARNING (severity: warning)
   - Länk i förstadelsparagraf (inte optimalt)
   - Rekommendation: Flytta till mitten av artikeln
   - AutoFix försökte: Flyttade länk till paragraf 4

3. ⚠️ ANCHOR RISK HIGH (severity: warning)
   - Money-keyword anchor i gambling-kontext
   - Risk för spam-signal
   - AutoFix försökte: Föreslog partial match anchor istället

AutoFix-logg:
- Attempt 1: Flyttade länk från paragraf 1 till paragraf 4
- Attempt 1: Lade till gambling disclaimer
- Attempt 1: Föreslog anchor-alternativ: "läs mer om casinobonusar"
- Result: Blocking condition kvarstår (gambling compliance)
- Human signoff: REQUIRED

Manuella åtgärder som krävs:
1. Granska compliance disclaimer (se artikel)
2. Godkänn eller justera disclaimer-text
3. Överväg anchor text-ändring till partial match
4. Manuellt godkänn artikeln efter granskning
```

**Claude:**
```
Todo-lista:
1. ✅ Hitta blockerat jobb
2. ✅ Läsa QC-rapport
3. ✅ Analysera blockeringsorsak
4. ⏳ Ge rekommendationer för fix

Här är mina rekommendationer för att lösa blockeringen:
```

**Claude ger rekommendationer:**
```
🔧 REKOMMENDATIONER FÖR FIX
===========================

Problemet är att detta är gambling-innehåll, vilket enligt Next-A1-specen
kräver mänsklig granskning även om AutoFix har lagt till compliance-text.

Alternativ för att fortsätta:

Option 1: MANUELL GRANSKNING (rekommenderat)
---------------------------------------------
1. Granska artikeln: storage/output/job_20251204_152341_b7k2_article.md
2. Verifiera att disclaimer-texten är korrekt
3. Kontrollera att länkplacering är lämplig
4. Manuellt godkänn genom att uppdatera job package:

   python -c "
   import json
   with open('storage/output/job_20251204_152341_b7k2_job_package.json', 'r+') as f:
       data = json.load(f)
       data['qc_report']['manual_approval'] = {
           'approved': True,
           'approved_by': 'content_manager',
           'timestamp': '2025-12-04T15:30:00Z',
           'notes': 'Compliance checked, disclaimer approved'
       }
       f.seek(0)
       json.dump(data, f, indent=2)
   "

Option 2: ÄNDRA INPUT (undvik blocking)
---------------------------------------
1. Ändra anchor text till partial match: "läs mer om casinobonusar"
2. Kör om jobbet med justerade parametrar:

   python production_main.py \
     --publisher casino-sida.se \
     --target "https://spelbolag.com/bonus" \
     --anchor "läs mer om casinobonusar" \
     --anchor-type partial \
     --llm anthropic

Option 3: JUSTERA THRESHOLDS (ej rekommenderat)
------------------------------------------------
Ändra blocking conditions i config/policies.yaml (men det påverkar alla
gambling-jobb och reducerar compliance-säkerhet)

Min rekommendation: Gå med Option 1. AutoFix har redan gjort sitt jobb och
lagt till rätt disclaimer. Du behöver bara verifiera att texten är korrekt
och manuellt godkänna artikeln.
```

---

## Sammanfattning: Typiska Claude Code-flöden för BACOWR

### Snabba single jobs:
```bash
python quickstart.py  # Interaktiv guide
python production_main.py --publisher X --target Y --anchor Z
```

### Batch-processing:
```bash
python batch_runner.py --input jobs.csv --parallel 3
python batch_monitor.py --watch storage/batch_output/
```

### Kostnadsestimering före körning:
```bash
python cost_calculator.py --jobs 100 --provider anthropic --strategy multi_stage
```

### Resultatgranskning:
```bash
# Hitta senaste jobb
ls -t storage/output/*_job_package.json | head -1

# Läs QC-rapport
cat storage/output/[job_id]_qc_report.json | jq '.status, .issues'

# Visa artikel
cat storage/output/[job_id]_article.md

# Validera mot schema
python -m jsonschema -i storage/output/[job_id]_job_package.json backlink_job_package.schema.json
```

### Vanliga troubleshooting-kommandon:
```bash
# Kör alla tester
pytest

# Validera schema
python tests/test_schema_validation.py

# Kör mock-test (utan API-kostnader)
python main.py --publisher test.com --target https://example.com --anchor "test" --serp-mode mock

# Kontrollera execution log för felsökning
cat storage/output/[job_id]_execution_log.json | jq '.[] | select(.success == false)'
```

---

## Claude Code-specifika fördelar med BACOWR

1. **Progressspårning**: TodoWrite-verktyget håller koll på varje steg
2. **Automatisk felsökning**: Claude läser execution logs och QC-rapporter
3. **Batch-optimering**: Claude kan köra parallella jobb och övervaka progress
4. **Schema-validering**: Claude validerar output mot JSON-schemat automatiskt
5. **Cost tracking**: Claude kan estimera kostnader före körning
6. **Export automation**: Claude kan automatiskt exportera till Google Docs/Sheets
7. **QC-analys**: Claude tolkar QC-rapporter och ger konkreta fix-rekommendationer

Alla dessa workflows drar nytta av Claude Codes förmåga att:
- Köra kommandon och läsa output
- Läsa och analysera JSON/log-filer
- Skapa todos och spåra progress
- Ge kontextuella rekommendationer baserat på QC-resultat
- Automatisera repetitiva batch-operationer
