#!/usr/bin/env python3
"""
BACOWR Startup Verification Script

This smoke test verifies that BACOWR can be imported and basic functionality works.
Can be used locally or in CI pipelines to verify installation.

Usage:
    python verify_startup.py
    python verify_startup.py --quick     # Skip full tests
    python verify_startup.py --verbose   # Show detailed output
"""

import sys
import os
from pathlib import Path
import argparse

# Setup Python path once at module level
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

# Colors for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


def print_status(message, status='info'):
    """Print status message with color."""
    if status == 'success':
        print(f"{GREEN}✓{NC} {message}")
    elif status == 'warning':
        print(f"{YELLOW}⚠{NC} {message}")
    elif status == 'error':
        print(f"{RED}✗{NC} {message}")
    else:
        print(f"  {message}")


def check_python_version():
    """Verify Python version is 3.8+."""
    print("\n1. Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print_status(f"Python {version.major}.{version.minor}.{version.micro}", 'success')
        return True
    else:
        print_status(f"Python {version.major}.{version.minor} is too old (need 3.8+)", 'error')
        return False


def check_imports():
    """Verify critical imports work."""
    print("\n2. Checking critical imports...")
    
    required_modules = [
        ('dotenv', 'python-dotenv'),
        ('requests', 'requests'),
        ('yaml', 'pyyaml'),
        ('jsonschema', 'jsonschema'),
        ('bs4', 'beautifulsoup4'),
    ]
    
    all_ok = True
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            print_status(f"{package_name}", 'success')
        except ImportError:
            print_status(f"{package_name} (missing)", 'error')
            all_ok = False
    
    return all_ok


def check_src_structure():
    """Verify src/ directory structure exists."""
    print("\n3. Checking project structure...")
    
    required_dirs = [
        'src',
        'src/utils',
        'src/pipeline',
        'src/qc',
        'src/profiling',
        'src/research',
        'src/writer',
        'config',
        'storage',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print_status(f"{dir_path}/", 'success')
        else:
            print_status(f"{dir_path}/ (missing)", 'warning')
            all_ok = False
    
    return all_ok


def check_config_files():
    """Verify configuration files exist."""
    print("\n4. Checking configuration files...")
    
    config_files = [
        ('config/thresholds.yaml', True),
        ('config/policies.yaml', True),
        ('.env.example', True),
        ('.env', False),  # Optional
    ]
    
    all_ok = True
    for file_path, required in config_files:
        path = Path(file_path)
        if path.exists():
            print_status(f"{file_path}", 'success')
        elif required:
            print_status(f"{file_path} (missing)", 'error')
            all_ok = False
        else:
            print_status(f"{file_path} (optional, not found)", 'warning')
    
    return all_ok


def test_dotenv_loading():
    """Test that .env loading works."""
    print("\n5. Testing .env loading...")
    
    try:
        from dotenv import load_dotenv
        
        # Try to load .env.example as a test
        env_example = Path('.env.example')
        if env_example.exists():
            load_dotenv(dotenv_path=env_example)
            print_status(".env loading mechanism works", 'success')
            return True
        else:
            print_status(".env.example not found for testing", 'warning')
            return True
    except Exception as e:
        print_status(f"dotenv loading failed: {e}", 'error')
        return False


def test_basic_imports():
    """Test that BACOWR modules can be imported."""
    print("\n6. Testing BACOWR module imports...")
    
    modules_to_test = [
        'src.utils.logger',
        'src.utils.validation',
        'src.qc.quality_controller',
        'src.pipeline.state_machine',  # Correct path as used in run_bacowr.py
    ]
    
    all_ok = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print_status(f"{module_name}", 'success')
        except ImportError as e:
            print_status(f"{module_name} (failed: {e})", 'error')
            all_ok = False
        except Exception as e:
            print_status(f"{module_name} (error: {e})", 'warning')
            # Don't fail on non-import errors in this smoke test
    
    return all_ok


def test_run_bacowr_exists():
    """Verify run_bacowr.py exists and is executable."""
    print("\n7. Checking run_bacowr.py entry point...")
    
    run_bacowr = Path('run_bacowr.py')
    if not run_bacowr.exists():
        print_status("run_bacowr.py not found", 'error')
        return False
    
    print_status("run_bacowr.py exists", 'success')
    
    # Check if it's executable (Unix-like systems)
    if os.name != 'nt':  # Not Windows
        if os.access(run_bacowr, os.X_OK):
            print_status("run_bacowr.py is executable", 'success')
        else:
            print_status("run_bacowr.py is not executable (run: chmod +x run_bacowr.py)", 'warning')
    
    return True


def quick_smoke_test():
    """Run a quick smoke test of core functionality."""
    print("\n8. Running quick smoke test...")
    
    try:
        # Try to import and create a logger
        from src.utils.logger import get_logger
        logger = get_logger("smoke_test")
        print_status("Logger creation works", 'success')
        
        # Try to load a config file
        import yaml
        config_path = Path('config/thresholds.yaml')
        if config_path.exists():
            with open(config_path) as f:
                yaml.safe_load(f)
            print_status("Config file loading works", 'success')
        
        return True
    except Exception as e:
        print_status(f"Smoke test failed: {e}", 'error')
        return False


def main():
    """Run all verification checks."""
    parser = argparse.ArgumentParser(description='BACOWR Startup Verification')
    parser.add_argument('--quick', action='store_true', help='Skip full tests')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    print("=" * 70)
    print("BACOWR Startup Verification")
    print("=" * 70)
    
    results = []
    
    # Run checks
    results.append(("Python version", check_python_version()))
    results.append(("Critical imports", check_imports()))
    results.append(("Project structure", check_src_structure()))
    results.append(("Configuration files", check_config_files()))
    results.append(("dotenv loading", test_dotenv_loading()))
    results.append(("BACOWR modules", test_basic_imports()))
    results.append(("Entry point", test_run_bacowr_exists()))
    
    if not args.quick:
        results.append(("Smoke test", quick_smoke_test()))
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = 'success' if result else 'error'
        print_status(f"{name}", status)
    
    print()
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print_status("All checks passed! BACOWR is ready to use.", 'success')
        print()
        print("Next steps:")
        print("  1. Copy .env.example to .env and add your API keys")
        print("  2. Run: python run_bacowr.py --mode dev --publisher example.com --target https://example.com --anchor 'test'")
        print("  3. Or use: ./start_bacowr.sh")
        return 0
    else:
        print_status(f"{total - passed} checks failed", 'error')
        print()
        print("Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == '__main__':
    sys.exit(main())
