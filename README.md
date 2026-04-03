# PostForge

A self-improving LinkedIn content engine. Generate posts, simulate audience reactions, learn from real performance, and automatically calibrate what works — all from the command line.

PostForge generates 6 post variants per topic, scores them across 6 engagement dimensions, simulates 10 audience personas, then learns from actual LinkedIn metrics to improve future output. Every 3 days it runs a sprint review that recalibrates scoring weights using EMA (Exponential Moving Average).

## How It Works

```
You give a rough idea
    ↓
intake_agent.md → collects topic, goal, format, timing
    ↓
research_agent.md → finds data points, competitor posts, hooks
    ↓
writer_agent.md → generates 6 distinct variants (Contrarian, Data Story, Personal, Framework, Hot Take, Trend)
    ↓
scorer_agent.md → scores on 6 dimensions, simulates 5 personas, ranks
    ↓
simulator.py → 10 personas react, comment threads emerge, composite ranking
    ↓
You pick and publish
    ↓
runner.py learn → input actual LinkedIn metrics
    ↓
auto_learn.py → sprint review every 3 days, EMA weight update
    ↓
Next generation uses calibrated weights ← loop
```

## Quick Start

### 1. Clone and enter

```bash
git clone https://github.com/harrrshall/postforge.git
cd postforge
```

### 2. First-time voice setup

PostForge needs your writing voice. Provide 3-5 writing samples (blog posts, LinkedIn posts, emails) and run the voice onboarding:

```bash
mkdir -p config/voice_samples
# Copy your writing samples into config/voice_samples/
# Then ask your AI tool: "Run scripts/voice_onboarding_agent.md"
```

### 3. Configure your LLM provider

Edit `config/provider.json` to set your provider and models:

```bash
# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
# OR
export OPENAI_API_KEY="sk-..."
# OR for any OpenAI-compatible API:
export LLM_API_KEY="your-key"
export LLM_BASE_URL="https://your-api.com/v1"
export LLM_PROVIDER="openai_compatible"
```

PostForge works with **any LLM provider** — Anthropic, OpenAI, Groq, local models, or any OpenAI-compatible API. No API key? It falls back to heuristic simulation (rule-based, no LLM calls).

### 4. Generate your first post

```bash
python3 scripts/runner.py status          # check system health
python3 scripts/runner.py generate        # full pipeline
python3 scripts/runner.py generate --auto-select  # + auto-pick winner via simulation
```

Or run each agent step manually with your AI coding tool:

```
1. "Run scripts/intake_agent.md"      → collects your topic + goal
2. "Run scripts/research_agent.md"    → deep research brief
3. "Run scripts/writer_agent.md"      → 6 post variants
4. "Run scripts/scorer_agent.md"      → score + rank + predict
```

### 5. Track performance and learn

After publishing, input your actual LinkedIn metrics:

```bash
python3 scripts/runner.py learn 2026-04-15-D    # post ID format: YYYY-MM-DD-VARIANT
```

The system compares predicted vs actual engagement and classifies the outcome as MATCHED, OUTPERFORMED, or UNDERPERFORMED.

### 6. Sprint review (automatic learning)

Every 3 days (or manually):

```bash
python3 scripts/runner.py sprint-review
```

This runs the self-improving loop:
- Calculates how each scoring dimension correlated with actual engagement
- Updates weights via EMA: `new = (1-lr) * old + lr * actual`
- Extracts winning hooks and anti-patterns to memory
- Damped learning rate: 0.10 (first 10 posts) → 0.15 (10-20) → 0.20 (20+)

## CLI Reference

```bash
python3 scripts/runner.py status              # system health dashboard
python3 scripts/runner.py generate            # full pipeline
python3 scripts/runner.py generate --auto-select  # + simulation-driven auto-pick
python3 scripts/runner.py learn <post_id>     # input metrics (e.g., 2026-04-15-D)
python3 scripts/runner.py sprint-review       # run sprint analysis + weight update
python3 scripts/runner.py simulate <date>     # multi-agent simulation (10 personas)
python3 scripts/runner.py simulate <path>     # simulate single variant file
python3 scripts/runner.py scan                # trend scan
python3 scripts/runner.py setup-cron          # install 4 automated cron jobs
```

## Works With Any AI Coding Tool

PostForge is **not locked to any specific AI tool**. The agent `.md` files are instruction sets that any AI coding tool can follow:

| Tool | How to use |
|------|-----------|
| **Claude Code** | Reads `CLAUDE.md` automatically |
| **Cursor** | Run `python3 scripts/generate_tool_configs.py` → creates `.cursorrules` |
| **OpenAI Codex** | Run the generator → creates `CODEX.md` |
| **OpenClaw / Kilo / Antigravity** | Run the generator → creates `AGENTS.md` and `CONVENTIONS.md` |
| **Any other tool** | Just tell it: "Follow the instructions in `scripts/writer_agent.md`" |

Generate config files for all supported tools:

```bash
python3 scripts/generate_tool_configs.py          # generate all
python3 scripts/generate_tool_configs.py --list    # see targets
python3 scripts/generate_tool_configs.py --clean   # remove generated files
```

## Scoring Dimensions

Posts are scored on 6 dimensions with dynamically calibrated weights:

| Dimension | What It Measures |
|-----------|-----------------|
| **Hook Strength** | First 150 chars — scroll-stopping power |
| **Save-Worthiness** | Reference value — would someone bookmark this? |
| **Comment-Worthiness** | Debate potential — does this trigger substantive comments? |
| **Dwell Time Potential** | Read time — progressive revelation, content density |
| **Voice Authenticity** | Matches your voice_profile.md, passes AI detection |
| **Algorithm Compliance** | No external links, no bait, Topic DNA aligned |

