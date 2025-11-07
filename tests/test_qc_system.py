#!/usr/bin/env python3
"""
QC System Tests for BACOWR
Per NEXT-A1-ENGINE-ADDENDUM.md § 3

Tests:
- QC validation logic
- AutoFixOnce functionality
- Blocking conditions
- Human signoff triggers
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.qc import QualityController, QCStatus, IssueSeverity, IssueCategory


def test_qc_lsi_check():
    """Test LSI requirements check"""
    print("Test: LSI Check")

    qc = QualityController()

    # Mock article with low LSI
    article = "This is a short article with minimal content."
    job_package = {
        'job_meta': {'job_id': 'test_001'},
        'input_minimal': {
            'publisher_domain': 'test.com',
            'target_url': 'https://example.com',
            'anchor_text': 'test'
        },
        'intent_extension': {
            'intent_alignment': {'overall': 'aligned'}
        }
    }

    lsi_result = qc.check_lsi_requirements(article, job_package)

    print(f"  LSI Count: {lsi_result['lsi_count']}")
    print(f"  Pass: {lsi_result['pass']}")

    assert 'lsi_count' in lsi_result
    assert 'pass' in lsi_result
    print("  ✅ PASS\n")


def test_qc_trust_sources():
    """Test trust source validation"""
    print("Test: Trust Sources Check")

    qc = QualityController()

    # Article with T1 source (must include URLs)
    article_good = """
    This article cites reliable sources.

    According to [Konsumentverket](https://konsumentverket.se/guide), consumers should always compare options.
    [Wikipedia](https://wikipedia.org/article) also provides background information.
    """

    result_good = qc.check_trust_sources(article_good)

    print(f"  T1 Sources: {result_good['tier_1_count']}")
    print(f"  Total Sources: {result_good['total_count']}")
    print(f"  Pass: {result_good['pass']}")

    assert result_good['tier_1_count'] >= 1, f"Expected T1 sources, got {result_good['tier_1_count']}"
    assert result_good['pass'] == True, f"Trust sources check failed: {result_good}"
    print("  ✅ PASS\n")


def test_qc_anchor_risk():
    """Test anchor risk assessment"""
    print("Test: Anchor Risk Check")

    qc = QualityController()

    # Low risk anchor
    job_low = {
        'input_minimal': {'anchor_text': 'read more'},
        'anchor_profile': {'llm_classified_type': 'generic'}
    }

    result_low = qc.check_anchor_risk(job_low)
    print(f"  Low risk anchor: {result_low['risk_level']}")
    assert result_low['risk_level'] == 'low'

    # Medium risk anchor
    job_medium = {
        'input_minimal': {'anchor_text': 'best product reviews'},
        'anchor_profile': {'llm_classified_type': 'partial'}
    }

    result_medium = qc.check_anchor_risk(job_medium)
    print(f"  Medium risk anchor: {result_medium['risk_level']}")
    assert result_medium['risk_level'] == 'medium'

    print("  ✅ PASS\n")


def test_qc_link_placement():
    """Test link placement validation"""
    print("Test: Link Placement Check")

    qc = QualityController()

    # Bad: link in H2
    article_bad = """
# Main Title

## [Bad Link](https://example.com)

Some content here.
"""

    result_bad = qc.check_link_placement(article_bad, {})
    print(f"  Link in H2 detected: {result_bad['in_forbidden_location']}")
    assert result_bad['in_forbidden_location'] == True
    assert 'H2' in result_bad['forbidden_locations_found']

    # Good: link in paragraph
    article_good = """
# Main Title

## Section

This is a paragraph with a [good link](https://example.com) in the middle.
"""

    result_good = qc.check_link_placement(article_good, {})
    print(f"  Link in paragraph: {result_good['in_forbidden_location']}")
    assert result_good['pass'] == True

    print("  ✅ PASS\n")


def test_qc_full_validation():
    """Test complete QC validation"""
    print("Test: Full QC Validation")

    qc = QualityController()

    job_package = {
        'job_meta': {'job_id': 'test_full'},
        'input_minimal': {
            'publisher_domain': 'test.com',
            'target_url': 'https://example.com',
            'anchor_text': 'test anchor'
        },
        'anchor_profile': {
            'llm_classified_type': 'partial',
            'llm_intent_hint': 'commercial_research'
        },
        'intent_extension': {
            'intent_alignment': {
                'overall': 'aligned'
            }
        }
    }

    article = """
# Test Article

## Introduction

This is a test article with [test anchor](https://example.com) included.

According to Konsumentverket.se, this is important information.
"""

    report = qc.validate(job_package, article)

    print(f"  Status: {report.status.value}")
    print(f"  Issues: {len(report.issues)}")
    print(f"  Human Signoff Required: {report.human_signoff_required}")

    assert report is not None
    assert hasattr(report, 'status')
    assert hasattr(report, 'issues')

    print("  ✅ PASS\n")


def test_autofix_once_limit():
    """Test that AutoFix runs max once"""
    print("Test: AutoFixOnce Limit")

    qc = QualityController()

    job_package = {
        'job_meta': {'job_id': 'test_autofix'},
        'input_minimal': {
            'publisher_domain': 'test.com',
            'target_url': 'https://example.com',
            'anchor_text': 'test'
        },
        'anchor_profile': {'llm_classified_type': 'partial'},
        'intent_extension': {'intent_alignment': {'overall': 'aligned'}}
    }

    article = "Short article with [link](url) in bad place."

    report = qc.validate(job_package, article)

    if report.status == QCStatus.BLOCKED:
        # Attempt fix
        fixed_pkg, fixed_article, fix_logs = qc.auto_fix_once(job_package, article, report)

        print(f"  AutoFix logs: {len(fix_logs)}")
        print(f"  Max 1 fix: {len(fix_logs) <= 1}")

        assert len(fix_logs) <= 1  # Max ONE fix

        if fix_logs:
            print(f"  Fix type: {fix_logs[0].fix_type}")

    print("  ✅ PASS\n")


def test_blocking_conditions():
    """Test critical blocking conditions"""
    print("Test: Blocking Conditions")

    qc = QualityController()

    # Intent alignment OFF should block
    job_blocked = {
        'job_meta': {'job_id': 'test_block'},
        'input_minimal': {
            'publisher_domain': 'test.com',
            'target_url': 'https://example.com',
            'anchor_text': 'test'
        },
        'anchor_profile': {'llm_classified_type': 'exact'},
        'intent_extension': {
            'intent_alignment': {
                'overall': 'off'  # CRITICAL - should block
            }
        }
    }

    article = "Test article"

    report = qc.validate(job_blocked, article)

    print(f"  Intent OFF detected: {report.intent_check['overall_alignment'] == 'off'}")
    print(f"  Human Signoff Required: {report.human_signoff_required}")

    assert report.intent_check['overall_alignment'] == 'off'
    # Should have critical issue
    critical_issues = [i for i in report.issues if i.severity == IssueSeverity.CRITICAL]
    assert len(critical_issues) > 0

    print("  ✅ PASS\n")


if __name__ == "__main__":
    print("=" * 70)
    print("BACOWR QC System Tests")
    print("Per NEXT-A1-ENGINE-ADDENDUM.md § 3")
    print("=" * 70)
    print()

    try:
        test_qc_lsi_check()
        test_qc_trust_sources()
        test_qc_anchor_risk()
        test_qc_link_placement()
        test_qc_full_validation()
        test_autofix_once_limit()
        test_blocking_conditions()

        print("=" * 70)
        print("✅ All QC tests passed!")
        print("=" * 70)
        sys.exit(0)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
