# BACOWR – BacklinkContent Engine (Next-A1)

**B**acklink **A**rticle **C**ontent **O**rchestration **W**ith **R**efinement

Ett ramverk för automatiserad, SERP-driven länkinnehållsproduktion baserat på Next-A1 specifikationen.

## 📋 Översikt

BACOWR är en produktionsklar motor för att skapa högkvalitativa backlink-artiklar som:

- ✅ **Analyserar SERP** för intent och toppresultat
- ✅ **Profilerar** målsida och publisher automatiskt
- ✅ **Genererar** backlink-innehåll som naturligt passar SERP-landskapet
- ✅ **Validerar** kvalitet med inbyggd QC (Quality Control)
- ✅ **Loggar** hela processen för spårbarhet

### Tre-input-paradigm

Motorn kräver endast tre inputs:

```json
{
  "publisher_domain": "example-publisher.com",
  "target_url": "https://client.com/product-x",
  "anchor_text": "bästa valet för [tema]"
}
```

Därifrån sker allt annat automatiskt.

## 🏗️ Arkitektur

### Komponenter

```
BACOWR/
├── backlink_job_package.schema.json    # JSON Schema (single source of truth)
├── BacklinkJobPackage.json             # Exempel-jobb
├── backlink_engine_ideal_flow.md       # Idealflöde dokumentation
├── next-a1-spec.json                   # Next-A1 specifikation
├── NEXT-A1-ENGINE-ADDENDUM.md          # Del 2 tillägg och krav
├── examples/
│   └── example_job_package.json        # Exempel på komplett job package
├── tests/
│   ├── test_schema_validation.py       # Schema-validering med jsonschema
│   └── test_live_validation.py         # Live E2E-validering
└── README.md                           # Denna fil
```

### Output (planerad produktion)

När motorn körs produceras:

1. **BacklinkJobPackage** (JSON) – Komplett kontext och instruktioner
2. **Backlink-artikel** (MD/HTML) – Typiskt ≥900 ord
3. **Next-A1 extensions** (JSON) – Intent, SERP-research, QC, LSI-data
4. **QC-rapport** (JSON) – Kvalitetsbedömning och AutoFix-historik
5. **Execution log** (JSON) – State machine-spårning

## 📦 Installation

### Krav

- Python 3.8+
- pip

### Setup

```bash
# Klona repot
git clone https://github.com/robwestz/BACOWR.git
cd BACOWR

# Installera beroenden
pip install -r requirements.txt
```

## 🧪 Tester

Projektet har två nivåer av validering enligt NEXT-A1-ENGINE-ADDENDUM.md:

### 1. Schema-validering (obligatorisk)

Validerar att exempel-JSON följer schemat:

```bash
python tests/test_schema_validation.py
```

**Vad testet gör:**
- Läser `backlink_job_package.schema.json`
- Läser `examples/example_job_package.json`
- Validerar med `jsonschema.validate()`
- Säkerställer att alla obligatoriska fält finns

**Förväntat resultat:**
```
[INFO] 🔍 Starting JSON Schema Validation
[SUCCESS] ✅ Schema loaded: BacklinkJobPackage
[SUCCESS] ✅ Example loaded: Job ID = example-job-001
[INFO] 🔬 Validating against schema...
[SUCCESS] ✅ VALIDATION PASSED!
[SUCCESS] ✅ TEST PASSED
```

### 2. Live validering (E2E light)

Validerar datakvalitet och konsistens:

```bash
python tests/test_live_validation.py
```

**Vad testet gör:**
- Läser schema och job package
- Validerar alla obligatoriska fält finns
- Kontrollerar språk-konsistens (sv/en/etc)
- Verifierar intent alignment
- Kontrollerar generation constraints (ordkrav, etc)

**Förväntat resultat:**
```
[INFO] 🚀 Startar BACOWR Live Test
[SUCCESS] ✅ Alla obligatoriska fält finns!
[CHECK] ✅ Språk konsistent: sv
[CHECK] ✅ Intent alignment: aligned
[CHECK] ✅ Ordkrav uppfyllt: 900 ord
[SUCCESS] 🎉 Alla tester godkända!
```

### Köra alla tester

```bash
# Från projektroten
python tests/test_schema_validation.py && python tests/test_live_validation.py
```

## 📖 Dokumentation

### Specifikationer

1. **[backlink_engine_ideal_flow.md](backlink_engine_ideal_flow.md)**
   - Detaljerat idealflöde från input till output
   - Beskriver alla profileringar och extensions

2. **[NEXT-A1-ENGINE-ADDENDUM.md](NEXT-A1-ENGINE-ADDENDUM.md)**
   - Formella krav för Del 2
   - QC & AutoFixOnce specifikation
   - State machine krav
   - Acceptance-kriterier

