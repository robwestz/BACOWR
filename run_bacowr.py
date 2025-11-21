#!/usr/bin/env python3
"""
BACOWR - Central Entry Point
BacklinkContent Engine - Next-A1 SERP-First Implementation

This is the unified entry point for running BACOWR in different modes.
Consolidates functionality from main.py, production_main.py, quickstart.py, and interactive_demo.py.

Usage:
    python run_bacowr.py --mode dev     # Development mode (mock data)
    python run_bacowr.py --mode prod    # Production mode (with LLM)
    python run_bacowr.py --mode demo    # Interactive demo

Environment Variables (from .env):
    ANTHROPIC_API_KEY: Required for production mode
    OPENAI_API_KEY: Optional LLM provider
    GOOGLE_API_KEY: Optional LLM provider
    AHREFS_API_KEY: Optional for real SERP data
"""

import argparse
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
    print(f"✓ Loaded environment from {env_path}")
else:
    print(f"⚠ No .env file found at {env_path}")
    print("  Using system environment variables only")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))


def run_dev_mode(args):
    """Run in development mode with mock data."""
    print("\n" + "=" * 70)
    print("BACOWR - DEVELOPMENT MODE (Mock)")
    print("=" * 70)
    print()
    
    # Import and run mock pipeline
    from src.pipeline.state_machine import BacklinkPipeline
    from src.utils.logger import configure_logging, get_logger
    
    configure_logging(
        level=args.log_level,
        json_output=args.json_logs
    )
    
    logger = get_logger(__name__)
    
    try:
        # Create pipeline
        pipeline = BacklinkPipeline(
            serp_mode="mock"
        )
        
        # Run pipeline
        from pathlib import Path
        result = pipeline.execute(
            publisher_domain=args.publisher,
            target_url=args.target,
            anchor_text=args.anchor,
            output_dir=Path(args.output)
        )
        
        print("\n" + "=" * 70)
        print("RESULT")
        print("=" * 70)
        print(f"Job ID: {result.get('job_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Output Directory: {args.output}")
        print("=" * 70 + "\n")
        
        if result.get('status') == 'DELIVERED':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.log_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_prod_mode(args):
    """Run in production mode with real LLM."""
    print("\n" + "=" * 70)
    print("BACOWR - PRODUCTION MODE")
    print("=" * 70)
    print()
    
    # Check API keys
    api_keys = {
        'anthropic': os.getenv('ANTHROPIC_API_KEY'),
        'openai': os.getenv('OPENAI_API_KEY'),
        'google': os.getenv('GOOGLE_API_KEY')
    }
    
    available_providers = [k for k, v in api_keys.items() if v]
    
    if not available_providers:
        print("❌ ERROR: No LLM API keys found in environment")
        print("\nPlease set at least one of:")
        print("  - ANTHROPIC_API_KEY")
        print("  - OPENAI_API_KEY")
        print("  - GOOGLE_API_KEY")
        print("\nEither in .env file or as environment variables")
        sys.exit(1)
    
    print(f"✓ Available LLM providers: {', '.join(available_providers)}")
    print()
    
    # Import and run production pipeline
    from src.production_api import run_production_job
    
    try:
        result = run_production_job(
            publisher_domain=args.publisher,
            target_url=args.target,
            anchor_text=args.anchor,
            llm_provider=args.llm,
            strategy=args.strategy,
            output_dir=args.output,
            verbose=args.verbose
        )
        
        print("\n" + "=" * 70)
        print("RESULT")
        print("=" * 70)
        print(f"Job ID: {result.get('job_id', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Output Directory: {args.output}")
        print("=" * 70 + "\n")
        
        if result.get('status') == 'success':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        if args.verbose or args.log_level == 'DEBUG':
            import traceback
            traceback.print_exc()
        sys.exit(1)


def run_demo_mode(args):
    """Run interactive demo mode."""
    print("\n" + "=" * 70)
    print("BACOWR - INTERACTIVE DEMO MODE")
    print("=" * 70)
    print()
    
    # Check if quickstart or interactive_demo
    if args.demo_type == 'quickstart':
        print("Starting quickstart guide...")
        import quickstart
        quickstart.main()
    elif args.demo_type == 'interactive':
        print("Starting interactive demo...")
        import interactive_demo
        interactive_demo.main()
    else:
        print("Choose demo type:")
        print("  1. Quickstart Guide")
        print("  2. Interactive Demo")
        print()
        choice = input("Enter choice (1-2): ").strip()
        
        if choice == '1':
            import quickstart
            quickstart.main()
        elif choice == '2':
            import interactive_demo
            interactive_demo.main()
        else:
            print("Invalid choice")
            sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="BACOWR - BacklinkContent Engine (Next-A1)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Development mode with mock data
  python run_bacowr.py --mode dev \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution"

  # Production mode with real LLM
  python run_bacowr.py --mode prod \\
    --publisher example.com \\
    --target https://target.com/page \\
    --anchor "best solution" \\
    --llm anthropic

  # Interactive demo
  python run_bacowr.py --mode demo

Environment:
  Load settings from .env file or set environment variables:
  - ANTHROPIC_API_KEY (required for prod mode)
  - OPENAI_API_KEY (optional)
  - GOOGLE_API_KEY (optional)
  - AHREFS_API_KEY (optional for real SERP)
"""
    )
    
    # Mode selection (required)
    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['dev', 'prod', 'demo'],
        help='Run mode: dev (mock), prod (LLM), or demo (interactive)'
    )
    
    # Common arguments for dev and prod modes
    parser.add_argument(
        '--publisher',
        type=str,
        help='Publisher domain (required for dev/prod modes)'
    )
    
    parser.add_argument(
        '--target',
        type=str,
        help='Target URL (required for dev/prod modes)'
    )
    
    parser.add_argument(
        '--anchor',
        type=str,
        help='Anchor text (required for dev/prod modes)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='./storage/output',
        help='Output directory (default: ./storage/output)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--json-logs',
        action='store_true',
        help='Output JSON-formatted logs'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    # Production mode specific arguments
    parser.add_argument(
        '--llm',
        type=str,
        default='auto',
        choices=['auto', 'anthropic', 'openai', 'google'],
        help='LLM provider for production mode (default: auto)'
    )
    
    parser.add_argument(
        '--strategy',
        type=str,
        default='multi_stage',
        choices=['multi_stage', 'single_shot'],
        help='Writing strategy for production mode (default: multi_stage)'
    )
    
    # Demo mode specific arguments
    parser.add_argument(
        '--demo-type',
        type=str,
        choices=['quickstart', 'interactive'],
        help='Demo type: quickstart or interactive'
    )
    
    args = parser.parse_args()
    
    # Validate required arguments based on mode
    if args.mode in ['dev', 'prod']:
        if not args.publisher or not args.target or not args.anchor:
            parser.error(f"{args.mode} mode requires --publisher, --target, and --anchor")
    
    # Route to appropriate mode
    try:
        if args.mode == 'dev':
            run_dev_mode(args)
        elif args.mode == 'prod':
            run_prod_mode(args)
        elif args.mode == 'demo':
            run_demo_mode(args)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
