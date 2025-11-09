"""
Next-A1 QC Validator.

Validates BacklinkArticle output against all 8 Next-A1 QC criteria:
1. Preflight: Correct variabelgifte and bridge_type
2. Draft: Flow, structure, clear narrative
3. Anchor: Natural placement and low/medium risk
4. Trust: Source quality and triangulation
5. Intent: Alignment with dominant SERP intent
6. LSI: 6-10 relevant terms in near-window
7. Fit: Voice and tone match publisher
8. Compliance: Disclaimers and policy requirements
"""

from typing import Dict, Any, List, Tuple
import re
from enum import Enum


class QCStatus(str, Enum):
    """QC status values."""
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class QCCriterion(str, Enum):
    """QC criterion identifiers."""
    PREFLIGHT = "preflight"
    DRAFT = "draft"
    ANCHOR = "anchor"
    TRUST = "trust"
    INTENT = "intent"
    LSI = "lsi"
    FIT = "fit"
    COMPLIANCE = "compliance"


class NextA1QCValidator:
    """
    Validates content against Next-A1 specification.

    All 8 QC criteria must pass or have acceptable warnings.
    BLOCKED status on any criterion fails the entire validation.
    """

    def __init__(self):
        """Initialize QC Validator."""
        pass

    def validate(
        self,
        article_content: str,
        links_extension: Dict[str, Any],
        intent_extension: Dict[str, Any],
        qc_extension: Dict[str, Any],
        serp_research_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform complete Next-A1 QC validation.

        Args:
            article_content: Generated article text
            links_extension: Next-A1 links_extension
            intent_extension: Next-A1 intent_extension
            qc_extension: Next-A1 qc_extension
            serp_research_extension: Next-A1 serp_research_extension

        Returns:
            QC report with status, scores, issues, recommendations
        """
        results = {}
        all_issues = []
        scores = {}

        # 1. Preflight validation
        preflight_result = self._validate_preflight(links_extension, intent_extension)
        results["preflight"] = preflight_result
        scores["preflight"] = preflight_result["score"]
        if preflight_result["issues"]:
            all_issues.extend([f"[Preflight] {i}" for i in preflight_result["issues"]])

        # 2. Draft validation
        draft_result = self._validate_draft(article_content, intent_extension)
        results["draft"] = draft_result
        scores["draft"] = draft_result["score"]
        if draft_result["issues"]:
            all_issues.extend([f"[Draft] {i}" for i in draft_result["issues"]])

        # 3. Anchor validation
        anchor_result = self._validate_anchor(
            article_content, links_extension, qc_extension
        )
        results["anchor"] = anchor_result
        scores["anchor"] = anchor_result["score"]
        if anchor_result["issues"]:
            all_issues.extend([f"[Anchor] {i}" for i in anchor_result["issues"]])

        # 4. Trust validation
        trust_result = self._validate_trust(article_content, links_extension)
        results["trust"] = trust_result
        scores["trust"] = trust_result["score"]
        if trust_result["issues"]:
            all_issues.extend([f"[Trust] {i}" for i in trust_result["issues"]])

        # 5. Intent validation
        intent_result = self._validate_intent(intent_extension)
        results["intent"] = intent_result
        scores["intent"] = intent_result["score"]
        if intent_result["issues"]:
            all_issues.extend([f"[Intent] {i}" for i in intent_result["issues"]])

        # 6. LSI validation
        lsi_result = self._validate_lsi(
            article_content, links_extension, intent_extension
        )
        results["lsi"] = lsi_result
        scores["lsi"] = lsi_result["score"]
        if lsi_result["issues"]:
            all_issues.extend([f"[LSI] {i}" for i in lsi_result["issues"]])

        # 7. Fit validation
        fit_result = self._validate_fit(article_content, qc_extension)
        results["fit"] = fit_result
        scores["fit"] = fit_result["score"]
        if fit_result["issues"]:
            all_issues.extend([f"[Fit] {i}" for i in fit_result["issues"]])

        # 8. Compliance validation
        compliance_result = self._validate_compliance(
            article_content, links_extension
        )
        results["compliance"] = compliance_result
        scores["compliance"] = compliance_result["score"]
        if compliance_result["issues"]:
            all_issues.extend([f"[Compliance] {i}" for i in compliance_result["issues"]])

        # Determine overall status
        overall_status = self._determine_overall_status(results)
        overall_score = sum(scores.values()) / len(scores) if scores else 0

        # Generate recommendations
        recommendations = self._generate_recommendations(results, all_issues)

        return {
            "status": overall_status.value,
            "overall_score": round(overall_score, 2),
            "scores": scores,
            "results": results,
            "issues": all_issues,
            "recommendations": recommendations,
            "thresholds_version": "A1"
        }

    def _validate_preflight(
        self,
        links_extension: Dict[str, Any],
        intent_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate preflight: Correct variabelgifte and bridge_type selection.

        QC Definition: "Korrekt variabelgifte och rimligt vald bridge_type"
        """
        issues = []
        score = 100

        # Check bridge_type consistency
        recommended = intent_extension.get("recommended_bridge_type")
        actual = links_extension.get("bridge_type")

        if recommended != actual:
            issues.append(
                f"Bridge type mismatch: recommended '{recommended}' but used '{actual}'"
            )
            score -= 30

        # Check intent alignment with bridge type
        alignment = intent_extension.get("intent_alignment", {})
        overall = alignment.get("overall")

        # Next-A1 rule validation
        if actual == "strong" and overall != "aligned":
            issues.append("Strong bridge requires 'aligned' overall intent")
            score -= 40

        if actual == "wrapper" and overall != "off":
            issues.append("Wrapper bridge should only be used when overall alignment is 'off'")
            score -= 30

        # Check if any component is 'off'
        if actual == "strong" and any(
            alignment.get(k) == "off"
            for k in ["anchor_vs_serp", "target_vs_serp", "publisher_vs_serp"]
        ):
            issues.append("Strong bridge not allowed when any alignment is 'off'")
            score -= 50

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_draft(
        self,
        article_content: str,
        intent_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate draft: Flow, structure, and clear narrative.

        QC Definition: "Flyt, struktur och tydlig röd tråd"
        """
        issues = []
        score = 100

        # Check minimum length (900 words from spec)
        word_count = len(article_content.split())
        if word_count < 900:
            issues.append(f"Content too short: {word_count} words (minimum 900)")
            score -= 40

        # Check for headers (H2/H3 structure)
        h2_count = len(re.findall(r'<h2[^>]*>.*?</h2>', article_content, re.IGNORECASE | re.DOTALL))
        if h2_count < 2:
            issues.append(f"Insufficient structure: only {h2_count} H2 headers (need ≥2)")
            score -= 20

        # Check for required subtopics coverage
        required_subtopics = intent_extension.get("required_subtopics", [])
        content_lower = article_content.lower()

        covered_subtopics = sum(
            1 for subtopic in required_subtopics
            if subtopic.lower() in content_lower
        )

        coverage_rate = covered_subtopics / len(required_subtopics) if required_subtopics else 1.0
        if coverage_rate < 0.6:
            issues.append(
                f"Poor subtopic coverage: {covered_subtopics}/{len(required_subtopics)} "
                f"({coverage_rate*100:.0f}%, need ≥60%)"
            )
            score -= 30

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues,
            "metadata": {
                "word_count": word_count,
                "h2_count": h2_count,
                "subtopic_coverage": f"{coverage_rate*100:.0f}%"
            }
        }

    def _validate_anchor(
        self,
        article_content: str,
        links_extension: Dict[str, Any],
        qc_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate anchor: Natural placement and acceptable risk.

        QC Definition: "Naturlig placering och ankarrisk låg/medel"
        """
        issues = []
        score = 100

        # Check anchor risk
        anchor_risk = qc_extension.get("anchor_risk")
        if anchor_risk == "high":
            issues.append("High anchor risk detected")
            score -= 50
        elif anchor_risk == "medium":
            score -= 15  # Minor penalty

        # Check anchor not in H1/H2 (Next-A1 rule)
        # Look for [[LINK]] or actual link in headers
        h1_content = re.findall(r'<h1[^>]*>(.*?)</h1>', article_content, re.IGNORECASE | re.DOTALL)
        h2_content = re.findall(r'<h2[^>]*>(.*?)</h2>', article_content, re.IGNORECASE | re.DOTALL)

        for h1 in h1_content:
            if '[[LINK]]' in h1 or '<a ' in h1:
                issues.append("Anchor found in H1 header (forbidden by Next-A1)")
                score -= 60

        for h2 in h2_content:
            if '[[LINK]]' in h2 or '<a ' in h2:
                issues.append("Anchor found in H2 header (forbidden by Next-A1)")
                score -= 40

        # Check placement (should be in middle sections)
        placement = links_extension.get("placement", {})
        paragraph_index = placement.get("paragraph_index_in_section", 0)

        if paragraph_index == 0:
            issues.append("Link in first paragraph of section - may feel forced")
            score -= 10

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_trust(
        self,
        article_content: str,
        links_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate trust: Source quality and triangulation.

        QC Definition: "Källkvalitet och rimlig triangulering mellan Publisher, TRUST och Target"
        """
        issues = []
        score = 100

        trust_policy = links_extension.get("trust_policy", {})
        level = trust_policy.get("level")
        unresolved = trust_policy.get("unresolved", [])

        # Check trust level
        if not level:
            issues.append("No trust source specified")
            score -= 40
        elif level == "T4_media":
            issues.append("Using T4 (media) trust - prefer T1-T3 if possible")
            score -= 10

        # Check for unresolved trust sources
        if unresolved:
            issues.append(f"Unresolved trust sources: {', '.join(unresolved[:3])}")
            score -= 20

        # Check fallback usage
        if trust_policy.get("fallback_used"):
            score -= 5  # Minor penalty for fallback

        # Check for competitive links (forbidden by Next-A1)
        # This is simplified - in real implementation, need target URL to compare
        if any(keyword in article_content.lower() for keyword in ['competitor', 'konkurrent']):
            issues.append("Possible competitive reference detected - review manually")
            score -= 15

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_intent(
        self,
        intent_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate intent: Alignment with dominant SERP intent.

        QC Definition: "Giftemålet följer dominant SERP-intent; anchor/target/publisher är inte 'off'"
        """
        issues = []
        score = 100

        alignment = intent_extension.get("intent_alignment", {})
        overall = alignment.get("overall")

        # Critical: overall cannot be 'off'
        if overall == "off":
            issues.append("Overall intent alignment is 'off' - requires wrapper or reconsideration")
            score -= 70

        # Check individual alignments
        for component, value in alignment.items():
            if component == "overall":
                continue

            if value == "off":
                issues.append(f"{component} alignment is 'off'")
                score -= 20

        # Check data confidence
        confidence = intent_extension.get("notes", {}).get("data_confidence")
        if confidence == "low":
            issues.append("Low data confidence in intent analysis")
            score -= 15

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_lsi(
        self,
        article_content: str,
        links_extension: Dict[str, Any],
        intent_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate LSI: 6-10 relevant terms in near-window.

        QC Definition: "6–10 relevanta LSI-termer i närfönster med god kvalitet"
        """
        issues = []
        score = 100

        near_window = links_extension.get("placement", {}).get("near_window", {})
        lsi_count = near_window.get("lsi_count", 0)

        # Check LSI count (6-10 required)
        if lsi_count < 6:
            issues.append(f"Insufficient LSI terms: {lsi_count} (need 6-10)")
            score -= 40
        elif lsi_count > 10:
            issues.append(f"Too many LSI terms: {lsi_count} (max 10) - may feel overoptimized")
            score -= 15

        # Check near-window configuration
        radius = near_window.get("radius", 0)
        if radius < 2:
            issues.append(f"Near-window radius too small: {radius} sentences (need ≥2)")
            score -= 20

        # Check required subtopics are covered
        required = intent_extension.get("required_subtopics", [])
        content_lower = article_content.lower()

        covered = sum(1 for sub in required if sub.lower() in content_lower)
        if required and covered == 0:
            issues.append("None of the required subtopics are covered")
            score -= 30

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_fit(
        self,
        article_content: str,
        qc_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate fit: Voice and tone match publisher.

        QC Definition: "Röst och ton matchar publikationssajten"
        """
        issues = []
        score = 100

        # Check readability (LIX score)
        readability = qc_extension.get("readability", {})
        lix = readability.get("lix")
        target_range = readability.get("target_range", "35–45")

        if lix:
            try:
                min_lix, max_lix = map(int, target_range.split("–"))
                if lix < min_lix or lix > max_lix:
                    issues.append(
                        f"Readability outside target range: LIX {lix} "
                        f"(target: {target_range})"
                    )
                    score -= 20
            except:
                pass

        # Check if autofix was needed
        observability = qc_extension.get("notes_observability", {})
        if observability.get("autofix_done"):
            score -= 5  # Minor penalty if autofix was needed

        # Check signals used
        signals = observability.get("signals_used", [])
        required_signals = ["publisher_profile", "SERP_intent"]

        for required in required_signals:
            if required not in signals:
                issues.append(f"Missing signal in analysis: {required}")
                score -= 10

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _validate_compliance(
        self,
        article_content: str,
        links_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate compliance: Disclaimers and policy requirements.

        QC Definition: "Disclaimers, policykrav och PII-hantering uppfylls"
        """
        issues = []
        score = 100

        compliance = links_extension.get("compliance", {})
        disclaimers = compliance.get("disclaimers_injected", [])

        # Check if sensitive topics require disclaimers
        content_lower = article_content.lower()

        # Gambling
        if any(word in content_lower for word in ["casino", "betting", "spel", "odds"]):
            if "gambling" not in disclaimers:
                issues.append("Gambling content without disclaimer")
                score -= 40

        # Finance
        if any(word in content_lower for word in ["invest", "trading", "aktie", "fond", "finansiell"]):
            if "finance" not in disclaimers:
                issues.append("Financial content without disclaimer")
                score -= 40

        # Health
        if any(word in content_lower for word in ["medicin", "treatment", "diagnos", "hälsa", "health"]):
            if "health" not in disclaimers:
                issues.append("Health content without disclaimer")
                score -= 40

        # Crypto
        if any(word in content_lower for word in ["crypto", "bitcoin", "blockchain", "kryptovaluta"]):
            if "crypto" not in disclaimers:
                issues.append("Crypto content without disclaimer")
                score -= 40

        status = "BLOCKED" if score < 50 else "WARNING" if score < 80 else "PASS"

        return {
            "status": status,
            "score": max(0, score),
            "issues": issues
        }

    def _determine_overall_status(self, results: Dict[str, Any]) -> QCStatus:
        """Determine overall QC status from individual results."""
        # If any criterion is BLOCKED, overall is BLOCKED
        if any(r["status"] == "BLOCKED" for r in results.values()):
            return QCStatus.BLOCKED

        # If any criterion is WARNING, overall is WARNING
        if any(r["status"] == "WARNING" for r in results.values()):
            return QCStatus.WARNING

        # All PASS
        return QCStatus.PASS

    def _generate_recommendations(
        self,
        results: Dict[str, Any],
        issues: List[str]
    ) -> List[str]:
        """Generate actionable recommendations based on QC results."""
        recommendations = []

        # Preflight issues
        if results["preflight"]["status"] != "PASS":
            recommendations.append("Review bridge type selection - may need to adjust intent alignment")

        # Draft issues
        if results["draft"]["score"] < 80:
            recommendations.append("Improve content structure - add more H2 sections and cover required subtopics")

        # Anchor issues
        if results["anchor"]["status"] == "BLOCKED":
            recommendations.append("CRITICAL: Remove anchor from H1/H2 or reduce anchor risk")
        elif results["anchor"]["score"] < 80:
            recommendations.append("Consider adjusting anchor placement for more natural integration")

        # Trust issues
        if results["trust"]["score"] < 70:
            recommendations.append("Add higher-quality trust sources (prefer T1-T3 over T4)")

        # Intent issues
        if results["intent"]["status"] == "BLOCKED":
            recommendations.append("CRITICAL: Intent alignment is 'off' - use wrapper bridge or reconsider placement")

        # LSI issues
        if results["lsi"]["score"] < 80:
            recommendations.append("Add more LSI terms in near-window (target: 6-10 relevant terms)")

        # Fit issues
        if results["fit"]["score"] < 80:
            recommendations.append("Adjust tone/voice to better match publisher profile")

        # Compliance issues
        if results["compliance"]["status"] != "PASS":
            recommendations.append("CRITICAL: Add required disclaimers for sensitive content")

        # If no recommendations, add positive feedback
        if not recommendations:
            recommendations.append("Content meets all Next-A1 quality criteria")

        return recommendations
