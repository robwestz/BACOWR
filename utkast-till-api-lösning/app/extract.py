
from typing import Iterable, Dict, Any
import asyncio, re
import httpx
from bs4 import BeautifulSoup
from .config import settings
from .utils import normalize_space

META_DESC_SELECTORS = [
    ('meta[name="description"]', "content"),
    ('meta[name="Description"]', "content"),
    ('meta[property="og:description"]', "content"),
    ('meta[name="twitter:description"]', "content"),
]

def _guess_page_type(url: str, title: str = "") -> str:
    u = url.lower()
    t = (title or "").lower()
    pairs = [
        ("comparison","vs"),
        ("comparison","jämförelse"),
        ("category","kategori"),
        ("product","produkt"),
        ("review","recension"),
        ("faq","faq"),
        ("news","nyhet"),
        ("official","myndighet"),
    ]
    for typ, token in pairs:
        if token in u or token in t:
            return typ
    if "best" in t or "bästa" in t:
        return "comparison"
    return "guide"

async def _fetch_one(client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
    try:
        r = await client.get(url, timeout=settings.REQUEST_TIMEOUT, follow_redirects=True)
        status = r.status_code
        html = r.text
    except Exception as e:
        return {"url": url, "http_status": None, "title": None, "meta_description": None, "h1": None, "excerpt": None}

    soup = BeautifulSoup(html, "lxml")
    title = normalize_space(soup.title.text if soup.title else "")
    meta_description = None
    for sel, attr in META_DESC_SELECTORS:
        tag = soup.select_one(sel)
        if tag and tag.get(attr):
            meta_description = normalize_space(tag.get(attr))
            break
    # fallback: first paragraph
    if not meta_description:
        p = soup.find("p")
        if p:
            meta_description = normalize_space(p.get_text())[:300]

    h1 = None
    h1tag = soup.find("h1")
    if h1tag:
        h1 = normalize_space(h1tag.get_text())

    # sample h2/h3
    h2_h3 = []
    for tag in soup.find_all(["h2","h3"])[:4]:
        h2_h3.append(normalize_space(tag.get_text()))

    # excerpt (first 500 chars of body text)
    texts = [normalize_space(t.get_text()) for t in soup.find_all(["p","li"])]
    excerpt = normalize_space(" ".join(texts))[:500] if texts else None

    return {
        "url": url,
        "http_status": status,
        "title": title or None,
        "meta_description": meta_description or None,
        "h1": h1,
        "h2_h3_sample": h2_h3,
        "excerpt": excerpt
    }

async def fetch_metadata(urls: Iterable[str]) -> Dict[str, Dict[str, Any]]:
    async with httpx.AsyncClient(headers={"User-Agent": settings.USER_AGENT}, http2=True) as client:
        tasks = [asyncio.create_task(_fetch_one(client, u)) for u in urls]
        done = await asyncio.gather(*tasks)
    return {d["url"]: d for d in done if isinstance(d, dict) and d.get("url")}
