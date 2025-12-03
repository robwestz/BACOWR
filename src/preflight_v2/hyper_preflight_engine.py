# hyper_preflight_engine.py

from __future__ import annotations

import json
import math
import random
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse


# ============================================================================
# ENUMS & CORE TYPES
# ============================================================================

class SourceTier(str, Enum):
    T1_GOVERNMENT = "T1_GOVERNMENT"
    T2_ACADEMIC = "T2_ACADEMIC"
    T3_INDUSTRY = "T3_INDUSTRY"
    T4_MEDIA = "T4_MEDIA"
    T5_BRAND = "T5_BRAND"
    DATA_PORTAL = "DATA_PORTAL"

    @property
    def authority_range(self) -> Tuple[int, int]:
        ranges = {
            SourceTier.T1_GOVERNMENT: (95, 100),
            SourceTier.T2_ACADEMIC: (85, 94),
            SourceTier.T3_INDUSTRY: (75, 84),
            SourceTier.T4_MEDIA: (65, 74),
            SourceTier.T5_BRAND: (50, 64),
            SourceTier.DATA_PORTAL: (70, 90),
        }
        return ranges[self]

    @property
    def weight(self) -> float:
        weights = {
            SourceTier.T1_GOVERNMENT: 1.0,
            SourceTier.T2_ACADEMIC: 0.9,
            SourceTier.T3_INDUSTRY: 0.8,
            SourceTier.T4_MEDIA: 0.7,
            SourceTier.T5_BRAND: 0.5,
            SourceTier.DATA_PORTAL: 0.85,
        }
        return weights[self]


class AnchorType(str, Enum):
    EXACT = "EXACT"
    PARTIAL = "PARTIAL"
    BRANDED = "BRANDED"
    GENERIC = "GENERIC"
    LSI = "LSI"
    UNKNOWN = "UNKNOWN"


class BridgeType(str, Enum):
    DIRECT = "DIRECT"
    CONTEXTUAL = "CONTEXTUAL"
    COMPARISON = "COMPARISON"
    WRAPPER = "WRAPPER"


class MarriageStatus(str, Enum):
    PERFECT = "PERFECT"
    MINOR_FIX = "MINOR_FIX"
    NEEDS_PIVOT = "NEEDS_PIVOT"
    NEEDS_WRAPPER = "NEEDS_WRAPPER"


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class GuardrailType(str, Enum):
    REQUIRED_DISCLAIMER = "REQUIRED_DISCLAIMER"
    NO_UNBACKED_HEALTH_CLAIMS = "NO_UNBACKED_HEALTH_CLAIMS"
    NO_UNKNOWN_EXTERNAL_URLS = "NO_UNKNOWN_EXTERNAL_URLS"
    MAX_COMMERCIAL_DENSITY = "MAX_COMMERCIAL_DENSITY"
    BLOCK_FORBIDDEN_ANGLE = "BLOCK_FORBIDDEN_ANGLE"
    TRUST_TIER_MINIMUM = "TRUST_TIER_MINIMUM"


class GuardrailPriority(Enum):
    HARD_BLOCK = 1
    STRONG = 2
    SOFT = 3


class DecisionLevel(str, Enum):
    AUTO_OK = "AUTO_OK"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    AUTO_BLOCK = "AUTO_BLOCK"


class ArticleType(str, Enum):
    GUIDE = "GUIDE"
    COMPARISON = "COMPARISON"
    WRAPPER = "WRAPPER"
    EDUCATIONAL = "EDUCATIONAL"
    LISTICLE = "LISTICLE"


# ============================================================================
# TRUSTLINK MODELS
# ============================================================================

@dataclass
class TrustSource:
    url: str
    title: str
    domain: str
    source_type: SourceTier
    topics: List[str]
    industries: List[str] = field(default_factory=list)
    snippet: Optional[str] = None
    authority_score: int = 75
    language: str = "sv"
    last_verified: Optional[datetime] = None
    http_status: int = 200

    @property
    def is_valid(self) -> bool:
        if self.http_status != 200:
            return False
        if self.last_verified is None:
            return True
        return datetime.utcnow() - self.last_verified < timedelta(days=90)

    def topic_match(self, query_topics: List[str]) -> float:
        if not query_topics or not self.topics:
            return 0.0
        q = {t.lower() for t in query_topics}
        s = {t.lower() for t in self.topics}
        return len(q & s) / len(q)

    def industry_match(self, industry: Optional[str]) -> bool:
        if not industry or not self.industries:
            return True
        return industry.lower() in [i.lower() for i in self.industries]


