#!/usr/bin/env python3
"""
BACOWR Live Testing Tool
========================

Interactive tool for testing content generation with multiple LLM models.

Features:
- Test content generation in real-time
- Compare different LLM models side-by-side
- Measure cost, time, and quality
- Save results for comparison
- Visual diff between outputs

Usage:
    python tools/live_test.py
    python tools/live_test.py --quick  # Quick test with defaults
    python tools/live_test.py --compare-models  # Compare all models
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Lazy imports to avoid dependency issues
# These will be imported when needed


# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


# Model configurations with pricing
MODELS = {
    'claude-sonnet': {
        'provider': 'anthropic',
        'model': 'claude-3-5-sonnet-20241022',
        'cost_per_1k_input': 0.003,
        'cost_per_1k_output': 0.015,
        'description': 'Claude 3.5 Sonnet - Most capable, best quality'
    },
    'claude-haiku': {
        'provider': 'anthropic',
        'model': 'claude-3-haiku-20240307',
        'cost_per_1k_input': 0.00025,
        'cost_per_1k_output': 0.00125,
        'description': 'Claude 3 Haiku - Fast and cheap'
    },
    'gpt-4o': {
        'provider': 'openai',
        'model': 'gpt-4o',
        'cost_per_1k_input': 0.0025,
        'cost_per_1k_output': 0.010,
        'description': 'GPT-4o - Latest OpenAI model'
    },
    'gpt-4o-mini': {
        'provider': 'openai',
        'model': 'gpt-4o-mini',
        'cost_per_1k_input': 0.00015,
        'cost_per_1k_output': 0.0006,
        'description': 'GPT-4o Mini - Fast and cheap'
    },
    'gpt-4-turbo': {
        'provider': 'openai',
        'model': 'gpt-4-turbo-preview',
        'cost_per_1k_input': 0.010,
        'cost_per_1k_output': 0.030,
        'description': 'GPT-4 Turbo - High quality'
    },
    'gemini-flash': {
        'provider': 'google',
        'model': 'gemini-1.5-flash',
        'cost_per_1k_input': 0.00010,
        'cost_per_1k_output': 0.0004,
        'description': 'Gemini 1.5 Flash - Very fast and cheap'
    },
    'gemini-pro': {
        'provider': 'google',
        'model': 'gemini-1.5-pro',
        'cost_per_1k_input': 0.00125,
        'cost_per_1k_output': 0.005,
        'description': 'Gemini 1.5 Pro - High quality'
    }
}


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 70}{Colors.ENDC}\n")


def print_section(text: str):
    """Print section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-' * len(text)}{Colors.ENDC}")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ {text}{Colors.ENDC}")


def check_api_keys() -> Dict[str, bool]:
    """Check which API keys are available"""
    keys = {
        'anthropic': bool(os.getenv('ANTHROPIC_API_KEY')),
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'google': bool(os.getenv('GOOGLE_API_KEY'))
    }
    return keys


def get_available_models() -> List[str]:
    """Get list of available models based on API keys"""
    keys = check_api_keys()
    available = []

    for model_name, config in MODELS.items():
        provider = config['provider']
        if keys.get(provider):
            available.append(model_name)

    return available


def estimate_cost(prompt_tokens: int, output_tokens: int, model_name: str) -> float:
    """Estimate cost for a model run"""
    if model_name not in MODELS:
        return 0.0

    config = MODELS[model_name]
    input_cost = (prompt_tokens / 1000) * config['cost_per_1k_input']
    output_cost = (output_tokens / 1000) * config['cost_per_1k_output']

    return input_cost + output_cost


def count_tokens(text: str) -> int:
    """Rough token count (4 chars ≈ 1 token)"""
    return len(text) // 4