3. **[next-a1-spec.json](next-a1-spec.json)**
   - Komplett Next-A1 specifikation
   - Intent-klassificering
   - Bridge-typer
   - Länkplacering och ankarpolicies

### JSON Schema

**Single Source of Truth:** `backlink_job_package.schema.json`

Detta schema definierar det bindande kontraktet för BacklinkJobPackage.

**Obligatoriska toppnivå-fält:**

- `job_meta` – Metadata (job_id, created_at, spec_version)
- `input_minimal` – Tre inputs (publisher, target, anchor)
- `publisher_profile` – Profilerad publishersida
- `target_profile` – Profilerad målsida
- `anchor_profile` – Ankaranalys
- `serp_research_extension` – SERP-research (main + cluster queries)
- `intent_extension` – Intent-modellering och alignment
- `generation_constraints` – Generationspolicies (språk, ordkrav, etc)

## 🎯 Acceptance-kriterier

Motorn anses stabil när (per NEXT-A1-ENGINE-ADDENDUM.md § 7):

- [x] `test_schema_validation.py` passerar
- [x] `test_live_validation.py` passerar
- [ ] QC-system implementerat med AutoFixOnce
- [ ] State machine loggar till `execution_log`
- [ ] Minst 1–2 manuella produktionskörningar genomförda
- [ ] README beskriver hur man kör och tolkar output

### Nuvarande status

**✅ Specifikation:** Komplett
**🚧 Implementation:** Pågående
**✅ Tester:** Schema-validering klar

## 🔧 Användning (planerad)

### CLI

```bash
python main.py \
  --publisher example-publisher.com \
  --target https://client.com/product-x \
  --anchor "bästa valet för [tema]" \
  --output ./storage/output/
```

### Python API

```python
from bacowr import run_backlink_job

result = run_backlink_job(
    publisher_domain="example-publisher.com",
    target_url="https://client.com/product-x",
    anchor_text="bästa valet för [tema]"
)

# result innehåller:
# - job_package (dict)
# - article (str)
# - qc_report (dict)
```

## 🛡️ QC & AutoFixOnce (planerad)

Quality Control-systemet har två nivåer:

### 1. Automatisk korrigering (AutoFixOnce)

Vid **mindre avvikelser** görs exakt en automatisk fix:

- Flytta länk inom samma sektion
- Justera ankartyp (exact → brand/generic)
- Injicera saknade LSI
- Lägga till compliance-disclaimers

Alla ändringar loggas i `qc_extension`.

### 2. Manuell signoff

Vid **allvarliga avvikelser** blockeras automatisk fix:

- Intent alignment: "off"
- Trust-källor: 0 godkända
- Konkurrent-detektion i content
- Reglerad vertikal utan disclaimers
- Ankar-risk: "high"

Sätter `human_signoff_required: true` i output.

## 📊 State Machine (planerad)

Varje körning går genom:

```
RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                                ↓
                              RESCUE (max 1 gång)
                                ↓
                              ABORT (vid loop/deadlock)
```

**Loop-skydd:** Om RESCUE inte ändrar payload → ABORT

**Spårbarhet:** Alla state-övergångar loggas i `execution_log.json`

## 🤝 Integration

Motorn är utformad för att vara **integrationsklar utan hårda beroenden**.

### Användningsfall

- **MCP-verktyg** (Model Context Protocol)
- **Batch-processer** för stora uppdrag
- **GUI/Dashboard** för manuell körning
- **CI/CD pipelines** för automatisk content-generering

Inga antaganden görs om externa orchestrators.

## 📝 Exempel

Se `examples/example_job_package.json` för ett komplett exempel på BacklinkJobPackage.

Exempel visar:
- Svensk publisher (consumer_magazine tone)
- Kommersiell målsida (Product X)
- Partial anchor med commercial_research intent
- Aligned intent mellan SERP, target och publisher
- Pivot bridge-type rekommenderad

## 🔬 Utveckling

### Lägg till nya tester

```bash
# Skapa ny testfil i tests/
touch tests/test_my_feature.py

# Kör alla tester
python -m pytest tests/
```

### Validera schema-ändringar

När du ändrar `backlink_job_package.schema.json`:

1. Uppdatera exempel i `examples/`
2. Kör `test_schema_validation.py`
3. Kör `test_live_validation.py`
4. Verifiera att båda passerar

## 📄 Licens

(Lägg till din licens här)

## 👥 Bidrag

(Lägg till bidragsinstruktioner här)

## 📞 Support

För frågor eller buggrapporter, öppna en issue i GitHub-repot.

---

**Version:** 1.0
**Status:** Specification Complete, Implementation In Progress
**Last Updated:** 2025-11-07
