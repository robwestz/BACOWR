# BACOWR Offline Preflight Check

## Snabbstart

Detta är den **tvådelade versionen** där du kör preflight offline och sedan manuellt använder resultatet i ChatGPT/Claude för att generera artikeln.

### Steg 1: Kör Preflight (Offline)

```bash
python run_preflight.py
```

Scriptet kommer fråga efter:
- **Ankartext**: t.ex. "bästa mobilabonnemang"
- **Målsida (URL)**: t.ex. "https://example.com/erbjudanden/mobil"
- **Publiceringsdomän**: t.ex. "blogg.exempelsite.se"

### Steg 2: Kopiera Output

Scriptet skapar två filer i `storage/preflight_output/`:

1. **JSON-fil** (`job_XXXXXXXX_preflight.json`) - Komplett job package data
2. **TXT-fil** (`job_XXXXXXXX_preflight.txt`) - Formatterad text för LLM

Öppna TXT-filen och kopiera hela innehållet.

### Steg 3: Kör Manuellt i ChatGPT/Claude

1. Öppna ChatGPT eller Claude
2. Klistra in innehållet från TXT-filen
3. LLM:en kommer att generera en artikel baserat på preflight-resultatet
4. Artikeln följer automatiskt alla krav (bridge type, språk, anchor placement, etc.)

---

## Exempel: Komplett Workflow

```bash
$ python run_preflight.py
================================================================================
BACOWR OFFLINE PREFLIGHT CHECK
================================================================================

Detta script kör endast preflight-analys utan API-anrop.
Du får ut en textfil som du kan köra manuellt i ChatGPT/Claude.

Mata in följande information:

Ankartext: bästa kreditkort
Målsida (URL): https://example.com/kreditkort
Publiceringsdomän: ekonomibloggen.se

--------------------------------------------------------------------------------
Kör preflight-analys...
--------------------------------------------------------------------------------

✓ Preflight-analys klar!

================================================================================
OUTPUT FILER
================================================================================

JSON (komplett):  /home/user/BACOWR/storage/preflight_output/job_20251120_135202_abc123_preflight.json
TEXT (för LLM):   /home/user/BACOWR/storage/preflight_output/job_20251120_135202_abc123_preflight.txt

================================================================================
KLART!
================================================================================

Nästa steg:
1. Öppna filen: /home/user/BACOWR/storage/preflight_output/job_20251120_135202_abc123_preflight.txt
2. Kopiera innehållet
3. Klistra in i ChatGPT eller Claude
4. Låt AI:n generera artikeln baserat på preflight-resultatet
```

---

## Vad Innehåller Preflight-Resultatet?

TXT-filen innehåller:

### 1. Job Metadata
- Job ID
- Skapad timestamp
- Spec version
- Mode (mock/real)

### 2. Input (Minimal)
- Publiceringsdomän
- Målsida (URL)
- Ankartext

### 3. Publisher Profil
- Domän
- Språk
- Topic focus
- Ton (tone_class)

### 4. Target Profil
- URL
- HTTP status
- Språk
- Titel
- Kärnentiteter
- Ämnen
- Kärnerbjudande

### 5. Ankartext Profil
- Föreslagen text
- Type hint
- LLM-klassificering
- LLM intent hint

### 6. SERP Research
- Huvudfråga
- Klusterfrågor
- Rationale
- Data confidence

### 7. Intent Extension (VIKTIGT!)
- SERP Intent (primär & sekundär)
- Target Page Intent
- Anchor Implied Intent
- Publisher Role Intent
- **Intent Alignment** (anchor vs SERP, target vs SERP, etc.)
- **Rekommenderad Bridge Type** (strong/pivot/wrapper)
- Artikelvinkel
- Nödvändiga subämnen
- Förbjudna vinklar

### 8. Generation Constraints
- Språk
- Min word count
- Max anchor usages
- Anchor policy

### 9. Instruktioner för LLM
Detaljerade instruktioner som talar om för ChatGPT/Claude exakt vad som ska göras.

---

## Fördelar med Offline-Läget

✅ **Ingen API-integration krävs** - Fungerar utan externa dependencies
✅ **Full kontroll** - Du ser exakt vad som skickas till LLM:en
✅ **Flexibelt** - Fungerar med vilken LLM som helst (ChatGPT, Claude, etc.)
✅ **Debugging** - Enkelt att felsöka eftersom du ser varje steg
✅ **Kostnadskontroll** - Du bestämmer när/om LLM:en ska köras

---

## Tekniska Detaljer

### Mode: Mock
Nuvarande version kör i "mock mode" vilket betyder:
- Ingen riktiga API-anrop till SERP
- Mock data för publisher/target profiling
- Perfekt för testing och demo

### Nästa Steg (Real Mode)
För produktion kan scriptet utökas till att göra:
- Riktig SERP research via API
- Riktig page profiling
- Riktig intent analysis

Men strukturen och outputen förblir densamma!

---

## Felsökning

### Problem: "ModuleNotFoundError"
**Lösning**: Kör `pip install -r requirements.txt` först

### Problem: Filerna skapas inte
**Kontrollera**: Att mappen `storage/preflight_output/` skapades
**Lösning**: Scriptet skapar mappen automatiskt, men kontrollera filrättigheter

### Problem: Output ser fel ut
**Kontrollera**: TXT-filen med `cat storage/preflight_output/*.txt | tail -1`
**Lösning**: Om JSON-strukturen är fel, kontrollera `build_mock_job_package()` funktionen

---

## Demo-Exempel för Chefer

### Scenario: Visa Upp Systemet Imorgon

1. **Kör preflight** för ett exempel:
   ```bash
   python run_preflight.py
   ```

2. **Input-exempel**:
   - Ankartext: "bästa bolån"
   - Målsida: "https://example.com/bolan"
   - Publiceringsdomän: "ekonomibloggen.se"

3. **Visa TXT-filen** - Öppna och visa hur strukturerad datan är

4. **Copy-paste till Claude** - Demonstrera hur det fungerar live

5. **Resultat** - Claude genererar en artikel som:
   - Följer rätt bridge type
   - Har rätt språk
   - Placerar anchor korrekt
   - Matchar publisher-ton
   - Täcker alla required subtopics

**Totaltid**: < 5 minuter från start till färdig artikel!

---

## Nästa Fas: API-Integration

När du är redo för API-integration kan du:

1. Byta `mock=True` till `mock=False` i `build_mock_job_package()`
2. Lägga till riktiga API-keys för SERP
3. Använda `src/core_api.py` istället för `run_preflight.py`
4. Automatisera hela flödet end-to-end

Men den tvådelade versionen fungerar redan NU! 🚀

---

## Support

För frågor eller problem:
- Kontrollera loggarna i `storage/preflight_output/`
- Kolla JSON-strukturen för debugging
- Verifiera att input-data är korrekt formaterad
