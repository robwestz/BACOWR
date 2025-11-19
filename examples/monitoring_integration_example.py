"""
Example: How to use monitoring metrics from other BACOWR modules

This shows how the Wave 3 monitoring integrates with existing services.
"""

# Example 1: Track LLM generation in ContentGenerator
# ====================================================
# In services/content_generator.py:

from api.app.middleware import track_llm_generation, track_qc_score
import time

class ContentGenerator:
    def generate_article(self, prompt: str, provider: str = 'anthropic'):
        start_time = time.time()

        # Generate content (existing code)
        article = self._call_llm_api(prompt, provider)

        # NEW: Track metrics for monitoring
        duration = time.time() - start_time
        cost = self._calculate_cost(article, provider)

        track_llm_generation(
            provider=provider,
            model='claude-3-opus',
            duration=duration,
            cost=cost
        )

        return article


# Example 2: Track job completion in JobOrchestrator
# ==================================================
# In services/job_orchestrator.py:

from api.app.middleware import track_job_completion, set_active_jobs

class JobOrchestrator:
    async def complete_job(self, job_id: str, status: str):
        # Complete job (existing code)
        job = await self._mark_job_complete(job_id, status)

        # NEW: Track metrics
        track_job_completion(status=status)

        # Update active jobs gauge
        active_count = await self._count_active_jobs()
        set_active_jobs(active_count)

        return job


# Example 3: Track QC scores in QualityControl
# ============================================
# In services/quality_control.py:

from api.app.middleware import track_qc_score

class QualityControl:
    async def evaluate_article(self, article: str):
        # Evaluate (existing code)
        score = await self._run_qc_checks(article)

        # NEW: Track QC score distribution
        track_qc_score(score=score)

        return score


# Example 4: Track batch progress in BatchReviewService
# =====================================================
# In services/batch_review_service.py:

from api.app.middleware import set_batch_progress

class BatchReviewService:
    async def process_batch(self, batch_id: str, articles: list):
        total = len(articles)

        for i, article in enumerate(articles):
            # Process article (existing code)
            await self._process_article(article)

            # NEW: Update batch progress
            progress = ((i + 1) / total) * 100
            set_batch_progress(batch_id=batch_id, progress_percent=progress)


# Example 5: Complete workflow with all metrics
# =============================================

async def complete_job_workflow_with_monitoring():
    """
    Shows how monitoring integrates into existing BACOWR workflow.
    This is the SAME workflow as before, just with added metrics tracking.
    """
    from services.job_orchestrator import JobOrchestrator
    from api.app.middleware import (
        track_llm_generation,
        track_job_completion,
        set_active_jobs,
        track_qc_score
    )

    orchestrator = JobOrchestrator()

    # 1. Create job (EXISTING functionality)
    job = await orchestrator.create_job(
        publisher='example.com',
        target_url='https://client.com/page',
        anchor_text='best product'
    )

    # 2. Generate content (EXISTING + NEW metrics)
    start = time.time()
    article = await orchestrator.generate_content(job.id)

    track_llm_generation(
        provider='anthropic',
        model='claude-3-opus',
        duration=time.time() - start,
        cost=0.045
    )

    # 3. QC evaluation (EXISTING + NEW metrics)
    qc_score = await orchestrator.evaluate_quality(job.id)
    track_qc_score(qc_score)

    # 4. Complete job (EXISTING + NEW metrics)
    await orchestrator.complete_job(job.id, status='delivered')
    track_job_completion(status='delivered')

    # 5. Update active jobs gauge
    active = await orchestrator.count_active_jobs()
    set_active_jobs(active)

    print(f"Job {job.id} completed with QC score {qc_score}")
    print(f"Metrics automatically sent to Prometheus at /metrics")


if __name__ == '__main__':
    import asyncio

    print("=" * 70)
    print("MONITORING INTEGRATION EXAMPLES")
    print("=" * 70)
    print()
    print("This shows how Wave 3 monitoring integrates with existing BACOWR code.")
    print()
    print("Key points:")
    print("1. All API endpoints get automatic metrics (requests, latency, errors)")
    print("2. Custom metrics can be tracked from any module")
    print("3. No changes to existing workflow - just ADD metric tracking calls")
    print("4. Metrics exposed at http://localhost:8000/metrics")
    print("5. Dashboards available at http://localhost:3001 (Grafana)")
    print()
    print("=" * 70)
