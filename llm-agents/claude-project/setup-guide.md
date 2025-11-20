# Claude Project Setup Guide: BACOWR Backlink Writer

## 🚀 Quick Setup (5 minutes)

### Step 1: Create New Project

1. Go to https://claude.ai
2. Click "Projects" in sidebar
3. Click "Create Project"
4. Name it: **"BACOWR Backlink Writer"**

### Step 2: Add Custom Instructions

1. In Project settings, find "Custom Instructions" section
2. Copy entire content from `custom-instructions.md`
3. Paste into Custom Instructions field
4. Save

**Note**: Claude Projects support longer instructions than Custom GPTs (no 8000 char limit), so the full detailed workflow fits perfectly!

### Step 3: Add Project Knowledge

Upload these files to Project Knowledge:

**From `../shared-knowledge/`**:
1. `next-a1-spec.json` - Schema definitions
2. `bridge-type-library.md` - Bridge strategies
3. `workflow-guide.md` - Detailed process
4. `lsi-optimization-guide.md` - LSI term selection
5. `publisher-voice-profiles.md` - Tone matching
6. `serp-analysis-guide.md` - Intent analysis

**How to upload**:
- Click "Add content" in Knowledge section
- Upload files one by one
- Or drag & drop multiple files
- Total size limit: ~10MB per project

### Step 4: Configure Project Settings

**Project Privacy**: Private (or Team if sharing)

**Conversation Memory**: Enable
- Claude will remember previous jobs
- Can reference past articles: "Use same style as last article"

**Sharing**:
- Private: Only you
- Team: Share with workspace members
- Link: Anyone with link

---

## 📝 Usage Patterns

### Standard Article Creation

**User starts chat**:
```
"Create backlink article for ekonomibloggen.se → https://example.com/bolan with anchor 'bästa bolån'"
```

**Claude guides through**:
1. Asks for target page info (or accepts screenshot)
2. Asks for publisher context (or accepts screenshot)
3. Requests SERP data for 3 queries (or accepts screenshot)
4. Generates preflight brief (Artifact 1)
5. After confirmation, writes article (Artifact 2)

**User receives**:
- Preflight brief for transparency
- Final article ready to publish
- Word count, placement verification
- Optional: Meta tags, internal links

### Quick Mode (Experienced Users)

**User provides everything upfront**:
```
Publisher: ekonomibloggen.se (consumer magazine, Swedish)
Target: https://example.com/bolan (mortgage comparison)
Anchor: bästa bolån

SERP Results for "bästa bolån":
1. Compricer - Jämför bolån...
2. Konsumentverket - Guide till...
3. Bank.se - Räkna på ditt...
[etc.]
```

**Claude**:
- Skips Q&A steps
- Goes straight to analysis + brief
- Generates article faster

### Screenshot Mode (Fastest)

**User**:
```
"Here are screenshots:
1. Target page
2. Publisher homepage
3. SERP for 'bästa bolån'"
[Uploads 3 images]
```

**Claude**:
- Uses vision to extract all data
- Analyzes and generates brief
- Writes article
- Total time: ~2-3 minutes

---

## 🎯 Advanced Features

### Conversation Memory Benefits

Because Projects have memory, you can:

**Reference previous work**:
```
User: "Write another article for ekonomibloggen.se but different topic"
Claude: "I'll use the same publisher profile we established last time..."
```

**Build style consistency**:
```
User: "Match the tone from the last article you wrote"
Claude: "I'll use the same consumer magazine style with..."
```

**Iterate on drafts**:
```
User: "Make it less commercial"
Claude: "I'll shift from STRONG to PIVOT bridge type..."
```

### Multi-Article Workflows

**Batch processing**:
```
User: "I need 5 articles for ekonomibloggen.se, all different topics"
Claude: "I'll use the same publisher profile. Please give me:
1. Target URL #1 + Anchor #1
2. Target URL #2 + Anchor #2
..."
```

Claude remembers publisher context, only needs target+anchor for each.

### Quality Review Mode

**Ask Claude to review drafts**:
```
User: "Here's an article I wrote. Review it against Next-A1 criteria."
[Paste article]

Claude analyzes:
- Bridge type alignment
- Subtopic coverage
- LSI optimization
- Anchor placement
- Tone match
Provides specific improvement suggestions
```

---

## 📊 Testing Your Project

### Test Case 1: Full Workflow
```
Input:
- Publisher: ekonomibloggen.se
- Target: https://example.com/bolan
- Anchor: bästa bolån
- Provide SERP screenshots

Expected:
✓ Preflight brief generated (Artifact)
✓ Article 900+ words (Artifact)
✓ Bridge type: PIVOT (commercial research intent)
✓ LSI terms injected near anchor
✓ All SERP subtopics covered
```

### Test Case 2: Screenshot Analysis
```
Input:
- Upload 3 screenshots (target, publisher, SERP)
- Anchor: bästa bolån

Expected:
✓ Claude extracts data from images
✓ Identifies entities, topics correctly
✓ Generates complete brief + article
✓ No need for manual data entry
```

### Test Case 3: Multi-Article Batch
```
Input:
- Publisher: ekonomibloggen.se (first time)
- 3 different target/anchor pairs

Expected:
✓ First article: Full publisher profiling
✓ Articles 2-3: Reuse publisher context
✓ Each has appropriate bridge type
✓ Consistent tone across all articles
```

---

## 🔧 Customization

