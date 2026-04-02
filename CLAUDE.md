# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Humanless** is an AI agent service business targeting Indian SMBs. It provides automated AI employees using OpenClaw (open-source AI agent framework) for customer service, scheduling, reporting, and business operations.

This repo contains: marketing website (Next.js), promotional video (Remotion), business research, and **PostForge** — a self-improving LinkedIn content engine with multi-agent simulation.

## Commands

### Frontend (Next.js 15)
```bash
cd frontend
npm run dev      # Dev server
npm run build    # Production build
npm run lint     # ESLint
```

### Humanless Demo (Remotion Video)
```bash
cd humanless_demo
npm run dev      # Remotion Studio
npm run build    # Bundle composition
npm run lint     # ESLint + TypeScript check
```

### PostForge (LinkedIn Content Engine)
```bash
cd linkedin_content/postforge

# CLI — all commands via runner.py
python3 scripts/runner.py status                # System health dashboard
python3 scripts/runner.py generate              # Full pipeline: intake → research → write → score → present
python3 scripts/runner.py generate --auto-select # + simulation-driven auto-pick winner
python3 scripts/runner.py learn 2026-04-02-D    # Input metrics for a published post
python3 scripts/runner.py sprint-review         # Run sprint analysis + EMA weight update
python3 scripts/runner.py simulate 2026-04-02   # Multi-agent simulation on all variants for a date
python3 scripts/runner.py simulate output/variants/2026-04-02/variant_d.md  # Single variant
python3 scripts/runner.py scan                  # Trend scan
python3 scripts/runner.py setup-cron            # Install 4 automated cron jobs

# Tests
python3 tests/test_system.py                    # 223 tests: structure, config, cross-refs, compliance

# Utilities
python3 scripts/voice_extractor.py --input <samples_dir> --output config/  # 3-layer voice extraction
python3 scripts/auto_learn.py --force           # Force sprint review regardless of thresholds
python3 scripts/setup_cron.py --list            # Show installed cron jobs
python3 scripts/setup_cron.py --remove          # Remove PostForge cron jobs
```

## PostForge Architecture

PostForge is the core system — a self-improving LinkedIn content engine that generates, simulates, scores, and learns from every post.

### Pipeline Flow

```
intake_agent.md → research_agent.md → writer_agent.md → scorer_agent.md → simulator.py → auto_learn.py
     ↓                  ↓                   ↓                 ↓                ↓              ↓
output/intakes/    research/briefs/    output/variants/    output/scores/  output/simulations/  config/scoring_weights.json
                                      (6 variants)        (ranked JSON)   (10 personas)        memory/sprint_log.json
```

### Agent Skills (Markdown files executed by Claude)

Each `.md` skill in `scripts/` is an instruction set that Claude follows step-by-step. They are NOT code — they are prompts that load config files, generate content, and produce structured output.

| Skill | Phase | What It Does |
|-------|-------|-------------|
| `intake_agent.md` | 0 | Asks 5 questions (topic, goal, context, format, timing) → JSON with `pipeline_hints` |
| `scan_agent.md` | 1 | Scans 6 platforms for trends → FIRE/HOT/WARM/COOL classification |
| `research_agent.md` | 2 | Deep topic research → 5 data points, competitor analysis, 5 hook options |
| `writer_agent.md` | 3 | Generates 6 distinct variants (Contrarian, Data Story, Personal, Framework, Hot Take, Trend) |
| `scorer_agent.md` | 4 | Scores variants on 6 dimensions + 5 persona simulation → ranked JSON |
| `learn_agent.md` | 6 | 4 learning functions: metrics intake, sprint review, voice drift, calibration |
| `voice_onboarding_agent.md` | Setup | One-time: collects writing samples → 3-layer extraction → voice_profile.md |

### Python Scripts (Actual executable code)

| Script | Purpose |
|--------|---------|
| `runner.py` | CLI hub — orchestrates all commands, delegates to agents and scripts |
| `config_loader.py` | Shared I/O: `load_json()`, `save_json()`, `load_md()`, `get_postforge_root()`, `ensure_dirs()` |
| `auto_learn.py` | `AutoLearner` class: EMA weight updates, sprint reviews, pattern extraction |
| `simulator.py` | `SimulationEngine`: 10 personas × 3 rounds, heuristic or Haiku API, composite ranking |
| `voice_extractor.py` | 3-layer voice pipeline: spaCy stats → Haiku sampling → Opus synthesis |
| `setup_cron.py` | Installs/removes 4 cron jobs (scan, sprint, voice drift, research) |

