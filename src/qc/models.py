"""
QC Data Models for BACOWR
Per NEXT-A1-ENGINE-ADDENDUM.md § 3
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class QCStatus(Enum):
    """QC validation status"""
    PASS = "PASS"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"


class IssueSeverity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"  # Blocks delivery, requires human signoff
    HIGH = "HIGH"          # Blocks delivery, may be auto-fixable
    MEDIUM = "MEDIUM"      # Warning, may affect quality
    LOW = "LOW"            # Info, minor quality issue


class IssueCategory(Enum):
    """Issue categories"""
    LSI = "LSI"
    TRUST_SOURCES = "TRUST_SOURCES"
    ANCHOR_RISK = "ANCHOR_RISK"
    LINK_PLACEMENT = "LINK_PLACEMENT"
    WORD_COUNT = "WORD_COUNT"
    INTENT_ALIGNMENT = "INTENT_ALIGNMENT"
    COMPLIANCE = "COMPLIANCE"
    CONTENT_QUALITY = "CONTENT_QUALITY"


@dataclass
class QCIssue:
    """Individual QC issue"""
    category: IssueCategory
    severity: IssueSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    auto_fixable: bool = False
    fix_suggestion: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'category': self.category.value,
            'severity': self.severity.value,
            'message': self.message,
            'details': self.details or {},
            'auto_fixable': self.auto_fixable,
            'fix_suggestion': self.fix_suggestion
        }


@dataclass
class AutoFixLog:
    """Log entry for automatic fix"""
    issue_category: str
    fix_type: str
    before: str
    after: str
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class QCReport:
    """Complete QC validation report"""
    job_id: str
    status: QCStatus
    issues: List[QCIssue] = field(default_factory=list)
    autofix_done: bool = False
    autofix_logs: List[AutoFixLog] = field(default_factory=list)
    human_signoff_required: bool = False
    human_signoff_reason: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Detailed check results
    lsi_check: Optional[Dict[str, Any]] = None
    trust_check: Optional[Dict[str, Any]] = None
    anchor_check: Optional[Dict[str, Any]] = None
    placement_check: Optional[Dict[str, Any]] = None
    compliance_check: Optional[Dict[str, Any]] = None
    intent_check: Optional[Dict[str, Any]] = None

    def add_issue(self, issue: QCIssue):
        """Add an issue to the report"""
        self.issues.append(issue)

        # Update status based on severity
        if issue.severity == IssueSeverity.CRITICAL:
            self.status = QCStatus.BLOCKED
            self.human_signoff_required = True
            if not self.human_signoff_reason:
                self.human_signoff_reason = issue.message
        elif issue.severity == IssueSeverity.HIGH and self.status == QCStatus.PASS:
            self.status = QCStatus.BLOCKED
        elif issue.severity == IssueSeverity.MEDIUM and self.status == QCStatus.PASS:
            self.status = QCStatus.WARNING

    def add_autofix(self, fix_log: AutoFixLog):
        """Add an autofix log entry"""
        self.autofix_logs.append(fix_log)
        self.autofix_done = True

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'job_id': self.job_id,
            'status': self.status.value,
            'issues': [issue.to_dict() for issue in self.issues],
            'autofix_done': self.autofix_done,
            'autofix_logs': [log.to_dict() for log in self.autofix_logs],
            'human_signoff_required': self.human_signoff_required,
            'human_signoff_reason': self.human_signoff_reason,
            'timestamp': self.timestamp,
            'checks': {
                'lsi': self.lsi_check,
                'trust_sources': self.trust_check,
                'anchor': self.anchor_check,
                'placement': self.placement_check,
                'compliance': self.compliance_check,
                'intent': self.intent_check
            }
        }

    def summary(self) -> str:
        """Human-readable summary"""
        lines = [
            f"QC Report for {self.job_id}",
            f"Status: {self.status.value}",
            f"Issues: {len(self.issues)} total"
        ]

        if self.issues:
            by_severity = {}
            for issue in self.issues:
                sev = issue.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1

            lines.append("Breakdown:")
            for sev, count in sorted(by_severity.items()):
                lines.append(f"  - {sev}: {count}")

        if self.autofix_done:
            lines.append(f"AutoFix applied: {len(self.autofix_logs)} fixes")

        if self.human_signoff_required:
            lines.append(f"⚠️  Human signoff required: {self.human_signoff_reason}")

        return "\n".join(lines)
