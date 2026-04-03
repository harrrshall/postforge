# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference: Common Commands

```bash
# System health and status
python3 scripts/runner.py status

# Generate content (full pipeline)
python3 scripts/runner.py generate --topic="Your topic" --goal=saves
python3 scripts/runner.py generate --topic="Your topic" --force  # Re-run today
python3 scripts/runner.py generate --topic="Your topic" --auto-select  # Auto-pick winner

# Testing
python3 -m pytest tests/ --ignore=tests/test_system.py -v           # All tests (204)
python3 -m pytest tests/test_simulator_unit.py -v                   # Single test file
python3 -m pytest tests/test_simulator_unit.py::TestLoadPersonas -v # Single test class
python3 -m pytest tests/test_simulator_unit.py::TestLoadPersonas::test_returns_10_personas -v  # Single test

# Learning and improvement
python3 scripts/runner.py learn 2026-04-15-D              # Input post metrics (24h + 7d)
python3 scripts/runner.py sprint-review                  # Run sprint analysis (every 3 days)
python3 scripts/runner.py simulate 2026-04-15            # Simulate variants for date
python3 scripts/runner.py simulate path/to/variant.md    # Simulate single variant

# Automation setup
python3 scripts/runner.py setup-cron                      # Install 4 background jobs
python3 scripts/setup_cron.py --list                      # Show installed cron jobs
python3 scripts/setup_cron.py --remove                    # Remove all PostForge jobs
```

## Architecture Overview

PostForge is a **self-improving LinkedIn content engine** with two modes: headless CLI and interactive (AI coding tool).

### Core Pipeline (runner.py → agents)

```
Input: topic + goal (from CLI or user)
   ↓
intake.py → Collects context, saves to output/intakes/YYYY-MM-DD.json
   ↓
research.py → Finds data points, hooks, angles → research/briefs/YYYY-MM-DD.md
   ↓
writer.py → Generates 6 distinct variants → output/variants/YYYY-MM-DD/
   ↓
scorer.py → Scores 6 dimensions, computes ranking → output/scores/YYYY-MM-DD.json
   ↓
simulator.py → 10 personas react, threads emerge → VariantSimulation results
   ↓
Output: top 3 ranked variants with scores + predictions
   ↓
[Human picks one and publishes to LinkedIn]
   ↓
learn → Input actual metrics (impressions, likes, comments, saves, shares)
   ↓
auto_learn.py → Sprint review every 3 days, recalibrate weights via EMA
   ↓
Next generation uses improved weights ← feedback loop
```

### Key Modules

**scripts/runner.py** — CLI entry point
- Dispatches `generate`, `learn`, `sprint-review`, `simulate`, `scan`, `setup-cron`, `status` commands
- Orchestrates agents and passes results through pipeline

**scripts/config_loader.py** — Shared I/O and utilities
- `load_json()`, `save_json()`, `load_md()` — File I/O
- `get_postforge_root()` — Resolves root directory (monkeypatched in tests to use tmp_path)
- `get_today()` — Returns fixed date (testable via monkeypatch)

**scripts/llm_client.py** — Provider-agnostic LLM abstraction
- Supports 7 providers: Anthropic, OpenAI, Groq, Mistral, Together, Ollama, Gemini
- `LLMClient.available` property — False if no API key set (heuristic-only mode)
- `complete(model_tier, prompt, max_tokens)` — Routes to configured provider
- model_tier: `"reasoning"` (slower, better), `"writing"` (fast), `"fast"`

**scripts/agents/intake.py** — Collect topic, goal, format, timing
**scripts/agents/research.py** — Generate research brief with data points and hooks
**scripts/agents/writer.py** — Generate 6 post variants
**scripts/agents/scorer.py** — Score variants on 6 dimensions (hook, saves, comments, dwell, voice, compliance)

**scripts/simulator.py** — Multi-agent heuristic + LLM-powered simulation
- `load_personas()` — Loads 10 personas from config/audience_personas.md
- `heuristic_simulate_persona()` — Deterministic persona reaction (with stochastic probability draws)
- `simulate_thread_heuristic()` — Generates 2-round comment threads from multiple reactions
- `SimulationEngine` — Orchestrates persona reactions, metrics aggregation, ranking
- **Key fix (Phase 7):** Distinct persona branches, stochastic actions, hook parsing, varied comments

