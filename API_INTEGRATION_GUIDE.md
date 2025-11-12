# API INTEGRATION GUIDE
## Hur ChatGPT:s API-förslag integreras med BACOWR-systemet

---

## ÖVERSIKT

Detta dokument beskriver hur **ChatGPT Pro's FastAPI-förslag** (`utkast-till-api-lösning`) ska integreras med **BACOWR-systemets kärnpipeline** (`IMPLEMENTATION_SPEC.md` + `BUILDER_PROMPT.md`).

### Två strategier finns:

1. **STRATEGI A: Hybrid (Rekommenderat för flexibilitet)**
   - Bygg ChatGPT:s API som separata microservices
   - Kärnpipelinen använder API:erna via HTTP
   - Möjliggör testning med Hoppscotch
   - Tillåter att köra steg separat eller tillsammans

2. **STRATEGI B: Monolitisk (Rekommenderat för enkelhet)**
   - Importera ChatGPT:s moduler direkt i kärnpipelinen
   - Allt körs i samma process
   - Enklare deployment, snabbare exekvering
   - API kan byggas senare som ett lager ovanpå

---

## CHATGPT:S API-FÖRSLAG - SAMMANFATTNING

### Vad finns:
```
utkast-till-api-lösning/
├── app/
│   ├── models.py           # Pydantic models (TargetProfile, PublisherProfile, etc.)
│   ├── config.py           # Settings (API keys, SERP provider)
│   ├── extract.py          # HTML scraping & metadata extraction
│   ├── serp_providers.py   # SERP fetching (mock, SerpAPI, Google CSE)
│   ├── intent_policy.py    # Intent modeling heuristics
│   ├── policy.py           # Extensions builder (links, qc, intent)
│   ├── utils.py            # Helper functions
│   └── webhooks.py         # Webhook posting with HMAC
├── README.md
└── requirements.txt
```

### Vad saknas:
- **`app/main.py`** - FastAPI app med endpoints ❌
- **LLM integration** - För djupare analys (ChatGPT använder heuristiker) ❌
- **Content generation** - Writer/article generation ❌
- **QC system** - Quality control validation ❌
- **State machine** - Pipeline orchestration ❌

### Endpoints som ska finnas (enligt README):
1. `POST /preflight/target-profile` - Profilera målsida
2. `POST /preflight/publisher-profile` - Profilera publisher
3. `POST /preflight/anchor-profile` - Klassificera ankare
4. `POST /serp/research` - Hämta SERP-resultat
5. `POST /derive/intent-profile` - Härled intent från alla källor
6. `POST /policies/apply` - Applicera A1-policies
7. `POST /handoff/writer-brief` - Skapa komplett brief (+ optional webhook)

---

## STRATEGI A: HYBRID INTEGRATION (Rekommenderat för utveckling & testning)

### Arkitektur:
```
┌─────────────────────────────────────────┐
│   BACOWR Core Pipeline (main.py)        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  1. Receive Input (3 fält)         │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  2. Call Preflight API             │ │◄─────┐
│  │     - POST /preflight/target       │ │      │
│  │     - POST /preflight/publisher    │ │      │
│  │     - POST /preflight/anchor       │ │      │
│  └───────────┬────────────────────────┘ │      │
│              ↓                           │      │
│  ┌────────────────────────────────────┐ │      │
│  │  3. Call SERP API                  │ │      │
│  │     - POST /serp/research          │ │      │
│  └───────────┬────────────────────────┘ │      │
│              ↓                           │      │
│  ┌────────────────────────────────────┐ │      │
│  │  4. Call Intent API                │ │      │  FastAPI Microservice
│  │     - POST /derive/intent-profile  │ │      │  (Port 8080)
│  └───────────┬────────────────────────┘ │      │
│              ↓                           │      │  ┌──────────────────┐
│  ┌────────────────────────────────────┐ │      └──┤  Preflight API   │
│  │  5. Generate Content (Local LLM)   │ │         ├──────────────────┤
│  │     - Writer with Claude           │ │         │  SERP API        │
│  └───────────┬────────────────────────┘ │         ├──────────────────┤
│              ↓                           │         │  Intent API      │
│  ┌────────────────────────────────────┐ │         ├──────────────────┤
│  │  6. QC & AutoFix (Local)           │ │         │  Policy API      │
│  └───────────┬────────────────────────┘ │         └──────────────────┘
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  7. Deliver Output                 │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Implementation:

#### Steg 1: Komplettera ChatGPT:s API med `main.py`

**Fil:** `utkast-till-api-lösning/app/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import APIKeyHeader
from .models import (
    TargetRequest, TargetProfile,
    PublisherRequest, PublisherProfile,
    AnchorRequest, AnchorProfile,
    SERPRequest, SERPResearch, SERPSet, TopResult,
    IntentProfile, IntentAlignment, IntentNotes,
    PolicyApplyRequest, WriterBrief,
    HandoffRequest
)
from .config import settings
from .extract import fetch_metadata, _guess_page_type
from .serp_providers import search_queries
from .intent_policy import (
    classify_intent_from_query,
    guess_intent_from_snippets,
    derive_required_subtopics,
    compute_alignment,
    recommend_bridge_type
)
from .policy import build_extensions
from .webhooks import post_with_signature
from .utils import detect_language_from_text

