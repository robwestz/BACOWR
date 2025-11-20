# Bridge Type Library - Next-A1 BACOWR

## Overview

Bridge types solve the **Variable Marriage** problem when Publisher, Anchor, Target, and Intent don't perfectly align.

**The three bridge types**:
1. **STRONG** - Direct recommendation (high alignment)
2. **PIVOT** - Informational angle (partial alignment)
3. **WRAPPER** - Contextual embedding (low alignment)

---

## Decision Matrix

| Alignment Score | Publisher Type | Target Type | SERP Intent | → Bridge Type |
|-----------------|----------------|-------------|-------------|---------------|
| **High (3/3)** | Info | Info | info_primary | **STRONG** |
| **High (3/3)** | Consumer | Commercial | commercial_research | **STRONG** |
| **Medium (2/3)** | Info | Commercial | commercial_research | **PIVOT** |
| **Medium (2/3)** | Consumer | Info | info_primary | **PIVOT** |
| **Low (1/3)** | Academic | Commercial | transactional | **WRAPPER** |
| **Low (0/3)** | Authority | Commercial | info_primary | **WRAPPER** |

**Rule of thumb**:
- All "aligned" → STRONG
- Any "partial" → PIVOT
- Any "off" → WRAPPER

---

## STRONG BRIDGE

### When to Use
- ✓ Publisher naturally covers this topic
- ✓ Anchor matches user search intent
- ✓ Target delivers on search promise
- ✓ Overall alignment: **aligned**

### Strategy
**Direct recommendation with confidence**

- Present target as primary/best solution
- Clear, confident language
- High commercial transparency
- Early link placement (after context established)

### Language Patterns (Swedish)

**Strong recommendation**:
```
"För [behov] rekommenderar vi [anchor]"
"Det bästa valet är ofta [anchor]"
"[Anchor] erbjuder den mest omfattande lösningen"
```

**Direct comparison**:
```
"Jämfört med andra alternativ levererar [anchor] [specific benefits]"
"Om du letar efter [quality], är [anchor] det rätta valet"
```

**Clear value proposition**:
```
"Med [anchor] får du [benefit 1], [benefit 2], och [benefit 3]"
```

### Example 1: Finance Blog → Finance Product

**Scenario**:
- Publisher: ekonomibloggen.se (consumer finance)
- Target: bank.se/bolan (mortgage products)
- Anchor: "bästa bolånen"
- SERP: commercial_research (comparing mortgages)

**Alignment**: ✓ ✓ ✓ (all aligned)

**Article excerpt**:
```markdown
## Att välja rätt bolån 2024

När du ska ta ett bolån är det viktigt att jämföra både
räntesatser, avgifter och villkor. Många banker erbjuder
konkurrenskraftiga lösningar, men det gäller att hitta det
som passar just din situation.

För de flesta låntagare är **[bästa bolånen](bank.se/bolan)**
de som kombinerar låg ränta med flexibla återbetalningsvillkor.
När du jämför alternativ, tänk på amorteringskrav, bindningstid,
och möjlighet till extrakörningar utan straffavgift.

[Continue with detailed comparison...]
```

**LSI terms near link**:
- ränta, villkor, jämförelse, alternativ, återbetalning, amortering

---

## PIVOT BRIDGE

### When to Use
- ⚠ Publisher is informational, target is commercial
- ⚠ Anchor is broader than target's specific offer
- ⚠ SERP shows info_primary, but target is transactional
- ✓ Overall alignment: **partial**

### Strategy
**Informational content that leads to target**

- Establish broader topic/problem first
- Build "pivot theme" connecting publisher ↔ target
- Present target as one of the better solutions (not only one)
- Medium commercial transparency
- Mid-article link placement

### Pivot Theme Patterns

**Problem → Solution**:
```
Establish problem → Discuss criteria → Present [anchor] as strong solution
```

**Comparison → Recommendation**:
```
Compare categories → Evaluate options → Position [anchor] favorably
```

**Education → Application**:
```
Explain concept → Practical usage → [Anchor] as implementation
```

### Language Patterns (Swedish)

**Informational lead-in**:
```
"När man utvärderar [category], finns flera viktiga faktorer"
"För att hitta rätt [solution], behöver du först förstå [concept]"
```

**Pivot to target**:
```
"Bland alternativen märks [anchor] genom [specific advantage]"
"Ett populärt val är [anchor], som erbjuder [balanced view]"
"För många användare har [anchor] visat sig vara en bra lösning tack vare [reasons]"
```

**Balanced framing**:
```
"Även om det finns flera bra alternativ, framstår [anchor] som särskilt lämplig för [use case]"
```

### Example 2: Lifestyle Blog → E-commerce Product

