
from typing import List, Dict, Any, Tuple
import re
from collections import Counter
from .models import IntentType, IntentAlignment

def classify_intent_from_query(query: str) -> IntentType:
    q = query.lower()
    if any(w in q for w in ["köp","pris","rabatt","beställ"]):
        return "transactional"
    if any(w in q for w in ["bäst","bästa","jämförelse","vs","alternativ","recension"]):
        return "commercial_research"
    if any(w in q for w in ["support","fel","problem","hjälp"]):
        return "support"
    if any(w in q for w in ["nära","närmast","i närheten"]):
        return "local"
    return "info_primary"

def guess_intent_from_snippets(snippets: List[str]) -> IntentType:
    joined = " ".join(snippets).lower()
    # very simple heuristic over snippets
    if any(w in joined for w in ["köp","pris","beställ"]):
        return "transactional"
    if any(w in joined for w in ["bäst","jämförelse","testade","recension"]):
        return "commercial_research"
    return "info_primary"

def derive_required_subtopics(results: List[Dict[str, Any]], top_k: int = 5) -> List[str]:
    tokens = []
    for r in results:
        title = (r.get("title") or "").lower()
        snip = (r.get("snippet") or "").lower()
        for t in re.findall(r"[a-zåäöA-ZÅÄÖ]{3,}", f"{title} {snip}"):
            tokens.append(t)
    stop = set("och att för med som den det detsamma är har på från inom utan enligt mellan under över ännu mera även samt trots där när hur vad vilken vilket vilka då".split())
    tokens = [t for t in tokens if t not in stop]
    common = [w for w,_ in Counter(tokens).most_common(50)]
    return common[:top_k]

def compute_alignment(anchor_intent: IntentType, serp_primary: IntentType, target_intent: str, publisher_role: IntentType) -> IntentAlignment:
    def cmp(x,y):
        return "aligned" if x == y or (x=="commercial_research" and y in ["info_primary","commercial_research"]) else "partial"
    anchor_vs_serp = cmp(anchor_intent, serp_primary)
    # target intent mapping heuristic
    ty = "transactional" if "transaction" in (target_intent or "") else "info_primary"
    target_vs_serp = "aligned" if (serp_primary==ty or (serp_primary in ["info_primary","commercial_research"] and ty in ["info_primary","commercial_research"])) else "partial"
    publisher_vs_serp = cmp(publisher_role, serp_primary)
    # overall: if any is "aligned" and none are "off" -> partial/aligned
    statuses = [anchor_vs_serp, target_vs_serp, publisher_vs_serp]
    overall = "aligned" if statuses.count("aligned") >= 2 else "partial"
    return IntentAlignment(anchor_vs_serp=anchor_vs_serp, target_vs_serp=target_vs_serp, publisher_vs_serp=publisher_vs_serp, overall=overall)

def recommend_bridge_type(alignment: IntentAlignment) -> str:
    # Based on Next-A1 rules: strong if none are 'off' and mostly aligned, pivot for partial, wrapper if 'off' (we never compute 'off' in this heuristic)
    if alignment.overall == "aligned":
        return "strong"
    return "pivot"
