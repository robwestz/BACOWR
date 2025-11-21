#!/usr/bin/env python3
"""
LEGACY SCRIPT - Can still be used via new entry point

This script can now be run through the unified entry point:
  python run_bacowr.py --mode demo --demo-type interactive

Or directly as before:
  python interactive_demo.py

---

BACOWR Interactive Demo - No Browser Required
Simulerar web-upplevelsen i terminalen
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Add BACOWR to path
sys.path.insert(0, '/home/user/BACOWR')

# Mock API keys for demo
os.environ['SERPAPI_KEY'] = 'demo_mock_key'
os.environ['ANTHROPIC_API_KEY'] = 'demo_mock_key'

def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_banner():
    """Print application banner."""
    clear_screen()
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "BACOWR BACKLINK CONTENT WRITER" + " " * 22 + "║")
    print("║" + " " * 18 + "Interactive Demo - Beta" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

def print_menu():
    """Print main menu."""
    print("\n" + "=" * 70)
    print("  MAIN MENU")
    print("=" * 70)
    print("\n  1. 📊 View System Status")
    print("  2. 🎯 Create New Job (Simulated)")
    print("  3. 📈 View QC Criteria Details")
    print("  4. 🔧 View Pipeline Architecture")
    print("  5. 💰 Cost Calculator")
    print("  6. 📚 API Documentation")
    print("  7. 🧪 Run Tests")
    print("  8. ❌ Exit")
    print("\n" + "=" * 70)

def show_system_status():
    """Show system status."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  SYSTEM STATUS")
    print("=" * 70)

    print("\n✅ Core Services:")

    try:
        from api.app.services.job_orchestrator import BacklinkJobOrchestrator
        from api.app.services.writer_engine import WriterEngine
        from api.app.services.serp_api import SerpAPIIntegration
        from api.app.services.qc_validator import NextA1QCValidator

        print("  ✓ Job Orchestrator      (438 lines)")
        print("  ✓ Writer Engine         (507 lines)")
        print("  ✓ SERP API Integration  (562 lines)")
        print("  ✓ QC Validator          (824 lines)")

        print("\n✅ Pipeline Status:")
        orchestrator = BacklinkJobOrchestrator(
            enable_llm_profiling=True,
            enable_qc_validation=True
        )
        print("  ✓ LLM Profiling: Enabled")
        print("  ✓ QC Validation: Enabled")
        print("  ✓ Full 9-step pipeline: Ready")

        print("\n✅ LLM Providers:")
        print("  ✓ Anthropic Claude   (Primary)")
        print("  ✓ OpenAI GPT         (Available)")
        print("  ✓ Google Gemini      (Available)")

        print("\n✅ Features:")
        print("  ✓ Multi-provider LLM support")
        print("  ✓ 8 automated QC criteria")
        print("  ✓ 3 bridge types (strong/pivot/wrapper)")
        print("  ✓ Real SERP integration (SerpAPI)")
        print("  ✓ Async job processing")

        print("\n📊 Performance:")
        print("  • Average time: 15-30 seconds/article")
        print("  • Average cost: $0.03-$0.09/article")
        print("  • QC pass rate: 95%+")
        print("  • Word count: 900-1500+ words")

    except Exception as e:
        print(f"\n❌ Error loading components: {e}")

    input("\n\nPress Enter to continue...")

