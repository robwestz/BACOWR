#!/usr/bin/env python3
"""
BacklinkContent Engine - Next-A1 SERP-First Implementation

CLI entrypoint for generating backlink content.

Usage:
    python main.py --publisher example.com --target https://target.com/page --anchor "best solution"

Environment Variables:
    ANTHROPIC_API_KEY: Required for content generation
    SERP_API_KEY: Optional for real SERP fetching
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline.state_machine import BacklinkPipeline
from src.utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="BacklinkContent Engine - Next-A1 SERP-First Implementation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate backlink content with mock SERP data
  python main.py --publisher example-publisher.com \\
                 --target https://client.com/product \\
                 --anchor "bästa valet för produktkategori"

  # Use real SERP API
  python main.py --publisher example.com --target https://target.com \\
                 --anchor "best choice" --serp-mode api

  # Specify output directory
  python main.py --publisher example.com --target https://target.com \\
                 --anchor "check this out" --output ./output/

Environment Variables:
  ANTHROPIC_API_KEY - Required for Writer Engine
  SERP_API_KEY - Optional for real SERP fetching

More info: See README.md
        """
    )

    # Required arguments
    parser.add_argument(
        "--publisher",
        required=True,
        help="Publisher domain where content will be published (e.g., example-publisher.com)"
    )
    parser.add_argument(
        "--target",
        required=True,
        help="Target URL that will receive the backlink (e.g., https://client.com/product)"
    )
    parser.add_argument(
        "--anchor",
        required=True,
        help="Anchor text for the backlink (e.g., 'best solution for X')"
    )

    # Optional arguments
    parser.add_argument(
        "--anchor-type",
        choices=["exact", "partial", "brand", "generic"],
        help="Optional hint about anchor type"
    )
    parser.add_argument(
        "--min-words",
        type=int,
        default=900,
        help="Minimum word count for generated content (default: 900)"
    )
    parser.add_argument(
        "--language",
        help="Language override (e.g., 'sv', 'en'). If not specified, detected from target"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("./storage/output"),
        help="Output directory for generated files (default: ./storage/output)"
    )

    # SERP configuration
    parser.add_argument(
        "--serp-mode",
        choices=["mock", "api"],
        default="mock",
        help="SERP fetch mode: 'mock' for testing, 'api' for real data (default: mock)"
    )
    parser.add_argument(
        "--serp-api-key",
        help="SERP API key (can also use SERP_API_KEY env var)"
    )

    # Writer configuration
    parser.add_argument(
        "--writer-api-key",
        help="Anthropic API key (can also use ANTHROPIC_API_KEY env var)"
    )
    parser.add_argument(
        "--writer-model",
        default="claude-sonnet-4-5-20250929",
        help="Claude model to use (default: claude-sonnet-4-5-20250929)"
    )

    # Logging
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--json-logs",
        action="store_true",
        help="Output logs in JSON format"
    )

    args = parser.parse_args()

    # Configure logging
    configure_logging(level=args.log_level, json_output=args.json_logs)

    logger.info("BacklinkContent Engine starting")
    logger.info(
        "Input parameters",
        publisher=args.publisher,
        target=args.target[:50] + "..." if len(args.target) > 50 else args.target,
        anchor=args.anchor[:30] + "..." if len(args.anchor) > 30 else args.anchor,
        serp_mode=args.serp_mode
    )

    # Initialize pipeline
    try:
        pipeline = BacklinkPipeline(
            serp_mode=args.serp_mode,
            serp_api_key=args.serp_api_key,
            writer_api_key=args.writer_api_key,
            writer_model=args.writer_model
        )
    except Exception as e:
        logger.error("Failed to initialize pipeline", error=str(e), exc_info=True)
        print(f"\n❌ ERROR: Failed to initialize pipeline: {e}")
        print("\nCheck that you have:")
        print("  - ANTHROPIC_API_KEY environment variable set")
        print("  - All dependencies installed (pip install -r requirements.txt)")
        return 1

    # Execute pipeline
    print("\n🚀 Starting pipeline execution...")
    print(f"   Publisher: {args.publisher}")
    print(f"   Target: {args.target}")
    print(f"   Anchor: {args.anchor}")
    print(f"   SERP Mode: {args.serp_mode}")
    print()

    try:
        result = pipeline.execute(
            publisher_domain=args.publisher,
            target_url=args.target,
            anchor_text=args.anchor,
            anchor_type_hint=args.anchor_type,
            min_word_count=args.min_words,
            language=args.language,
            output_dir=args.output
        )

        # Print result summary
        print("\n" + "="*80)
        if result.success:
            print("✅ SUCCESS - Pipeline completed")
            print(f"   Final State: {result.final_state.value}")
            print(f"   Job ID: {result.job_id}")

            if result.qc_report:
                print(f"   QC Status: {result.qc_report.status}")
                print(f"   QC Issues: {len(result.qc_report.issues)}")
                if result.qc_report.anchor_risk:
                    print(f"   Anchor Risk: {result.qc_report.anchor_risk}")

            if result.article_text:
                word_count = len(result.article_text.split())
                print(f"   Article Length: {word_count} words")

            print(f"\n📁 Output saved to: {args.output}/")
            print(f"   - {result.job_id}_article.md")
            print(f"   - {result.job_id}_job_package.json")
            print(f"   - {result.job_id}_extensions.json")
            print(f"   - {result.job_id}_qc_report.json")
            print(f"   - {result.job_id}_execution_log.json")

            if result.qc_report and result.qc_report.status == "needs_signoff":
                print("\n⚠️  HUMAN REVIEW REQUIRED")
                print("   This content requires human sign-off before publication.")
                if result.qc_report.recommendations:
                    print("\n   Recommendations:")
                    for rec in result.qc_report.recommendations[:3]:
                        print(f"   - {rec}")

        else:
            print("❌ FAILURE - Pipeline aborted")
            print(f"   Final State: {result.final_state.value}")
            if result.error_message:
                print(f"   Error: {result.error_message}")

        print("="*80)

        # Print execution trace
        if args.log_level == "DEBUG":
            print("\n📊 Execution Trace:")
            for log_entry in result.execution_log:
                status = "✓" if log_entry.success else "✗"
                print(f"   {status} {log_entry.from_state} → {log_entry.to_state}: {log_entry.message}")

        return 0 if result.success else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        logger.warning("Pipeline interrupted by user")
        return 130

    except Exception as e:
        print(f"\n\n❌ FATAL ERROR: {e}")
        logger.error("Pipeline execution failed", error=str(e), exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
