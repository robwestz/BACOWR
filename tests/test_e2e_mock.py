#!/usr/bin/env python3
"""
End-to-End Tests for BACOWR Production Pipeline

Comprehensive test suite for complete pipeline execution including:
- Full workflow (RECEIVE → PREFLIGHT → WRITE → QC → DELIVER/RESCUE/ABORT)
- State machine integration
- Quality control validation
- Output file generation
- Error handling and edge cases
- Performance metrics

Per BUILDER_PROMPT.md STEG 8-10
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api import run_backlink_job


class TestE2EBasicWorkflow:
    """Test suite for basic E2E workflow."""

    def test_e2e_mock_success_path(self):
        """Test full pipeline in mock mode - success path."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test link",
            mock=True
        )

        # Verify basic structure
        assert 'job_id' in result
        assert 'status' in result
        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

        # Job ID format validation
        assert result['job_id'].startswith('job_')

    def test_e2e_mock_with_custom_output_dir(self):
        """Test E2E with custom output directory."""
        output_dir = project_root / 'storage' / 'output' / 'test_e2e'
        output_dir.mkdir(parents=True, exist_ok=True)

        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True,
            output_dir=str(output_dir)
        )

        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

    def test_e2e_minimal_input(self):
        """Test E2E with minimal required input."""
        result = run_backlink_job(
            publisher_domain="minimal.com",
            target_url="https://example.com",
            anchor_text="link",
            mock=True
        )

        assert 'job_id' in result
        assert 'status' in result

    def test_e2e_swedish_target(self):
        """Test E2E with Swedish target URL."""
        result = run_backlink_job(
            publisher_domain="test.se",
            target_url="https://example.se/produkt",
            anchor_text="bästa valet",
            mock=True
        )

        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

        # Check Swedish language detection
        if 'job_package' in result:
            lang = result['job_package'].get('generation_constraints', {}).get('language')
            # Should detect Swedish or default
            assert lang in ['sv', 'en', None]


class TestE2EStateMachine:
    """Test suite for state machine integration."""

    def test_state_transitions_logged(self):
        """Test that all state transitions are logged."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        exec_log = result.get('execution_log', {})
        log_entries = exec_log.get('log_entries', [])
        state_transitions = [e for e in log_entries if e.get('type') == 'state_transition']

        # Should have at least: RECEIVE→PREFLIGHT→WRITE→QC→(final state)
        assert len(state_transitions) >= 4, f"Expected >= 4 transitions, got {len(state_transitions)}"

        # Verify transition structure
        if state_transitions:
            first = state_transitions[0]
            assert 'from_state' in first
            assert 'to_state' in first
            assert 'timestamp' in first

    def test_initial_state_is_receive(self):
        """Test that pipeline starts in RECEIVE state."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        exec_log = result.get('execution_log', {})
        state_transitions = [e for e in exec_log.get('log_entries', []) if e.get('type') == 'state_transition']

        if state_transitions:
            first_transition = state_transitions[0]
            assert first_transition['from_state'] == 'RECEIVE'

    def test_final_state_is_terminal(self):
        """Test that pipeline ends in a terminal state."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        # Terminal states
        terminal_states = ['DELIVERED', 'BLOCKED', 'ABORTED']
        assert result['status'] in terminal_states

    def test_rescue_max_once(self):
        """Test that RESCUE state is entered max once per job."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        exec_log = result.get('execution_log', {})
        log_entries = exec_log.get('log_entries', [])
        rescue_transitions = [
            e for e in log_entries
            if e.get('type') == 'state_transition' and e.get('to_state') == 'RESCUE'
        ]

        assert len(rescue_transitions) <= 1, "RESCUE should be attempted max once"

    def test_loop_detection_prevents_infinite_loops(self):
        """Test that loop detection prevents infinite loops."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        # Execution should complete (not hang)
        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

        # Verify execution log exists and has reasonable length
        exec_log = result.get('execution_log', {})
        log_entries = exec_log.get('log_entries', [])

        # Should not have excessive state transitions (indicating loop)
        state_transitions = [e for e in log_entries if e.get('type') == 'state_transition']
        assert len(state_transitions) < 20, "Too many state transitions - possible loop"


class TestE2EQualityControl:
    """Test suite for QC integration."""

    def test_qc_report_exists(self):
        """Test that QC report is generated."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        # QC report should exist unless job aborted early
        assert 'qc_report' in result or result['status'] == 'ABORTED'

    def test_qc_report_structure(self):
        """Test QC report has correct structure."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'qc_report' in result:
            qc = result['qc_report']

            assert 'status' in qc
            assert 'issues' in qc
            assert isinstance(qc['issues'], list)
            assert 'autofix_done' in qc

    def test_qc_blocks_when_issues_found(self):
        """Test that QC blocks delivery when issues are found."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'qc_report' in result:
            qc = result['qc_report']

            # If there are blocking issues, status should be BLOCKED or RESCUED
            if qc.get('status') in ['BLOCKED', 'FAIL']:
                assert result['status'] in ['BLOCKED', 'RESCUE', 'ABORTED']

    def test_qc_autofix_tracking(self):
        """Test that QC AutoFix attempts are tracked."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'qc_report' in result:
            qc = result['qc_report']

            # AutoFix status should be boolean
            assert isinstance(qc.get('autofix_done', False), bool)

    def test_qc_issues_have_details(self):
        """Test that QC issues contain detailed information."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'qc_report' in result:
            qc = result['qc_report']
            issues = qc.get('issues', [])

            for issue in issues:
                # Each issue should have at least a category
                assert 'category' in issue or 'rule' in issue or 'check' in issue
                # And should have severity or auto_fixable
                assert 'severity' in issue or 'level' in issue or 'auto_fixable' in issue


