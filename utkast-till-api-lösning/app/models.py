
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, HttpUrl, Field

# ------------------ Preflight models ------------------

class TargetProfile(BaseModel):
    url: HttpUrl
    http_status: Optional[int] = None
    title: Optional[str] = None
    meta_description: Optional[str] = None
    h1: Optional[str] = None
    h2_h3_sample: List[str] = []
    main_content_excerpt: Optional[str] = None
    detected_language: Optional[str] = None
    core_entities: List[str] = []
    core_topics: List[str] = []
    core_offer: Optional[str] = None
    candidate_main_queries: List[str] = []

class PublisherProfile(BaseModel):
    domain: str
    sample_urls: List[HttpUrl] = []
    about_excerpt: Optional[str] = None
    detected_language: Optional[str] = None
    topic_focus: List[str] = []
    audience: Optional[str] = None
    tone_class: Optional[str] = None
    allowed_commerciality: Optional[str] = None
    brand_safety_notes: Optional[str] = None

class AnchorProfile(BaseModel):
    proposed_text: str
    type_hint: Optional[Literal["exact", "partial", "brand", "generic"]] = None
    llm_classified_type: Optional[Literal["exact", "partial", "brand", "generic"]] = None
    llm_intent_hint: Optional[Literal["info_primary","commercial_research","transactional","navigational_brand","support","local","mixed"]] = None

# ------------------ SERP models ------------------

PageType = Literal["guide","comparison","category","product","review","tool","faq","news","official","other"]
IntentType = Literal["info_primary","commercial_research","transactional","navigational_brand","support","local","mixed"]

class TopResult(BaseModel):
    rank: int
    url: HttpUrl
    title: Optional[str] = None
    snippet: Optional[str] = None
    detected_page_type: Optional[PageType] = None
    key_entities: List[str] = []
    key_subtopics: List[str] = []

class SERPSet(BaseModel):
    query: str
    dominant_intent: Optional[IntentType] = None
    secondary_intents: List[IntentType] = []
    page_archetypes: List[PageType] = []
    required_subtopics: List[str] = []
    top_results: List[TopResult] = []

class SERPResearch(BaseModel):
    main_query: str
    cluster_queries: List[str] = []
    queries_rationale: Optional[str] = None
    results: List[SERPSet] = []
    confidence: Optional[Literal["high","medium","low"]] = "medium"

# ------------------ Intent profile ------------------

class IntentAlignment(BaseModel):
    anchor_vs_serp: Literal["aligned","partial","off"]
    target_vs_serp: Literal["aligned","partial","off"]
    publisher_vs_serp: Literal["aligned","partial","off"]
    overall: Literal["aligned","partial","off"]

class IntentNotes(BaseModel):
    rationale: Optional[str] = None
    data_confidence: Optional[Literal["high","medium","low"]] = "medium"

class IntentProfile(BaseModel):
    serp_intent_primary: IntentType
    serp_intent_secondary: List[IntentType] = []
    target_page_intent: Optional[str] = None
    anchor_implied_intent: Optional[IntentType] = None
    publisher_role_intent: Optional[IntentType] = None
    required_subtopics_merged: List[str] = []
    forbidden_angles: List[str] = []
    alignment: IntentAlignment
    recommended_bridge_type: Literal["strong","pivot","wrapper"]
    recommended_article_angle: Optional[str] = None
    rationale: Optional[str] = None

# ------------------ A1 extensions (subset matching your spec) ------------------

class LinksExtension(BaseModel):
    bridge_type: Literal["strong","pivot","wrapper"]
    bridge_theme: Optional[str] = None
    anchor_policy_used: Optional[str] = None
    trust_policy_level: Optional[Literal["T1_public","T2_academic","T3_industry","T4_media"]] = None

class QCExtension(BaseModel):
    anchor_risk: Literal["low","medium","high"]
    thresholds_version: str = "A1"
    notes_observability: dict = {}

class IntentExtension(BaseModel):
    serp_intent_primary: IntentType
    serp_intent_secondary: List[IntentType] = []
    target_page_intent: Optional[str] = None
    anchor_implied_intent: Optional[IntentType] = None
    publisher_role_intent: Optional[IntentType] = None
    intent_alignment: IntentAlignment
    recommended_bridge_type: Literal["strong","pivot","wrapper"]
    recommended_article_angle: Optional[str] = None
    required_subtopics: List[str] = []
    forbidden_angles: List[str] = []
    notes: IntentNotes = IntentNotes()

class WriterBrief(BaseModel):
    links_extension: LinksExtension
    qc_extension: QCExtension
    intent_extension: IntentExtension
    serp_research_extension: SERPResearch

# ------------------ API I/O models ------------------

class TargetRequest(BaseModel):
    target_url: HttpUrl

class PublisherRequest(BaseModel):
    publisher_domain: str
    sample_urls: List[HttpUrl] = []
    about_excerpt: Optional[str] = None

class AnchorRequest(BaseModel):
    anchor_text: str
    type_hint: Optional[Literal["exact","partial","brand","generic"]] = None

class SERPRequest(BaseModel):
    queries: List[str]
    provider: Optional[str] = "mock"
    fetch_metadata: bool = True
    locale: Optional[str] = "sv-SE"

class PolicyApplyRequest(BaseModel):
    target_profile: TargetProfile
    publisher_profile: PublisherProfile
    anchor_profile: AnchorProfile
    intent_profile: IntentProfile
    serp_research: SERPResearch

class HandoffRequest(BaseModel):
    target_profile: TargetProfile
    publisher_profile: PublisherProfile
    anchor_profile: AnchorProfile
    serp_research: SERPResearch
    intent_profile: IntentProfile
    webhook_url: Optional[str] = None
    correlation_id: Optional[str] = None