app = FastAPI(
    title="BACOWR Preflight API",
    version="0.1.0",
    description="Upstream services for BACOWR backlink content generation"
)

# Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def verify_api_key(api_key: str = Depends(api_key_header)):
    if settings.API_KEY and api_key != settings.API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

# ----- ENDPOINTS -----

@app.post("/preflight/target-profile", response_model=TargetProfile)
async def profile_target(req: TargetRequest, _: str = Depends(verify_api_key)):
    """Fetch and profile target URL"""
    url_str = str(req.target_url)
    meta = await fetch_metadata([url_str])
    data = meta.get(url_str, {})

    # TODO: Add LLM analysis for core_entities, core_topics, core_offer, candidate_main_queries
    # For now, use basic extraction

    return TargetProfile(
        url=req.target_url,
        http_status=data.get("http_status"),
        title=data.get("title"),
        meta_description=data.get("meta_description"),
        h1=data.get("h1"),
        h2_h3_sample=data.get("h2_h3_sample", []),
        main_content_excerpt=data.get("excerpt"),
        detected_language=detect_language_from_text(data.get("excerpt", "")),
        core_entities=[],  # TODO: LLM extraction
        core_topics=[],    # TODO: LLM extraction
        core_offer=None,   # TODO: LLM analysis
        candidate_main_queries=[]  # TODO: LLM generation
    )

@app.post("/preflight/publisher-profile", response_model=PublisherProfile)
async def profile_publisher(req: PublisherRequest, _: str = Depends(verify_api_key)):
    """Fetch and profile publisher domain"""
    # TODO: Crawl homepage, about page, sample articles
    # TODO: LLM analysis for tone_class, topic_focus, audience

    return PublisherProfile(
        domain=req.publisher_domain,
        sample_urls=req.sample_urls if req.sample_urls else [],
        about_excerpt=req.about_excerpt,
        detected_language="sv",  # TODO: detect
        topic_focus=[],   # TODO: LLM analysis
        audience=None,    # TODO: LLM analysis
        tone_class=None,  # TODO: LLM classification
        allowed_commerciality=None,
        brand_safety_notes=None
    )

@app.post("/preflight/anchor-profile", response_model=AnchorProfile)
async def profile_anchor(req: AnchorRequest, _: str = Depends(verify_api_key)):
    """Classify anchor text"""
    # TODO: LLM classification
    # For now, use heuristics

    anchor_lower = req.anchor_text.lower()

    # Simple type classification
    if any(word in anchor_lower for word in ["bästa", "bäst", "topp", "ledande"]):
        classified_type = "partial"
    elif any(word in anchor_lower for word in ["köp", "beställ", "här"]):
        classified_type = "generic"
    else:
        classified_type = "partial"

    # Simple intent hint
    if any(word in anchor_lower for word in ["köp", "pris", "erbjudande"]):
        intent_hint = "transactional"
    elif any(word in anchor_lower for word in ["bästa", "jämför", "alternativ"]):
        intent_hint = "commercial_research"
    else:
        intent_hint = "info_primary"

    return AnchorProfile(
        proposed_text=req.anchor_text,
        type_hint=req.type_hint,
        llm_classified_type=classified_type,
        llm_intent_hint=intent_hint
    )

