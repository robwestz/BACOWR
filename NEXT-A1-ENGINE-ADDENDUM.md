# Tillägg till Del 2 – BacklinkContent Engine (Next-A1)

**Syfte:**
Detta tillägg formaliserar verifiering, robusthet och integrationsberedskap för BacklinkContent Engine efter första produktionsimplementeringen. Det ersätter spridda ad hoc-instruktioner och definierar de minimikrav som måste vara uppfyllda för att motorn ska betraktas som stabil, testbar och redo att användas av externa system.

Fokus:

* inga arkitekturändringar,
* inga MCP-beroenden,
* endast förstärkning av befintlig Next-A1-implementation.

---

## 1. Kontraktsnivå – BacklinkJobPackage & Extensions

Motorn ska fortsatt utgå från tre-input-paradigmet:

* `publisher_domain`
* `target_url`
* `anchor_text`

och producera:

1. `BacklinkJobPackage` (JSON)
2. Backlink-artikel (MD/HTML, typiskt ≥ 900 ord)
3. `Next-A1 extensions` (JSON)
4. `QC-rapport` (JSON)
5. `Execution log` (JSON)

**Krav (bindande):**

* `backlink_job_package.schema.json` är **single source of truth**.

* Minst följande toppnivå-fält ska alltid finnas i genererat job package:

  * `job_meta`
  * `input_minimal`
  * `publisher_profile`
  * `target_profile`
  * `anchor_profile`
  * `serp_research_extension`
  * `intent_extension`
  * `generation_constraints`

* Eventuella ytterligare fält ska:

  * vara dokumenterade,
  * inte bryta kompatibilitet med schema.

All generering, QC och writer-logik ska läsa/skriva utifrån detta kontrakt.

---

## 2. Schema- och strukturvalidering

För att säkerställa att motorn är deterministisk och kontraktsäker gäller:

### 2.1. JSON Schema-validering (obligatorisk)

* Ett Python-baserat test ska finnas under `tests/` som:

  1. Läser `backlink_job_package.schema.json`.
  2. Läser minst ett exempel-JSON (t.ex. `examples/example_job_package.json`).
  3. Validerar med `jsonschema.validate(instance=data, schema=schema)`.

* Testet ska:

  * fallera med exit code ≠ 0 vid ogiltig struktur,
  * köras i CI (om/när CI läggs till),
  * vara dokumenterat i README under "Tests".

### 2.2. Live Generation Validation (E2E light)

Ett kompletterande test (tex `tests/test_live_validation.py`) ska:

1. Trigga den riktiga pipelinen med mock-läge (ingen extern SERP/LLM krävs).
2. Skapa ett faktiskt `*_job_package.json`.
3. Validera detta mot samma schema.
4. Säkerställa minst:

   * språkfält konsistent (t.ex. `sv`),
   * `intent_extension.overall` är ifyllt,
   * `generation_constraints.min_word_count` finns,
   * nödvändiga profiler finns (publisher/target/anchor).

Detta test är en miniminivå för att säkerställa att implementation och schema inte glidit isär.

---

## 3. QC & AutoFixOnce – kodifierad nivå

QC-systemet i `config/thresholds.yaml` + `config/policies.yaml` ska:

1. Vara **enda källan** till:

   * LSI-krav (6–10, radius ±2 meningar),
   * trust-krav (T1–T4, minst 1 godkänd källa),
   * ankarrisk-regler,
   * placeringsregler (ej H1/H2, mittsektion),
   * compliance (disclaimers för reglerade vertikaler).

2. Tillämpas i `QualityController` på det genererade paketet + texten.

3. AutoFixOnce:

   * Vid mindre avvikelser får systemet göra **exakt en** automatisk korrigering, t.ex.:

     * flytta länk inom samma sektion,
     * justera ankartyp (t.ex. exact → brand/generic),
     * injicera saknade LSI (inom policy),
     * lägga till nödvändig disclaimer.

   * Alla ändringar ska:

     * loggas i `qc_extension` (t.ex. `autofix_done: true`, `notes`),
     * avspeglas i `execution_log`.

   * Vid allvarliga avvikelser (intent "off", trust 0, konkurrent-detektion, felaktig branschhantering):

     * **ingen aggressiv autofix**,
     * QC rapporterar fel och markerar för manuell åtgärd (ex. `status: "BLOCKED"` eller `human_signoff_required: true`).

---

## 4. State Machine – determinism & spårbarhet

Den interna state machine-implementeringen ska ses som normativ:

* Stater:

  * `RECEIVE`
  * `PREFLIGHT`
  * `WRITE`
  * `QC`
  * `DELIVER`
  * `RESCUE` (valfritt)
  * `ABORT`

