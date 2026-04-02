# LinkedIn Post Writer — Complete System Design

## System Name: **PostForge**
> Generate → Simulate → Predict → AutoLoop → Dominate

---

## ARCHITECTURE OVERVIEW

```
┌──────────────────────────────────────────────────────────────────┐
│                        USER INPUT                                │
│  "I want to post about [topic/intention]"                        │
│  + Your past 20-50 LinkedIn posts (voice training)               │
│  + Your niche / audience definition                              │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                 PHASE 1: DEEP RESEARCH AGENT                     │
│  Model: Claude Haiku (fast, cheap, long context)                 │
│                                                                  │
│  ① Scrape top 50 performing posts in your niche (Firecrawl/Exa) │
│  ② Analyze WHY they performed (hook, structure, format, CTA)    │
│  ③ Research your topic deeply (web search, papers, data)         │
│  ④ Identify trending angles, contrarian takes, data points      │
│  ⑤ Pull LinkedIn algorithm rules (2026 360Brew signals)         │
│                                                                  │
│  OUTPUT → research_brief.md                                      │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│                 PHASE 2: VOICE ANALYSIS ENGINE                   │
│  (Runs once, cached and updated periodically)                    │
│                                                                  │
│  ① Ingest your 20-50 past LinkedIn posts                        │
│  ② Generate voice_profile.md:                                    │
│     - Tone (warm/direct/analytical/casual)                       │
│     - Sentence rhythm (short punchy vs flowing)                  │
│     - Vocabulary fingerprint (words you overuse/avoid)           │
│     - Structure patterns (lists vs stories vs frameworks)        │
│     - Opening patterns (question/stat/story/bold claim)          │
│     - CTA style (soft question/direct ask/none)                  │
│     - Emoji usage, formatting habits                             │
│     - "Sentence Palette" (5 openers, 5 transitions, 5 closers)  │
│                                                                  │
│  OUTPUT → voice_profile.md (persistent, updated with feedback)   │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│              PHASE 3: MULTI-VARIANT GENERATION                   │
│  Model: Claude Sonnet (best writing quality)                     │
│                                                                  │
│  INPUT: research_brief.md + voice_profile.md + algorithm_rules   │
│                                                                  │
│  Generate 6 DISTINCT post variants:                              │
│                                                                  │
│  Variant A: "The Contrarian Take"                                │
│    → Bold opinion that challenges conventional wisdom            │
│  Variant B: "The Data Story"                                     │
│    → Lead with a surprising stat or data point                   │
│  Variant C: "The Personal Story"                                 │
│    → Narrative-driven, vulnerability + lesson                    │
│  Variant D: "The Framework/Listicle"                             │
│    → Step-by-step, save-worthy, high dwell time                  │
│  Variant E: "The Hot Take"                                       │
│    → Provocative opening, drives comments/debate                 │
│  Variant F: "The Thread/Carousel Concept"                        │
│    → Multi-slide content outline for PDF carousel                │
│                                                                  │
│  ALL variants must:                                              │
│  ✓ Match voice_profile.md exactly                                │
│  ✓ Hook in first 150 chars (before "See more")                   │
│  ✓ No external links in body                                     │
│  ✓ Short paragraphs (3-4 lines max)                              │
│  ✓ One clear actionable takeaway                                 │
│  ✓ Comment-driving CTA (not "Agree? 👇")                        │
│  ✓ 200-300 words for text posts                                  │
│  ✓ No generic AI patterns (no "In today's fast-paced world")     │
│                                                                  │
│  OUTPUT → 6 post variants with metadata                          │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│           PHASE 4: ENGAGEMENT SIMULATION ENGINE                  │
│  Model: Claude Opus (strongest reasoning)                        │
│                                                                  │
│  This is the core innovation. Each variant is scored against     │
│  a SIMULATED AUDIENCE using LinkedIn's known algorithm signals.  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐     │
│  │            SCORING DIMENSIONS (0-100 each)              │     │
│  │                                                         │     │
│  │  1. HOOK STRENGTH (25% weight)                          │     │
│  │     - First 150 chars: scroll-stopping power            │     │
│  │     - Curiosity gap / emotional trigger / specificity   │     │
│  │     - Rehook: does line 2-3 force "See more" click?     │     │
│  │                                                         │     │
│  │  2. DWELL TIME POTENTIAL (20% weight)                   │     │
│  │     - Estimated read time                               │     │
│  │     - Content density (info per line)                   │     │
│  │     - Formatting for mobile scanning                    │     │
│  │     - Progressive revelation (keeps reading)            │     │
│  │                                                         │     │
│  │  3. COMMENT-WORTHINESS (20% weight)                     │     │
│  │     - Does it provoke a response? (15x value of like)   │     │
│  │     - Debate potential without being offensive           │     │
│  │     - CTA that invites sharing experience               │     │
│  │     - "I disagree because..." trigger potential          │     │
│  │                                                         │     │
│  │  4. SAVE-WORTHINESS (15% weight)                        │     │
│  │     - Is this reference material?                       │     │
│  │     - Framework / checklist / template value            │     │
│  │     - "I need to come back to this" factor              │     │
│  │                                                         │     │
│  │  5. VOICE AUTHENTICITY (10% weight)                     │     │
│  │     - Match to voice_profile.md                         │     │
│  │     - Does it sound like YOU, not generic AI?           │     │
│  │     - Vocabulary consistency                            │     │
│  │                                                         │     │
│  │  6. ALGORITHM COMPLIANCE (10% weight)                   │     │
│  │     - No external links in body                         │     │
│  │     - No engagement bait phrases                        │     │
│  │     - Expertise match (topic DNA alignment)             │     │
│  │     - Optimal length for format                         │     │
│  │     - No AI-slop patterns detected                      │     │
│  └─────────────────────────────────────────────────────────┘     │
│                                                                  │
│  PERSONA SIMULATION (advanced):                                  │
│  Simulate 5 virtual audience personas:                           │
│    👤 "The Busy Executive" — skims, only stops for bold claims   │
│    👤 "The Peer Expert" — engages with depth, challenges ideas   │
│    👤 "The Aspiring Learner" — saves frameworks, asks questions  │
│    👤 "The Contrarian" — comments to disagree or add nuance      │
│    👤 "The Lurker" — reads but rarely engages, high dwell time   │
│                                                                  │
│  For each persona × each variant: predict action                 │
│  (skip / read / like / comment / save / share)                   │
│                                                                  │
│  OUTPUT → ranked_variants.json                                   │
│  {                                                               │
│    variant: "B",                                                 │
│    overall_score: 87,                                            │
│    predicted_engagement: {                                       │
│      impressions_estimate: "2,500-5,000",                        │
│      comment_probability: "high",                                │
│      save_probability: "medium",                                 │
│      predicted_engagement_rate: "4.2-6.8%"                       │
│    },                                                            │
│    improvement_suggestions: [...]                                │
│  }                                                               │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│              PHASE 5: HUMAN REVIEW & SELECTION                   │
│                                                                  │
│  Present TOP 3 variants with:                                    │
│  - Full post text                                                │
│  - Score breakdown across all 6 dimensions                       │
│  - Persona simulation results                                    │
│  - Predicted engagement range                                    │
│  - Specific improvement suggestions                              │
│  - "Why this will work" reasoning                                │
│                                                                  │
│  User can:                                                       │
│  → Pick one as-is                                                │
│  → Edit and re-score                                             │
│  → Ask for regeneration with specific tweaks                     │
│  → Merge elements from multiple variants                         │
└──────────────┬───────────────────────────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────────────────────────┐
│          PHASE 6: AUTO-IMPROVEMENT FEEDBACK LOOP                 │
│                                                                  │
│  ┌──────────────────────────────────────────────────────┐        │
│  │              THE LEARNING CYCLE                      │        │
│  │                                                      │        │
│  │  POST PUBLISHED                                      │        │
│  │       │                                              │        │
│  │       ▼                                              │        │
│  │  TRACK ACTUAL PERFORMANCE (manual input or scrape)   │        │
│  │  - Impressions                                       │        │
│  │  - Likes, Comments, Saves, Shares                    │        │
│  │  - Profile visits generated                          │        │
│  │  - Engagement rate                                   │        │
│  │  - Time to first comment                             │        │
│  │  - Comment quality (thoughtful vs generic)           │        │
│  │       │                                              │        │
│  │       ▼                                              │        │
│  │  COMPARE: Predicted vs Actual                        │        │
│  │       │                                              │        │
│  │       ├─── OUTPERFORMED ──▶ Analyze WHY              │        │
│  │       │    - What hook pattern worked?                │        │
│  │       │    - What format drove saves?                 │        │
│  │       │    - Update scoring weights                   │        │
│  │       │    - Store as "winning template"              │        │
│  │       │    - Boost similar patterns in future         │        │
│  │       │                                              │        │
│  │       └─── UNDERPERFORMED ─▶ Analyze WHY             │        │
│  │            - Was the hook weak? (low click-through)   │        │
│  │            - Was dwell time low? (content issue)      │        │
│  │            - Zero comments? (no debate trigger)       │        │
│  │            - Wrong timing? Wrong format?              │        │
│  │            - Penalize similar patterns                │        │
│  │            - Generate "lesson learned" entry          │        │
│  │                                                      │        │
│  │       ▼                                              │        │
│  │  UPDATE SYSTEM FILES:                                │        │
│  │  ┌─ performance_history.json (append)                │        │
│  │  ├─ scoring_weights.json (adjust)                    │        │
│  │  ├─ winning_templates.md (grow)                      │        │
│  │  ├─ anti_patterns.md (grow)                          │        │
│  │  └─ voice_profile.md (refine if needed)              │        │
│  │                                                      │        │
│  │       ▼                                              │        │
│  │  NEXT POST GENERATION uses updated weights           │        │
│  │  (System gets smarter with every post)               │        │
│  └──────────────────────────────────────────────────────┘        │
└──────────────────────────────────────────────────────────────────┘
```

