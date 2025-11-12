#!/usr/bin/env python3
"""
State Machine Tests for BACOWR

Tests the BacklinkStateMachine and ExecutionLogger for production readiness.

Per BUILDER_PROMPT.md STEG 2.3
"""

import pytest
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.engine.state_machine import BacklinkStateMachine, State
from src.engine.execution_logger import ExecutionLogger


class TestBacklinkStateMachine:
    """Test suite for BacklinkStateMachine."""

    def setup_method(self):
        """Setup test fixtures before each test."""
        self.job_id = "test_job_123"
        self.sm = BacklinkStateMachine(self.job_id)

    def test_initialization(self):
        """Test state machine initializes correctly."""
        assert self.sm.job_id == self.job_id
        assert self.sm.state == State.RECEIVE
        assert self.sm.rescue_count == 0
        assert len(self.sm.transitions) == 0
        assert self.sm.started_at is not None

    def test_valid_happy_path_transitions(self):
        """Test valid state transitions through happy path."""
        # RECEIVE → PREFLIGHT
        self.sm.transition(State.PREFLIGHT)
        assert self.sm.state == State.PREFLIGHT
        assert len(self.sm.transitions) == 1

        # PREFLIGHT → WRITE
        self.sm.transition(State.WRITE)
        assert self.sm.state == State.WRITE
        assert len(self.sm.transitions) == 2

        # WRITE → QC
        self.sm.transition(State.QC)
        assert self.sm.state == State.QC

        # QC → DELIVER
        self.sm.transition(State.DELIVER)
        assert self.sm.state == State.DELIVER
        assert self.sm.completed_at is not None

    def test_rescue_path_transitions(self):
        """Test transitions through RESCUE path."""
        # Navigate to QC
        self.sm.transition(State.PREFLIGHT)
        self.sm.transition(State.WRITE)
        self.sm.transition(State.QC)

        # QC → RESCUE
        self.sm.transition(State.RESCUE)
        assert self.sm.state == State.RESCUE
        assert self.sm.rescue_count == 1

        # RESCUE → QC
        self.sm.transition(State.QC)
        assert self.sm.state == State.QC

        # QC → DELIVER (after rescue)
        self.sm.transition(State.DELIVER)
        assert self.sm.state == State.DELIVER

    def test_invalid_transition(self):
        """Test that invalid transitions raise ValueError."""
        # Cannot go directly from RECEIVE to DELIVER
        with pytest.raises(ValueError, match="Invalid transition"):
            self.sm.transition(State.DELIVER)

        # Cannot go from RECEIVE to QC
        with pytest.raises(ValueError, match="Invalid transition"):
            self.sm.transition(State.QC)

    def test_rescue_limit_enforcement(self):
        """Test that RESCUE is limited to once per job."""
        # Navigate to QC
        self.sm.transition(State.PREFLIGHT)
        self.sm.transition(State.WRITE)
        self.sm.transition(State.QC)

        # First RESCUE - should work
        self.sm.transition(State.RESCUE)
        assert self.sm.rescue_count == 1

        # Back to QC
        self.sm.transition(State.QC)

        # Second RESCUE - should fail
        with pytest.raises(ValueError, match="Max RESCUE attempts"):
            self.sm.transition(State.RESCUE)

        # Should be able to ABORT instead
        self.sm.transition(State.ABORT)
        assert self.sm.state == State.ABORT

    def test_loop_detection(self):
        """Test payload loop detection."""
        payload_v1 = {"content": "Version 1"}
        payload_v2 = {"content": "Version 2"}

        # Check payload after WRITE - first time
        is_loop = self.sm.check_loop(payload_v1, "WRITE")
        assert not is_loop, "First time should not be a loop"

        # Check same payload again - should detect loop
        is_loop = self.sm.check_loop(payload_v1, "WRITE")
        assert is_loop, "Same payload second time should be detected as loop"

        # Different payload should not be a loop
        is_loop = self.sm.check_loop(payload_v2, "RESCUE")
        assert not is_loop, "Different payload should not be a loop"

        # Same payload again on RESCUE should be loop
        is_loop = self.sm.check_loop(payload_v2, "RESCUE")
        assert is_loop, "Same payload on same state should be loop"

    def test_transition_history(self):
        """Test that transitions are logged."""
        # Make several transitions
        self.sm.transition(State.PREFLIGHT, metadata={"test": "data"})
        self.sm.transition(State.WRITE)
        self.sm.transition(State.QC)

        # Check history
        assert len(self.sm.transitions) == 3

        # Check first transition
        trans = self.sm.transitions[0]
        assert trans['from_state'] == State.RECEIVE.value
        assert trans['to_state'] == State.PREFLIGHT.value
        assert trans['metadata']['test'] == "data"
        assert 'timestamp' in trans

    def test_get_execution_log(self):
        """Test getting execution log."""
        # Make some transitions
        self.sm.transition(State.PREFLIGHT)
        self.sm.transition(State.WRITE)
        self.sm.transition(State.QC)
        self.sm.transition(State.DELIVER)

        # Get execution log
        log = self.sm.get_execution_log()

        assert log['job_id'] == self.job_id
        assert log['current_state'] == State.DELIVER.value
        assert log['final_state'] == State.DELIVER.value
        assert log['total_transitions'] == 4
        assert log['rescue_count'] == 0
        assert 'started_at' in log
        assert 'completed_at' in log

    def test_terminal_state_enforcement(self):
        """Test that terminal states (DELIVER, ABORT) cannot transition."""
        # Navigate to DELIVER
        self.sm.transition(State.PREFLIGHT)
        self.sm.transition(State.WRITE)
        self.sm.transition(State.QC)
        self.sm.transition(State.DELIVER)

        # Try to transition from DELIVER - should fail
        with pytest.raises(ValueError, match="Invalid transition"):
            self.sm.transition(State.WRITE)

    def test_abort_path(self):
        """Test transitioning to ABORT from various states."""
        # Can abort from RECEIVE
        sm_abort1 = BacklinkStateMachine("abort_test_1")
        sm_abort1.transition(State.ABORT)
        assert sm_abort1.state == State.ABORT

        # Can abort from PREFLIGHT
        sm_abort2 = BacklinkStateMachine("abort_test_2")
        sm_abort2.transition(State.PREFLIGHT)
        sm_abort2.transition(State.ABORT)
        assert sm_abort2.state == State.ABORT

        # Can abort from QC
        sm_abort3 = BacklinkStateMachine("abort_test_3")
        sm_abort3.transition(State.PREFLIGHT)
        sm_abort3.transition(State.WRITE)
        sm_abort3.transition(State.QC)
        sm_abort3.transition(State.ABORT)
        assert sm_abort3.state == State.ABORT


