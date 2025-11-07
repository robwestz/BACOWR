"""
Wrapper for BACOWR production API.

This module integrates the existing BACOWR system with the FastAPI backend.
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

# Add BACOWR root to path
BACOWR_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(BACOWR_ROOT))

from src.production_api import run_production_job


class BACOWRWrapper:
    """Wrapper for BACOWR production system."""

    def __init__(self):
        """Initialize wrapper."""
        self.bacowr_root = BACOWR_ROOT

    async def run_job(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        llm_provider: Optional[str] = None,
        writing_strategy: str = "multi_stage",
        use_ahrefs: bool = True,
        country: str = "se",
        enable_llm_profiling: bool = True,
        output_dir: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run a BACOWR content generation job.

        Args:
            publisher_domain: Publisher domain (e.g. "aftonbladet.se")
            target_url: Target URL to link to
            anchor_text: Anchor text for the link
            llm_provider: LLM provider ("anthropic", "openai", "google", or None for auto)
            writing_strategy: "multi_stage" or "single_shot"
            use_ahrefs: Whether to use Ahrefs SERP data
            country: Country code for SERP (default "se")
            enable_llm_profiling: Enable LLM-enhanced profiling
            output_dir: Custom output directory
            progress_callback: Async callback for progress updates
                              Signature: async def callback(progress: float, message: str)

        Returns:
            {
                "job_id": str,
                "status": str,  # "DELIVERED", "BLOCKED", "ABORTED"
                "article": str,
                "job_package": dict,
                "qc_report": dict,
                "execution_log": dict,
                "metrics": dict,
                "output_files": dict
            }
        """
        # Prepare progress updates
        if progress_callback:
            await progress_callback(0, "Initializing job...")

        # Run BACOWR in executor to avoid blocking
        loop = asyncio.get_event_loop()

        try:
            if progress_callback:
                await progress_callback(10, "Starting content generation...")

            # Run BACOWR job (blocks, so run in executor)
            result = await loop.run_in_executor(
                None,
                run_production_job,
                publisher_domain,
                target_url,
                anchor_text,
                llm_provider,
                writing_strategy,
                use_ahrefs,
                country,
                output_dir,
                enable_llm_profiling
            )

            if progress_callback:
                if result['status'] == 'DELIVERED':
                    await progress_callback(100, "Job completed successfully!")
                elif result['status'] == 'BLOCKED':
                    await progress_callback(100, "Job blocked by QC")
                else:
                    await progress_callback(100, f"Job {result['status'].lower()}")

            return result

        except Exception as e:
            if progress_callback:
                await progress_callback(100, f"Error: {str(e)}")
            raise

    def estimate_cost(
        self,
        llm_provider: str,
        writing_strategy: str,
        num_jobs: int = 1
    ) -> Dict[str, Any]:
        """
        Estimate cost for job(s).

        Args:
            llm_provider: LLM provider
            writing_strategy: Writing strategy
            num_jobs: Number of jobs

        Returns:
            {
                "estimated_cost_per_job": float,
                "estimated_total_cost": float,
                "estimated_time_seconds": float
            }
        """
        # Cost estimates (from cost_calculator.py)
        COST_ESTIMATES = {
            "anthropic": {
                "multi_stage": 0.06,
                "single_shot": 0.02
            },
            "openai": {
                "multi_stage": 0.09,
                "single_shot": 0.03
            },
            "google": {
                "multi_stage": 0.03,
                "single_shot": 0.01
            }
        }

        TIME_ESTIMATES = {
            "multi_stage": 30,  # seconds
            "single_shot": 15    # seconds
        }

        provider = llm_provider if llm_provider != "auto" else "anthropic"
        cost_per_job = COST_ESTIMATES.get(provider, {}).get(writing_strategy, 0.05)
        time_per_job = TIME_ESTIMATES.get(writing_strategy, 20)

        return {
            "estimated_cost_per_job": cost_per_job,
            "estimated_total_cost": cost_per_job * num_jobs,
            "estimated_time_seconds": time_per_job * num_jobs
        }


# Global instance
bacowr = BACOWRWrapper()
