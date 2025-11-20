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

    # Detect language from domain (simple heuristic)
    lang = 'sv' if '.se' in publisher_domain else 'en'

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
            'detected_language': lang,
            'topic_focus': [
                'Livsstil och inredning',
                'Produktguider',
                'Jämförelser och tester'
            ],
            'tone_class': 'consumer_magazine',
            'target_audience': 'allmänheten',
            'allowed_commercialization': 'high',
            'typical_headlines': [
                'Guide: Så hittar du bästa...',
                'Testa själv: Vi jämför...',
                'Expertråd: Detta bör du tänka på när...'
            ]
        },
        'target_profile': {
            'url': target_url,
            'http_status': 200,
            'detected_language': lang,
            'title': f'Utbud och erbjudanden - {target_url.split("/")[2]}',
            'core_entities': [
                'Produktkategori',
                'Varumärke',
                'Erbjudanden'
            ],
            'core_topics': [
                'Produktsortiment',
                'Priser och villkor',
                'Kvalitet och recensioner',
                'Leverans och support'
            ],
            'core_offer': 'Omfattande sortiment med konkurrenskraftiga priser och god kundservice. Flera alternativ för olika behov och budgetar.',
            'search_queries': [
                f'{anchor_text}',
                f'{anchor_text} pris',
                f'{anchor_text} test',
                f'{anchor_text} recension'
            ]
        },
        'anchor_profile': {
            'proposed_text': anchor_text,
            'type_hint': None,
            'llm_classified_type': 'partial',
            'llm_intent_hint': 'commercial_research'
        },
        'serp_research_extension': {
            'main_query': anchor_text,
            'dominant_intent': 'commercial_research',
            'cluster_queries': [
                f'{anchor_text} jämförelse',
                f'{anchor_text} test',
                f'{anchor_text} guide',
                f'{anchor_text} recension'
            ],
            'queries_rationale': 'Användare söker efter information för att jämföra alternativ innan köp. Kommersiell intent men informationsbehov.',
            'serp_sets': [
                {
                    'query': anchor_text,
                    'result_count': 10,
                    'dominant_intent': 'commercial_research'
                },
                {
                    'query': f'{anchor_text} jämförelse',
                    'result_count': 10,
                    'dominant_intent': 'info_primary'
                },
                {
                    'query': f'{anchor_text} test',
                    'result_count': 10,
                    'dominant_intent': 'info_primary'
                }
            ],
            'page_archetypes': [
                'Jämförelseguide',
                'Produktrecension',
                'How-to artikel',
                'Kategoriöversikt',
                'E-handel produktsida'
            ],
            'top_entities': [
                'Konsumentverket',
                'Testinstitut',
                'Populära varumärken',
                'Priskämförelsetjänster'
            ],
            'data_confidence': 'medium'
        },
        'intent_extension': {
            'serp_intent_primary': 'commercial_research',
            'serp_intent_secondary': ['info_primary', 'transactional'],
            'target_page_intent': 'transactional_with_info_support',
            'anchor_implied_intent': 'commercial_research',
            'publisher_role_intent': 'info_primary',
            'intent_alignment': {
                'anchor_vs_serp': 'aligned',
                'target_vs_serp': 'partial',
                'publisher_vs_serp': 'aligned',
                'overall': 'partial'
            },
            'recommended_bridge_type': 'pivot',
            'recommended_article_angle': 'Informativ guide med jämförelser som naturligt leder till target som ett av de bättre alternativen',
            'required_subtopics': [
                'Vad ska du tänka på vid valet',
                'Jämförelse av alternativ',
                'Fördelar och nackdelar',
                'Prissammanställning',
                'Expertråd och rekommendationer',
                'Vanliga frågor och svar'
            ],
            'forbidden_angles': [
                'Ren produktpitch utan kontext',
                'Enbart fokus på ett enda alternativ',
                'Aggressiv säljtext'
            ],
            'notes': {
                'rationale': 'Pivot bridge passar bäst eftersom publisher är informativ medan target är kommersiell. Läsaren vill ha objektiv information men kan guidas mot target som en bra lösning.',
                'data_confidence': 'medium'
            }
        },
        'links_extension': {
            'bridge_type': 'pivot',
            'anchor_text': anchor_text,
            'anchor_type': 'partial',
            'lsi_terms': [
                'kvalitet',
                'jämförelse',
                'alternativ',
                'pris',
                'erbjudande',
                'recension',
                'test',
                'guide',
                'rekommendation',
                'val'
            ],
            'placement_context': 'Placera i en jämförelsesektion där flera alternativ diskuteras, men target framhålls som ett av de mer fördelaktiga valen baserat på specifika kriterier.'
        },
        'generation_constraints': {
            'language': lang,
            'min_word_count': 900,
            'max_anchor_usages': 2,
            'anchor_policy': 'Ingen anchor i H1/H2, mittsektion',
            'anchor_placement': 'mittsektion'
        }
    }


