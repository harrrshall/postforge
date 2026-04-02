# Repo Analysis & Voice Capture Strategy

---

## 🔍 REPO 1: Agent-Reach (Panniantong/Agent-Reach)

### What it is
A **scaffolding/installer tool** that wires 17 internet platforms (Twitter, Reddit, YouTube, LinkedIn, Exa, Bilibili, WeChat, etc.) into your AI agent (Claude Code, Cursor, OpenClaw). It installs upstream CLI tools and MCP servers so your agent can read/search these platforms natively.

### Usefulness for PostForge: ⭐⭐⭐⭐ HIGH

| Your Need | Agent-Reach Does It? |
|-----------|---------------------|
| Scrape top LinkedIn posts for analysis | ✅ LinkedIn MCP: `get_person_profile`, Jina Reader fallback |
| Search LinkedIn profiles/people | ✅ `linkedin-scraper.search_people` |
| Scrape Twitter for engagement patterns | ✅ `twitter-cli` / `bird` CLI |
| Search Reddit for content ideas | ✅ `rdt-cli` |
| Web search for topic research | ✅ Exa MCP via mcporter |
| YouTube transcript extraction | ✅ `yt-dlp` |
| Read any web page | ✅ Jina Reader (`curl https://r.jina.ai/URL`) |

### What it does NOT do
- ❌ No engagement prediction
- ❌ No post generation
- ❌ No simulation
- ❌ No auto-improvement loop
- ❌ LinkedIn MCP is READ-ONLY (no posting)

### Verdict
**USE IT as your RESEARCH LAYER.** Install Agent-Reach to give your PostForge system eyes on 17 platforms. It directly powers Phase 1 (Deep Research Agent) — scraping competitor posts, analyzing top performers, pulling trending topics from Reddit/Twitter/YouTube. Zero config for 8 channels, free API key for 5 more.

### Installation
```bash
pip install agent-reach
agent-reach install       # installs all upstream tools
agent-reach doctor        # health check all channels
agent-reach configure     # set API keys
```

---

## 🔍 REPO 2: MiroFish (JayFarei/MiroFish)

### What it is
A **multi-agent societal simulation engine** — a "digital twin of society." You upload seed content → it creates thousands of AI agents with unique personas (MBTI, profession, interests) → they interact on simulated Twitter/Reddit → it generates a Future Prediction Report.

### Architecture (5 stages)
1. **Graph Building** — Zep GraphRAG ingests your documents into a knowledge graph
2. **Environment Setup** — CAMEL-AI OASIS generates agent personas from entities
3. **Simulation** — Thousands of AI agents interact on simulated Twitter/Reddit
4. **Report Generation** — ReACT agent loop analyzes simulation → produces report
5. **Deep Interaction** — Chat with any simulated agent

### Tech Stack
- Python 3.11+, Flask 3.x, Vue 3.5
- **Zep Cloud** (GraphRAG memory)
- **CAMEL-AI OASIS** (social interaction simulation engine)
- OpenAI SDK (Qwen-plus or Claude Code headless)
- D3.js for graph visualization

### Usefulness for PostForge: ⭐⭐⭐ MEDIUM-HIGH (as component source)

| Your Need | MiroFish Component |
|-----------|-------------------|
| Simulate audience engagement with posts | ⭐⭐⭐⭐ **CAMEL-AI OASIS** — simulates agents posting, liking, commenting on content. Could be fed LinkedIn posts as seed. |
| Generate audience personas | ⭐⭐⭐⭐⭐ **OasisProfileGenerator** — creates rich personas (MBTI, profession, interests, bio, personality). Directly applicable. |
| Auto-improvement loop | ⭐⭐⭐ **ReACT Loop pattern** in ReportAgent — clean Thought→Tool→Observation→Answer cycle, adaptable for post iteration. |
| Memory across iterations | ⭐⭐⭐ **Zep GraphRAG** — stores and retrieves facts about past performance, learnable history. |
| Content generation | ❌ Generates prediction reports, NOT social media posts |
| Scoring content quality | ❌ Observes emergent behavior but doesn't score posts |

