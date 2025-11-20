#!/usr/bin/env python3
"""
BACOWR Offline Preflight Check
===============================
Kör endast preflight-steget och genererar text-output för manuell LLM-körning.

Användning:
    python run_preflight.py

Följ instruktionerna och mata in:
- Ankartext
- Målsida (URL)
- Publiceringsdomän

Output:
- JSON-fil med komplett job package
- TXT-fil med formatterad preflight-info för copy-paste till ChatGPT/Claude
"""

import json
import uuid
from pathlib import Path
from datetime import datetime


def generate_job_id() -> str:
    """Generate unique job ID"""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:8]
    return f"job_{timestamp}_{unique_id}"


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


def format_preflight_for_llm(job_package: dict) -> str:
    """
    Formatera job package som läsbar text för manuell LLM-användning.

    Returns:
        Formatterad text som kan copy-pastas till ChatGPT/Claude
    """
    jp = job_package

    # Extrahera viktiga delar
    job_id = jp.get('job_meta', {}).get('job_id', 'unknown')
    created = jp.get('job_meta', {}).get('created_at', 'unknown')

    input_data = jp.get('input_minimal', {})
    publisher = input_data.get('publisher_domain', 'N/A')
    target = input_data.get('target_url', 'N/A')
    anchor = input_data.get('anchor_text', 'N/A')

    publisher_prof = jp.get('publisher_profile', {})
    target_prof = jp.get('target_profile', {})
    anchor_prof = jp.get('anchor_profile', {})
    intent_ext = jp.get('intent_extension', {})
    serp_ext = jp.get('serp_research_extension', {})
    gen_constraints = jp.get('generation_constraints', {})

    # Bygg textformat
    output = f"""
================================================================================
BACOWR PREFLIGHT RESULTAT
================================================================================

JOB METADATA
------------
Job ID:       {job_id}
Skapad:       {created}
Spec:         {jp.get('job_meta', {}).get('spec_version', 'N/A')}
Mode:         {jp.get('job_meta', {}).get('mode', 'N/A')}


INPUT (MINIMAL)
---------------
Publiceringsdomän:  {publisher}
Målsida (URL):      {target}
Ankartext:          {anchor}


PUBLISHER PROFIL
----------------
Domän:              {publisher_prof.get('domain', 'N/A')}
Språk:              {publisher_prof.get('detected_language', 'N/A')}
Topic Focus:        {', '.join(publisher_prof.get('topic_focus', []))}
Ton:                {publisher_prof.get('tone_class', 'N/A')}


TARGET PROFIL
-------------
URL:                {target_prof.get('url', 'N/A')}
HTTP Status:        {target_prof.get('http_status', 'N/A')}
Språk:              {target_prof.get('detected_language', 'N/A')}
Titel:              {target_prof.get('title', 'N/A')}
Kärnentiteter:      {', '.join(target_prof.get('core_entities', []))}
Ämnen:              {', '.join(target_prof.get('core_topics', []))}
Kärnerbjudande:     {target_prof.get('core_offer', 'N/A')}


ANKARTEXT PROFIL
----------------
Föreslagen text:    {anchor_prof.get('proposed_text', 'N/A')}
Type hint:          {anchor_prof.get('type_hint', 'N/A')}
LLM-klassificering: {anchor_prof.get('llm_classified_type', 'N/A')}
LLM intent hint:    {anchor_prof.get('llm_intent_hint', 'N/A')}


SERP RESEARCH
-------------
Huvudfråga:         {serp_ext.get('main_query', 'N/A')}
Klusterfrågor:      {', '.join(serp_ext.get('cluster_queries', []))}
Rationale:          {serp_ext.get('queries_rationale', 'N/A')}
Data Confidence:    {serp_ext.get('data_confidence', 'N/A')}


INTENT EXTENSION
----------------
SERP Intent (primär):        {intent_ext.get('serp_intent_primary', 'N/A')}
SERP Intent (sekundär):      {', '.join(intent_ext.get('serp_intent_secondary', []))}
Target Page Intent:          {intent_ext.get('target_page_intent', 'N/A')}
Anchor Implied Intent:       {intent_ext.get('anchor_implied_intent', 'N/A')}
Publisher Role Intent:       {intent_ext.get('publisher_role_intent', 'N/A')}

Intent Alignment:
  - Anchor vs SERP:          {intent_ext.get('intent_alignment', {}).get('anchor_vs_serp', 'N/A')}
  - Target vs SERP:          {intent_ext.get('intent_alignment', {}).get('target_vs_serp', 'N/A')}
  - Publisher vs SERP:       {intent_ext.get('intent_alignment', {}).get('publisher_vs_serp', 'N/A')}
  - Overall:                 {intent_ext.get('intent_alignment', {}).get('overall', 'N/A')}

Rekommenderad Bridge Type:   {intent_ext.get('recommended_bridge_type', 'N/A')}
Artikelvinkel:               {intent_ext.get('recommended_article_angle', 'N/A')}
Nödvändiga Subämnen:         {', '.join(intent_ext.get('required_subtopics', []))}
Förbjudna Vinklar:           {', '.join(intent_ext.get('forbidden_angles', []))}

Notes:
  Rationale:                 {intent_ext.get('notes', {}).get('rationale', 'N/A')}
  Data Confidence:           {intent_ext.get('notes', {}).get('data_confidence', 'N/A')}


GENERATION CONSTRAINTS
----------------------
Språk:                       {gen_constraints.get('language', 'N/A')}
Min Word Count:              {gen_constraints.get('min_word_count', 'N/A')}
Max Anchor Usages:           {gen_constraints.get('max_anchor_usages', 'N/A')}
Anchor Policy:               {gen_constraints.get('anchor_policy', 'N/A')}


================================================================================
NÄSTA STEG: MANUELL LLM-KÖRNING
================================================================================

INSTRUKTIONER FÖR CHATGPT/CLAUDE:

Du ska nu skriva en artikel baserat på ovanstående preflight-analys.

VIKTIGA KRAV:
- Bridge Type:       {intent_ext.get('recommended_bridge_type', 'N/A')}
- Språk:             {gen_constraints.get('language', 'sv')}
- Minst ord:         {gen_constraints.get('min_word_count', 900)}
- Anchor placement:  {gen_constraints.get('anchor_policy', 'Ingen anchor i H1/H2, mittsektion')}
- Max anchor:        {gen_constraints.get('max_anchor_usages', 2)} gånger

SKRIV EN ARTIKEL SOM:
1. Följer rekommenderad artikelvinkel: {intent_ext.get('recommended_article_angle', 'N/A')}
2. Täcker nödvändiga subämnen: {', '.join(intent_ext.get('required_subtopics', []))}
3. Undviker förbjudna vinklar: {', '.join(intent_ext.get('forbidden_angles', [])) or 'inga'}
4. Matchar publisher-ton: {publisher_prof.get('tone_class', 'N/A')}
5. Inkluderar ankarlänken [{anchor}]({target}) i rätt position

Format: Markdown med H1, H2, H3 rubriker och strukturerade paragrafer.

================================================================================
"""

    return output.strip()


