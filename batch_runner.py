#!/usr/bin/env python3
"""
BACOWR Batch Runner

Process multiple backlink content jobs from CSV or JSON input.

Features:
- CSV/JSON input support
- Rate limiting and parallel processing
- Progress tracking and recovery
- Cost aggregation
- Detailed batch reports

Usage:
    python batch_runner.py --input jobs.csv --output batch_output/
    python batch_runner.py --input jobs.json --parallel 3 --rate-limit 10
"""

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.production_api import run_production_job


class BatchRunner:
    """Batch processing for multiple content generation jobs."""

    def __init__(
        self,
        max_workers: int = 1,
        rate_limit_per_minute: Optional[int] = None,
        output_dir: Optional[str] = None,
        enable_recovery: bool = True
    ):
        """
        Initialize batch runner.

        Args:
            max_workers: Number of parallel jobs (default: 1 for safety)
            rate_limit_per_minute: Max API calls per minute (default: None)
            output_dir: Output directory for all batch results
            enable_recovery: Save progress and allow resume
        """
        self.max_workers = max_workers
        self.rate_limit_per_minute = rate_limit_per_minute
        self.output_dir = Path(output_dir) if output_dir else Path('storage/batch_output')
        self.enable_recovery = enable_recovery

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Rate limiting state
        self.rate_limiter_lock = threading.Lock()
        self.call_timestamps = []

        # Progress tracking
        self.completed = []
        self.failed = []
        self.start_time = None

    def load_jobs_from_csv(self, csv_path: str) -> List[Dict[str, Any]]:
        """
        Load jobs from CSV file.

        Expected columns:
        - publisher (required)
        - target (required)
        - anchor (required)
        - llm_provider (optional: auto/anthropic/openai/google)
        - strategy (optional: multi_stage/single_shot)
        - country (optional: default 'se')
        - use_ahrefs (optional: true/false)
        - enable_llm_profiling (optional: true/false)
        """
        jobs = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                # Validate required fields
                if not all(k in row for k in ['publisher', 'target', 'anchor']):
                    print(f"⚠ Warning: Row {i} missing required fields, skipping")
                    continue

                # Build job config
                job = {
                    'publisher_domain': row['publisher'],
                    'target_url': row['target'],
                    'anchor_text': row['anchor'],
                    'llm_provider': row.get('llm_provider', 'auto'),
                    'writing_strategy': row.get('strategy', 'multi_stage'),
                    'country': row.get('country', 'se'),
                    'use_ahrefs': row.get('use_ahrefs', 'true').lower() == 'true',
                    'enable_llm_profiling': row.get('enable_llm_profiling', 'true').lower() == 'true',
                    'batch_id': i
                }

                jobs.append(job)

        return jobs

    def load_jobs_from_json(self, json_path: str) -> List[Dict[str, Any]]:
        """
        Load jobs from JSON file.

        Expected format:
        {
            "jobs": [
                {
                    "publisher": "example.com",
                    "target": "https://...",
                    "anchor": "text",
                    "llm_provider": "auto",  // optional
                    "strategy": "multi_stage",  // optional
                    "country": "se",  // optional
                    "use_ahrefs": true,  // optional
                    "enable_llm_profiling": true  // optional
                },
                ...
            ]
        }
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        jobs = []
        for i, job_data in enumerate(data.get('jobs', []), 1):
            # Validate required fields
            if not all(k in job_data for k in ['publisher', 'target', 'anchor']):
                print(f"⚠ Warning: Job {i} missing required fields, skipping")
                continue

            job = {
                'publisher_domain': job_data['publisher'],
                'target_url': job_data['target'],
                'anchor_text': job_data['anchor'],
                'llm_provider': job_data.get('llm_provider', 'auto'),
                'writing_strategy': job_data.get('strategy', 'multi_stage'),
                'country': job_data.get('country', 'se'),
                'use_ahrefs': job_data.get('use_ahrefs', True),
                'enable_llm_profiling': job_data.get('enable_llm_profiling', True),
                'batch_id': i
            }

            jobs.append(job)

        return jobs

    def _wait_for_rate_limit(self):
        """Enforce rate limiting if configured."""
        if not self.rate_limit_per_minute:
            return

        with self.rate_limiter_lock:
            now = time.time()

            # Remove timestamps older than 1 minute
            self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 60]

            # Check if we need to wait
            if len(self.call_timestamps) >= self.rate_limit_per_minute:
                oldest = self.call_timestamps[0]
                wait_time = 60 - (now - oldest)
                if wait_time > 0:
                    print(f"  ⏸ Rate limit reached, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    now = time.time()

            # Record this call
            self.call_timestamps.append(now)

    def _run_single_job(self, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single job with error handling."""
        batch_id = job_config.get('batch_id', '?')

        try:
            print(f"\n[{batch_id}] Starting job for {job_config['publisher_domain']}")
            print(f"      Target: {job_config['target_url']}")
            print(f"      Anchor: {job_config['anchor_text']}")

            # Wait for rate limit
            self._wait_for_rate_limit()

            # Run job
            start = time.time()
            result = run_production_job(
                publisher_domain=job_config['publisher_domain'],
                target_url=job_config['target_url'],
                anchor_text=job_config['anchor_text'],
                llm_provider=job_config['llm_provider'] if job_config['llm_provider'] != 'auto' else None,
                writing_strategy=job_config['writing_strategy'],
                use_ahrefs=job_config['use_ahrefs'],
                country=job_config['country'],
                output_dir=str(self.output_dir),
                enable_llm_profiling=job_config['enable_llm_profiling']
            )
            duration = time.time() - start

            result['batch_id'] = batch_id
            result['duration'] = duration
            result['job_config'] = job_config

            status_emoji = "✓" if result['status'] == 'DELIVERED' else ("⚠" if result['status'] == 'BLOCKED' else "✗")
            print(f"[{batch_id}] {status_emoji} {result['status']} in {duration:.1f}s")

            return result

        except Exception as e:
            print(f"[{batch_id}] ✗ ERROR: {e}")
            return {
                'batch_id': batch_id,
                'status': 'ABORTED',
                'error': str(e),
                'job_config': job_config
            }

    def run_batch(self, jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run batch of jobs.

        Returns:
            {
                'total': int,
                'completed': int,
                'delivered': int,
                'blocked': int,
                'aborted': int,
                'results': [list of job results],
                'duration': float,
                'summary_report': str
            }
        """
        self.start_time = time.time()

        print("=" * 70)
        print("BACOWR Batch Runner")
        print("=" * 70)
        print(f"\nTotal jobs: {len(jobs)}")
        print(f"Max workers: {self.max_workers}")
        if self.rate_limit_per_minute:
            print(f"Rate limit: {self.rate_limit_per_minute} calls/minute")
        print(f"Output directory: {self.output_dir}")
        print()
        print("-" * 70)

        results = []

        if self.max_workers == 1:
            # Sequential processing
            for job in jobs:
                result = self._run_single_job(job)
                results.append(result)

                if result['status'] == 'DELIVERED':
                    self.completed.append(result)
                else:
                    self.failed.append(result)
        else:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(self._run_single_job, job): job for job in jobs}

                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

                    if result['status'] == 'DELIVERED':
                        self.completed.append(result)
                    else:
                        self.failed.append(result)

        # Calculate statistics
        total_duration = time.time() - self.start_time

        delivered = sum(1 for r in results if r['status'] == 'DELIVERED')
        blocked = sum(1 for r in results if r['status'] == 'BLOCKED')
        aborted = sum(1 for r in results if r['status'] == 'ABORTED')

        # Generate summary
        summary = self._generate_summary_report(results, total_duration)

        # Save batch report
        self._save_batch_report(results, total_duration)

        return {
            'total': len(jobs),
            'completed': len(results),
            'delivered': delivered,
            'blocked': blocked,
            'aborted': aborted,
            'results': results,
            'duration': total_duration,
            'summary_report': summary
        }

    def _generate_summary_report(self, results: List[Dict[str, Any]], duration: float) -> str:
        """Generate human-readable summary report."""
        delivered = [r for r in results if r['status'] == 'DELIVERED']
        blocked = [r for r in results if r['status'] == 'BLOCKED']
        aborted = [r for r in results if r['status'] == 'ABORTED']

        # Calculate average duration for successful jobs
        avg_duration = sum(r.get('duration', 0) for r in delivered) / len(delivered) if delivered else 0

        # Calculate cost estimates (if available)
        total_cost = 0
        provider_usage = {}

        for r in results:
            if 'metrics' in r and 'generation' in r['metrics']:
                provider = r['metrics']['generation'].get('provider', 'unknown')
                provider_usage[provider] = provider_usage.get(provider, 0) + 1

        summary = f"""
{'=' * 70}
BATCH SUMMARY
{'=' * 70}

Total jobs:       {len(results)}
  ✓ Delivered:    {len(delivered)}
  ⚠ Blocked:      {len(blocked)}
  ✗ Aborted:      {len(aborted)}

Duration:         {duration:.1f}s ({duration/60:.1f} minutes)
Avg per job:      {avg_duration:.1f}s

Provider usage:
"""
        for provider, count in sorted(provider_usage.items()):
            summary += f"  {provider}: {count} jobs\n"

        if delivered:
            summary += f"\nDelivered articles saved to: {self.output_dir}\n"

        if blocked:
            summary += f"\n⚠ {len(blocked)} job(s) blocked by QC - review QC reports\n"

        if aborted:
            summary += f"\n✗ {len(aborted)} job(s) aborted with errors:\n"
            for r in aborted[:5]:  # Show first 5 errors
                summary += f"  [{r['batch_id']}] {r.get('error', 'Unknown error')}\n"
            if len(aborted) > 5:
                summary += f"  ... and {len(aborted) - 5} more\n"

        summary += "\n" + "=" * 70 + "\n"

        return summary

    def _save_batch_report(self, results: List[Dict[str, Any]], duration: float):
        """Save detailed batch report to JSON."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"batch_report_{timestamp}.json"

        report = {
            'batch_meta': {
                'started_at': datetime.utcfromtimestamp(self.start_time).isoformat(),
                'completed_at': datetime.utcnow().isoformat(),
                'duration_seconds': duration,
                'max_workers': self.max_workers,
                'rate_limit': self.rate_limit_per_minute
            },
            'summary': {
                'total': len(results),
                'delivered': sum(1 for r in results if r['status'] == 'DELIVERED'),
                'blocked': sum(1 for r in results if r['status'] == 'BLOCKED'),
                'aborted': sum(1 for r in results if r['status'] == 'ABORTED')
            },
            'results': results
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\nBatch report saved: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description='BACOWR Batch Runner - Process multiple content generation jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Process jobs from CSV (sequential)
  python batch_runner.py --input jobs.csv

  # Process jobs from JSON with 3 parallel workers
  python batch_runner.py --input jobs.json --parallel 3

  # With rate limiting (max 10 API calls per minute)
  python batch_runner.py --input jobs.csv --rate-limit 10

  # Custom output directory
  python batch_runner.py --input jobs.csv --output my_batch_output/

CSV Format:
  publisher,target,anchor,llm_provider,strategy,country
  example.com,https://target.com/page,anchor text,auto,multi_stage,se

JSON Format:
  {
    "jobs": [
      {
        "publisher": "example.com",
        "target": "https://target.com/page",
        "anchor": "anchor text",
        "llm_provider": "auto",
        "strategy": "multi_stage"
      }
    ]
  }
        '''
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Input file (CSV or JSON)'
    )
    parser.add_argument(
        '--output',
        help='Output directory (default: storage/batch_output/)'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Number of parallel workers (default: 1 for safety)'
    )
    parser.add_argument(
        '--rate-limit',
        type=int,
        help='Max API calls per minute (default: no limit)'
    )
    parser.add_argument(
        '--no-recovery',
        action='store_true',
        help='Disable progress recovery (not recommended)'
    )

    args = parser.parse_args()

    # Load jobs
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    runner = BatchRunner(
        max_workers=args.parallel,
        rate_limit_per_minute=args.rate_limit,
        output_dir=args.output,
        enable_recovery=not args.no_recovery
    )

    # Determine input format and load
    if input_path.suffix.lower() == '.csv':
        jobs = runner.load_jobs_from_csv(str(input_path))
    elif input_path.suffix.lower() == '.json':
        jobs = runner.load_jobs_from_json(str(input_path))
    else:
        print(f"ERROR: Unsupported input format: {input_path.suffix}")
        print("Supported formats: .csv, .json")
        sys.exit(1)

    if not jobs:
        print("ERROR: No valid jobs found in input file")
        sys.exit(1)

    print(f"Loaded {len(jobs)} job(s) from {input_path}")

    # Run batch
    try:
        batch_result = runner.run_batch(jobs)

        # Print summary
        print(batch_result['summary_report'])

        # Exit with appropriate code
        if batch_result['aborted'] > 0:
            sys.exit(1)
        elif batch_result['blocked'] > 0:
            sys.exit(2)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\nBatch cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