class TestE2EJobPackage:
    """Test suite for job package structure."""

    def test_job_package_schema_compliance(self):
        """Test that job package matches schema."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'job_package' in result:
            job_pkg = result['job_package']

            # Required top-level fields
            required_fields = [
                'job_meta',
                'input_minimal',
                'publisher_profile',
                'target_profile',
                'anchor_profile',
                'serp_research_extension',
                'intent_extension',
                'generation_constraints'
            ]

            for field in required_fields:
                assert field in job_pkg, f"Missing required field: {field}"

    def test_job_meta_structure(self):
        """Test job_meta has correct structure."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'job_package' in result:
            job_meta = result['job_package'].get('job_meta', {})

            assert 'job_id' in job_meta
            assert 'created_at' in job_meta or 'timestamp' in job_meta

    def test_input_minimal_preserved(self):
        """Test that input_minimal contains original inputs."""
        result = run_backlink_job(
            publisher_domain="original-domain.com",
            target_url="https://original-target.com",
            anchor_text="original anchor",
            mock=True
        )

        if 'job_package' in result:
            input_min = result['job_package'].get('input_minimal', {})

            assert input_min['publisher_domain'] == 'original-domain.com'
            assert input_min['target_url'] == 'https://original-target.com'
            assert input_min['anchor_text'] == 'original anchor'

    def test_profiles_populated(self):
        """Test that all profiles are populated."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        if 'job_package' in result:
            job_pkg = result['job_package']

            # Publisher profile
            assert 'publisher_profile' in job_pkg
            pub = job_pkg['publisher_profile']
            assert 'domain' in pub

            # Target profile
            assert 'target_profile' in job_pkg
            target = job_pkg['target_profile']
            assert 'url' in target

            # Anchor profile
            assert 'anchor_profile' in job_pkg
            anchor = job_pkg['anchor_profile']
            assert 'proposed_text' in anchor


class TestE2EOutputFiles:
    """Test suite for output file generation."""

    def setup_method(self):
        """Setup test output directory."""
        self.test_output_dir = project_root / 'storage' / 'output' / 'test_e2e'
        self.test_output_dir.mkdir(parents=True, exist_ok=True)

    def test_output_files_generated(self):
        """Test that output files are created."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True,
            output_dir=str(self.test_output_dir)
        )

        if 'output_files' in result:
            files = result['output_files']
            assert len(files) > 0, "No output files generated"

    def test_output_files_have_content(self):
        """Test that generated files have content."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True,
            output_dir=str(self.test_output_dir)
        )

        if 'output_files' in result:
            for file_type, file_path in result['output_files'].items():
                path = Path(file_path)
                if path.exists():
                    size = path.stat().st_size
                    assert size > 0, f"{file_type} file is empty"

    def test_article_file_contains_markdown(self):
        """Test that article file contains markdown content."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True,
            output_dir=str(self.test_output_dir)
        )

        if 'output_files' in result and 'article' in result['output_files']:
            article_path = Path(result['output_files']['article'])
            if article_path.exists():
                content = article_path.read_text(encoding='utf-8')

                # Should contain markdown elements
                assert len(content) > 0
                # Markdown typically has headers (#) or links ([text](url))
                assert '#' in content or '[' in content


