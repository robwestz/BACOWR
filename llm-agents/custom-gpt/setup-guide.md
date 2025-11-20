# Custom GPT Setup Guide: BACOWR Backlink Writer

## 🚀 Quick Setup (5 minutes)

### Step 1: Create Custom GPT
1. Go to https://chat.openai.com/gpts/editor
2. Click "Create a GPT"
3. Switch to "Configure" tab

### Step 2: Basic Info
**Name**: BACOWR Backlink Writer

**Description**:
```
Expert SEO content writer for backlink articles. Creates 900+ word articles using Next-A1 framework with SERP research, intent analysis, and semantic optimization. Supports Swedish & English.
```

**Profile Picture**:
- Upload a relevant icon (e.g., link chain, SEO graph, or article icon)
- Or use DALL-E to generate one

### Step 3: Instructions
Copy-paste the entire content from `instructions.md` into the "Instructions" field.

**Important**: OpenAI has an 8000 character limit. If needed, condense by:
- Removing examples
- Shortening explanations
- Moving detailed info to Knowledge files

### Step 4: Conversation Starters
Add these 4 starters:

```
1. "Create a backlink article for my site"

2. "Analyze SERP intent and recommend bridge type"

3. "I have screenshots of target page and SERP results"

4. "Review my draft article against Next-A1 criteria"
```

### Step 5: Knowledge Base
Upload these files from `../shared-knowledge/`:

**Required files**:
- `next-a1-spec.json` (schema definitions)
- `bridge-type-library.md` (strategy examples)
- `workflow-guide.md` (step-by-step process)

**Optional but recommended**:
- `lsi-optimization-guide.md` (semantic optimization)
- `publisher-voice-profiles.md` (tone matching)
- `serp-analysis-guide.md` (intent classification)

### Step 6: Capabilities
Enable these:
- ✅ **Web Browsing** (for research if needed)
- ✅ **DALL-E Image Generation** (for diagrams if requested)
- ✅ **Code Interpreter** (for JSON validation, word counts, etc.)

### Step 7: Actions (Optional - Advanced)
Leave blank for now. In future, you could add:
- SERP API integration
- Page scraping service
- Analytics tracking

### Step 8: Additional Settings

**Custom Actions**: None (leave empty)

**Use conversation data**: Your choice
- Enable: Improves GPT over time
- Disable: More privacy

**Category**: Writing

---

## 📋 Testing Your GPT

### Test Case 1: Basic Article
```
User: "Create a backlink article for ekonomibloggen.se → https://example.com/bolan with anchor 'bästa bolån'"

GPT should:
1. Ask for target page details
2. Ask for publisher context
3. Request SERP data (or accept screenshots)
4. Generate preflight brief
5. Write article

Verify:
- Article is 900+ words
- Anchor placed in middle section
- Bridge type appropriate
- LSI terms included
```

### Test Case 2: Screenshot Upload
```
User: "I have screenshots of my target page and SERP results"
[Upload screenshots]

GPT should:
1. Use Vision to extract info from screenshots
2. Analyze content
3. Proceed with preflight + article generation

Verify:
- Correctly extracted data from images
- Proper intent analysis
```

### Test Case 3: Intent Analysis Only
```
User: "Analyze SERP intent for 'bästa bolån' and recommend bridge type"

GPT should:
1. Ask for SERP data
2. Classify intent
3. Recommend bridge type with rationale
4. NOT write full article (unless requested)
```

---

## 🎨 Customization Options

### For Swedish Market
Add to instructions:
```
Default language: Swedish
Swedish-specific:
- Use LIX readability score (target: 35-50)
- Reference Konsumentverket when appropriate
- Follow Swedish SEO best practices
```

### For Specific Niche
Add industry knowledge:
```
Specialization: [Finance/Health/Tech/etc.]
Compliance: [Add specific disclaimers]
Trust sources: [Preferred authorities]
```

### For Team Use
Add workflow hints:
```
After article generation, provide:
- Meta title (60 chars)
- Meta description (160 chars)
- Focus keyword
- Internal linking suggestions
```

---

## 🔧 Troubleshooting

### Problem: GPT skips steps
**Solution**: In instructions, add:
```
CRITICAL: Complete ALL steps in order. Do not skip to article writing.
Always show preflight brief before writing article.
```

### Problem: Articles too short
**Solution**: Add validation:
```
After writing, count words using Code Interpreter.
If <900 words, expand required subtopics.
```

### Problem: Wrong bridge type
**Solution**: Strengthen alignment rules:
```
Bridge type MUST match intent alignment:
- All "aligned" → STRONG
- Any "partial" → PIVOT
- Any "off" → WRAPPER
Never use STRONG if alignment is partial/off.
```

### Problem: Anchor in wrong place
**Solution**: Add explicit rule:
```
CRITICAL PLACEMENT RULE:
1. Never in H1 or H2 headings
2. Never in first 3 paragraphs (introduction)
3. Always in a middle H2 section
4. Validate before outputting
```

---

## 📊 Success Metrics

Track these to measure GPT performance:

**Quality Metrics**:
- ✓ Bridge type accuracy (matches intent alignment)
- ✓ Subtopic coverage (all SERP-derived topics included)
- ✓ Word count (900+ words)
- ✓ LSI term injection (6-10 near anchor)
- ✓ Tone match (matches publisher profile)

**User Satisfaction**:
- Time saved vs manual writing
- Revision rate (how often articles need edits)
- Publisher acceptance rate

**SEO Performance** (track post-publication):
- Ranking position for target keywords
- Organic traffic generated
- Link acceptance rate

---

## 🚀 Advanced Features (Future)

### Integration Ideas:
1. **SERP API** - Auto-fetch search results
2. **Page Scraper** - Auto-extract target/publisher data
3. **Readability API** - Auto-calculate LIX/Flesch scores
4. **QC Validator** - Run Next-A1 validation checks
5. **Analytics** - Track article performance

### Multi-Language Support:
- English (EN)
- Swedish (SV)
- Norwegian (NO)
- Danish (DK)
- Finnish (FI)

---

## 📖 Resources

**Documentation**:
- Next-A1 Spec: `../shared-knowledge/next-a1-spec.json`
- Workflow Guide: `../shared-knowledge/workflow-guide.md`

**Community**:
- GitHub: [Your repo URL]
- Support: [Your support email]

**Updates**:
Check `CHANGELOG.md` for Custom GPT updates and improvements.

---

## ✅ Launch Checklist

Before making GPT public:
- [ ] Instructions uploaded and tested
- [ ] All knowledge files uploaded
- [ ] Conversation starters configured
- [ ] Capabilities enabled (Web Browsing, Code Interpreter)
- [ ] Test Case 1 passed (basic article)
- [ ] Test Case 2 passed (screenshot upload)
- [ ] Test Case 3 passed (intent analysis)
- [ ] Description written
- [ ] Profile picture uploaded
- [ ] Privacy settings configured
- [ ] Sharing settings configured (Public/Private/Link only)

**Ready to launch!** 🎉

Share link with team or publish to GPT Store.
