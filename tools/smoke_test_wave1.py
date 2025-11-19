#!/usr/bin/env python3
"""
BACOWR Wave 1 Smoke Test

Tests the complete backend pipeline end-to-end:
- Publisher profiling
- Target profiling
- SERP research (mock mode)
- Intent analysis
- Article generation (mock mode if no API keys)
- QC validation
- Storage

This script can run WITHOUT LLM API keys using mock mode.

Usage:
    python tools/smoke_test_wave1.py

Environment variables:
    BACOWR_LLM_MODE=mock    Force mock mode (optional, auto-detected if no keys)
    ANTHROPIC_API_KEY       Use real Claude API (optional)
    OPENAI_API_KEY          Use real GPT API (optional)
    GOOGLE_API_KEY          Use real Gemini API (optional)
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.production_api import run_production_job


def print_header(title):
    """Print formatted header"""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def print_section(title):
    """Print formatted section"""
    print()
    print(f"--- {title} ---")
    print()


def check_api_keys():
    """Check which API keys are available"""
    keys = {
        'ANTHROPIC_API_KEY': bool(os.getenv('ANTHROPIC_API_KEY')),
        'OPENAI_API_KEY': bool(os.getenv('OPENAI_API_KEY')),
        'GOOGLE_API_KEY': bool(os.getenv('GOOGLE_API_KEY'))
    }

    mock_mode = os.getenv('BACOWR_LLM_MODE', '').lower() == 'mock'

    print_section("Environment Check")

    if mock_mode:
        print("✓ BACOWR_LLM_MODE=mock (explicit mock mode)")

    for key, has_key in keys.items():
        status = "✓" if has_key else "✗"
        print(f"{status} {key}: {'SET' if has_key else 'NOT SET'}")

    if not any(keys.values()) and not mock_mode:
        print("\n⚠ No LLM API keys found - will auto-enable mock mode")
        return 'mock'
    elif mock_mode:
        return 'mock'
    else:
        return 'real'


def run_test():
    """Run smoke test"""
    print_header("BACOWR WAVE 1 SMOKE TEST")

    # Check environment
    mode = check_api_keys()

    # Test inputs
    test_inputs = {
        'publisher_domain': 'konsumenternas.se',
        'target_url': 'https://sv.wikipedia.org/wiki/Artificiell_intelligens',
        'anchor_text': 'läs mer om AI'
    }

    print_section("Test Input")
    print(f"Publisher:  {test_inputs['publisher_domain']}")
    print(f"Target:     {test_inputs['target_url']}")
    print(f"Anchor:     {test_inputs['anchor_text']}")
    print(f"LLM Mode:   {mode.upper()}")

    # Run job
    print_section("Running BACOWR Pipeline")
    print("Starting job execution...")
    print()

    try:
        result = run_production_job(
            publisher_domain=test_inputs['publisher_domain'],
            target_url=test_inputs['target_url'],
            anchor_text=test_inputs['anchor_text'],
            llm_provider=None,  # Auto-detect
            writing_strategy='multi_stage',
            use_ahrefs=False,  # Use mock SERP
            country='se',
            output_dir=str(PROJECT_ROOT / 'storage' / 'smoke_test_output'),
            enable_llm_profiling=False  # Skip LLM profiling for speed
        )

        # Print results
        print_section("Results")

        job_id = result.get('job_id')
        status = result.get('status')

        print(f"Job ID:     {job_id}")
        print(f"Status:     {status}")

        if result.get('error'):
            print(f"Error:      {result['error']}")

        # Article
        article = result.get('article', '')
        if article:
            word_count = len(article.split())
            print(f"Article:    ✓ Generated ({word_count} words)")
            print()
            print("Article preview (first 300 chars):")
            print("-" * 80)
            print(article[:300] + "...")
            print("-" * 80)
        else:
            print("Article:    ✗ Not generated")

        # QC Report
        qc_report = result.get('qc_report', {})
        if qc_report:
            qc_status = qc_report.get('status', 'unknown')
            print(f"QC Status:  {qc_status}")
            if qc_report.get('issues'):
                print(f"QC Issues:  {len(qc_report['issues'])} found")
        else:
            print("QC Report:  Not available")

        # Execution log
        exec_log = result.get('execution_log', {})
        if exec_log.get('log_entries'):
            log_count = len(exec_log['log_entries'])
            final_state = exec_log.get('metadata', {}).get('final_state', 'unknown')
            print(f"Exec Log:   {log_count} entries (final state: {final_state})")

        # Metrics
        metrics = result.get('metrics', {})
        if metrics:
            duration = metrics.get('completed_at', '') and metrics.get('started_at', '')
            if duration:
                print(f"Duration:   ~{metrics.get('duration', 'N/A')} seconds")

            gen_metrics = metrics.get('generation', {})
            if gen_metrics:
                provider = gen_metrics.get('provider', 'N/A')
                model = gen_metrics.get('model', 'N/A')
                print(f"LLM Used:   {provider} / {model}")

        # Output files
        output_files = result.get('output_files', {})
        if output_files:
            print()
            print("Output files:")
            for file_type, file_path in output_files.items():
                exists = Path(file_path).exists() if file_path else False
                status = "✓" if exists else "✗"
                print(f"  {status} {file_type}: {file_path}")

        # Final verdict
        print_section("Test Verdict")

        if status == 'DELIVERED':
            print("✅ SUCCESS: Job completed successfully!")
            print()
            print("Wave 1 backend pipeline is WORKING:")
            print("  ✓ Preflight (publisher + target profiling)")
            print("  ✓ SERP research (mock mode)")
            print("  ✓ Intent analysis")
            print("  ✓ Article generation (mock mode)" if mode == 'mock' else "  ✓ Article generation (real LLM)")
            print("  ✓ QC validation")
            print("  ✓ Storage")
            return 0

        elif status == 'BLOCKED':
            print("⚠️  WARNING: Job completed but blocked by QC")
            print("    This means the pipeline works but QC found issues.")
            print("    Check QC report for details.")
            return 1

        else:
            print(f"❌ FAILURE: Job status = {status}")
            if result.get('error'):
                print(f"   Error: {result['error']}")
            return 1

    except Exception as e:
        print_section("Error")
        print(f"❌ Exception occurred: {type(e).__name__}")
        print(f"   {str(e)}")
        print()
        print("Stack trace:")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    exit_code = run_test()
    print()
    sys.exit(exit_code)
