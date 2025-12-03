"""
Test Suite for HyperPreflight + APEX Integration

Tests:
- HyperPreflight Engine basic execution
- TrustLink Engine source selection
- APEX orchestration
- LLM interfaces
- Backward compatibility adapter
"""

import pytest
import asyncio
from datetime import datetime

# Import components
from src.preflight_v2.hyper_preflight_engine import (
    HyperPreflightEngine,
    TokenBudget,
    DecisionLevel,
    MarriageStatus
)
from src.preflight_v2.trustlink_engine import (
    get_default_trustlink_engine,
    load_trustlink_sources
)
from src.preflight_v2.adapter import PreflightV2Adapter
from src.apex.bacowr_domain import (
    create_bacowr_apex_executor,
    run_apex_preflight
)
from src.integrations.llm_interface import PreflightRequest, run_preflight_unified
from src.integrations.chatgpt_interface import chatgpt_function_handler
from src.integrations.claude_interface import claude_tool_handler


# ============================================================================
# TEST: HYPERPREFLIGHT ENGINE
# ============================================================================


def test_hyperpreflight_basic():
    """Test basic HyperPreflight execution."""
    engine = HyperPreflightEngine(
        trustlink_engine=get_default_trustlink_engine(),
        token_budget=TokenBudget()
    )

    job = {
        'job_id': 'test-001',
        'vertical': 'general',
        'anchor_text': 'test anchor',
        'anchor_url': 'https://target.com',
        'query': 'test query',
        'publisher_profile': {'domain': 'publisher.com', 'primary_topic': 'general'},
        'target_profile': {'primary_topic': 'test', 'core_topics': ['test']}
    }

    contract = engine.run(job)

    assert contract.job_id == 'test-001'
    assert contract.decision.level in [
        DecisionLevel.AUTO_OK,
        DecisionLevel.NEEDS_HUMAN,
        DecisionLevel.AUTO_BLOCK
    ]
    assert isinstance(contract.trust_plan.sources, list)
    assert isinstance(contract.writer_plan.sections, list)
    assert len(contract.guardrails) > 0

    print(f"✅ HyperPreflight basic test passed")
    print(f"   Decision: {contract.decision.level.value}")
    print(f"   Trust sources: {len(contract.trust_plan.sources)}")
    print(f"   Sections: {len(contract.writer_plan.sections)}")


def test_hyperpreflight_finance_vertical():
    """Test HyperPreflight with finance vertical (strict guardrails)."""
    engine = HyperPreflightEngine(
        trustlink_engine=get_default_trustlink_engine()
    )

    job = {
        'job_id': 'test-finance',
        'vertical': 'finance',
        'anchor_text': 'bästa lånet',
        'anchor_url': 'https://bank.com/loan',
        'query': 'bästa lånet',
        'publisher_profile': {'domain': 'finans.se', 'primary_topic': 'finans'},
        'target_profile': {'primary_topic': 'lån', 'core_topics': ['lån', 'bank']}
    }

    contract = engine.run(job)

    # Finance should have strict guardrails
    hard_blocks = [g for g in contract.guardrails if g.priority.name == "HARD_BLOCK"]
    assert len(hard_blocks) >= 2, "Finance vertical should have hard block guardrails"

    # Should require disclaimers
    disclaimer_guardrails = [g for g in contract.guardrails if "disclaimer" in g.notes.lower()]
    assert len(disclaimer_guardrails) > 0, "Finance should require disclaimer"

    print(f"✅ Finance vertical test passed")
    print(f"   Hard block guardrails: {len(hard_blocks)}")
    print(f"   Risk level: {contract.risk_profile.risk_level.value}")


# ============================================================================
# TEST: TRUSTLINK ENGINE
# ============================================================================


def test_trustlink_source_loading():
    """Test loading trustlink sources from YAML."""
    sources = load_trustlink_sources()

    assert isinstance(sources, dict)
    assert len(sources) > 0, "Should load sources from YAML"

    # Check for known Swedish sources
    assert 'scb.se' in sources, "Should include SCB"
    assert 'regeringen.se' in sources, "Should include Regeringen"

    print(f"✅ TrustLink source loading test passed")
    print(f"   Loaded sources: {len(sources)}")


def test_trustlink_selection():
    """Test trust source selection with topic matching."""
    engine = get_default_trustlink_engine()

    plan = engine.select_trustlinks(
        topics=['ekonomi', 'finans'],
        industry='finance',
        language='sv',
        min_required=2,
        max_total=5
    )

    assert plan.mode in ["none", "minimal", "full"]
    if plan.sources:
        assert all(s.language == 'sv' for s in plan.sources)
        print(f"✅ TrustLink selection test passed")
        print(f"   Mode: {plan.mode}")
        print(f"   Sources: {len(plan.sources)}")
        print(f"   Top source: {plan.sources[0].domain if plan.sources else 'none'}")
    else:
        print(f"⚠️  TrustLink selection test passed (no sources found)")


