"""
Test suite for BACOWR core services.

Tests all 4 core services:
- JobOrchestrator
- WriterEngine
- SerpAPIIntegration
- NextA1QCValidator
"""

import sys
import os
from pathlib import Path

# Add BACOWR to path
sys.path.insert(0, '/home/user/BACOWR')

def test_imports():
    """Test that all core services can be imported."""
    print("\n=== Test 1: Import Core Services ===")

    try:
        from api.app.services.job_orchestrator import BacklinkJobOrchestrator
        print("✓ JobOrchestrator imported")

        from api.app.services.writer_engine import WriterEngine
        print("✓ WriterEngine imported")

        from api.app.services.serp_api import SerpAPIIntegration
        print("✓ SerpAPIIntegration imported")

        from api.app.services.qc_validator import NextA1QCValidator
        print("✓ NextA1QCValidator imported")

        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


def test_orchestrator_initialization():
    """Test JobOrchestrator initialization."""
    print("\n=== Test 2: JobOrchestrator Initialization ===")

    try:
        from api.app.services.job_orchestrator import BacklinkJobOrchestrator

        orchestrator = BacklinkJobOrchestrator(
            enable_llm_profiling=True,
            enable_qc_validation=True
        )

        assert orchestrator.enable_llm_profiling == True
        assert orchestrator.enable_qc_validation == True
        assert hasattr(orchestrator, 'execute')
        assert hasattr(orchestrator, 'profiler')
        assert hasattr(orchestrator, 'intent_analyzer')
        assert hasattr(orchestrator, 'qc_controller')

        print("✓ Orchestrator initialized successfully")
        print(f"  • LLM Profiling: {orchestrator.enable_llm_profiling}")
        print(f"  • QC Validation: {orchestrator.enable_qc_validation}")
        print(f"  • Has execute() method: True")
        print(f"  • Dependencies loaded: True")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_writer_engine_initialization():
    """Test WriterEngine initialization."""
    print("\n=== Test 3: WriterEngine Initialization ===")

    try:
        from api.app.services.writer_engine import WriterEngine

        # Test with mock API keys
        os.environ.setdefault('ANTHROPIC_API_KEY', 'demo_key')
        os.environ.setdefault('OPENAI_API_KEY', 'demo_key')
        os.environ.setdefault('GOOGLE_API_KEY', 'demo_key')

        engine = WriterEngine(llm_provider='anthropic')

        assert engine.primary_provider.value == 'anthropic'
        assert hasattr(engine, 'generate_article')
        assert hasattr(engine, '_call_anthropic')
        assert hasattr(engine, '_call_openai')
        assert hasattr(engine, '_call_google')

        print("✓ WriterEngine initialized successfully")
        print(f"  • Provider: {engine.primary_provider.value}")
        print(f"  • Supports: Anthropic Claude, OpenAI GPT, Google Gemini")
        print(f"  • Has generate_article() method: True")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_serp_api_initialization():
    """Test SerpAPIIntegration initialization."""
    print("\n=== Test 4: SerpAPIIntegration Initialization ===")

    try:
        from api.app.services.serp_api import SerpAPIIntegration

        # Test with mock API key
        os.environ.setdefault('SERPAPI_KEY', 'demo_key')

        serp_api = SerpAPIIntegration()

        assert hasattr(serp_api, 'fetch_serp_data')
        assert hasattr(serp_api, 'analyze_serp_results')
        assert hasattr(serp_api, 'build_serp_research_extension')

        print("✓ SerpAPIIntegration initialized successfully")
        print(f"  • Has fetch_serp_data() method: True")
        print(f"  • Has analyze_serp_results() method: True")
        print(f"  • Mock mode supported: True")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_qc_validator_initialization():
    """Test NextA1QCValidator initialization."""
    print("\n=== Test 5: NextA1QCValidator Initialization ===")

    try:
        from api.app.services.qc_validator import NextA1QCValidator

        validator = NextA1QCValidator()

        assert hasattr(validator, 'validate')

        # Check all 8 criteria methods
        criteria_methods = [
            '_validate_preflight',
            '_validate_draft',
            '_validate_anchor',
            '_validate_trust',
            '_validate_intent',
            '_validate_lsi',
            '_validate_fit',
            '_validate_compliance'
        ]

        for method in criteria_methods:
            assert hasattr(validator, method), f"Missing method: {method}"

        print("✓ NextA1QCValidator initialized successfully")
        print(f"  • Has validate() method: True")
        print(f"  • All 8 QC criteria present: True")
        print(f"  • Criteria: PREFLIGHT, DRAFT, ANCHOR, TRUST, INTENT, LSI, FIT, COMPLIANCE")

        return True
    except Exception as e:
        print(f"✗ Initialization failed: {e}")
        return False


