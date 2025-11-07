"""
BACOWR API
Per NEXT-A1-ENGINE-ADDENDUM.md § 6

Main entrypoint for running backlink jobs.
Supports mock mode for testing without external dependencies.
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

from .qc import QualityController, QCStatus
from .engine import BacklinkStateMachine, State, ExecutionLogger


def generate_job_id() -> str:
    """Generate unique job ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"job_{timestamp}_{unique_id}"


def load_mock_package() -> dict:
    """Load mock BacklinkJobPackage from examples"""
    example_path = Path(__file__).parent.parent / 'examples' / 'example_job_package.json'
    with open(example_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_mock_article(job_package: dict) -> str:
    """
    Generate mock article for testing.

    Returns markdown article with proper structure.
    """
    publisher = job_package.get('input_minimal', {}).get('publisher_domain', 'Unknown')
    target = job_package.get('input_minimal', {}).get('target_url', 'Unknown')
    anchor = job_package.get('input_minimal', {}).get('anchor_text', 'Unknown')
    language = job_package.get('generation_constraints', {}).get('language', 'sv')

    # Swedish template
    if language == 'sv':
        article = f"""# Guide: Hitta bästa lösningen för dina behov

När man letar efter rätt lösning är det viktigt att jämföra olika alternativ. I denna guide går vi igenom vad du bör tänka på.

## Vad ska du tänka på?

Det finns flera faktorer som spelar in när du väljer. Här är de viktigaste:

1. **Pris och villkor** - Jämför alltid olika alternativ
2. **Kvalitet** - Läs recensioner och erfarenheter
3. **Support** - Hur bra är kundtjänsten?

## Jämförelse av alternativ

När vi tittar på marknaden ser vi att det finns många olika alternativ. Ett av de mer intressanta är [{anchor}]({target}) som erbjuder en komplett lösning.

### Fördelar och nackdelar

Varje lösning har sina för- och nackdelar. Det är viktigt att du själv gör research och hittar vad som passar dina specifika behov.

#### Nyckelfaktorer att överväga

- Kostnad i relation till värde
- Användarupplevelse och gränssnitt
- Tillgänglighet och support
- Säkerhet och integritet
- Skalbarhet för framtida behov

## Expertråd

Konsumentverket rekommenderar att alltid:
- Läsa villkoren noga
- Jämföra flera alternativ
- Söka oberoende recensioner

## Sammanfattning

Att välja rätt lösning kräver research och jämförelse. Ta dig tid att utvärdera olika alternativ baserat på dina specifika behov.

### Källor och referenser

- Konsumentverket.se - "Guide till smarta köp"
- Wikipedia.org - Bakgrundsinformation om branschen

---

*Denna artikel är genererad för demonstrationsändamål. Rådgör alltid med expert innan viktiga beslut.*

*Wordcount: Cirka 250 ord (mock, i produktion: 900+)*
"""
    else:
        # English template
        article = f"""# Complete Guide: Finding the Best Solution

Finding the right solution requires careful comparison. This guide covers what you need to know.

## Key Considerations

Several factors matter when choosing:

1. **Price and terms** - Always compare
2. **Quality** - Read reviews
3. **Support** - Check customer service

## Comparing Options

The market offers many alternatives. One interesting option is [{anchor}]({target}) which provides a complete solution.

### Pros and Cons

Every solution has trade-offs. Research thoroughly to find what fits your specific needs.

## Expert Advice

Consumer protection agencies recommend:
- Read terms carefully
- Compare multiple options
- Seek independent reviews

*Mock article - Production would be 900+ words*
"""

    return article


def build_mock_job_package(publisher_domain: str, target_url: str, anchor_text: str) -> dict:
    """
    Build a mock BacklinkJobPackage with realistic data.

    Args:
        publisher_domain: Publisher domain
        target_url: Target URL
        anchor_text: Anchor text

    Returns:
        Complete BacklinkJobPackage dict
    """
    job_id = generate_job_id()

    return {
        'job_meta': {
            'job_id': job_id,
            'created_at': datetime.utcnow().isoformat(),
            'spec_version': 'Next-A1-SERP-First-v1',
            'mode': 'mock'
        },
        'input_minimal': {
            'publisher_domain': publisher_domain,
            'target_url': target_url,
            'anchor_text': anchor_text
        },
        'publisher_profile': {
            'domain': publisher_domain,
            'detected_language': 'sv',
            'topic_focus': ['mock_topic'],
            'tone_class': 'consumer_magazine'
        },
        'target_profile': {
            'url': target_url,
            'http_status': 200,
            'detected_language': 'sv',
            'title': 'Mock Target Page',
            'core_entities': ['Mock Entity'],
            'core_topics': ['mock_topic'],
            'core_offer': 'Mock offer description'
        },
        'anchor_profile': {
            'proposed_text': anchor_text,
            'type_hint': None,
            'llm_classified_type': 'partial',
            'llm_intent_hint': 'commercial_research'
        },
        'serp_research_extension': {
            'main_query': 'mock query',
            'cluster_queries': ['mock cluster 1'],
            'queries_rationale': 'Mock rationale',
            'serp_sets': [],
            'data_confidence': 'medium'
        },
        'intent_extension': {
            'serp_intent_primary': 'commercial_research',
            'serp_intent_secondary': ['info_primary'],
            'target_page_intent': 'transactional_with_info_support',
            'anchor_implied_intent': 'commercial_research',
            'publisher_role_intent': 'info_primary',
            'intent_alignment': {
                'anchor_vs_serp': 'aligned',
                'target_vs_serp': 'partial',
                'publisher_vs_serp': 'aligned',
                'overall': 'aligned'
            },
            'recommended_bridge_type': 'pivot',
            'recommended_article_angle': 'Mock angle',
            'required_subtopics': ['subtopic1'],
            'forbidden_angles': [],
            'notes': {
                'rationale': 'Mock rationale',
                'data_confidence': 'medium'
            }
        },
        'generation_constraints': {
            'language': 'sv',
            'min_word_count': 900,
            'max_anchor_usages': 2,
            'anchor_policy': 'Ingen anchor i H1/H2, mittsektion'
        }
    }


def run_backlink_job(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    mock: bool = True,
    output_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run complete Next-A1 backlink job pipeline.

    Args:
        publisher_domain: Domain where content will be published
        target_url: URL to link to
        anchor_text: Anchor text for link
        mock: Run in mock mode (default: True, no external APIs)
        output_dir: Output directory (default: storage/output/)

    Returns:
        {
            'job_id': str,
            'status': 'DELIVERED' | 'BLOCKED' | 'ABORTED',
            'job_package': dict,
            'article': str,
            'qc_report': dict,
            'execution_log': dict
        }
    """
    # Initialize
    job_id = generate_job_id()
    sm = BacklinkStateMachine(job_id)
    logger = ExecutionLogger(job_id, output_dir)

    try:
        # RECEIVE → PREFLIGHT
        logger.log_info(f"Starting job {job_id}", {
            'publisher': publisher_domain,
            'target': target_url,
            'anchor': anchor_text,
            'mock': mock
        })

        sm.transition(State.PREFLIGHT, {'mock_mode': mock})
        logger.log_state_transition('RECEIVE', 'PREFLIGHT', {'mock': mock})

        # Build job package
        if mock:
            job_package = build_mock_job_package(publisher_domain, target_url, anchor_text)
            # Override job_id
            job_package['job_meta']['job_id'] = job_id
        else:
            # Real implementation would call:
            # - PageProfiler
            # - SERPResearcher
            # - IntentAnalyzer
            raise NotImplementedError("Real mode not yet implemented. Use mock=True.")

        logger.log_info("Job package built", {'mode': 'mock' if mock else 'real'})

        # PREFLIGHT → WRITE
        sm.transition(State.WRITE)
        logger.log_state_transition('PREFLIGHT', 'WRITE')

        # Generate article
        if mock:
            article = generate_mock_article(job_package)
        else:
            raise NotImplementedError("Real WriterEngine not yet implemented.")

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
                'execution_log': logger.get_log()
            }

        logger.log_info("Article generated", {'length': len(article)})

        # WRITE → QC
        sm.transition(State.QC)
        logger.log_state_transition('WRITE', 'QC')

        # Run QC
        qc = QualityController()
        qc_report = qc.validate(job_package, article)
        logger.log_qc_result(qc_report.to_dict())

        # Handle QC result
        if qc_report.status == QCStatus.BLOCKED:
            logger.log_warning("QC blocked - attempting RESCUE")

            # QC → RESCUE
            sm.transition(State.RESCUE, {'reason': 'qc_blocked'})
            logger.log_state_transition('QC', 'RESCUE', {'qc_status': 'BLOCKED'})

            # Attempt AutoFix
            fixed_package, fixed_article, fix_logs = qc.auto_fix_once(job_package, article, qc_report)

            if fix_logs:
                logger.log_autofix([log.to_dict() for log in fix_logs])
                job_package = fixed_package
                article = fixed_article

                # Check for loop after fix
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
                        'execution_log': logger.get_log()
                    }

                # Re-run QC
                sm.transition(State.QC, {'autofix_applied': True})
                logger.log_state_transition('RESCUE', 'QC', {'autofix': True})

                qc_report = qc.validate(job_package, article)
                logger.log_qc_result(qc_report.to_dict())

                if qc_report.status == QCStatus.BLOCKED:
                    # Still blocked after fix
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
                        'execution_log': logger.get_log()
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

        logger.log_info("Outputs saved", {
            'job_package': str(job_package_path),
            'article': str(article_path),
            'qc_report': str(qc_report_path),
            'execution_log': str(execution_log_path)
        })

        return {
            'job_id': job_id,
            'status': 'DELIVERED',
            'job_package': job_package,
            'article': article,
            'qc_report': qc_report.to_dict(),
            'execution_log': sm.get_execution_log(),
            'output_files': {
                'job_package': str(job_package_path),
                'article': str(article_path),
                'qc_report': str(qc_report_path),
                'execution_log': str(execution_log_path)
            }
        }

    except Exception as e:
        # Handle errors
        logger.log_error(str(e), type(e).__name__)
        sm.transition(State.ABORT, {'reason': 'exception', 'error': str(e)})
        logger.finalize('ABORT', 'exception')

        return {
            'job_id': job_id,
            'status': 'ABORTED',
            'error': str(e),
            'execution_log': logger.get_log()
        }
