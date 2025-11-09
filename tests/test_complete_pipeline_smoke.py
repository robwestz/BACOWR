"""
Smoke test for complete pipeline orchestration.

Tests that all modules integrate correctly without requiring real API keys.
"""

import sys
import os
from pathlib import Path

# Add BACOWR root to path
BACOWR_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(BACOWR_ROOT))

# Set mock environment variables
os.environ['SERPAPI_KEY'] = 'mock_serp_key'
os.environ['ANTHROPIC_API_KEY'] = 'mock_anthropic_key'


def test_orchestrator_initialization():
    """Test that orchestrator can be initialized."""
    from api.app.services.job_orchestrator import BacklinkJobOrchestrator

    orchestrator = BacklinkJobOrchestrator(llm_provider='anthropic')

    assert orchestrator is not None
    assert orchestrator.llm_provider == 'anthropic'
    print("✓ Orchestrator initialization test passed")


def test_writer_engine_initialization():
    """Test that writer engine can be initialized."""
    from api.app.services.writer_engine import WriterEngine

    engine = WriterEngine(provider='anthropic')

    assert engine is not None
    assert engine.provider == 'anthropic'
    print("✓ Writer engine initialization test passed")


def test_serp_api_initialization():
    """Test that SERP API can be initialized."""
    from api.app.services.serp_api import SerpAPIIntegration

    client = SerpAPIIntegration()

    assert client is not None
    print("✓ SERP API initialization test passed")


def test_qc_validator_initialization():
    """Test that QC validator can be initialized."""
    from api.app.services.qc_validator import NextA1QCValidator

    validator = NextA1QCValidator()

    assert validator is not None
    print("✓ QC validator initialization test passed")


def test_all_imports():
    """Test that all required imports work."""
    try:
        from api.app.services.job_orchestrator import BacklinkJobOrchestrator
        from api.app.services.writer_engine import WriterEngine
        from api.app.services.serp_api import SerpAPIIntegration
        from api.app.services.qc_validator import NextA1QCValidator
        from api.app.routes.serp_research import router as serp_router
        from api.app.routes.intent_analysis import router as intent_router
        from api.app.routes.qc_validation import router as qc_router

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_orchestrator_methods_exist():
    """Test that orchestrator has all required methods."""
    from api.app.services.job_orchestrator import BacklinkJobOrchestrator

    orchestrator = BacklinkJobOrchestrator(llm_provider='anthropic')

    # Check critical methods exist
    assert hasattr(orchestrator, 'execute')
    assert callable(orchestrator.execute)

    print("✓ Orchestrator methods test passed")


def test_writer_engine_methods_exist():
    """Test that writer engine has all required methods."""
    from api.app.services.writer_engine import WriterEngine

    engine = WriterEngine(provider='anthropic')

    # Check critical methods exist
    assert hasattr(engine, 'generate')
    assert callable(engine.generate)
    assert hasattr(engine, '_build_prompt')
    assert callable(engine._build_prompt)

    print("✓ Writer engine methods test passed")


def test_qc_validator_criteria():
    """Test that QC validator has all 8 Next-A1 criteria."""
    from api.app.services.qc_validator import NextA1QCValidator

    validator = NextA1QCValidator()

    # Check validation method exists
    assert hasattr(validator, 'validate')
    assert callable(validator.validate)

    # The validator should have methods for all 8 criteria
    expected_criteria = [
        '_validate_preflight',
        '_validate_draft',
        '_validate_anchor',
        '_validate_trust',
        '_validate_intent',
        '_validate_lsi',
        '_validate_fit',
        '_validate_compliance'
    ]

    for criterion in expected_criteria:
        assert hasattr(validator, criterion), f"Missing {criterion}"

    print("✓ QC validator criteria test passed")


def run_all_tests():
    """Run all smoke tests."""
    print("=" * 60)
    print("BACOWR Complete Pipeline - Smoke Tests")
    print("=" * 60)
    print()

    tests = [
        ("All Imports", test_all_imports),
        ("Orchestrator Init", test_orchestrator_initialization),
        ("Writer Engine Init", test_writer_engine_initialization),
        ("SERP API Init", test_serp_api_initialization),
        ("QC Validator Init", test_qc_validator_initialization),
        ("Orchestrator Methods", test_orchestrator_methods_exist),
        ("Writer Engine Methods", test_writer_engine_methods_exist),
        ("QC Validator Criteria", test_qc_validator_criteria),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\n[{test_name}]")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_name} failed: {e}")
            failed += 1

    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n🎉 All smoke tests passed! Pipeline integration looks good.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
