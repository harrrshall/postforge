# LinkedIn 2026 Algorithm Rules (360Brew Era)

## 1. 360Brew — The Ranking Engine

LinkedIn replaced its entire content ranking infrastructure with **360Brew**: a 150-billion-parameter decoder-only transformer trained entirely on LinkedIn's networking data.

### How 360Brew Works
- Reads content semantically before showing it to any human
- Checks for spam signals: too many tags, hashtag stuffing, engagement bait
- Performs **AI fingerprinting**: detects generic, unedited AI-written text
- Assigns your profile a **"Topic DNA"** based on headline, about section, and past posts
- Cross-references post topic with your professional expertise
- Posts aligned with verified expertise get **40% higher organic impressions**
- Off-topic posts get actively suppressed

### Interest Graph (replaces Social Graph)
- Content is now judged on merit and topical authority, NOT connection count
- Algorithm maps content to professionals who consume your topic cluster
- Your post can reach ANYONE on the platform who's interested in your topic
- This means: niche depth > broad reach

### Topic DNA
- 360Brew calculates a relevance score by mapping your professional history against post topics
- Profiles with scattered topic signals get diluted reach
- **Consistency is a technical requirement for reach**
- Posting about unrelated topics confuses the algorithm

## 2. Engagement Signal Hierarchy

Ranked by algorithmic impact (highest to lowest):

| Signal | Weight vs Like | Why It Matters |
|--------|---------------|----------------|
| **Saves (Bookmarks)** | **5x a like, 2x a comment** | Strongest quality indicator. Drives massive reach. |
| **Substantive Comments** (10+ words) | **15x a like** | 20 quality comments >> 100 likes. Thread depth counts. |
| **Dwell Time** (seconds reading) | High | 0-3s = "click bounce" = penalty. 60+ seconds = boost. |
| **Shares with Commentary** | High | "Reposts with insight" are prioritized. Blind reposts invisible. |
| **Engagement Velocity** | Critical | First 60-90 min make-or-break. Triggers "Momentum Model." |
| **Likes/Reactions** | 1x (baseline) | Lowest value signal. Quantity without quality = nothing. |

### Depth Score
Composite metric LinkedIn uses to evaluate whether content is actually valuable or just "noisy."
- A post with 200 saves dramatically outperforms a post with 1,000 likes
- Comment quality (length, relevance, authority of commenter) matters more than count

## 3. Critical Timing Rules

### The Golden Hour
- First **60-90 minutes** after posting are make-or-break
- If substantive comments land in this window → 360Brew "Momentum Model" triggers
- Post gets categorized as "trending" within its niche
- Only **5% of underperforming posts recover** after a weak first hour

### Optimal Posting Times (IST)
- **Peak:** Wednesday 9:00 AM
- **Strong:** Tuesday-Thursday, 8:00-10:00 AM
- **Weekend:** Saturday 10:00 AM (lighter competition)
- **Avoid:** Sunday, late evenings

### Posting Frequency
- **Sweet spot:** 5-7 posts/week for aggressive growth
- **Maximum without penalty:** 1 post/day
- **Penalty zone:** 2+ posts/day → **40% drop in per-post reach**
- LinkedIn compounds visibility with consistent frequency (doesn't cap reach)

## 4. Format Performance (2026 Data)

| Format | Avg Engagement Rate | Dwell Time Signal | Best Use |
|--------|-------------------|-------------------|----------|
| **PDF Carousel** | **6.60%** (+596% vs text) | Very High (every swipe = dwell) | Frameworks, data stories, tutorials |
| **Native Video** (<90s) | **5.60%** | High (face in first 4s = +69%) | Demos, hot takes, behind-scenes |
| **Strategic Text** | **2-4%** | Medium (hook-dependent) | Stories, contrarian takes, personal |
| **Document/Long-form** | **1-3%** (but high save rate) | High | Deep frameworks, industry analysis |
| **Poll** | **2-3%** | Low | Community research, quick engagement |
| **Single Image** | **1-2%** | Low | Avoid as primary format |

### Carousel-Specific Rules
- Every swipe counts as dwell time → massive positive algorithm signal
- Optimal: 5-8 slides
- Each slide: one clear idea
- Works best when teaching something practical
- Keeps users ON LinkedIn (vs links that send them away)

### Video-Specific Rules
- Face/brand in first 4 seconds = +69% performance boost
- Under 90 seconds optimal
- Must include captions (mobile first)
- Vertical format preferred

## 5. Content Constraints

### MUST DO
- First 150 characters = scroll-stopper (before "See more" truncation)
- Short paragraphs: 1-3 lines max (mobile readability)
- 200-300 words for text posts
- One clear, actionable takeaway per post
- CTA that invites sharing experiences (not generic "Thoughts?")
- Stick to 2-3 core expertise topics (Topic DNA)
- Profile-content alignment (posts match headline/about)
- Target 15+ substantive comments in first 60 minutes
- High lexical diversity (vary vocabulary, sentence structure)
- 95% of citations come from ORIGINAL posts (not reshares)

### MUST NOT
- No external links in post body (**60% reach penalty**)
- No "link in first comment" (also penalized in 2026)
- No engagement bait ("Comment YES if you agree", "Tag someone who")
- No generic AI patterns ("In today's fast-paced world", "Let me break it down")
- No "bro-etry" (one-line paragraphs with empty platitudes)
- No excessive hashtags (max 3-5, in first comment only)
- No AI-generated generic content (360Brew detects and deprioritizes)
- No posting outside your niche (expertise matching is enforced)
- No blind reposts without commentary (invisible in feed)
- No engagement pods (**97% detection accuracy**, instant shadowban)

## 6. AI Detection Avoidance

360Brew's AI detection looks for:
1. **Low lexical diversity** — AI tends to repeat patterns; humans vary naturally
2. **Generic phrasing** — "Let me share", "Here's what I learned", "Game-changer"
3. **Perfect grammar with no personality** — Too polished = suspicious
4. **Profile-content mismatch** — AI-written content lacks contextual professional language
5. **Engagement bait patterns** — Generic CTAs that AI tools default to

### How to Pass 360Brew
- Edit AI output to include personal voice, specific examples, real data
- Reference specific people, companies, situations
- Use contractions, informal language, personality markers
- Maintain vocabulary consistent with your past posts
- Include domain-specific jargon that shows real expertise
- Vary sentence length dramatically (short punch. Then a longer, more flowing thought.)

## 7. Engagement Mechanics

### Comments
- 10+ words = "substantive" → highest algorithmic weight
- Comments from authoritative, relevant accounts weigh more
- Thread depth matters (replies to comments create threads)
- Every reply you make in first hour extends distribution
- 10 comments from industry peers > 100 from randoms

### Saves
- Save = "this is reference material" signal
- Drives 5x more reach than a like
- Frameworks, checklists, data = highest save rate
- Carousel format optimized for saves (swipe = value)

### Dwell Time
- Measured in exact seconds per user
- 0-3 seconds = "click bounce" = negative signal
- 60+ seconds = strong positive signal
- Progressive revelation (keep reading) = dwell time hack
- Carousel swipes count as dwell time

## Sources
- Richard van der Blom's 1.8M+ post analysis
- LinkedIn's 360Brew documentation
- Dataslayer.ai algorithm analysis (Feb 2026)
- Sprout Social algorithm guide (2026)
- Buffer posting frequency study (2M+ posts)
- Linkmate engagement strategy guide (2026)