@app.post("/serp/research", response_model=SERPResearch)
async def research_serp(req: SERPRequest, _: str = Depends(verify_api_key)):
    """Fetch and analyze SERP results"""

    # Fetch SERP results
    raw_results = await search_queries(req.queries, num=10)

    # Build SERPSet for each query
    serp_sets = []
    for query in req.queries:
        results = raw_results.get(query, [])

        # Classify intent
        dominant_intent = classify_intent_from_query(query)

        # If fetch_metadata, get page metadata
        if req.fetch_metadata and results:
            urls = [r["url"] for r in results if r.get("url")]
            metadata = await fetch_metadata(urls[:10])
        else:
            metadata = {}

        # Build TopResult list
        top_results = []
        for r in results:
            url = r.get("url")
            meta = metadata.get(url, {})

            # Guess page type
            page_type = _guess_page_type(url, r.get("title", ""))

            top_results.append(TopResult(
                rank=r.get("rank", 0),
                url=url,
                title=r.get("title") or meta.get("title"),
                snippet=r.get("snippet"),
                detected_page_type=page_type,
                key_entities=[],  # TODO: LLM extraction
                key_subtopics=[]  # TODO: LLM extraction
            ))

        # Derive required subtopics from snippets
        snippets = [r.get("snippet", "") for r in results if r.get("snippet")]
        required_subtopics = derive_required_subtopics(results, top_k=5)

        serp_sets.append(SERPSet(
            query=query,
            dominant_intent=dominant_intent,
            secondary_intents=[],
            page_archetypes=[],  # TODO: aggregate from top_results
            required_subtopics=required_subtopics,
            top_results=top_results
        ))

    return SERPResearch(
        main_query=req.queries[0] if req.queries else "",
        cluster_queries=req.queries[1:] if len(req.queries) > 1 else [],
        queries_rationale="Based on target profile and anchor",
        results=serp_sets,
        confidence="medium"
    )

@app.post("/derive/intent-profile", response_model=IntentProfile)
async def derive_intent(
    target_profile: TargetProfile,
    publisher_profile: PublisherProfile,
    anchor_profile: AnchorProfile,
    serp_research: SERPResearch,
    _: str = Depends(verify_api_key)
):
    """Derive intent profile from all inputs"""

    # Get primary SERP intent
    serp_intent_primary = serp_research.results[0].dominant_intent if serp_research.results else "info_primary"

    # Aggregate required subtopics
    required_subtopics_merged = []
    for serp_set in serp_research.results:
        required_subtopics_merged.extend(serp_set.required_subtopics)
    required_subtopics_merged = list(set(required_subtopics_merged))[:10]

    # Compute alignment
    anchor_intent = anchor_profile.llm_intent_hint or "info_primary"
    publisher_intent = publisher_profile.tone_class if publisher_profile.tone_class else "info_primary"

    # Map publisher tone_class to intent
    tone_to_intent = {
        "academic": "info_primary",
        "authority_public": "info_primary",
        "consumer_magazine": "commercial_research",
        "hobby_blog": "info_primary"
    }
    publisher_role_intent = tone_to_intent.get(publisher_intent, "info_primary")

    alignment = compute_alignment(
        anchor_intent,
        serp_intent_primary,
        target_profile.core_offer or "",
        publisher_role_intent
    )

    # Recommend bridge type
    bridge_type = recommend_bridge_type(alignment)

    return IntentProfile(
        serp_intent_primary=serp_intent_primary,
        serp_intent_secondary=[],
        target_page_intent=target_profile.core_offer,
        anchor_implied_intent=anchor_intent,
        publisher_role_intent=publisher_role_intent,
        required_subtopics_merged=required_subtopics_merged,
        forbidden_angles=[],  # TODO: LLM analysis
        alignment=alignment,
        recommended_bridge_type=bridge_type,
        recommended_article_angle=None,  # TODO: LLM generation
        rationale=f"Alignment: {alignment.overall}; Bridge: {bridge_type}"
    )