### Self-Improving Loop

```
Post published → runner.py learn → performance_history.json grows
→ auto_learn.py (every 3 days) → calculates dimension correlations
→ EMA: new_weight = (1-lr) × old_weight + lr × actual_correlation
→ scoring_weights.json updated (version++, history logged)
→ next generation uses calibrated weights
```

- Learning rate is damped: 0.10 (<10 posts), 0.15 (10-20 posts), 0.20 (20+ posts)
- Weights always normalized to sum to 1.0
- Winners (outperformed >20%) extracted to `memory/winning_hooks.md`
- Anti-patterns (underperformed >20%) logged to `memory/anti_patterns.md`

### Scoring Dimensions (dynamic weights, calibrated by auto_learn)

| Dimension | What It Measures |
|-----------|-----------------|
| hook_strength | First 150 chars scroll-stopping power |
| save_worthiness | Bookmark-worthy framework/data value (saves = 5x reach of a like) |
| comment_worthiness | Debate potential, CTA quality (comments = 15x a like) |
| dwell_time_potential | Read time, progressive revelation |
| voice_authenticity | Matches voice_profile.md, passes 360Brew AI detection |
| algorithm_compliance | No external links, no engagement bait, Topic DNA aligned |

### Goal-Based Adaptation

When the intake specifies a goal, the pipeline adapts:
- **Writer** (Step 1.5): Prioritizes variants matching the goal (e.g., `maximize_saves` → Framework + Data Story)
- **Scorer** (Step 3.5): Applies 1.20x multiplier to the goal's primary dimension

### Simulation Engine

`simulator.py` expands 5 base personas to 10 (with MBTI variation), then:
1. **Phase 1**: Each persona reacts to each variant (SKIP/SKIM/READ/LIKE/COMMENT/SAVE/SHARE)
2. **Phase 2**: Comment thread simulation — commenting personas see each other's comments and reply (2 rounds)
3. **Phase 3**: Aggregate metrics and composite ranking: `0.40×saves + 0.35×comments + 0.25×thread_depth`
4. Uses Anthropic API (Haiku) if `ANTHROPIC_API_KEY` is set, otherwise heuristic rules

### Key Conventions

- **Post IDs**: `YYYY-MM-DD-X` (e.g., `2026-04-02-D`)
- **Variant files**: `variant_[a-f].md` (lowercase), variant IDs in output: uppercase `A-F`
- **Date folders**: `YYYY-MM-DD` everywhere
- **AI-slop never allowed**: "In today's fast-paced world", "Game-changer", "Let me break it down", "Dive deep"
- **No external links** in any generated post body (60% reach penalty per LinkedIn 2026 algorithm)
- **Cron automation**: 4 jobs installed via `setup_cron.py` — scan (4h), sprint (3d), voice drift (9d), research (daily)

## Frontend

- Next.js 15.2.4 with App Router, React 19, TypeScript 5.8
- Custom CSS only (no component library) — dark brutalist "Kinetic Monolith" design system
- `app/page.tsx` — Main landing page with hero, services, integrations, pricing, Cal.com booking
- `app/case-studies/` — Dynamic routes by sector, data-driven from `data.ts` (6 sectors)
- `DESIGN.md` — Detailed design system specification; follow this when making UI changes

### Design Principles
- Dark mode only (#09090b background, #ff995f orange accent)
- Tonal stacking for depth (no shadows), ghost borders only
- No rounded corners > 12px, no glows
- Typography: Space Grotesk (headers), JetBrains Mono (code), Inter (body)
- Minimum 4.5:1 contrast ratio

## Humanless Demo (Remotion)

- Remotion 4.0.441, React 19, Tailwind CSS 4.0
- `src/Root.tsx` — Composition: 1920x1080, 30fps, 1432 frames (12 scenes, 8 transitions, 3 light leaks)
- `src/Composition.tsx` — All scenes and animations
- `out/HumanlessLaunch.mp4` — 47.7s rendered output

## Business Context

- Target: Indian SMBs (healthcare, e-commerce, agencies, education, local business)
- Pricing: ₹4,999 (Starter), ₹14,999 (Pro), Custom (Enterprise)
- Key integrations: WhatsApp, Telegram, Notion, Google Calendar, Razorpay, Zoho
- CTAs → WhatsApp and Cal.com booking
- PostForge brand voice: direct, data-driven, slightly irreverent, "dark brutalist" energy — never corporate
