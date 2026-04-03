# PostForge — Agent as a Service (AaaS)

A self-improving LinkedIn content engine that runs headless or interactively. Generate posts, simulate audience reactions, learn from real performance, and automatically calibrate what works.

PostForge generates 6 post variants per topic, scores them across 6 engagement dimensions, simulates 10 audience personas, then learns from actual LinkedIn metrics to improve future output. Every 3 days it runs a sprint review that recalibrates scoring weights using EMA (Exponential Moving Average).

**Works with any LLM provider**: Anthropic, OpenAI, Groq, Mistral, Together, Ollama, or any OpenAI-compatible API. No API key? Runs entirely on heuristic simulation.

## How It Works

```
Input: topic + goal (CLI or interactive)
    ↓
intake.py → collects topic, goal, format, timing → output/intakes/
    ↓
research.py → finds data points, hooks, contrarian angle → research/briefs/
    ↓
writer.py → generates 6 distinct variants → output/variants/
    ↓
scorer.py → scores on 6 dimensions, ranks → output/scores/
    ↓
simulator.py → 10 personas react, comment threads emerge → composite ranking
    ↓
Output: top 3 variants with full scores + predictions
    ↓
[You pick and publish]
    ↓
runner.py learn → input actual LinkedIn metrics
    ↓
auto_learn.py → sprint review every 3 days, EMA weight calibration
    ↓
Next generation uses improved weights ← feedback loop
```

## Quick Start

### 1. Clone and set up

```bash
git clone https://github.com/harrrshall/postforge.git
cd postforge
pip install -r requirements.txt  # optional: installs anthropic/openai SDKs
```

### 2. Configure your LLM provider (optional)

Set your API key to enable LLM-powered generation. If you skip this, PostForge runs in **heuristic-only mode** (rule-based simulation, no API calls).

```bash
# Anthropic (Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# OR OpenAI (GPT)
export OPENAI_API_KEY="sk-..."

# OR Groq (free tier available)
export GROQ_API_KEY="gsk_..."

# OR local Ollama
export OLLAMA_API_KEY="ollama"
export LLM_PROVIDER=ollama

# OR any other provider: Mistral, Together, Gemini, etc.
export LLM_API_KEY="your-key"
export LLM_PROVIDER=mistral  # (or: together, gemini, groq, ollama)
```

Edit `config/provider.json` to see all 7 supported providers and add custom ones.

### 3. Optional: Set up voice profile

PostForge can match your writing voice. Provide 3-5 samples:

```bash
mkdir -p config/voice_samples
# Copy your writing samples into config/voice_samples/
# Then in your AI coding tool: "Run scripts/voice_onboarding_agent.md"
```

### 4. Generate your first post

**Headless CLI mode** (no coding tool needed):

```bash
python3 scripts/runner.py status                                    # system health
python3 scripts/runner.py generate --topic="AI agents for SMBs"     # generate pipeline
python3 scripts/runner.py generate --topic="..." --goal=comments    # specify goal
python3 scripts/runner.py generate --topic="..." --force            # re-run today
```

**Interactive mode** (with Claude Code, Cursor, or other AI coding tools):

Open this directory in your coding tool and say:
- "Generate a LinkedIn post about WhatsApp automation"
- "Create content ideas for Indian SMBs"

The tool reads `CLAUDE.md` (or generated `CODEX.md`, `.cursorrules`, etc.) and follows the agent workflow.

### 5. Track performance and learn

After publishing to LinkedIn, input your metrics:

```bash
python3 scripts/runner.py learn 2026-04-15-D    # post ID: YYYY-MM-DD-VARIANT
```

The system compares predicted vs actual engagement (MATCHED / OUTPERFORMED / UNDERPERFORMED).

### 6. Sprint review (automatic improvement)

Every 3 days (or manually):

```bash
python3 scripts/runner.py sprint-review
```

Automatically:
- Calculates which scoring dimensions correlated with real engagement
- Updates weights via EMA: `new = (1-lr) * old + lr * actual`
- Extracts winning hooks and anti-patterns to memory
- Adjusts learning rate: 0.10 → 0.15 → 0.20 (based on post count)

### 7. Automate everything with cron

```bash
python3 scripts/runner.py setup-cron
```

Runs 4 background jobs:
- Trend scan: every 4 hours
- Sprint review: every 3 days
- Voice drift check: every 9 days
- Daily research brief: every morning at 7 AM

## CLI Reference

