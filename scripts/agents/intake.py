#!/usr/bin/env python3
"""Intake Agent — Collect topic, goal, and context before generation."""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import save_json, load_json, get_postforge_root
from llm_client import LLMClient


# ─── Pillar Detection ───

def detect_pillar(goal: str) -> str:
    """Auto-detect content pillar from goal."""
    goal_to_pillar = {
        "saves": "proof",
        "comments": "shift",
        "velocity": "trend",
        "authority": "proof",
        "leads": "build",
    }
    return goal_to_pillar.get(goal, "proof")


def compute_pipeline_hints(goal: str) -> dict:
    """Compute variant emphasis and scoring boost from goal."""
    goal_to_hints = {
        "saves": {
            "variant_emphasis": "D, B, C",  # Framework, Data Story, Personal
            "scoring_boost_dimension": "save_worthiness",
            "scoring_boost_multiplier": 1.20,
        },
        "comments": {
            "variant_emphasis": "A, E, C",  # Contrarian, Hot Take, Personal
            "scoring_boost_dimension": "comment_worthiness",
            "scoring_boost_multiplier": 1.20,
        },
        "velocity": {
            "variant_emphasis": "F, E, A",  # Trend, Hot Take, Contrarian
            "scoring_boost_dimension": "hook_strength",
            "scoring_boost_multiplier": 1.15,
        },
        "authority": {
            "variant_emphasis": "B, D, C",  # Data Story, Framework, Personal
            "scoring_boost_dimension": "voice_authenticity",
            "scoring_boost_multiplier": 1.20,
        },
        "leads": {
            "variant_emphasis": "C, D, B",  # Personal, Framework, Data Story
            "scoring_boost_dimension": "comment_worthiness",
            "scoring_boost_multiplier": 1.15,
        },
    }
    return goal_to_hints.get(goal, goal_to_hints["saves"])


# ─── Main Agent ───

def run(root: Path = None, llm: LLMClient = None, date: str = "",
        topic: str = "", goal: str = "saves", format_: str = "text",
        context: str = "") -> Path:
    """
    Collect intake for today. Returns path to written intake JSON.

    Args:
        root: PostForge root directory
        llm: LLMClient instance
        date: YYYY-MM-DD date string (today if empty)
        topic: Topic string (interactive prompt if empty)
        goal: Primary goal (saves, comments, velocity, authority, leads)
        format_: Content format (text, carousel, video)
        context: User-provided context/data points
    """
    if root is None:
        root = get_postforge_root()
    if llm is None:
        llm = LLMClient()
    if not date:
        from config_loader import get_today
        date = get_today()

    intake_path = root / "output" / "intakes" / f"{date}.json"

    # Idempotency: if intake already exists, load and return it
    if intake_path.exists():
        return intake_path

    # ─── Interactive Path (if topic not provided) ───
    if not topic:
        print("\n  PostForge Intake Agent")
        print("  " + "=" * 40)
        topic = input("\n  Topic (or 'q' to quit): ").strip()
        if topic.lower() == 'q':
            return intake_path
        goal = input(f"  Goal (saves/comments/velocity/authority/leads) [{goal}]: ").strip() or goal
        format_ = input(f"  Format (text/carousel/video) [{format_}]: ").strip() or format_
        context = input("  Context / data points (optional): ").strip() or ""

    # ─── Compute pipeline hints ───
    pillar = detect_pillar(goal)
    hints = compute_pipeline_hints(goal)

    # ─── Build intake JSON ───
    intake = {
        "date": date,
        "created_at": datetime.now().isoformat(),
        "topic": topic,
        "angle": None,
        "goal": {
            "primary": goal,
            "description": f"Optimize for {goal.replace('_', ' ')}",
        },
        "context": {
            "user_provided": context if context else None,
            "data_points": [context] if context else [],
            "stories": [],
        },
        "format": format_,
        "timing": {
            "preference": "next_optimal",
            "recommended": "Wednesday 9:00 AM IST",
            "urgency": "standard",
        },
        "topic_dna_check": "aligned",  # TODO: validate against niche_topics.md
        "pipeline_hints": {
            "research_focus": topic.replace(" ", " OR "),
            "variant_emphasis": hints["variant_emphasis"],
            "scoring_boost_dimension": hints["scoring_boost_dimension"],
            "scoring_boost_multiplier": hints["scoring_boost_multiplier"],
            "pillar": pillar,
        },
    }

    # ─── Write intake JSON ───
    intake_path.parent.mkdir(parents=True, exist_ok=True)
    save_json(intake_path, intake)

    return intake_path


if __name__ == "__main__":
    # CLI usage: python scripts/agents/intake.py [topic] [goal] [format]
    topic = sys.argv[1] if len(sys.argv) > 1 else ""
    goal = sys.argv[2] if len(sys.argv) > 2 else "saves"
    format_ = sys.argv[3] if len(sys.argv) > 3 else "text"

    from config_loader import get_today
    date = get_today()
    path = run(topic=topic, goal=goal, format_=format_, date=date)
    print(f"  Intake saved: {path}")
