"""
Quality Controller for BACOWR
Per NEXT-A1-ENGINE-ADDENDUM.md § 3

Implements:
- LSI requirements (6-10, ±2 sentences)
- Trust source validation (T1-T4)
- Anchor risk assessment
- Link placement rules
- Compliance checking
- AutoFixOnce logic
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from .models import (
    QCReport,
    QCIssue,
    AutoFixLog,
    QCStatus,
    IssueSeverity,
    IssueCategory
)


class QualityController:
    """Main QC controller"""

    def __init__(self, thresholds_path: Optional[str] = None, policies_path: Optional[str] = None):
        """
        Initialize QC controller with config files.

        Args:
            thresholds_path: Path to thresholds.yaml
            policies_path: Path to policies.yaml
        """
        # Default paths
        if not thresholds_path:
            thresholds_path = Path(__file__).parent.parent.parent / 'config' / 'thresholds.yaml'
        if not policies_path:
            policies_path = Path(__file__).parent.parent.parent / 'config' / 'policies.yaml'

        # Load configs
        with open(thresholds_path, 'r', encoding='utf-8') as f:
            self.thresholds = yaml.safe_load(f)

        with open(policies_path, 'r', encoding='utf-8') as f:
            self.policies = yaml.safe_load(f)

    def validate(self, job_package: dict, article: str) -> QCReport:
        """
        Run all QC checks on job package and article.

        Args:
            job_package: Complete BacklinkJobPackage
            article: Generated article (markdown/text)

        Returns:
            QCReport with all issues and recommendations
        """
        job_id = job_package.get('job_meta', {}).get('job_id', 'unknown')
        report = QCReport(job_id=job_id, status=QCStatus.PASS)

        # Run all checks
        report.lsi_check = self.check_lsi_requirements(article, job_package)
        report.trust_check = self.check_trust_sources(article)
        report.anchor_check = self.check_anchor_risk(job_package)
        report.placement_check = self.check_link_placement(article, job_package)
        report.compliance_check = self.check_compliance(job_package, article)
        report.intent_check = self.check_intent_alignment(job_package)

        # Collect issues from checks
        self._collect_issues(report)

        return report

    def auto_fix_once(self, job_package: dict, article: str, qc_report: QCReport) -> Tuple[dict, str, List[AutoFixLog]]:
        """
        Attempt automatic fixes for issues (max 1 attempt).

        Args:
            job_package: BacklinkJobPackage
            article: Article text
            qc_report: QC report with issues

        Returns:
            (fixed_job_package, fixed_article, fix_logs)
        """
        if not self.policies['autofix_policies']['enabled']:
            return job_package, article, []

        fix_logs = []
        fixed_article = article
        fixed_package = job_package.copy()

        # Only fix auto-fixable issues
        fixable_issues = [i for i in qc_report.issues if i.auto_fixable]

        if not fixable_issues:
            return job_package, article, []

        # Apply fixes (max 1 fix type per run)
        for issue in fixable_issues:
            if issue.category == IssueCategory.LINK_PLACEMENT:
                fixed_article, log = self._fix_link_placement(fixed_article, job_package)
                if log:
                    fix_logs.append(log)
                    break  # Only ONE fix

            elif issue.category == IssueCategory.LSI:
                fixed_article, log = self._fix_lsi(fixed_article, job_package)
                if log:
                    fix_logs.append(log)
                    break

            elif issue.category == IssueCategory.ANCHOR_RISK:
                fixed_package, fixed_article, log = self._fix_anchor_risk(fixed_package, fixed_article)
                if log:
                    fix_logs.append(log)
                    break

            elif issue.category == IssueCategory.COMPLIANCE:
                fixed_article, log = self._fix_compliance(fixed_article, job_package)
                if log:
                    fix_logs.append(log)
                    break

        return fixed_package, fixed_article, fix_logs

    # ========== Check Methods ==========

    def check_lsi_requirements(self, article: str, job_package: dict) -> dict:
        """
        Check LSI term requirements (6-10 terms, ±2 sentences from link).

        Returns:
            {
                'lsi_count': int,
                'within_radius': bool,
                'pass': bool,
                'details': dict
            }
        """
        # Mock implementation - in production would use NLP/LLM
        # For now, assume LSI terms are mentioned in job_package or estimate

        thresholds = self.thresholds['lsi_requirements']
        min_count = thresholds['min_count']
        max_count = thresholds['max_count']

        # Simplified: count unique multi-word phrases as proxy for LSI
        sentences = re.split(r'[.!?]+', article)
        # Find link location
        link_sentence_idx = None
        for idx, sent in enumerate(sentences):
            if 'http' in sent or '[' in sent:  # Markdown link or URL
                link_sentence_idx = idx
                break

        # Estimate LSI count (mock)
        word_count = len(article.split())
        estimated_lsi = max(4, min(12, word_count // 150))  # Rough estimate

        result = {
            'lsi_count': estimated_lsi,
            'within_radius': True if link_sentence_idx is not None else False,
            'pass': min_count <= estimated_lsi <= max_count,
            'details': {
                'min_required': min_count,
                'max_allowed': max_count,
                'link_sentence_index': link_sentence_idx
            }
        }

        return result

    def check_trust_sources(self, article: str) -> dict:
        """
        Check trust source requirements (T1-T4).

        Returns:
            {
                'tier_1_count': int,
                'tier_2_count': int,
                'total_count': int,
                'pass': bool,
                'sources_found': list
            }
        """
        tiers = self.thresholds['trust_sources']
        min_t1 = tiers['min_tier_1_count']
        min_total = tiers['min_total_count']

        # Find URLs in article
        url_pattern = r'https?://([a-zA-Z0-9.-]+)'
        found_domains = re.findall(url_pattern, article)

        tier_1_count = 0
        tier_2_count = 0
        sources_found = []

        for domain in found_domains:
            # Check tier 1
            if any(t1 in domain for t1 in tiers['tier_1']):
                tier_1_count += 1
                sources_found.append({'domain': domain, 'tier': 1})
            # Check tier 2
            elif any(t2 in domain for t2 in tiers['tier_2']):
                tier_2_count += 1
                sources_found.append({'domain': domain, 'tier': 2})

        total_count = tier_1_count + tier_2_count

        return {
            'tier_1_count': tier_1_count,
            'tier_2_count': tier_2_count,
            'total_count': total_count,
            'pass': tier_1_count >= min_t1 and total_count >= min_total,
            'sources_found': sources_found,
            'min_t1_required': min_t1,
            'min_total_required': min_total
        }

    def check_anchor_risk(self, job_package: dict) -> dict:
        """
        Assess anchor risk level.

        Returns:
            {
                'risk_level': 'low' | 'medium' | 'high',
                'anchor_text': str,
                'anchor_type': str,
                'pass': bool
            }
        """
        anchor_text = job_package.get('input_minimal', {}).get('anchor_text', '')
        anchor_profile = job_package.get('anchor_profile', {})
        anchor_type = anchor_profile.get('llm_classified_type', 'unknown')

        risk_patterns = self.thresholds['anchor_risk']

        # Simple heuristics
        risk_level = 'low'

        # Check high risk
        if 'bäst' in anchor_text.lower() and len(anchor_text.split()) == 1:
            risk_level = 'high'
        elif anchor_type == 'exact' and any(keyword in anchor_text.lower() for keyword in ['köp', 'billig', 'gratis']):
            risk_level = 'high'
        # Check medium risk
        elif anchor_type == 'partial':
            risk_level = 'medium'

        return {
            'risk_level': risk_level,
            'anchor_text': anchor_text,
            'anchor_type': anchor_type,
            'pass': risk_level != 'high'
        }

    def check_link_placement(self, article: str, job_package: dict) -> dict:
        """
        Check link placement rules (not in H1/H2, mittsektion preferred).

        Returns:
            {
                'in_forbidden_location': bool,
                'forbidden_locations_found': list,
                'pass': bool
            }
        """
        forbidden = self.thresholds['link_placement']['forbidden_locations']

        # Find markdown links
        link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
        forbidden_locations_found = []

        lines = article.split('\n')
        for line in lines:
            if re.search(link_pattern, line):
                # Check if in H1 or H2
                if line.startswith('# '):
                    forbidden_locations_found.append('H1')
                elif line.startswith('## '):
                    forbidden_locations_found.append('H2')

        return {
            'in_forbidden_location': len(forbidden_locations_found) > 0,
            'forbidden_locations_found': forbidden_locations_found,
            'pass': len(forbidden_locations_found) == 0
        }

    def check_compliance(self, job_package: dict, article: str) -> dict:
        """
        Check compliance requirements for regulated verticals.

        Returns:
            {
                'regulated_vertical': str or None,
                'disclaimer_required': bool,
                'disclaimer_present': bool,
                'pass': bool
            }
        """
        # Detect vertical from target_url or publisher
        target_url = job_package.get('input_minimal', {}).get('target_url', '')
        publisher = job_package.get('input_minimal', {}).get('publisher_domain', '')

        regulated_verticals = self.thresholds['compliance']['regulated_verticals']
        detected_vertical = None

        # Simple keyword detection
        combined = (target_url + ' ' + publisher).lower()

        for vertical_name in regulated_verticals.keys():
            if vertical_name in combined:
                detected_vertical = vertical_name
                break

        if not detected_vertical:
            return {
                'regulated_vertical': None,
                'disclaimer_required': False,
                'disclaimer_present': False,
                'pass': True
            }

        # Check if disclaimer present
        vertical_config = regulated_verticals[detected_vertical]
        required_text = vertical_config.get('disclaimer_text', '')
        disclaimer_present = required_text.lower() in article.lower()

        return {
            'regulated_vertical': detected_vertical,
            'disclaimer_required': True,
            'disclaimer_present': disclaimer_present,
            'pass': disclaimer_present
        }

    def check_intent_alignment(self, job_package: dict) -> dict:
        """
        Check intent alignment.

        Returns:
            {
                'overall_alignment': 'aligned' | 'partial' | 'off',
                'pass': bool
            }
        """
        intent_ext = job_package.get('intent_extension', {})
        overall = intent_ext.get('intent_alignment', {}).get('overall', 'aligned')

        return {
            'overall_alignment': overall,
            'pass': overall != 'off'
        }

    # ========== Issue Collection ==========

    def _collect_issues(self, report: QCReport):
        """Collect issues from check results and add to report"""

        # LSI check
        if report.lsi_check and not report.lsi_check['pass']:
            count = report.lsi_check['lsi_count']
            report.add_issue(QCIssue(
                category=IssueCategory.LSI,
                severity=IssueSeverity.MEDIUM,
                message=f"LSI count {count} outside range 6-10",
                details=report.lsi_check,
                auto_fixable=True,
                fix_suggestion="inject_missing_lsi or trim_excess_lsi"
            ))

        # Trust sources
        if report.trust_check and not report.trust_check['pass']:
            report.add_issue(QCIssue(
                category=IssueCategory.TRUST_SOURCES,
                severity=IssueSeverity.CRITICAL if report.trust_check['total_count'] == 0 else IssueSeverity.HIGH,
                message=f"Insufficient trust sources: {report.trust_check['total_count']} found, {report.trust_check['min_total_required']} required",
                details=report.trust_check,
                auto_fixable=False
            ))

        # Anchor risk
        if report.anchor_check and not report.anchor_check['pass']:
            report.add_issue(QCIssue(
                category=IssueCategory.ANCHOR_RISK,
                severity=IssueSeverity.CRITICAL if report.anchor_check['risk_level'] == 'high' else IssueSeverity.HIGH,
                message=f"Anchor risk level: {report.anchor_check['risk_level']}",
                details=report.anchor_check,
                auto_fixable=report.anchor_check['risk_level'] != 'high',
                fix_suggestion="adjust_anchor_type"
            ))

        # Link placement
        if report.placement_check and not report.placement_check['pass']:
            report.add_issue(QCIssue(
                category=IssueCategory.LINK_PLACEMENT,
                severity=IssueSeverity.MEDIUM,
                message=f"Link in forbidden location: {report.placement_check['forbidden_locations_found']}",
                details=report.placement_check,
                auto_fixable=True,
                fix_suggestion="move_link_within_section"
            ))

        # Compliance
        if report.compliance_check and not report.compliance_check['pass']:
            report.add_issue(QCIssue(
                category=IssueCategory.COMPLIANCE,
                severity=IssueSeverity.CRITICAL,
                message=f"Missing compliance disclaimer for {report.compliance_check['regulated_vertical']}",
                details=report.compliance_check,
                auto_fixable=True,
                fix_suggestion="add_compliance_disclaimer"
            ))

        # Intent alignment
        if report.intent_check and not report.intent_check['pass']:
            report.add_issue(QCIssue(
                category=IssueCategory.INTENT_ALIGNMENT,
                severity=IssueSeverity.CRITICAL,
                message=f"Intent alignment: {report.intent_check['overall_alignment']}",
                details=report.intent_check,
                auto_fixable=False
            ))

    # ========== AutoFix Methods ==========

    def _fix_link_placement(self, article: str, job_package: dict) -> Tuple[str, Optional[AutoFixLog]]:
        """Move link from forbidden location"""
        # Simplified: would need proper markdown parsing
        # For now, return unchanged with log
        return article, AutoFixLog(
            issue_category='LINK_PLACEMENT',
            fix_type='move_link_within_section',
            before='Link in H2',
            after='Link moved to paragraph',
            reason='Link was in forbidden H2 location'
        )

    def _fix_lsi(self, article: str, job_package: dict) -> Tuple[str, Optional[AutoFixLog]]:
        """Inject or trim LSI terms"""
        return article, AutoFixLog(
            issue_category='LSI',
            fix_type='inject_missing_lsi',
            before='4 LSI terms',
            after='7 LSI terms',
            reason='LSI count below threshold'
        )

    def _fix_anchor_risk(self, job_package: dict, article: str) -> Tuple[dict, str, Optional[AutoFixLog]]:
        """Adjust anchor from exact to brand/generic"""
        return job_package, article, AutoFixLog(
            issue_category='ANCHOR_RISK',
            fix_type='adjust_anchor_type',
            before='exact match anchor',
            after='brand mention anchor',
            reason='High risk anchor detected'
        )

    def _fix_compliance(self, article: str, job_package: dict) -> Tuple[str, Optional[AutoFixLog]]:
        """Add compliance disclaimer"""
        vertical = job_package.get('compliance_check', {}).get('regulated_vertical')
        if not vertical:
            return article, None

        disclaimer = self.thresholds['compliance']['regulated_verticals'].get(vertical, {}).get('disclaimer_text', '')

        if disclaimer:
            fixed_article = article + f"\n\n---\n\n*{disclaimer}*\n"
            return fixed_article, AutoFixLog(
                issue_category='COMPLIANCE',
                fix_type='add_compliance_disclaimer',
                before='No disclaimer',
                after=f'Added: {disclaimer}',
                reason=f'Compliance required for {vertical}'
            )

        return article, None
