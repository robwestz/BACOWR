#!/usr/bin/env python3
"""
BACOWR Cost Calculator

Estimate costs before running batch jobs.

Usage:
    python cost_calculator.py --input jobs.csv --provider anthropic --strategy multi_stage
    python cost_calculator.py --jobs 100 --provider openai --model gpt-4o-mini
"""

import argparse
import sys
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional


# Pricing per 1M tokens (as of Nov 2025)
PRICING = {
    'anthropic': {
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
        'claude-3-sonnet-20240229': {'input': 3.00, 'output': 15.00},
        'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00},
        'claude-3-opus-20240229': {'input': 15.00, 'output': 75.00},
    },
    'openai': {
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4o': {'input': 2.50, 'output': 10.00},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},
    },
    'google': {
        'gemini-1.5-flash': {'input': 0.075, 'output': 0.30},
        'gemini-1.5-pro': {'input': 1.25, 'output': 5.00},
        'gemini-1.0-pro': {'input': 0.50, 'output': 1.50},
    }
}

# Default models per provider
DEFAULT_MODELS = {
    'anthropic': 'claude-3-haiku-20240307',
    'openai': 'gpt-4o-mini',
    'google': 'gemini-1.5-flash'
}

# Estimated token usage per article
# Based on typical 1000-word article with profiling
TOKEN_ESTIMATES = {
    'single_shot': {
        'input': 4000,   # Job package + profiling + prompt
        'output': 1500   # Generated article ~1000 words
    },
    'multi_stage': {
        'input': 12000,  # 3 stages × 4000 tokens input
        'output': 4500   # 3 stages × 1500 tokens output
    }
}


class CostCalculator:
    """Calculate estimated costs for batch jobs."""

    def __init__(self):
        self.pricing = PRICING

    def calculate_job_cost(
        self,
        provider: str,
        model: str,
        strategy: str
    ) -> Dict[str, float]:
        """
        Calculate cost for a single job.

        Returns:
            {
                'input_tokens': int,
                'output_tokens': int,
                'input_cost': float,
                'output_cost': float,
                'total_cost': float
            }
        """
        # Get pricing
        if provider not in self.pricing:
            raise ValueError(f"Unknown provider: {provider}")

        if model not in self.pricing[provider]:
            raise ValueError(f"Unknown model: {model} for provider {provider}")

        pricing = self.pricing[provider][model]

        # Get token estimates
        if strategy not in TOKEN_ESTIMATES:
            raise ValueError(f"Unknown strategy: {strategy}")

        tokens = TOKEN_ESTIMATES[strategy]

        # Calculate costs (pricing is per 1M tokens)
        input_cost = (tokens['input'] / 1_000_000) * pricing['input']
        output_cost = (tokens['output'] / 1_000_000) * pricing['output']
        total_cost = input_cost + output_cost

        return {
            'input_tokens': tokens['input'],
            'output_tokens': tokens['output'],
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost
        }

    def calculate_batch_cost(
        self,
        num_jobs: int,
        provider: str,
        model: str,
        strategy: str
    ) -> Dict[str, float]:
        """Calculate cost for batch of jobs."""
        job_cost = self.calculate_job_cost(provider, model, strategy)

        return {
            'num_jobs': num_jobs,
            'input_tokens': job_cost['input_tokens'] * num_jobs,
            'output_tokens': job_cost['output_tokens'] * num_jobs,
            'input_cost': job_cost['input_cost'] * num_jobs,
            'output_cost': job_cost['output_cost'] * num_jobs,
            'total_cost': job_cost['total_cost'] * num_jobs,
            'cost_per_job': job_cost['total_cost']
        }

    def load_batch_file(self, file_path: Path) -> List[Dict]:
        """Load jobs from CSV or JSON."""
        if file_path.suffix.lower() == '.csv':
            with open(file_path, 'r', encoding='utf-8') as f:
                return list(csv.DictReader(f))
        elif file_path.suffix.lower() == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('jobs', [])
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

    def calculate_batch_file_cost(
        self,
        file_path: Path,
        default_provider: Optional[str] = None,
        default_strategy: Optional[str] = None
    ) -> Dict[str, float]:
        """Calculate cost for all jobs in batch file."""
        jobs = self.load_batch_file(file_path)

        # Group jobs by provider/model/strategy
        job_groups = {}

        for job in jobs:
            provider = job.get('llm_provider', default_provider or 'auto')
            if provider == 'auto':
                provider = 'anthropic'  # Default

            strategy = job.get('strategy', default_strategy or 'multi_stage')
            model = DEFAULT_MODELS.get(provider)

            key = (provider, model, strategy)
            if key not in job_groups:
                job_groups[key] = 0
            job_groups[key] += 1

        # Calculate costs per group
        total_cost = 0
        details = []

        for (provider, model, strategy), count in job_groups.items():
            batch_cost = self.calculate_batch_cost(count, provider, model, strategy)
            total_cost += batch_cost['total_cost']
            details.append({
                'provider': provider,
                'model': model,
                'strategy': strategy,
                'jobs': count,
                'cost': batch_cost['total_cost']
            })

        return {
            'total_jobs': len(jobs),
            'total_cost': total_cost,
            'details': details
        }

    def display_cost_estimate(self, estimate: Dict, show_details: bool = False):
        """Display formatted cost estimate."""
        print("\n" + "=" * 70)
        print("BACOWR COST ESTIMATE")
        print("=" * 70)
        print()

        if 'num_jobs' in estimate:
            # Single configuration
            print(f"Jobs:           {estimate['num_jobs']}")
            print(f"Cost per job:   ${estimate['cost_per_job']:.4f}")
            print()
            print(f"Total cost:     ${estimate['total_cost']:.2f}")
            print()
            print("Token usage:")
            print(f"  Input:        {estimate['input_tokens']:,} tokens")
            print(f"  Output:       {estimate['output_tokens']:,} tokens")
            print()
            print("Cost breakdown:")
            print(f"  Input cost:   ${estimate['input_cost']:.4f}")
            print(f"  Output cost:  ${estimate['output_cost']:.4f}")
        else:
            # Multiple configurations
            print(f"Total jobs:     {estimate['total_jobs']}")
            print(f"Total cost:     ${estimate['total_cost']:.2f}")
            print()

            if show_details and estimate['details']:
                print("Cost breakdown by configuration:")
                print()
                for detail in estimate['details']:
                    print(f"  {detail['provider']} / {detail['model']}")
                    print(f"    Strategy:   {detail['strategy']}")
                    print(f"    Jobs:       {detail['jobs']}")
                    print(f"    Cost:       ${detail['cost']:.2f}")
                    print()

        print("=" * 70)
        print()
        print("Note: This is an estimate based on typical usage.")
        print("Actual costs may vary based on content complexity and length.")
        print()


