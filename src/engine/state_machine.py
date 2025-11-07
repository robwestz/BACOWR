"""
State Machine for BACOWR Pipeline
Per NEXT-A1-ENGINE-ADDENDUM.md § 4

States: RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
                                         ↓ (on fail)
                                      RESCUE → QC
                                         ↓ (on loop)
                                       ABORT
"""

import hashlib
import json
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List


class State(Enum):
    """Pipeline states"""
    RECEIVE = "RECEIVE"
    PREFLIGHT = "PREFLIGHT"
    WRITE = "WRITE"
    QC = "QC"
    DELIVER = "DELIVER"
    RESCUE = "RESCUE"
    ABORT = "ABORT"


class BacklinkStateMachine:
    """
    Manages state transitions for backlink content pipeline.

    Ensures deterministic flow with:
    - Loop protection
    - Max 1 RESCUE attempt
    - Full transition logging
    """

    def __init__(self, job_id: str):
        """
        Initialize state machine for a job.

        Args:
            job_id: Unique job identifier
        """
        self.job_id = job_id
        self.state = State.RECEIVE
        self.transitions: List[Dict[str, Any]] = []
        self.rescue_count = 0
        self.payload_hashes: Dict[str, str] = {}  # state -> hash
        self.started_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None

    def transition(self, new_state: State, metadata: Optional[Dict[str, Any]] = None):
        """
        Transition to a new state with validation.

        Args:
            new_state: Target state
            metadata: Additional context for transition

        Raises:
            ValueError: If transition is invalid
        """
        if metadata is None:
            metadata = {}

        # Validate transition
        if not self._is_valid_transition(self.state, new_state):
            raise ValueError(
                f"Invalid transition from {self.state.value} to {new_state.value}"
            )

        # Check RESCUE limit
        if new_state == State.RESCUE:
            if self.rescue_count >= 1:
                raise ValueError("Max RESCUE attempts (1) exceeded. Transitioning to ABORT.")

            self.rescue_count += 1

        # Log transition
        transition_record = {
            'from_state': self.state.value,
            'to_state': new_state.value,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
        self.transitions.append(transition_record)

        # Update state
        old_state = self.state
        self.state = new_state

        # Mark completion time for terminal states
        if new_state in [State.DELIVER, State.ABORT]:
            self.completed_at = datetime.utcnow().isoformat()

    def check_loop(self, payload: Any, state_label: str) -> bool:
        """
        Check if payload is unchanged (indicating a loop).

        Args:
            payload: Current payload (dict or str)
            state_label: Label for this state check (e.g., 'WRITE', 'RESCUE')

        Returns:
            True if loop detected, False otherwise
        """
        # Hash the payload
        payload_str = json.dumps(payload, sort_keys=True) if isinstance(payload, dict) else str(payload)
        payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        # Check if we've seen this hash before
        if state_label in self.payload_hashes:
            previous_hash = self.payload_hashes[state_label]
            if previous_hash == payload_hash:
                return True  # Loop detected!

        # Store current hash
        self.payload_hashes[state_label] = payload_hash
        return False

    def should_abort(self, reason: str) -> bool:
        """
        Determine if pipeline should abort.

        Args:
            reason: Reason for potential abort

        Returns:
            True if should abort
        """
        # Abort conditions:
        # 1. Loop detected
        # 2. Max RESCUE attempts
        # 3. Critical QC failure with no autofix

        if 'loop' in reason.lower():
            return True

        if self.rescue_count >= 1 and 'rescue_failed' in reason.lower():
            return True

        return False

    def get_execution_log(self) -> Dict[str, Any]:
        """
        Get complete execution log.

        Returns:
            Execution log with all transitions and metadata
        """
        return {
            'job_id': self.job_id,
            'initial_state': State.RECEIVE.value,
            'current_state': self.state.value,
            'final_state': self.state.value if self.state in [State.DELIVER, State.ABORT] else None,
            'transitions': self.transitions,
            'rescue_count': self.rescue_count,
            'payload_hashes': {k: v[:8] for k, v in self.payload_hashes.items()},  # Truncated for readability
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'total_transitions': len(self.transitions)
        }

    def _is_valid_transition(self, from_state: State, to_state: State) -> bool:
        """
        Validate state transition.

        Returns:
            True if transition is allowed
        """
        # Define allowed transitions
        allowed = {
            State.RECEIVE: [State.PREFLIGHT, State.ABORT],
            State.PREFLIGHT: [State.WRITE, State.ABORT],
            State.WRITE: [State.QC, State.ABORT],
            State.QC: [State.DELIVER, State.RESCUE, State.ABORT],
            State.RESCUE: [State.QC, State.ABORT],
            State.DELIVER: [],  # Terminal
            State.ABORT: []     # Terminal
        }

        return to_state in allowed.get(from_state, [])

    def summary(self) -> str:
        """
        Human-readable summary of state machine.

        Returns:
            Summary string
        """
        lines = [
            f"State Machine for Job {self.job_id}",
            f"Current State: {self.state.value}",
            f"Transitions: {len(self.transitions)}",
            f"RESCUE Count: {self.rescue_count}"
        ]

        if self.completed_at:
            lines.append(f"Status: Completed at {self.completed_at}")
        else:
            lines.append("Status: In Progress")

        return "\n".join(lines)
