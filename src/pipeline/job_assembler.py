"""
BacklinkJobPackage Assembler - Assembles and validates complete job packages.

This module orchestrates all analysis steps and creates the final BacklinkJobPackage
that will be consumed by the Writer Engine.

Central component that ensures all required data is collected and validated.
"""

import uuid
from datetime import datetime
from typing import Dict, Tuple

from ..modules.publisher_profiler import PublisherProfiler, PublisherProfile
from ..modules.target_profiler import TargetProfiler, TargetProfile
from ..modules.anchor_classifier import AnchorClassifier, AnchorProfile
from ..modules.query_selector import QuerySelector, QuerySet
from ..modules.serp_fetcher import SerpFetcher
from ..modules.serp_analyzer import SerpAnalyzer, SerpResearchExtension
from ..modules.intent_modeler import IntentModeler, IntentExtension
from ..utils.logger import get_logger
from ..utils.validation import get_validator

logger = get_logger(__name__)


class BacklinkJobAssembler:
    """
    Assembles complete BacklinkJobPackages from minimal input.

    Takes three inputs (publisher_domain, target_url, anchor_text) and
    orchestrates all analysis steps to create a validated job package.
    """

    def __init__(
        self,
        serp_mode: str = "mock",
        serp_api_key: str = None
    ):
        """
        Initialize job assembler with required modules.

        Args:
            serp_mode: "mock" or "api" for SERP fetching
            serp_api_key: Optional API key for real SERP fetching
        """
        self.publisher_profiler = PublisherProfiler()
        self.target_profiler = TargetProfiler()
        self.anchor_classifier = AnchorClassifier()
        self.query_selector = QuerySelector()
        self.serp_fetcher = SerpFetcher(mode=serp_mode, api_key=serp_api_key)
        self.serp_analyzer = SerpAnalyzer()
        self.intent_modeler = IntentModeler()
        self.validator = get_validator()

        logger.info("BacklinkJobAssembler initialized", serp_mode=serp_mode)

    def assemble_job_package(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        anchor_type_hint: str = None,
        min_word_count: int = 900,
        language: str = None
    ) -> Tuple[Dict, bool, str]:
        """
        Assemble a complete BacklinkJobPackage from minimal input.

        This is the main entry point that orchestrates the entire analysis pipeline.

        Args:
            publisher_domain: Domain where content will be published
            target_url: URL that will receive the backlink
            anchor_text: Proposed anchor text
            anchor_type_hint: Optional hint about anchor type
            min_word_count: Minimum word count for generated content
            language: Optional language override

        Returns:
            Tuple of (job_package_dict, is_valid, error_message)

        Pipeline steps:
        1. Profile target page
        2. Profile publisher site
        3. Classify anchor
        4. Select queries
        5. Fetch SERP data
        6. Analyze SERP
        7. Model intent alignment
        8. Assemble package
        9. Validate
        """
        logger.info(
            "Assembling job package",
            publisher=publisher_domain,
            target=target_url[:50],
            anchor=anchor_text[:30]
        )

        try:
            # Step 1: Profile target page
            logger.debug("Step 1: Profiling target")
            target_profile = self.target_profiler.profile_target(target_url)

            if target_profile.http_status != 200:
                error_msg = f"Target URL returned HTTP {target_profile.http_status}"
                logger.error("Target profiling failed", error=error_msg)
                return None, False, error_msg

            # Step 2: Profile publisher
            logger.debug("Step 2: Profiling publisher")
            publisher_profile = self.publisher_profiler.profile_publisher(publisher_domain)

            # Step 3: Classify anchor
            logger.debug("Step 3: Classifying anchor")
            anchor_profile = self.anchor_classifier.classify_anchor(
                anchor_text,
                target_title=target_profile.title,
                target_entities=target_profile.core_entities,
                type_hint=anchor_type_hint
            )

            # Step 4: Select queries
            logger.debug("Step 4: Selecting queries")
            query_set = self.query_selector.select_queries(target_profile, anchor_profile)

            # Step 5: Fetch SERP data
            logger.debug("Step 5: Fetching SERP data")
            serp_sets = []

            # Fetch for main query
            main_serp = self.serp_fetcher.fetch_serp(
                query_set.main_query,
                language=language or target_profile.detected_language
            )
            serp_sets.append(main_serp)

            # Fetch for cluster queries
            for cluster_query in query_set.cluster_queries:
                cluster_serp = self.serp_fetcher.fetch_serp(
                    cluster_query,
                    language=language or target_profile.detected_language
                )
                serp_sets.append(cluster_serp)

            # Step 6: Analyze SERP
            logger.debug("Step 6: Analyzing SERP data")
            serp_research = self.serp_analyzer.analyze_full_research(query_set, serp_sets)

            # Step 7: Model intent alignment
            logger.debug("Step 7: Modeling intent alignment")
            intent_extension = self.intent_modeler.model_intent(
                publisher_profile,
                target_profile,
                anchor_profile,
                serp_research
            )

            # Step 8: Assemble package
            logger.debug("Step 8: Assembling job package")
            job_package = self._build_job_package(
                publisher_profile,
                target_profile,
                anchor_profile,
                serp_research,
                intent_extension,
                min_word_count,
                language or target_profile.detected_language
            )

            # Step 9: Validate
            logger.debug("Step 9: Validating job package")
            is_valid, error_msg = self.validator.validate_job_package(job_package)

            if not is_valid:
                logger.error("Job package validation failed", error=error_msg)
                return job_package, False, error_msg

            logger.info(
                "Job package assembled successfully",
                job_id=job_package["job_meta"]["job_id"],
                bridge_type=intent_extension.recommended_bridge_type
            )

            return job_package, True, None

        except Exception as e:
            error_msg = f"Failed to assemble job package: {str(e)}"
            logger.error("Job assembly failed", error=error_msg, exc_info=True)
            return None, False, error_msg

    def _build_job_package(
        self,
        publisher_profile: PublisherProfile,
        target_profile: TargetProfile,
        anchor_profile: AnchorProfile,
        serp_research: SerpResearchExtension,
        intent_extension: IntentExtension,
        min_word_count: int,
        language: str
    ) -> Dict:
        """
        Build the complete job package dictionary.

        Returns dict matching backlink_job_package.schema.json structure.
        """
        job_id = str(uuid.uuid4())

        # Build job_meta
        job_meta = {
            "job_id": job_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "spec_version": "Next-A1-SERP-First-v1",
            "notes": f"Auto-generated job package for {target_profile.url}"
        }

        # Build input_minimal
        input_minimal = {
            "publisher_domain": publisher_profile.domain,
            "target_url": target_profile.url,
            "anchor_text": anchor_profile.proposed_text
        }

        # Convert profiles to job package format
        publisher_dict = self.publisher_profiler.to_job_package_format(publisher_profile)
        target_dict = self.target_profiler.to_job_package_format(target_profile)
        anchor_dict = self.anchor_classifier.to_job_package_format(anchor_profile)

        # Convert extensions to job package format
        serp_research_dict = self.serp_analyzer.to_job_package_format(serp_research)
        intent_extension_dict = self.intent_modeler.to_job_package_format(intent_extension)

        # Build generation_constraints
        generation_constraints = {
            "language": language,
            "min_word_count": min_word_count,
            "max_anchor_usages": 2,
            "anchor_policy": "Ingen anchor i H1/H2, placera i mittsektionens första relevanta stycken",
            "tone_override": None  # Use publisher_profile.tone_class by default
        }

        # Assemble final package
        job_package = {
            "job_meta": job_meta,
            "input_minimal": input_minimal,
            "publisher_profile": publisher_dict,
            "target_profile": target_dict,
            "anchor_profile": anchor_dict,
            "serp_research_extension": serp_research_dict,
            "intent_extension": intent_extension_dict,
            "generation_constraints": generation_constraints
        }

        return job_package

    def save_job_package(self, job_package: Dict, output_path: str) -> None:
        """
        Save job package to JSON file.

        Args:
            job_package: Complete job package dict
            output_path: Path to save JSON file
        """
        import json
        from pathlib import Path

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(job_package, f, ensure_ascii=False, indent=2)

        logger.info("Job package saved", path=str(output_file))
