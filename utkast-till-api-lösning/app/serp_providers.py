
from typing import List, Dict, Any
import os, asyncio
import httpx
from .config import settings
from .utils import slugify

GOOGLE_CSE_ENDPOINT = "https://www.googleapis.com/customsearch/v1"
SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

async def _serpapi_search(client: httpx.AsyncClient, query: str, num: int = 10) -> List[Dict[str, Any]]:
    params = {
        "engine": "google",
        "q": query,
        "num": num,
        "hl": "sv",
        "gl": "se",
        "api_key": settings.SERPAPI_KEY,
    }
    r = await client.get(SERPAPI_ENDPOINT, params=params, timeout=settings.REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    results = []
    for i, item in enumerate(data.get("organic_results", [])[:num], start=1):
        results.append({
            "rank": i,
            "url": item.get("link"),
            "title": item.get("title"),
            "snippet": item.get("snippet"),
        })
    return results

async def _google_cse_search(client: httpx.AsyncClient, query: str, num: int = 10) -> List[Dict[str, Any]]:
    params = {
        "key": settings.GOOGLE_CSE_KEY,
        "cx": settings.GOOGLE_CSE_CX,
        "q": query,
        "num": num,
        "hl": "sv"
    }
    r = await client.get(GOOGLE_CSE_ENDPOINT, params=params, timeout=settings.REQUEST_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    results = []
    for i, item in enumerate(data.get("items", [])[:num], start=1):
        results.append({
            "rank": i,
            "url": item.get("link"),
            "title": item.get("title"),
            "snippet": item.get("snippet") or item.get("title"),
        })
    return results

async def _mock_search(query: str, num: int = 10) -> List[Dict[str, Any]]:
    slug = slugify(query)
    results = []
    for i in range(1, num + 1):
        results.append({
            "rank": i,
            "url": f"https://example.com/{slug}-{i}",
            "title": f"{query} — exempelresultat {i}",
            "snippet": f"Detta är en simulerad träff för '{query}' med rank {i}.",
        })
    return results

async def search_queries(queries: List[str], num: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    provider = (settings.SERP_PROVIDER or "mock").lower()
    results: Dict[str, List[Dict[str, Any]]] = {}
    async with httpx.AsyncClient(headers={"User-Agent": settings.USER_AGENT}, http2=True) as client:
        for q in queries:
            if provider == "serpapi" and settings.SERPAPI_KEY:
                results[q] = await _serpapi_search(client, q, num)
            elif provider == "google_cse" and settings.GOOGLE_CSE_KEY and settings.GOOGLE_CSE_CX:
                results[q] = await _google_cse_search(client, q, num)
            elif provider == "selenium":
                # Placeholder - implement selenium-backed Google search here if desired
                # to avoid rate limiting. For now, fallback to mock.
                results[q] = await _mock_search(q, num)
            else:
                results[q] = await _mock_search(q, num)
    return results
