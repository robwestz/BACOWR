#!/usr/bin/env python3
"""
BACOWR Batch Monitor

Real-time monitoring dashboard for batch processing.

Usage:
    python batch_monitor.py --watch storage/batch_output/
    python batch_monitor.py --report batch_report_20251107_140000.json
"""

import argparse
import json
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class BatchMonitor:
    """Monitor and analyze batch processing."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)

    def get_latest_report(self) -> Optional[Path]:
        """Find most recent batch report."""
        reports = list(self.output_dir.glob('batch_report_*.json'))
        if not reports:
            return None
        return max(reports, key=lambda p: p.stat().st_mtime)

    def load_report(self, report_path: Path) -> Dict[str, Any]:
        """Load batch report from file."""
        with open(report_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def count_recent_outputs(self, since: float) -> Dict[str, int]:
        """Count outputs created since timestamp."""
        counts = {
            'articles': 0,
            'job_packages': 0,
            'qc_reports': 0,
            'execution_logs': 0
        }

        for pattern, key in [
            ('*_article.md', 'articles'),
            ('*_job_package.json', 'job_packages'),
            ('*_qc_report.json', 'qc_reports'),
            ('*_execution_log.json', 'execution_logs')
        ]:
            for path in self.output_dir.glob(pattern):
                if path.stat().st_mtime >= since:
                    counts[key] += 1

        return counts

    def display_dashboard(self, report: Dict[str, Any], show_details: bool = False):
        """Display formatted dashboard."""
        meta = report.get('batch_meta', {})
        summary = report.get('summary', {})
        results = report.get('results', [])

        # Header
        print("\n" + "=" * 70)
        print("BACOWR BATCH MONITOR")
        print("=" * 70)
        print()

        # Timing
        started = meta.get('started_at', 'Unknown')
        completed = meta.get('completed_at', 'Unknown')
        duration = meta.get('duration_seconds', 0)

        print(f"Started:    {started}")
        print(f"Completed:  {completed}")
        print(f"Duration:   {duration:.1f}s ({duration/60:.1f} minutes)")
        print()

        # Configuration
        print("Configuration:")
        print(f"  Workers:      {meta.get('max_workers', 1)}")
        rate_limit = meta.get('rate_limit')
        print(f"  Rate limit:   {rate_limit if rate_limit else 'None'}")
        print()

        # Summary stats
        total = summary.get('total', 0)
        delivered = summary.get('delivered', 0)
        blocked = summary.get('blocked', 0)
        aborted = summary.get('aborted', 0)

        success_rate = (delivered / total * 100) if total > 0 else 0

        print("Results:")
        print(f"  Total:        {total}")
        print(f"  ✓ Delivered:  {delivered} ({success_rate:.1f}%)")
        if blocked > 0:
            print(f"  ⚠ Blocked:    {blocked}")
        if aborted > 0:
            print(f"  ✗ Aborted:    {aborted}")
        print()

        # Provider breakdown
        provider_counts = {}
        provider_durations = {}

        for r in results:
            if 'metrics' in r and 'generation' in r['metrics']:
                provider = r['metrics']['generation'].get('provider', 'unknown')
                duration = r['metrics']['generation'].get('duration_seconds', 0)

                provider_counts[provider] = provider_counts.get(provider, 0) + 1
                if provider not in provider_durations:
                    provider_durations[provider] = []
                provider_durations[provider].append(duration)

        if provider_counts:
            print("LLM Provider Usage:")
            for provider in sorted(provider_counts.keys()):
                count = provider_counts[provider]
                durations = provider_durations[provider]
                avg_duration = sum(durations) / len(durations) if durations else 0
                print(f"  {provider}: {count} jobs (avg {avg_duration:.1f}s)")
            print()

        # Strategy breakdown
        strategy_counts = {}
        for r in results:
            if 'job_config' in r:
                strategy = r['job_config'].get('writing_strategy', 'unknown')
                strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        if strategy_counts:
            print("Writing Strategy:")
            for strategy, count in sorted(strategy_counts.items()):
                print(f"  {strategy}: {count} jobs")
            print()

        # Performance metrics
        if results:
            durations = [r.get('duration', 0) for r in results if r.get('status') == 'DELIVERED']
            if durations:
                avg_duration = sum(durations) / len(durations)
                min_duration = min(durations)
                max_duration = max(durations)

                print("Performance:")
                print(f"  Avg time:     {avg_duration:.1f}s")
                print(f"  Min time:     {min_duration:.1f}s")
                print(f"  Max time:     {max_duration:.1f}s")
                print()

        # Errors
        errors = [r for r in results if r.get('status') == 'ABORTED']
        if errors:
            print(f"Errors ({len(errors)}):")
            for r in errors[:5]:
                batch_id = r.get('batch_id', '?')
                error = r.get('error', 'Unknown')
                print(f"  [{batch_id}] {error}")
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more")
            print()

        # Detailed results
        if show_details:
            print("=" * 70)
            print("DETAILED RESULTS")
            print("=" * 70)
            print()

            for r in results:
                batch_id = r.get('batch_id', '?')
                status = r.get('status', 'UNKNOWN')
                duration = r.get('duration', 0)

                status_emoji = "✓" if status == 'DELIVERED' else ("⚠" if status == 'BLOCKED' else "✗")

                print(f"[{batch_id}] {status_emoji} {status} ({duration:.1f}s)")

                if 'job_config' in r:
                    config = r['job_config']
                    print(f"      Publisher: {config.get('publisher_domain', 'N/A')}")
                    print(f"      Target:    {config.get('target_url', 'N/A')}")
                    print(f"      Anchor:    {config.get('anchor_text', 'N/A')}")

                if 'job_id' in r:
                    print(f"      Job ID:    {r['job_id']}")

                if status == 'DELIVERED' and 'qc_report' in r:
                    qc = r['qc_report']
                    qc_status = qc.get('status', 'N/A')
                    issues = len(qc.get('issues', []))
                    print(f"      QC:        {qc_status} ({issues} issues)")

                if status == 'ABORTED' and 'error' in r:
                    print(f"      Error:     {r['error']}")

                print()

        print("=" * 70)

    def watch_batch(self, interval: int = 10):
        """Watch batch processing in real-time."""
        print("Watching for batch activity...")
        print(f"Output directory: {self.output_dir}")
        print("Press Ctrl+C to stop")
        print()

        last_report = None
        last_check = time.time()

        try:
            while True:
                latest = self.get_latest_report()

                if latest and (not last_report or latest != last_report):
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] New report detected: {latest.name}")
                    report = self.load_report(latest)
                    self.display_dashboard(report)
                    last_report = latest
                    last_check = time.time()
                else:
                    # Show activity since last check
                    now = time.time()
                    counts = self.count_recent_outputs(last_check)
                    total = sum(counts.values())

                    if total > 0:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] Activity: {counts['articles']} articles, {counts['job_packages']} jobs")

                    last_check = now

                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\nMonitoring stopped")


def main():
    parser = argparse.ArgumentParser(
        description='BACOWR Batch Monitor - Real-time monitoring for batch jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Watch for batch activity (live monitoring)
  python batch_monitor.py --watch storage/batch_output/

  # Display report for specific batch
  python batch_monitor.py --report storage/batch_output/batch_report_20251107_140000.json

  # Show detailed results
  python batch_monitor.py --report report.json --details
        '''
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--watch',
        metavar='DIR',
        help='Watch directory for batch activity (live monitoring)'
    )
    group.add_argument(
        '--report',
        metavar='FILE',
        help='Display specific batch report'
    )

    parser.add_argument(
        '--details',
        action='store_true',
        help='Show detailed per-job results'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=10,
        help='Watch interval in seconds (default: 10)'
    )

    args = parser.parse_args()

    if args.watch:
        # Live monitoring mode
        output_dir = Path(args.watch)
        if not output_dir.exists():
            print(f"ERROR: Directory not found: {output_dir}")
            sys.exit(1)

        monitor = BatchMonitor(str(output_dir))
        monitor.watch_batch(interval=args.interval)

    else:
        # Single report mode
        report_path = Path(args.report)
        if not report_path.exists():
            print(f"ERROR: Report file not found: {report_path}")
            sys.exit(1)

        output_dir = report_path.parent
        monitor = BatchMonitor(str(output_dir))

        report = monitor.load_report(report_path)
        monitor.display_dashboard(report, show_details=args.details)


if __name__ == '__main__':
    main()
