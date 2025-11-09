"""
Core services smoke test - tests services without API routes.
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


def test_core_services():
    """Test core services initialization."""
    print("=" * 60)
    print("Testing Core Services")
    print("=" * 60)

    # Test job orchestrator
    print("\n1. Job Orchestrator...")
    from api.app.services.job_orchestrator import BacklinkJobOrchestrator
    orchestrator = BacklinkJobOrchestrator(llm_provider='anthropic')
    assert orchestrator is not None
    assert hasattr(orchestrator, 'execute')
    print("   ✓ Initialized")
    print("   ✓ Has execute() method")

    # Test writer engine
    print("\n2. Writer Engine...")
    from api.app.services.writer_engine import WriterEngine
    engine = WriterEngine(provider='anthropic')
    assert engine is not None
    assert hasattr(engine, 'generate')
    assert hasattr(engine, '_build_prompt')
    print("   ✓ Initialized")
    print("   ✓ Has generate() method")
    print("   ✓ Has _build_prompt() method")

    # Test SERP API
    print("\n3. SERP API Integration...")
    from api.app.services.serp_api import SerpAPIIntegration
    serp_client = SerpAPIIntegration()
    assert serp_client is not None
    assert hasattr(serp_client, 'research')
    print("   ✓ Initialized")
    print("   ✓ Has research() method")

    # Test QC Validator
    print("\n4. Next-A1 QC Validator...")
    from api.app.services.qc_validator import NextA1QCValidator
    validator = NextA1QCValidator()
    assert validator is not None
    assert hasattr(validator, 'validate')

    # Check all 8 criteria methods exist
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
        assert hasattr(validator, method), f"Missing {method}"

    print("   ✓ Initialized")
    print("   ✓ Has validate() method")
    print("   ✓ Has all 8 QC criteria methods")

    # Test that orchestrator can access all dependencies
    print("\n5. Orchestrator Dependencies...")
    assert orchestrator.llm_provider == 'anthropic'
    print(f"   ✓ LLM Provider: {orchestrator.llm_provider}")

    # Test writer engine can access all dependencies
    print("\n6. Writer Engine Dependencies...")
    assert engine.provider == 'anthropic'
    assert engine.api_key is not None
    print(f"   ✓ Provider: {engine.provider}")
    print(f"   ✓ API Key configured")

    print("\n" + "=" * 60)
    print("🎉 All Core Services Tests Passed!")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Set real API keys (ANTHROPIC_API_KEY, SERPAPI_KEY)")
    print("2. Test with real target URL")
    print("3. Verify complete end-to-end pipeline")
    print()


if __name__ == "__main__":
    try:
        test_core_services()
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
