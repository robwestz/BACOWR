1. Idealflöde för en körning (enda input: publisher + target + anchor)

Detta är den fulla kedjan, i den ordning en LLM-baserad motor bör få och använda datan.

0. Minimal input (från människa / UI)

{
  "publisher_domain": "example-publisher.com",
  "target_url": "https://client.com/product-x",
  "anchor_text": "bästa valet för [entitet/tema]"
}


Därifrån sker allt annat automatiskt.

1. Fetch & profilering: Target (målsida)

Upstream-komponent (inte writer-agenten) måste ta fram:

HTML

Strukturerade element

Innehållssammanfattning

Entiteter

Potentiella huvudqueries

Writer-agenten ska inte behöva gissa detta från scratch; den får det serverat.

"target_profile": {
  "url": "https://client.com/product-x",
  "http_status": 200,
  "title": "string",
  "meta_description": "string",
  "h1": "string",
  "h2_h3_sample": ["string"],
  "main_content_excerpt": "trunkerad bodytext",
  "detected_language": "sv",
  "core_entities": ["Product X", "kategori Y", "problem Z"],
  "core_topics": ["tema1", "tema2"],
  "core_offer": "kort beskrivning av vad sidan hjälper användaren med",
  "candidate_main_queries": [
    "huvudquery 1",
    "huvudquery 2"
  ]
}


2. Fetch & profilering: Publisher (publiceringsdomän)

Samma sak här: upstream tar fram:

"publisher_profile": {
  "domain": "example-publisher.com",
  "sample_urls": [
    "https://example-publisher.com/artikel-1",
    "https://example-publisher.com/artikel-2"
  ],
  "about_excerpt": "trunkerad 'Om oss'-text eller liknande",
  "detected_language": "sv",
  "topic_focus": ["privatekonomi", "konsumentråd"],
  "audience": "kort beskrivning",
  "tone_class": "consumer_magazine",
  "allowed_commerciality": "low_to_medium",
  "brand_safety_notes": "ingen hardcore gambling, inga tveksamma lån etc."
}


3. Anchor: hypotes & klassning (kan göras upstream eller av writer-agent)

"anchor_profile": {
  "proposed_text": "bästa valet för [tema]",
  "type_hint": null,
  "llm_classified_type": "partial", 
  "llm_intent_hint": "commercial_research"
}


4. SERP Preflight: huvudquery + klusterqueries (the big one)

Här kommer det du beskrev: minst tre sökningar, upp till topp-10 resultat per query.

Upstream-komponent ansvarar för att ta reda på detta och mata in det strukturerat.

"serp_research": {
  "main_query": "huvudquery baserad på target_profile.core_entities",
  "cluster_queries": [
    "klusterquery_1",
    "klusterquery_2"
  ],
  "queries_rationale": "varför dessa valdes utifrån target_profile och anchor_profile",
  "results": [
    {
      "query": "huvudquery baserad på target",
      "dominant_intent": "commercial_research",
      "secondary_intents": ["info_primary"],
      "top_results": [
        {
          "rank": 1,
          "url": "https://topsite1.com",
          "title": "string",
          "snippet": "string",
          "detected_page_type": "guide | kategori | produkt | jämförelse | recension | myndighet | annat",
          "content_excerpt": "kort truncerad text",
          "key_entities": ["entitet1", "entitet2"],
          "key_subtopics": ["tema1", "tema2"],
          "why_it_ranks": "1–3 meningar: sammanfattning av value/coverage/format"
        },
        {
          "rank": 2,
          "url": "https://topsite2.com",
          "title": "string",
          "snippet": "string",
          "detected_page_type": "guide",
          "content_excerpt": "…",
          "key_entities": ["…"],
          "key_subtopics": ["…"],
          "why_it_ranks": "…"
        }
        // upp till rank 10
      ],
      "required_subtopics": [
        "subtopic som nästan alla toppresultat täcker",
        "ytterligare subtopic"
      ],
      "page_archetypes": [
        "guide",
        "jämförelse",
        "produktlista"
      ]
    },
    {
      "query": "klusterquery_1",
      "dominant_intent": "info_primary",
      "secondary_intents": [],
      "top_results": [ /* samma struktur */ ],
      "required_subtopics": ["…"],
      "page_archetypes": ["…"]
    },
    {
      "query": "klusterquery_2",
      "dominant_intent": "transactional",
      "secondary_intents": ["commercial_research"],
      "top_results": [ /* samma struktur */ ],
      "required_subtopics": ["…"],
      "page_archetypes": ["…"]
    }
  ],
  "confidence": "high"
}


Här är vi överdrivet noggranna: detta är exakt vad en LLM kan tolka till ett Intent/ClusterProfile.

5. Härledning: Intent & ClusterProfile (input till writer-agent)

Denna del kan göras av en “analysis-agent” eller direkt av writer-agent. Men du vill ha den som data.

"intent_profile": {
  "serp_intent_primary": "commercial_research",
  "serp_intent_secondary": ["info_primary"],
  "target_page_intent": "transactional_with_info_support",
  "anchor_implied_intent": "commercial_research",
  "publisher_role_intent": "info_primary",
  "required_subtopics_merged": [
    "pris/jämförelse",
    "fördelar/nackdelar",
    "hur det fungerar",
    "risker/villkor",
    "vem det passar"
  ],
  "forbidden_angles": [
    "direkt aggressiv CTA om publisher_role_intent är info_primary",
    "löften som går längre än målsidan kan backa upp"
  ],
  "alignment": {
    "anchor_vs_serp": "aligned",
    "target_vs_serp": "partial",
    "publisher_vs_serp": "aligned",
    "overall": "aligned"
  },
  "recommended_bridge_type": "pivot",
  "rationale": "SERP vill ha jämförande/informerande innehåll; publisher är info-first; target är kommersiell men kan presenteras som lösning inom en bredare jämförelse."
}


Detta mappas 1:1 mot din intent_extension + serp_research_extension.

6. Writer-agentens uppdrag (nu har den ALLT)

När writer-agenten får detta kompletta paket kan den:

lösa variabelgiftermålet,

välja strong/pivot/wrapper,

skapa intersect mellan:

vad SERP premierar,

vad målsidan erbjuder,

vad publisher kan säga med trovärdighet,

bygga ett 900+ ords stycke content,

placera länken,

fylla dina extensions.

Writer-agenten ska då producera:

"generation_constraints": {
  "language": "sv",
  "min_word_count": 900,
  "max_anchor_usages": 2,
  "anchor_policy": "ingen anchor i H1/H2, naturlig placering i mittsektion",
  "tone_profile": "enligt publisher_profile.tone_class"
}


Och sedan two-layer output:

Läsbar text (analys, strategi, brief, fulltext).

JSON:

"backlink_article_output_v2": {
  "links_extension": { ... },
  "intent_extension": { ... },
  "qc_extension": { ... },
  "serp_research_extension": { ... } 
}


Där serp_research_extension i princip är det block vi definierade i punkt 4, eventuellt kondenserat.
