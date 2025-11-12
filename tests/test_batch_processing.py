#!/usr/bin/env python3
"""
Tests for Batch Processing

Comprehensive test suite for batch job processing including:
- BatchRunner initialization and configuration
- CSV/JSON input parsing
- Batch execution workflow
- Rate limiting
- Progress tracking
- Batch reporting

Per BUILDER_PROMPT.md STEG 11
"""

import pytest
import sys
import csv
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from batch_runner import BatchRunner


class TestBatchRunnerInitialization:
    """Test suite for BatchRunner initialization."""

    def test_initialization_defaults(self):
        """Test default initialization."""
        runner = BatchRunner()

        assert runner.max_workers == 1
        assert runner.rate_limit_per_minute is None
        assert runner.enable_recovery is True
        assert runner.output_dir.exists()

    def test_initialization_with_options(self):
        """Test initialization with custom options."""
        temp_dir = tempfile.mkdtemp()
        runner = BatchRunner(
            max_workers=3,
            rate_limit_per_minute=10,
            output_dir=temp_dir,
            enable_recovery=False
        )

        assert runner.max_workers == 3
        assert runner.rate_limit_per_minute == 10
        assert runner.enable_recovery is False
        assert str(runner.output_dir) == temp_dir

    def test_output_directory_creation(self):
        """Test that output directory is created."""
        temp_dir = Path(tempfile.mkdtemp()) / 'new_batch_output'
        runner = BatchRunner(output_dir=str(temp_dir))

        assert temp_dir.exists()
        assert temp_dir.is_dir()


class TestCSVJobLoading:
    """Test suite for CSV job loading."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = BatchRunner()
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_load_jobs_from_csv_basic(self):
        """Test loading basic jobs from CSV."""
        csv_file = self.temp_dir / 'jobs.csv'
        csv_file.write_text(
            'publisher,target,anchor\n'
            'test.com,https://example.com,test link\n'
            'test2.com,https://example2.com,another link\n',
            encoding='utf-8'
        )

        jobs = self.runner.load_jobs_from_csv(str(csv_file))

        assert len(jobs) == 2
        assert jobs[0]['publisher_domain'] == 'test.com'
        assert jobs[0]['target_url'] == 'https://example.com'
        assert jobs[0]['anchor_text'] == 'test link'

    def test_load_jobs_from_csv_with_optional_fields(self):
        """Test loading jobs with optional fields."""
        csv_file = self.temp_dir / 'jobs.csv'
        csv_file.write_text(
            'publisher,target,anchor,llm_provider,strategy,country\n'
            'test.com,https://example.com,test,anthropic,multi_stage,us\n',
            encoding='utf-8'
        )

        jobs = self.runner.load_jobs_from_csv(str(csv_file))

        assert len(jobs) == 1
        assert jobs[0]['llm_provider'] == 'anthropic'
        assert jobs[0]['writing_strategy'] == 'multi_stage'  # Note: writing_strategy not strategy
        assert jobs[0]['country'] == 'us'

    def test_load_jobs_from_csv_missing_required_fields(self):
        """Test handling of missing required fields."""
        csv_file = self.temp_dir / 'jobs.csv'
        csv_file.write_text(
            'publisher,target\n'
            'test.com,https://example.com\n',  # Missing anchor
            encoding='utf-8'
        )

        jobs = self.runner.load_jobs_from_csv(str(csv_file))

        # Should skip rows with missing required fields
        assert len(jobs) == 0

    def test_load_jobs_from_csv_empty_file(self):
        """Test loading from empty CSV."""
        csv_file = self.temp_dir / 'empty.csv'
        csv_file.write_text('publisher,target,anchor\n', encoding='utf-8')

        jobs = self.runner.load_jobs_from_csv(str(csv_file))

        assert len(jobs) == 0

    def test_load_jobs_from_csv_special_characters(self):
        """Test loading jobs with special characters."""
        csv_file = self.temp_dir / 'jobs.csv'
        csv_file.write_text(
            'publisher,target,anchor\n'
            'test.com,https://example.com,"anchor & special <chars>"\n',
            encoding='utf-8'
        )

        jobs = self.runner.load_jobs_from_csv(str(csv_file))

        assert len(jobs) == 1
        assert 'anchor & special <chars>' in jobs[0]['anchor_text']


class TestJSONJobLoading:
    """Test suite for JSON job loading."""

    def setup_method(self):
        """Setup test fixtures."""
        self.runner = BatchRunner()
        self.temp_dir = Path(tempfile.mkdtemp())

    def test_load_jobs_from_json_basic(self):
        """Test loading jobs from JSON."""
        json_file = self.temp_dir / 'jobs.json'
        jobs_data = {
            'jobs': [
                {
                    'publisher': 'test.com',
                    'target': 'https://example.com',
                    'anchor': 'test link'
                },
                {
                    'publisher': 'test2.com',
                    'target': 'https://example2.com',
                    'anchor': 'another link'
                }
            ]
        }
        json_file.write_text(json.dumps(jobs_data), encoding='utf-8')

        jobs = self.runner.load_jobs_from_json(str(json_file))

        assert len(jobs) == 2
        assert jobs[0]['publisher_domain'] == 'test.com'

    def test_load_jobs_from_json_with_options(self):
        """Test loading JSON jobs with all options."""
        json_file = self.temp_dir / 'jobs.json'
        jobs_data = {
            'jobs': [
                {
                    'publisher': 'test.com',
                    'target': 'https://example.com',
                    'anchor': 'test',
                    'llm_provider': 'openai',
                    'strategy': 'single_shot',
                    'country': 'uk',
                    'use_ahrefs': False
                }
            ]
        }
        json_file.write_text(json.dumps(jobs_data), encoding='utf-8')

        jobs = self.runner.load_jobs_from_json(str(json_file))

        assert jobs[0]['llm_provider'] == 'openai'
        assert jobs[0]['writing_strategy'] == 'single_shot'
        assert jobs[0]['country'] == 'uk'

    def test_load_jobs_from_json_empty(self):
        """Test loading empty JSON array."""
        json_file = self.temp_dir / 'jobs.json'
        json_file.write_text('{"jobs": []}', encoding='utf-8')

        jobs = self.runner.load_jobs_from_json(str(json_file))

        assert len(jobs) == 0


class TestBatchExecution:
    """Test suite for batch execution."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.runner = BatchRunner(output_dir=str(self.temp_dir))

    def test_run_batch_mock_mode_single_job(self):
        """Test running single batch job in mock mode."""
        jobs = [
            {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test link',
                'mock': True
            }
        ]

        result = self.runner.run_batch(jobs)

        # run_batch returns a dict with results
        assert isinstance(result, dict)
        assert 'total' in result
        assert 'results' in result
        assert result['total'] == 1

    def test_run_batch_returns_proper_structure(self):
        """Test that batch results have proper structure."""
        jobs = [
            {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'test',
                'mock': True
            }
        ]

        result = self.runner.run_batch(jobs)

        # Check expected keys
        assert 'total' in result
        assert 'completed' in result
        assert 'results' in result
        assert isinstance(result['results'], list)

    def test_run_batch_empty_jobs_list(self):
        """Test running batch with empty jobs list."""
        result = self.runner.run_batch([])

        assert result['total'] == 0
        assert len(result['results']) == 0


