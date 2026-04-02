# LinkedIn Post Writer — Research & Resources (Jan–Apr 2026)

## 🎯 Your Vision
Build the world's best LinkedIn post writer that:
- Uses AI agents (Claude Code / Codex) — no LinkedIn API needed
- Analyzes top posts & adapts your voice/tone
- Generates 5-6 variants → simulates engagement → picks the best one
- Does deep research on your topic before writing

---

## 1. SPECIALIZED LINKEDIN AI AGENT TOOLS (Launched/Updated 2026)

### Tier 1 — Best Fit for Your Architecture

| Tool | What It Does | Why It Matters | Link |
|------|-------------|----------------|------|
| **LiGo Post Lab** | Suite of specialized AI agents (Content Repurposer, Hot Take Generator, Campaign Builder, Story Crafter, Best Post Reviver). Voice matching, strategic intelligence, human-review workflow. | Closest to your "generate multiple → pick the best" concept. Agents pull from your saved ideas. | [ligosocial.com/blog/best-ai-agents-for-linkedin-content-creation](https://ligosocial.com/blog/best-ai-agents-for-linkedin-content-creation) |
| **LangChain Social Media Agent** | Open-source agent (GitHub) that takes a URL → generates LinkedIn + Twitter posts with HITL. Uses Anthropic API, Firecrawl, Arcade for posting. Customizable post style & few-shot examples. | **Best open-source starting point.** You can fork this and add simulation/scoring. | [github.com/langchain-ai/social-media-agent](https://github.com/langchain-ai/social-media-agent) |
| **Leaps** | "Anti-AI slop" platform. Won't write until it understands your POV. Uses async interviews to capture your voice. Human-led, AI-assisted. | The gold standard for voice-matching without producing generic content. $49-149/mo. | [leapshq.com](https://leapshq.com/blog/best-linkedin-post-generators) |
| **Latitude (Personal Content AI)** | AI personal content agent for LinkedIn. Learns what resonates with your audience, suggests ideas, schedules, tracks performance. 14-day free trial. Founded 2025, active 2026. | Has the "learns from your performance data" feedback loop you want. | [get-latitude.com](https://www.linkedin.com/company/get-latitude-ai) |
| **AuthorityMax** | Learns your tone/structure from existing posts. Asks clarifying questions before writing. Has LinkedIn-optimized templates, smart scheduling, performance feedback. | Strong voice-matching + doesn't write until it understands your angle. | [authoritymax.ai](https://authoritymax.ai/blog/linkedin-posts-ai-writing-tools-to-sound-human) |

### Tier 2 — Established Players (Updated for 2026)

| Tool | Key Feature | Link |
|------|-------------|------|
| **Taplio** | Viral post library + lead database + scheduling + analytics. All-in-one. | [taplio.com](https://taplio.com) |
| **ContentIn** | AI Ghostwriter trained on your past content + 1000s of viral templates + carousel generator. | [contentin.io](https://contentin.io) |
| **RedactAI** | Personalized AI model from your past posts + content recycling + performance stats. | [redactai.io](https://redactai.io) |
| **Anyword.ai** | **A/B testing with performance prediction.** Compares variations and predicts which will perform better. | [anyword.com](https://anyword.com) |
| **WRITER** | New voice functionality — train agents on any voice, then build LinkedIn post agents in your voice. Matt Sobel demo (March 2026). | [writer.com](https://www.linkedin.com/posts/mattesobel_friday-means-its-time-for-another-writer-activity-7418013611115212801-6944) |

---

## 2. BUILD-IT-YOURSELF APPROACH (Using Claude Code / Codex)

### Key Resources

| Resource | Description | Link |
|----------|-------------|------|
| **Scott Martinis: Self-Improving Agent on Claude Code** | Built a self-improving LinkedIn agent with Slack integration, persistent memory (CLAUDE.md + identity files + daily logs), heartbeat scheduling, and agent identity that persists across sessions. Reverse-engineered OpenClaw's architecture. | [LinkedIn post](https://www.linkedin.com/posts/scott-martinis_last-week-i-said-i-wanted-to-build-a-self-improving-activity-7427018578551439360-Z_pP) |
| **Devon Coombs: Codex Practitioner's Guide** | Detailed walkthrough of building agent workflows with Codex (GPT-5.4). Covers AGENTS.md files, skill files, retrospective loops. Published Mar 31, 2026. | [LinkedIn article](https://www.linkedin.com/pulse/openai-codex-practitioners-guide-building-ai-agents-devon-coombs-jnmlc) |
| **Nate Herkelman: Claude Code + n8n** | How to supercharge Claude Code with n8n knowledge to turn workflows into web apps in 30 minutes. | [LinkedIn post](https://www.linkedin.com/posts/nateherkelman) |
| **German Arutyunov: 3-Stage Claude Code Workflow** | Research (Haiku) → Write (Sonnet) → Review & Fix (Opus). Proven effective for high-quality output. | [LinkedIn comment thread](https://www.linkedin.com/posts/vaibhavs10_this-is-a-brilliant-read-for-anyone-building-activity-7411337608620011520-wQqO) |
| **Ed Gandia: AI Tone Guide Prompt** | A prompt that creates a complete voice brief (tone, formality, sentence rhythm, sentence palette) from 3-4 writing samples in <10 minutes. | [LinkedIn post](https://www.linkedin.com/posts/edgandia_dont-have-a-tone-guide-from-your-client-activity-7392182880925347840-G2bY) |

### Architecture Pattern for Your Tool

Based on the research, here's the architecture the top builders are converging on:

```
┌─────────────────────────────────────────────────┐
│                YOUR LINKEDIN AGENT               │
├─────────────────────────────────────────────────┤
│                                                   │
│  1. VOICE CAPTURE                                │
│     - Feed 10-20 of your past LinkedIn posts     │
│     - Generate a voice brief (tone, rhythm,      │
│       vocabulary, sentence structure)            │
│     - Store as identity/voice file               │
│                                                   │
│  2. RESEARCH AGENT (Haiku/fast model)            │
│     - Deep research on your topic intention      │
│     - Analyze top-performing posts in your niche │
│     - Pull trending angles, data points          │
│     - Scrape relevant content (Firecrawl/Exa)    │
│                                                   │
│  3. GENERATION AGENT (Sonnet/main model)         │
│     - Generate 5-6 post variants                 │
│     - Each with different hooks, angles, formats │
│     - All in YOUR voice (from voice file)        │
│     - Apply LinkedIn algorithm best practices    │
│                                                   │
│  4. SIMULATION / SCORING AGENT (Opus/strong)     │
│     - Score each variant on:                     │
│       • Hook strength (first 150 chars)          │
│       • Dwell time potential                     │
│       • Comment-worthiness                       │
│       • Save-worthiness                          │
│       • Voice authenticity                       │
│     - Rank and pick the winner                   │
│                                                   │
│  5. HUMAN REVIEW                                 │
│     - Present top 2-3 with reasoning             │
│     - You pick / edit / approve                  │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## 3. LINKEDIN ALGORITHM INTELLIGENCE (2026)

Critical data from Richard van der Blom's 1.8M+ post analysis and LinkedIn's own guidance:

### What the Algorithm Rewards in 2026
- **"360 Brew" AI system** — reads content semantically, checks if content matches author's profile/expertise
- **Dwell time > likes** — how long people read matters more than reactions
- **First 60 minutes are critical** — only 5% of underperforming posts recover
- **Saves and comments are king** — the biggest metrics for reach
- **Niche depth over broad reach** — algorithm rewards demonstrated expertise
- **External links penalized ~60%** — even "link in first comment" is penalized

### Best Performing Formats (2026)
| Format | Avg Engagement | Notes |
|--------|---------------|-------|
| **PDF Carousels** | 6.60% | 278% more than video, 596% more than text |
| **Native Video (30-90s)** | 5.60% | Growing 2x faster, must include captions |
| **Strategic Text** | 2-4% | Strong hooks, short paragraphs, no links |

### Content Rules for Maximum Engagement
- First 150 characters = everything (before "See more")
- One-line paragraphs for mobile
- 200-300 words for short posts, 800-1200 for articles
- 95% of citations come from ORIGINAL posts (not reshares)
- Post 3-5x/week maximum
- 10+ comments on a post significantly helps reach
- AI-generated generic content is actively detected and deprioritized

Source: [dataslayer.ai/blog/linkedin-algorithm-february-2026](https://www.dataslayer.ai/blog/linkedin-algorithm-february-2026-whats-working-now)

---

## 4. OPEN-SOURCE FRAMEWORKS TO BUILD WITH

| Framework | Use For | Link |
|-----------|---------|------|
| **LangChain Social Media Agent** | Fork as your base. Has HITL, post generation, scheduling. | [github.com/langchain-ai/social-media-agent](https://github.com/langchain-ai/social-media-agent) |
| **CrewAI** | Multi-agent orchestration (Research Agent + Writer Agent + Reviewer Agent). | [github.com/crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) |
| **n8n** | Visual workflow automation — connect AI to scheduling, analytics, research. Self-hostable. | [n8n.io](https://n8n.io) |
| **Firecrawl** | Web scraping for research (scrape top posts, competitor content). | [firecrawl.dev](https://firecrawl.dev) |
| **Arcade** | Social media auth & scheduling without building your own OAuth. | [arcade.dev](https://arcade.dev) |
| **awesome-ai-agents-2026** | Comprehensive 300+ resource list of all AI agent tools. | [github.com/caramaschiHG/awesome-ai-agents-2026](https://github.com/caramaschiHG/awesome-ai-agents-2026) |

---

## 5. KEY ARTICLES & GUIDES (Jan–Apr 2026)

| Title | Author | Why Read It |
|-------|--------|-------------|
| "Best AI LinkedIn Post Generators in 2026" | Leaps (Jan 2026) | Comprehensive comparison of 8+ tools with pricing. Anti-slop philosophy. |
| "Best AI Agents for LinkedIn Content Creation in 2026" | LiGo / Junaid Khalid (Mar 2026) | Explains agents vs tools, voice matching, strategic intelligence. |
| "How to Leverage LinkedIn for AI Visibility in 2026" | LinkedIn Official / Davang Shah (Mar 2026) | LinkedIn's OWN guide to what works. Educational content, original posts, credibility > virality. |
| "How I Doubled My LinkedIn Impressions in 28 Days Using Claude" | Neeraj Shah (2026) | Practical case study of using Claude for LinkedIn growth. |
| "How to Use AI to Write LinkedIn Posts That Get You Paid" | The AI Studio / Medium (Mar 2026) | 15-35% of LinkedIn posts are now partially AI-written. Framework for standing out. |
| "LinkedIn Algorithm Feb 2026" | Dataslayer.ai (Feb 2026) | Data-driven breakdown: PDF carousels = 6.6% engagement, text = 2-4%. |

---

## 6. THE "SIMULATION" CONCEPT — Who's Doing It

Your idea of **generating multiple posts → simulating performance → picking the winner** is cutting-edge. Here's who's closest:

1. **Anyword.ai** — Has built-in **performance prediction** and A/B testing. Compares variations and predicts which will perform better before publishing. Closest to your vision.

2. **LiGo Post Lab** — Multiple specialized agents generate different types of content. You review all and pick the best. Not automated simulation, but multi-variant.

3. **CrewAI Multi-Agent Pattern** — You could build: `Writer Agent (generates 5 variants)` → `Critic Agent (scores each)` → `Selector Agent (picks winner)` → `Human Review`. This is the pattern Scott Martinis and others are building with Claude Code.

4. **German Arutyunov's 3-Stage Workflow** — Research (Haiku) → Write (Sonnet) → Review (Opus). The review stage with Opus acts as the "simulation" — it evaluates quality against the original intent.

---

## 7. RECOMMENDED TECH STACK FOR YOUR BUILD

```
Core Engine:     Claude Code (Amp) — orchestration + generation
Research:        Firecrawl + Exa web search — scrape top posts + research topics
Voice Capture:   Ed Gandia's tone guide prompt + your past posts as few-shot examples
Multi-Agent:     CrewAI or LangChain — for Research → Write → Score → Select pipeline
Scoring:         Claude Opus — evaluate posts against LinkedIn algorithm rules
Workflow:        n8n — connect everything, schedule, track
Analytics:       Dataslayer.ai — track actual performance to feed back into the system
Base Template:   Fork langchain-ai/social-media-agent as starting point
```

---

## 8. WHAT DOESN'T EXIST YET (Your Opportunity)

Nobody has built the full loop you're describing:
1. ✅ Voice capture → exists (Leaps, AuthorityMax, WRITER)
2. ✅ Deep research → exists (Perplexity, Deep Research, Firecrawl)
3. ✅ Multi-variant generation → partially exists (LiGo agents)
4. ⚠️ **Engagement simulation before posting** → Anyword predicts, but nobody SIMULATES with persona-based virtual audiences
5. ⚠️ **Automated pick-the-winner** → Nobody fully automates this with Claude Code
6. ❌ **Full closed-loop learning** → Nobody feeds actual post performance back into the generation system automatically

**This is your blue ocean.** The full pipeline with simulation is what would make yours "the world's best."
