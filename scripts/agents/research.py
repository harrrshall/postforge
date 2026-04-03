#!/usr/bin/env python3
"""Research Agent — Generate research brief from intake."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import load_json, save_json, get_postforge_root, get_today, load_md
from llm_client import LLMClient


def run(root: Path = None, llm: LLMClient = None, date: str = "") -> Path:
    """
    Generate research brief from today's intake. Returns brief path.

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

    brief_path = root / "research" / "briefs" / f"{date}.md"

    # Idempotency: if brief already exists, return it
    if brief_path.exists():
        return brief_path

    # ─── Load context ───
    intake_path = root / "output" / "intakes" / f"{date}.json"
    if not intake_path.exists():
        # No intake — write template brief
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text(f"""# Research Brief — {date}

## Status
No intake data available. Please run intake_agent first.

## Next Steps
1. Run: scripts/intake_agent.md
2. Then re-run: scripts/research_agent.md
""")
        return brief_path

    intake = load_json(intake_path)
    topic = intake.get("topic", "Unknown topic")
    goal = intake.get("goal", {}).get("primary", "unknown")

    # Try to load voice profile for context
    voice_profile = ""
    voice_path = root / "config" / "voice_profile.md"
    if voice_path.exists():
        voice_profile = load_md(voice_path)[:500]  # First 500 chars

    # ─── LLM Path ───
    if llm.available:
        prompt = f"""You are a LinkedIn content researcher for Indian SMBs and startup founders.

Topic: {topic}
Goal: {goal} (maximize saves, comments, or velocity)

Your voice:
{voice_profile}

Generate a research brief with EXACTLY these sections:

## Hook Angles (3 specific angles, each < 150 chars)
1. [First 150 chars hook]
2. [Second 150 chars hook]
3. [Third 150 chars hook]

## Key Stats & Data Points (5 specific facts)
1. [Stat about {topic}]
2. [Stat about {topic}]
3. [Stat about {topic}]
4. [Stat about {topic}]
5. [Stat about {topic}]

## Contrarian Angle
[One paragraph: the counter-narrative or bold take on {topic}]

## Indian SMB Angle
[One paragraph: how this connects to Indian small/medium businesses]

## Suggested CTA
[One sentence: invite experience-sharing, NOT engagement bait]

---

Output only the markdown above. No introductions, no disclaimers.
"""
        brief_text = llm.complete("writing", prompt, max_tokens=800)
        if brief_text:
            brief_path.parent.mkdir(parents=True, exist_ok=True)
            brief_path.write_text(brief_text)
            return brief_path

    # ─── Fallback Path (no LLM or LLM failed) ───
    fallback_brief = f"""# Research Brief — {date}

## Hook Angles (3 specific angles, each < 150 chars)
1. {topic} — [PLACEHOLDER: specific number or bold claim]
2. {topic} + Indian context — [PLACEHOLDER: contrarian angle]
3. ROI of {topic} — [PLACEHOLDER: impact metric]

## Key Stats & Data Points (5 specific facts)
1. [PLACEHOLDER: statistic about {topic}]
2. [PLACEHOLDER: statistic about {topic}]
3. [PLACEHOLDER: statistic about {topic}]
4. [PLACEHOLDER: statistic about {topic}]
5. [PLACEHOLDER: statistic about {topic}]

## Contrarian Angle
[PLACEHOLDER: Counter-narrative on {topic}. Most people believe X, but Y is actually true because of Z.]

## Indian SMB Angle
[PLACEHOLDER: How {topic} applies specifically to Indian small/medium businesses. Include ₹ amounts, specific regions (Tier 1/2/3 cities), or industries (healthcare, e-commerce, education).]

## Suggested CTA
[PLACEHOLDER: Invite experience-sharing. Example: "What's your biggest blocker with {topic}?"]
"""

    brief_path.parent.mkdir(parents=True, exist_ok=True)
    brief_path.write_text(fallback_brief)

    return brief_path


if __name__ == "__main__":
    date = sys.argv[1] if len(sys.argv) > 1 else ""
    if not date:
        from config_loader import get_today
        date = get_today()
    path = run(date=date)
    print(f"  Research brief: {path}")