def simulate_job_creation():
    """Simulate creating a new job."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  CREATE NEW JOB")
    print("=" * 70)

    print("\n📝 Enter job details:\n")

    # Get inputs
    publisher = input("Publisher domain (e.g., 'svd.se'): ").strip() or "svd.se"
    target = input("Target URL (e.g., 'https://example.com'): ").strip() or "https://example.com"
    anchor = input("Anchor text (e.g., 'läs mer'): ").strip() or "läs mer"

    print("\n🎯 Select LLM Provider:")
    print("  1. Anthropic Claude (Recommended)")
    print("  2. OpenAI GPT")
    print("  3. Google Gemini")
    provider_choice = input("\nChoice (1-3): ").strip() or "1"

    provider_map = {"1": "anthropic", "2": "openai", "3": "google"}
    provider = provider_map.get(provider_choice, "anthropic")

    print("\n⚙️  Select Strategy:")
    print("  1. Expert (Best quality)")
    print("  2. Balanced")
    print("  3. Fast")
    strategy_choice = input("\nChoice (1-3): ").strip() or "1"

    strategy_map = {"1": "expert", "2": "balanced", "3": "fast"}
    strategy = strategy_map.get(strategy_choice, "expert")

    # Show summary
    print("\n" + "=" * 70)
    print("  JOB SUMMARY")
    print("=" * 70)
    print(f"\n  Publisher: {publisher}")
    print(f"  Target URL: {target}")
    print(f"  Anchor: {anchor}")
    print(f"  LLM Provider: {provider.title()}")
    print(f"  Strategy: {strategy.title()}")

    # Estimate cost
    cost_map = {
        ("anthropic", "expert"): 0.06,
        ("anthropic", "balanced"): 0.04,
        ("anthropic", "fast"): 0.02,
        ("openai", "expert"): 0.09,
        ("openai", "balanced"): 0.06,
        ("openai", "fast"): 0.03,
        ("google", "expert"): 0.03,
        ("google", "balanced"): 0.02,
        ("google", "fast"): 0.01,
    }

    cost = cost_map.get((provider, strategy), 0.05)
    time_estimate = 30 if strategy == "expert" else (20 if strategy == "balanced" else 15)

    print(f"\n  Estimated Cost: ${cost:.2f}")
    print(f"  Estimated Time: ~{time_estimate} seconds")

    confirm = input("\n\nProceed? (y/n): ").strip().lower()

    if confirm == 'y':
        print("\n" + "=" * 70)
        print("  PROCESSING JOB")
        print("=" * 70)

        job_id = f"job_{int(time.time())}"

        # Simulate pipeline steps
        steps = [
            ("Profiling target URL", 2),
            ("Profiling publisher domain", 2),
            ("Classifying anchor text", 1),
            ("Generating SERP queries", 1),
            ("Fetching SERP data", 3),
            ("Analyzing intent alignment", 2),
            ("Generating content with LLM", 8),
            ("Validating quality (QC)", 2),
            ("Packaging results", 1)
        ]

        print(f"\n  Job ID: {job_id}")
        print(f"  Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        for i, (step, duration) in enumerate(steps, 1):
            print(f"  [{i}/9] {step}...", end="", flush=True)
            time.sleep(duration * 0.3)  # Faster for demo
            print(" ✓")

        print("\n" + "=" * 70)
        print("  JOB COMPLETED")
        print("=" * 70)

        # Simulate results
        qc_score = 85
        status = "DELIVERED" if qc_score >= 80 else ("WARNING" if qc_score >= 50 else "BLOCKED")

        print(f"\n  Status: {status}")
        print(f"  QC Score: {qc_score}/100")
        print(f"  Word Count: 1,234 words")
        print(f"  Processing Time: {sum(d for _, d in steps)} seconds")
        print(f"  Actual Cost: ${cost:.2f}")

        print("\n  📄 Output Files:")
        print(f"    • Article: storage/output/{job_id}_article.md")
        print(f"    • QC Report: storage/output/{job_id}_qc_report.json")
        print(f"    • Job Package: storage/output/{job_id}_package.json")

        print("\n  ✅ Article ready for review!")

    input("\n\nPress Enter to continue...")

def show_qc_criteria():
    """Show QC criteria details."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  NEXT-A1 QC CRITERIA (8 Automated Checks)")
    print("=" * 70)

    criteria = [
        {
            "name": "1. PREFLIGHT",
            "weight": "10%",
            "description": "Bridge type matches intent alignment",
            "checks": [
                "✓ Job package completeness",
                "✓ Bridge type selection (strong/pivot/wrapper)",
                "✓ Required profiles present"
            ]
        },
        {
            "name": "2. DRAFT",
            "weight": "15%",
            "description": "Structure and content quality",
            "checks": [
                "✓ Word count minimum 900 words",
                "✓ 2+ H2 sections",
                "✓ 60%+ subtopic coverage",
                "✓ Introduction and conclusion present"
            ]
        },
        {
            "name": "3. ANCHOR",
            "weight": "15%",
            "description": "Link placement and risk assessment",
            "checks": [
                "✓ NOT in H1/H2 headers (CRITICAL)",
                "✓ Max 2 anchor usages",
                "✓ Risk assessment (exact/partial/branded)",
                "✓ Middle section placement"
            ]
        },
        {
            "name": "4. TRUST",
            "weight": "10%",
            "description": "Source quality validation",
            "checks": [
                "✓ T1 sources: Gov/Academic/Major News (min 1)",
                "✓ T2 sources: Industry leaders",
                "✓ T3 sources: Niche authorities",
                "✓ T4 sources: General blogs",
                "✓ Minimum 2 total trust sources"
            ]
        },
        {
            "name": "5. INTENT",
            "weight": "15%",
            "description": "Intent alignment validation",
            "checks": [
                "✓ Overall alignment (aligned/partial/off)",
                "✓ No 'off' alignments",
                "✓ SERP intent matching"
            ]
        },
        {
            "name": "6. LSI",
            "weight": "10%",
            "description": "LSI term integration",
            "checks": [
                "✓ 6-10 LSI terms required",
                "✓ Within ±2 sentences of anchor",
                "✓ Natural integration",
                "✓ No keyword stuffing"
            ]
        },
        {
            "name": "7. FIT",
            "weight": "15%",
            "description": "Readability and tone matching",
            "checks": [
                "✓ Language validation",
                "✓ Readability LIX 35-45",
                "✓ Tone matches publisher",
                "✓ No repetition"
            ]
        },
        {
            "name": "8. COMPLIANCE",
            "weight": "10%",
            "description": "Regulatory compliance",
            "checks": [
                "✓ Auto-detect regulated verticals",
                "✓ Gambling: Stödlinjen.se disclaimer",
                "✓ Finance: Loan/credit disclaimers",
                "✓ Health: Medical advice disclaimer"
            ]
        }
    ]

    for criterion in criteria:
        print(f"\n{criterion['name']} ({criterion['weight']})")
        print(f"  {criterion['description']}")
        for check in criterion['checks']:
            print(f"    {check}")

    print("\n" + "=" * 70)
    print("  SCORING")
    print("=" * 70)
    print("\n  • PASS:     ≥80 points (green light)")
    print("  • WARNING:  50-79 points (yellow light)")
    print("  • BLOCKED:  <50 points (red light, requires fixes)")

    input("\n\nPress Enter to continue...")

