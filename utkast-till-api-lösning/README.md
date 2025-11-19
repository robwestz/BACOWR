
# SERP Brief API (FastAPI)

Ett lättviktigt API som hämtar SERP-resultat + metadata, härleder intent & policy och paketerar allt till **writer-brief** enligt din A1‑spec.

## 🚀 Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# (valfritt) sätt API-nyckel
echo 'API_KEY=devkey' > .env

uvicorn app.main:app --reload --port 8080
```

Öppna docs: http://localhost:8080/docs  
OpenAPI JSON: http://localhost:8080/openapi.json

> **Hoppscotch**: Importera OpenAPI (från fil eller URL) och kör kollektionen direkt. Se Hoppscotch-dokumentation: *Import from OpenAPI*.

## 🔑 Autentisering

Skicka header `X-API-Key: <din nyckel>` om `API_KEY` är satt i `.env`.

## 🔧 Konfiguration (.env)

```env
# Säkerhet
API_KEY=devkey

# SERP-provider (mock | serpapi | google_cse | selenium)
SERP_PROVIDER=mock
SERPAPI_KEY=

# Google Custom Search
GOOGLE_CSE_KEY=
GOOGLE_CSE_CX=

# Webhook‑signering
WEBHOOK_SECRET=
```

## 🔌 Endpoints

### 1) `POST /preflight/target-profile`
Input: `{ "target_url": "https://exempel.se/sida" }`  
Output: `TargetProfile` med titel, meta description, H1, m.m.

### 2) `POST /preflight/publisher-profile`
Input: `{ "publisher_domain": "example-publisher.com" }`  
Output: `PublisherProfile` (ton/roll kan förfinas).

### 3) `POST /preflight/anchor-profile`
Input: `{ "anchor_text": "bästa X" }`  
Output: `AnchorProfile` med enkel typning + intent-hint.

### 4) `POST /serp/research`
Input:
```json
{ "queries": ["huvudquery", "kluster 1", "kluster 2"], "provider": "mock", "fetch_metadata": true }
```
Output: `SERPResearch` med topp-10 för varje query (mock/live beroende på provider).

### 5) `POST /derive/intent-profile`
Input: `{ serp_research, target_profile, anchor_profile, publisher_profile }`  
Output: `IntentProfile` (dominerande intent, alignment, rekommenderad bridge_type).

### 6) `POST /policies/apply`
Input: `{ target_profile, publisher_profile, anchor_profile, intent_profile, serp_research }`  
Output: `WriterBrief` (A1: links_extension, qc_extension, intent_extension + serp_research_extension).

### 7) `POST /handoff/writer-brief`
Som (6) men **pushar** till `webhook_url` om den anges:  
```json
{
  "...": "...",
  "webhook_url": "https://app.dittsystem.se/hooks/brief",
  "correlation_id": "abc-123"
}
```

HMAC‑SHA256 signatur i header: `X-Signature` om `WEBHOOK_SECRET` är satt.

### Test-webhook
`POST /webhooks/echo` – enkel mottagare för lokal testning.

## 🧩 Koppling till ditt idealflöde (A1)

- **Input-minimum**: `publisher_domain + target_url + anchor_text`. Upstream bygger `target_profile`, `publisher_profile`, `anchor_profile`.  → *backlink_engine_ideal_flow.md* beskriver detta flöde.  
- **SERP preflight**: huvud + kluster, topp-10, `required_subtopics`, `page_archetypes` → `SERPResearch`.  
- **Intent/bridge**: sammanvägning till `IntentProfile` och A1‑regler för strong/pivot/wrapper.  
- **Policy/QC/LSI/Trust**: kapslat som `links_extension`, `qc_extension`, `intent_extension` i `WriterBrief`.

## 🔄 Hoppscotch

- Importera **OpenAPI** från `http://localhost:8080/openapi.json` (*Import from OpenAPI*)  
- Alternativt: skapa en kollektion med bas‑URL `http://localhost:8080` och lägg till endpoints ovan.

## 🧠 Noteringar

- `SERP_PROVIDER=mock` ger deterministiska exempel. Byt till `serpapi` eller `google_cse` för riktiga sökresultat.
- För Selenium: implementera provider i `app/serp_providers.py` (kommentar i filen) med headless Chrome + anti‑bot‑hänsyn.
- Metadata‑hämtning sker parallellt med `httpx` och parse:as med `BeautifulSoup`.
- Intent/QC/policy innehåller **enkla heuristiker** – byt till LLM/logik efter dina A1‑regler allt eftersom.