### Add Industry-Specific Knowledge

Upload additional files:
```
compliance-requirements.md (if finance/health)
trust-sources-library.md (pre-approved authorities)
brand-guidelines.md (if working for specific client)
```

Claude will reference these automatically.

### Modify Instructions for Your Workflow

**Add post-generation steps**:
```markdown
After article, always provide:
- Meta title (max 60 chars)
- Meta description (max 160 chars)
- Focus keyword
- 3 internal link suggestions
- Social media snippet (LinkedIn format)
```

**Add validation rules**:
```markdown
Before outputting article, validate:
- Swedish language: LIX score 35-50
- No passive voice in H1/H2
- At least 2 trust sources cited
- Compliance disclaimer if finance/health
```

**Add client-specific constraints**:
```markdown
Client: Acme Corp
- Always mention "sustainability" in articles
- Never link to competitors: [list]
- Preferred trust sources: [list]
- Brand voice: Professional but approachable
```

---

## 💡 Pro Tips

### Use Artifacts Effectively

Claude generates TWO artifacts:
1. **Preflight Brief** - Keep for records, transparency
2. **Final Article** - Ready to publish

You can:
- Download both as separate files
- Copy directly to CMS
- Share brief with client for approval before writing
- Edit artifacts inline and ask Claude to refine

### Leverage Vision for Speed

Screenshot instead of typing:
- Target page → Extract entities, offer, topics
- Publisher homepage → Extract style, focus, tone
- SERP results → Extract titles, snippets, types

This is **3-5x faster** than manual data entry.

### Build a Knowledge Library

Over time, add to Project Knowledge:
- `publisher-profiles/` - Pre-analyzed publishers
- `trust-sources/` - Verified authority sites per niche
- `lsi-libraries/` - Pre-generated term lists per topic

Claude will auto-reference when relevant.

### Use for Training

Have new team members:
1. Watch you create an article with Claude
2. Review the preflight brief to understand analysis
3. Try themselves with Claude's guidance
4. Compare output to your examples

Claude becomes a **training tool** for Next-A1 methodology.

---

## 🚨 Troubleshooting

### Problem: Claude skips steps

**Solution**:
Start fresh chat, say:
```
"Follow the 7-step process exactly.
Wait for my response after each step before proceeding."
```

### Problem: Articles lack depth

**Solution**:
Add to custom instructions:
```
"For each required subtopic, write minimum 150 words.
Include specific examples or data where possible."
```

### Problem: Wrong bridge type selected

**Solution**:
Provide explicit SERP data:
```
"SERP for 'bästa bolån' is dominated by comparison guides (80%).
Top 3 are all info_primary intent.
My target is commercial (transactional).
→ This suggests PIVOT bridge, correct?"
```

Claude will adjust if you provide clear evidence.

### Problem: Can't access knowledge files

**Solution**:
- Verify files uploaded successfully (check size limits)
- Mention file name explicitly: "Check bridge-type-library.md for examples"
- Re-upload if needed

---

## 📈 Success Metrics

**Track over time**:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Time per article | <10 min | Start to final output |
| Revision rate | <20% | How often edited post-generation |
| Bridge type accuracy | >90% | Manually verify against intent |
| Subtopic coverage | 100% | All SERP-derived topics included |
| Publisher acceptance | >95% | Articles accepted without major edits |

**SEO Performance** (post-publication):
- Ranking for target keywords
- Organic traffic to article
- Link engagement rate
- Time on page

---

## 🔄 Workflow Optimization

### For SEO Teams

**Multi-person workflow**:
1. **Junior SEO** - Provides input (publisher, target, anchor)
2. **Claude** - Generates preflight brief
3. **Senior SEO** - Reviews and approves brief
4. **Claude** - Writes article
5. **Editor** - Final polish

**Time savings**: ~70% reduction vs. manual writing

### For Content Agencies

**Client process**:
1. Client provides: Publisher, Target, Anchor
2. Claude generates preflight brief
3. **Share brief with client for approval** ← Key step
4. After approval, Claude writes article
5. Deliver article + brief as package

**Client transparency**: Preflight brief shows research methodology

### For In-House Teams

**Batch processing**:
- Monday: Gather 10 publisher/target/anchor combos
- Tuesday: Generate all 10 preflight briefs with Claude
- Wednesday: Review briefs, request article generation
- Thursday: Edit & polish articles
- Friday: Publish

**Efficiency**: 10 articles/week per person (vs. 2-3 manually)

---

## ✅ Launch Checklist

Before using in production:

- [ ] Custom instructions uploaded
- [ ] All knowledge files added (6 files minimum)
- [ ] Project privacy configured
- [ ] Test Case 1 passed (full workflow)
- [ ] Test Case 2 passed (screenshot mode)
- [ ] Test Case 3 passed (multi-article batch)
- [ ] Team members trained (if applicable)
- [ ] Client brief template created (if agency)
- [ ] Internal workflow documented
- [ ] Success metrics tracking set up

**Ready to scale backlink content production!** 🚀

---

## 📚 Resources

**Documentation**:
- Next-A1 Spec: `../shared-knowledge/next-a1-spec.json`
- Bridge Library: `../shared-knowledge/bridge-type-library.md`

**Support**:
- GitHub Issues: [Your repo]
- Team Slack: #bacowr-support

**Updates**:
- Check `CHANGELOG.md` for new features
- Re-upload knowledge files when schema updates