**Scenario**:
- Publisher: modernalivet.se (lifestyle, consumer magazine)
- Target: rusta.com/belysning (lighting products)
- Anchor: "bästa lamporna för"
- SERP: info_primary + commercial_research mixed

**Alignment**: ✓ ⚠ ⚠ (partial - publisher aligned, target/SERP partial)

**Article excerpt**:
```markdown
## Guide: Rätt belysning för varje rum

Belysning påverkar både stämning och funktionalitet i hemmet.
Att välja rätt lampor handlar om att matcha ljusstyrka, färgtemperatur
och stil med rummets användning.

### Faktorer att tänka på

När du väljer belysning är det viktigt att överväga:

1. **Ljusstyrka (lumen)** - Olika rum kräver olika intensitet
2. **Färgtemperatur** - Varmvitt vs kallvitt skapar olika atmosfär
3. **Energieffektivitet** - LED sparar både energi och pengar
4. **Design** - Lampan som inredningsdetalj

### Jämförelse av alternativ

Marknaden erbjuder allt från exklusiva designlampor till prisvärd
vardagsbelysning. För de flesta hem är **[bästa lamporna för](rusta.com/belysning)**
de som kombinerar funktion, kvalitet och stil till rimligt pris. När du
jämför alternativ, tänk på både ljuskvalitet och livslängd.

Olika typer har olika fördelar:
- **Taklampa**: Huvudbelysning, täcker hela rummet
- **Bordslampa**: Punktbelysning för arbete eller läsning
- **Golvlampa**: Flexibel placering, skapar zoner
```

**LSI terms near link**:
- kvalitet, jämförelse, alternativ, pris, funktion, stil, design, val

**Pivot theme**: "Choosing lighting" (broad informational) → "Rusta as practical option" (specific commercial)

---

## WRAPPER BRIDGE

### When to Use
- ✗ Publisher and target are mismatched (academic → commercial)
- ✗ Anchor doesn't match SERP intent
- ✗ Low credibility for direct recommendation
- ✓ Overall alignment: **off** or very partial

### Strategy
**Broad contextual frame with target embedded**

- Build neutral meta-framework first (methodology, risk, ethics, trends)
- Establish broader context before mentioning target
- Present target as one example among several alternatives
- Low commercial transparency
- Late link placement (after framework established)

### Wrapper Framework Patterns

**Methodology wrapper**:
```
"Hur man utvärderar [category]" → Methods → [Anchor] as one approach
```

**Risk/Safety wrapper**:
```
"Risker att tänka på med [topic]" → Risk factors → [Anchor] addresses some
```

**Trend/Innovation wrapper**:
```
"Utvecklingen inom [industry]" → Current trends → [Anchor] as example
```

**Regulatory/Ethics wrapper**:
```
"Regelverk för [topic]" → Compliance → [Anchor] meets standards
```

### Language Patterns (Swedish)

**Establish meta-frame**:
```
"När man analyserar [category] ur [perspective], finns flera viktiga aspekter"
"Från metodologisk synvinkel kräver [topic] noggrant övervägande av [factors]"
```

**Embed target neutrally**:
```
"Bland de lösningar som adresserar [concern] finns exempelvis [anchor]"
"Marknaden erbjuder olika alternativ, däribland [anchor], som [neutral description]"
```

**De-emphasize commercial**:
```
"Utöver etablerade aktörer har även [anchor] presenterat lösningar inom [area]"
```

### Example 3: Academic Blog → Commercial Product

**Scenario**:
- Publisher: forskarbloggen.se (academic, research-focused)
- Target: crypto-exchange.com (cryptocurrency trading)
- Anchor: "blockkedjeteknik"
- SERP: info_primary (educational content about blockchain)

