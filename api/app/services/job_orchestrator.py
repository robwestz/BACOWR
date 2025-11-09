"""
BacklinkContent Job Orchestrator.

Orchestrates complete pipeline from INPUT (publisher + target + anchor) to OUTPUT (article + QC report).

Pipeline Steps:
1. Profile Target URL
2. Profile Publisher Domain
3. Classify Anchor
4. Generate Queries
5. Fetch SERP Data
6. Analyze Intent
7. Generate Content (Writer Engine)
8. Validate QC
9. Package Results
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BacklinkJobOrchestrator:
    """
    Orchestrates complete backlink content generation pipeline.

    Follows backlink_engine_ideal_flow.md and Next-A1 specification.
    """

    def __init__(
        self,
        serp_api_key: Optional[str] = None,
        llm_provider: str = "anthropic",
        llm_api_key: Optional[str] = None
    ):
        """
        Initialize orchestrator.

        Args:
            serp_api_key: SerpAPI key for SERP research
            llm_provider: LLM provider (anthropic/openai/google)
            llm_api_key: LLM API key
        """
        self.serp_api_key = serp_api_key
        self.llm_provider = llm_provider
        self.llm_api_key = llm_api_key

    async def execute(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        user_id: str,
        country: str = "se",
        language: str = "sv",
        writing_strategy: str = "expert"
    ) -> Dict[str, Any]:
        """
        Execute complete backlink content generation pipeline.

        Args:
            publisher_domain: Publisher domain (e.g., "privatekonomi.se")
            target_url: Target URL to link to
            anchor_text: Anchor text for link
            user_id: User ID for tracking
            country: Country code for SERP
            language: Language code
            writing_strategy: Writing strategy (standard/expert/comprehensive)

        Returns:
            Complete BacklinkJobPackage with article, extensions, and QC report
        """
        logger.info(
            f"Starting job orchestration: {publisher_domain} -> {target_url} "
            f"(anchor: {anchor_text})"
        )

        result = {
            "job_id": self._generate_job_id(),
            "user_id": user_id,
            "input": {
                "publisher_domain": publisher_domain,
                "target_url": target_url,
                "anchor_text": anchor_text,
                "country": country,
                "language": language,
                "writing_strategy": writing_strategy
            },
            "started_at": datetime.utcnow().isoformat(),
            "status": "processing"
        }

        try:
            # Step 1: Profile Target
            logger.info("Step 1: Profiling target URL...")
            target_profile = await self._profile_target(target_url, language)
            result["target_profile"] = target_profile

            # Step 2: Profile Publisher
            logger.info("Step 2: Profiling publisher domain...")
            publisher_profile = await self._profile_publisher(publisher_domain, language)
            result["publisher_profile"] = publisher_profile

            # Step 3: Classify Anchor
            logger.info("Step 3: Classifying anchor text...")
            anchor_profile = self._classify_anchor(anchor_text, target_profile)
            result["anchor_profile"] = anchor_profile

            # Step 4: Generate Queries
            logger.info("Step 4: Generating search queries...")
            main_query, cluster_queries, queries_rationale = self._generate_queries(
                target_profile, anchor_text
            )
            result["queries"] = {
                "main_query": main_query,
                "cluster_queries": cluster_queries,
                "rationale": queries_rationale
            }

            # Step 5: SERP Research
            logger.info("Step 5: Performing SERP research...")
            serp_research = await self._perform_serp_research(
                main_query, cluster_queries, country, language
            )
            result["serp_research_extension"] = serp_research

            # Step 6: Intent Analysis
            logger.info("Step 6: Analyzing intent alignment...")
            intent_extension = self._analyze_intent(
                target_profile, publisher_profile, anchor_profile, serp_research
            )
            result["intent_extension"] = intent_extension

            # Step 7: Generate Content
            logger.info("Step 7: Generating content with Writer Engine...")
            content_result = await self._generate_content(
                target_profile,
                publisher_profile,
                anchor_profile,
                serp_research,
                intent_extension,
                writing_strategy
            )
            result["article_content"] = content_result["article_content"]
            result["links_extension"] = content_result["links_extension"]
            result["qc_extension"] = content_result["qc_extension"]

            # Step 8: QC Validation
            logger.info("Step 8: Performing QC validation...")
            qc_report = self._validate_qc(
                article_content=content_result["article_content"],
                links_extension=content_result["links_extension"],
                intent_extension=intent_extension,
                qc_extension=content_result["qc_extension"],
                serp_research_extension=serp_research
            )
            result["qc_report"] = qc_report

            # Step 9: Finalize
            result["status"] = "completed" if qc_report["status"] == "PASS" else "warning"
            result["completed_at"] = datetime.utcnow().isoformat()

            logger.info(
                f"Job orchestration completed: {result['job_id']} "
                f"(status: {result['status']}, QC: {qc_report['status']})"
            )

            return result

        except Exception as e:
            logger.error(f"Job orchestration failed: {e}", exc_info=True)
            result["status"] = "failed"
            result["error"] = str(e)
            result["completed_at"] = datetime.utcnow().isoformat()
            return result

    async def _profile_target(self, target_url: str, language: str) -> Dict[str, Any]:
        """Profile target URL."""
        from ...src.profiling.page_profiler import PageProfiler

        profiler = PageProfiler()
        return profiler.profile_target(target_url, language)

    async def _profile_publisher(self, domain: str, language: str) -> Dict[str, Any]:
        """Profile publisher domain."""
        from ...src.profiling.page_profiler import PageProfiler

        profiler = PageProfiler()
        return profiler.profile_publisher(domain, language)

    def _classify_anchor(
        self,
        anchor_text: str,
        target_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Classify anchor text."""
        # Simplified classification - can be enhanced with LLM
        anchor_lower = anchor_text.lower()

        # Determine type
        if any(word in anchor_lower for word in ['best', 'bäst', 'top']):
            anchor_type = 'partial'
        elif target_profile.get('title', '').lower() in anchor_lower:
            anchor_type = 'exact'
        elif any(entity.lower() in anchor_lower for entity in target_profile.get('core_entities', [])):
            anchor_type = 'brand'
        else:
            anchor_type = 'generic'

        # Determine intent
        if any(word in anchor_lower for word in ['buy', 'köp', 'order']):
            intent_hint = 'transactional'
        elif any(word in anchor_lower for word in ['best', 'bäst', 'compare', 'jämför']):
            intent_hint = 'commercial_research'
        else:
            intent_hint = 'info_primary'

        return {
            "proposed_text": anchor_text,
            "type_hint": anchor_type,
            "llm_classified_type": anchor_type,
            "llm_intent_hint": intent_hint
        }

    def _generate_queries(
        self,
        target_profile: Dict[str, Any],
        anchor_text: str
    ) -> tuple[str, list, str]:
        """Generate main and cluster queries."""
        from ...src.research.serp_researcher import SERPResearcher

        researcher = SERPResearcher(mock_mode=True)
        return researcher.generate_queries(target_profile, anchor_text, max_cluster_queries=3)

    async def _perform_serp_research(
        self,
        main_query: str,
        cluster_queries: list,
        country: str,
        language: str
    ) -> Dict[str, Any]:
        """Perform SERP research."""
        from ..services.serp_api import SerpAPIIntegration

        serp_service = SerpAPIIntegration(api_key=self.serp_api_key)

        try:
            return await serp_service.research(
                main_query=main_query,
                cluster_queries=cluster_queries,
                country=country,
                language=language
            )
        except Exception as e:
            logger.warning(f"SERP research failed, using fallback: {e}")
            # Fallback to mock mode
            from ...src.research.serp_researcher import SERPResearcher
            researcher = SERPResearcher(mock_mode=True)
            return researcher.research(
                target_profile={"core_entities": [main_query], "core_topics": []},
                anchor_text=main_query,
                num_results=10
            )

    def _analyze_intent(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze intent alignment."""
        from ...src.analysis.intent_analyzer import IntentAnalyzer

        analyzer = IntentAnalyzer()
        return analyzer.analyze(
            target_profile=target_profile,
            publisher_profile=publisher_profile,
            anchor_profile=anchor_profile,
            serp_research=serp_research
        )

    async def _generate_content(
        self,
        target_profile: Dict[str, Any],
        publisher_profile: Dict[str, Any],
        anchor_profile: Dict[str, Any],
        serp_research: Dict[str, Any],
        intent_extension: Dict[str, Any],
        writing_strategy: str
    ) -> Dict[str, Any]:
        """Generate content using Writer Engine."""
        from ..services.writer_engine import WriterEngine

        writer = WriterEngine(
            provider=self.llm_provider,
            api_key=self.llm_api_key
        )

        return await writer.generate(
            target_profile=target_profile,
            publisher_profile=publisher_profile,
            anchor_profile=anchor_profile,
            serp_research=serp_research,
            intent_extension=intent_extension,
            writing_strategy=writing_strategy
        )

    def _validate_qc(
        self,
        article_content: str,
        links_extension: Dict[str, Any],
        intent_extension: Dict[str, Any],
        qc_extension: Dict[str, Any],
        serp_research_extension: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate content against Next-A1 QC criteria."""
        from ..services.qc_validator import NextA1QCValidator

        validator = NextA1QCValidator()
        return validator.validate(
            article_content=article_content,
            links_extension=links_extension,
            intent_extension=intent_extension,
            qc_extension=qc_extension,
            serp_research_extension=serp_research_extension
        )

    def _generate_job_id(self) -> str:
        """Generate unique job ID."""
        import uuid
        return f"job_{uuid.uuid4().hex[:12]}"
