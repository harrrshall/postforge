#!/usr/bin/env python3
"""Writer Agent — Generate 6 post variants from research brief."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import load_json, load_md, get_postforge_root, get_today
from llm_client import LLMClient


VARIANT_TYPES = [
    ("A", "Contrarian Take", "text"),
    ("B", "Data Story", "text"),
    ("C", "Framework Post", "carousel"),
    ("D", "Build Story", "text"),
    ("E", "Trend Hijack", "text"),
    ("F", "Deep Dive", "carousel"),
]


def _load_context(root: Path, date: str) -> dict:
    """Load all context files needed for writing."""
    ctx = {
        "voice_profile": "",
        "algorithm_rules": "",
        "research_brief": "",
        "intake": None,
        "scoring_weights_version": 1,
    }

    voice_path = root / "config" / "voice_profile.md"
    if voice_path.exists():
        ctx["voice_profile"] = load_md(voice_path)

    algo_path = root / "config" / "algorithm_rules.md"
    if algo_path.exists():
        ctx["algorithm_rules"] = load_md(algo_path)

    brief_path = root / "research" / "briefs" / f"{date}.md"
    if brief_path.exists():
        ctx["research_brief"] = load_md(brief_path)

    intake_path = root / "output" / "intakes" / f"{date}.json"
    if intake_path.exists():
        ctx["intake"] = load_json(intake_path)

    weights_path = root / "config" / "scoring_weights.json"
    if weights_path.exists():
        weights = load_json(weights_path)
        ctx["scoring_weights_version"] = weights.get("version", 1)

    return ctx


def _write_variant(root: Path, llm: LLMClient, ctx: dict, variant_id: str,
                   variant_type: str, format_: str, date: str) -> Path:
    """Write a single variant. Returns path."""
    variant_dir = root / "output" / "variants" / date
    variant_dir.mkdir(parents=True, exist_ok=True)
    variant_path = variant_dir / f"variant_{variant_id.lower()}.md"

    # ─── Prepare prompt ───
    topic = ctx.get("intake", {}).get("topic", "Unknown topic")
    goal = ctx.get("intake", {}).get("goal", {}).get("primary", "saves")
    voice_snippet = ctx["voice_profile"][:300] if ctx["voice_profile"] else "Direct, data-driven tone"

    variant_prompt = f"""You are a LinkedIn post writer for Indian startup founders and SMB owners.

Variant Type: {variant_type}
Format: {format_} ({"6-8 slides for carousel" if format_ == "carousel" else "200-300 words for text"})
Topic: {topic}
Goal: {goal.replace('_', ' ')}

Voice (tone & vocabulary):
{voice_snippet}

Research Brief:
{ctx["research_brief"][:500]}

Write ONLY the post content in this exact markdown format (no explanations, no preamble):

# Variant {variant_id}: {variant_type}

## Metadata
- Type: {variant_type}
- Format: {format_}
- Pillar: proof
- Word count: [number]
- Primary engagement target: {goal}

## Hook Analysis
- First 150 chars: "[Hook in quotes — must be < 150 chars, specific number or bold claim]"
- Hook pattern: [number/contrast/story/question]

## Post Text
[Your {format_} post here. {
  "For text: 200-300 words, short paragraphs (1-3 lines), actionable takeaway, CTA invites experience-sharing."
  if format_ == "text"
  else "For carousel: Slide by slide, each 30-50 words, progressive revelation."
}]

## First Comment
#hashtag1 #hashtag2 #hashtag3

---

RULES (non-negotiable):
- No external links
- No engagement bait ("Comment YES", "Agree?", "Tag someone who")
- No AI-slop: avoid "In today's fast-paced world", "Let me break it down", "Game-changer"
- High lexical diversity (use varied vocabulary)
- Match the voice above
- First 150 chars = scroll-stopper (specific number, bold claim, or curiosity gap)
"""

    # ─── LLM Path ───
    if llm.available:
        variant_text = llm.complete("writing", variant_prompt, max_tokens=700)
        if variant_text:
            variant_path.write_text(variant_text)
            return variant_path

    # ─── Fallback Path ───
    fallback_variant = f"""# Variant {variant_id}: {variant_type}

## Metadata
- Type: {variant_type}
- Format: {format_}
- Pillar: proof
- Word count: 250
- Primary engagement target: {goal}

## Hook Analysis
- First 150 chars: "[PLACEHOLDER: Specific number or bold claim about {topic}]"
- Hook pattern: number/contrast

## Post Text
[PLACEHOLDER: {variant_type} post about {topic}.

For text format: 200-300 words, short paragraphs.
For carousel format: 6-8 slides with progressive revelation.]

## First Comment
#AIAgents #IndianSMB #Innovation
"""

    variant_path.write_text(fallback_variant)
    return variant_path


def run(root: Path = None, llm: LLMClient = None, date: str = "") -> list[Path]:
    """
    Generate 6 post variants. Returns list of written paths.

    Args:
        root: PostForge root directory
        llm: LLMClient instance
        date: YYYY-MM-DD date string (today if empty)
    """
    if root is None:
        root = get_postforge_root()
    if llm is None:
        llm = LLMClient()
    if not date:
        date = get_today()

    variant_dir = root / "output" / "variants" / date
    existing_variants = list(variant_dir.glob("variant_*.md")) if variant_dir.exists() else []

    # Idempotency: if all 6 variants exist, return them
    if len(existing_variants) == 6:
        return sorted(existing_variants)

    # ─── Load all context ───
    ctx = _load_context(root, date)

    # ─── Generate each variant ───
    paths = []
    for variant_id, variant_type, format_ in VARIANT_TYPES:
        path = _write_variant(root, llm, ctx, variant_id, variant_type, format_, date)
        paths.append(path)

    return paths


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else ""
    if not date:
        from config_loader import get_today
        date = get_today()
    paths = run(date=date)
    print(f"  Generated {len(paths)} variants")
    for p in paths:
        print(f"    {p.name}")