**Alignment**: ✗ ✗ ⚠ (off - academic can't directly recommend commercial product)

**Article excerpt**:
```markdown
## Metodologiska utmaningar vid utvärdering av blockkedjesystem

Inom informationsteknikforskning har blockkedjeteknologi väckt
både entusiasm och skepsis. För en vetenskaplig bedömning krävs
strukturerad analys av säkerhet, skalbarhet och decentralisering.

### Utvärderingskriterier

Akademisk litteratur (Nakamoto, 2008; Buterin, 2014) föreslår
flera nyckelfaktorer:

1. **Konsensusmekanismer** - Proof-of-Work vs Proof-of-Stake
2. **Transaktionshastighet** - Throughput och latens
3. **Säkerhetsmodeller** - Attackvektorer och försvar

### Praktiska implementationer

I praktiken återfinns blockkedjeteknologi i olika sammanhang,
från finansiella tillämpningar till supply chain management.
Bland kommersiella implementationer som söker adressera
skalbarhetsproblem finns exempelvis **[blockkedjeteknik](crypto-exchange.com)**
som en av flera tekniska lösningar under utveckling.

För forskare som studerar dessa system rekommenderas att
utvärdera både tekniska specifikationer och akademisk peer-review.

### Forskningsfronten

[Continue with academic discussion...]
```

**LSI terms near link**:
- implementering, teknisk, lösning, utveckling, system, specifikation

**Wrapper theme**: "Methodology for evaluating blockchain" (academic frame) → Target mentioned as one commercial implementation among many

---

## Advanced Scenarios

### Scenario 4: Switching Bridge Types Mid-Article

Sometimes you need to shift strategy within same article.

**Use case**: Start WRAPPER, transition to PIVOT

```markdown
## [H1: Broad academic/neutral topic]

[Wrapper section 1: Establish methodology]
[Wrapper section 2: Present framework]

## [H2: Practical Applications] ← SHIFT POINT

[Now transition to PIVOT tone]
"När teorin möter praktiken..."

[PIVOT section with anchor link]

[Continue with more specific recommendations]
```

**When to use**:
- Long-form content (1500+ words)
- Publisher has mixed authority (academic + practical)
- Target has both info and commercial value

### Scenario 5: Multi-Link Bridge

If article links to both target AND trust sources:

**Pattern**:
```
Trust source (STRONG) → Establishes authority
↓
Target link (PIVOT/WRAPPER) → Softer approach
```

**Example**:
```markdown
Enligt Konsumentverket [trust link] är viktigt att [regulation].

När man jämför marknaden, erbjuder [anchor - target link] en lösning
som tar hänsyn till dessa aspekter.
```

---

## Testing Bridge Type Selection

### Validation Checklist

For each article, verify:

**STRONG Bridge**:
- [ ] Publisher regularly covers this topic
- [ ] Anchor matches SERP dominant intent
- [ ] Target page delivers what SERP users want
- [ ] Confident, direct language used
- [ ] Link placed early (after intro, in first H2 section)

**PIVOT Bridge**:
- [ ] Informational frame established first
- [ ] Pivot theme connects publisher ↔ target
- [ ] Target presented as strong option (not only option)
- [ ] Balanced language (not aggressive sales pitch)
- [ ] Link placed mid-article

**WRAPPER Bridge**:
- [ ] Meta-framework established before target mention
- [ ] Target embedded as example among alternatives
- [ ] Neutral, de-emphasized language
- [ ] Link placed late (after context fully established)
- [ ] No direct recommendation language

### Common Mistakes

**❌ Using STRONG when should use PIVOT**:
```
"Det enda valet är [anchor]" ← Too aggressive for partial alignment
```

**✓ Correct PIVOT**:
```
"Ett populärt alternativ är [anchor] tack vare [specific benefits]"
```

**❌ Using WRAPPER when STRONG is appropriate**:
```
"Bland många alternativ finns också [anchor]" ← Undersells when high alignment
```

**✓ Correct STRONG**:
```
"För [use case] rekommenderar vi [anchor]"
```

**❌ Using PIVOT when WRAPPER needed**:
```
Academic blog: "Vi rekommenderar [commercial product]" ← Breaks credibility
```

**✓ Correct WRAPPER**:
```
"Bland kommersiella implementationer återfinns [product] som en av flera lösningar"
```

---

## Language Libraries by Bridge Type

### STRONG - Swedish Phrases

**Recommendations**:
- "rekommenderar vi"
- "bästa valet är"
- "det rätta alternativet"
- "överlägsen lösning"

**Comparisons**:
- "jämfört med andra alternativ"
- "bättre än konkurrenterna inom"
- "den mest omfattande lösningen"

**Direct value**:
- "ger dig"
- "erbjuder"
- "levererar"

### PIVOT - Swedish Phrases

**Informational lead**:
- "när man utvärderar"
- "för att hitta rätt"
- "bland alternativen"
- "ett populärt val"

**Balanced framing**:
- "visat sig vara en bra lösning"
- "framstår som särskilt lämplig"
- "erbjuder fördelar inom"
- "kan vara ett bra alternativ"

**Contextual**:
- "tack vare"
- "genom att"
- "med fokus på"

### WRAPPER - Swedish Phrases

**Neutral introduction**:
- "bland de lösningar som"
- "marknaden erbjuder olika alternativ, däribland"
- "återfinns exempelvis"
- "en av flera"

**Academic/Formal**:
- "ur metodologisk synvinkel"
- "från forskningsperspektiv"
- "i praktiken"
- "kommersiella implementationer inkluderar"

**De-emphasized**:
- "utöver etablerade aktörer"
- "som en av flera tekniska lösningar"
- "bland annat"

---

Use this library as reference when writing articles. Match bridge type to alignment pattern, then use appropriate language strategies.
