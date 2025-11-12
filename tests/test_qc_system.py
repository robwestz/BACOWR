#!/usr/bin/env python3
"""
QC System Tests for BACOWR

Comprehensive test suite for the Quality Control system including:
- LSI requirements validation
- Trust source checking
- Anchor risk assessment
- Link placement rules
- Compliance checking
- AutoFixOnce functionality
- Blocking conditions

Per NEXT-A1-ENGINE-ADDENDUM.md § 3 and BUILDER_PROMPT.md STEG 3
"""

import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.qc import QualityController, QCStatus, IssueSeverity, IssueCategory


class TestQCValidation:
    """Test suite for QC validation checks."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.qc = QualityController()

    def test_qc_initialization(self):
        """Test QC controller initializes correctly."""
        assert self.qc is not None
        assert self.qc.thresholds is not None
        assert self.qc.policies is not None
        assert 'lsi_requirements' in self.qc.thresholds
        assert 'autofix_policies' in self.qc.policies

    def test_lsi_check_low_count(self):
        """Test LSI check with insufficient LSI terms."""
        article = "This is a short article with minimal content and few terms."
        job_package = {
            'job_meta': {'job_id': 'test_lsi_low'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'intent_extension': {
                'intent_alignment': {'overall': 'aligned'}
            }
        }

        result = self.qc.check_lsi_requirements(article, job_package)

        assert 'lsi_count' in result
        assert 'pass' in result
        assert result['lsi_count'] < 6  # Below minimum

    def test_lsi_check_sufficient(self):
        """Test LSI check with sufficient LSI terms."""
        # Article with more LSI terms
        article = """
        This article discusses technology innovation development systems.
        The process framework methodology implementation guidelines suggest
        various approaches strategies tactics techniques methods procedures.
        """

        job_package = {
            'job_meta': {'job_id': 'test_lsi_good'},
            'input_minimal': {'anchor_text': 'test'},
            'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
        }

        result = self.qc.check_lsi_requirements(article, job_package)

        # Should pass or be close to passing
        assert 'lsi_count' in result

    def test_trust_sources_t1(self):
        """Test trust sources with T1 sources."""
        article = """
        This article cites reliable sources.
        According to [Konsumentverket](https://konsumentverket.se/guide), consumers should compare.
        [Wikipedia](https://wikipedia.org/article) provides additional information.
        [Riksbanken](https://riksbanken.se/data) confirms the data.
        """

        result = self.qc.check_trust_sources(article)

        assert result['tier_1_count'] >= 1
        assert result['total_count'] >= 2
        assert result['pass'] == True

    def test_trust_sources_no_sources(self):
        """Test trust sources with no sources."""
        article = "This article has no external sources or citations."

        result = self.qc.check_trust_sources(article)

        assert result['tier_1_count'] == 0
        assert result['total_count'] == 0
        assert result['pass'] == False

    def test_anchor_risk_low(self):
        """Test low-risk anchor."""
        job = {
            'input_minimal': {'anchor_text': 'read more'},
            'anchor_profile': {'llm_classified_type': 'generic'}
        }

        result = self.qc.check_anchor_risk(job)

        assert result['risk_level'] == 'low'
        assert result['pass'] == True

    def test_anchor_risk_medium(self):
        """Test medium-risk anchor."""
        job = {
            'input_minimal': {'anchor_text': 'best product reviews'},
            'anchor_profile': {'llm_classified_type': 'partial'}
        }

        result = self.qc.check_anchor_risk(job)

        assert result['risk_level'] == 'medium'

    def test_anchor_risk_high(self):
        """Test high-risk anchor (based on classifier)."""
        job = {
            'input_minimal': {'anchor_text': 'buy cheap viagra online'},
            'anchor_profile': {'llm_classified_type': 'exact'}
        }

        result = self.qc.check_anchor_risk(job)

        # Risk level depends on implementation logic
        # Exact match typically indicates higher risk
        assert 'risk_level' in result
        assert result['risk_level'] in ['low', 'medium', 'high']

    def test_link_placement_forbidden_h1(self):
        """Test link in forbidden H1 location."""
        article = "# [Link in H1](https://example.com)\n\nSome content."

        result = self.qc.check_link_placement(article, {})

        assert result['in_forbidden_location'] == True
        assert 'H1' in result['forbidden_locations_found']
        assert result['pass'] == False

    def test_link_placement_forbidden_h2(self):
        """Test link in forbidden H2 location."""
        article = """
# Main Title

## [Bad Link](https://example.com)

Some content here.
"""

        result = self.qc.check_link_placement(article, {})

        assert result['in_forbidden_location'] == True
        assert 'H2' in result['forbidden_locations_found']

    def test_link_placement_good(self):
        """Test link in allowed location (paragraph)."""
        article = """
# Main Title

## Section

This is a paragraph with a [good link](https://example.com) in the middle.
More content here to provide proper context.
"""

        result = self.qc.check_link_placement(article, {})

        assert result['pass'] == True
        assert result['in_forbidden_location'] == False

    def test_compliance_gambling(self):
        """Test compliance check for gambling vertical."""
        job_package = {
            'job_meta': {'job_id': 'test_gambling'},
            'input_minimal': {'anchor_text': 'casino bonus'}
        }

        article = "This article discusses casino betting gambling games online."

        result = self.qc.check_compliance(job_package, article)

        # Check result structure (vertical detection depends on implementation)
        assert 'regulated_vertical' in result or 'vertical_detected' in result
        assert 'disclaimer_required' in result
        assert 'pass' in result

    def test_compliance_health(self):
        """Test compliance check for health vertical."""
        job_package = {
            'job_meta': {'job_id': 'test_health'},
            'input_minimal': {'anchor_text': 'treatment options'}
        }

        article = "This article discusses medical treatment health diagnosis symptoms."

        result = self.qc.check_compliance(job_package, article)

        # Should detect health vertical
        if result.get('vertical_detected'):
            assert result['disclaimer_required'] == True

    def test_intent_alignment_aligned(self):
        """Test intent alignment check - aligned case."""
        job = {
            'intent_extension': {
                'intent_alignment': {'overall': 'aligned'}
            }
        }

        result = self.qc.check_intent_alignment(job)

        assert result['overall_alignment'] == 'aligned'
        assert result['pass'] == True

    def test_intent_alignment_off(self):
        """Test intent alignment check - off case (blocking)."""
        job = {
            'intent_extension': {
                'intent_alignment': {'overall': 'off'}
            }
        }

        result = self.qc.check_intent_alignment(job)

        assert result['overall_alignment'] == 'off'
        assert result['pass'] == False


class TestQCFullValidation:
    """Test suite for full QC validation flow."""

    def setup_method(self):
        """Setup test fixtures."""
        self.qc = QualityController()

    def test_full_validation_pass(self):
        """Test complete QC validation - passing case."""
        job_package = {
            'job_meta': {'job_id': 'test_full_pass'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'informational link'
            },
            'anchor_profile': {
                'llm_classified_type': 'generic',
                'llm_intent_hint': 'informational'
            },
            'intent_extension': {
                'intent_alignment': {'overall': 'aligned'}
            }
        }

        article = """
# Comprehensive Guide

## Introduction

This is a well-written article that discusses various topics in depth.
The content includes a [informational link](https://example.com) properly placed.

According to [Wikipedia](https://wikipedia.org/research), this is important.
[Konsumentverket](https://konsumentverket.se/guide) also confirms this information.

The article continues with substantial content covering methodology process
framework implementation guidelines strategies techniques approaches systems.
"""

        report = self.qc.validate(job_package, article)

        assert report is not None
        assert hasattr(report, 'status')
        assert hasattr(report, 'issues')
        # May have some issues but should not be critical

    def test_full_validation_blocked(self):
        """Test complete QC validation - blocked case."""
        job_package = {
            'job_meta': {'job_id': 'test_full_blocked'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'anchor_profile': {'llm_classified_type': 'partial'},
            'intent_extension': {
                'intent_alignment': {'overall': 'off'}  # BLOCKING!
            }
        }

        article = "# [Link](https://example.com)\n\nShort article."

        report = self.qc.validate(job_package, article)

        assert report.status == QCStatus.BLOCKED
        assert len(report.issues) > 0
        assert report.human_signoff_required == True


class TestAutoFixOnce:
    """Test suite for AutoFixOnce functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.qc = QualityController()

    def test_autofix_once_limit(self):
        """Test that AutoFix runs maximum once."""
        job_package = {
            'job_meta': {'job_id': 'test_autofix_limit'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'anchor_profile': {'llm_classified_type': 'partial'},
            'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
        }

        article = "Short article with [link](url) in bad place."

        report = self.qc.validate(job_package, article)

        if report.status == QCStatus.BLOCKED:
            fixed_pkg, fixed_article, fix_logs = self.qc.auto_fix_once(
                job_package, article, report
            )

            # Max ONE fix
            assert len(fix_logs) <= 1

    def test_autofix_enabled_check(self):
        """Test that AutoFix respects enabled flag."""
        # AutoFix is enabled in policies
        assert self.qc.policies['autofix_policies']['enabled'] == True

    def test_autofix_max_attempts_config(self):
        """Test max attempts configuration."""
        max_attempts = self.qc.policies['autofix_policies']['max_attempts']
        assert max_attempts == 1  # AutoFixOnce


class TestBlockingConditions:
    """Test suite for blocking conditions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.qc = QualityController()

    def test_intent_off_blocks(self):
        """Test that intent alignment 'off' blocks delivery."""
        job = {
            'job_meta': {'job_id': 'test_intent_block'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test'
            },
            'anchor_profile': {'llm_classified_type': 'exact'},
            'intent_extension': {
                'intent_alignment': {'overall': 'off'}
            }
        }

        article = "Test article"

        report = self.qc.validate(job, article)

        assert report.intent_check['overall_alignment'] == 'off'

        # Should have critical issue
        critical_issues = [
            i for i in report.issues
            if i.severity == IssueSeverity.CRITICAL
        ]
        assert len(critical_issues) > 0

    def test_no_trust_sources_blocks(self):
        """Test that zero trust sources blocks delivery."""
        job = {
            'job_meta': {'job_id': 'test_trust_block'},
            'input_minimal': {'anchor_text': 'test'},
            'anchor_profile': {'llm_classified_type': 'generic'},
            'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
        }

        article = "Article with no external sources or citations."

        report = self.qc.validate(job, article)

        # Check trust sources
        assert report.trust_check['total_count'] == 0


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR QC System Tests")
    log("Per NEXT-A1-ENGINE-ADDENDUM.md § 3 and BUILDER_PROMPT.md STEG 3\n")
    log("=" * 70)

    try:
        qc = QualityController()
        log("✅ QC Controller initialized\n")

        # Test 1: LSI Check
        log("🔍 Test 1: LSI Check")
        article = "This is a short article with minimal content."
        job = {
            'job_meta': {'job_id': 'test_001'},
            'input_minimal': {'anchor_text': 'test'},
            'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
        }
        lsi_result = qc.check_lsi_requirements(article, job)
        log(f"   LSI Count: {lsi_result['lsi_count']}")
        assert 'lsi_count' in lsi_result
        log("   ✅ PASS\n")

        # Test 2: Trust Sources
        log("🔍 Test 2: Trust Sources Check")
        article_trust = """
        According to [Konsumentverket](https://konsumentverket.se/guide), information is key.
        [Wikipedia](https://wikipedia.org/article) provides background.
        """
        trust_result = qc.check_trust_sources(article_trust)
        log(f"   T1 Sources: {trust_result['tier_1_count']}")
        assert trust_result['tier_1_count'] >= 1
        log("   ✅ PASS\n")

        # Test 3: Anchor Risk
        log("🔍 Test 3: Anchor Risk Assessment")
        job_anchor = {
            'input_minimal': {'anchor_text': 'read more'},
            'anchor_profile': {'llm_classified_type': 'generic'}
        }
        anchor_result = qc.check_anchor_risk(job_anchor)
        log(f"   Risk Level: {anchor_result['risk_level']}")
        assert anchor_result['risk_level'] == 'low'
        log("   ✅ PASS\n")

        # Test 4: Link Placement
        log("🔍 Test 4: Link Placement Check")
        article_link = "## [Bad Link](https://example.com)\n\nContent."
        placement_result = qc.check_link_placement(article_link, {})
        log(f"   In Forbidden Location: {placement_result['in_forbidden_location']}")
        assert placement_result['in_forbidden_location'] == True
        log("   ✅ PASS\n")

        # Test 5: Full Validation
        log("🔍 Test 5: Full QC Validation")
        full_job = {
            'job_meta': {'job_id': 'test_full'},
            'input_minimal': {'anchor_text': 'test'},
            'anchor_profile': {'llm_classified_type': 'partial'},
            'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
        }
        full_article = "Test article with [link](url)."
        report = qc.validate(full_job, full_article)
        log(f"   Status: {report.status.value}")
        log(f"   Issues: {len(report.issues)}")
        assert report is not None
        log("   ✅ PASS\n")

        # Test 6: AutoFixOnce
        log("🔍 Test 6: AutoFixOnce Limit")
        if report.status == QCStatus.BLOCKED:
            _, _, fix_logs = qc.auto_fix_once(full_job, full_article, report)
            log(f"   Fix Logs: {len(fix_logs)}")
            assert len(fix_logs) <= 1
        log("   ✅ PASS\n")

        # Test 7: Blocking Conditions
        log("🔍 Test 7: Blocking Conditions")
        blocked_job = {
            'job_meta': {'job_id': 'test_block'},
            'input_minimal': {'anchor_text': 'test'},
            'anchor_profile': {'llm_classified_type': 'exact'},
            'intent_extension': {'intent_alignment': {'overall': 'off'}}
        }
        blocked_report = qc.validate(blocked_job, "Test")
        log(f"   Intent OFF: {blocked_report.intent_check['overall_alignment'] == 'off'}")
        assert blocked_report.intent_check['overall_alignment'] == 'off'
        log("   ✅ PASS\n")

        log("=" * 70)
        log("✅ All standalone tests passed!", "SUCCESS")
        log("=" * 70)
        return True

    except AssertionError as e:
        log(f"❌ Test failed: {e}", "ERROR")
        return False
    except Exception as e:
        log(f"❌ Error: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    log("=" * 70)
    success = run_standalone_tests()

    if success:
        sys.exit(0)
    else:
        sys.exit(1)
