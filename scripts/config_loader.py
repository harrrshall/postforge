#!/usr/bin/env python3
"""
PostForge Config Loader — Shared file I/O utilities for all scripts.
"""

import json
from datetime import datetime
from pathlib import Path


def get_postforge_root() -> Path:
    """Return the PostForge project root directory."""
    return Path(__file__).parent.parent


def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict if missing or invalid."""
    path = Path(path)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_json(path: Path, data: dict):
    """Save data as formatted JSON."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_md(path: Path) -> str:
    """Load a markdown file, return empty string if missing."""
    path = Path(path)
    if not path.exists():
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def append_md(path: Path, content: str):
    """Append content to a markdown file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write("\n" + content)


def ensure_dirs():
    """Create all required PostForge directories if they don't exist."""
    root = get_postforge_root()
    dirs = [
        root / "config",
        root / "config" / "voice_samples",
        root / "memory",
        root / "research" / "scan",
        root / "research" / "briefs",
        root / "output" / "variants",
        root / "output" / "scores",
        root / "output" / "selected",
        root / "output" / "intakes",
        root / "output" / "simulations",
        root / "logs",
        root / "tests",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def load_performance_history() -> dict:
    """Load performance_history.json."""
    root = get_postforge_root()
    return load_json(root / "memory" / "performance_history.json")


def load_scoring_weights() -> dict:
    """Load scoring_weights.json."""
    root = get_postforge_root()
    return load_json(root / "config" / "scoring_weights.json")


def load_sprint_log() -> dict:
    """Load sprint_log.json."""
    root = get_postforge_root()
    return load_json(root / "memory" / "sprint_log.json")


def load_intake(date: str = None) -> dict:
    """Load today's (or specified date's) intake JSON."""
    root = get_postforge_root()
    date = date or get_today()
    return load_json(root / "output" / "intakes" / f"{date}.json")


def load_scores(date: str = None) -> dict:
    """Load today's (or specified date's) scores JSON."""
    root = get_postforge_root()
    date = date or get_today()
    return load_json(root / "output" / "scores" / f"{date}.json")


def count_tracked_posts() -> int:
    """Count total tracked posts in performance history."""
    history = load_performance_history()
    return len(history.get("posts", []))


def load_provider_config() -> dict:
    """Load LLM provider configuration."""
    root = get_postforge_root()
    return load_json(root / "config" / "provider.json")


def get_last_sprint_date() -> str | None:
    """Get the end date of the last sprint review."""
    sprint_log = load_sprint_log()
    sprints = sprint_log.get("sprints", [])
    if not sprints:
        return None
    return sprints[-1].get("dates", "").split(" to ")[-1] if sprints[-1].get("dates") else None