Weights start equal and shift based on what actually drives engagement for *your* audience.

## Simulation Engine

10 virtual personas (expanded from 5 base types with personality variation):

- **Busy Founder** (Pragmatic + Skeptical) — fast scroll, saves ROI frameworks
- **Tech Peer** (Builder + Critical) — medium scroll, comments substantively
- **Aspiring SMB Owner** (Eager + Cautious) — slow scroll, saves everything actionable
- **Contrarian** (Veteran + Academic) — medium scroll, debates everything bold
- **Silent Lurker** (Passive + Saver) — reads everything, rarely engages

Each persona reacts (SKIP/SKIM/READ/LIKE/COMMENT/SAVE/SHARE), generates comment text, then comment threads emerge across 2 rounds. Composite ranking: `0.40 * saves + 0.35 * comments + 0.25 * thread_depth`.

**Two modes:**
- **LLM mode** — personas powered by your configured LLM (richer, more varied reactions)
- **Heuristic mode** — rule-based simulation (no API key needed, deterministic)

## Project Structure

```
postforge/
├── CLAUDE.md                    # Agent operating rules (also used as project config)
├── config/
│   ├── provider.json            # LLM provider config (Anthropic/OpenAI/custom)
│   ├── voice_profile.md         # Your writing DNA (tone, vocabulary, rhythm)
│   ├── algorithm_rules.md       # LinkedIn 2026 algorithm rules
│   ├── scoring_weights.json     # 6-dimension weights (auto-calibrated)
│   ├── audience_personas.md     # 5 base personas for simulation
│   ├── niche_topics.md          # Topic DNA — what to write about
│   └── trend_triggers.md        # Urgency classification (FIRE/HOT/WARM/COOL)
├── scripts/
│   ├── runner.py                # CLI entry point — all commands
│   ├── config_loader.py         # Shared file I/O utilities
│   ├── llm_client.py            # Provider-agnostic LLM client
│   ├── auto_learn.py            # Sprint review + EMA weight calibration
│   ├── simulator.py             # 10-persona simulation engine
│   ├── voice_extractor.py       # 3-layer voice fingerprinting
│   ├── setup_cron.py            # Cron job manager
│   ├── generate_tool_configs.py # Multi-tool config generator
│   ├── intake_agent.md          # Phase 0: Collect topic + goal
│   ├── scan_agent.md            # Phase 1: Trend scanning
│   ├── research_agent.md        # Phase 2: Deep topic research
│   ├── writer_agent.md          # Phase 3: Generate 6 variants
│   ├── scorer_agent.md          # Phase 4: Score + rank + predict
│   ├── learn_agent.md           # Phase 6: Sprint review + drift detection
│   └── voice_onboarding_agent.md # Setup: Voice profile extraction
├── memory/
│   ├── performance_history.json # All tracked posts + accuracy metrics
│   ├── sprint_log.json          # Sprint reviews + weight change history
│   ├── winning_hooks.md         # Hooks that outperformed (auto-extracted)
│   ├── winning_templates.md     # Post structures that worked
│   └── anti_patterns.md         # Patterns to avoid (auto-extracted)
├── output/
│   ├── variants/YYYY-MM-DD/     # 6 post variants per day
│   ├── scores/YYYY-MM-DD.json   # Scoring results + predictions
│   ├── simulations/             # Simulation results
│   ├── selected/                # Published post copies
│   └── intakes/                 # Intake briefs
├── research/
│   ├── briefs/                  # Daily research briefs
│   └── scan/                    # Trend scan results
├── tests/
│   ├── test_system.py           # 248 structure + compliance tests
│   ├── test_config_loader.py    # I/O primitives
│   ├── test_auto_learn_unit.py  # EMA math, learning rates, correlations
│   ├── test_auto_learn_integration.py  # Sprint review pipeline
│   ├── test_simulator_unit.py   # Persona reactions, metrics, ranking
│   ├── test_simulator_integration.py   # Full simulation with files
│   ├── test_runner.py           # CLI command tests
│   ├── test_llm_client.py       # Provider abstraction tests
│   ├── test_voice_extractor_unit.py    # Statistical analysis
│   └── test_self_improving_loop.py     # End-to-end feedback loop
└── pyproject.toml               # pytest config
```

## Tests

```bash
# Run all 163 pytest tests (unit + integration + e2e)
python3 -m pytest tests/ --ignore=tests/test_system.py -v

# Run by category
python3 -m pytest -m unit -v           # 124 pure logic tests
python3 -m pytest -m integration -v    # 31 cross-component tests
python3 -m pytest -m e2e -v            # 8 full feedback loop tests

# Run 248 structure/compliance tests
python3 tests/test_system.py
```

## Cron Automation

Install 4 background jobs:

```bash
python3 scripts/runner.py setup-cron
```

| Job | Schedule | What |
|-----|----------|------|
| Trend scan | Every 4 hours | Scans for trending topics |
| Sprint review | Every 3 days | Recalibrates scoring weights |
| Voice drift | Every 9 days | Checks for voice consistency |
| Daily research | 7:00 AM | Generates research brief |

```bash
python3 scripts/setup_cron.py --list     # show installed jobs
python3 scripts/setup_cron.py --remove   # remove all PostForge jobs
```

## Requirements

- Python 3.10+
- No required packages for heuristic mode
- Optional: `anthropic` SDK or `openai` SDK (for LLM-powered simulation)

## License

MIT
