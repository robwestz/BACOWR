"""
Execution Logger for BACOWR
Per NEXT-A1-ENGINE-ADDENDUM.md § 4

Logs all state transitions, QC results, and autofix operations
to storage/output/{job_id}_execution_log.json
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class ExecutionLogger:
    """
    Manages execution logging for a job.

    Collects:
    - State transitions
    - QC results
    - AutoFix operations
    - Errors and warnings
    """

    def __init__(self, job_id: str, output_dir: Optional[str] = None):
        """
        Initialize execution logger.

        Args:
            job_id: Job identifier
            output_dir: Output directory (default: storage/output/)
        """
        self.job_id = job_id
        self.log_entries: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            'job_id': job_id,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None
        }

        # Set output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).parent.parent.parent / 'storage' / 'output'

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def log_state_transition(self, from_state: str, to_state: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Log a state transition.

        Args:
            from_state: Source state
            to_state: Target state
            metadata: Additional context
        """
        entry = {
            'type': 'state_transition',
            'timestamp': datetime.utcnow().isoformat(),
            'from_state': from_state,
            'to_state': to_state,
            'metadata': metadata or {}
        }
        self.log_entries.append(entry)

    def log_qc_result(self, qc_report: Dict[str, Any]):
        """
        Log QC validation result.

        Args:
            qc_report: QC report dict
        """
        entry = {
            'type': 'qc_result',
            'timestamp': datetime.utcnow().isoformat(),
            'status': qc_report.get('status'),
            'issues_count': len(qc_report.get('issues', [])),
            'human_signoff_required': qc_report.get('human_signoff_required', False),
            'details': qc_report
        }
        self.log_entries.append(entry)

    def log_autofix(self, fix_logs: List[Dict[str, Any]]):
        """
        Log AutoFix operations.

        Args:
            fix_logs: List of AutoFixLog dicts
        """
        for fix_log in fix_logs:
            entry = {
                'type': 'autofix',
                'timestamp': fix_log.get('timestamp', datetime.utcnow().isoformat()),
                'fix_type': fix_log.get('fix_type'),
                'issue_category': fix_log.get('issue_category'),
                'reason': fix_log.get('reason'),
                'details': fix_log
            }
            self.log_entries.append(entry)

    def log_error(self, error_message: str, error_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        """
        Log an error.

        Args:
            error_message: Error message
            error_type: Type of error
            details: Additional error details
        """
        entry = {
            'type': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error_type': error_type or 'unknown',
            'message': error_message,
            'details': details or {}
        }
        self.log_entries.append(entry)

    def log_warning(self, warning_message: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a warning.

        Args:
            warning_message: Warning message
            details: Additional details
        """
        entry = {
            'type': 'warning',
            'timestamp': datetime.utcnow().isoformat(),
            'message': warning_message,
            'details': details or {}
        }
        self.log_entries.append(entry)

    def log_info(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Log general information.

        Args:
            message: Info message
            details: Additional details
        """
        entry = {
            'type': 'info',
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'details': details or {}
        }
        self.log_entries.append(entry)

    def finalize(self, final_state: str, status: str):
        """
        Finalize the log.

        Args:
            final_state: Final state (DELIVER/ABORT)
            status: Final status
        """
        self.metadata['completed_at'] = datetime.utcnow().isoformat()
        self.metadata['final_state'] = final_state
        self.metadata['final_status'] = status
        self.metadata['total_log_entries'] = len(self.log_entries)

    def save(self, filename: Optional[str] = None) -> Path:
        """
        Save execution log to file.

        Args:
            filename: Custom filename (default: {job_id}_execution_log.json)

        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"{self.job_id}_execution_log.json"

        filepath = self.output_dir / filename

        log_data = {
            'metadata': self.metadata,
            'log_entries': self.log_entries,
            'summary': {
                'total_entries': len(self.log_entries),
                'entry_types': self._count_entry_types(),
                'duration_seconds': self._calculate_duration()
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        return filepath

    def get_log(self) -> Dict[str, Any]:
        """
        Get current log data without saving.

        Returns:
            Complete log data
        """
        return {
            'metadata': self.metadata,
            'log_entries': self.log_entries,
            'summary': {
                'total_entries': len(self.log_entries),
                'entry_types': self._count_entry_types(),
                'duration_seconds': self._calculate_duration()
            }
        }

    def _count_entry_types(self) -> Dict[str, int]:
        """Count entries by type"""
        counts = {}
        for entry in self.log_entries:
            entry_type = entry.get('type', 'unknown')
            counts[entry_type] = counts.get(entry_type, 0) + 1
        return counts

    def _calculate_duration(self) -> Optional[float]:
        """Calculate duration in seconds"""
        if not self.metadata.get('completed_at'):
            return None

        started = datetime.fromisoformat(self.metadata['started_at'])
        completed = datetime.fromisoformat(self.metadata['completed_at'])
        duration = (completed - started).total_seconds()
        return round(duration, 2)

    def summary(self) -> str:
        """
        Human-readable summary.

        Returns:
            Summary string
        """
        lines = [
            f"Execution Log for Job {self.job_id}",
            f"Started: {self.metadata['started_at']}"
        ]

        if self.metadata.get('completed_at'):
            lines.append(f"Completed: {self.metadata['completed_at']}")
            duration = self._calculate_duration()
            if duration:
                lines.append(f"Duration: {duration}s")

        lines.append(f"\nTotal Entries: {len(self.log_entries)}")

        entry_counts = self._count_entry_types()
        if entry_counts:
            lines.append("\nBy Type:")
            for entry_type, count in sorted(entry_counts.items()):
                lines.append(f"  - {entry_type}: {count}")

        return "\n".join(lines)