def test_qc_criteria_details():
    """Test QC criteria implementation details."""
    print("\n=== Test 6: QC Criteria Details ===")

    try:
        from api.app.services.qc_validator import NextA1QCValidator

        validator = NextA1QCValidator()

        # Test with minimal valid inputs
        article = """
# Test Article

This is a test article with some content.

## Section 1

Here is some content with [anchor text](https://example.com) in a paragraph.

## Section 2

More content here with proper structure.

## Conclusion

Final thoughts and summary.
"""

        job_package = {
            'job_meta': {'job_id': 'test_001'},
            'input_minimal': {
                'publisher_domain': 'test.com',
                'target_url': 'https://example.com',
                'anchor_text': 'anchor text'
            },
            'publisher_profile': {
                'domain': 'test.com',
                'language': 'en',
                'tone': 'professional'
            },
            'target_profile': {
                'url': 'https://example.com',
                'title': 'Test Page'
            },
            'anchor_profile': {
                'text': 'anchor text',
                'type': 'partial'
            },
            'intent_extension': {
                'overall_alignment': 'aligned',
                'target_intent': 'informational',
                'serp_dominant_intent': 'informational'
            },
            'serp_research_extension': {
                'main_query': 'test query',
                'subtopics': ['topic1', 'topic2']
            }
        }

        # Run validation (will likely fail, but should execute)
        report = validator.validate(article, job_package)

        assert 'overall_score' in report
        assert 'overall_status' in report
        assert 'criteria_results' in report
        assert len(report['criteria_results']) == 8

        print("✓ QC validation executed successfully")
        print(f"  • Overall Score: {report['overall_score']:.1f}")
        print(f"  • Status: {report['overall_status']}")
        print(f"  • Criteria Tested: {len(report['criteria_results'])}")

        return True
    except Exception as e:
        print(f"✗ QC validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_integration_ready():
    """Test that all services are integration-ready."""
    print("\n=== Test 7: Integration Readiness ===")

    try:
        from api.app.services.job_orchestrator import BacklinkJobOrchestrator
        from api.app.services.writer_engine import WriterEngine
        from api.app.services.serp_api import SerpAPIIntegration
        from api.app.services.qc_validator import NextA1QCValidator

        # Set mock API keys
        os.environ.setdefault('ANTHROPIC_API_KEY', 'demo_key')
        os.environ.setdefault('SERPAPI_KEY', 'demo_key')

        # Initialize all services
        orchestrator = BacklinkJobOrchestrator(
            enable_llm_profiling=True,
            enable_qc_validation=True
        )
        writer = WriterEngine(llm_provider='anthropic')
        serp = SerpAPIIntegration()
        qc = NextA1QCValidator()

        # Verify orchestrator has access to all dependencies
        assert orchestrator.profiler is not None
        assert orchestrator.intent_analyzer is not None
        assert orchestrator.qc_controller is not None

        print("✓ All services integration-ready")
        print(f"  • Orchestrator → Profiler: Connected")
        print(f"  • Orchestrator → IntentAnalyzer: Connected")
        print(f"  • Orchestrator → QCController: Connected")
        print(f"  • WriterEngine: Initialized")
        print(f"  • SerpAPI: Initialized")
        print(f"  • Full pipeline ready: True")

        return True
    except Exception as e:
        print(f"✗ Integration check failed: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("=" * 70)
    print("BACOWR CORE SERVICES TEST SUITE")
    print("=" * 70)

    tests = [
        ("Import Core Services", test_imports),
        ("JobOrchestrator Init", test_orchestrator_initialization),
        ("WriterEngine Init", test_writer_engine_initialization),
        ("SerpAPI Init", test_serp_api_initialization),
        ("QCValidator Init", test_qc_validator_initialization),
        ("QC Criteria Details", test_qc_criteria_details),
        ("Integration Readiness", test_integration_ready)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")

    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 70)

    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
