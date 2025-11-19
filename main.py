#!/usr/bin/env python3
"""
BACOWR BacklinkContent Engine CLI
Per NEXT-A1-ENGINE-ADDENDUM.md § 6

Usage:
    python main.py --publisher domain.com --target URL --anchor "text"
    python main.py --publisher example.com --target https://client.com --anchor "best choice" --mock

Example:
    python main.py \\
        --publisher example-publisher.com \\
        --target https://client.com/product-x \\
        --anchor "bästa valet för [tema]" \\
        --mock
"""

import argparse
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.api import run_backlink_job


def main():
    parser = argparse.ArgumentParser(
        description="BACOWR - BacklinkContent Engine (Next-A1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run in mock mode (no external APIs)
  python main.py --publisher example.com --target https://client.com --anchor "best choice" --mock

  # Specify output directory
  python main.py --publisher test.com --target https://example.com --anchor "test" --output ./my_output/

  # Real mode (requires implementation)
  python main.py --publisher real.com --target https://target.com --anchor "anchor"
"""
    )

    parser.add_argument(
        '--publisher',
        required=True,
        help='Publisher domain where content will be published'
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

    parser.add_argument(
        '--output',
        default='./storage/output/',
        help='Output directory for generated files (default: ./storage/output/)'
    )

    parser.add_argument(
        '--mock',
        action='store_true',
        help='Run in mock mode (no external API calls)'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Print header
    print("=" * 70)
    print("BACOWR - BacklinkContent Engine (Next-A1)")
    print("=" * 70)
    print()
    print(f"Publisher:  {args.publisher}")
    print(f"Target:     {args.target}")
    print(f"Anchor:     {args.anchor}")
    print(f"Mode:       {'MOCK' if args.mock else 'REAL'}")
    print(f"Output:     {args.output}")
    print()
    print("-" * 70)
    print()

    try:
        # Run the job
        result = run_backlink_job(
            publisher_domain=args.publisher,
            target_url=args.target,
            anchor_text=args.anchor,
            mock=args.mock,
            output_dir=args.output
        )

        # Print results
        print(f"Job ID: {result['job_id']}")
        print(f"Status: {result['status']}")
        print()

        if result['status'] == 'DELIVERED':
            print("✅ Job completed successfully!")
            print()

            # QC summary
            qc = result.get('qc_report', {})
            print("QC Report:")
            print(f"  Status: {qc.get('status')}")
            print(f"  Issues: {len(qc.get('issues', []))}")
            print(f"  AutoFix: {'Yes' if qc.get('autofix_done') else 'No'}")
            print(f"  Human Signoff Required: {'Yes' if qc.get('human_signoff_required') else 'No'}")
            print()

            # Output files
            if 'output_files' in result:
                print("Output Files:")
                for file_type, file_path in result['output_files'].items():
                    print(f"  - {file_type}: {file_path}")
                print()

            # Article preview
            if args.verbose and 'article' in result:
                print("Article Preview (first 500 chars):")
                print("-" * 70)
                print(result['article'][:500])
                print("...")
                print("-" * 70)
                print()

        elif result['status'] == 'BLOCKED':
            print("⚠️  Job blocked by QC")
            print()
            print(f"Reason: {result.get('reason', 'Unknown')}")
            print()

            qc = result.get('qc_report', {})
            if qc:
                print("QC Issues:")
                for issue in qc.get('issues', []):
                    print(f"  - [{issue['severity']}] {issue['message']}")
                print()

        elif result['status'] == 'ABORTED':
            print("❌ Job aborted")
            print()
            print(f"Reason: {result.get('reason', 'Unknown')}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            print()

        # Execution log summary
        if args.verbose and 'execution_log' in result:
            exec_log = result['execution_log']
            print("Execution Log Summary:")
            print(f"  Transitions: {exec_log.get('total_transitions', 0)}")
            print(f"  RESCUE count: {exec_log.get('rescue_count', 0)}")
            print()

        # Exit code
        sys.exit(0 if result['status'] == 'DELIVERED' else 1)

    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
