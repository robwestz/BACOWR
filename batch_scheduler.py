#!/usr/bin/env python3
"""
BACOWR Batch Scheduler

Schedule and manage batch jobs over time.

Features:
- Schedule batches for specific times
- Split large batches into chunks
- Distribute load across time periods
- Respect API rate limits

Usage:
    # Schedule batch for tonight at 23:00
    python batch_scheduler.py --input large_batch.csv --time 23:00

    # Split into chunks of 10 jobs, 5 minute intervals
    python batch_scheduler.py --input large_batch.csv --chunk-size 10 --interval 5
"""

import argparse
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json
import csv


class BatchScheduler:
    """Schedule and manage batch processing."""

    def __init__(self):
        self.scheduled_batches = []

    def split_batch(
        self,
        input_file: Path,
        chunk_size: int,
        output_dir: Path
    ) -> List[Path]:
        """
        Split large batch file into smaller chunks.

        Args:
            input_file: Original batch file (CSV or JSON)
            chunk_size: Jobs per chunk
            output_dir: Where to save chunk files

        Returns:
            List of chunk file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load all jobs
        if input_file.suffix.lower() == '.csv':
            jobs = self._load_csv(input_file)
        elif input_file.suffix.lower() == '.json':
            jobs = self._load_json(input_file)
        else:
            raise ValueError(f"Unsupported file format: {input_file.suffix}")

        # Split into chunks
        chunks = []
        for i in range(0, len(jobs), chunk_size):
            chunk = jobs[i:i + chunk_size]
            chunks.append(chunk)

        # Save chunks
        chunk_files = []
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for i, chunk in enumerate(chunks, 1):
            if input_file.suffix.lower() == '.csv':
                chunk_file = output_dir / f"chunk_{timestamp}_{i:03d}.csv"
                self._save_csv(chunk, chunk_file)
            else:
                chunk_file = output_dir / f"chunk_{timestamp}_{i:03d}.json"
                self._save_json(chunk, chunk_file)

            chunk_files.append(chunk_file)

        print(f"Split {len(jobs)} jobs into {len(chunks)} chunks of {chunk_size}")
        for i, cf in enumerate(chunk_files, 1):
            print(f"  Chunk {i}: {cf.name}")

        return chunk_files

    def _load_csv(self, csv_path: Path) -> List[Dict[str, Any]]:
        """Load jobs from CSV."""
        jobs = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                jobs.append(dict(row))
        return jobs

    def _load_json(self, json_path: Path) -> List[Dict[str, Any]]:
        """Load jobs from JSON."""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data.get('jobs', [])

    def _save_csv(self, jobs: List[Dict[str, Any]], output_path: Path):
        """Save jobs to CSV."""
        if not jobs:
            return

        fieldnames = list(jobs[0].keys())
        with open(output_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(jobs)

    def _save_json(self, jobs: List[Dict[str, Any]], output_path: Path):
        """Save jobs to JSON."""
        data = {'jobs': jobs}
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def calculate_schedule(
        self,
        num_chunks: int,
        start_time: datetime,
        interval_minutes: int
    ) -> List[datetime]:
        """Calculate schedule times for chunks."""
        schedule = []
        current = start_time

        for i in range(num_chunks):
            schedule.append(current)
            current += timedelta(minutes=interval_minutes)

        return schedule

    def run_scheduled_batch(
        self,
        chunk_files: List[Path],
        schedule: List[datetime],
        parallel: int = 1,
        rate_limit: int = None,
        output_dir: str = None
    ):
        """
        Run chunks according to schedule.

        Args:
            chunk_files: List of chunk files to process
            schedule: List of scheduled times (one per chunk)
            parallel: Workers per chunk
            rate_limit: Rate limit per chunk
            output_dir: Output directory
        """
        print("\n" + "=" * 70)
        print("BATCH SCHEDULE")
        print("=" * 70)
        print()

        for i, (chunk_file, scheduled_time) in enumerate(zip(chunk_files, schedule), 1):
            print(f"Chunk {i}/{len(chunk_files)}: {chunk_file.name}")
            print(f"  Scheduled: {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}")

        print()
        print("=" * 70)
        print()

        for i, (chunk_file, scheduled_time) in enumerate(zip(chunk_files, schedule), 1):
            # Wait until scheduled time
            now = datetime.now()
            if now < scheduled_time:
                wait_seconds = (scheduled_time - now).total_seconds()
                print(f"\n[{now.strftime('%H:%M:%S')}] Waiting {wait_seconds:.0f}s until next chunk...")
                time.sleep(wait_seconds)

            # Run chunk
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Starting chunk {i}/{len(chunk_files)}: {chunk_file.name}")

            cmd = [
                'python', 'batch_runner.py',
                '--input', str(chunk_file),
                '--parallel', str(parallel)
            ]

            if rate_limit:
                cmd.extend(['--rate-limit', str(rate_limit)])

            if output_dir:
                cmd.extend(['--output', output_dir])

            try:
                result = subprocess.run(cmd, check=False)
                if result.returncode == 0:
                    print(f"✓ Chunk {i} completed successfully")
                elif result.returncode == 2:
                    print(f"⚠ Chunk {i} completed with some blocked jobs")
                else:
                    print(f"✗ Chunk {i} failed")
            except Exception as e:
                print(f"✗ Chunk {i} error: {e}")

        print("\n" + "=" * 70)
        print("ALL CHUNKS COMPLETED")
        print("=" * 70)


def parse_time(time_str: str) -> datetime:
    """Parse time string like '23:00' or '14:30' to datetime today."""
    try:
        hour, minute = map(int, time_str.split(':'))
        now = datetime.now()
        scheduled = datetime(now.year, now.month, now.day, hour, minute)

        # If time has passed today, schedule for tomorrow
        if scheduled < now:
            scheduled += timedelta(days=1)

        return scheduled
    except:
        raise ValueError(f"Invalid time format: {time_str}. Use HH:MM format (e.g., '23:00')")


def main():
    parser = argparse.ArgumentParser(
        description='BACOWR Batch Scheduler - Schedule and manage batch jobs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Split large batch into chunks of 10 jobs
  python batch_scheduler.py --input large_batch.csv --chunk-size 10 --split-only

  # Schedule batch for tonight at 23:00
  python batch_scheduler.py --input batch.csv --time 23:00

  # Split and schedule with 5 minute intervals between chunks
  python batch_scheduler.py --input large_batch.csv --chunk-size 10 --interval 5

  # Split, schedule for specific time, with rate limiting
  python batch_scheduler.py --input large_batch.csv \
    --chunk-size 10 --time 23:00 --interval 15 --rate-limit 10
        '''
    )

    parser.add_argument(
        '--input',
        required=True,
        help='Input batch file (CSV or JSON)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=10,
        help='Jobs per chunk (default: 10)'
    )
    parser.add_argument(
        '--time',
        help='Start time (HH:MM format, e.g., 23:00)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Minutes between chunks (default: 5)'
    )
    parser.add_argument(
        '--parallel',
        type=int,
        default=1,
        help='Parallel workers per chunk (default: 1)'
    )
    parser.add_argument(
        '--rate-limit',
        type=int,
        help='Max API calls per minute per chunk'
    )
    parser.add_argument(
        '--output',
        help='Output directory for results'
    )
    parser.add_argument(
        '--split-only',
        action='store_true',
        help='Only split into chunks, do not run'
    )

    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(1)

    # Initialize scheduler
    scheduler = BatchScheduler()

    # Split batch
    chunks_dir = Path('storage/batch_chunks')
    print(f"Splitting batch file: {input_path}")
    chunk_files = scheduler.split_batch(input_path, args.chunk_size, chunks_dir)

    if args.split_only:
        print("\nChunks created. Use batch_runner.py to process them individually.")
        sys.exit(0)

    # Calculate schedule
    if args.time:
        start_time = parse_time(args.time)
    else:
        start_time = datetime.now()

    schedule = scheduler.calculate_schedule(
        len(chunk_files),
        start_time,
        args.interval
    )

    # Confirm with user
    print("\n" + "=" * 70)
    print("SCHEDULE CONFIRMATION")
    print("=" * 70)
    print()
    print(f"Total jobs:     {len(chunk_files) * args.chunk_size}")
    print(f"Chunks:         {len(chunk_files)}")
    print(f"Jobs per chunk: {args.chunk_size}")
    print(f"Start time:     {schedule[0].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"End time:       {schedule[-1].strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total duration: ~{(schedule[-1] - schedule[0]).total_seconds() / 60:.0f} minutes")
    print()

    response = input("Proceed with scheduled batch? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled")
        sys.exit(0)

    # Run scheduled batch
    try:
        scheduler.run_scheduled_batch(
            chunk_files,
            schedule,
            parallel=args.parallel,
            rate_limit=args.rate_limit,
            output_dir=args.output
        )
    except KeyboardInterrupt:
        print("\n\nScheduled batch cancelled by user")
        sys.exit(130)


if __name__ == '__main__':
    main()