---

## LINKEDIN 2026 ALGORITHM RULES (Baked Into System)

These are hardcoded into the generation and scoring agents:

### MUST DO
- First 150 chars = scroll-stopper (specific, emotional, or data-driven)
- Short paragraphs: 1-3 lines max for mobile
- Posts 200-300 words for text format
- One clear, actionable takeaway
- CTA that invites sharing experiences (not "Agree? 👇")
- Stick to 2-3 core expertise topics (topic DNA)
- Profile-content alignment (posts match your headline/about)
- Target 10+ comments in first 60 minutes
- Saves > Likes > Reactions (weight content for save-worthiness)
- Comments worth 15x a like in algorithm weight

### MUST NOT
- No external links in post body (60% reach penalty)
- No "link in first comment" (also penalized in 2026)
- No engagement bait ("Comment YES if you agree")
- No generic AI patterns ("In today's fast-paced world...")
- No "bro-etry" (one-line paragraphs with empty platitudes)
- No excessive hashtags (max 3-5, preferably in first comment)
- No AI-generated generic content (360Brew detects this)
- No posting outside your niche (expertise matching is real)

### FORMAT PRIORITY (by engagement rate)
1. **PDF Carousels** → 6.60% avg engagement (BEST)
2. **Native Video 30-90s** → 5.60% avg engagement
3. **Strategic Text** → 2-4% avg engagement
4. **Single Image** → 1-2% avg engagement