def show_pipeline_architecture():
    """Show pipeline architecture."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  PIPELINE ARCHITECTURE")
    print("=" * 70)

    print("""
INPUT (3 parameters)
  ├─ publisher_domain: "svd.se"
  ├─ target_url: "https://example.com/article"
  └─ anchor_text: "läs mer här"

PIPELINE (9 automated steps)
  ├─ 1. Profile Target URL
  │    └─ Extract: title, description, topics, language
  │
  ├─ 2. Profile Publisher Domain
  │    └─ Extract: tone, style, typical topics
  │
  ├─ 3. Classify Anchor Text
  │    └─ Determine: type (exact/partial/branded)
  │
  ├─ 4. Generate SERP Queries
  │    └─ Create: main query + 2-3 cluster queries
  │
  ├─ 5. Fetch SERP Data (SerpAPI)
  │    └─ Get: top 10 results, subtopics, intent
  │
  ├─ 6. Analyze Intent Alignment
  │    └─ Determine: bridge type (strong/pivot/wrapper)
  │
  ├─ 7. Generate Content (LLM)
  │    └─ Create: 900+ word article with anchor
  │
  ├─ 8. Validate Quality (8 QC Criteria)
  │    └─ Score: 0-100, PASS/WARNING/BLOCKED
  │
  └─ 9. Package Results
       └─ Output: article + QC report + job package

OUTPUT
  ├─ article_content: Complete markdown article
  ├─ qc_report: 8 criteria validation results
  ├─ job_package: Complete BacklinkJobPackage (Next-A1)
  └─ execution_log: Detailed pipeline execution data
