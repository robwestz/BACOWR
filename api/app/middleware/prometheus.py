"""
Prometheus Metrics Middleware for BACOWR FastAPI

Exports metrics for monitoring:
- API requests (total, duration, status codes)
- LLM generation (duration, cost by provider)
- Active jobs
- Batch processing progress

Metrics exposed at /metrics endpoint
"""

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI, Response
from typing import Callable
import time


# Define custom metrics
# API Metrics
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

# LLM Metrics
llm_generation_duration_seconds = Histogram(
    'llm_generation_duration_seconds',
    'LLM generation duration in seconds',
    ['provider', 'model'],
    buckets=[5.0, 10.0, 20.0, 30.0, 60.0, 120.0, 300.0]
)

llm_generation_cost_dollars = Counter(
    'llm_generation_cost_dollars',
    'LLM generation cost in USD',
    ['provider', 'model']
)

# Job Metrics
active_jobs = Gauge(
    'active_jobs',
    'Number of currently active jobs'
)

jobs_completed_total = Counter(
    'jobs_completed_total',
    'Total completed jobs',
    ['status']  # delivered, blocked, failed
)

# Batch Metrics
batch_review_progress_percent = Gauge(
    'batch_review_progress_percent',
    'Batch review progress percentage',
    ['batch_id']
)

# QC Metrics
qc_score_histogram = Histogram(
    'qc_score',
    'QC score distribution',
    buckets=[0, 20, 40, 60, 70, 80, 85, 90, 95, 100]
)


def setup_metrics(app: FastAPI):
    """
    Setup Prometheus metrics for FastAPI application.

    Args:
        app: FastAPI application instance
    """
    # Initialize instrumentator with default metrics
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_respect_env_var=True,
        should_instrument_requests_inprogress=True,
        excluded_handlers=["/metrics", "/health"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="http_requests_inprogress",
        inprogress_labels=True,
    )

    # Add default metrics
    instrumentator.instrument(app)

    # Custom metrics endpoint
    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        """Expose Prometheus metrics."""
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Middleware for custom metrics
    @app.middleware("http")
    async def prometheus_middleware(request, call_next):
        """Custom middleware to track additional metrics."""
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)

        # Track request
        method = request.method
        endpoint = request.url.path
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        status_code = response.status_code

        # Update counters
        api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=f"{status_code // 100}xx"
        ).inc()

        # Update histogram
        api_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        return response

    return instrumentator


def track_llm_generation(provider: str, model: str, duration: float, cost: float):
    """
    Track LLM generation metrics.

    Args:
        provider: LLM provider (anthropic, openai, google)
        model: Model name (claude-3-haiku, gpt-4o, etc.)
        duration: Generation duration in seconds
        cost: Generation cost in USD
    """
    llm_generation_duration_seconds.labels(
        provider=provider,
        model=model
    ).observe(duration)

    llm_generation_cost_dollars.labels(
        provider=provider,
        model=model
    ).inc(cost)


def track_job_completion(status: str):
    """
    Track job completion.

    Args:
        status: Job status (delivered, blocked, failed)
    """
    jobs_completed_total.labels(status=status).inc()


def set_active_jobs(count: int):
    """
    Set number of active jobs.

    Args:
        count: Number of active jobs
    """
    active_jobs.set(count)


def set_batch_progress(batch_id: str, progress_percent: float):
    """
    Set batch processing progress.

    Args:
        batch_id: Batch identifier
        progress_percent: Progress percentage (0-100)
    """
    batch_review_progress_percent.labels(batch_id=batch_id).set(progress_percent)


def track_qc_score(score: float):
    """
    Track QC score.

    Args:
        score: QC score (0-100)
    """
    qc_score_histogram.observe(score)


# Export tracking functions for use in other modules
__all__ = [
    'setup_metrics',
    'track_llm_generation',
    'track_job_completion',
    'set_active_jobs',
    'set_batch_progress',
    'track_qc_score',
]
