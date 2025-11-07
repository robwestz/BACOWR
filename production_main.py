#!/usr/bin/env python3
"""
BACOWR Production CLI

Production-ready command-line interface with:
- Multi-provider LLM support
- Ahrefs SERP integration
- Full error handling
- Progress reporting
"""

import argparse
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.production_api import run_production_job


def main():
    parser = argparse.ArgumentParser(
        description='BACOWR Production - BacklinkContent Engine',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Run with Claude (Anthropic)
  python production_main.py \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --llm anthropic

  # Run with GPT-5 (OpenAI)
  python production_main.py \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --llm openai

  # Run with Gemini (Google)
  python production_main.py \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --llm google

  # Multi-stage writing for best quality
  python production_main.py \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --strategy multi_stage

  # Quick single-shot mode
  python production_main.py \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --strategy single_shot

Environment variables required:
  ANTHROPIC_API_KEY - for Claude
  OPENAI_API_KEY - for GPT
  GOOGLE_API_KEY - for Gemini
  AHREFS_API_KEY - for SERP data (optional, falls back to mock)
        '''
    )

    # Required arguments
    parser.add_argument(
        '--publisher',
        required=True,
        help='Publisher domain (e.g., example.com)'
    )
    parser.add_argument(
        '--target',
        required=True,
        help='Target URL to link to'
    )
    parser.add_argument(
        '--anchor',
        required=True,
        help='Anchor text for the link'
    )

    # Optional arguments
    parser.add_argument(
        '--llm',
        choices=['anthropic', 'openai', 'google', 'auto'],
        default='auto',
        help='LLM provider to use (default: auto-detect)'
    )
    parser.add_argument(
        '--strategy',
        choices=['multi_stage', 'single_shot'],
        default='multi_stage',
        help='Writing strategy: multi_stage (best quality) or single_shot (faster)'
    )
    parser.add_argument(
        '--country',
        default='se',
        help='Country code for SERP data (default: se)'
    )
    parser.add_argument(
        '--no-ahrefs',
        action='store_true',
        help='Disable Ahrefs, use mock SERP data'
    )
    parser.add_argument(
        '--no-llm-profiling',
        action='store_true',
        help='Disable LLM-enhanced profiling'
    )
    parser.add_argument(
        '--output',
        help='Output directory (default: storage/output/)'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check for API keys
    print("=" * 70)
    print("BACOWR Production - BacklinkContent Engine")
    print("=" * 70)
    print()

    # Detect available providers
    available_providers = []
    if os.getenv('ANTHROPIC_API_KEY'):
        available_providers.append('anthropic (Claude)')
    if os.getenv('OPENAI_API_KEY'):
        available_providers.append('openai (GPT)')
    if os.getenv('GOOGLE_API_KEY'):
        available_providers.append('google (Gemini)')

    if not available_providers:
        print("ERROR: No LLM API keys found in environment!")
        print()
        print("Please set at least one of:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("  export OPENAI_API_KEY='your-key-here'")
        print("  export GOOGLE_API_KEY='your-key-here'")
        sys.exit(1)

    print("Available LLM providers:", ', '.join(available_providers))

    if os.getenv('AHREFS_API_KEY'):
        print("SERP source: Ahrefs API")
    else:
        print("SERP source: Mock data (set AHREFS_API_KEY for real data)")

    print()
    print("Configuration:")
    print(f"  Publisher:  {args.publisher}")
    print(f"  Target:     {args.target}")
    print(f"  Anchor:     {args.anchor}")
    print(f"  LLM:        {args.llm}")
    print(f"  Strategy:   {args.strategy}")
    print(f"  Country:    {args.country}")
    print(f"  Ahrefs:     {'disabled' if args.no_ahrefs else 'enabled'}")
    print(f"  LLM Profile: {'disabled' if args.no_llm_profiling else 'enabled'}")
    print()
    print("-" * 70)
    print()

    try:
        # Run job
        result = run_production_job(
            publisher_domain=args.publisher,
            target_url=args.target,
            anchor_text=args.anchor,
            llm_provider=args.llm if args.llm != 'auto' else None,
            writing_strategy=args.strategy,
            use_ahrefs=not args.no_ahrefs,
            country=args.country,
            output_dir=args.output,
            enable_llm_profiling=not args.no_llm_profiling
        )

        # Print results
        print()
        print("=" * 70)
        print(f"Job ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print("=" * 70)
        print()

        if result['status'] == 'DELIVERED':
            print("✓ Article generated successfully!")
            print()

            # Metrics
            if 'metrics' in result:
                metrics = result['metrics']
                if 'generation' in metrics:
                    gen = metrics['generation']
                    print("Generation metrics:")
                    print(f"  Provider:   {gen.get('provider', 'N/A')}")
                    print(f"  Model:      {gen.get('model', 'N/A')}")
                    print(f"  Stages:     {gen.get('stages_completed', 'N/A')}")
                    print(f"  Duration:   {gen.get('duration_seconds', 0):.2f}s")
                    print()

            # QC Report
            if 'qc_report' in result:
                qc = result['qc_report']
                print("QC Report:")
                print(f"  Status:     {qc.get('status', 'N/A')}")
                print(f"  Issues:     {len(qc.get('issues', []))}")
                print(f"  AutoFix:    {'Yes' if qc.get('autofix_logs') else 'No'}")
                print(f"  Signoff:    {'Required' if qc.get('human_signoff_required') else 'Not required'}")
                print()

            # Output files
            if 'output_files' in result:
                print("Output files:")
                for key, path in result['output_files'].items():
                    print(f"  {key}: {path}")
                print()

            # Show article preview
            if args.verbose and 'article' in result:
                print("-" * 70)
                print("Article preview (first 500 chars):")
                print("-" * 70)
                print(result['article'][:500])
                print("...")
                print()

        elif result['status'] == 'BLOCKED':
            print("⚠ Article generated but QC blocked delivery")
            print()
            print("Reason:", result.get('reason', 'QC validation failed'))
            print()
            print("Review QC report for details:")
            if 'output_files' in result:
                print(f"  {result['output_files'].get('qc_report', 'N/A')}")
            print()

        else:  # ABORTED
            print("✗ Job aborted")
            print()
            print("Reason:", result.get('reason', 'Unknown'))
            if 'error' in result:
                print("Error:", result['error'])
            print()

        sys.exit(0 if result['status'] == 'DELIVERED' else 1)

    except KeyboardInterrupt:
        print()
        print("Job cancelled by user")
        sys.exit(130)

    except Exception as e:
        print()
        print(f"ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
