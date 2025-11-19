"""
Production API for BACOWR

Full production pipeline with:
- Multi-provider LLM support (OpenAI, Anthropic, Google)
- Ahrefs SERP integration
- LLM-enhanced profiling
- Error handling and retry logic
- Cost tracking
"""

import json
import uuid
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

from .qc import QualityController, QCStatus
from .engine import BacklinkStateMachine, State, ExecutionLogger
from .profiling.page_profiler import PageProfiler
from .profiling.llm_enhancer import LLMEnhancer
from .research.ahrefs_serp import AhrefsEnhancedResearcher
from .analysis.intent_analyzer import IntentAnalyzer
from .writer.production_writer import ProductionWriter, LLMProvider


def generate_job_id() -> str:
    """Generate unique job ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"job_{timestamp}_{unique_id}"


def run_production_job(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    llm_provider: Optional[str] = None,  # 'openai', 'anthropic', or 'google'
    writing_strategy: str = 'multi_stage',  # 'multi_stage' or 'single_shot'
    use_ahrefs: bool = True,
    country: str = 'se',
    output_dir: Optional[str] = None,
    enable_llm_profiling: bool = True
) -> Dict[str, Any]:
    """
    Run complete production backlink job.

    Args:
        publisher_domain: Domain where content will be published
        target_url: URL to link to
        anchor_text: Anchor text for link
        llm_provider: Preferred LLM provider (auto-detect if None)
        writing_strategy: 'multi_stage' for best quality, 'single_shot' for speed
        use_ahrefs: Use Ahrefs API for SERP (falls back to mock if unavailable)
        country: Country code for SERP data
        output_dir: Output directory (default: storage/output/)
        enable_llm_profiling: Use LLM for enhanced profiling

    Returns:
        {
            'job_id': str,
            'status': 'DELIVERED' | 'BLOCKED' | 'ABORTED',
            'job_package': dict,
            'article': str,
            'qc_report': dict,
            'execution_log': dict,
            'output_files': dict,
            'metrics': dict  # Performance and cost metrics
        }
    """
    # Initialize
    job_id = generate_job_id()
    sm = BacklinkStateMachine(job_id)
    logger = ExecutionLogger(job_id, output_dir)

    metrics = {
        'job_id': job_id,
        'started_at': datetime.utcnow().isoformat(),
        'llm_provider': llm_provider or 'auto',
        'writing_strategy': writing_strategy,
        'serp_source': 'ahrefs' if use_ahrefs else 'mock'
    }

    try:
        # RECEIVE → PREFLIGHT
        logger.log_info(f"Starting production job {job_id}", {
            'publisher': publisher_domain,
            'target': target_url,
            'anchor': anchor_text,
            'llm_provider': llm_provider,
            'strategy': writing_strategy
        })

        sm.transition(State.PREFLIGHT, {'mode': 'production'})
        logger.log_state_transition('RECEIVE', 'PREFLIGHT', {'mode': 'production'})

        # Initialize components
        logger.log_info("Initializing components", {})

        profiler = PageProfiler()

        if enable_llm_profiling:
            try:
                llm_enhancer = LLMEnhancer(provider=llm_provider)
                logger.log_info(f"LLM profiling enabled with {llm_enhancer.provider}", {})
            except:
                llm_enhancer = None
                logger.log_warning("LLM profiling unavailable, using standard profiling")
        else:
            llm_enhancer = None

        researcher = AhrefsEnhancedResearcher(fallback_to_mock=True)
        analyzer = IntentAnalyzer()

        # Profile publisher
        logger.log_info("Profiling publisher", {'domain': publisher_domain})
        publisher_profile = profiler.profile_publisher_domain(publisher_domain)

        # Enhance with LLM if available
        if llm_enhancer and publisher_profile.get('about_excerpt'):
            try:
                tone_analysis = llm_enhancer.analyze_publisher_tone(
                    [publisher_profile.get('about_excerpt', '')],
                    publisher_profile.get('about_excerpt')
                )
                publisher_profile['tone_class'] = tone_analysis.get('tone_class', publisher_profile['tone_class'])
                publisher_profile['allowed_commerciality'] = tone_analysis.get('commerciality', 'medium')
                publisher_profile['llm_enhanced'] = True
                logger.log_info("Publisher profile enhanced with LLM", {})
            except Exception as e:
                logger.log_warning(f"LLM enhancement failed: {e}")

        # Profile target
        logger.log_info("Profiling target", {'url': target_url})
        target_profile = profiler.profile_target_page(target_url)

        # Enhance entities with LLM if available
        if llm_enhancer:
            try:
                enhanced_entities = llm_enhancer.extract_entities_and_topics(
                    target_profile.get('title', ''),
                    target_profile.get('main_content_excerpt', ''),
                    target_profile.get('h2_h3_sample', [])
                )
                if enhanced_entities.get('entities'):
                    target_profile['core_entities'] = enhanced_entities['entities']
                if enhanced_entities.get('topics'):
                    target_profile['core_topics'] = enhanced_entities['topics']
                target_profile['llm_enhanced'] = True
                logger.log_info("Target profile enhanced with LLM", {})
            except Exception as e:
                logger.log_warning(f"LLM enhancement failed: {e}")

        # Analyze anchor with LLM if available
        if llm_enhancer:
            try:
                anchor_classification = llm_enhancer.classify_anchor(
                    anchor_text,
                    target_profile.get('title'),
                    f"Publisher: {publisher_domain}"
                )
                anchor_profile = {
                    'proposed_text': anchor_text,
                    'type_hint': None,
                    'llm_classified_type': anchor_classification.get('type'),
                    'llm_intent_hint': anchor_classification.get('intent'),
                    'llm_confidence': anchor_classification.get('confidence'),
                    'llm_reasoning': anchor_classification.get('reasoning')
                }
                logger.log_info("Anchor classified with LLM", anchor_classification)
            except Exception as e:
                logger.log_warning(f"LLM anchor classification failed: {e}")
                anchor_profile = {
                    'proposed_text': anchor_text,
                    'type_hint': None,
                    'llm_classified_type': 'partial',
                    'llm_intent_hint': None
                }
        else:
            anchor_profile = {
                'proposed_text': anchor_text,
                'type_hint': None,
                'llm_classified_type': 'partial',
                'llm_intent_hint': None
            }

        # SERP research
        logger.log_info("Performing SERP research", {'use_ahrefs': use_ahrefs})
        serp_research = researcher.research(target_profile, anchor_text, country=country)
        logger.log_info(f"SERP research completed via {serp_research.get('data_confidence', 'unknown')} confidence", {})

        # Intent analysis
        logger.log_info("Analyzing intent alignment", {})
        intent_extension = analyzer.analyze(
            target_profile,
            publisher_profile,
            anchor_profile,
            serp_research
        )

        # Generation constraints
        generation_constraints = {
            'language': target_profile.get('detected_language', 'sv'),
            'min_word_count': 900,
            'max_anchor_usages': 2,
            'anchor_policy': 'Ingen anchor i H1/H2, mittsektion'
        }

        # Build complete job package
        job_package = {
            'job_meta': {
                'job_id': job_id,
                'created_at': datetime.utcnow().isoformat(),
                'spec_version': 'Next-A1-SERP-First-v1',
                'mode': 'production',
                'llm_provider': llm_provider or 'auto',
                'serp_source': 'ahrefs' if use_ahrefs else 'mock'
            },
            'input_minimal': {
                'publisher_domain': publisher_domain,
                'target_url': target_url,
                'anchor_text': anchor_text
            },
            'publisher_profile': publisher_profile,
            'target_profile': target_profile,
            'anchor_profile': anchor_profile,
            'serp_research_extension': serp_research,
            'intent_extension': intent_extension,
            'generation_constraints': generation_constraints
        }

        logger.log_info("Job package built", {'mode': 'production'})

        # PREFLIGHT → WRITE
        sm.transition(State.WRITE)
        logger.log_state_transition('PREFLIGHT', 'WRITE')

        # Generate article with ProductionWriter
        logger.log_info(f"Generating article with {writing_strategy} strategy", {})

        # Check if we should use mock mode
        use_mock_mode = os.getenv('BACOWR_LLM_MODE', '').lower() == 'mock'

        # Auto-detect if no LLM API keys are available
        has_api_keys = any([
            os.getenv('ANTHROPIC_API_KEY'),
            os.getenv('OPENAI_API_KEY'),
            os.getenv('GOOGLE_API_KEY')
        ])

        if not has_api_keys and not use_mock_mode:
            logger.log_warning("No LLM API keys found - automatically enabling mock mode")
            use_mock_mode = True

        if use_mock_mode:
            logger.log_info("Using MOCK mode for article generation", {'reason': 'no_api_keys' if not has_api_keys else 'explicit'})

        writer = ProductionWriter(
            mock_mode=use_mock_mode,
            auto_fallback=True,
            enable_cost_tracking=True
        )

        article, generation_metrics = writer.generate(job_package, strategy=writing_strategy)

        metrics['generation'] = {
            'provider': generation_metrics.provider,
            'model': generation_metrics.model,
            'stages_completed': generation_metrics.stages_completed,
            'duration_seconds': generation_metrics.duration_seconds,
            'retries': generation_metrics.retries
        }

        logger.log_info(f"Article generated successfully with {generation_metrics.provider}", {
            'stages': generation_metrics.stages_completed,
            'duration': generation_metrics.duration_seconds
        })

        # Check for payload loop
        if sm.check_loop(article, 'WRITE'):
            logger.log_error("Loop detected in WRITE state", 'loop_detection')
            sm.transition(State.ABORT, {'reason': 'loop_detected'})
            logger.log_state_transition('WRITE', 'ABORT', {'reason': 'loop'})
            logger.finalize('ABORT', 'loop_detected')
            return {
                'job_id': job_id,
                'status': 'ABORTED',
                'reason': 'Loop detected',
                'execution_log': logger.get_log(),
                'metrics': metrics
            }

        # WRITE → QC
        sm.transition(State.QC)
        logger.log_state_transition('WRITE', 'QC')

        # Run QC
        qc = QualityController()
        qc_report = qc.validate(job_package, article)
        logger.log_qc_result(qc_report.to_dict())

        # Handle QC result (same as before)
        if qc_report.status == QCStatus.BLOCKED:
            logger.log_warning("QC blocked - attempting RESCUE")

            sm.transition(State.RESCUE, {'reason': 'qc_blocked'})
            logger.log_state_transition('QC', 'RESCUE', {'qc_status': 'BLOCKED'})

            fixed_package, fixed_article, fix_logs = qc.auto_fix_once(job_package, article, qc_report)

            if fix_logs:
                logger.log_autofix([log.to_dict() for log in fix_logs])
                job_package = fixed_package
                article = fixed_article

                if sm.check_loop(article, 'RESCUE'):
                    logger.log_error("Loop detected after RESCUE", 'loop_detection')
                    sm.transition(State.ABORT, {'reason': 'rescue_loop'})
                    logger.log_state_transition('RESCUE', 'ABORT', {'reason': 'loop'})
                    logger.finalize('ABORT', 'rescue_loop')
                    return {
                        'job_id': job_id,
                        'status': 'ABORTED',
                        'reason': 'No changes after RESCUE (loop)',
                        'qc_report': qc_report.to_dict(),
                        'execution_log': logger.get_log(),
                        'metrics': metrics
                    }

                sm.transition(State.QC, {'autofix_applied': True})
                logger.log_state_transition('RESCUE', 'QC', {'autofix': True})

                qc_report = qc.validate(job_package, article)
                logger.log_qc_result(qc_report.to_dict())

                if qc_report.status == QCStatus.BLOCKED:
                    sm.transition(State.ABORT, {'reason': 'qc_failed_after_rescue'})
                    logger.log_state_transition('QC', 'ABORT', {'reason': 'qc_failed'})
                    logger.finalize('ABORT', 'qc_blocked')
                    return {
                        'job_id': job_id,
                        'status': 'BLOCKED',
                        'reason': 'QC blocked even after AutoFix',
                        'job_package': job_package,
                        'article': article,
                        'qc_report': qc_report.to_dict(),
                        'execution_log': logger.get_log(),
                        'metrics': metrics
                    }

        # QC → DELIVER
        sm.transition(State.DELIVER)
        logger.log_state_transition('QC', 'DELIVER', {'qc_status': qc_report.status.value})
        logger.finalize('DELIVER', 'success')

        # Save outputs
        if output_dir:
            output_path = Path(output_dir)
        else:
            output_path = Path(__file__).parent.parent / 'storage' / 'output'

        output_path.mkdir(parents=True, exist_ok=True)

        # Save files
        job_package_path = output_path / f"{job_id}_job_package.json"
        with open(job_package_path, 'w', encoding='utf-8') as f:
            json.dump(job_package, f, indent=2, ensure_ascii=False)

        article_path = output_path / f"{job_id}_article.md"
        with open(article_path, 'w', encoding='utf-8') as f:
            f.write(article)

        qc_report_path = output_path / f"{job_id}_qc_report.json"
        with open(qc_report_path, 'w', encoding='utf-8') as f:
            json.dump(qc_report.to_dict(), f, indent=2, ensure_ascii=False)

        execution_log_path = logger.save()

        # Save metrics
        metrics['completed_at'] = datetime.utcnow().isoformat()
        metrics_path = output_path / f"{job_id}_metrics.json"
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)

        logger.log_info("Outputs saved", {
            'job_package': str(job_package_path),
            'article': str(article_path),
            'qc_report': str(qc_report_path),
            'execution_log': str(execution_log_path),
            'metrics': str(metrics_path)
        })

        return {
            'job_id': job_id,
            'status': 'DELIVERED',
            'job_package': job_package,
            'article': article,
            'qc_report': qc_report.to_dict(),
            'execution_log': sm.get_execution_log(),
            'metrics': metrics,
            'output_files': {
                'job_package': str(job_package_path),
                'article': str(article_path),
                'qc_report': str(qc_report_path),
                'execution_log': str(execution_log_path),
                'metrics': str(metrics_path)
            }
        }

    except Exception as e:
        # Handle errors
        logger.log_error(str(e), type(e).__name__)
        sm.transition(State.ABORT, {'reason': 'exception', 'error': str(e)})
        logger.finalize('ABORT', 'exception')

        metrics['completed_at'] = datetime.utcnow().isoformat()
        metrics['error'] = str(e)

        return {
            'job_id': job_id,
            'status': 'ABORTED',
            'error': str(e),
            'execution_log': logger.get_log(),
            'metrics': metrics
        }