@dataclass
class TrustPlan:
    sources: List[TrustSource] = field(default_factory=list)
    min_required: int = 2
    tier_mix: Dict[SourceTier, int] = field(default_factory=dict)
    mode: str = "none"  # "none" | "minimal" | "full"

    def to_contract_dict(self) -> List[Dict[str, Any]]:
        result = []
        for s in self.sources:
            result.append({
                "url": s.url,
                "title": s.title,
                "domain": s.domain,
                "source_type": s.source_type.value,
                "authority_score": s.authority_score,
                "topics": s.topics,
                "industries": s.industries,
                "snippet": s.snippet,
            })
        return result


# ============================================================================
# SERP & INTENT
# ============================================================================

@dataclass
class SerpResult:
    url: str
    title: str
    snippet: str
    intent: str
    position: int
    domain: str


@dataclass
class SerpCluster:
    id: str
    label: str
    primary_intent: str
    subtopics: List[str] = field(default_factory=list)
    results: List[SerpResult] = field(default_factory=list)


@dataclass
class SerpTopology:
    query: str
    primary_intent: str
    clusters: List[SerpCluster] = field(default_factory=list)
    source: str = "template"  # "real" | "llm_estimated" | "template"


@dataclass
class IntentStep:
    id: str
    label: str
    description: str
    importance: int
    serp_cluster_id: Optional[str] = None


@dataclass
class CompactIntentPath:
    primary_path: List[IntentStep] = field(default_factory=list)


# ============================================================================
# MARRIAGE & RISK
# ============================================================================

@dataclass
class VariableMarriageV2:
    status: MarriageStatus
    anchor_fidelity: float
    context_fidelity: float
    anchor_type: AnchorType
    recommended_bridge_type: BridgeType
    recommended_article_type: ArticleType
    forbidden_angles: List[str] = field(default_factory=list)
    implementation_notes: List[str] = field(default_factory=list)


@dataclass
class RiskProfile:
    risk_level: RiskLevel
    editorial_risks: List[str] = field(default_factory=list)
    brand_risks: List[str] = field(default_factory=list)
    legal_risks: List[str] = field(default_factory=list)


# ============================================================================
# CLAIMS, SECTIONS, WRITER PLAN
# ============================================================================

@dataclass
class PlannedClaim:
    claim_id: str
    section_id: str
    claim_text: str
    evidence_urls: List[str]
    required: bool
    confidence: float


@dataclass
class SectionPlan:
    section_id: str
    heading: str
    purpose: str
    target_intent_step_id: Optional[str]
    required_points: List[str] = field(default_factory=list)
    optional_points: List[str] = field(default_factory=list)
    planned_claim_ids: List[str] = field(default_factory=list)
    lsi_terms: List[str] = field(default_factory=list)
    trustlink_candidates: List[str] = field(default_factory=list)
    max_brand_mentions: int = 3


@dataclass
class HyperWriterPlan:
    article_type: ArticleType
    thesis: str
    angle: str
    sections: List[SectionPlan] = field(default_factory=list)
    global_lsi_terms: List[str] = field(default_factory=list)
    link_plan: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# GUARDRAILS & DECISION
# ============================================================================

@dataclass
class GuardrailRule:
    id: str
    type: GuardrailType
    priority: GuardrailPriority
    threshold: Optional[float] = None
    verticals: Optional[List[str]] = None
    notes: Optional[str] = None


@dataclass
class FallbackContext:
    serp_mode: str = "template"
    publisher_mode: str = "fallback"
    target_mode: str = "fallback"
    trustlink_mode: str = "none"
    notes: List[str] = field(default_factory=list)


@dataclass
class TokenBudget:
    total_preflight: int = 1500
    intent: int = 300
    seo_opportunities: int = 250
    planned_claims: int = 250
    guardrails: int = 150
    writer_plan: int = 350
    misc_metadata: int = 200


@dataclass
class PreflightDecision:
    level: DecisionLevel
    reason: str
    confidence: float


# ============================================================================
# HYPER HANDOFF CONTRACT
# ============================================================================