""")

    input("\nPress Enter to continue...")

def show_cost_calculator():
    """Show cost calculator."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  COST CALCULATOR")
    print("=" * 70)

    print("\n📊 Cost per Article:\n")
    print("  Provider          Strategy    Cost/Article  Time")
    print("  " + "-" * 60)
    print("  Anthropic Claude  expert      $0.06        ~30s")
    print("  Anthropic Claude  balanced    $0.04        ~20s")
    print("  Anthropic Claude  fast        $0.02        ~15s")
    print("  OpenAI GPT-4      expert      $0.09        ~30s")
    print("  OpenAI GPT-4      balanced    $0.06        ~20s")
    print("  OpenAI GPT-4      fast        $0.03        ~15s")
    print("  Google Gemini     expert      $0.03        ~30s")
    print("  Google Gemini     balanced    $0.02        ~20s")
    print("  Google Gemini     fast        $0.01        ~15s")

    print("\n  + SERP API: ~$0.02 per job (optional)")

    print("\n" + "=" * 70)
    print("  BATCH CALCULATOR")
    print("=" * 70)

    try:
        num_articles = int(input("\n  Number of articles: ").strip() or "10")

        print("\n  Select provider:")
        print("    1. Anthropic Claude ($0.04 avg)")
        print("    2. OpenAI GPT ($0.06 avg)")
        print("    3. Google Gemini ($0.02 avg)")

        choice = input("\n  Choice (1-3): ").strip() or "1"

        cost_map = {"1": 0.04, "2": 0.06, "3": 0.02}
        cost_per = cost_map.get(choice, 0.04)

        total_cost = num_articles * (cost_per + 0.02)  # +SERP
        total_time = num_articles * 20  # avg 20s

        print("\n" + "=" * 70)
        print("  ESTIMATE")
        print("=" * 70)
        print(f"\n  Articles: {num_articles}")
        print(f"  Cost per article: ${cost_per:.2f} + $0.02 (SERP)")
        print(f"  Total cost: ${total_cost:.2f}")
        print(f"  Total time: ~{total_time//60}m {total_time%60}s")
        print(f"  Per hour capacity: ~{3600//20} articles")

    except ValueError:
        print("\n  Invalid input!")

    input("\n\nPress Enter to continue...")

def show_api_docs():
    """Show API documentation."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  API DOCUMENTATION")
    print("=" * 70)

    print("""
📡 Base URL: http://localhost:8000/api/v1

🔐 Authentication: Bearer token (JWT)

═══════════════════════════════════════════════════════════════════════

POST /api/v1/jobs

Create new content generation job

Request:
{
  "publisher_domain": "svd.se",
  "target_url": "https://example.com",
  "anchor_text": "läs mer",
  "llm_provider": "anthropic",    // or "openai", "google", "auto"
  "writing_strategy": "expert",   // or "balanced", "fast"
  "use_ahrefs": true,
  "country": "se"
}

Response:
{
  "id": "550e8400-...",
  "status": "PENDING",
  "estimated_cost": 0.06,
  "created_at": "2025-11-12T10:30:00Z"
}

═══════════════════════════════════════════════════════════════════════

GET /api/v1/jobs/{job_id}

Get job status and results

Response:
{
  "id": "550e8400-...",
  "status": "DELIVERED",           // or "PENDING", "PROCESSING", "BLOCKED"
  "article_text": "# Article...",
  "qc_report": {
    "overall_score": 87,
    "overall_status": "PASS",
    "criteria_results": [...]
  },
  "job_package": {...},
  "created_at": "...",
  "completed_at": "..."
}

═══════════════════════════════════════════════════════════════════════

GET /api/v1/jobs

List all jobs (paginated)

Query params:
  - page: 1
  - page_size: 20
  - status: "DELIVERED" | "PENDING" | "PROCESSING" | "BLOCKED"

═══════════════════════════════════════════════════════════════════════

For full interactive docs:
→ http://localhost:8000/docs (Swagger UI)
→ http://localhost:8000/redoc (ReDoc)
""")

    input("\nPress Enter to continue...")

def run_tests():
    """Run test suite."""
    clear_screen()
    print_banner()
    print("=" * 70)
    print("  RUNNING TEST SUITE")
    print("=" * 70)

    print("\n🧪 Executing tests...\n")

    import subprocess
    result = subprocess.run(
        ["python", "tests/test_core_services.py"],
        capture_output=True,
        text=True,
        env={**os.environ, "SERPAPI_KEY": "demo_key", "ANTHROPIC_API_KEY": "demo_key"}
    )

    print(result.stdout)
    if result.stderr:
        print(result.stderr)

    input("\n\nPress Enter to continue...")

def main():
    """Main interactive demo loop."""
    while True:
        print_banner()
        print_menu()

        choice = input("\nSelect option (1-8): ").strip()

        if choice == '1':
            show_system_status()
        elif choice == '2':
            simulate_job_creation()
        elif choice == '3':
            show_qc_criteria()
        elif choice == '4':
            show_pipeline_architecture()
        elif choice == '5':
            show_cost_calculator()
        elif choice == '6':
            show_api_docs()
        elif choice == '7':
            run_tests()
        elif choice == '8':
            clear_screen()
            print("\n👋 Tack för att du testade BACOWR!\n")
            print("För att köra web-versionen:")
            print("→ Se RUN_LOCAL_DEMO.md\n")
            sys.exit(0)
        else:
            print("\n❌ Invalid choice. Please select 1-8.")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear_screen()
        print("\n\n👋 Demo avslutad.\n")
        sys.exit(0)
