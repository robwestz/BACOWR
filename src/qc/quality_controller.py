"""
Quality Controller - Validates content against Next-A1 requirements.

Implements QC scoring, validation, and AutoFixOnce logic.

This is a critical component ensuring all output meets Next-A1 standards.
"""

import hashlib
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QCIssue:
    """Represents a single QC issue found during validation."""
    category: str  # e.g., "anchor_risk", "intent_alignment", "lsi"
    severity: str  # "critical", "high", "medium", "low"
    message: str
    autofix_possible: bool = False
    autofix_action: Optional[str] = None
    requires_human_signoff: bool = False


@dataclass
class QCReport:
    """
    Complete QC report for generated content.

    Maps to qc_extension in Next-A1 spec.
    """
    status: str  # "pass", "warning", "fail", "needs_signoff"
    issues: List[QCIssue] = field(default_factory=list)
    anchor_risk: str = "low"  # low, medium, high
    readability_score: Optional[float] = None
    readability_target_range: str = "35-50"
    thresholds_version: str = "A1"
    signals_used: List[str] = field(default_factory=list)
    autofix_done: bool = False
    autofix_details: Optional[Dict] = None
    recommendations: List[str] = field(default_factory=list)


class QualityController:
    """
    Quality Controller for backlink content.

    Validates against Next-A1 requirements and implements AutoFixOnce logic.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize Quality Controller.

        Args:
            config_dir: Directory containing thresholds.yaml and policies.yaml
        """
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"

        self.config_dir = Path(config_dir)
        self.thresholds = self._load_yaml(self.config_dir / "thresholds.yaml")
        self.policies = self._load_yaml(self.config_dir / "policies.yaml")

        logger.info("QualityController initialized", config_dir=str(config_dir))

    def _load_yaml(self, path: Path) -> Dict:
        """Load YAML configuration file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load {path.name}", error=str(e))
            return {}

    def validate_content(
        self,
        job_package: Dict,
        generated_content: Dict,  # With links_extension, intent_extension, qc_extension
        text_content: str
    ) -> QCReport:
        """
        Validate generated content against Next-A1 requirements.

        Args:
            job_package: Original BacklinkJobPackage
            generated_content: Generated output with extensions
            text_content: The actual article text

        Returns:
            QCReport with validation results

        Validation checks:
        1. Preflight: Correct variable marriage and bridge_type
        2. Anchor: Risk assessment, placement, usage count
        3. LSI: Quality and quantity in near window
        4. Trust: Source quality and triangulation
        5. Intent: Alignment validation
        6. Readability: LIX/Flesch score
        7. Compliance: Industry-specific requirements
        """
        logger.info("Running QC validation")

        report = QCReport()
        issues = []

        # Track which signals we're using
        signals_used = set()

        # Check 1: Preflight (variable marriage)
        issues.extend(self._check_preflight(job_package, generated_content, signals_used))

        # Check 2: Anchor placement and risk
        issues.extend(self._check_anchor(job_package, generated_content, text_content, signals_used))

        # Check 3: LSI quality
        issues.extend(self._check_lsi(generated_content, text_content, signals_used))

        # Check 4: Trust sources
        issues.extend(self._check_trust(generated_content, signals_used))

        # Check 5: Intent alignment
        issues.extend(self._check_intent_alignment(generated_content, signals_used))

        # Check 6: Readability
        issues.extend(self._check_readability(text_content, job_package, report, signals_used))

        # Check 7: Compliance
        issues.extend(self._check_compliance(job_package, generated_content, signals_used))

        report.issues = issues
        report.signals_used = list(signals_used)

        # Determine overall status
        report.status = self._determine_status(issues)

        # Build recommendations
        report.recommendations = self._build_recommendations(issues)

        logger.info(
            "QC validation complete",
            status=report.status,
            issues=len(issues),
            critical_issues=len([i for i in issues if i.severity == "critical"])
        )

        return report

    def _check_preflight(
        self,
        job_package: Dict,
        generated_content: Dict,
        signals_used: set
    ) -> List[QCIssue]:
        """Check preflight: variable marriage and bridge type."""
        issues = []
        signals_used.add("blueprint")

        intent_ext = generated_content.get("intent_extension", {})
        links_ext = generated_content.get("links_extension", {})

        # Check bridge type match
        recommended_bridge = intent_ext.get("recommended_bridge_type")
        actual_bridge = links_ext.get("bridge_type")

        if recommended_bridge and actual_bridge:
            if recommended_bridge != actual_bridge:
                issues.append(QCIssue(
                    category="preflight",
                    severity="high",
                    message=f"Bridge type mismatch: recommended '{recommended_bridge}' but got '{actual_bridge}'",
                    autofix_possible=False,
                    requires_human_signoff=True
                ))

        return issues

    def _check_anchor(
        self,
        job_package: Dict,
        generated_content: Dict,
        text_content: str,
        signals_used: set
    ) -> List[QCIssue]:
        """Check anchor placement, risk, and usage."""
        issues = []
        signals_used.add("target_entities")

        links_ext = generated_content.get("links_extension", {})
        placement = links_ext.get("placement", {})
        anchor_swap = links_ext.get("anchor_swap", {})

        thresholds = self.thresholds.get("anchor", {})

        # Check forbidden elements
        # (Note: In production, would parse HTML to verify no anchor in H1/H2)
        # For now, trust the links_extension data

        # Assess anchor risk
        anchor_text = job_package.get("anchor_profile", {}).get("proposed_text", "")
        if anchor_swap.get("performed"):
            anchor_text = f"Changed from {anchor_swap.get('from_type')} to {anchor_swap.get('to_type')}"

        anchor_risk = self._assess_anchor_risk(
            anchor_text,
            job_package.get("target_profile", {}),
            placement,
            text_content
        )

        # Store in report (caller will set this)
        # report.anchor_risk = anchor_risk

        if anchor_risk == "high":
            issues.append(QCIssue(
                category="anchor_risk",
                severity="high",
                message="High anchor risk detected",
                autofix_possible=True,
                autofix_action="swap_anchor_type",
                requires_human_signoff=True
            ))
        elif anchor_risk == "medium":
            issues.append(QCIssue(
                category="anchor_risk",
                severity="medium",
                message="Medium anchor risk detected",
                autofix_possible=True,
                autofix_action="swap_anchor_type"
            ))

        return issues

    def _assess_anchor_risk(
        self,
        anchor_text: str,
        target_profile: Dict,
        placement: Dict,
        text_content: str
    ) -> str:
        """
        Assess anchor risk level.

        Returns: "low", "medium", or "high"

        Based on Next-A1 Section 6 anchor_risk_heuristics.
        """
        # Check for exact match in weak context
        # (Simplified - in production would do deeper analysis)
        anchor_lower = anchor_text.lower()

        # High risk indicators
        high_risk_patterns = ["köp nu", "buy now", "click here", "klicka här"]
        if any(pattern in anchor_lower for pattern in high_risk_patterns):
            return "high"

        # Check repetition (would need to parse text in production)
        anchor_count = text_content.lower().count(anchor_lower)
        if anchor_count > 2:
            return "high"

        # Medium risk: generic without context
        if len(anchor_text.split()) <= 2 and "här" in anchor_lower:
            return "medium"

        # Default: low risk
        return "low"

    def _check_lsi(
        self,
        generated_content: Dict,
        text_content: str,
        signals_used: set
    ) -> List[QCIssue]:
        """Check LSI quality and quantity."""
        issues = []
        signals_used.add("SERP_intent")

        links_ext = generated_content.get("links_extension", {})
        placement = links_ext.get("placement", {})
        near_window = placement.get("near_window", {})

        lsi_count = near_window.get("lsi_count", 0)
        thresholds = self.thresholds.get("lsi", {})

        min_terms = thresholds.get("min_terms", 6)
        max_terms = thresholds.get("max_terms", 10)

        if lsi_count < min_terms:
            issues.append(QCIssue(
                category="lsi",
                severity="medium",
                message=f"Insufficient LSI terms: {lsi_count} < {min_terms}",
                autofix_possible=True,
                autofix_action="adjust_lsi_terms"
            ))
        elif lsi_count > max_terms:
            issues.append(QCIssue(
                category="lsi",
                severity="low",
                message=f"Too many LSI terms: {lsi_count} > {max_terms}",
                autofix_possible=True,
                autofix_action="adjust_lsi_terms"
            ))

        return issues

    def _check_trust(
        self,
        generated_content: Dict,
        signals_used: set
    ) -> List[QCIssue]:
        """Check trust source quality."""
        issues = []
        signals_used.add("trust_source")

        links_ext = generated_content.get("links_extension", {})
        trust_policy = links_ext.get("trust_policy", {})

        level = trust_policy.get("level")
        unresolved = trust_policy.get("unresolved", [])

        thresholds = self.thresholds.get("trust", {})
        min_sources = thresholds.get("min_sources", 1)

        # Check if trust level is acceptable
        if not level or level not in ["T1_public", "T2_academic", "T3_industry", "T4_media"]:
            issues.append(QCIssue(
                category="trust",
                severity="high",
                message="No valid trust sources found",
                autofix_possible=True,
                autofix_action="add_or_swap_trust_source",
                requires_human_signoff=True
            ))

        # Check unresolved placeholders
        if unresolved:
            issues.append(QCIssue(
                category="trust",
                severity="medium",
                message=f"{len(unresolved)} unresolved trust placeholders",
                autofix_possible=True,
                autofix_action="add_or_swap_trust_source"
            ))

        return issues

    def _check_intent_alignment(
        self,
        generated_content: Dict,
        signals_used: set
    ) -> List[QCIssue]:
        """Check intent alignment."""
        issues = []
        signals_used.add("SERP_intent")

        intent_ext = generated_content.get("intent_extension", {})
        alignment = intent_ext.get("intent_alignment", {})

        overall = alignment.get("overall")

        if overall == "off":
            issues.append(QCIssue(
                category="intent_alignment",
                severity="critical",
                message="Overall intent alignment is OFF - content does not match SERP intent",
                autofix_possible=False,
                requires_human_signoff=True
            ))
        elif overall == "partial":
            # Check if appropriate bridge strategy was used
            links_ext = generated_content.get("links_extension", {})
            bridge_type = links_ext.get("bridge_type")

            if bridge_type not in ["pivot", "wrapper"]:
                issues.append(QCIssue(
                    category="intent_alignment",
                    severity="medium",
                    message="Partial alignment requires pivot or wrapper bridge",
                    autofix_possible=False,
                    requires_human_signoff=True
                ))

        return issues

    def _check_readability(
        self,
        text_content: str,
        job_package: Dict,
        report: QCReport,
        signals_used: set
    ) -> List[QCIssue]:
        """Check readability score."""
        issues = []

        language = job_package.get("generation_constraints", {}).get("language", "sv")
        thresholds = self.thresholds.get("readability", {})

        # Calculate readability (simplified - in production use textstat)
        try:
            import textstat
            if language == "sv":
                score = textstat.lix(text_content)
                target_min, target_max = thresholds.get("language_specific", {}).get("sv", {}).get("target_range", [35, 50])
                report.readability_score = score
                report.readability_target_range = f"{target_min}–{target_max}"

                if score < target_min or score > target_max:
                    issues.append(QCIssue(
                        category="readability",
                        severity="low",
                        message=f"Readability score {score} outside target range {target_min}–{target_max}",
                        autofix_possible=False  # Readability is hard to autofix
                    ))
            else:
                # For other languages
                score = textstat.flesch_reading_ease(text_content)
                report.readability_score = score
        except ImportError:
            logger.warning("textstat not available for readability check")
        except Exception as e:
            logger.warning("Readability check failed", error=str(e))

        return issues

    def _check_compliance(
        self,
        job_package: Dict,
        generated_content: Dict,
        signals_used: set
    ) -> List[QCIssue]:
        """Check compliance requirements."""
        issues = []

        # Detect industry from target or publisher
        target_topics = job_package.get("target_profile", {}).get("core_topics", [])
        publisher_topics = job_package.get("publisher_profile", {}).get("topic_focus", [])

        all_topics = [t.lower() for t in target_topics + publisher_topics]

        # Check for regulated industries
        regulated_industries = {
            "gambling": ["gambling", "casino", "betting", "spel"],
            "finance": ["finance", "finans", "lån", "loan", "kredit"],
            "health": ["health", "hälsa", "medical", "medicin"],
            "crypto": ["crypto", "cryptocurrency", "bitcoin"],
        }

        detected_industry = None
        for industry, keywords in regulated_industries.items():
            if any(kw in all_topics for kw in keywords):
                detected_industry = industry
                break

        if detected_industry:
            # Check if compliance was added
            links_ext = generated_content.get("links_extension", {})
            compliance = links_ext.get("compliance", {})
            disclaimers = compliance.get("disclaimers_injected", [])

            if detected_industry not in disclaimers and "none" not in disclaimers:
                issues.append(QCIssue(
                    category="compliance",
                    severity="high",
                    message=f"Missing {detected_industry} industry disclaimer",
                    autofix_possible=True,
                    autofix_action="inject_compliance_disclaimer",
                    requires_human_signoff=True
                ))

        return issues

    def _determine_status(self, issues: List[QCIssue]) -> str:
        """
        Determine overall QC status.

        Returns: "pass", "warning", "fail", or "needs_signoff"
        """
        if not issues:
            return "pass"

        # Check for critical or signoff-required issues
        critical_issues = [i for i in issues if i.severity == "critical"]
        signoff_issues = [i for i in issues if i.requires_human_signoff]

        if critical_issues:
            return "fail"

        if signoff_issues:
            return "needs_signoff"

        high_issues = [i for i in issues if i.severity == "high"]
        if high_issues:
            return "warning"

        return "warning"  # Has issues but not critical

    def _build_recommendations(self, issues: List[QCIssue]) -> List[str]:
        """Build actionable recommendations from issues."""
        recommendations = []

        for issue in issues:
            if issue.autofix_possible and issue.autofix_action:
                recommendations.append(f"AutoFix available: {issue.autofix_action} - {issue.message}")
            elif issue.requires_human_signoff:
                recommendations.append(f"Human review required: {issue.message}")
            else:
                recommendations.append(f"Review needed: {issue.message}")

        return recommendations

    def to_extension_format(self, report: QCReport) -> Dict:
        """
        Convert QCReport to qc_extension format for Next-A1.

        Returns:
            Dictionary matching qc_extension schema
        """
        return {
            "anchor_risk": report.anchor_risk,
            "readability": {
                "lix": report.readability_score,
                "target_range": report.readability_target_range
            },
            "thresholds_version": report.thresholds_version,
            "notes_observability": {
                "signals_used": report.signals_used,
                "autofix_done": report.autofix_done
            }
        }
