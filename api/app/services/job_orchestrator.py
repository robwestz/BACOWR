"""
Job Orchestrator Service - BACOWR Demo Environment

This service orchestrates the complete 9-step backlink content generation pipeline,
providing a clean management-friendly interface to the BACOWR system.

Part of the BACOWR Demo API - Production-ready wrapper over core src/ modules.
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

# Import core BACOWR modules
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.profiling.page_profiler import PageProfiler
from src.profiling.llm_enhancer import LLMEnhancer
from src.analysis.intent_analyzer import IntentAnalyzer
from src.qc import QualityController, QCStatus


class BacklinkJobPackage:
    """
    Standard job package structure for BACOWR pipeline.

    Contains all context, profiles, and constraints needed for content generation.
    """

    def __init__(
        self,
        job_id: str,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        llm_provider: str = 'anthropic'
    ):
        self.job_id = job_id
        self.publisher_domain = publisher_domain
        self.target_url = target_url
        self.anchor_text = anchor_text
        self.llm_provider = llm_provider

        # Will be populated by orchestrator
        self.publisher_profile: Optional[Dict[str, Any]] = None
        self.target_profile: Optional[Dict[str, Any]] = None
        self.anchor_profile: Optional[Dict[str, Any]] = None
        self.serp_research: Optional[Dict[str, Any]] = None
        self.intent_extension: Optional[Dict[str, Any]] = None
        self.generation_constraints: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'job_meta': {
                'job_id': self.job_id,
                'created_at': datetime.utcnow().isoformat(),
                'spec_version': 'Next-A1-SERP-First-v1',
                'llm_provider': self.llm_provider
            },
            'input_minimal': {
                'publisher_domain': self.publisher_domain,
                'target_url': self.target_url,
                'anchor_text': self.anchor_text
            },
            'publisher_profile': self.publisher_profile,
            'target_profile': self.target_profile,
            'anchor_profile': self.anchor_profile,
            'serp_research_extension': self.serp_research,
            'intent_extension': self.intent_extension,
            'generation_constraints': self.generation_constraints
        }


class BacklinkJobOrchestrator:
    """
    Main orchestrator for the BACOWR backlink content generation pipeline.

    Executes the complete 9-step process:
    1. Profile Target URL
    2. Profile Publisher Domain
    3. Classify Anchor Text
    4. Generate SERP Queries
    5. Fetch SERP Data
    6. Analyze Intent Alignment
    7. Generate Content (LLM)
    8. Validate Quality (QC)
    9. Package Results

    This is a clean, production-ready facade over the core BACOWR system,
    designed for management demos and API integration.
    """

    def __init__(
        self,
        enable_llm_profiling: bool = True,
        enable_qc_validation: bool = True,
        output_directory: Optional[str] = None
    ):
        """
        Initialize the job orchestrator.

        Args:
            enable_llm_profiling: Use LLM for enhanced profiling (recommended)
            enable_qc_validation: Run quality control validation
            output_directory: Directory for saving outputs (default: storage/output)
        """
        self.enable_llm_profiling = enable_llm_profiling
        self.enable_qc_validation = enable_qc_validation
        self.output_directory = output_directory or str(
            Path(__file__).parent.parent.parent.parent / 'storage' / 'output'
        )

        # Initialize core components
        self.profiler = PageProfiler()
        self.llm_enhancer: Optional[LLMEnhancer] = None
        self.intent_analyzer = IntentAnalyzer()
        self.qc_controller = QualityController() if enable_qc_validation else None

    def execute(
        self,
        publisher_domain: str,
        target_url: str,
        anchor_text: str,
        llm_provider: str = 'anthropic',
        country: str = 'se'
    ) -> Dict[str, Any]:
        """
        Execute the complete 9-step backlink job pipeline.

        Args:
            publisher_domain: Domain where content will be published
            target_url: URL to create backlink to
            anchor_text: Anchor text for the link
            llm_provider: LLM provider to use ('anthropic', 'openai', 'google')
            country: Country code for SERP research (default: 'se')

        Returns:
            Complete job result with package, article, and QC report
            {
                'job_id': str,
                'status': 'DELIVERED' | 'BLOCKED' | 'FAILED',
                'job_package': BacklinkJobPackage,
                'article': str,
                'qc_report': dict,
                'execution_log': list,
                'metrics': dict
            }
        """
        # Generate unique job ID
        job_id = self._generate_job_id()

        # Initialize execution log
        execution_log = []
        metrics = {
            'started_at': datetime.utcnow().isoformat(),
            'pipeline_steps_completed': 0,
            'total_steps': 9
        }

        try:
            execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'step': 'INIT',
                'message': f'Starting job {job_id}',
                'details': {
                    'publisher': publisher_domain,
                    'target': target_url,
                    'anchor': anchor_text,
                    'llm_provider': llm_provider
                }
            })

            # Create job package
            package = BacklinkJobPackage(
                job_id=job_id,
                publisher_domain=publisher_domain,
                target_url=target_url,
                anchor_text=anchor_text,
                llm_provider=llm_provider
            )

            # STEP 1: Profile Target URL
            execution_log.append(self._log_step(1, 'Profile Target URL'))
            package.target_profile = self._profile_target(target_url)
            metrics['pipeline_steps_completed'] = 1

            # STEP 2: Profile Publisher Domain
            execution_log.append(self._log_step(2, 'Profile Publisher Domain'))
            package.publisher_profile = self._profile_publisher(publisher_domain)
            metrics['pipeline_steps_completed'] = 2

            # STEP 3: Classify Anchor Text
            execution_log.append(self._log_step(3, 'Classify Anchor Text'))
            package.anchor_profile = self._classify_anchor(
                anchor_text,
                package.target_profile,
                llm_provider
            )
            metrics['pipeline_steps_completed'] = 3

            # STEP 4-5: Generate SERP Queries and Fetch Data
            execution_log.append(self._log_step(4, 'Generate SERP Queries'))
            execution_log.append(self._log_step(5, 'Fetch SERP Data'))

            # Import SERP service here to avoid circular dependency
            from .serp_api import SerpAPIIntegration
            serp_service = SerpAPIIntegration()

            package.serp_research = serp_service.build_serp_research_extension(
                target_profile=package.target_profile,
                anchor_text=anchor_text,
                country=country
            )
            metrics['pipeline_steps_completed'] = 5

            # STEP 6: Analyze Intent Alignment
            execution_log.append(self._log_step(6, 'Analyze Intent Alignment'))
            package.intent_extension = self.intent_analyzer.analyze(
                target_profile=package.target_profile,
                publisher_profile=package.publisher_profile,
                anchor_profile=package.anchor_profile,
                serp_research=package.serp_research
            )
            metrics['pipeline_steps_completed'] = 6

            # Set generation constraints
            package.generation_constraints = {
                'language': package.target_profile.get('detected_language', 'sv'),
                'min_word_count': 900,
                'max_anchor_usages': 2,
                'anchor_policy': 'Ingen anchor i H1/H2, mittsektion'
            }

            # STEP 7: Generate Content
            execution_log.append(self._log_step(7, 'Generate Content (LLM)'))

            # Import writer here to avoid circular dependency
            from .writer_engine import WriterEngine
            writer = WriterEngine(llm_provider=llm_provider)

            article, generation_metrics = writer.generate_article(
                context=package.to_dict(),
                strategy='expert'
            )
            metrics['generation'] = generation_metrics
            metrics['pipeline_steps_completed'] = 7

            # STEP 8: Validate Quality (QC)
            execution_log.append(self._log_step(8, 'Validate Quality (QC)'))
            qc_report = None

            if self.qc_controller:
                from .qc_validator import NextA1QCValidator
                qc_validator = NextA1QCValidator()
                qc_report = qc_validator.validate(
                    article=article,
                    job_package=package.to_dict()
                )
                metrics['pipeline_steps_completed'] = 8
            else:
                qc_report = {
                    'status': 'PASS',
                    'message': 'QC validation disabled'
                }

            # STEP 9: Package Results
            execution_log.append(self._log_step(9, 'Package Results'))
            metrics['pipeline_steps_completed'] = 9
            metrics['completed_at'] = datetime.utcnow().isoformat()

            # Determine final status
            if qc_report.get('overall_score', 100) >= 80:
                status = 'DELIVERED'
            elif qc_report.get('overall_score', 100) >= 50:
                status = 'WARNING'
            else:
                status = 'BLOCKED'

            return {
                'job_id': job_id,
                'status': status,
                'job_package': package.to_dict(),
                'article': article,
                'qc_report': qc_report,
                'execution_log': execution_log,
                'metrics': metrics
            }

        except Exception as e:
            execution_log.append({
                'timestamp': datetime.utcnow().isoformat(),
                'step': 'ERROR',
                'message': f'Pipeline failed: {str(e)}',
                'error_type': type(e).__name__
            })

            return {
                'job_id': job_id,
                'status': 'FAILED',
                'error': str(e),
                'execution_log': execution_log,
                'metrics': metrics
            }

    def _generate_job_id(self) -> str:
        """Generate unique job ID"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        return f"job_{timestamp}_{unique_id}"

    def _log_step(self, step_number: int, step_name: str) -> Dict[str, Any]:
        """Create log entry for pipeline step"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'step': f'STEP_{step_number}',
            'message': f'Step {step_number}/9: {step_name}',
            'status': 'started'
        }

    def _profile_target(self, target_url: str) -> Dict[str, Any]:
        """
        Profile target URL to extract entities, topics, and content structure.

        Args:
            target_url: URL to profile

        Returns:
            Target profile with entities, topics, and metadata
        """
        profile = self.profiler.profile_target_page(target_url)

        # Enhance with LLM if enabled
        if self.enable_llm_profiling:
            try:
                if not self.llm_enhancer:
                    self.llm_enhancer = LLMEnhancer()

                enhanced_entities = self.llm_enhancer.extract_entities_and_topics(
                    profile.get('title', ''),
                    profile.get('main_content_excerpt', ''),
                    profile.get('h2_h3_sample', [])
                )

                if enhanced_entities.get('entities'):
                    profile['core_entities'] = enhanced_entities['entities']
                if enhanced_entities.get('topics'):
                    profile['core_topics'] = enhanced_entities['topics']

                profile['llm_enhanced'] = True

            except Exception as e:
                print(f"LLM enhancement failed: {e}")
                profile['llm_enhanced'] = False

        return profile

    def _profile_publisher(self, publisher_domain: str) -> Dict[str, Any]:
        """
        Profile publisher domain to understand tone, style, and editorial guidelines.

        Args:
            publisher_domain: Domain to profile

        Returns:
            Publisher profile with tone, style, and constraints
        """
        profile = self.profiler.profile_publisher_domain(publisher_domain)

        # Enhance with LLM if enabled
        if self.enable_llm_profiling and profile.get('about_excerpt'):
            try:
                if not self.llm_enhancer:
                    self.llm_enhancer = LLMEnhancer()

                tone_analysis = self.llm_enhancer.analyze_publisher_tone(
                    [profile.get('about_excerpt', '')],
                    profile.get('about_excerpt')
                )

                profile['tone_class'] = tone_analysis.get('tone_class', profile.get('tone_class'))
                profile['allowed_commerciality'] = tone_analysis.get('commerciality', 'medium')
                profile['llm_enhanced'] = True

            except Exception as e:
                print(f"LLM enhancement failed: {e}")
                profile['llm_enhanced'] = False

        return profile

    def _classify_anchor(
        self,
        anchor_text: str,
        target_profile: Dict[str, Any],
        llm_provider: str
    ) -> Dict[str, Any]:
        """
        Classify anchor text type and risk level.

        Args:
            anchor_text: Anchor text to classify
            target_profile: Target profile for context
            llm_provider: LLM provider to use

        Returns:
            Anchor classification with type, intent, and risk assessment
        """
        anchor_profile = {
            'proposed_text': anchor_text,
            'type_hint': None,
            'llm_classified_type': 'partial',
            'llm_intent_hint': None,
            'llm_confidence': 0.0
        }

        # Enhance with LLM if enabled
        if self.enable_llm_profiling:
            try:
                if not self.llm_enhancer:
                    self.llm_enhancer = LLMEnhancer(provider=llm_provider)

                classification = self.llm_enhancer.classify_anchor(
                    anchor_text,
                    target_profile.get('title'),
                    f"Target: {target_profile.get('url', '')}"
                )

                anchor_profile['llm_classified_type'] = classification.get('type', 'partial')
                anchor_profile['llm_intent_hint'] = classification.get('intent')
                anchor_profile['llm_confidence'] = classification.get('confidence', 0.0)
                anchor_profile['llm_reasoning'] = classification.get('reasoning', '')

            except Exception as e:
                print(f"Anchor classification failed: {e}")

        return anchor_profile