@dataclass
class HyperHandoffContract:
    job_id: str
    publisher_profile: Dict[str, Any]
    target_profile: Dict[str, Any]
    anchor_text: str
    anchor_url: str
    anchor_type: AnchorType
    vertical: str
    serp_topology: SerpTopology
    intent_path: CompactIntentPath
    variable_marriage: VariableMarriageV2
    risk_profile: RiskProfile
    trust_plan: TrustPlan
    planned_claims: List[PlannedClaim]
    writer_plan: HyperWriterPlan
    guardrails: List[GuardrailRule]
    fallback_context: FallbackContext
    decision: PreflightDecision
    token_budget: TokenBudget

    def to_compact_json(self) -> str:
        """
        Kompakt serialisering med token-budget medveten trimning.
        """
        data = asdict(self)

        # Aggressiv trimming på låg-prio fält om vi närmar oss budget
        def approx_tokens(obj: Any) -> int:
            return math.ceil(len(json.dumps(obj)) / 4)

        budget = self.token_budget.total_preflight

        # Trim planned_claims → behåll högst 7, prioritera required + hög confidence
        if len(data["planned_claims"]) > 7:
            claims = data["planned_claims"]
            claims.sort(key=lambda c: (not c["required"], -c["confidence"]))
            data["planned_claims"] = claims[:7]

        # Trim sections.optional_points om för mycket text
        for sec in data["writer_plan"]["sections"]:
            if len(sec["optional_points"]) > 4:
                sec["optional_points"] = sec["optional_points"][:4]

        # Trim guardrails till de hårdaste först
        if len(data["guardrails"]) > 8:
            rules = data["guardrails"]
            rules.sort(key=lambda r: r["priority"])
            data["guardrails"] = rules[:8]

        # Om fortfarande över budget, trimma SERP-kluster
        if approx_tokens(data) > budget:
            topo = data["serp_topology"]
            if len(topo["clusters"]) > 3:
                topo["clusters"] = topo["clusters"][:3]

        # Sista säkerhetsbälte – trimma intent-path till 3 steg
        if approx_tokens(data) > budget:
            steps = data["intent_path"]["primary_path"]
            data["intent_path"]["primary_path"] = steps[:3]

        return json.dumps(data, ensure_ascii=False)


# ============================================================================
# TRUSTLINK ENGINE
# ============================================================================

class TrustLinkEngine:
    """
    Produktionsredo trustlink-motor:
    - prekonfigurerad pool med godkända domäner
    - topic/industry-matchning
    - tier-mix
    - evidence-koppling till claims
    """

    def __init__(self, preconfigured_sources: Optional[Dict[str, Dict[str, Any]]] = None):
        self.pool: Dict[str, TrustSource] = {}
        if preconfigured_sources:
            self._load_preconfigured(preconfigured_sources)

    def _load_preconfigured(self, cfg: Dict[str, Dict[str, Any]]) -> None:
        for domain, meta in cfg.items():
            tier: SourceTier = SourceTier(meta["tier"])
            authority: int = meta.get("authority", tier.authority_range[0])
            self.pool[domain] = TrustSource(
                url=f"https://{domain}",
                title=meta["title"],
                domain=domain,
                source_type=tier,
                topics=meta.get("topics", []),
                industries=meta.get("industries", []),
                authority_score=authority,
                language="sv" if domain.endswith(".se") else "en",
                last_verified=datetime.utcnow(),
                http_status=200,
            )

    def register_source(self, source: TrustSource) -> None:
        self.pool[source.domain] = source

    def _score_source(
        self,
        source: TrustSource,
        topics: List[str],
        industry: Optional[str]
    ) -> float:
        if not source.is_valid:
            return 0.0
        if industry and not source.industry_match(industry):
            return 0.0

        topic_score = source.topic_match(topics)
        tier_weight = source.source_type.weight
        authority_norm = (source.authority_score - 50) / 50.0  # 0–1 approx

        return topic_score * 0.6 + tier_weight * 0.3 + authority_norm * 0.1

    def select_trustlinks(
        self,
        topics: List[str],
        industry: Optional[str],
        language: str = "sv",
        min_required: int = 2,
        max_total: int = 6,
    ) -> TrustPlan:
        candidates: List[Tuple[TrustSource, float]] = []
        for source in self.pool.values():
            if language and source.language != language:
                continue
            score = self._score_source(source, topics, industry)
            if score > 0:
                candidates.append((source, score))

        candidates.sort(key=lambda x: (x[1], x[0].authority_score), reverse=True)
        selected: List[TrustSource] = [s for s, _ in candidates[:max_total]]

        tier_mix: Dict[SourceTier, int] = {}
        for s in selected:
            tier_mix[s.source_type] = tier_mix.get(s.source_type, 0) + 1

        if not selected:
            mode = "none"
        elif len(selected) < min_required:
            mode = "minimal"
        else:
            mode = "full"

        return TrustPlan(
            sources=selected,
            min_required=min_required,
            tier_mix=tier_mix,
            mode=mode,
        )

    @staticmethod
    def link_claims_to_sources(
        claims: List[PlannedClaim],
        trust_plan: TrustPlan
    ) -> List[PlannedClaim]:
        """
        Koppla varje claim till 1–3 relevanta källor baserat på enkel topic-heuristik.
        (I praktiken kan detta göras LLM-baserat, men denna version är deterministisk.)
        """
        if not trust_plan.sources:
            return claims

        enriched: List[PlannedClaim] = []
        for claim in claims:
            # Grovt: välj 2–3 starkaste källor, prioritera T1/T2
            sorted_sources = sorted(
                trust_plan.sources,
                key=lambda s: (s.source_type in {SourceTier.T1_GOVERNMENT, SourceTier.T2_ACADEMIC},
                               s.authority_score),
                reverse=True,
            )
            selected = sorted_sources[:3]
            enriched.append(PlannedClaim(
                claim_id=claim.claim_id,
                section_id=claim.section_id,
                claim_text=claim.claim_text,
                evidence_urls=[s.url for s in selected],
                required=claim.required,
                confidence=claim.confidence,
            ))
        return enriched