**scripts/auto_learn.py** — EMA-based weight recalibration
- Runs every 3 days after sprint review
- Compares predictions vs actuals, updates scoring_weights.json
- Learning rate: 0.10 (<10 posts), 0.15 (10-20), 0.20 (20+)

**scripts/voice_extractor.py** — 3-layer voice fingerprinting
- Layer 1: Lexical stats (word count, sentence length, question density, etc.)
- Layer 2: Top words and bigrams (frequency-based)
- Layer 3: Writing samples (full text snippets with stats)

### Configuration Files

**config/provider.json** — LLM provider config (which provider + models)
**config/voice_profile.md** — Brand voice + vocabulary (tone, rhythm, patterns to avoid)
**config/algorithm_rules.md** — LinkedIn algorithm constraints (no links, no bait, etc.)
**config/scoring_weights.json** — 6-dimension weights (auto-calibrated via auto_learn.py)
**config/audience_personas.md** — 10 personas for simulation (used by simulator.py)
**config/niche_topics.md** — Topic DNA for content pillars

### Memory (Performance Learning)

**memory/performance_history.json** — All tracked posts with actual metrics
**memory/sprint_log.json** — Sprint reviews + weight change history
**memory/winning_hooks.md** — Hooks that outperformed (auto-extracted)
**memory/winning_templates.md** — Post structures that worked
**memory/anti_patterns.md** — Patterns to avoid (auto-extracted)

### Output Structure

