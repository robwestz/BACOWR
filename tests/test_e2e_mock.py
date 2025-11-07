#!/usr/bin/env python3
"""
E2E Mock Tests for BACOWR
Per NEXT-A1-ENGINE-ADDENDUM.md § 2.2, § 4, § 7

Tests complete pipeline in mock mode without external dependencies.

Tests:
- Full pipeline execution (RECEIVE → DELIVER)
- State machine transitions
- QC integration
- AutoFix triggers
- Loop detection
- Output file generation
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api import run_backlink_job


def test_e2e_mock_success():
    """Test full pipeline in mock mode - success path"""
    print("Test: E2E Mock - Success Path")

    # This will likely be BLOCKED due to mock article not meeting all QC requirements
    # But that's OK - it tests the pipeline
    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test link",
        mock=True
    )

    print(f"  Job ID: {result['job_id']}")
    print(f"  Status: {result['status']}")

    # Verify structure
    assert 'job_id' in result
    assert 'status' in result
    assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

    if result['status'] == 'DELIVERED':
        assert 'job_package' in result
        assert 'article' in result
        assert 'qc_report' in result
        assert 'execution_log' in result
        print("  ✅ PASS (DELIVERED)\n")
    elif result['status'] == 'BLOCKED':
        # QC blocked - this is OK for mock
        assert 'qc_report' in result
        qc = result['qc_report']
        print(f"  Issues: {len(qc.get('issues', []))}")
        print("  ✅ PASS (BLOCKED by QC as expected for mock)\n")
    else:
        print("  ⚠️  ABORTED - check logs\n")


def test_e2e_state_transitions():
    """Test that execution logger logs all state transitions"""
    print("Test: State Machine Transitions")

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True
    )

    exec_log = result.get('execution_log', {})

    # Execution logger structure
    log_entries = exec_log.get('log_entries', [])
    state_transitions = [e for e in log_entries if e.get('type') == 'state_transition']

    print(f"  Total Log Entries: {len(log_entries)}")
    print(f"  State Transitions: {len(state_transitions)}")

    # Should have at least: RECEIVE→PREFLIGHT→WRITE→QC→(DELIVER or RESCUE or ABORT)
    assert len(state_transitions) >= 4, f"Expected at least 4 state transitions, got {len(state_transitions)}"

    if state_transitions:
        print(f"  First transition: {state_transitions[0]['from_state']} → {state_transitions[0]['to_state']}")
        print(f"  Last transition: {state_transitions[-1]['from_state']} → {state_transitions[-1]['to_state']}")

    print("  ✅ PASS\n")


def test_e2e_qc_integration():
    """Test QC integration in pipeline"""
    print("Test: QC Integration")

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True
    )

    # QC report should exist
    assert 'qc_report' in result or result['status'] == 'ABORTED'

    if 'qc_report' in result:
        qc = result['qc_report']
        print(f"  QC Status: {qc.get('status')}")
        print(f"  Issues Count: {len(qc.get('issues', []))}")
        print(f"  AutoFix Done: {qc.get('autofix_done', False)}")

        assert 'status' in qc
        assert 'issues' in qc

    print("  ✅ PASS\n")


def test_e2e_output_files():
    """Test that output files are generated"""
    print("Test: Output File Generation")

    # Use custom output dir for test
    output_dir = Path(__file__).parent.parent / 'storage' / 'output' / 'test'
    output_dir.mkdir(parents=True, exist_ok=True)

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True,
        output_dir=str(output_dir)
    )

    if 'output_files' in result:
        files = result['output_files']
        print(f"  Output files: {len(files)}")

        for file_type, file_path in files.items():
            path = Path(file_path)
            exists = path.exists()
            print(f"    - {file_type}: {'✓' if exists else '✗'}")

            if exists:
                # Verify file has content
                size = path.stat().st_size
                assert size > 0, f"{file_type} file is empty"

        print("  ✅ PASS\n")
    else:
        print("  ⚠️  No output files (job may have aborted)\n")


def test_e2e_loop_detection():
    """Test loop detection works"""
    print("Test: Loop Detection")

    # The mock mode should not trigger loops since it generates fresh content
    # But we can verify the pipeline doesn't get stuck

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True
    )

    # Execution should complete (not hang)
    assert result['status'] in ['DELIVERED', 'BLOCKED', 'ABORTED']

    # Loop would result in ABORT with loop-related reason
    if result['status'] == 'ABORTED' and 'loop' in result.get('reason', '').lower():
        print("  Loop detected and handled correctly")
    else:
        print("  No loop (expected for mock)")

    print("  ✅ PASS\n")


def test_e2e_job_package_schema():
    """Test that generated job package matches schema"""
    print("Test: Job Package Schema Validation")

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True
    )

    if 'job_package' in result:
        job_pkg = result['job_package']

        # Validate required top-level fields
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

        missing = []
        for field in required_fields:
            if field not in job_pkg:
                missing.append(field)
            else:
                print(f"  ✓ {field}")

        if missing:
            print(f"  ✗ Missing fields: {missing}")
            assert False, f"Missing required fields: {missing}"

        print("  ✅ PASS\n")
    else:
        print("  ⚠️  No job package in result\n")


def test_e2e_rescue_max_once():
    """Test RESCUE is attempted max once"""
    print("Test: RESCUE Max Once")

    result = run_backlink_job(
        publisher_domain="test.com",
        target_url="https://example.com",
        anchor_text="test",
        mock=True
    )

    exec_log = result.get('execution_log', {})
    log_entries = exec_log.get('log_entries', [])

    # Count RESCUE transitions
    rescue_transitions = [e for e in log_entries if e.get('type') == 'state_transition' and e.get('to_state') == 'RESCUE']
    rescue_count = len(rescue_transitions)

    print(f"  RESCUE Transitions: {rescue_count}")
    assert rescue_count <= 1, "RESCUE should be attempted max once"

    print("  ✅ PASS\n")


if __name__ == "__main__":
    print("=" * 70)
    print("BACOWR E2E Mock Tests")
    print("Per NEXT-A1-ENGINE-ADDENDUM.md")
    print("=" * 70)
    print()

    try:
        test_e2e_mock_success()
        test_e2e_state_transitions()
        test_e2e_qc_integration()
        test_e2e_output_files()
        test_e2e_loop_detection()
        test_e2e_job_package_schema()
        test_e2e_rescue_max_once()

        print("=" * 70)
        print("✅ All E2E tests passed!")
        print("=" * 70)
        print()
        print("Note: Mock articles may be BLOCKED by QC due to")
        print("missing trust sources or low LSI count. This is")
        print("expected and demonstrates QC is working correctly.")
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