def main():
    """Huvudfunktion för offline preflight check"""

    print("=" * 80)
    print("BACOWR OFFLINE PREFLIGHT CHECK")
    print("=" * 80)
    print()
    print("Detta script kör endast preflight-analys utan API-anrop.")
    print("Du får ut en textfil som du kan köra manuellt i ChatGPT/Claude.")
    print()

    # Hämta input från användaren
    print("Mata in följande information:")
    print()

    anchor_text = input("Ankartext: ").strip()
    if not anchor_text:
        print("ERROR: Ankartext måste anges!")
        sys.exit(1)

    target_url = input("Målsida (URL): ").strip()
    if not target_url:
        print("ERROR: Målsida måste anges!")
        sys.exit(1)

    publisher_domain = input("Publiceringsdomän: ").strip()
    if not publisher_domain:
        print("ERROR: Publiceringsdomän måste anges!")
        sys.exit(1)

    print()
    print("-" * 80)
    print("Kör preflight-analys...")
    print("-" * 80)
    print()

    # Bygg mock job package (offline, inga API-anrop)
    job_package = build_mock_job_package(
        publisher_domain=publisher_domain,
        target_url=target_url,
        anchor_text=anchor_text
    )

    job_id = job_package['job_meta']['job_id']

    # Skapa output-mapp
    output_dir = Path(__file__).parent / 'storage' / 'preflight_output'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Spara JSON
    json_path = output_dir / f"{job_id}_preflight.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(job_package, f, indent=2, ensure_ascii=False)

    # Formatera och spara text
    text_output = format_preflight_for_llm(job_package)
    txt_path = output_dir / f"{job_id}_preflight.txt"
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text_output)

    # Visa resultat
    print("✓ Preflight-analys klar!")
    print()
    print("=" * 80)
    print("OUTPUT FILER")
    print("=" * 80)
    print()
    print(f"JSON (komplett):  {json_path}")
    print(f"TEXT (för LLM):   {txt_path}")
    print()
    print("=" * 80)
    print("PREFLIGHT RESULTAT (förhandsvisning)")
    print("=" * 80)
    print()
    print(text_output)
    print()
    print("=" * 80)
    print("KLART!")
    print("=" * 80)
    print()
    print("Nästa steg:")
    print(f"1. Öppna filen: {txt_path}")
    print("2. Kopiera innehållet")
    print("3. Klistra in i ChatGPT eller Claude")
    print("4. Låt AI:n generera artikeln baserat på preflight-resultatet")
    print()


if __name__ == '__main__':
    main()