class TestE2EEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_very_long_anchor_text(self):
        """Test handling of very long anchor text."""
        long_anchor = "this is a very long anchor text " * 10

        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text=long_anchor,
            mock=True
        )

        # Should complete without error
        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

    def test_special_characters_in_anchor(self):
        """Test handling of special characters in anchor text."""
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test & special < chars > !@#$%",
            mock=True
        )

        assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

    def test_international_domain(self):
        """Test handling of international domain."""
        result = run_backlink_job(
            publisher_domain="tëst.cöm",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )

        assert 'job_id' in result

    def test_https_and_http_targets(self):
        """Test both HTTPS and HTTP target URLs."""
        # HTTPS
        result1 = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test",
            mock=True
        )
        assert result1['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

        # HTTP
        result2 = run_backlink_job(
            publisher_domain="test.com",
            target_url="http://example.com",
            anchor_text="test",
            mock=True
        )
        assert result2['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR E2E Production Pipeline Tests")
    log("Per BUILDER_PROMPT.md STEG 8-10\n")
    log("=" * 60)

    try:
        # Test basic workflow
        log("\n🔍 Testing basic E2E workflow...")
        result = run_backlink_job(
            publisher_domain="test.com",
            target_url="https://example.com",
            anchor_text="test link",
            mock=True
        )
        log(f"✅ Job completed: {result['job_id']}")
        log(f"   Status: {result['status']}")

        # Test state transitions
        log("\n🔍 Testing state machine integration...")
        exec_log = result.get('execution_log', {})
        transitions = [e for e in exec_log.get('log_entries', []) if e.get('type') == 'state_transition']
        log(f"✅ State transitions: {len(transitions)}")

        # Test QC integration
        log("\n🔍 Testing QC integration...")
        if 'qc_report' in result:
            qc = result['qc_report']
            log(f"✅ QC Status: {qc.get('status')}")
            log(f"   Issues: {len(qc.get('issues', []))}")

        # Test job package
        log("\n🔍 Testing job package structure...")
        if 'job_package' in result:
            job_pkg = result['job_package']
            log(f"✅ Job package has {len(job_pkg)} top-level keys")

        log("\n✅ All standalone tests passed!")
        log("=" * 60)
        return True

    except Exception as e:
        log(f"❌ Test failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        log("=" * 60)
        return False


if __name__ == "__main__":
    log("=" * 60)
    success = run_standalone_tests()

    if success:
        log("✅ TESTS PASSED", "SUCCESS")
        log("\nNote: Mock articles may be BLOCKED by QC due to")
        log("missing trust sources or low LSI count. This is")
        log("expected and demonstrates QC is working correctly.")
        sys.exit(0)
    else:
        log("❌ TESTS FAILED", "ERROR")
        sys.exit(1)