**output/intakes/YYYY-MM-DD.json** — Topic, goal, context from intake agent
**output/variants/YYYY-MM-DD/** — 6 markdown files (variant_a.md, variant_b.md, etc.)
**output/scores/YYYY-MM-DD.json** — Scoring results, predictions, ranking
**output/simulations/YYYY-MM-DD.json** — Persona reactions, thread data, composite scores
**output/selected/YYYY-MM-DD-D.md** — Copy of published post (with variant ID suffix)

**research/briefs/YYYY-MM-DD.md** — Daily research brief (data points, hooks, trends)
**research/scan/** — Trend scan results

---

## Testing

### Test Organization (204 tests total)

```
tests/test_config_loader.py              # File I/O primitives
tests/test_simulator_unit.py             # Persona logic (29 tests)
tests/test_simulator_integration.py      # Full simulation flow
tests/test_auto_learn_unit.py            # EMA weight math
tests/test_auto_learn_integration.py     # Sprint review pipeline
tests/test_runner.py                     # CLI commands
tests/test_llm_client.py                 # Provider abstraction
tests/test_voice_extractor_unit.py       # Voice fingerprinting
tests/test_self_improving_loop.py        # End-to-end feedback loop
tests/test_agents_*.py                   # Individual agent tests
tests/conftest.py                        # Shared fixtures
```

### Key Testing Patterns

**Fixture: `postforge_root`** (conftest.py)
- Creates full directory tree in tmp_path
- Monkeypatches `get_postforge_root()` across all modules
- Seeds `random.seed(42)` for deterministic stochastic tests
- Writes minimal provider.json for LLMClient initialization

**Fixture: `freeze_today`** (conftest.py)
- Monkeypatches `get_today()` to return "2026-04-15"
- Ensures date-based file operations are testable

**Sample data fixtures** (conftest.py)
- `sample_scoring_weights()` — v1 weights with known values
- `sample_performance_history()` — 3 posts with controlled metrics
- `sample_sprint_log_*()` — Empty or populated sprint logs
- `populated_postforge()` — Full working directory with sample content

### Running Tests

```bash
# All tests
python3 -m pytest tests/ --ignore=tests/test_system.py -v

# By category
python3 -m pytest -m unit -v           # Unit tests (logic + primitives)
python3 -m pytest -m integration -v    # Integration tests (cross-component)
python3 -m pytest -m e2e -v            # End-to-end tests (feedback loop)

# Specific test file or function
python3 -m pytest tests/test_simulator_unit.py::TestLoadPersonas::test_returns_10_personas -v

# With output capture disabled (see print statements)
python3 -m pytest tests/test_simulator_unit.py -v -s
```

---

## Architecture Highlights

### 1. Provider Abstraction (llm_client.py)
Different LLMs, same interface. `LLMClient.available` property allows graceful degradation:
- With API key: Full LLM mode (richer persona reactions, LLM-generated comments)
- Without API key: Heuristic-only mode (rule-based simulation, deterministic)

### 2. Simulation Engine (simulator.py) — Phase 7 Fixes
**Problem**: Old code produced nearly-identical scores across variants (all ~0.657), making rankings arbitrary.

**Solution (Phase 7 — 6 fixes)**:
- **Fix 1**: Distinct persona branches — Paired personas (pragmatic/skeptic, builder/critic, etc.) now branch distinctly with different probabilities
- **Fix 2**: Stochastic probability draws — Added `random.seed(42)` to fixtures; actions use probability-based draws instead of deterministic returns
- **Fix 3**: Hook parsing — First 150 chars analyzed separately; fast-scroll personas respond to hooks only
- **Fix 4**: Varied comment templates — ~12 templates per persona type instead of 4 static strings
- **Fix 5**: Signal-based dimension scoring — `voice_authenticity` (penalizes AI-slop), `algorithm_compliance` (penalizes links/bait)
- **Fix 6**: Correct like_count metric — Was counting LIKE+COMMENT+SAVE+SHARE; now counts only LIKE

Result: Simulation now meaningfully differentiates variants. Persona reactions are stochastic yet reproducible (seeded). Comments reference actual post content.

### 3. Self-Improvement Loop (auto_learn.py)
Every 3 days, sprint review:
1. Compares predictions (from scoring) vs actuals (from LinkedIn metrics)
2. Calculates correlation for each dimension
3. Updates weights via EMA: `new = (1-lr) * old + lr * actual_correlation`
4. Extracts winning hooks and anti-patterns to memory

Learning rate increases with post count: 0.10 → 0.15 → 0.20 (damped learning).

### 4. Voice Fingerprinting (voice_extractor.py)
3-layer approach:
- **Layer 1**: Lexical stats (word/sentence length, question %, unique word ratio)
- **Layer 2**: Top words and bigrams (what topics + vocabulary are favored)
- **Layer 3**: Writing samples (actual text with extracted stats)

Used in writer.py to match brand voice, in scorer.py to detect AI-slop.

---

## Common Development Tasks

### Adding a New Scoring Dimension
1. **Add to config/scoring_weights.json**: `{ "new_dimension": { "weight": 0.05, "description": "..." } }`
2. **Update scorer.py**: Add logic to `_score_with_simulator()` to extract signal from post text
3. **Update simulator.py**: Add persona branching logic based on new dimension (if relevant to persona type)
4. **Update auto_learn.py**: Include new dimension in correlation calculations
5. **Update tests**: Add test cases verifying the new dimension is scored correctly

### Modifying Persona Behavior
1. **Edit config/audience_personas.md**: Update persona descriptions
2. **Update simulator.py `heuristic_simulate_persona()`**: Modify branching logic for the persona
3. **Update tests/test_simulator_unit.py**: Adjust expected actions/probabilities for the persona
4. **Verify**: Run `python3 -m pytest tests/test_simulator_unit.py -v` to ensure all persona tests pass

### Adding a New LLM Provider
1. **Update config/provider.json**: Add new provider config with SDK info
2. **Modify scripts/llm_client.py**: Add provider case in `_complete()` method
3. **Update tests/test_llm_client.py**: Add test cases for the new provider
4. **Document**: Update README.md with new provider in the table

### Debugging a Generation Pipeline
```bash
# 1. Check system health
python3 scripts/runner.py status

# 2. Run generate with verbose output
python3 scripts/runner.py generate --topic="Test topic" --goal=saves --force

# 3. Inspect intermediate outputs
cat output/intakes/2026-04-03.json                    # What was the intake?
cat research/briefs/2026-04-03.md                     # What research was gathered?
ls output/variants/2026-04-03/                        # What variants were generated?
cat output/scores/2026-04-03.json                     # What were the scores?
cat output/simulations/2026-04-03.json                # What did personas think?

# 4. Simulate a specific variant
python3 scripts/runner.py simulate output/variants/2026-04-03/variant_a.md
```

### Checking if Code Works Offline (Heuristic Mode)
When `ANTHROPIC_API_KEY` and other LLM keys are unset:
- Intake and research still run (rule-based)
- Writer agent falls back to template-based generation
- Scorer uses heuristic simulation (no LLM calls)
- Simulator runs all 10 personas deterministically (no LLM-generated comments)

This is intentional and testable:
```python
def test_works_without_llm(postforge_root):
    # No API key set → llm.available = False
    from scripts.runner import generate
    results = generate(llm=LLMClient())
    assert results is not None  # Still produces output
```

---

## Brand Voice & Content Rules

(Reference section for content generation via writer agent.)

### Identity & Audience
- **Target**: Indian SMB owners, AI practitioners, startup founders
- **Tone**: Direct, data-driven, slightly irreverent ("dark brutalist")
- **Avoid**: Corporate speak, fluff, hedging, generic AI patterns, engagement bait

### Content Pillars (80/20 Rule)
- 35% **The Proof** — AI ROI data (saves)
- 20% **The Build** — Behind-scenes (comments)
- 20% **The Shift** — Hot takes (comments)
- 15% **The Framework** — Playbooks (saves)
- 10% **Trend Hijack** — Breaking news (velocity)

80% of posts must be within primary cluster (AI agents for Indian business). 20% max adjacent.

### Generation Constraints (Enforced by writer + scorer)
- **Hook**: First 150 chars must be a scroll-stopper (specific number, bold claim, or curiosity gap)
- **No links** in post body (only in first comment via CTA)
- **No bait**: "Comment if", "Tag someone", "Agree?", "Repost this"
- **No AI-slop**: "In today's fast-paced world", "Game-changer", "Dive deep", "Let me break it down", "Unlock your potential", "Leverage", "Synergy", "Paradigm shift"
- **Length**: 200-300 words for text, 5-8 slides for carousel
- **Mobile-first**: Short paragraphs (1-3 lines)
- **Voice match**: High lexical diversity (>0.6 unique words / total words), match vocabulary from voice_profile.md

### First-Time Setup
If `config/voice_profile.md` header says "based on brand analysis, no corpus data yet":
- Prompt user to run voice onboarding: `python3 scripts/voice_onboarding_agent.md` (or via markdown workflow)
- This collects 3-5 writing samples and builds a real voice fingerprint

### Learning Cadence (Feedback Loop)
- **Per-post**: Input metrics at 24h + 7d via `runner.py learn <post_id>`
- **Every 3 days**: Sprint review via `runner.py sprint-review` (auto-updates weights)
- **Every 9 days**: Voice drift check (detects if voice has shifted)
- **After 20+ posts**: Full simulation calibration

---

## Implementation Notes

### Why Tests Use monkeypatch for get_postforge_root
Different modules import `get_postforge_root` differently:
- `from config_loader import get_postforge_root`
- `from config_loader import get_postforge_root as get_root`
- Direct calls in modules

Monkeypatch applies across all these patterns:
```python
monkeypatch.setattr(config_loader, "get_postforge_root", lambda: tmp_path)
for mod_name in ["simulator", "auto_learn", "runner", ...]:
    if hasattr(mod, "get_postforge_root"):
        monkeypatch.setattr(mod, "get_postforge_root", lambda: tmp_path)
```

### Why Simulation Uses random.seed(42)
Heuristic simulation is stochastic (probability-based persona reactions). Tests need deterministic results. `random.seed(42)` in the `postforge_root` fixture ensures all tests run with the same random sequence. Running the same test twice produces identical results.

### Phase 7: Simulation Engine Fixes
Previous implementation had 5 critical bugs making simulation output useless:
1. Persona pairs (pragmatic/skeptic, builder/critic, etc.) branched identically
2. Probability field was recorded but never used in random draw
3. Lurker and aspiring fallbacks always returned READ (engagement=100%)
4. Comments were 4 hardcoded static strings
5. voice_authenticity and algorithm_compliance always returned fixed values

Fixed in c508c86 commit. All 204 tests now pass. Simulation output is now meaningful.