### Verdict
**DON'T use MiroFish as a whole** (it's a societal prediction tool, architecturally misaligned). **BUT extract 3 key components:**

1. **CAMEL-AI OASIS** → Use its social simulation engine to simulate how virtual LinkedIn personas would react to your posts. Feed your 6 post variants as "seed content" and observe simulated likes/comments/shares. This is the engagement simulation engine.

2. **OasisProfileGenerator** → Use its persona generation code to create your 5 virtual LinkedIn audience personas with real depth (not just labels, but MBTI, profession, interests, personality descriptions).

3. **ReACT Loop** (from ReportAgent) → Adapt this pattern for your auto-improvement feedback agent. Thought: "Post X got 50% less engagement than predicted" → Tool: analyze hook/format/timing → Observation: "Hook was generic" → Action: update scoring weights.

---

## 🎤 VOICE CAPTURE: Handling Hundreds of MBs of Text

### The Challenge
You have hundreds of MBs of your own text. A standard LLM context window (even Claude's 200K tokens ~= 150K words ~= ~600KB) can't hold it all at once. You need a **chunked extraction pipeline**.

### Strategy: 3-Layer Voice Fingerprint Extraction

```
LAYER 1: Statistical Analysis (runs on ALL text, no LLM needed)
──────────────────────────────────────────────────────────────
Tools: Python NLP libraries (spaCy, NLTK, textstat)

Extract:
├── Vocabulary frequency map (your most-used 500 words)
├── Average sentence length + distribution
├── Paragraph length patterns
├── Readability scores (Flesch-Kincaid, Coleman-Liau)
├── Punctuation patterns (semicolons, dashes, ellipses)
├── Emoji/symbol usage frequency
├── Question frequency (rhetorical vs genuine)
├── Contraction usage (don't vs do not)
├── Active vs passive voice ratio
├── First person vs third person ratio
├── Transition word preferences
└── Unique phrases / pet phrases (n-gram analysis)

OUTPUT → voice_stats.json


LAYER 2: Sampled LLM Analysis (runs on ~50 representative chunks)
──────────────────────────────────────────────────────────────
Randomly sample 50 chunks of ~2000 words each from your corpus.
For each chunk, Claude Haiku analyzes:

├── Tone classification (warm/direct/analytical/casual/authoritative)
├── Humor style (sarcastic/dry/wholesome/none)
├── Argument structure (claim→evidence→conclusion or story→lesson)
├── Opening patterns (question/stat/story/bold claim/scenario)
├── Closing patterns (CTA/reflection/challenge/summary)
├── Emotional register (high energy/measured/contemplative)
├── Metaphor/analogy preferences
├── How you handle disagreement
├── How you introduce data/statistics
└── Cultural references / domain jargon

Aggregate all 50 analyses → find consensus patterns.

OUTPUT → voice_analysis.md


LAYER 3: Distilled Voice DNA (final synthesis)
──────────────────────────────────────────────────────────────
Claude Opus takes voice_stats.json + voice_analysis.md and produces:

voice_profile.md:
├── TONE: [2-3 sentence description]
├── RHYTHM: [sentence length patterns, pacing]
├── VOCABULARY: [word cloud of signature words + words to avoid]
├── STRUCTURE: [how you build arguments/narratives]
├── OPENINGS: [5 example opening patterns in your style]
├── TRANSITIONS: [5 bridge phrases you naturally use]
├── CLOSINGS: [5 ending patterns in your style]
├── PERSONALITY MARKERS: [humor, empathy, directness level]
├── ANTI-PATTERNS: [things you NEVER say/do]
├── SENTENCE PALETTE: [10 reusable sentence templates from your actual writing]
└── FEW-SHOT EXAMPLES: [5 best paragraphs from your corpus]

This file is ~2-3 pages and is loaded into every generation session.
```

### Implementation Script Skeleton

```python
# voice_extractor.py — runs on your hundreds of MBs of text

import os, json, random
from collections import Counter
import spacy
import textstat

# ─── LAYER 1: Statistical Analysis ───
def extract_stats(text_corpus: str) -> dict:
    nlp = spacy.load("en_core_web_sm")
    
    stats = {
        "total_words": len(text_corpus.split()),
        "total_chars": len(text_corpus),
        "avg_sentence_length": 0,
        "avg_paragraph_length": 0,
        "readability_flesch": textstat.flesch_reading_ease(text_corpus[:100000]),
        "top_500_words": [],
        "top_100_bigrams": [],
        "top_50_trigrams": [],
        "question_frequency": text_corpus.count("?") / len(text_corpus.split()) * 100,
        "exclamation_frequency": text_corpus.count("!") / len(text_corpus.split()) * 100,
        "contraction_ratio": 0,  # calculate don't/do not ratio
        "first_person_ratio": 0, # I/me/my vs he/she/they
    }
    
    # Word frequency
    words = text_corpus.lower().split()
    word_freq = Counter(words)
    stats["top_500_words"] = word_freq.most_common(500)
    
    # N-grams for pet phrases
    bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words)-1)]
    trigrams = [f"{words[i]} {words[i+1]} {words[i+2]}" for i in range(len(words)-2)]
    stats["top_100_bigrams"] = Counter(bigrams).most_common(100)
    stats["top_50_trigrams"] = Counter(trigrams).most_common(50)
    
    return stats

# ─── LAYER 2: Sampled LLM Analysis ───
def sample_and_analyze(text_corpus: str, num_samples=50, chunk_size=2000):
    words = text_corpus.split()
    chunks = []
    for _ in range(num_samples):
        start = random.randint(0, len(words) - chunk_size)
        chunk = " ".join(words[start:start + chunk_size])
        chunks.append(chunk)
    
    # Send each chunk to Claude Haiku with voice analysis prompt
    # Aggregate results across all 50 chunks
    # Return consensus analysis
    pass

# ─── LAYER 3: Synthesis ───  
def synthesize_voice_profile(stats: dict, analysis: str) -> str:
    # Send stats + analysis to Claude Opus
    # Generate final voice_profile.md
    pass
```

### Key Insight: Continuous Voice Refinement
After every post you publish + edit, the system compares:
- What it generated vs what you actually published
- Your edits reveal what the voice profile is missing
- Auto-update voice_profile.md with learned corrections
- After 20+ posts, the voice profile becomes near-perfect

---

## UPDATED ARCHITECTURE (with repos integrated)

```
┌─────────────────────────────────────────────────┐
│              POSTFORGE SYSTEM                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  RESEARCH LAYER (Agent-Reach)                    │
│  ├── LinkedIn scraping (top posts, profiles)     │
│  ├── Twitter trending topics                     │
│  ├── Reddit discussions for angles               │
│  ├── YouTube transcripts for ideas               │
│  ├── Exa web search for data/stats               │
│  └── Jina Reader for any web page                │
│                                                  │
│  VOICE LAYER (Custom 3-Layer Pipeline)           │
│  ├── Layer 1: spaCy/NLTK stats on full corpus    │
│  ├── Layer 2: Claude Haiku on 50 sampled chunks  │
│  └── Layer 3: Claude Opus → voice_profile.md     │
│                                                  │
│  GENERATION LAYER (Claude Sonnet)                │
│  └── 6 variants × voice_profile × algorithm rules│
│                                                  │
│  SIMULATION LAYER (MiroFish components)          │
│  ├── CAMEL-AI OASIS: virtual audience simulation │
│  ├── OasisProfileGenerator: persona creation     │
│  └── Weighted scoring across 6 dimensions        │
│                                                  │
│  AUTO-LOOP LAYER (ReACT pattern from MiroFish)   │
│  ├── Track actual vs predicted performance       │
│  ├── Zep GraphRAG for memory persistence         │
│  ├── Pattern recognition (weekly)                │
│  └── Voice drift detection (monthly)             │
│                                                  │
└─────────────────────────────────────────────────┘
```