@app.post("/policies/apply", response_model=WriterBrief)
async def apply_policies(req: PolicyApplyRequest, _: str = Depends(verify_api_key)):
    """Apply A1 policies and build writer brief"""

    extensions = build_extensions(
        req.intent_profile,
        req.target_profile,
        req.publisher_profile,
        req.anchor_profile,
        req.serp_research
    )

    return WriterBrief(
        links_extension=extensions["links_extension"],
        qc_extension=extensions["qc_extension"],
        intent_extension=extensions["intent_extension"],
        serp_research_extension=req.serp_research
    )

@app.post("/handoff/writer-brief")
async def handoff_writer_brief(req: HandoffRequest, _: str = Depends(verify_api_key)):
    """Create writer brief and optionally push to webhook"""

    # Build writer brief
    extensions = build_extensions(
        req.intent_profile,
        req.target_profile,
        req.publisher_profile,
        req.anchor_profile,
        req.serp_research
    )

    brief = WriterBrief(
        links_extension=extensions["links_extension"],
        qc_extension=extensions["qc_extension"],
        intent_extension=extensions["intent_extension"],
        serp_research_extension=req.serp_research
    )

    # If webhook URL provided, push
    if req.webhook_url:
        payload = {
            "correlation_id": req.correlation_id,
            "writer_brief": brief.dict()
        }
        await post_with_signature(req.webhook_url, payload, settings.WEBHOOK_SECRET)

    return brief

@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.1.0"}
```

#### Steg 2: Uppdatera Core Pipeline för att använda API

**Fil:** `src/api.py` (modified)

```python
import httpx
from typing import Optional