def format_preflight_for_llm(job_package: dict) -> str:
    """
    Formatera job package som läsbar text för manuell LLM-användning.
    Följer samma format som det tidigare systemet.

    Returns:
        Formatterad text som kan copy-pastas till ChatGPT/Claude
    """
    jp = job_package

    # Extrahera data
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
    links_ext = jp.get('links_extension', {})

    # Språk för instruktioner
    lang = gen_constraints.get('language', 'sv')
    lang_name = 'Swedish' if lang == 'sv' else 'English'

    # Bridge type förklaringar
    bridge_type = intent_ext.get('recommended_bridge_type', 'pivot').upper()
    bridge_explanations = {
        'STRONG': """
**STRONG BRIDGE - Direktlänkning**
- Direkt, tydlig länk till target
- Target presenteras som primär lösning
- Hög kommersiell transparens
- Exempel: "För [behov] rekommenderar vi starkt [anchor]."
- Använd när: Hög alignment mellan alla variabler (publisher, target, SERP, anchor)
""",
        'PIVOT': """
**PIVOT BRIDGE - Informationsvinkel**
- Informativt innehåll som leder till target
- Target presenteras som en av flera resurser (men bäst)
- Medium kommersiell transparens
- Exempel: "När man utvärderar [topic], kan [anchor] ge värdefulla insikter."
- Använd när: Publisher är info, men target är kommersiell
""",
        'WRAPPER': """
**WRAPPER BRIDGE - Kontextinbäddning**
- Target inbäddad i bredare kontext
- Target som exempel bland flera alternativ
- Låg kommersiell transparens
- Exempel: "Marknaden erbjuder olika alternativ, inklusive [anchor]."
- Använd när: Låg alignment, stor skillnad mellan publisher-ton och target-intent
"""
    }

    bridge_explanation = bridge_explanations.get(bridge_type, bridge_explanations['PIVOT'])

    # Formatera subtopics med checkboxar
    required_subtopics = intent_ext.get('required_subtopics', [])
    subtopics_formatted = '\n'.join([f"  ✓ {topic}" for topic in required_subtopics]) if required_subtopics else '  (inga subtopics tillgängliga)'

    # Formatera forbidden angles
    forbidden_angles = intent_ext.get('forbidden_angles', [])
    forbidden_formatted = '\n'.join([f"  ✗ {angle}" for angle in forbidden_angles]) if forbidden_angles else '  (inga förbjudna vinklar identifierade)'

    # LSI-termer
    lsi_terms = links_ext.get('lsi_terms', [])
    lsi_formatted = '\n'.join([f"  - {term}" for term in lsi_terms]) if lsi_terms else '  (inga LSI-termer tillgängliga)'

    # SERP sets
    serp_sets = serp_ext.get('serp_sets', [])
    serp_sets_formatted = ''
    if serp_sets:
        for serp_set in serp_sets:
            query = serp_set.get('query', 'N/A')
            count = serp_set.get('result_count', 0)
            intent = serp_set.get('dominant_intent', 'N/A')
            serp_sets_formatted += f"  - {query}: {count} resultat, {intent} intent\n"
    else:
        serp_sets_formatted = '  (ingen SERP data tillgänglig)\n'

    # Topic focus
    topic_focus = publisher_prof.get('topic_focus', [])
    topic_focus_formatted = '\n'.join([f"  - {topic}" for topic in topic_focus]) if topic_focus else '  (inga topics tillgängliga)'

    # Typical headlines
    typical_headlines = publisher_prof.get('typical_headlines', [])
    headlines_formatted = '\n'.join([f"  - {headline}" for headline in typical_headlines]) if typical_headlines else '  (inga exempel tillgängliga)'

    # Core entities
    core_entities = target_prof.get('core_entities', [])
    entities_formatted = '\n'.join([f"  - {entity}" for entity in core_entities]) if core_entities else '  (inga entiteter tillgängliga)'

    # Core topics
    core_topics = target_prof.get('core_topics', [])
    topics_formatted = '\n'.join([f"  - {topic}" for topic in core_topics]) if core_topics else '  (inga topics tillgängliga)'

    # Search queries
    search_queries = target_prof.get('search_queries', [])
    queries_formatted = '\n'.join([f"  - {query}" for query in search_queries]) if search_queries else '  (inga queries tillgängliga)'

    # Page archetypes
    page_archetypes = serp_ext.get('page_archetypes', [])
    archetypes_formatted = '\n'.join([f"  - {archetype}" for archetype in page_archetypes]) if page_archetypes else '  (ingen data tillgänglig)'

    # Top entities in SERP
    top_entities = serp_ext.get('top_entities', [])
    top_entities_formatted = '\n'.join([f"  - {entity}" for entity in top_entities]) if top_entities else '  (data ej tillgänglig)'

    # Cluster queries
    cluster_queries = serp_ext.get('cluster_queries', [])
    cluster_formatted = '\n'.join([f"  - {query}" for query in cluster_queries]) if cluster_queries else '  (inga kluster tillgängliga)'

    # Kommersialisering
    commercialization = publisher_prof.get('allowed_commercialization', 'medium')

    # Bygg output i samma format som exemplet
    output = f"""# BACOWR BACKLINK ARTICLE - COMPLETE RESEARCH CONTEXT

Du ska nu skriva en SEO-optimerad backlink-artikel baserad på omfattande research.

---

## 📋 UPPDRAG

Skriv en **{lang_name}** artikel (minimum {gen_constraints.get('min_word_count', 900)} ord) som naturligt länkar till målsidan.

**Anchor text:** "{anchor}"
**Target URL:** {target}

---

## 🏢 PUBLIKATIONSKONTEKT (Publisher Profile)

**Domain:** {publisher}

**Språk:** {lang_name}

**Ton & Stil:** {publisher_prof.get('tone_class', 'N/A')}
- Målgrupp: {publisher_prof.get('target_audience', 'allmänheten')}
- Tillåten kommersialisering: {commercialization}

**Ämnesfokus:**
{topic_focus_formatted}

**Typiska rubriker:**
{headlines_formatted}

---

## 🎯 MÅLSIDA (Target Profile)

**URL:** {target}

**Titel:** {target_prof.get('title', 'N/A')}

**Kärnentiteter:**
{entities_formatted}

**Huvudämnen:**
{topics_formatted}

**Erbjudande/Värde:**
{target_prof.get('core_offer', 'N/A')}

**Huvudsökfrågor (från target):**
{queries_formatted}

---

## 🔍 SERP RESEARCH (Search Intent Analysis)

### Huvudsökning
**Query:** {serp_ext.get('main_query', 'N/A')}
**Dominant Intent:** {serp_ext.get('dominant_intent', 'N/A')}

### Kluster-sökningar
{cluster_formatted}

### SERP-sets analyserade
{serp_sets_formatted}
### Sidtyper som rankar högt (Page Archetypes)
{archetypes_formatted}

### Toppentiteter i SERP
{top_entities_formatted}

---

## 🎨 INNEHÅLLSSTRATEGI (Intent Extension)

### Alignment-analys
- **SERP Intent:** {intent_ext.get('serp_intent_primary', 'N/A')}
- **Target Intent:** {intent_ext.get('target_page_intent', 'N/A')}
- **Publisher Role:** {intent_ext.get('publisher_role_intent', 'N/A')}
- **Overall Alignment:** {intent_ext.get('intent_alignment', {}).get('overall', 'N/A')}

### Bridge Type (KRITISKT!)
**{bridge_type}**

{bridge_explanation}

### Obligatoriska subtopics (från SERP)
Dessa MÅSTE täckas för att artikeln ska vara SERP-optimerad:
{subtopics_formatted}

### Förbjudna vinklar
Undvik dessa (ej i linje med SERP/publisher):
{forbidden_formatted}

### LSI-termer (Latent Semantic Indexing)
Inkludera naturligt 6-10 av dessa INOM ±2 MENINGAR från länken:
{lsi_formatted}

---

## 📝 GENERATIONSKRAV

### Struktur
1. **H1** - Huvudrubrik (fängslande, SERP-optimerad)
2. **Introduktion** - 2-3 stycken som etablerar kontext
3. **4-6 huvudsektioner** med H2-rubriker (täck required subtopics)
4. **Subsektioner** med H3 där lämpligt
5. **Avslutning** - Sammanfatta nyckelpunkter

### Länkplacering
- Använd anchor text: **"{anchor}"**
- Länka till: **{target}**
- Placera i **{gen_constraints.get('anchor_placement', 'mittsektion')}** (INTE i H1, H2 eller introduktion)
- Kontexten måste kännas naturlig och tillföra värde
- Använd bridge type: **{bridge_type.lower()}**

### LSI-termer
Inom ±2 meningar från länken, inkludera 6-10 av dessa termer naturligt:
{lsi_formatted}

### Ton & Stil
- Matcha publisher-ton: **{publisher_prof.get('tone_class', 'N/A')}**
- Skriv för målgrupp: **{publisher_prof.get('target_audience', 'allmänheten')}**
- Kommersialisering: **{commercialization}**

### Kvalitetskrav
- ✓ Täck ALLA required subtopics från SERP
- ✓ Undvik forbidden angles
- ✓ Tillför genuint värde och insikter
- ✓ Trovärdigt resonemang
- ✓ Naturligt, engagerande språk
- ✓ Minimum **{gen_constraints.get('min_word_count', 900)} ord**

### Formatering
- Markdown-format
- Korrekt rubrikhierarki (H1 → H2 → H3)
- Korta stycken (3-4 meningar)
- Punktlistor där lämpligt
- Ingen meta-text (inga "[X ord]" eller liknande)

---

## 🚀 GENERERA ARTIKELN

Baserat på all research ovan, skriv nu den kompletta artikeln.

**Kom ihåg:**
1. Följ bridge type: **{bridge_type.lower()}**
2. Täck alla required subtopics
3. Placera länk naturligt i {gen_constraints.get('anchor_placement', 'mittsektion')}
4. Injicera 6-10 LSI-termer nära länken
5. Matcha publisher-ton
6. Minimum {gen_constraints.get('min_word_count', 900)} ord

**Börja nu:**
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