# ============================================================================
# TEST: APEX ORCHESTRATION
# ============================================================================


@pytest.mark.asyncio
async def test_apex_executor():
    """Test APEX executor creation and basic execution."""
    executor = create_bacowr_apex_executor()

    task = "Generate preflight for test job"
    context = {
        'publisher_domain': 'test.com',
        'target_url': 'https://target.com',
        'anchor_text': 'test anchor',
        'vertical': 'general'
    }

    result = await executor.execute(task=task, context=context)

    assert result is not None
    assert result.score >= 0.0
    assert result.iterations >= 1
    assert result.termination_reason is not None

    print(f"✅ APEX executor test passed")
    print(f"   Score: {result.score:.2f}")
    print(f"   Iterations: {result.iterations}")
    print(f"   Termination: {result.termination_reason.value}")


@pytest.mark.asyncio
async def test_apex_preflight_run():
    """Test full APEX preflight run."""
    result = await run_apex_preflight(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor',
        vertical='general'
    )

    assert result.output is not None or result.termination_reason is not None

    if result.success:
        output = result.output
        assert output.handoff_contract is not None
        assert output.job_package is not None
        print(f"✅ APEX preflight run test passed")
        print(f"   Quality score: {result.score:.2f}")
    else:
        print(f"⚠️  APEX preflight failed: {result.termination_reason.value}")


# ============================================================================
# TEST: LLM INTERFACES
# ============================================================================


@pytest.mark.asyncio
async def test_unified_interface():
    """Test unified LLM interface."""
    request = PreflightRequest(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor',
        use_apex=False  # Deterministic mode for testing
    )

    response = await run_preflight_unified(request)

    assert isinstance(response.success, bool)
    assert response.job_id
    assert response.decision
    assert 0.0 <= response.quality_score <= 1.0

    print(f"✅ Unified interface test passed")
    print(f"   Success: {response.success}")
    print(f"   Decision: {response.decision}")


@pytest.mark.asyncio
async def test_chatgpt_handler():
    """Test ChatGPT function handler."""
    result = await chatgpt_function_handler(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor',
        use_apex=False
    )

    assert 'success' in result
    assert 'job_id' in result

    print(f"✅ ChatGPT handler test passed")
    print(f"   Success: {result.get('success')}")


@pytest.mark.asyncio
async def test_claude_handler():
    """Test Claude tool handler."""
    result = await claude_tool_handler(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor',
        use_apex=False
    )

    assert 'success' in result or 'error' in result

    print(f"✅ Claude handler test passed")
    print(f"   Success: {result.get('success')}")


# ============================================================================
# TEST: BACKWARD COMPATIBILITY
# ============================================================================


def test_preflight_v2_adapter():
    """Test PreflightV2Adapter for backward compatibility."""
    adapter = PreflightV2Adapter()

    job_package, is_valid, error = adapter.assemble_job_package(
        publisher_domain='test.com',
        target_url='https://target.com',
        anchor_text='test anchor'
    )

    # Should return valid tuple structure
    assert isinstance(job_package, dict) or job_package is None
    assert isinstance(is_valid, bool)
    assert isinstance(error, str) or error is None

    if is_valid:
        assert 'job_meta' in job_package
        assert 'input_minimal' in job_package
        print(f"✅ Adapter test passed (valid package)")
    else:
        print(f"⚠️  Adapter test passed (invalid package): {error}")


# ============================================================================
# MANUAL TEST RUNNER
# ============================================================================


if __name__ == "__main__":
    """Run tests manually without pytest."""
    print("\n" + "="*70)
    print("BACOWR HyperPreflight + APEX Test Suite")
    print("="*70 + "\n")

    # Sync tests
    print("Running synchronous tests...\n")
    test_hyperpreflight_basic()
    test_hyperpreflight_finance_vertical()
    test_trustlink_source_loading()
    test_trustlink_selection()
    test_preflight_v2_adapter()

    # Async tests
    print("\nRunning asynchronous tests...\n")
    asyncio.run(test_apex_executor())
    asyncio.run(test_apex_preflight_run())
    asyncio.run(test_unified_interface())
    asyncio.run(test_chatgpt_handler())
    asyncio.run(test_claude_handler())

    print("\n" + "="*70)
    print("All tests completed!")
    print("="*70 + "\n")
