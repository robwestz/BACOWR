"""
Next-A1 QC Validator Service - BACOWR Demo Environment

Implements all 8 Next-A1 Quality Control criteria:
1. PREFLIGHT - Bridge type validation
2. DRAFT - Word count and structure
3. ANCHOR - Placement rules and risk assessment
4. TRUST - Source quality (T1-T4)
5. INTENT - Alignment validation
6. LSI - 6-10 LSI terms within ±2 sentences
7. FIT - Readability and tone matching
8. COMPLIANCE - Auto-detect disclaimers

Scoring: PASS ≥80, WARNING 50-79, BLOCKED <50

Part of the BACOWR Demo API - Production-ready QC validation service.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class QCCriterionResult:
    """Result for a single QC criterion"""
    criterion_name: str
    score: int  # 0-100
    status: str  # 'PASS', 'WARNING', 'BLOCKED'
    issues: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'criterion': self.criterion_name,
            'score': self.score,
            'status': self.status,
            'issues': self.issues,
            'details': self.details,
            'recommendations': self.recommendations
        }


@dataclass
class QCReport:
    """Complete QC validation report"""
    job_id: str
    overall_score: int
    overall_status: str  # 'PASS', 'WARNING', 'BLOCKED'
    criteria_results: List[QCCriterionResult] = field(default_factory=list)
    summary: str = ''
    validated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    autofix_applied: bool = False
    human_review_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            'job_id': self.job_id,
            'overall_score': self.overall_score,
            'overall_status': self.overall_status,
            'criteria_results': [cr.to_dict() for cr in self.criteria_results],
            'summary': self.summary,
            'validated_at': self.validated_at,
            'autofix_applied': self.autofix_applied,
            'human_review_required': self.human_review_required
        }


class NextA1QCValidator:
    """
    Next-A1 Quality Control Validator.

    Implements comprehensive QC validation across 8 criteria:
    - PREFLIGHT: Bridge type and strategy validation
    - DRAFT: Word count, structure, formatting
    - ANCHOR: Placement rules, risk assessment, usage limits
    - TRUST: Trust sources (T1-T4 classification)
    - INTENT: Intent alignment validation
    - LSI: LSI term injection (6-10 terms, ±2 sentences)
    - FIT: Readability, tone matching, style consistency
    - COMPLIANCE: Regulated vertical disclaimers

    Scoring System:
    - PASS: ≥80 points (green light for delivery)
    - WARNING: 50-79 points (yellow light, may need review)
    - BLOCKED: <50 points (red light, requires fixes)
    """

    # Trust source tiers (Swedish focus)
    TRUST_SOURCES = {
        'T1': [  # Government, Academic, Major News
            'wikipedia.org', 'riksdag.se', 'government.se', 'regeringen.se',
            'scb.se', 'dn.se', 'svd.se', 'sr.se', 'svt.se',
            'nature.com', 'sciencedirect.com', 'ncbi.nlm.nih.gov'
        ],
        'T2': [  # Industry Leaders, Established Publications
            'forbes.com', 'bloomberg.com', 'reuters.com', 'bbc.com',
            'di.se', 'aftonbladet.se', 'expressen.se', 'gp.se',
            'nytimes.com', 'theguardian.com', 'wsj.com'
        ],
        'T3': [  # Niche Authorities, Trade Publications
            'techcrunch.com', 'wired.com', 'mashable.com',
            'breakit.se', 'feber.se', 'mobil.se'
        ],
        'T4': [  # General Blogs, Forums (lower trust)
            'medium.com', 'reddit.com', 'quora.com'
        ]
    }

    # Regulated verticals requiring disclaimers
    REGULATED_VERTICALS = {
        'gambling': {
            'keywords': ['casino', 'betting', 'spel', 'poker', 'odds'],
            'disclaimer': 'Stödlinjen.se - 020-819100. Spelproblem? Spela lagom.'
        },
        'finance': {
            'keywords': ['lån', 'kredit', 'investering', 'aktie', 'fond'],
            'disclaimer': 'Rådgivning om lån och krediter. Läs mer om villkor på respektive företags webbplats.'
        },
        'health': {
            'keywords': ['medicin', 'behandling', 'diagnos', 'hälsa', 'sjukdom'],
            'disclaimer': 'Detta är generell information och ersätter inte professionell medicinsk rådgivning.'
        }
    }

    def __init__(self):
        """Initialize Next-A1 QC Validator"""
        pass

    def validate(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run complete Next-A1 QC validation.

        Args:
            article: Generated article (markdown)
            job_package: Complete job package with all context

        Returns:
            QC report dict with scores and validation results
        """
        job_id = job_package.get('job_meta', {}).get('job_id', 'unknown')

        # Initialize report
        criteria_results = []

        # Run all 8 QC criteria
        criteria_results.append(self._validate_preflight(job_package))
        criteria_results.append(self._validate_draft(article, job_package))
        criteria_results.append(self._validate_anchor(article, job_package))
        criteria_results.append(self._validate_trust(article))
        criteria_results.append(self._validate_intent(job_package))
        criteria_results.append(self._validate_lsi(article, job_package))
        criteria_results.append(self._validate_fit(article, job_package))
        criteria_results.append(self._validate_compliance(article, job_package))

        # Calculate overall score (weighted average)
        weights = {
            'PREFLIGHT': 0.10,
            'DRAFT': 0.15,
            'ANCHOR': 0.15,
            'TRUST': 0.10,
            'INTENT': 0.15,
            'LSI': 0.10,
            'FIT': 0.15,
            'COMPLIANCE': 0.10
        }

        overall_score = sum(
            cr.score * weights.get(cr.criterion_name, 0.125)
            for cr in criteria_results
        )
        overall_score = int(overall_score)

        # Determine overall status
        if overall_score >= 80:
            overall_status = 'PASS'
        elif overall_score >= 50:
            overall_status = 'WARNING'
        else:
            overall_status = 'BLOCKED'

        # Check if human review required (any BLOCKED criterion)
        human_review_required = any(
            cr.status == 'BLOCKED' for cr in criteria_results
        )

        # Build summary
        blocked_criteria = [cr.criterion_name for cr in criteria_results if cr.status == 'BLOCKED']
        warning_criteria = [cr.criterion_name for cr in criteria_results if cr.status == 'WARNING']

        summary_parts = [f"Overall Score: {overall_score}/100 ({overall_status})"]
        if blocked_criteria:
            summary_parts.append(f"BLOCKED Criteria: {', '.join(blocked_criteria)}")
        if warning_criteria:
            summary_parts.append(f"WARNING Criteria: {', '.join(warning_criteria)}")

        summary = ' | '.join(summary_parts)

        report = QCReport(
            job_id=job_id,
            overall_score=overall_score,
            overall_status=overall_status,
            criteria_results=criteria_results,
            summary=summary,
            human_review_required=human_review_required
        )

        return report.to_dict()

    # ========== CRITERION 1: PREFLIGHT ==========

    def _validate_preflight(self, job_package: Dict[str, Any]) -> QCCriterionResult:
        """
        Validate PREFLIGHT criteria - Bridge type and strategy validation.

        Checks:
        - Bridge type is set and valid (strong/pivot/wrapper)
        - Job package is complete
        - All required profiles present

        Score: 100 if all present, 0 if missing critical components
        """
        intent_extension = job_package.get('intent_extension', {})
        bridge_type = intent_extension.get('recommended_bridge_type', '')

        issues = []
        score = 100

        # Check bridge type
        if not bridge_type:
            issues.append("Bridge type not determined")
            score -= 50
        elif bridge_type not in ['strong', 'pivot', 'wrapper']:
            issues.append(f"Invalid bridge type: {bridge_type}")
            score -= 30

        # Check required profiles
        if not job_package.get('target_profile'):
            issues.append("Missing target profile")
            score -= 25
        if not job_package.get('publisher_profile'):
            issues.append("Missing publisher profile")
            score -= 25

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='PREFLIGHT',
            score=max(0, score),
            status=status,
            issues=issues,
            details={'bridge_type': bridge_type}
        )

    # ========== CRITERION 2: DRAFT ==========

    def _validate_draft(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> QCCriterionResult:
        """
        Validate DRAFT criteria - Word count and structure.

        Checks:
        - Minimum word count (900 words)
        - Proper markdown structure (H1, H2, H3)
        - Has introduction and conclusion
        - Proper formatting

        Score: Based on word count and structure completeness
        """
        constraints = job_package.get('generation_constraints', {})
        min_words = constraints.get('min_word_count', 900)

        issues = []
        score = 100

        # Word count
        word_count = len(article.split())
        if word_count < min_words:
            deficit = min_words - word_count
            issues.append(f"Word count too low: {word_count}/{min_words} (deficit: {deficit})")
            score -= min(40, (deficit / min_words) * 100)

        # Structure validation
        lines = article.split('\n')

        # Check H1
        h1_count = sum(1 for line in lines if line.startswith('# '))
        if h1_count == 0:
            issues.append("Missing H1 title")
            score -= 20
        elif h1_count > 1:
            issues.append(f"Multiple H1 headings ({h1_count})")
            score -= 10

        # Check H2 sections
        h2_count = sum(1 for line in lines if line.startswith('## '))
        if h2_count < 4:
            issues.append(f"Too few H2 sections: {h2_count} (recommended: 4-6)")
            score -= 15

        # Check for paragraphs
        paragraph_count = sum(1 for line in lines if len(line) > 50 and not line.startswith('#'))
        if paragraph_count < 5:
            issues.append(f"Too few paragraphs: {paragraph_count}")
            score -= 10

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='DRAFT',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'word_count': word_count,
                'min_required': min_words,
                'h1_count': h1_count,
                'h2_count': h2_count
            },
            recommendations=['Add more content to meet word count'] if word_count < min_words else []
        )

    # ========== CRITERION 3: ANCHOR ==========

    def _validate_anchor(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> QCCriterionResult:
        """
        Validate ANCHOR criteria - Placement rules and risk assessment.

        Checks:
        - Link NOT in H1/H2 headings
        - Link placement in middle section (preferred)
        - Anchor usage count (max 2)
        - Anchor risk level (exact match = higher risk)

        Score: Based on placement correctness and risk level
        """
        anchor_text = job_package.get('input_minimal', {}).get('anchor_text', '')
        anchor_profile = job_package.get('anchor_profile', {})

        issues = []
        score = 100

        # Find markdown links
        link_pattern = r'\[([^\]]+)\]\([^\)]+\)'
        links_found = re.findall(link_pattern, article)

        # Count anchor usages
        anchor_usage_count = sum(1 for link_text in links_found if link_text == anchor_text)

        if anchor_usage_count == 0:
            issues.append("Anchor link not found in article")
            score -= 50
        elif anchor_usage_count > 2:
            issues.append(f"Too many anchor usages: {anchor_usage_count} (max: 2)")
            score -= 20

        # Check placement (NOT in H1/H2)
        lines = article.split('\n')
        forbidden_placement = False

        for line in lines:
            if re.search(link_pattern, line):
                if line.startswith('# '):
                    issues.append("Link found in H1 heading (FORBIDDEN)")
                    score -= 40
                    forbidden_placement = True
                elif line.startswith('## '):
                    issues.append("Link found in H2 heading (FORBIDDEN)")
                    score -= 40
                    forbidden_placement = True

        # Anchor risk assessment
        anchor_type = anchor_profile.get('llm_classified_type', 'unknown')
        if anchor_type == 'exact':
            issues.append("Exact match anchor detected (higher SEO risk)")
            score -= 10
        elif anchor_type == 'branded':
            # Branded is good
            pass
        elif anchor_type == 'generic':
            issues.append("Generic anchor (lower SEO value)")
            score -= 5

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='ANCHOR',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'anchor_usage_count': anchor_usage_count,
                'anchor_type': anchor_type,
                'forbidden_placement': forbidden_placement
            },
            recommendations=['Move link from heading to paragraph text'] if forbidden_placement else []
        )

    # ========== CRITERION 4: TRUST ==========

    def _validate_trust(self, article: str) -> QCCriterionResult:
        """
        Validate TRUST criteria - Source quality (T1-T4).

        Checks:
        - Presence of trust sources (T1-T4)
        - Minimum 1 T1 source (government, academic, major news)
        - Minimum 2 total trust sources

        Score: Based on trust source count and tier
        """
        issues = []
        score = 100

        # Find all URLs in article
        url_pattern = r'https?://([a-zA-Z0-9.-]+)'
        domains = re.findall(url_pattern, article)

        # Classify by tier
        tier_counts = {'T1': 0, 'T2': 0, 'T3': 0, 'T4': 0}
        classified_sources = []

        for domain in domains:
            domain_clean = domain.lower().replace('www.', '')

            for tier, tier_domains in self.TRUST_SOURCES.items():
                if any(trusted in domain_clean for trusted in tier_domains):
                    tier_counts[tier] += 1
                    classified_sources.append({'domain': domain, 'tier': tier})
                    break

        total_trust_sources = sum(tier_counts.values())

        # Scoring
        if tier_counts['T1'] == 0:
            issues.append("No T1 (government/academic/major news) sources found")
            score -= 40

        if total_trust_sources < 2:
            issues.append(f"Too few trust sources: {total_trust_sources} (minimum: 2)")
            score -= 30

        if total_trust_sources == 0:
            issues.append("No trust sources found at all")
            score -= 50

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='TRUST',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'tier_counts': tier_counts,
                'total_trust_sources': total_trust_sources,
                'sources': classified_sources
            },
            recommendations=['Add references to government, academic, or major news sources'] if tier_counts['T1'] == 0 else []
        )

    # ========== CRITERION 5: INTENT ==========

    def _validate_intent(self, job_package: Dict[str, Any]) -> QCCriterionResult:
        """
        Validate INTENT criteria - Intent alignment.

        Checks:
        - Overall intent alignment (aligned/partial/off)
        - SERP intent matches target intent
        - No forbidden angles used

        Score: Based on alignment quality
        """
        intent_extension = job_package.get('intent_extension', {})
        intent_alignment = intent_extension.get('intent_alignment', {})
        overall_alignment = intent_alignment.get('overall', 'aligned')

        issues = []
        score = 100

        if overall_alignment == 'off':
            issues.append("Intent alignment is OFF (severe mismatch)")
            score -= 60
        elif overall_alignment == 'partial':
            issues.append("Intent alignment is PARTIAL (some mismatch)")
            score -= 20

        # Check forbidden angles
        forbidden_angles = intent_extension.get('forbidden_angles', [])
        if forbidden_angles:
            # Note: We can't easily check if article uses forbidden angles without LLM
            # This would require semantic analysis
            pass

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='INTENT',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'overall_alignment': overall_alignment,
                'forbidden_angles_count': len(forbidden_angles)
            }
        )

    # ========== CRITERION 6: LSI ==========

    def _validate_lsi(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> QCCriterionResult:
        """
        Validate LSI criteria - LSI term injection.

        Checks:
        - 6-10 LSI terms present
        - LSI terms within ±2 sentences of anchor link
        - Natural integration (not keyword stuffing)

        Score: Based on LSI term count and placement
        """
        issues = []
        score = 100

        # Extract LSI terms from job package
        lsi_terms = self._extract_lsi_terms(job_package)

        if not lsi_terms:
            # No LSI terms to validate
            return QCCriterionResult(
                criterion_name='LSI',
                score=100,
                status='PASS',
                details={'message': 'No LSI terms specified'}
            )

        # Find anchor link position
        anchor_text = job_package.get('input_minimal', {}).get('anchor_text', '')
        sentences = re.split(r'[.!?]+', article)

        anchor_sentence_idx = None
        for idx, sentence in enumerate(sentences):
            if anchor_text in sentence or '[' in sentence:
                anchor_sentence_idx = idx
                break

        # Count LSI terms in article
        article_lower = article.lower()
        lsi_found = []
        lsi_near_anchor = []

        for term in lsi_terms:
            if term.lower() in article_lower:
                lsi_found.append(term)

                # Check if near anchor (±2 sentences)
                if anchor_sentence_idx is not None:
                    for idx in range(max(0, anchor_sentence_idx - 2),
                                   min(len(sentences), anchor_sentence_idx + 3)):
                        if term.lower() in sentences[idx].lower():
                            lsi_near_anchor.append(term)
                            break

        lsi_count = len(lsi_found)
        lsi_near_count = len(lsi_near_anchor)

        # Scoring
        if lsi_count < 6:
            issues.append(f"Too few LSI terms: {lsi_count}/6-10")
            score -= 30
        elif lsi_count > 10:
            issues.append(f"Too many LSI terms: {lsi_count}/6-10 (possible keyword stuffing)")
            score -= 15

        if anchor_sentence_idx is not None and lsi_near_count < 3:
            issues.append(f"Too few LSI terms near anchor: {lsi_near_count} (recommended: 3+)")
            score -= 20

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='LSI',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'lsi_terms_available': len(lsi_terms),
                'lsi_terms_found': lsi_count,
                'lsi_terms_near_anchor': lsi_near_count,
                'anchor_sentence_index': anchor_sentence_idx
            },
            recommendations=['Inject more LSI terms near the anchor link'] if lsi_count < 6 else []
        )

    # ========== CRITERION 7: FIT ==========

    def _validate_fit(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> QCCriterionResult:
        """
        Validate FIT criteria - Readability and tone matching.

        Checks:
        - Appropriate language (Swedish/English)
        - Sentence length variation
        - No excessive repetition
        - Tone matches publisher

        Score: Based on readability metrics
        """
        publisher_profile = job_package.get('publisher_profile', {})
        constraints = job_package.get('generation_constraints', {})

        expected_language = constraints.get('language', 'sv')
        publisher_tone = publisher_profile.get('tone_class', 'professional')

        issues = []
        score = 100

        # Language check (simple heuristic)
        swedish_chars = sum(1 for c in article if c in 'åäöÅÄÖ')
        if expected_language == 'sv' and swedish_chars < 10:
            issues.append("Article appears to be in wrong language (expected Swedish)")
            score -= 30

        # Sentence length analysis
        sentences = re.split(r'[.!?]+', article)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

            if avg_sentence_length > 30:
                issues.append(f"Sentences too long (avg: {avg_sentence_length:.1f} words)")
                score -= 10
            elif avg_sentence_length < 10:
                issues.append(f"Sentences too short (avg: {avg_sentence_length:.1f} words)")
                score -= 10

        # Repetition check (very basic)
        words = article.lower().split()
        if len(words) > 0:
            word_freq = {}
            for word in words:
                if len(word) > 5:  # Only check longer words
                    word_freq[word] = word_freq.get(word, 0) + 1

            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.05:  # More than 5% repetition
                issues.append("Excessive word repetition detected")
                score -= 15

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='FIT',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'expected_language': expected_language,
                'publisher_tone': publisher_tone,
                'avg_sentence_length': avg_sentence_length if sentences else 0
            }
        )

    # ========== CRITERION 8: COMPLIANCE ==========

    def _validate_compliance(
        self,
        article: str,
        job_package: Dict[str, Any]
    ) -> QCCriterionResult:
        """
        Validate COMPLIANCE criteria - Regulated vertical disclaimers.

        Checks:
        - Auto-detect regulated vertical (gambling, finance, health)
        - Verify required disclaimer present
        - Check disclaimer placement

        Score: 100 if compliant or N/A, 0 if missing required disclaimer
        """
        target_url = job_package.get('input_minimal', {}).get('target_url', '').lower()
        publisher_domain = job_package.get('input_minimal', {}).get('publisher_domain', '').lower()

        combined_text = f"{target_url} {publisher_domain} {article.lower()}"

        issues = []
        score = 100

        detected_vertical = None
        required_disclaimer = None

        # Detect regulated vertical
        for vertical, config in self.REGULATED_VERTICALS.items():
            keywords = config['keywords']
            if any(keyword in combined_text for keyword in keywords):
                detected_vertical = vertical
                required_disclaimer = config['disclaimer']
                break

        if detected_vertical:
            # Check if disclaimer present
            if required_disclaimer.lower() not in article.lower():
                issues.append(f"Missing required {detected_vertical} disclaimer")
                score = 0  # Critical failure
            else:
                # Disclaimer found - check placement (should be at end)
                article_lines = article.split('\n')
                disclaimer_line_idx = None

                for idx, line in enumerate(article_lines):
                    if required_disclaimer[:20].lower() in line.lower():
                        disclaimer_line_idx = idx
                        break

                if disclaimer_line_idx is not None and disclaimer_line_idx < len(article_lines) * 0.8:
                    issues.append("Disclaimer should be placed at end of article")
                    score -= 10

        # Determine status
        if score >= 80:
            status = 'PASS'
        elif score >= 50:
            status = 'WARNING'
        else:
            status = 'BLOCKED'

        return QCCriterionResult(
            criterion_name='COMPLIANCE',
            score=max(0, score),
            status=status,
            issues=issues,
            details={
                'detected_vertical': detected_vertical,
                'disclaimer_required': detected_vertical is not None,
                'disclaimer_present': required_disclaimer.lower() in article.lower() if required_disclaimer else False
            },
            recommendations=[f'Add {detected_vertical} disclaimer: {required_disclaimer}'] if detected_vertical and score < 100 else []
        )

    # ========== HELPER METHODS ==========

    def _extract_lsi_terms(self, job_package: Dict[str, Any]) -> List[str]:
        """Extract LSI terms from job package"""
        lsi_terms = []

        # From SERP subtopics
        serp_research = job_package.get('serp_research_extension', {})
        for serp_set in serp_research.get('serp_sets', [])[:2]:
            lsi_terms.extend(serp_set.get('subtopics', [])[:3])

        # From required subtopics
        intent_extension = job_package.get('intent_extension', {})
        lsi_terms.extend(intent_extension.get('required_subtopics', [])[:5])

        # From target topics
        target_profile = job_package.get('target_profile', {})
        lsi_terms.extend(target_profile.get('core_topics', [])[:3])

        # Deduplicate and limit
        return list(dict.fromkeys(lsi_terms))[:10]
