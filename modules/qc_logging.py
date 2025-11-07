"""
QcAndLogging Module

Quality control and validation of Writer Engine output.
"""

import re
from typing import Dict, Any, List
from bs4 import BeautifulSoup

from .base import BaseModule


class QcAndLogging(BaseModule):
    """
    QC and logging for backlink content.

    Input:
        - backlink_job_package: The original job package
        - writer_output: Output from WriterEngineInterface

    Output:
        - qc_report: Dict with status, flags, scores, recommendations
    """

    def run(
        self,
        backlink_job_package: Dict[str, Any],
        writer_output: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run QC validation

        Returns:
            QC report dict
        """
        self.log_step("Running QC validation")

        flags = []
        scores = {}

        # 1. Intent validation
        intent_flags, intent_score = self._validate_intent(
            backlink_job_package,
            writer_output
        )
        flags.extend(intent_flags)
        scores['intent_alignment_score'] = intent_score

        # 2. Anchor risk
        anchor_flags, anchor_risk = self._validate_anchor(
            backlink_job_package,
            writer_output
        )
        flags.extend(anchor_flags)
        scores['anchor_risk_score'] = anchor_risk

        # 3. LSI quality
        lsi_flags, lsi_score = self._validate_lsi(
            writer_output
        )
        flags.extend(lsi_flags)
        scores['lsi_quality_score'] = lsi_score

        # 4. Trust quality
        trust_flags, trust_score = self._validate_trust(
            writer_output
        )
        flags.extend(trust_flags)
        scores['trust_quality_score'] = trust_score

        # 5. Compliance
        compliance_flags = self._validate_compliance(
            backlink_job_package,
            writer_output
        )
        flags.extend(compliance_flags)

        # 6. Word count
        wordcount_flags = self._validate_wordcount(
            backlink_job_package,
            writer_output
        )
        flags.extend(wordcount_flags)

        # Determine overall status
        qc_status = self._determine_status(flags)

        # Generate recommendations
        recommendations = self._generate_recommendations(flags, scores)

        report = {
            "qc_status": qc_status,
            "flags": flags,
            "scores": scores,
            "recommendations": recommendations
        }

        self.log_step(f"QC complete: status={qc_status}, {len(flags)} flags")

        return report

    def _validate_intent(
        self,
        job_package: Dict[str, Any],
        writer_output: Dict[str, Any]
    ) -> tuple:
        """Validate intent alignment"""
        flags = []
        score = 1.0

        intent_ext = job_package.get('intent_extension', {})
        output_intent_ext = writer_output.get('backlink_article_output_v2', {}).get('intent_extension', {})

        recommended_bridge = intent_ext.get('recommended_bridge_type')
        actual_bridge = writer_output.get('backlink_article_output_v2', {}).get('links_extension', {}).get('bridge_type')

        # Check bridge type match
        if recommended_bridge and actual_bridge and recommended_bridge != actual_bridge:
            flags.append({
                "severity": "error",
                "category": "intent_mismatch",
                "message": f"Bridge type mismatch: recommended '{recommended_bridge}' but got '{actual_bridge}'"
            })
            score -= 0.3

        # Check overall alignment
        alignment = intent_ext.get('intent_alignment', {})
        if alignment.get('overall') == 'off':
            flags.append({
                "severity": "error",
                "category": "intent_mismatch",
                "message": "Intent alignment overall is 'off' – content may not match SERP expectations"
            })
            score -= 0.5

        return flags, max(score, 0.0)

    def _validate_anchor(
        self,
        job_package: Dict[str, Any],
        writer_output: Dict[str, Any]
    ) -> tuple:
        """Validate anchor placement and risk"""
        flags = []

        qc_ext = writer_output.get('backlink_article_output_v2', {}).get('qc_extension', {})
        anchor_risk = qc_ext.get('anchor_risk', 'medium')

        html = writer_output.get('full_text_html', '')

        # Check if anchor is in H1/H2
        if html:
            soup = BeautifulSoup(html, 'html.parser')

            h1_text = soup.find('h1')
            h1_text = h1_text.get_text() if h1_text else ""

            h2_texts = [h.get_text() for h in soup.find_all('h2')]

            anchor_text = job_package.get('anchor_profile', {}).get('proposed_text', '')

            if anchor_text in h1_text:
                flags.append({
                    "severity": "error",
                    "category": "anchor_risk",
                    "message": "Anchor found in H1 (forbidden per policy)"
                })

            for h2 in h2_texts:
                if anchor_text in h2:
                    flags.append({
                        "severity": "warning",
                        "category": "anchor_risk",
                        "message": "Anchor found in H2 (discouraged per policy)"
                    })

        # Check anchor risk level
        if anchor_risk == 'high':
            flags.append({
                "severity": "warning",
                "category": "anchor_risk",
                "message": "Anchor risk is HIGH – review placement and context"
            })

        return flags, anchor_risk

    def _validate_lsi(self, writer_output: Dict[str, Any]) -> tuple:
        """Validate LSI quality"""
        flags = []
        score = 1.0

        links_ext = writer_output.get('backlink_article_output_v2', {}).get('links_extension', {})
        near_window = links_ext.get('placement', {}).get('near_window', {})
        lsi_count = near_window.get('lsi_count', 0)

        if lsi_count < 6:
            flags.append({
                "severity": "warning",
                "category": "lsi_missing",
                "message": f"LSI count is {lsi_count}, should be 6-10"
            })
            score = 0.6

        elif lsi_count > 10:
            flags.append({
                "severity": "info",
                "category": "lsi_quality",
                "message": f"LSI count is {lsi_count}, might be over-optimized"
            })
            score = 0.9

        else:
            score = 1.0

        return flags, score

    def _validate_trust(self, writer_output: Dict[str, Any]) -> tuple:
        """Validate trust sources"""
        flags = []
        score = 1.0

        links_ext = writer_output.get('backlink_article_output_v2', {}).get('links_extension', {})
        trust_policy = links_ext.get('trust_policy', {})

        unresolved = trust_policy.get('unresolved', [])

        if unresolved:
            flags.append({
                "severity": "warning",
                "category": "trust_missing",
                "message": f"Unresolved trust sources: {', '.join(unresolved)}"
            })
            score = 0.7

        fallback_used = trust_policy.get('fallback_used', False)
        if fallback_used:
            flags.append({
                "severity": "info",
                "category": "trust_quality",
                "message": "Fallback trust source used"
            })
            score = min(score, 0.85)

        return flags, score

    def _validate_compliance(
        self,
        job_package: Dict[str, Any],
        writer_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate compliance (disclaimers, brand safety)"""
        flags = []

        # Check if disclaimers are needed
        target_url = job_package.get('target_profile', {}).get('url', '')

        # Simple heuristic: check domain for known high-risk categories
        needs_disclaimer = []

        if any(kw in target_url.lower() for kw in ['casino', 'betting', 'spel']):
            needs_disclaimer.append('gambling')

        if any(kw in target_url.lower() for kw in ['lån', 'loan', 'kredit', 'credit']):
            needs_disclaimer.append('finance')

        # Check if disclaimers were injected
        links_ext = writer_output.get('backlink_article_output_v2', {}).get('links_extension', {})
        injected = links_ext.get('compliance', {}).get('disclaimers_injected', [])

        for needed in needs_disclaimer:
            if needed not in injected:
                flags.append({
                    "severity": "error",
                    "category": "compliance",
                    "message": f"Missing required disclaimer: {needed}"
                })

        return flags

    def _validate_wordcount(
        self,
        job_package: Dict[str, Any],
        writer_output: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Validate word count"""
        flags = []

        min_word_count = job_package.get('generation_constraints', {}).get('min_word_count', 900)

        html = writer_output.get('full_text_html', '')
        if html:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text(separator=' ', strip=True)
            words = re.findall(r'\b\w+\b', text)
            actual_count = len(words)

            if actual_count < min_word_count:
                flags.append({
                    "severity": "error",
                    "category": "wordcount",
                    "message": f"Word count {actual_count} is below minimum {min_word_count}"
                })

        return flags

    def _determine_status(self, flags: List[Dict[str, Any]]) -> str:
        """Determine overall QC status"""
        if any(f['severity'] == 'error' for f in flags):
            return "fail"
        elif any(f['severity'] == 'warning' for f in flags):
            return "warning"
        else:
            return "pass"

    def _generate_recommendations(
        self,
        flags: List[Dict[str, Any]],
        scores: Dict[str, Any]
    ) -> List[str]:
        """Generate recommendations based on flags and scores"""
        recommendations = []

        if scores.get('lsi_quality_score', 1.0) < 0.8:
            recommendations.append("Add more LSI terms in anchor near-window (target: 6-10)")

        if scores.get('trust_quality_score', 1.0) < 0.8:
            recommendations.append("Resolve missing trust sources or add more authoritative references")

        if scores.get('intent_alignment_score', 1.0) < 0.7:
            recommendations.append("Review intent alignment – content may not match SERP expectations")

        if not recommendations:
            recommendations.append("Content meets all quality thresholds")

        return recommendations