class TestExecutionLogger:
    """Test suite for ExecutionLogger."""

    def setup_method(self):
        """Setup test fixtures."""
        self.job_id = "test_job_logger_123"
        self.output_dir = project_root / "storage" / "output"
        self.logger = ExecutionLogger(self.job_id, str(self.output_dir))

    def test_initialization(self):
        """Test logger initializes correctly."""
        assert self.logger.job_id == self.job_id
        assert len(self.logger.log_entries) == 0
        assert self.logger.metadata['job_id'] == self.job_id
        assert self.logger.metadata['started_at'] is not None
        assert self.logger.output_dir.exists()

    def test_log_state_transition(self):
        """Test logging state transitions."""
        self.logger.log_state_transition("RECEIVE", "PREFLIGHT", {"test": "data"})

        assert len(self.logger.log_entries) == 1

        entry = self.logger.log_entries[0]
        assert entry['type'] == 'state_transition'
        assert entry['from_state'] == "RECEIVE"
        assert entry['to_state'] == "PREFLIGHT"
        assert entry['metadata']['test'] == "data"
        assert 'timestamp' in entry

    def test_log_qc_result(self):
        """Test logging QC results."""
        qc_report = {
            'status': 'PASS',
            'issues': [{'issue': 'test'}],
            'human_signoff_required': False
        }

        self.logger.log_qc_result(qc_report)

        assert len(self.logger.log_entries) == 1

        entry = self.logger.log_entries[0]
        assert entry['type'] == 'qc_result'
        assert entry['status'] == 'PASS'
        assert entry['issues_count'] == 1
        assert entry['human_signoff_required'] is False

    def test_log_autofix(self):
        """Test logging AutoFix operations."""
        fix_logs = [
            {
                'timestamp': datetime.utcnow().isoformat(),
                'fix_type': 'inject_lsi',
                'issue_category': 'LSI',
                'reason': 'Missing LSI terms'
            },
            {
                'timestamp': datetime.utcnow().isoformat(),
                'fix_type': 'move_link',
                'issue_category': 'LINK_PLACEMENT',
                'reason': 'Link in H1'
            }
        ]

        self.logger.log_autofix(fix_logs)

        assert len(self.logger.log_entries) == 2

        entry1 = self.logger.log_entries[0]
        assert entry1['type'] == 'autofix'
        assert entry1['fix_type'] == 'inject_lsi'

        entry2 = self.logger.log_entries[1]
        assert entry2['type'] == 'autofix'
        assert entry2['fix_type'] == 'move_link'

    def test_log_error(self):
        """Test logging errors."""
        self.logger.log_error(
            "Test error message",
            error_type="ValidationError",
            details={"key": "value"}
        )

        assert len(self.logger.log_entries) == 1

        entry = self.logger.log_entries[0]
        assert entry['type'] == 'error'
        assert entry['error_type'] == "ValidationError"
        assert entry['message'] == "Test error message"
        assert entry['details']['key'] == "value"

    def test_log_warning(self):
        """Test logging warnings."""
        self.logger.log_warning("Test warning", {"context": "test"})

        assert len(self.logger.log_entries) == 1

        entry = self.logger.log_entries[0]
        assert entry['type'] == 'warning'
        assert entry['message'] == "Test warning"

    def test_log_info(self):
        """Test logging info messages."""
        self.logger.log_info("Test info message", {"detail": "value"})

        assert len(self.logger.log_entries) == 1

        entry = self.logger.log_entries[0]
        assert entry['type'] == 'info'
        assert entry['message'] == "Test info message"

    def test_finalize(self):
        """Test finalizing the log."""
        self.logger.finalize("DELIVER", "success")

        assert self.logger.metadata['completed_at'] is not None
        assert self.logger.metadata['final_state'] == "DELIVER"
        assert self.logger.metadata['final_status'] == "success"
        assert self.logger.metadata['total_log_entries'] == 0  # No entries yet

    def test_save_and_load(self):
        """Test saving log to file."""
        # Add some log entries
        self.logger.log_state_transition("RECEIVE", "PREFLIGHT")
        self.logger.log_info("Test message")
        self.logger.finalize("DELIVER", "success")

        # Save
        filepath = self.logger.save()

        assert filepath.exists()
        assert filepath.name == f"{self.job_id}_execution_log.json"

        # Load and verify
        with open(filepath, 'r') as f:
            log_data = json.load(f)

        assert log_data['metadata']['job_id'] == self.job_id
        assert len(log_data['log_entries']) == 2
        assert log_data['summary']['total_entries'] == 2
        assert 'duration_seconds' in log_data['summary']

        # Cleanup
        filepath.unlink()

    def test_get_log(self):
        """Test getting log data without saving."""
        self.logger.log_state_transition("RECEIVE", "PREFLIGHT")
        self.logger.log_info("Test")

        log_data = self.logger.get_log()

        assert 'metadata' in log_data
        assert 'log_entries' in log_data
        assert 'summary' in log_data
        assert log_data['summary']['total_entries'] == 2

    def test_count_entry_types(self):
        """Test entry type counting."""
        self.logger.log_state_transition("RECEIVE", "PREFLIGHT")
        self.logger.log_state_transition("PREFLIGHT", "WRITE")
        self.logger.log_info("Info 1")
        self.logger.log_info("Info 2")
        self.logger.log_error("Error 1")

        log_data = self.logger.get_log()
        entry_types = log_data['summary']['entry_types']

        assert entry_types['state_transition'] == 2
        assert entry_types['info'] == 2
        assert entry_types['error'] == 1

    def test_duration_calculation(self):
        """Test duration calculation."""
        import time

        # Add some entries
        self.logger.log_info("Start")

        # Wait a bit
        time.sleep(0.1)

        # Finalize
        self.logger.finalize("DELIVER", "success")

        log_data = self.logger.get_log()
        duration = log_data['summary']['duration_seconds']

        assert duration is not None
        assert duration >= 0.1
        assert duration < 1.0  # Should be less than 1 second

    def test_summary_string(self):
        """Test human-readable summary."""
        self.logger.log_state_transition("RECEIVE", "PREFLIGHT")
        self.logger.log_info("Test message")
        self.logger.finalize("DELIVER", "success")

        summary = self.logger.summary()

        assert self.job_id in summary
        assert "Started:" in summary
        assert "Completed:" in summary
        # Duration line is only added if duration exists and is > 0
        assert "Total Entries: 2" in summary


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """Run tests in standalone mode (without pytest)."""
    log("BACOWR State Machine & Execution Logger Tests")
    log("Per BUILDER_PROMPT.md STEG 2.3\n")
    log("=" * 60)

    try:
        # Test state machine
        log("\n🔍 Testing BacklinkStateMachine...")

        sm = BacklinkStateMachine("standalone_test_job")
        log(f"✅ State machine initialized: {sm.job_id}")

        # Test happy path
        sm.transition(State.PREFLIGHT)
        sm.transition(State.WRITE)
        sm.transition(State.QC)
        sm.transition(State.DELIVER)
        log(f"✅ Happy path transitions: {len(sm.transitions)} transitions")

        # Test execution logger
        log("\n🔍 Testing ExecutionLogger...")

        logger = ExecutionLogger("standalone_logger_test")
        log(f"✅ Logger initialized: {logger.job_id}")

        logger.log_state_transition("RECEIVE", "PREFLIGHT")
        logger.log_info("Test message")
        logger.finalize("DELIVER", "success")
        log(f"✅ Logger working: {len(logger.log_entries)} entries")

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
        sys.exit(0)
    else:
        log("❌ TESTS FAILED", "ERROR")
        sys.exit(1)
