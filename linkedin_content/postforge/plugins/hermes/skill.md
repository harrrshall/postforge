---
name: postforge
description: Self-improving LinkedIn content engine. Generate post variants, simulate audience reactions, score content, learn from metrics, and auto-calibrate via sprint reviews.
version: 1.0.0
author: Harshal Singh
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [linkedin, content, social-media, ai-agents, postforge, openclaw]
---

# PostForge — LinkedIn Content Engine

PostForge is a self-improving LinkedIn content pipeline targeting Indian SMB owners, AI practitioners, and startup founders.

## What It Does

1. **Generate** — Creates 6 distinct post variants from a topic + goal
2. **Score** — Rates each on 6 dimensions (hook, saves, comments, dwell, voice, compliance)
3. **Simulate** — 10 audience personas react with stochastic behavior
4. **Rank** — Top 3 variants surfaced with predictions
5. **Learn** — Input real LinkedIn metrics after publishing
6. **Improve** — Sprint reviews every 3 days auto-recalibrate scoring weights via EMA

## Quick Workflows

### Generate a post
```
Use postforge_generate with topic and goal (saves/comments/impressions)
```

### Check system state
```
Use postforge_status to see health, tracked posts, sprint count
```

### After publishing — input metrics
```
Use postforge_learn with post_id (YYYY-MM-DD-X), impressions, likes, comments, saves, shares
```

### Review performance
```
Use postforge_sprint_review every 3 days to recalibrate
```

### Read a specific variant
```
Use postforge_read_variant with date and variant letter (a-f)
```

## Content Rules (Enforced Automatically)

- Hook: First 150 chars must scroll-stop
- No links in post body
- No engagement bait ("Comment if", "Tag someone")
- No AI-slop phrases ("game-changer", "leverage", "synergy")
- 200-300 words, mobile-first short paragraphs

## Goals

| Goal | Optimizes For | Best For |
|------|---------------|----------|
| `saves` | Frameworks, playbooks | Reference content people bookmark |
| `comments` | Hot takes, provocative angles | Engagement and reach |
| `impressions` | Trend hijacks, velocity | Maximum visibility |

## Content Pillars

- 35% The Proof — AI ROI data
- 20% The Build — Behind-the-scenes
- 20% The Shift — Hot takes
- 15% The Framework — Playbooks
- 10% Trend Hijack — Breaking news