```bash
python3 scripts/runner.py status                                  # system health dashboard
python3 scripts/runner.py generate                                # full pipeline (interactive)
python3 scripts/runner.py generate --topic="..."                  # pipeline with topic (headless)
python3 scripts/runner.py generate --topic="..." --goal=saves     # specify goal: saves|comments|velocity
python3 scripts/runner.py generate --topic="..." --force          # re-generate even if today exists
python3 scripts/runner.py generate --auto-select                  # + auto-pick winner via simulation
python3 scripts/runner.py learn <post_id>                         # input metrics (e.g., 2026-04-15-D)
python3 scripts/runner.py sprint-review                           # run sprint analysis + weight update
python3 scripts/runner.py simulate <date>                         # multi-agent simulation (10 personas)
python3 scripts/runner.py simulate <path>                         # simulate single variant file
python3 scripts/runner.py scan                                    # trend scan
python3 scripts/runner.py auto-research                           # non-interactive daily research (cron)
python3 scripts/runner.py voice-drift                             # voice consistency check (cron)
python3 scripts/runner.py setup-cron                              # install 4 automated background jobs
```

## Works With Any AI Coding Tool

PostForge supports **both modes**:

### 1. Headless / CLI-only
No coding tool needed. All logic runs in Python agents via `runner.py`.

### 2. Interactive / Coding Tool Mode
Use any AI coding tool (Claude Code, Cursor, Codex, etc.). The tool reads instructions from `CLAUDE.md` and calls `runner.py` for mechanical steps.

Supported tools:

| Tool | Integration |
|------|-------------|
| **Claude Code** | Reads `CLAUDE.md` automatically |
| **Cursor / VS Code** | Run `python3 scripts/generate_tool_configs.py` → creates `.cursorrules` |
| **OpenAI Codex / ChatGPT** | Run generator → creates `CODEX.md` |
| **OpenClaw / Kilo / Antigravity** | Run generator → creates `AGENTS.md` and `CONVENTIONS.md` |
| **Any other tool** | Just tell it: "Follow the instructions in `scripts/intake_agent.md`" |

Generate multi-tool config files:

```bash
python3 scripts/generate_tool_configs.py          # generate all
python3 scripts/generate_tool_configs.py --list    # see available targets
python3 scripts/generate_tool_configs.py --clean   # remove generated files
```

## Supported LLM Providers

| Provider | API Key Env Var | Setup | Model Tiers |
|----------|-----------------|-------|-------------|
| **Anthropic** | `ANTHROPIC_API_KEY` | Native | Claude 3.5 Sonnet, Haiku |
| **OpenAI** | `OPENAI_API_KEY` | Native | GPT-4, GPT-4o, GPT-4 Turbo |
| **Groq** | `GROQ_API_KEY` | `config/provider.json` | Llama 3.3 70B (free tier) |
| **Mistral** | `MISTRAL_API_KEY` | `config/provider.json` | Mistral Large, Medium, Small |
| **Together** | `TOGETHER_API_KEY` | `config/provider.json` | Llama 3.3 70B, Qwen, Phi |
| **Ollama** | `OLLAMA_API_KEY` | Local (self-hosted) | Any local model |
| **Gemini** | `GEMINI_API_KEY` | `config/provider.json` | Gemini 2.0, 1.5 Pro/Flash |

No API key? PostForge runs entirely on **heuristic simulation** — rule-based, deterministic, no external calls.

## Flexibility: Two Ways to Use PostForge

### 1. Headless CLI (No Coding Tool)
Run the full pipeline from your terminal:

```bash
python3 scripts/runner.py generate --topic="AI agents for SMBs"
# Outputs: variants, scores, simulation results, top 3 picks
```

Great for: automation, cron jobs, CI/CD pipelines, servers, pure Python integration.

### 2. Interactive with AI Coding Tools
Use Claude Code, Cursor, or any AI coding tool:

Open the repo in your tool and say:
- "Generate a LinkedIn post about WhatsApp automation"
- "Create 3 content ideas for healthcare startups"

The tool reads `CLAUDE.md` (or auto-generated `.cursorrules`, `CODEX.md`, etc.) and follows the agent workflow, calling Python agents as needed.

Great for: iterative refinement, real-time feedback, human-in-the-loop editing, prototyping.

