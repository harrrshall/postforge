# Audience Personas — PostForge Engagement Simulation

## Persona 1: The Busy Founder
**Profile:** 35-50, runs a 10-50 person business in Tier 1 Indian city (Mumbai, Bangalore, Delhi). Uses WhatsApp for everything. Heard about AI but hasn't implemented it. Scrolls LinkedIn for 10 min during morning chai.

**LinkedIn Behavior:**
- Scroll speed: Fast (1-2 seconds per post)
- Stops for: Bold ROI claims with specific numbers, "saved X hours" or "earned ₹Y more"
- Engagement pattern: Likes > Saves > Rarely comments
- Time on platform: 10-15 min/day, morning
- Network size: 500-2000 connections

**What triggers action:**
- STOP SCROLLING: Specific revenue/time number in first line ("₹2L/month recovered")
- SAVE: Actionable framework they can implement this week
- COMMENT: Only if they've experienced the exact pain point described
- SHARE: Almost never (too busy, don't want to seem like they need help)
- SKIP: Generic advice, long text without numbers, anything that feels like a pitch

**Simulation rules:**
- If hook contains specific ₹ amount or time saved → READ (70%) or SAVE (30%)
- If hook is generic → SKIP (90%)
- Comments only when post describes their exact daily frustration
- Never shares. Saves practical frameworks.

---

## Persona 2: The Tech Peer
**Profile:** 25-40, developer or AI practitioner. Works at a startup or tech company. Builds with AI tools daily. Follows OpenClaw, LangChain, Anthropic discourse. Deep technical knowledge.

**LinkedIn Behavior:**
- Scroll speed: Medium (reads hooks, skips fluff)
- Stops for: Technical depth, novel architecture, contrarian tech opinions
- Engagement pattern: Comments > Likes (they engage with substance)
- Time on platform: 20-30 min/day, spread across day
- Network size: 1000-5000 connections

**What triggers action:**
- STOP SCROLLING: Technical specificity ("512 vulnerabilities", "3-layer pipeline", architecture diagrams)
- SAVE: Technical frameworks, code patterns, architecture decisions
- COMMENT: To add nuance, challenge an assumption, share their own experience
- SHARE: If post contains genuinely novel technical insight
- SKIP: Surface-level AI hype, no technical depth, marketing speak

**Simulation rules:**
- If post has technical depth → COMMENT (60%) with substantive addition
- If post has novel architecture → SAVE (50%) + COMMENT (40%)
- If post is surface-level → SKIP (80%)
- Comments are 20+ words, add context or challenge a specific claim
- Will share if they've never seen this technical angle before

---

## Persona 3: The Aspiring SMB Owner
**Profile:** 25-35, runs a small shop/clinic/coaching center in Tier 2-3 Indian city. Wants to grow but overwhelmed by technology. Sees AI as both opportunity and mystery. Uses LinkedIn to learn, not to network.

**LinkedIn Behavior:**
- Scroll speed: Slow (reads carefully when topic is relevant)
- Stops for: Simple explanations, step-by-step guides, "how to" content
- Engagement pattern: Saves >> Likes > Rarely comments
- Time on platform: 15-20 min/day, evening
- Network size: 200-800 connections

**What triggers action:**
- STOP SCROLLING: "How to [solve their problem] in [specific steps]"
- SAVE: Every framework, checklist, how-to, template
- COMMENT: Only to ask a question ("How much does this cost?" "Does this work in Hindi?")
- SHARE: To their WhatsApp groups (not on LinkedIn)
- SKIP: Jargon-heavy posts, content for large enterprises, abstract thought leadership

**Simulation rules:**
- If post is a framework/carousel → SAVE (80%) + READ fully (90%)
- If post has jargon without explanation → SKIP (70%)
- If post mentions specific Indian city/context → engagement +30%
- Comments are questions, not opinions
- Highest dwell time of all personas (reads everything relevant)

---

## Persona 4: The Contrarian
**Profile:** 30-50, industry veteran or consultant. Has opinions. Loves debate. Engages to challenge, add nuance, or play devil's advocate. Often has 5000+ followers.

**LinkedIn Behavior:**
- Scroll speed: Medium-fast (looking for something to react to)
- Stops for: Bold claims, controversial opinions, oversimplified takes
- Engagement pattern: Comments >> everything else
- Time on platform: 30+ min/day
- Network size: 3000-10000+ connections

**What triggers action:**
- STOP SCROLLING: "Most people think X. They're wrong." / Bold claim that invites pushback
- SAVE: Rarely (unless it's data they want to reference in their own counter-argument)
- COMMENT: To disagree, add nuance, share a counter-example, challenge the data
- SHARE: With their own commentary adding the counter-perspective
- SKIP: Posts that are too agreeable, no edge, no opinion to push back on

**Simulation rules:**
- If post has a bold claim → COMMENT (80%) with disagreement or nuance
- If post is a "hot take" → COMMENT (90%) with "Yes, but..." or "Actually..."
- If post is a neutral framework → SKIP (60%) or LIKE only (30%)
- Comments are 30+ words, always add a counter-perspective
- Their comments often generate thread discussions (high algorithmic value)

---

## Persona 5: The Silent Lurker
**Profile:** Any age, any role. Reads everything in their feed but almost never engages visibly. High dwell time, low visible engagement. Represents ~70% of LinkedIn users.

**LinkedIn Behavior:**
- Scroll speed: Slow-medium (reads fully if hook works)
- Stops for: Anything in their interest area that looks valuable
- Engagement pattern: READ >> occasional Like >> very rare Save >> almost never Comment
- Time on platform: 20-40 min/day
- Network size: Variable

**What triggers action:**
- STOP SCROLLING: Same triggers as other personas but lower threshold
- SAVE: Only exceptional content they know they'll need later
- COMMENT: Almost never (maybe once a month)
- SHARE: Never
- SKIP: If hook doesn't grab in 2 seconds

**Simulation rules:**
- If hook works → READ fully (80%), estimated dwell 30-90 seconds
- If carousel → swipe through all slides (70%), dwell 60-120 seconds
- LIKE probability: 15% of reads
- SAVE probability: 5% of reads (only frameworks/data)
- COMMENT probability: 1% of reads
- Their dwell time is the primary algorithm signal they generate
- High aggregate dwell time from lurkers = broad distribution signal

---

## Simulation Matrix

For each variant, predict each persona's action:

| Persona | SKIP | SKIM | READ | LIKE | COMMENT | SAVE | SHARE |
|---------|------|------|------|------|---------|------|-------|
| Busy Founder | % | % | % | % | % | % | % |
| Tech Peer | % | % | % | % | % | % | % |
| Aspiring SMB | % | % | % | % | % | % | % |
| Contrarian | % | % | % | % | % | % | % |
| Lurker | % | % | % | % | % | % | % |

**Engagement prediction formula:**
```
predicted_engagement = sum(
  persona_weight * sum(action_probability * action_value)
  for each persona
)

Action values: SKIP=0, SKIM=0.1, READ=0.5, LIKE=1, COMMENT=15, SAVE=5, SHARE=10
Persona weights: Equal (0.20 each) — adjusted by calibration after 20+ posts
```
