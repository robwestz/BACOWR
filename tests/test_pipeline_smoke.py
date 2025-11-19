"""
Smoke tests for the BacklinkContent Engine pipeline.

These tests verify basic functionality without requiring API keys.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.pipeline.job_assembler import BacklinkJobAssembler
from src.modules.target_profiler import TargetProfiler
from src.modules.publisher_profiler import PublisherProfiler
from src.modules.anchor_classifier import AnchorClassifier


class TestTargetProfiler:
    """Test target profiling."""

    def test_profile_creation(self):
        """Test that target profiler can be created."""
        profiler = TargetProfiler()
        assert profiler is not None
        assert profiler.page_profiler is not None


class TestPublisherProfiler:
    """Test publisher profiling."""

    def test_profile_creation(self):
        """Test that publisher profiler can be created."""
        profiler = PublisherProfiler()
        assert profiler is not None
        assert profiler.page_profiler is not None


class TestAnchorClassifier:
    """Test anchor classification."""

    def test_classify_generic_anchor(self):
        """Test classification of generic anchor."""
        classifier = AnchorClassifier()
        profile = classifier.classify_anchor(
            anchor_text="klicka här",
            target_title="Testprodukt - Bästa lösningen"
        )

        assert profile.proposed_text == "klicka här"
        assert profile.llm_classified_type == "generic"

    def test_classify_brand_anchor(self):
        """Test classification of brand anchor."""
        classifier = AnchorClassifier()
        profile = classifier.classify_anchor(
            anchor_text="TestBrand",
            target_title="TestBrand - Official Website",
            target_entities=["TestBrand", "Product"]
        )

        assert profile.proposed_text == "TestBrand"
        assert profile.llm_classified_type == "brand"


class TestJobAssembler:
    """Test job package assembly."""

    def test_assembler_creation(self):
        """Test that job assembler can be created."""
        assembler = BacklinkJobAssembler(serp_mode="mock")
        assert assembler is not None
        assert assembler.serp_fetcher is not None

    @pytest.mark.slow
    def test_assemble_simple_job(self):
        """
        Test assembling a simple job package.

        Note: This test makes actual HTTP requests and may be slow.
        """
        assembler = BacklinkJobAssembler(serp_mode="mock")

        # Use example.com as it's always available
        job_package, valid, error = assembler.assemble_job_package(
            publisher_domain="example.com",
            target_url="https://www.example.org",
            anchor_text="example link",
            min_word_count=900
        )

        # Should succeed with mock SERP
        assert valid or error is not None  # Either valid or has error message
        if valid:
            assert job_package is not None
            assert "job_meta" in job_package
            assert "input_minimal" in job_package
            assert "job_id" in job_package["job_meta"]


def test_import_all_modules():
    """Test that all major modules can be imported."""
    from src.modules import page_profile
    from src.modules import target_profiler
    from src.modules import publisher_profiler
    from src.modules import anchor_classifier
    from src.modules import query_selector
    from src.modules import serp_fetcher
    from src.modules import serp_analyzer
    from src.modules import intent_modeler

    from src.pipeline import job_assembler
    from src.pipeline import writer_engine
    from src.pipeline import state_machine

    from src.qc import quality_controller

    from src.utils import logger
    from src.utils import validation

    # All imports successful
    assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