### TIMING
- Peak: Wednesday 9 AM (audience timezone)
- Strong: Tue-Thu, 8-10 AM
- Frequency: 3-5 posts/week max
- First 60 minutes = critical (only 5% of weak starts recover)

---

## EXISTING TOOLS THAT DO PIECES OF THIS

| What | Tool | Status |
|------|------|--------|
| **Engagement simulation (virtual audience)** | **Artificial Societies "Reach"** (YC W25) — [societies.io](https://societies.io) | EXACTLY your concept. They simulate your LinkedIn audience with AI twins and predict engagement before posting. Helped them get 1M impressions in 4 weeks. |
| **Performance prediction + A/B** | **Anyword.ai** | Predicts which content variation will perform better. Built-in A/B testing. |
| **Self-improving content loop** | **axite** (AX Semantics) | "Performance Feedback Loop" — content learns from its performance (SEO, conversion) and adapts. Enterprise-grade. |
| **Voice cloning for posts** | **WRITER** | Train agents on any voice, then generate posts in that voice. |
| **Open-source post agent** | **LangChain Social Media Agent** | Fork-ready. HITL, Anthropic API, Firecrawl, post scheduling. |
| **Multi-agent orchestration** | **CrewAI** | Research Agent → Writer Agent → Critic Agent → Selector Agent pipeline. |
| **3-stage quality workflow** | German Arutyunov's pattern | Haiku (research) → Sonnet (write) → Opus (review). Battle-tested. |

---

## AUTO-LOOP: HOW THE SYSTEM GETS SMARTER

### Loop 1: Per-Post Learning
```
Post published → Track metrics at 24h, 48h, 7d →
Compare predicted vs actual → Update scoring weights →
Next post uses calibrated weights
```

### Loop 2: Pattern Recognition (Weekly)
```
Every Sunday: Analyze all posts from the week →
Identify winning patterns (hook types, formats, topics, timing) →
Update winning_templates.md and anti_patterns.md →
Next week's generation biases toward proven patterns
```

### Loop 3: Voice Drift Detection (Monthly)
```
Every month: Compare generated posts to your actual editing patterns →
If you consistently edit out certain phrases → remove from voice_profile →
If you consistently add certain elements → add to voice_profile →
Voice profile evolves to match your ACTUAL preferences, not initial analysis
```

### Loop 4: Simulation Calibration (Ongoing)
```
After 20+ posts with tracked performance:
- Calculate simulation accuracy (predicted vs actual engagement)
- Adjust persona weights (maybe "Busy Executive" skips more than predicted)
- Recalibrate scoring dimensions (maybe save-worthiness matters more than expected)
- The simulator gets more accurate with every data point
```

---

## FILE STRUCTURE

```
postforge/
├── CLAUDE.md                    # Agent instructions + system prompt
├── config/
│   ├── voice_profile.md         # Your writing style DNA
│   ├── algorithm_rules.md       # LinkedIn 2026 algorithm rules
│   ├── scoring_weights.json     # Current engagement scoring weights
│   ├── audience_personas.md     # Virtual audience persona definitions
│   └── niche_topics.md          # Your 2-3 core expertise topics
├── memory/
│   ├── performance_history.json # Every post's predicted vs actual
│   ├── winning_templates.md     # Posts that outperformed
│   ├── anti_patterns.md         # Patterns that underperformed
│   └── lessons_learned.md       # Auto-generated improvement notes
├── research/
│   ├── top_posts_analysis.md    # Analysis of top niche posts
│   └── topic_research/         # Per-topic deep research
├── output/
│   ├── variants/                # Generated post variants
│   └── scores/                  # Simulation scores per variant
└── scripts/
    ├── research_agent.md        # Research agent prompt/skill
    ├── writer_agent.md          # Writer agent prompt/skill
    ├── simulator_agent.md       # Simulation/scoring prompt/skill
    └── feedback_agent.md        # Auto-improvement loop prompt/skill
```

---

## HOW TO BUILD THIS (Step by Step)

### Phase 1: MVP (Week 1) — Claude Code / Amp
1. Create voice_profile.md from your past posts
2. Build research_agent.md skill
3. Build writer_agent.md skill (generates 6 variants)
4. Build simulator_agent.md skill (scores all 6)
5. Manual performance tracking → feed back into system

### Phase 2: Automation (Week 2-3)
1. Add n8n workflow for scheduled research
2. Connect Firecrawl/Exa for automated top-post scraping
3. Build performance tracking input mechanism
4. Implement auto-loop feedback agent

### Phase 3: Intelligence (Week 4+)
1. After 20+ tracked posts, calibrate simulation accuracy
2. Build pattern recognition (weekly analysis)
3. Voice drift detection (monthly)
4. Graduate from MVP scoring to calibrated prediction model

### Optional: External Integration
- **Artificial Societies "Reach"** for advanced audience simulation
- **Anyword.ai** for independent performance prediction validation
- **n8n** for full workflow automation