class TestRateLimiting:
    """Test suite for rate limiting."""

    def test_rate_limiter_initialized_correctly(self):
        """Test that rate limiter is initialized."""
        runner = BatchRunner(rate_limit_per_minute=10)

        assert runner.rate_limit_per_minute == 10
        assert hasattr(runner, 'call_timestamps')

    def test_rate_limiter_disabled_when_none(self):
        """Test that rate limiter is disabled when None."""
        runner = BatchRunner(rate_limit_per_minute=None)

        # Should not wait
        start = datetime.now()
        runner._wait_for_rate_limit()
        end = datetime.now()

        # Should be instant (< 1 second)
        assert (end - start).total_seconds() < 1


def log(message, level="INFO"):
    """Simple logger for standalone execution."""
    print(f"[{level}] {message}", flush=True)


def run_standalone_tests():
    """
    Run tests in standalone mode (without pytest).
    For backwards compatibility with existing workflow.
    """
    log("BACOWR Batch Processing Tests")
    log("Per BUILDER_PROMPT.md STEG 11\n")
    log("=" * 60)

    try:
        # Test initialization
        log("\n🔍 Testing BatchRunner initialization...")
        runner = BatchRunner()
        log(f"✅ BatchRunner initialized")
        log(f"   Max workers: {runner.max_workers}")
        log(f"   Output dir: {runner.output_dir}")

        # Test CSV loading
        log("\n🔍 Testing CSV job loading...")
        temp_dir = Path(tempfile.mkdtemp())
        csv_file = temp_dir / 'test.csv'
        csv_file.write_text(
            'publisher,target,anchor\n'
            'test.com,https://example.com,test link\n',
            encoding='utf-8'
        )
        jobs = runner.load_jobs_from_csv(str(csv_file))
        log(f"✅ Loaded {len(jobs)} jobs from CSV")

        # Test JSON loading
        log("\n🔍 Testing JSON job loading...")
        json_file = temp_dir / 'test.json'
        json_data = {
            'jobs': [
                {
                    'publisher': 'test.com',
                    'target': 'https://example.com',
                    'anchor': 'test'
                }
            ]
        }
        json_file.write_text(json.dumps(json_data), encoding='utf-8')
        jobs = runner.load_jobs_from_json(str(json_file))
        log(f"✅ Loaded {len(jobs)} jobs from JSON")

        # Test batch execution
        log("\n🔍 Testing batch execution...")
        jobs[0]['mock'] = True  # Run in mock mode
        result = runner.run_batch(jobs)
        log(f"✅ Batch execution completed")
        log(f"   Total: {result['total']}")
        log(f"   Completed: {result['completed']}")

        log("\n✅ All standalone tests passed!")
        log("=" * 60)
        return True

    except Exception as e:
        log(f"❌ Test failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        log("=" * 60)
        return False


if __name__ == "__main__":
    log("=" * 60)
    success = run_standalone_tests()

    if success:
        log("✅ TESTS PASSED", "SUCCESS")
        sys.exit(0)
    else:
        log("❌ TESTS FAILED", "ERROR")
        sys.exit(1)
