#!/usr/bin/env python3
"""
BacklinkContent Engine – Main Orchestrator

SERP-First, Intent-First Backlink Content Generation System
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

from modules import (
    TargetScraperAndProfiler,
    PublisherScraperAndProfiler,
    AnchorClassifier,
    QuerySelector,
    SerpFetcher,
    SerpAnalyzer,
    IntentAndClusterModeler,
    BacklinkJobAssembler,
    WriterEngineInterface,
    QcAndLogging,
)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('backlink_engine.log')
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/default.json") -> Dict[str, Any]:
    """Load configuration from JSON file"""
    config_file = Path(config_path)

    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        logger.warning(f"Config file {config_path} not found, using defaults")
        return {
            "timeout": 10,
            "user_agent": "BacklinkBot/1.0",
            "min_word_count": 900,
            "max_anchor_usages": 2,
            "rate_limit_delay": 0.5
        }


def generate_backlink_content(
    publisher_domain: str,
    target_url: str,
    anchor_text: str,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Main orchestration function

    Args:
        publisher_domain: Publisher domain
        target_url: Target URL to link to
        anchor_text: Proposed anchor text
        config: Configuration dict

    Returns:
        Complete result dict with job_package, content, qc_report
    """
    logger.info("="*60)
    logger.info("BacklinkContent Engine – Starting Generation")
    logger.info("="*60)
    logger.info(f"Publisher: {publisher_domain}")
    logger.info(f"Target: {target_url}")
    logger.info(f"Anchor: {anchor_text}")
    logger.info("="*60)

    try:
        # 1. Profilering (parallel i production)
        logger.info("[1/10] Profiling target...")
        target_profiler = TargetScraperAndProfiler(config)
        target_profile = target_profiler.run(target_url)

        logger.info("[2/10] Profiling publisher...")
        publisher_profiler = PublisherScraperAndProfiler(config)
        publisher_profile = publisher_profiler.run(publisher_domain)

        # 2. Anchor & Query Selection
        logger.info("[3/10] Classifying anchor...")
        anchor_classifier = AnchorClassifier(config)
        anchor_profile = anchor_classifier.run(anchor_text)

        logger.info("[4/10] Selecting queries...")
        query_selector = QuerySelector(config)
        query_selection = query_selector.run(target_profile, anchor_profile)

        queries_for_serp = [query_selection['main_query']] + query_selection['cluster_queries']

        # 3. SERP Research
        logger.info("[5/10] Fetching SERP...")
        serp_fetcher = SerpFetcher(config)
        serp_raw = serp_fetcher.run(queries_for_serp)

        logger.info("[6/10] Analyzing SERP...")
        serp_analyzer = SerpAnalyzer(config)
        serp_research_extension = serp_analyzer.run(serp_raw, query_selection)

        # 4. Intent Modeling
        logger.info("[7/10] Modeling intent...")
        intent_modeler = IntentAndClusterModeler(config)
        intent_extension = intent_modeler.run(
            target_profile,
            publisher_profile,
            anchor_profile,
            serp_research_extension
        )

        # 5. Assemble Job Package
        logger.info("[8/10] Assembling BacklinkJobPackage...")
        job_assembler = BacklinkJobAssembler(config)
        job_package = job_assembler.run(
            input_minimal={
                'publisher_domain': publisher_domain,
                'target_url': target_url,
                'anchor_text': anchor_text
            },
            target_profile=target_profile,
            publisher_profile=publisher_profile,
            anchor_profile=anchor_profile,
            serp_research_extension=serp_research_extension,
            intent_extension=intent_extension
        )

        # 6. Writer Engine
        logger.info("[9/10] Calling Writer Engine...")
        writer_engine = WriterEngineInterface(config)
        writer_output = writer_engine.run(job_package)

        # 7. QC & Logging
        logger.info("[10/10] Running QC...")
        qc = QcAndLogging(config)
        qc_report = qc.run(job_package, writer_output)

        logger.info("="*60)
        logger.info(f"Generation complete! QC Status: {qc_report['qc_status'].upper()}")
        logger.info("="*60)

        return {
            'job_package': job_package,
            'content': writer_output,
            'qc_report': qc_report
        }

    except Exception as e:
        logger.error(f"Error during generation: {e}", exc_info=True)
        raise


def save_output(result: Dict[str, Any], output_dir: str = "output") -> None:
    """Save output to files"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    job_id = result['job_package']['job_meta']['job_id']

    # Save job package
    package_file = output_path / f"{job_id}_package.json"
    with open(package_file, 'w', encoding='utf-8') as f:
        json.dump(result['job_package'], f, indent=2, ensure_ascii=False)
    logger.info(f"Saved job package: {package_file}")

    # Save content (HTML)
    html_file = output_path / f"{job_id}_content.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(result['content']['full_text_html'])
    logger.info(f"Saved HTML content: {html_file}")

    # Save content (Markdown)
    md_file = output_path / f"{job_id}_content.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(result['content']['full_text_markdown'])
    logger.info(f"Saved Markdown content: {md_file}")

    # Save QC report
    qc_file = output_path / f"{job_id}_qc_report.json"
    with open(qc_file, 'w', encoding='utf-8') as f:
        json.dump(result['qc_report'], f, indent=2, ensure_ascii=False)
    logger.info(f"Saved QC report: {qc_file}")

    # Save full output
    full_file = output_path / f"{job_id}_full_output.json"
    with open(full_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved full output: {full_file}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="BacklinkContent Engine – SERP-First Content Generation"
    )

    parser.add_argument(
        '--publisher',
        required=True,
        help='Publisher domain (e.g., example.com)'
    )

    parser.add_argument(
        '--target',
        required=True,
        help='Target URL to link to'
    )

    parser.add_argument(
        '--anchor',
        required=True,
        help='Proposed anchor text'
    )

    parser.add_argument(
        '--config',
        default='config/default.json',
        help='Path to config file (default: config/default.json)'
    )

    parser.add_argument(
        '--output',
        default='output',
        help='Output directory (default: output)'
    )

    args = parser.parse_args()

    # Load config
    config = load_config(args.config)

    # Generate content
    result = generate_backlink_content(
        publisher_domain=args.publisher,
        target_url=args.target,
        anchor_text=args.anchor,
        config=config
    )

    # Save output
    save_output(result, args.output)

    # Print summary
    print("\n" + "="*60)
    print("GENERATION SUMMARY")
    print("="*60)
    print(f"Job ID: {result['job_package']['job_meta']['job_id']}")
    print(f"QC Status: {result['qc_report']['qc_status'].upper()}")
    print(f"Flags: {len(result['qc_report']['flags'])}")

    if result['qc_report']['flags']:
        print("\nFlags:")
        for flag in result['qc_report']['flags']:
            print(f"  [{flag['severity'].upper()}] {flag['category']}: {flag['message']}")

    print("\nRecommendations:")
    for rec in result['qc_report']['recommendations']:
        print(f"  - {rec}")

    print("\nOutput files saved to:", args.output)
    print("="*60)


if __name__ == '__main__':
    main()