# ============================================================================
# PREFLIGHT ENGINE
# ============================================================================

class HyperPreflightEngine:
    """
    HyperPreflight vNEXT++:
    - Bygger SERP-topologi (mock/template eller real)
    - Härleder intent-path
    - Beräknar VariableMarriage
    - Bygger TrustPlan + PlannedClaims
    - Genererar HyperWriterPlan
    - Sätter Guardrails
    - Fattar PreflightDecision med fallback- & trust-awareness
    """

    def __init__(
        self,
        trustlink_engine: TrustLinkEngine,
        logger: Optional[Any] = None,
        token_budget: Optional[TokenBudget] = None,
    ):
        self.trustlink_engine = trustlink_engine
        self.logger = logger or self._noop_logger()
        self.token_budget = token_budget or TokenBudget()

    # ----------------- PUBLIC API -----------------

    def run(self, job: Dict[str, Any]) -> HyperHandoffContract:
        """
        job: dict med minst:
          - job_id
          - vertical
          - anchor_text
          - anchor_url
          - query
          - publisher_profile
          - target_profile
        """
        self.logger["info"](f"Starting HyperPreflight for job {job.get('job_id')}")

        fallback = FallbackContext()

        serp_topology = self._build_serp_topology(job, fallback)
        intent_path = self._build_intent_path(serp_topology)
        anchor_type = self._classify_anchor_type(job["anchor_text"], job["target_profile"])
        marriage = self._compute_marriage(job, serp_topology, anchor_type)
        risk_profile = self._compute_risk_profile(job, marriage)

        trust_plan = self._build_trust_plan(job, serp_topology, fallback)
        planned_claims = self._build_planned_claims(job, serp_topology, intent_path, trust_plan)
        writer_plan = self._build_writer_plan(job, intent_path, marriage, planned_claims, trust_plan)

        guardrails = self._build_guardrails(job, marriage, risk_profile, trust_plan)
        decision = self._make_decision(job, marriage, risk_profile, trust_plan, fallback)

        contract = HyperHandoffContract(
            job_id=job["job_id"],
            publisher_profile=job["publisher_profile"],
            target_profile=job["target_profile"],
            anchor_text=job["anchor_text"],
            anchor_url=job["anchor_url"],
            anchor_type=anchor_type,
            vertical=job["vertical"],
            serp_topology=serp_topology,
            intent_path=intent_path,
            variable_marriage=marriage,
            risk_profile=risk_profile,
            trust_plan=trust_plan,
            planned_claims=planned_claims,
            writer_plan=writer_plan,
            guardrails=guardrails,
            fallback_context=fallback,
            decision=decision,
            token_budget=self.token_budget,
        )

        # Token-budget medveten serialisering (kommer trimma vid behov)
        _ = contract.to_compact_json()

        self.logger["info"](f"Preflight complete for job {job.get('job_id')} – decision: {decision.level}")
        return contract

    # ----------------- SERP & INTENT -----------------

    def _build_serp_topology(self, job: Dict[str, Any], fallback: FallbackContext) -> SerpTopology:
        query = job.get("query") or job["target_profile"].get("primary_topic", "")
        vertical = job["vertical"]

        # Här skulle riktig SERP-integrering ske – nu använder vi en mall per vertical
        if vertical.lower() in ("finance", "health", "medical"):
            primary_intent = "commercial_informational"
            clusters = [
                SerpCluster(
                    id="overview",
                    label="Vad är / grunder",
                    primary_intent="informational",
                    subtopics=[f"vad är {query}", "fördelar/nackdelar"],
                ),
                SerpCluster(
                    id="compare",
                    label="Jämförelser & val",
                    primary_intent="commercial",
                    subtopics=[f"bästa {query}", f"jämförelse {query}"],
                ),
                SerpCluster(
                    id="risk",
                    label="Risker & reglering",
                    primary_intent="informational",
                    subtopics=["risker", "regler", "lagar"],
                ),
            ]
        else:
            primary_intent = "mixed"
            clusters = [
                SerpCluster(
                    id="overview",
                    label="Översikt & guider",
                    primary_intent="informational",
                    subtopics=[f"guide {query}", f"vad är {query}"],
                ),
                SerpCluster(
                    id="best",
                    label="Topplistor & köpguider",
                    primary_intent="commercial",
                    subtopics=[f"bäst i test {query}", f"köpguide {query}"],
                ),
            ]

        fallback.serp_mode = "template"
        return SerpTopology(
            query=query,
            primary_intent=primary_intent,
            clusters=clusters,
            source=fallback.serp_mode,
        )

    def _build_intent_path(self, topology: SerpTopology) -> CompactIntentPath:
        steps: List[IntentStep] = []
        # Basera stegen på klusterordning
        for i, cluster in enumerate(topology.clusters):
            steps.append(IntentStep(
                id=f"step_{i+1}",
                label=cluster.label,
                description=f"Täck {cluster.label.lower()} med fokus på: {', '.join(cluster.subtopics[:3])}",
                importance=3 - i,  # tidiga steg viktigare
                serp_cluster_id=cluster.id,
            ))
        return CompactIntentPath(primary_path=steps[:5])

    # ----------------- ANCHOR & MARRIAGE -----------------

    def _classify_anchor_type(self, anchor_text: str, target_profile: Dict[str, Any]) -> AnchorType:
        at = anchor_text.strip().lower()
        if at in ("klicka här", "läs mer", "läs mer här", "se mer"):
            return AnchorType.GENERIC

        title = (target_profile.get("page_title") or target_profile.get("primary_topic") or "").lower()
        if not title:
            return AnchorType.UNKNOWN

        if at == title:
            return AnchorType.EXACT
        if at in title or title in at:
            return AnchorType.PARTIAL

        brand = (target_profile.get("brand_name") or "").lower()
        if brand and brand in at:
            return AnchorType.BRANDED

        return AnchorType.LSI

    def _compute_marriage(
        self,
        job: Dict[str, Any],
        serp: SerpTopology,
        anchor_type: AnchorType
    ) -> VariableMarriageV2:
        vertical = job["vertical"].lower()
        target_topic = job["target_profile"].get("primary_topic", "")
        query = serp.query

        # Enkel fidelity: token overlap mellan query och target_topic
        def token_overlap(a: str, b: str) -> float:
            sa = {t for t in re.findall(r"\w+", a.lower()) if len(t) > 2}
            sb = {t for t in re.findall(r"\w+", b.lower()) if len(t) > 2}
            if not sa or not sb:
                return 0.0
            return len(sa & sb) / len(sa | sb)

        base_fidelity = token_overlap(query, target_topic)
        context_fidelity = min(1.0, base_fidelity + 0.2 if serp.primary_intent in ("mixed", "commercial_informational") else base_fidelity)

        # Justera för anchor-typ & vertikal
        anchor_penalty = {
            AnchorType.EXACT: 0.0,
            AnchorType.PARTIAL: -0.05,
            AnchorType.BRANDED: -0.1,
            AnchorType.LSI: -0.05,
            AnchorType.GENERIC: -0.25,
            AnchorType.UNKNOWN: -0.3,
        }[anchor_type]
        anchor_fidelity = max(0.0, min(1.0, base_fidelity + anchor_penalty))

        if vertical in ("finance", "health", "medical"):
            context_fidelity *= 0.9
            anchor_fidelity *= 0.9

        # Bestäm status
        if anchor_fidelity >= 0.8 and context_fidelity >= 0.8:
            status = MarriageStatus.PERFECT
            bridge = BridgeType.DIRECT
        elif anchor_fidelity >= 0.6 and context_fidelity >= 0.7:
            status = MarriageStatus.MINOR_FIX
            bridge = BridgeType.CONTEXTUAL
        elif anchor_fidelity >= 0.4 and context_fidelity >= 0.6:
            status = MarriageStatus.NEEDS_PIVOT
            bridge = BridgeType.COMPARISON
        else:
            status = MarriageStatus.NEEDS_WRAPPER
            bridge = BridgeType.WRAPPER

        # Article type utifrån bridge & intent
        if bridge == BridgeType.COMPARISON:
            article_type = ArticleType.COMPARISON
        elif bridge == BridgeType.WRAPPER:
            article_type = ArticleType.EDUCATIONAL
        else:
            article_type = ArticleType.GUIDE

        forbidden_angles: List[str] = []
        if status in (MarriageStatus.NEEDS_PIVOT, MarriageStatus.NEEDS_WRAPPER):
            forbidden_angles.append("överdrivet hård säljtakt mot target-url")

        notes: List[str] = []
        if bridge == BridgeType.WRAPPER:
            notes.append("Placera target-url sent i artikeln som kompletterande resurs.")
        elif bridge == BridgeType.COMPARISON:
            notes.append("Jämför target med 2–3 alternativ, var transparent med styrkor/svagheter.")

        return VariableMarriageV2(
            status=status,
            anchor_fidelity=anchor_fidelity,
            context_fidelity=context_fidelity,
            anchor_type=anchor_type,
            recommended_bridge_type=bridge,
            recommended_article_type=article_type,
            forbidden_angles=forbidden_angles,
            implementation_notes=notes,
        )

    def _compute_risk_profile(self, job: Dict[str, Any], marriage: VariableMarriageV2) -> RiskProfile:
        vertical = job["vertical"].lower()
        risks: List[str] = []
        brand_risks: List[str] = []
        legal_risks: List[str] = []

        if vertical in ("finance", "health", "medical", "legal"):
            risks.append("Reglerad vertikal – krav på disclaimers och evidens.")
        if marriage.anchor_type == AnchorType.EXACT:
            risks.append("Exact match-ankare – potentiellt SEO-risk.")
        if marriage.status in (MarriageStatus.NEEDS_PIVOT, MarriageStatus.NEEDS_WRAPPER):
            brand_risks.append("Svag relevans mellan target och artikelns topic.")

        if vertical in ("finance", "health", "medical"):
            level = RiskLevel.HIGH
        elif marriage.anchor_type in (AnchorType.EXACT, AnchorType.GENERIC) and marriage.anchor_fidelity < 0.5:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW

        return RiskProfile(
            risk_level=level,
            editorial_risks=risks,
            brand_risks=brand_risks,
            legal_risks=legal_risks,
        )

    # ----------------- TRUST, CLAIMS, WRITER PLAN -----------------

    def _build_trust_plan(
        self,
        job: Dict[str, Any],
        serp: SerpTopology,
        fallback: FallbackContext,
    ) -> TrustPlan:
        vertical = job["vertical"]
        target_topics = job["target_profile"].get("core_topics") or [serp.query]
        industry = job["target_profile"].get("industry") or vertical

        plan = self.trustlink_engine.select_trustlinks(
            topics=target_topics,
            industry=industry,
            language="sv",
            min_required=2,
            max_total=5,
        )

        if plan.mode == "none":
            fallback.trustlink_mode = "none"
            fallback.notes.append("Inga matchande trustlinks hittades – QC bör vara strängare.")
        elif plan.mode == "minimal":
            fallback.trustlink_mode = "minimal"
        else:
            fallback.trustlink_mode = "full"

        return plan

    def _build_planned_claims(
        self,
        job: Dict[str, Any],
        serp: SerpTopology,
        intent_path: CompactIntentPath,
        trust_plan: TrustPlan,
    ) -> List[PlannedClaim]:
        topic = job["target_profile"].get("primary_topic", "")
        claims: List[PlannedClaim] = []

        # Skapa 4–6 claims baserat på subtopics och vertical
        vertical = job["vertical"].lower()
        base_subtopics: List[str] = []
        for step in intent_path.primary_path[:3]:
            base_subtopics.extend(step.description.split(":")[-1].split(","))

        base_subtopics = [s.strip() for s in base_subtopics if s.strip()]

        candidate_texts: List[str] = []
        for st in base_subtopics[:6]:
            candidate_texts.append(f"{topic} – {st}")

        if vertical in ("finance", "health", "medical"):
            # Lägg till extra evidens-kritiska claims
            candidate_texts.append(f"Det är viktigt att jämföra flera {topic} innan du bestämmer dig.")
            candidate_texts.append(f"Rådfråga alltid expert innan du fattar beslut om {topic}.")

        for idx, text in enumerate(candidate_texts[:6], start=1):
            section_id = "body_1" if idx <= 3 else "body_2"
            required = idx <= 4  # 4 core-claims, resten optional
            confidence = 0.8 if required else 0.6
            claims.append(PlannedClaim(
                claim_id=f"claim_{idx}",
                section_id=section_id,
                claim_text=text,
                evidence_urls=[],
                required=required,
                confidence=confidence,
            ))

        # Koppla evidens
        claims = self.trustlink_engine.link_claims_to_sources(claims, trust_plan)
        return claims

    def _build_writer_plan(
        self,
        job: Dict[str, Any],
        intent_path: CompactIntentPath,
        marriage: VariableMarriageV2,
        claims: List[PlannedClaim],
        trust_plan: TrustPlan,
    ) -> HyperWriterPlan:
        topic = job["target_profile"].get("primary_topic", "")
        vertical = job["vertical"]

        # Artikeltyp styr struktur
        if marriage.recommended_article_type == ArticleType.COMPARISON:
            sections_spec = [
                ("intro", "Introduktion & läsarens problem"),
                ("criteria", "Så väljer du rätt"),
                ("compare", "Jämförelse mellan alternativ"),
                ("target_fit", "När passar target vs alternativ"),
                ("summary", "Sammanfattning & nästa steg"),
            ]
        elif marriage.recommended_article_type == ArticleType.EDUCATIONAL:
            sections_spec = [
                ("intro", f"Vad är {topic}?"),
                ("basics", "Grunderna och nyckelbegreppen"),
                ("deep_dive", "Fördjupning & vanliga frågor"),
                ("application", "Hur du använder kunskapen i praktiken"),
                ("summary", "Sammanfattning"),
            ]
        else:
            sections_spec = [
                ("intro", f"Introduktion till {topic}"),
                ("benefits", f"Fördelar med {topic}"),
                ("how_to", f"Hur du väljer/använder {topic}"),
                ("summary", "Sammanfattning & call-to-action"),
            ]

        # Map claims → sektioner
        claims_by_section: Dict[str, List[PlannedClaim]] = {}
        for c in claims:
            claims_by_section.setdefault(c.section_id, []).append(c)

        sections: List[SectionPlan] = []
        lsi_terms: List[str] = job["target_profile"].get("lsi_terms", [])[:10]
        intent_steps = intent_path.primary_path

        for idx, (sec_id, heading) in enumerate(sections_spec):
            intent_step_id = intent_steps[min(idx, len(intent_steps) - 1)].id if intent_steps else None

            sec_claims = claims_by_section.get(sec_id, [])
            required_points = [c.claim_text for c in sec_claims if c.required]
            optional_points = [c.claim_text for c in sec_claims if not c.required]

            # trustlink-kandidater: alla källor, men QC/writer får välja placering
            trust_candidates = [s.url for s in trust_plan.sources]

            sections.append(SectionPlan(
                section_id=sec_id,
                heading=heading,
                purpose="",
                target_intent_step_id=intent_step_id,
                required_points=required_points,
                optional_points=optional_points,
                planned_claim_ids=[c.claim_id for c in sec_claims],
                lsi_terms=lsi_terms[:3],
                trustlink_candidates=trust_candidates,
                max_brand_mentions=3 if idx > 0 else 1,  # låg brand-intro
            ))

        thesis = f"Artikeln ska hjälpa läsaren att fatta ett välgrundat beslut om {topic} i kontexten av {vertical.lower()}."
        angle = "Objektiv, rådgivande vinkel med tydligt värde för läsaren innan någon call-to-action."

        link_plan = {
            "bridge_type": marriage.recommended_bridge_type.value,
            "article_type": marriage.recommended_article_type.value,
            "target_link_rules": {
                "max_mentions": 2,
                "first_allowed_section": "how_to" if marriage.recommended_bridge_type != BridgeType.DIRECT else "intro",
                "avoid_headings": True,
            },
            "trustlink_rules": {
                "min_total": trust_plan.min_required,
                "prefer_tiers": ["T1_GOVERNMENT", "T2_ACADEMIC", "DATA_PORTAL"],
                "avoid_unknown_domains": True,
            },
        }

        return HyperWriterPlan(
            article_type=marriage.recommended_article_type,
            thesis=thesis,
            angle=angle,
            sections=sections,
            global_lsi_terms=lsi_terms,
            link_plan=link_plan,
        )

    # ----------------- GUARDRAILS & DECISION -----------------

    def _build_guardrails(
        self,
        job: Dict[str, Any],
        marriage: VariableMarriageV2,
        risk: RiskProfile,
        trust_plan: TrustPlan,
    ) -> List[GuardrailRule]:
        vertical = job["vertical"].lower()
        rules: List[GuardrailRule] = []

        # Disclaimers för reglerade vertikaler
        if vertical in ("finance", "health", "medical", "legal"):
            rules.append(GuardrailRule(
                id="req_disclaimer_vertical",
                type=GuardrailType.REQUIRED_DISCLAIMER,
                priority=GuardrailPriority.HARD_BLOCK,
                notes=f"Artikel måste innehålla vertikalspecifik disclaimer för {vertical}.",
                verticals=[vertical],
            ))
            rules.append(GuardrailRule(
                id="no_unbacked_claims_regulated",
                type=GuardrailType.NO_UNBACKED_HEALTH_CLAIMS,
                priority=GuardrailPriority.HARD_BLOCK,
                verticals=[vertical],
                notes="Inga medicinska/finansiella påståenden utan T1/T2-evidens.",
            ))

        # Blockera förbjudna vinklar från marriage
        if marriage.forbidden_angles:
            rules.append(GuardrailRule(
                id="forbidden_angles",
                type=GuardrailType.BLOCK_FORBIDDEN_ANGLE,
                priority=GuardrailPriority.STRONG,
                notes="Undvik följande vinklar: " + ", ".join(marriage.forbidden_angles),
            ))

        # Minsta trust-tier
        rules.append(GuardrailRule(
            id="trust_tier_minimum",
            type=GuardrailType.TRUST_TIER_MINIMUM,
            priority=GuardrailPriority.STRONG,
            threshold=1.0,  # minst en T1/T2
            notes="Minst en källa ska vara T1/T2 eller data-portal.",
        ))

        # Okända externa URL:er förbjudna
        rules.append(GuardrailRule(
            id="no_unknown_urls",
            type=GuardrailType.NO_UNKNOWN_EXTERNAL_URLS,
            priority=GuardrailPriority.HARD_BLOCK,
            notes="Inga externa länkar till domäner utanför trustlink-plan + target-url.",
        ))

        # Kommersiell densitet
        rules.append(GuardrailRule(
            id="max_commercial_density",
            type=GuardrailType.MAX_COMMERCIAL_DENSITY,
            priority=GuardrailPriority.STRONG,
            threshold=0.25,
            notes="Högst 25 % av styckena får innehålla direkta uppmaningar att klicka/köpa.",
        ))

        return rules

    def _make_decision(
        self,
        job: Dict[str, Any],
        marriage: VariableMarriageV2,
        risk: RiskProfile,
        trust_plan: TrustPlan,
        fallback: FallbackContext,
    ) -> PreflightDecision:
        vertical = job["vertical"].lower()

        # Utgå från anchor- & context-fidelity
        af = marriage.anchor_fidelity
        cf = marriage.context_fidelity

        # Hårda block-scenarier
        if af < 0.25 and marriage.anchor_type in (AnchorType.EXACT, AnchorType.GENERIC):
            return PreflightDecision(
                level=DecisionLevel.AUTO_BLOCK,
                reason="Extremt låg anchor-fidelity med riskabel anchortyp.",
                confidence=0.9,
            )

        if risk.risk_level == RiskLevel.HIGH and trust_plan.mode == "none":
            return PreflightDecision(
                level=DecisionLevel.AUTO_BLOCK,
                reason="Reglerad vertikal utan evidens-källor.",
                confidence=0.95,
            )

        # Vertikal-specifik försiktighet
        if vertical in ("finance", "health", "medical"):
            if af < 0.5 or cf < 0.6:
                return PreflightDecision(
                    level=DecisionLevel.NEEDS_HUMAN,
                    reason="Måttlig relevans i reglerad vertikal – kräver manuell review.",
                    confidence=0.8,
                )

        # Fallback-degradering
        degraded_count = sum(
            1 for mode in [fallback.publisher_mode, fallback.target_mode]
            if mode != "enriched"
        )
        if degraded_count >= 2 and trust_plan.mode != "full":
            return PreflightDecision(
                level=DecisionLevel.NEEDS_HUMAN,
                reason="Både publisher- och target-profiler/fallback + begränsad evidens.",
                confidence=0.75,
            )

        # AUTO_OK-scenarier
        if af >= 0.7 and cf >= 0.7 and trust_plan.mode == "full" and risk.risk_level == RiskLevel.LOW:
            return PreflightDecision(
                level=DecisionLevel.AUTO_OK,
                reason="Stark relevans, låg risk, full evidens.",
                confidence=0.9,
            )

        # Default
        return PreflightDecision(
            level=DecisionLevel.NEEDS_HUMAN,
            reason="Standardfall – bör snabbgranskas av människa.",
            confidence=0.7,
        )

    # ----------------- LOGGER HELP -----------------

    @staticmethod
    def _noop_logger() -> Dict[str, Any]:
        return {
            "info": lambda msg: None,
            "warning": lambda msg: None,
            "error": lambda msg: None,
        }
