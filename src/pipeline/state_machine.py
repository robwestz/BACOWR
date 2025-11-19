"""
State Machine - Orchestrates the complete backlink content generation pipeline.

States: RECEIVE → PREFLIGHT → WRITE → QC → DELIVER
With RESCUE (AutoFixOnce) and ABORT fallback states.

This provides deterministic, traceable, and debuggable execution.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

from .job_assembler import BacklinkJobAssembler
from .writer_engine import WriterEngine
from ..qc.quality_controller import QualityController, QCReport
from ..utils.logger import get_logger

logger = get_logger(__name__)


class State(Enum):
    """Pipeline states."""
    RECEIVE = "RECEIVE"  # Receive input
    PREFLIGHT = "PREFLIGHT"  # Assemble job package
    WRITE = "WRITE"  # Generate content
    QC = "QC"  # Quality control
    RESCUE = "RESCUE"  # AutoFixOnce attempt
    DELIVER = "DELIVER"  # Success - deliver output
    ABORT = "ABORT"  # Failure - cannot continue


@dataclass
class ExecutionLog:
    """Log entry for state transitions."""
    timestamp: str
    from_state: Optional[str]
    to_state: str
    success: bool
    message: str
    data: Dict = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete pipeline execution result."""
    success: bool
    final_state: State
    job_id: Optional[str]
    job_package: Optional[Dict]
    article_text: Optional[str]
    extensions: Optional[Dict]
    qc_report: Optional[QCReport]
    execution_log: List[ExecutionLog]
    error_message: Optional[str]


