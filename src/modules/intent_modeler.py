"""
Intent and Cluster Modeler - Models intent alignment and recommends bridge strategy.

This is the CORE of Next-A1's "variabelgiftermål" (variable marriage goal):
- Aligns publisher, anchor, target, and SERP intention
- Recommends bridge_type (strong, pivot, wrapper)
- Defines article angle and required subtopics

EXTENSIBILITY NOTE:
Intent modeling can be reused for:
- Content planning systems
- Editorial calendar tools
- Topic clustering platforms
- Semantic analysis tools
- Content-target matching algorithms
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .publisher_profiler import PublisherProfile
from .target_profiler import TargetProfile
from .anchor_classifier import AnchorProfile
from .serp_analyzer import SerpResearchExtension
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class IntentExtension:
    """
    Intent profile for BacklinkJobPackage.

    Maps to intent_extension in Next-A1 spec.
    Implements the "variabelgiftermål" - marriage of publisher, anchor, target, intention.
    """
    serp_intent_primary: str
    serp_intent_secondary: List[str]
    target_page_intent: str
    anchor_implied_intent: str
    publisher_role_intent: str
    intent_alignment: Dict[str, str]  # anchor_vs_serp, target_vs_serp, publisher_vs_serp, overall
    recommended_bridge_type: str  # strong, pivot, wrapper
    recommended_article_angle: str
    required_subtopics: List[str]
    forbidden_angles: List[str]
    notes: Dict[str, str]  # rationale, data_confidence


class IntentModeler:
    """
    Models intent alignment and recommends bridge strategy.

    This implements Next-A1's core "variabelgiftermål" logic:
    The content must marry publisher role, anchor semantics, target offer,
    and dominant SERP intent into a coherent, natural article.
    """

    def __init__(self):
        """Initialize intent modeler."""
        pass

    def model_intent(
        self,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        anchor_profile: AnchorProfile,
        serp_research: SerpResearchExtension
    ) -> IntentExtension:
        """
        Model intent alignment and recommend bridge strategy.

        This is the CRITICAL decision point that determines article strategy.

        Args:
            publisher_profile: Publisher analysis
            target_profile: Target page analysis
            anchor_profile: Anchor classification
            serp_research: SERP research results

        Returns:
            IntentExtension with alignment analysis and recommendations

        LLM ENHANCEMENT OPPORTUNITY:
        In production, an LLM could:
        - Perform deeper semantic intent matching
        - Generate more nuanced article angles
        - Identify non-obvious bridge opportunities
        - Suggest creative wrapper themes
        - Assess intent confidence more accurately
        """
        logger.info("Modeling intent alignment")

        # Extract primary SERP intent
        serp_intent_primary = self._extract_primary_serp_intent(serp_research)
        serp_intent_secondary = self._extract_secondary_serp_intents(serp_research)

        # Infer target page intent
        target_page_intent = self._infer_target_intent(target_profile)

        # Get anchor implied intent (already classified)
        anchor_implied_intent = anchor_profile.llm_intent_hint

        # Infer publisher role intent
        publisher_role_intent = self._infer_publisher_intent(publisher_profile)

        # Calculate alignment
        intent_alignment = self._calculate_alignment(
            anchor_implied_intent,
            target_page_intent,
            publisher_role_intent,
            serp_intent_primary
        )

        # Recommend bridge type based on alignment
        recommended_bridge_type = self._recommend_bridge_type(
            intent_alignment,
            publisher_profile,
            target_profile,
            anchor_profile
        )

        # Generate article angle
        recommended_article_angle = self._generate_article_angle(
            recommended_bridge_type,
            publisher_profile,
            target_profile,
            serp_intent_primary
        )

        # Merge required subtopics from SERP
        required_subtopics = self._merge_required_subtopics(serp_research)

        # Identify forbidden angles
        forbidden_angles = self._identify_forbidden_angles(
            publisher_profile,
            target_profile,
            intent_alignment
        )

        # Build rationale
        rationale = self._build_rationale(
            intent_alignment,
            recommended_bridge_type,
            serp_intent_primary
        )

        # Assess confidence
        data_confidence = serp_research.data_confidence

        # Build notes
        notes = {
            "rationale": rationale,
            "data_confidence": data_confidence
        }

        extension = IntentExtension(
            serp_intent_primary=serp_intent_primary,
            serp_intent_secondary=serp_intent_secondary,
            target_page_intent=target_page_intent,
            anchor_implied_intent=anchor_implied_intent,
            publisher_role_intent=publisher_role_intent,
            intent_alignment=intent_alignment,
            recommended_bridge_type=recommended_bridge_type,
            recommended_article_angle=recommended_article_angle,
            required_subtopics=required_subtopics,
            forbidden_angles=forbidden_angles,
            notes=notes
        )

        logger.info(
            "Intent modeling complete",
            bridge_type=recommended_bridge_type,
            overall_alignment=intent_alignment["overall"]
        )

        return extension

    def _extract_primary_serp_intent(self, serp_research: SerpResearchExtension) -> str:
        """Extract primary intent from SERP research."""
        # Use the first (main query) SERP set's dominant intent
        if serp_research.serp_sets:
            return serp_research.serp_sets[0].get("dominant_intent", "mixed")
        return "mixed"

    def _extract_secondary_serp_intents(self, serp_research: SerpResearchExtension) -> List[str]:
        """Extract secondary intents from SERP research."""
        secondary = []
        if serp_research.serp_sets:
            secondary.extend(serp_research.serp_sets[0].get("secondary_intents", []))
        return list(set(secondary))

    def _infer_target_intent(self, target_profile: TargetProfile) -> str:
        """
        Infer the primary intent of the target page.

        Based on content type and commercial signals.
        """
        if target_profile.content_type == "product":
            if "price" in target_profile.commercial_signals:
                return "transactional_with_info_support"
            return "commercial_research"
        elif target_profile.content_type == "comparison":
            return "commercial_research"
        elif target_profile.content_type == "guide":
            return "info_primary"
        elif target_profile.content_type == "service":
            return "transactional_with_info_support"
        elif target_profile.content_type == "tool":
            return "transactional"
        else:
            # Fallback: check commercial signals
            if target_profile.commercial_signals:
                return "commercial_research"
            return "info_primary"

    def _infer_publisher_intent(self, publisher_profile: PublisherProfile) -> str:
        """
        Infer the publisher's natural role in the search ecosystem.

        Based on tone_class and topic_focus.
        """
        tone_class = publisher_profile.tone_class

        # Map tone to natural intent role
        tone_to_intent = {
            "academic": "info_primary",
            "authority_public": "info_primary",
            "consumer_magazine": "commercial_research",
            "hobby_blog": "info_primary"
        }

        return tone_to_intent.get(tone_class, "info_primary")

    def _calculate_alignment(
        self,
        anchor_intent: str,
        target_intent: str,
        publisher_intent: str,
        serp_intent: str
    ) -> Dict[str, str]:
        """
        Calculate alignment between all four intent dimensions.

        Returns alignment scores: "aligned", "partial", or "off"

        This is the CORE of Next-A1's intent validation.
        """
        # Anchor vs SERP
        anchor_vs_serp = self._compare_intents(anchor_intent, serp_intent)

        # Target vs SERP
        target_vs_serp = self._compare_intents(target_intent, serp_intent)

        # Publisher vs SERP
        publisher_vs_serp = self._compare_intents(publisher_intent, serp_intent)

        # Overall: worst of the three
        alignments = [anchor_vs_serp, target_vs_serp, publisher_vs_serp]
        if "off" in alignments:
            overall = "off"
        elif "partial" in alignments:
            overall = "partial"
        else:
            overall = "aligned"

        return {
            "anchor_vs_serp": anchor_vs_serp,
            "target_vs_serp": target_vs_serp,
            "publisher_vs_serp": publisher_vs_serp,
            "overall": overall
        }

    def _compare_intents(self, intent_a: str, intent_b: str) -> str:
        """
        Compare two intents and return alignment level.

        Returns: "aligned", "partial", or "off"
        """
        # Direct match
        if intent_a == intent_b:
            return "aligned"

        # Normalize compound intents
        intent_a_base = intent_a.split("_")[0] if "_" in intent_a else intent_a
        intent_b_base = intent_b.split("_")[0] if "_" in intent_b else intent_b

        if intent_a_base == intent_b_base:
            return "aligned"

        # Compatible intents (partial alignment)
        compatible_pairs = {
            ("info_primary", "commercial_research"),
            ("commercial_research", "transactional"),
            ("info_primary", "support"),
        }

        if (intent_a_base, intent_b_base) in compatible_pairs or \
           (intent_b_base, intent_a_base) in compatible_pairs:
            return "partial"

        # Check for "mixed" intent (always partial)
        if "mixed" in [intent_a, intent_b]:
            return "partial"

        # No alignment
        return "off"

    def _recommend_bridge_type(
        self,
        alignment: Dict[str, str],
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        anchor_profile: AnchorProfile
    ) -> str:
        """
        Recommend bridge_type based on alignment and profiles.

        Next-A1 rules:
        - strong: All alignments are aligned or partial, publisher overlap ≥ 0.7
        - pivot: At least one partial, can be bridged thematically
        - wrapper: Overall is off, need meta-frame

        Returns: "strong", "pivot", or "wrapper"
        """
        overall = alignment["overall"]

        # If overall is off, must use wrapper
        if overall == "off":
            logger.debug("Recommending wrapper due to overall=off")
            return "wrapper"

        # If all aligned, prefer strong
        if all(v == "aligned" for v in alignment.values()):
            logger.debug("Recommending strong due to full alignment")
            return "strong"

        # Check publisher-target topic overlap
        publisher_topics = set(t.lower() for t in publisher_profile.topic_focus)
        target_topics = set(t.lower() for t in target_profile.core_topics)

        if publisher_topics and target_topics:
            overlap = len(publisher_topics & target_topics) / len(publisher_topics)
            if overlap >= 0.7:
                logger.debug("Recommending strong due to high topic overlap", overlap=overlap)
                return "strong"
            elif overlap >= 0.4:
                logger.debug("Recommending pivot due to medium overlap", overlap=overlap)
                return "pivot"

        # Default: if partial alignment, use pivot
        if overall == "partial":
            return "pivot"

        # Fallback
        return "pivot"

    def _generate_article_angle(
        self,
        bridge_type: str,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        serp_intent: str
    ) -> str:
        """
        Generate recommended article angle based on bridge type.

        LLM ENHANCEMENT OPPORTUNITY:
        An LLM could generate much more creative and specific angles by:
        - Analyzing competitor content gaps
        - Identifying unique positioning opportunities
        - Crafting angles that match publisher voice perfectly
        - Suggesting seasonal or trending angles
        """
        if bridge_type == "strong":
            # Direct, natural connection
            return (
                f"Skriv en {self._get_content_format(serp_intent)} som naturligt "
                f"presenterar {target_profile.core_entities[0] if target_profile.core_entities else 'ämnet'} "
                f"inom ramen för {publisher_profile.topic_focus[0] if publisher_profile.topic_focus else 'publikationens fokus'}."
            )

        elif bridge_type == "pivot":
            # Thematic bridge
            return (
                f"Bygg en {self._get_content_format(serp_intent)} kring "
                f"{target_profile.core_topics[0] if target_profile.core_topics else 'relaterat tema'}, "
                f"som naturligt introducerar {target_profile.core_entities[0] if target_profile.core_entities else 'målsidan'} "
                f"som en relevant lösning eller resurs."
            )

        else:  # wrapper
            # Meta-frame strategy
            return (
                f"Skapa en {self._get_content_format(serp_intent)} som behandlar "
                f"ett övergripande tema (metodik, risker, jämförelser, innovation) "
                f"där {target_profile.core_entities[0] if target_profile.core_entities else 'målsidan'} "
                f"kan introduceras som ett relevant exempel efter att ramverket etablerats."
            )

    def _get_content_format(self, serp_intent: str) -> str:
        """Get appropriate content format for intent."""
        format_map = {
            "info_primary": "informativ guide",
            "commercial_research": "jämförande översikt",
            "transactional": "köpguide",
            "support": "hjälpartrikel",
            "mixed": "omfattande artikel"
        }
        return format_map.get(serp_intent, "artikel")

    def _merge_required_subtopics(self, serp_research: SerpResearchExtension) -> List[str]:
        """
        Merge required subtopics from all SERP sets.

        These are "table stakes" - what content must cover to compete.
        """
        all_subtopics = []
        for serp_set in serp_research.serp_sets:
            all_subtopics.extend(serp_set.get("required_subtopics", []))

        # Deduplicate while preserving order
        seen = set()
        merged = []
        for subtopic in all_subtopics:
            subtopic_lower = subtopic.lower()
            if subtopic_lower not in seen:
                seen.add(subtopic_lower)
                merged.append(subtopic)

        return merged[:10]  # Top 10

    def _identify_forbidden_angles(
        self,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        alignment: Dict[str, str]
    ) -> List[str]:
        """
        Identify angles that should be avoided based on constraints.

        E.g., academic publishers shouldn't use aggressive sales copy.
        """
        forbidden = []

        # Publisher tone constraints
        if publisher_profile.tone_class in ["academic", "authority_public"]:
            forbidden.append("Aggressiv säljcopy eller överdrivna claims")
            forbidden.append("Personliga testimonials utan vetenskaplig grund")

        if publisher_profile.tone_class == "academic":
            forbidden.append("Opinionsdrivet innehåll utan källhänvisning")

        # Brand safety constraints
        if publisher_profile.brand_safety_notes:
            forbidden.append(f"Bryt mot: {publisher_profile.brand_safety_notes}")

        # Intent alignment constraints
        if alignment["overall"] == "off":
            forbidden.append("Tvinga in länken utan tydlig tematisk brygga")

        # Target content constraints
        if target_profile.content_type == "product" and publisher_profile.tone_class == "academic":
            forbidden.append("Direkt produktmarknadsföring i akademisk ton")

        return forbidden

    def _build_rationale(
        self,
        alignment: Dict[str, str],
        bridge_type: str,
        serp_intent: str
    ) -> str:
        """
        Build rationale explaining intent decisions.

        Provides transparency for debugging and validation.
        """
        parts = []

        parts.append(f"SERP visar dominant {serp_intent} intent.")

        if alignment["overall"] == "aligned":
            parts.append("Alla dimensioner (anchor, target, publisher) är alignade med SERP.")
            parts.append(f"Rekommenderar {bridge_type} bridge för naturlig koppling.")
        elif alignment["overall"] == "partial":
            parts.append("Partiell alignment mellan dimensioner.")
            parts.append(f"Rekommenderar {bridge_type} bridge för att bygga tematisk koppling.")
        else:
            parts.append("Låg alignment mellan dimensioner.")
            parts.append(f"Rekommenderar {bridge_type} bridge för att etablera meta-ram först.")

        return " ".join(parts)

    def to_job_package_format(self, extension: IntentExtension) -> Dict:
        """
        Convert IntentExtension to BacklinkJobPackage format.

        Returns:
            Dictionary matching intent_extension schema
        """
        return {
            "serp_intent_primary": extension.serp_intent_primary,
            "serp_intent_secondary": extension.serp_intent_secondary,
            "target_page_intent": extension.target_page_intent,
            "anchor_implied_intent": extension.anchor_implied_intent,
            "publisher_role_intent": extension.publisher_role_intent,
            "intent_alignment": extension.intent_alignment,
            "recommended_bridge_type": extension.recommended_bridge_type,
            "recommended_article_angle": extension.recommended_article_angle,
            "required_subtopics": extension.required_subtopics,
            "forbidden_angles": extension.forbidden_angles,
            "notes": extension.notes
        }
