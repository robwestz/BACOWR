#!/usr/bin/env python3
"""
BACOWR Quick Start

Interactive guide to generate your first backlink content.

Usage:
    python quickstart.py
"""

import os
import sys
import subprocess
from pathlib import Path


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)
    print()


def print_section(text):
    """Print formatted section."""
    print("\n" + "-" * 70)
    print(text)
    print("-" * 70)
    print()


def check_api_keys():
    """Check which API keys are available."""
    available = {}

    if os.getenv('ANTHROPIC_API_KEY'):
        available['anthropic'] = 'Claude (Anthropic)'

    if os.getenv('OPENAI_API_KEY'):
        available['openai'] = 'GPT (OpenAI)'

    if os.getenv('GOOGLE_API_KEY'):
        available['google'] = 'Gemini (Google)'

    return available


def get_input(prompt, default=None):
    """Get input from user with optional default."""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "

    response = input(prompt).strip()
    return response if response else default


def main():
    print_header("BACOWR Quick Start")
    print("Welcome to BACOWR - BacklinkContent Engine!")
    print()
    print("This interactive guide will help you generate your first")
    print("backlink content article.")
    print()

    # Check API keys
    print_section("Step 1: Checking API Configuration")

    available_providers = check_api_keys()

    if not available_providers:
        print("❌ No LLM API keys found!")
        print()
        print("You need at least one API key. Please set one of:")
        print("  export ANTHROPIC_API_KEY='sk-ant-...'")
        print("  export OPENAI_API_KEY='sk-proj-...'")
        print("  export GOOGLE_API_KEY='...'")
        print()
        print("Then run this script again.")
        sys.exit(1)

    print("✓ Found LLM providers:")
    for key, name in available_providers.items():
        print(f"  - {name}")
    print()

    if os.getenv('AHREFS_API_KEY'):
        print("✓ Ahrefs API key found (will use real SERP data)")
    else:
        print("ℹ No Ahrefs API key (will use mock SERP data)")
        print("  Set AHREFS_API_KEY to use real SERP data")

    # Get job parameters
    print_section("Step 2: Configure Your Content")

    print("We need three pieces of information:")
    print()

    publisher = get_input(
        "1. Publisher domain (where content will be published)",
        "aftonbladet.se"
    )

    target = get_input(
        "2. Target URL (the page you want to link to)",
        "https://sv.wikipedia.org/wiki/Artificiell_intelligens"
    )

    anchor = get_input(
        "3. Anchor text (the clickable link text)",
        "läs mer om AI"
    )

    print()
    print("Configuration:")
    print(f"  Publisher: {publisher}")
    print(f"  Target:    {target}")
    print(f"  Anchor:    {anchor}")
    print()

    # Choose provider
    print_section("Step 3: Choose LLM Provider")

    if len(available_providers) == 1:
        provider = list(available_providers.keys())[0]
        print(f"Using: {available_providers[provider]}")
    else:
        print("Available providers:")
        provider_list = list(available_providers.keys())
        for i, (key, name) in enumerate(available_providers.items(), 1):
            print(f"  {i}. {name}")
        print()

        choice = get_input("Choose provider (number or name)", "1")

        try:
            if choice.isdigit():
                provider = provider_list[int(choice) - 1]
            else:
                provider = choice
        except:
            provider = provider_list[0]

    print(f"\nUsing: {available_providers[provider]}")

    # Choose strategy
    print_section("Step 4: Choose Writing Strategy")

    print("Available strategies:")
    print()
    print("1. multi_stage (Recommended)")
    print("   - Best quality")
    print("   - 3 LLM calls (outline → content → polish)")
    print("   - ~30-60 seconds per article")
    print("   - Higher cost")
    print()
    print("2. single_shot (Fast)")
    print("   - Good quality")
    print("   - 1 LLM call")
    print("   - ~10-20 seconds per article")
    print("   - Lower cost")
    print()

    strategy_choice = get_input("Choose strategy (1 or 2)", "1")
    strategy = "multi_stage" if strategy_choice in ["1", "multi_stage"] else "single_shot"

    print(f"\nUsing: {strategy}")

    # Estimate cost
    print_section("Step 5: Cost Estimate")

    try:
        result = subprocess.run(
            [
                'python', 'cost_calculator.py',
                '--jobs', '1',
                '--provider', provider,
                '--strategy', strategy
            ],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Extract just the cost line
            for line in result.stdout.split('\n'):
                if 'Total cost:' in line or 'Cost per job:' in line:
                    print(line)
    except:
        print("Could not estimate cost (cost_calculator.py not available)")

    # Confirm
    print_section("Step 6: Ready to Generate")

    print("Summary:")
    print(f"  Publisher:  {publisher}")
    print(f"  Target:     {target}")
    print(f"  Anchor:     {anchor}")
    print(f"  Provider:   {provider}")
    print(f"  Strategy:   {strategy}")
    print()

    confirm = get_input("Generate article? (y/n)", "y")

    if confirm.lower() != 'y':
        print("\nCancelled")
        sys.exit(0)

    # Run generation
    print_section("Step 7: Generating Article")

    print("Starting generation...")
    print()

    cmd = [
        'python', 'production_main.py',
        '--publisher', publisher,
        '--target', target,
        '--anchor', anchor,
        '--llm', provider,
        '--strategy', strategy
    ]

    if not os.getenv('AHREFS_API_KEY'):
        cmd.append('--no-ahrefs')

    try:
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print_header("✓ Success!")
            print("Your article has been generated successfully!")
            print()
            print("Output files saved to: storage/output/")
            print()
            print("Next steps:")
            print("  1. Review the generated article")
            print("  2. Check the QC report for any issues")
            print("  3. Review PRODUCTION_GUIDE.md for more options")
            print("  4. Try batch processing with batch_runner.py")
            print()
        else:
            print_header("Generation Failed")
            print("Check the error messages above for details.")
            print()

    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
