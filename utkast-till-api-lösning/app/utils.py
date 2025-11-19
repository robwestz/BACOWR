
import re, unicodedata
from typing import Iterable

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9\- ]+", "", text).strip().lower()
    text = re.sub(r"\s+", "-", text)
    return text or "item"

def detect_language_from_text(text: str) -> str:
    # naive heuristic placeholder (swap with fasttext/CLD3 in prod)
    swedish_terms = ["och", "att", "är", "det", "som", "kan", "för", "med", "utan"]
    if any(t in (text or "").lower() for t in swedish_terms):
        return "sv"
    return "en"