**Same codebase, two interfaces.** Pick the workflow that fits your use case.

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
├── CLAUDE.md                    # Agent operating rules + brand identity
├── README.md                    # This file
├── requirements.txt             # Python dependencies (optional)
├── config/
│   ├── provider.json            # LLM provider config (7 providers supported)
│   ├── voice_profile.md         # Your writing DNA (tone, vocabulary, rhythm)
│   ├── algorithm_rules.md       # LinkedIn algorithm rules
│   ├── scoring_weights.json     # 6-dimension weights (auto-calibrated)
│   ├── audience_personas.md     # 5 base personas for simulation
│   ├── niche_topics.md          # Topic DNA — what to write about
│   └── trend_triggers.md        # Urgency classification (FIRE/HOT/WARM/COOL)
├── scripts/
│   ├── runner.py                # CLI entry point — all commands
│   ├── config_loader.py         # Shared file I/O utilities
│   ├── llm_client.py            # Provider-agnostic LLM client (7 providers)
│   ├── auto_learn.py            # Sprint review + EMA weight calibration
│   ├── simulator.py             # 10-persona simulation engine
│   ├── voice_extractor.py       # 3-layer voice fingerprinting
│   ├── setup_cron.py            # Cron job manager
│   ├── generate_tool_configs.py # Multi-tool config generator
│   ├── agents/                  # Python implementation of agents
│   │   ├── __init__.py
│   │   ├── intake.py            # Collect topic + goal → output/intakes/
│   │   ├── research.py          # Generate research brief → research/briefs/
│   │   ├── writer.py            # Generate 6 variants → output/variants/
│   │   └── scorer.py            # Score variants → output/scores/
│   ├── intake_agent.md          # Markdown workflow (for AI coding tools)
│   ├── research_agent.md        # Markdown workflow
│   ├── writer_agent.md          # Markdown workflow
│   ├── scorer_agent.md          # Markdown workflow
│   ├── learn_agent.md           # Markdown workflow
│   └── voice_onboarding_agent.md # Setup workflow
├── memory/
│   ├── performance_history.json # All tracked posts + accuracy metrics
│   ├── sprint_log.json          # Sprint reviews + weight change history
│   ├── winning_hooks.md         # Hooks that outperformed (auto-extracted)
│   ├── winning_templates.md     # Post structures that worked
│   └── anti_patterns.md         # Patterns to avoid (auto-extracted)
├── output/
│   ├── variants/YYYY-MM-DD/     # 6 post variants per day
│   ├── scores/YYYY-MM-DD.json   # Scoring results + predictions
│   ├── intakes/YYYY-MM-DD.json  # Intake briefs
│   ├── simulations/             # Simulation results
│   └── selected/                # Published post copies
├── research/
│   ├── briefs/                  # Daily research briefs
│   └── scan/                    # Trend scan results
├── tests/
│   ├── test_system.py                  # Structure + compliance tests
│   ├── test_config_loader.py           # I/O primitives
│   ├── test_auto_learn_unit.py         # EMA math, learning rates
│   ├── test_auto_learn_integration.py  # Sprint review pipeline
│   ├── test_simulator_unit.py          # Persona logic
│   ├── test_simulator_integration.py   # Full simulation flow
│   ├── test_runner.py                  # CLI commands
│   ├── test_llm_client.py              # Provider abstraction
│   ├── test_voice_extractor_unit.py    # Voice fingerprinting
│   ├── test_self_improving_loop.py     # End-to-end feedback loop
│   ├── test_agents_intake.py           # Intake agent tests
│   ├── test_agents_research.py         # Research agent tests
│   ├── test_agents_writer.py           # Writer agent tests
│   └── test_agents_scorer.py           # Scorer agent tests
└── pyproject.toml               # pytest config
```

## Tests

```bash
# Run all 204 pytest tests (unit + integration + e2e)
python3 -m pytest tests/ --ignore=tests/test_system.py -v

# Run by category
python3 -m pytest -m unit -v           # Unit tests (logic + primitives)
python3 -m pytest -m integration -v    # Integration tests (cross-component)
python3 -m pytest -m e2e -v            # End-to-end tests (feedback loop)

# Run agent tests specifically
python3 -m pytest tests/test_agents_*.py -v

# Run structure/compliance tests
python3 -m pytest tests/test_system.py -v
```

**Coverage**: 204 tests covering agents, CLI, simulation, learning, voice profiling, and end-to-end feedback loops.

## Cron Automation

Install 4 background jobs that run automatically:

```bash
python3 scripts/runner.py setup-cron
```

| Job | Schedule | What It Does |
|-----|----------|-------------|
| Trend scan | Every 4 hours | Scans for trending topics in your niche |
| Sprint review | Every 3 days | Recalibrates scoring weights via EMA |
| Voice drift | Every 9 days | Checks if your voice profile has shifted |
| Daily research | 7:00 AM daily | Generates research brief for next post |

Manage jobs:

```bash
python3 scripts/setup_cron.py --list     # show installed jobs
python3 scripts/setup_cron.py --remove   # remove all PostForge jobs
```

## Requirements

**Minimum:**
- Python 3.10+
- No external dependencies for heuristic-only mode

**Optional:**
- `anthropic>=0.40.0` — for Claude models (recommended)
- `openai>=1.50.0` — for OpenAI, Groq, Mistral, Together, Ollama, Gemini, etc.

Install optional dependencies:

```bash
pip install -r requirements.txt
```

Or install per-provider:

```bash
pip install anthropic         # Anthropic/Claude
pip install openai            # OpenAI + OpenAI-compatible (Groq, Mistral, etc.)
```

## License

MIT