def main():
    parser = argparse.ArgumentParser(
        description='BACOWR Cost Calculator - Estimate batch processing costs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Estimate cost for 100 jobs with Anthropic multi-stage
  python cost_calculator.py --jobs 100 --provider anthropic --strategy multi_stage

  # Estimate cost for batch file
  python cost_calculator.py --input jobs.csv

  # Estimate with specific model
  python cost_calculator.py --jobs 50 --provider openai --model gpt-4o

  # Show detailed breakdown
  python cost_calculator.py --input jobs.csv --details
        '''
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--jobs',
        type=int,
        help='Number of jobs to estimate'
    )
    group.add_argument(
        '--input',
        help='Batch input file (CSV or JSON)'
    )

    parser.add_argument(
        '--provider',
        choices=['anthropic', 'openai', 'google'],
        default='anthropic',
        help='LLM provider (default: anthropic)'
    )
    parser.add_argument(
        '--model',
        help='Specific model (uses default for provider if not specified)'
    )
    parser.add_argument(
        '--strategy',
        choices=['multi_stage', 'single_shot'],
        default='multi_stage',
        help='Writing strategy (default: multi_stage)'
    )
    parser.add_argument(
        '--details',
        action='store_true',
        help='Show detailed breakdown'
    )

    args = parser.parse_args()

    calc = CostCalculator()

    try:
        if args.jobs:
            # Simple estimate
            model = args.model or DEFAULT_MODELS[args.provider]
            estimate = calc.calculate_batch_cost(
                args.jobs,
                args.provider,
                model,
                args.strategy
            )
            calc.display_cost_estimate(estimate, show_details=args.details)

        else:
            # Estimate from file
            file_path = Path(args.input)
            if not file_path.exists():
                print(f"ERROR: File not found: {file_path}")
                sys.exit(1)

            estimate = calc.calculate_batch_file_cost(
                file_path,
                default_provider=args.provider,
                default_strategy=args.strategy
            )
            calc.display_cost_estimate(estimate, show_details=args.details)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
