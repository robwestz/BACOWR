"""
Middleware package for BACOWR API.

Contains middleware components for:
- Prometheus metrics export
- Rate limiting
- Audit logging
- Request logging
- Error handling
"""

from .prometheus import setup_metrics, track_llm_generation, track_job_completion, set_active_jobs, set_batch_progress, track_qc_score

__all__ = [
    'setup_metrics',
    'track_llm_generation',
    'track_job_completion',
    'set_active_jobs',
    'set_batch_progress',
    'track_qc_score',
]