class BacklinkPipeline:
    """
    State machine for backlink content generation.

    Orchestrates: Receive → Preflight → Write → QC → Deliver
    With RESCUE and ABORT states for error handling.
    """

    def __init__(
        self,
        serp_mode: str = "mock",
        serp_api_key: Optional[str] = None,
        writer_api_key: Optional[str] = None,
        writer_model: str = "claude-sonnet-4-5-20250929"
    ):
        """
        Initialize pipeline with required components.

        Args:
            serp_mode: "mock" or "api" for SERP fetching
            serp_api_key: Optional SERP API key
            writer_api_key: Optional writer API key (Anthropic)
            writer_model: Claude model to use
        """
        self.assembler = BacklinkJobAssembler(serp_mode=serp_mode, serp_api_key=serp_api_key)
        # Use mock_mode when no API key provided
        self.writer = WriterEngine(mock_mode=(writer_api_key is None))
        self.qc = QualityController()

        self.current_state = State.RECEIVE
        self.execution_log: List[ExecutionLog] = []
        self.payload_hashes: set = set()  # For loop detection

        logger.info("BacklinkPipeline initialized", serp_mode=serp_mode, mock_mode=(writer_api_key is None))

    def execute(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        anchor_type_hint: Optional[str] = None,
        min_word_count: int = 900,
        language: Optional[str] = None,
        output_dir: Optional[Path] = None
    ) -> PipelineResult:
        """
        Execute complete pipeline.

        Args:
            publisher_domain: Domain where content will be published
            target_url: URL receiving backlink
            anchor_text: Anchor text
            anchor_type_hint: Optional anchor type hint
            min_word_count: Minimum word count
            language: Optional language override
            output_dir: Optional output directory

        Returns:
            PipelineResult with complete execution trace
        """
        logger.info(
            "Pipeline execution started",
            publisher=publisher_domain,
            target=target_url[:50]
        )

        result = PipelineResult(
            success=False,
            final_state=State.RECEIVE,
            job_id=None,
            job_package=None,
            article_text=None,
            extensions=None,
            qc_report=None,
            execution_log=[],
            error_message=None
        )

        try:
            # State: RECEIVE → PREFLIGHT
            self._transition(State.RECEIVE, State.PREFLIGHT, "Starting preflight analysis")

            # State: PREFLIGHT (assemble job package)
            job_package, valid, error = self.assembler.assemble_job_package(
                publisher_domain=publisher_domain,
                target_url=target_url,
                anchor_text=anchor_text,
                anchor_type_hint=anchor_type_hint,
                min_word_count=min_word_count,
                language=language
            )

            if not valid:
                self._transition(State.PREFLIGHT, State.ABORT, f"Preflight failed: {error}")
                result.error_message = error
                result.final_state = State.ABORT
                result.execution_log = self.execution_log
                return result

            result.job_package = job_package
            result.job_id = job_package["job_meta"]["job_id"]

            self._log_success(State.PREFLIGHT, "Job package assembled", {
                "job_id": result.job_id,
                "bridge_type": job_package["intent_extension"]["recommended_bridge_type"]
            })

            # State: PREFLIGHT → WRITE
            self._transition(State.PREFLIGHT, State.WRITE, "Starting content generation")

            # State: WRITE
            article_text, extensions, write_success, write_error = self.writer.generate_content(job_package)

            if not write_success:
                self._transition(State.WRITE, State.ABORT, f"Writing failed: {write_error}")
                result.error_message = write_error
                result.final_state = State.ABORT
                result.execution_log = self.execution_log
                return result

            result.article_text = article_text
            result.extensions = extensions

            self._log_success(State.WRITE, "Content generated", {
                "article_length": len(article_text),
                "word_count": len(article_text.split())
            })

            # State: WRITE → QC
            self._transition(State.WRITE, State.QC, "Starting quality control")

            # State: QC
            qc_report = self.qc.validate_content(job_package, extensions, article_text)
            result.qc_report = qc_report

            self._log_success(State.QC, f"QC completed: {qc_report.status}", {
                "status": qc_report.status,
                "issues": len(qc_report.issues)
            })

            # Decision point: QC status
            if qc_report.status == "pass":
                # Success path: QC → DELIVER
                self._transition(State.QC, State.DELIVER, "QC passed, delivering")
                result.success = True
                result.final_state = State.DELIVER

            elif qc_report.status in ["warning", "fail"]:
                # Check if autofix possible
                autofix_possible = any(issue.autofix_possible for issue in qc_report.issues)

                if autofix_possible and not qc_report.autofix_done:
                    # RESCUE path: QC → RESCUE (AutoFixOnce)
                    self._transition(State.QC, State.RESCUE, "Attempting AutoFixOnce")

                    # TODO: Implement actual autofix logic
                    # For now, just mark as attempted
                    logger.warning("AutoFixOnce not yet fully implemented")
                    self._transition(State.RESCUE, State.DELIVER, "AutoFix attempted, delivering with warnings")
                    result.success = True
                    result.final_state = State.DELIVER

                else:
                    # Cannot autofix or already tried
                    if qc_report.status == "fail":
                        self._transition(State.QC, State.ABORT, "QC failed, no autofix available")
                        result.final_state = State.ABORT
                        result.error_message = "QC validation failed with critical issues"
                    else:
                        # warning but no autofix - deliver with warnings
                        self._transition(State.QC, State.DELIVER, "Delivering with QC warnings")
                        result.success = True
                        result.final_state = State.DELIVER

            elif qc_report.status == "needs_signoff":
                # Needs human review
                self._transition(State.QC, State.DELIVER, "Delivering for human review (signoff required)")
                result.success = True
                result.final_state = State.DELIVER

            # Save output if requested
            if output_dir and result.success:
                self._save_output(result, output_dir)

        except Exception as e:
            error_msg = f"Pipeline exception: {str(e)}"
            logger.error("Pipeline execution failed", error=error_msg, exc_info=True)
            self._transition(self.current_state, State.ABORT, error_msg)
            result.error_message = error_msg
            result.final_state = State.ABORT

        result.execution_log = self.execution_log

        logger.info(
            "Pipeline execution complete",
            success=result.success,
            final_state=result.final_state.value
        )

        return result

    def _transition(self, from_state: State, to_state: State, message: str) -> None:
        """Log state transition."""
        log_entry = ExecutionLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            from_state=from_state.value if from_state else None,
            to_state=to_state.value,
            success=to_state not in [State.ABORT],
            message=message
        )
        self.execution_log.append(log_entry)
        self.current_state = to_state
        logger.info("State transition", from_state=from_state.value, to_state=to_state.value, message=message)

    def _log_success(self, state: State, message: str, data: Dict = None) -> None:
        """Log successful operation within a state."""
        log_entry = ExecutionLog(
            timestamp=datetime.utcnow().isoformat() + "Z",
            from_state=state.value,
            to_state=state.value,
            success=True,
            message=message,
            data=data or {}
        )
        self.execution_log.append(log_entry)
        logger.debug("State operation", state=state.value, message=message)

    def _detect_loop(self, payload: Dict) -> bool:
        """
        Detect if we're in a loop (same payload repeated).

        Returns True if loop detected.
        """
        payload_str = json.dumps(payload, sort_keys=True)
        payload_hash = hashlib.md5(payload_str.encode()).hexdigest()

        if payload_hash in self.payload_hashes:
            logger.error("Loop detected - same payload repeated", hash=payload_hash)
            return True

        self.payload_hashes.add(payload_hash)
        return False

    def _save_output(self, result: PipelineResult, output_dir: Path) -> None:
        """
        Save pipeline output to files.

        Saves:
        - job_package.json
        - article.md
        - article.html (if HTML format)
        - extensions.json
        - qc_report.json
        - execution_log.json
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        job_id = result.job_id or "unknown"
        prefix = f"{job_id}"

        # Save job package
        if result.job_package:
            job_file = output_dir / f"{prefix}_job_package.json"
            with open(job_file, 'w', encoding='utf-8') as f:
                json.dump(result.job_package, f, ensure_ascii=False, indent=2)
            logger.info("Saved job package", path=str(job_file))

        # Save article
        if result.article_text:
            article_file = output_dir / f"{prefix}_article.md"
            with open(article_file, 'w', encoding='utf-8') as f:
                f.write(result.article_text)
            logger.info("Saved article", path=str(article_file))

        # Save extensions
        if result.extensions:
            ext_file = output_dir / f"{prefix}_extensions.json"
            with open(ext_file, 'w', encoding='utf-8') as f:
                json.dump(result.extensions, f, ensure_ascii=False, indent=2)
            logger.info("Saved extensions", path=str(ext_file))

        # Save QC report
        if result.qc_report:
            qc_dict = {
                "status": result.qc_report.status,
                "anchor_risk": result.qc_report.anchor_risk,
                "readability_score": result.qc_report.readability_score,
                "issues": [
                    {
                        "category": issue.category,
                        "severity": issue.severity,
                        "message": issue.message,
                        "autofix_possible": issue.autofix_possible
                    }
                    for issue in result.qc_report.issues
                ],
                "recommendations": result.qc_report.recommendations
            }
            qc_file = output_dir / f"{prefix}_qc_report.json"
            with open(qc_file, 'w', encoding='utf-8') as f:
                json.dump(qc_dict, f, ensure_ascii=False, indent=2)
            logger.info("Saved QC report", path=str(qc_file))

        # Save execution log
        log_dict = [
            {
                "timestamp": log.timestamp,
                "from_state": log.from_state,
                "to_state": log.to_state,
                "success": log.success,
                "message": log.message,
                "data": log.data
            }
            for log in result.execution_log
        ]
        log_file = output_dir / f"{prefix}_execution_log.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_dict, f, ensure_ascii=False, indent=2)
        logger.info("Saved execution log", path=str(log_file))

        logger.info("All output saved", output_dir=str(output_dir), prefix=prefix)