class PreflightAPIClient:
    """Client for calling Preflight API services"""

    def __init__(self, base_url: str = "http://localhost:8080", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {}
        if api_key:
            self.headers["X-API-Key"] = api_key

    async def profile_target(self, target_url: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preflight/target-profile",
                json={"target_url": target_url},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def profile_publisher(self, publisher_domain: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preflight/publisher-profile",
                json={"publisher_domain": publisher_domain},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def profile_anchor(self, anchor_text: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/preflight/anchor-profile",
                json={"anchor_text": anchor_text},
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def research_serp(self, queries: list, provider: str = "mock") -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/serp/research",
                json={
                    "queries": queries,
                    "provider": provider,
                    "fetch_metadata": True
                },
                headers=self.headers,
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    async def derive_intent(
        self,
        target_profile: dict,
        publisher_profile: dict,
        anchor_profile: dict,
        serp_research: dict
    ) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/derive/intent-profile",
                json={
                    "target_profile": target_profile,
                    "publisher_profile": publisher_profile,
                    "anchor_profile": anchor_profile,
                    "serp_research": serp_research
                },
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

# Usage in state machine:
async def run_backlink_job_hybrid(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    preflight_api_url: str = "http://localhost:8080",
    preflight_api_key: Optional[str] = None
) -> dict:
    """Run backlink job using hybrid architecture (API + local pipeline)"""

    # Initialize API client
    api_client = PreflightAPIClient(preflight_api_url, preflight_api_key)

    # Call upstream APIs
    target_profile = await api_client.profile_target(target_url)
    publisher_profile = await api_client.profile_publisher(publisher_domain)
    anchor_profile = await api_client.profile_anchor(anchor_text)

    # Determine queries from target profile
    queries = target_profile.get("candidate_main_queries", [])
    if not queries:
        queries = [f"{anchor_text} {target_profile.get('title', '')}".strip()]

    serp_research = await api_client.research_serp(queries)
    intent_profile = await api_client.derive_intent(
        target_profile, publisher_profile, anchor_profile, serp_research
    )

    # Continue with local pipeline (content generation, QC, etc.)
    # ... rest of implementation using local LLM
```

### Deployment för Strategi A:

```bash
# Terminal 1: Start Preflight API
cd utkast-till-api-lösning
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Terminal 2: Run Core Pipeline
cd ..
python main.py \
  --publisher example.com \
  --target https://client.com/page \
  --anchor "bästa valet" \
  --preflight-api http://localhost:8080
```

---

## STRATEGI B: MONOLITISK INTEGRATION (Rekommenderat för enkelhet)

### Arkitektur:
```
┌─────────────────────────────────────────┐
│   BACOWR Core Pipeline (main.py)        │
│                                          │
│  ┌────────────────────────────────────┐ │
│  │  1. Receive Input (3 fält)         │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  2. Preflight (Import modules)     │ │
│  │     from preflight import extract  │ │
│  │     from preflight import serp     │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  3. Intent Modeling (Local)        │ │
│  │     from preflight import intent   │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  4. Content Generation (LLM)       │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  5. QC & AutoFix                   │ │
│  └───────────┬────────────────────────┘ │
│              ↓                           │
│  ┌────────────────────────────────────┐ │
│  │  6. Deliver Output                 │ │
│  └────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Implementation:

#### Steg 1: Kopiera ChatGPT:s moduler till Core Pipeline

```bash
cp -r utkast-till-api-lösning/app src/preflight
```

Filstruktur blir:
```
src/
├── preflight/          # <-- ChatGPT's modules
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── extract.py
│   ├── serp_providers.py
│   ├── intent_policy.py
│   ├── policy.py
│   ├── utils.py
│   └── webhooks.py
├── profile/
│   ├── target_profiler.py    # Uses preflight.extract
│   ├── publisher_profiler.py # Uses preflight.extract
│   └── anchor_profiler.py    # Uses preflight.intent_policy
├── serp/
│   └── research.py           # Uses preflight.serp_providers
├── intent/
│   └── modeler.py            # Uses preflight.intent_policy
...
```

#### Steg 2: Refactor Profilers att använda ChatGPT:s moduler

**Fil:** `src/profile/target_profiler.py`

```python
from ..preflight.extract import fetch_metadata
from ..preflight.utils import detect_language_from_text
from ..utils.llm import LLMClient

async def profile_target(url: str, llm_client: LLMClient) -> dict:
    """Profile target URL using preflight extraction + LLM analysis"""

    # Use ChatGPT's metadata fetcher
    meta = await fetch_metadata([url])
    data = meta.get(url, {})

    # Now enhance with LLM analysis
    llm_prompt = f"""
    Analyze this webpage and extract structured information:

    TITLE: {data.get('title')}
    META: {data.get('meta_description')}
    H1: {data.get('h1')}
    HEADINGS: {data.get('h2_h3_sample')}
    CONTENT EXCERPT (first 500 chars): {data.get('excerpt', '')[:500]}

    Extract and return JSON:
    {{
      "core_entities": ["key named entities on the page"],
      "core_topics": ["main themes"],
      "core_offer": "what does this page help the user achieve? (1 sentence)",
      "candidate_main_queries": ["2-3 search queries this page wants to rank for"]
    }}
    """

    llm_analysis = llm_client.generate_structured(llm_prompt, schema={...})

    return {
        "url": url,
        "http_status": data.get("http_status"),
        "title": data.get("title"),
        "meta_description": data.get("meta_description"),
        "h1": data.get("h1"),
        "h2_h3_sample": data.get("h2_h3_sample", []),
        "main_content_excerpt": data.get("excerpt"),
        "detected_language": detect_language_from_text(data.get("excerpt", "")),
        "core_entities": llm_analysis.get("core_entities", []),
        "core_topics": llm_analysis.get("core_topics", []),
        "core_offer": llm_analysis.get("core_offer"),
        "candidate_main_queries": llm_analysis.get("candidate_main_queries", [])
    }
```

**Fil:** `src/serp/research.py`

```python
from ..preflight.serp_providers import search_queries
from ..preflight.extract import fetch_metadata, _guess_page_type
from ..preflight.intent_policy import classify_intent_from_query, derive_required_subtopics
from ..utils.llm import LLMClient

async def conduct_serp_research(
    target_profile: dict,
    anchor_profile: dict,
    llm_client: LLMClient
) -> dict:
    """Conduct SERP research using preflight SERP providers + LLM enhancement"""

    # Get queries from target profile
    queries = target_profile.get("candidate_main_queries", [])
    if not queries:
        queries = [target_profile.get("title", "")]

    # Fetch SERP results using ChatGPT's provider
    raw_results = await search_queries(queries[:3], num=10)

    # Build SERP sets
    serp_sets = []
    for query in queries[:3]:
        results = raw_results.get(query, [])

        # Basic intent classification from query
        dominant_intent = classify_intent_from_query(query)

        # Fetch metadata for top results
        urls = [r["url"] for r in results if r.get("url")]
        metadata = await fetch_metadata(urls[:10])

        # Build top results with LLM enhancement
        top_results = []
        for r in results:
            url = r.get("url")
            meta = metadata.get(url, {})

            # Basic page type guess
            page_type = _guess_page_type(url, r.get("title", ""))

            # LLM: Extract entities & subtopics from snippet + metadata
            llm_prompt = f"""
            Analyze this SERP result:

            TITLE: {r.get('title')}
            SNIPPET: {r.get('snippet')}
            META: {meta.get('meta_description')}

            Extract JSON:
            {{
              "key_entities": ["3-5 key named entities"],
              "key_subtopics": ["2-4 main subtopics covered"]
            }}
            """

            llm_analysis = llm_client.generate_structured(llm_prompt, schema={...})

            top_results.append({
                "rank": r.get("rank"),
                "url": url,
                "title": r.get("title"),
                "snippet": r.get("snippet"),
                "detected_page_type": page_type,
                "key_entities": llm_analysis.get("key_entities", []),
                "key_subtopics": llm_analysis.get("key_subtopics", [])
            })

        # Aggregate required subtopics (use heuristic first, then LLM)
        required_subtopics = derive_required_subtopics(results, top_k=5)

        # LLM: Analyze entire SERP set
        llm_serp_prompt = f"""
        Analyze these top-10 SERP results for query: "{query}"

        RESULTS:
        {json.dumps(top_results, indent=2)}

        Determine:
        1. dominant_intent (info_primary, commercial_research, transactional, etc.)
        2. secondary_intents (list)
        3. required_subtopics (what ALL top results cover - these MUST be in our article)
        4. page_archetypes (what types of pages dominate? guide, comparison, product, etc.)

        Return JSON according to schema.
        """

        serp_analysis = llm_client.generate_structured(llm_serp_prompt, schema={...})

        serp_sets.append({
            "query": query,
            "dominant_intent": serp_analysis.get("dominant_intent", dominant_intent),
            "secondary_intents": serp_analysis.get("secondary_intents", []),
            "page_archetypes": serp_analysis.get("page_archetypes", []),
            "required_subtopics": serp_analysis.get("required_subtopics", required_subtopics),
            "top_results": top_results
        })

    return {
        "main_query": queries[0],
        "cluster_queries": queries[1:],
        "queries_rationale": "Based on target profile candidate queries",
        "results": serp_sets,
        "confidence": "high"
    }
```

### Deployment för Strategi B:

```bash
# Single process - everything runs locally
python main.py \
  --publisher example.com \
  --target https://client.com/page \
  --anchor "bästa valet"
```

---

## JÄMFÖRELSE: STRATEGI A VS B

| Aspekt | Strategi A (Hybrid) | Strategi B (Monolitisk) |
|--------|---------------------|--------------------------|
| **Arkitektur** | Microservices (API + Pipeline) | Monolith (all-in-one) |
| **Deployment** | 2 processer (FastAPI + Pipeline) | 1 process |
| **Testbarhet** | Excellent (kan testa varje API separat i Hoppscotch) | God (unit tests) |
| **Utvecklingstakt** | Långsammare (behöver synka API + pipeline) | Snabbare (allt i ett) |
| **Flexibilitet** | Hög (kan byta ut delar, använda API från andra system) | Medel (tight coupling) |
| **Performance** | Långsammare (HTTP overhead) | Snabbare (no network calls) |
| **Komplexitet** | Högre (behöver hantera API, ports, networking) | Lägre (enklare codebase) |
| **Skalbarhet** | Excellent (kan skala API och pipeline separat) | God (kan skala hela systemet) |
| **Debugging** | Lättare (kan testa steg-för-steg via API) | Svårare (behöver debugga hela pipelinen) |

---

## REKOMMENDATION

### FÖR UTVECKLING & TESTNING:
**Använd Strategi A (Hybrid)**

Fördelar:
- ✅ Kan testa varje steg isolerat med Hoppscotch
- ✅ Snabbare iteration (ändra API utan att röra pipeline)
- ✅ Lättare att hitta buggar
- ✅ Kan mocka delar (t.ex. använd mock SERP medan du utvecklar writer)

### FÖR PRODUKTION & DEPLOYMENT:
**Använd Strategi B (Monolitisk)**

Fördelar:
- ✅ Enklare deployment (en Docker container)
- ✅ Snabbare exekvering (no HTTP overhead)
- ✅ Färre moving parts (mindre som kan gå fel)
- ✅ Lägre hosting-kostnader (en server istället för två)

### BÄSTA LÖSNINGEN:
**Bygg för Strategi B, men behåll möjligheten till Strategi A**

Implementation:
1. Bygg kärnpipelinen med ChatGPT:s moduler importerade direkt (Strategi B)
2. Skapa ett tunt API-lager ovanpå som exponerar endpoints (optional, för Hoppscotch-testning)
3. Använd environment variable för att växla mellan "direct" och "api" mode

```python
# src/config.py
USE_PREFLIGHT_API = os.getenv("USE_PREFLIGHT_API", "false").lower() == "true"
PREFLIGHT_API_URL = os.getenv("PREFLIGHT_API_URL", "http://localhost:8080")

# src/profile/target_profiler.py
if USE_PREFLIGHT_API:
    # Call API
    response = await api_client.profile_target(url)
else:
    # Direct import
    from ..preflight.extract import fetch_metadata
    response = await profile_target_direct(url)
```

---

## NÄSTA STEG

### 1. Komplettera ChatGPT:s API (om du väljer Strategi A)

Skapa filen:
- `utkast-till-api-lösning/app/main.py` (använd koden ovan)

Testa:
```bash
cd utkast-till-api-lösning
uvicorn app.main:app --reload --port 8080
# Öppna http://localhost:8080/docs
```

### 2. Integrera med Core Pipeline

Välj strategi och följ implementation-stegen ovan.

### 3. LLM-integration

ChatGPT:s kod använder heuristiker för:
- Entity extraction
- Topic extraction
- Intent classification

Dessa behöver förstärkas med LLM-calls. Använd koden i mina exempel ovan.

### 4. Testa End-to-End

```bash
# Strategi A
Terminal 1: uvicorn app.main:app --reload --port 8080
Terminal 2: python main.py --publisher example.com --target https://... --anchor "..."

# Strategi B
python main.py --publisher example.com --target https://... --anchor "..."
```

---

## SAMMANFATTNING

ChatGPT Pro's API-förslag är **excellent** för:
- ✅ Modular design med Pydantic models
- ✅ SERP-hämtning med flera providers
- ✅ Metadata extraction med async httpx
- ✅ Grundläggande intent-heuristiker

Det **kompletterar** min IMPLEMENTATION_SPEC perfekt genom att tillhandahålla:
- Konkret kod för SERP & metadata-hämtning (som jag endast specificerade)
- FastAPI structure (för API-lager om önskat)
- Webhook support (för integration med andra system)

**Integration är straightforward:**
- Strategi A: Använd som separate API services
- Strategi B: Importera moduler direkt i pipeline

**Mitt förslag:** Börja med **Strategi B** för enkelhet, bygg **Strategi A** senare om API-lager behövs.

---

**Version:** 1.0
**Datum:** 2025-11-12
**Status:** INTEGRATION STRATEGY COMPLETE - READY TO BUILD