**Krav:**

1. Varje körning ska:

   * få ett unikt `job_id`,
   * få en `execution_log`-fil i `storage/output/` som loggar state-övergångar.

2. Loop-skydd:

   * Om samma payload genereras i RESCUE/AutoFix-steget utan ändring:

     * bryt och sätt status till `ABORT` eller `BLOCKED`.

3. `RESCUE` + AutoFixOnce:

   * Får triggas max en gång.
   * Därefter ska flödet gå till `QC` → `DELIVER` eller `ABORT`.

4. `human_signoff_required: true` ska sättas när:

   * `anchor_risk == "high"`,
   * inga godkända trust-källor hittas,
   * compliance-disclaimers saknas i reglerad vertikal,
   * `intent_alignment.overall == "off"`.

Detta gör motorn förutsägbar och loggbar utan extra systems.

---

## 5. PageProfile & SERP-datamodell – återanvändbar grund

För att förbereda motorn för framtida verktyg (utan att rikta om fokus):

**PageProfile (redan implementerat):**

* Ska användas konsekvent för:

  * `target_profile`
  * `publisher_profile`
* Bör minst innehålla:

  * title, meta, H1-H3,
  * extraherad huvudtext,
  * språk,
  * centrala entiteter/ämnen.

**SERP-datamodell / `serp_research_extension`:**

* Ska innehålla:

  * queries (main + cluster),
  * intents,
  * top-urls-sample,
  * entiteter/subtopics,
  * derived `required_subtopics` och `forbidden_angles` där det är relevant.

Denna struktur ska vara stabil nog att:

* användas för intentmodellering i motorn,
* återanvändas i framtida semantiska verktyg & SEO-analytics
  utan att behöva bryta existerande kod.

---

## 6. Offentliga entrypoints – integrationsredo utan hårda beroenden

Motorn ska vara enkel att anropa utifrån, utan att anta MCP eller viss orkestrator.

**Minst en dokumenterad entrypoint krävs:**

1. CLI (redan finns via `main.py`):

   * Exempel:

     ```bash
     python main.py \
       --publisher example-publisher.com \
       --target https://client.com/product-x \
       --anchor "bästa valet för [tema]" \
       --output ./storage/output/
     ```

2. Intern Python-funktion (rekommenderas):

   I t.ex. `src/api.py`:

   ```python
   def run_backlink_job(publisher_domain: str, target_url: str, anchor_text: str):
       """
       Kör full Next-A1-pipeline.
       Returnerar:
         - job_package (dict)
         - article (str)
         - qc_report (dict)
       """
       ...
   ```

Detta gör att:

* andra system (inkl. MCP-projektet, framtida GUI, batch-processer)
  kan använda motorn som en modul utan att ändra dess internlogik.

---

## 7. Acceptance-kriterier för Del 2 (med tillägg)

Motorn kan betraktas som stabil när följande uppfylls:

1. **`tests/test_schema_validation.py`:**

   * validerar exempel-BacklinkJobPackage mot schemat,
   * passerar.

2. **Ett E2E-test:**

   * kör full pipeline i mock-läge,
   * genererar output-filer,
   * validerar genererat job_package mot schemat,
   * passerar.

3. **QC:**

   * flaggar fel vid tydliga brott mot Next-A1,
   * gör max en AutoFixOnce,
   * loggar beslut i QC + execution_log.

4. **Minst 1–2 manuella körningar:**

   * på skarpa men ofarliga case
   * visar:

     * rimlig intent-modellering,
     * vettig bridge_type,
     * korrekt länkplacering,
     * rimliga LSI,
     * inga uppenbara policybrott.

5. **README:**

   * beskriver:

     * hur man kör,
     * vilken output som förväntas,
     * hur QC ska tolkas.

När allt ovan är uppfyllt är Del 2 + detta tillägg en hållbar, produktionsklar motor, redo att stå själv – och redo att kopplas på en större plattform när du väljer det.

---

## Implementation Status

### ✅ Implemented

- [x] BacklinkJobPackage JSON Schema definition
- [x] Example job package with complete structure
- [x] Basic live validation test

### 🚧 In Progress

- [ ] Full test suite under `tests/`
- [ ] Schema validation with jsonschema library
- [ ] QC system configuration files
- [ ] State machine implementation
- [ ] CLI entrypoint (`main.py`)
- [ ] Comprehensive README

### 📋 Planned

- [ ] AutoFixOnce implementation
- [ ] Execution logging system
- [ ] Integration API (`src/api.py`)
- [ ] CI/CD pipeline configuration
- [ ] Production deployment guidelines

---

**Version:** 1.0
**Last Updated:** 2025-11-07
**Status:** Specification Complete, Implementation In Progress