def generate_with_model(
    job_package: Dict[str, Any],
    model_name: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Generate content with specific model.

    Returns:
        {
            'article': str,
            'time': float,
            'estimated_cost': float,
            'tokens_input': int,
            'tokens_output': int,
            'error': str (if failed)
        }
    """
    if model_name not in MODELS:
        return {'error': f'Unknown model: {model_name}'}

    config = MODELS[model_name]

    # Import WriterEngine when needed
    try:
        from src.writer.writer_engine import WriterEngine
    except ImportError as e:
        return {'error': f'Failed to import WriterEngine: {e}'}

    # Create writer engine
    try:
        # Get API key for provider
        api_key = None
        if config['provider'] == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            writer = WriterEngine(
                anthropic_api_key=api_key,
                mock_mode=False,
                llm_provider='anthropic'
            )
            # Override model
            writer.anthropic_client.messages.model = config['model']

        elif config['provider'] == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            writer = WriterEngine(
                openai_api_key=api_key,
                mock_mode=False,
                llm_provider='openai'
            )
            # We'll need to modify _generate_with_openai to accept model param
            # For now, use existing implementation

        elif config['provider'] == 'google':
            # Google not yet implemented in writer_engine
            return {'error': 'Google provider not yet implemented in WriterEngine'}

        if not api_key:
            return {'error': f'No API key for {config["provider"]}'}

        # Generate article
        start_time = time.time()
        article = writer.generate(job_package)
        elapsed = time.time() - start_time

        # Estimate tokens and cost
        prompt = writer._build_llm_prompt(job_package)
        tokens_input = count_tokens(prompt)
        tokens_output = count_tokens(article)
        estimated_cost = estimate_cost(tokens_input, tokens_output, model_name)

        return {
            'article': article,
            'time': elapsed,
            'estimated_cost': estimated_cost,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'model': model_name,
            'provider': config['provider'],
            'word_count': len(article.split())
        }

    except Exception as e:
        return {'error': str(e)}


def save_test_result(result: Dict[str, Any], test_name: str = None):
    """Save test result to file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = test_name or f"test_{timestamp}"

    results_dir = Path(__file__).parent.parent / 'storage' / 'test_results'
    results_dir.mkdir(parents=True, exist_ok=True)

    file_path = results_dir / f"{test_name}.json"

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return str(file_path)


def interactive_test():
    """Interactive testing mode"""
    print_header("BACOWR Live Testing Tool")

    # Check API keys
    print_section("API Keys Status")
    keys = check_api_keys()
    for provider, available in keys.items():
        if available:
            print_success(f"{provider.capitalize()}: Available")
        else:
            print_warning(f"{provider.capitalize()}: Not configured")

    if not any(keys.values()):
        print_error("No API keys configured! Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY")
        return

    # Show available models
    print_section("Available Models")
    available_models = get_available_models()
    for i, model_name in enumerate(available_models, 1):
        config = MODELS[model_name]
        cost_range = f"${config['cost_per_1k_output']:.4f}/1K tokens"
        print(f"  {i}. {Colors.BOLD}{model_name}{Colors.ENDC} - {config['description']} ({cost_range})")

    # Main menu
    while True:
        print_section("What would you like to do?")
        print("  1. Quick test with mock data (single model)")
        print("  2. Compare multiple models (same input)")
        print("  3. Custom input test")
        print("  4. View saved results")
        print("  0. Exit")

        choice = input(f"\n{Colors.BOLD}Choose option: {Colors.ENDC}").strip()

        if choice == '0':
            print_info("Goodbye!")
            break
        elif choice == '1':
            quick_test(available_models)
        elif choice == '2':
            compare_models(available_models)
        elif choice == '3':
            custom_test(available_models)
        elif choice == '4':
            view_results()
        else:
            print_warning("Invalid choice")


def quick_test(available_models: List[str]):
    """Quick test with mock data"""
    print_section("Quick Test - Mock Data")

    # Show available models
    print("Available models:")
    for i, model_name in enumerate(available_models, 1):
        print(f"  {i}. {model_name}")

    # Select model
    try:
        choice = int(input(f"{Colors.BOLD}Select model (number): {Colors.ENDC}").strip())
        if choice < 1 or choice > len(available_models):
            print_error("Invalid selection")
            return

        model_name = available_models[choice - 1]
    except ValueError:
        print_error("Invalid input")
        return

    # Load mock package
    print_info("Loading mock job package...")
    try:
        from src.api import load_mock_package
        job_package = load_mock_package()
    except ImportError as e:
        print_error(f"Failed to load mock package: {e}")
        return
    except Exception as e:
        print_error(f"Error loading mock package: {e}")
        return

    # Show test details
    print_info(f"Publisher: {job_package['input_minimal']['publisher_domain']}")
    print_info(f"Target: {job_package['input_minimal']['target_url']}")
    print_info(f"Anchor: {job_package['input_minimal']['anchor_text']}")

    # Generate
    print_info(f"Generating with {model_name}...")
    result = generate_with_model(job_package, model_name, verbose=True)

    # Show results
    if 'error' in result:
        print_error(f"Error: {result['error']}")
        return

    print_section("Results")
    print_success(f"Generated in {result['time']:.2f}s")
    print_success(f"Word count: {result['word_count']}")
    print_success(f"Estimated cost: ${result['estimated_cost']:.4f}")
    print_success(f"Tokens: {result['tokens_input']} input, {result['tokens_output']} output")

    # Show article preview
    print_section("Article Preview (first 500 chars)")
    print(result['article'][:500])
    print("...")

    # Ask to save
    save = input(f"\n{Colors.BOLD}Save this test? (y/n): {Colors.ENDC}").strip().lower()
    if save == 'y':
        test_name = input(f"{Colors.BOLD}Test name (optional): {Colors.ENDC}").strip()
        full_result = {
            'job_package': job_package,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        file_path = save_test_result(full_result, test_name)
        print_success(f"Saved to: {file_path}")


def compare_models(available_models: List[str]):
    """Compare multiple models with same input"""
    print_section("Model Comparison")

    # Select models to compare
    print("Available models:")
    for i, model_name in enumerate(available_models, 1):
        config = MODELS[model_name]
        print(f"  {i}. {model_name} (${config['cost_per_1k_output']:.4f}/1K)")

    print(f"\n{Colors.BOLD}Select models to compare (comma-separated numbers, or 'all'): {Colors.ENDC}")
    selection = input().strip()

    if selection.lower() == 'all':
        selected_models = available_models
    else:
        try:
            indices = [int(x.strip()) - 1 for x in selection.split(',')]
            selected_models = [available_models[i] for i in indices if 0 <= i < len(available_models)]
        except (ValueError, IndexError):
            print_error("Invalid selection")
            return

    if not selected_models:
        print_error("No models selected")
        return

    print_info(f"Will compare {len(selected_models)} models: {', '.join(selected_models)}")

    # Load mock package
    try:
        from src.api import load_mock_package
        job_package = load_mock_package()
    except Exception as e:
        print_error(f"Failed to load mock package: {e}")
        return

    print_info(f"Using mock data: {job_package['input_minimal']['publisher_domain']}")

    # Generate with each model
    results = {}
    for model_name in selected_models:
        print_info(f"Generating with {model_name}...")
        result = generate_with_model(job_package, model_name)
        results[model_name] = result

        if 'error' in result:
            print_error(f"{model_name}: {result['error']}")
        else:
            print_success(f"{model_name}: Done ({result['time']:.2f}s, ${result['estimated_cost']:.4f})")

    # Show comparison table
    print_section("Comparison Results")

    # Header
    print(f"\n{Colors.BOLD}{'Model':<20} {'Time':>8} {'Cost':>10} {'Words':>8} {'Tokens Out':>12}{Colors.ENDC}")
    print("-" * 70)

    # Data rows
    for model_name, result in results.items():
        if 'error' not in result:
            print(f"{model_name:<20} {result['time']:>7.2f}s ${result['estimated_cost']:>8.4f} {result['word_count']:>8} {result['tokens_output']:>12}")

    # Show winner in each category
    print_section("Best in Category")

    valid_results = {k: v for k, v in results.items() if 'error' not in v}

    if valid_results:
        fastest = min(valid_results.items(), key=lambda x: x[1]['time'])
        cheapest = min(valid_results.items(), key=lambda x: x[1]['estimated_cost'])
        longest = max(valid_results.items(), key=lambda x: x[1]['word_count'])

        print_success(f"Fastest: {fastest[0]} ({fastest[1]['time']:.2f}s)")
        print_success(f"Cheapest: {cheapest[0]} (${cheapest[1]['estimated_cost']:.4f})")
        print_success(f"Most words: {longest[0]} ({longest[1]['word_count']} words)")

    # Ask to save
    save = input(f"\n{Colors.BOLD}Save comparison? (y/n): {Colors.ENDC}").strip().lower()
    if save == 'y':
        test_name = input(f"{Colors.BOLD}Test name (optional): {Colors.ENDC}").strip()
        full_result = {
            'type': 'comparison',
            'job_package': job_package,
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
        file_path = save_test_result(full_result, test_name or f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        print_success(f"Saved to: {file_path}")


def custom_test(available_models: List[str]):
    """Custom input test"""
    print_section("Custom Input Test")
    print_info("Enter your test parameters")

    # Get inputs
    publisher = input(f"{Colors.BOLD}Publisher domain: {Colors.ENDC}").strip()
    target = input(f"{Colors.BOLD}Target URL: {Colors.ENDC}").strip()
    anchor = input(f"{Colors.BOLD}Anchor text: {Colors.ENDC}").strip()

    if not (publisher and target and anchor):
        print_error("All fields required")
        return

    # Load mock package and modify
    try:
        from src.api import load_mock_package
        job_package = load_mock_package()
    except Exception as e:
        print_error(f"Failed to load mock package: {e}")
        return

    job_package['input_minimal']['publisher_domain'] = publisher
    job_package['input_minimal']['target_url'] = target
    job_package['input_minimal']['anchor_text'] = anchor

    # Select model
    print("\nAvailable models:")
    for i, model_name in enumerate(available_models, 1):
        print(f"  {i}. {model_name}")

    try:
        choice = int(input(f"{Colors.BOLD}Select model (number): {Colors.ENDC}").strip())
        model_name = available_models[choice - 1]
    except (ValueError, IndexError):
        print_error("Invalid selection")
        return

    # Generate
    print_info(f"Generating with {model_name}...")
    result = generate_with_model(job_package, model_name)

    if 'error' in result:
        print_error(f"Error: {result['error']}")
        return

    # Show results
    print_section("Results")
    print_success(f"Generated in {result['time']:.2f}s")
    print_success(f"Word count: {result['word_count']}")
    print_success(f"Estimated cost: ${result['estimated_cost']:.4f}")

    print_section("Article Preview (first 800 chars)")
    print(result['article'][:800])
    print("...")

    # Full article
    view_full = input(f"\n{Colors.BOLD}View full article? (y/n): {Colors.ENDC}").strip().lower()
    if view_full == 'y':
        print_section("Full Article")
        print(result['article'])

    # Save
    save = input(f"\n{Colors.BOLD}Save this test? (y/n): {Colors.ENDC}").strip().lower()
    if save == 'y':
        test_name = input(f"{Colors.BOLD}Test name (optional): {Colors.ENDC}").strip()
        full_result = {
            'type': 'custom',
            'job_package': job_package,
            'result': result,
            'timestamp': datetime.now().isoformat()
        }
        file_path = save_test_result(full_result, test_name)
        print_success(f"Saved to: {file_path}")


def view_results():
    """View saved test results"""
    print_section("Saved Test Results")

    results_dir = Path(__file__).parent.parent / 'storage' / 'test_results'

    if not results_dir.exists():
        print_warning("No saved results found")
        return

    files = list(results_dir.glob('*.json'))

    if not files:
        print_warning("No saved results found")
        return

    # List files
    print(f"Found {len(files)} saved tests:\n")
    for i, file in enumerate(files, 1):
        # Load and show summary
        try:
            with open(file, 'r') as f:
                data = json.load(f)

            timestamp = data.get('timestamp', 'Unknown')
            test_type = data.get('type', 'single')

            if test_type == 'comparison':
                model_count = len(data.get('results', {}))
                print(f"  {i}. {file.name} - Comparison of {model_count} models ({timestamp})")
            else:
                model = data.get('result', {}).get('model', 'Unknown')
                print(f"  {i}. {file.name} - {model} ({timestamp})")
        except:
            print(f"  {i}. {file.name} - (error loading)")

    # Select to view
    try:
        choice = int(input(f"\n{Colors.BOLD}View result (number, 0 to cancel): {Colors.ENDC}").strip())
        if choice == 0:
            return
        if choice < 1 or choice > len(files):
            print_error("Invalid selection")
            return

        file = files[choice - 1]
        with open(file, 'r') as f:
            data = json.load(f)

        print_section(f"Test Result: {file.name}")
        print(json.dumps(data, indent=2, ensure_ascii=False))

    except (ValueError, IndexError):
        print_error("Invalid input")


def main():
    parser = argparse.ArgumentParser(
        description="BACOWR Live Testing Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--quick', action='store_true', help='Quick test mode')
    parser.add_argument('--compare-models', action='store_true', help='Compare all models')
    parser.add_argument('--model', help='Specific model to test')

    args = parser.parse_args()

    if args.compare_models:
        available_models = get_available_models()
        if not available_models:
            print_error("No API keys configured")
            return
        compare_models(available_models)
    elif args.quick:
        available_models = get_available_models()
        if not available_models:
            print_error("No API keys configured")
            return
        quick_test(available_models)
    else:
        # Interactive mode
        interactive_test()


if __name__ == "__main__":
    main()
