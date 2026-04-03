#!/usr/bin/env python3
"""
PostForge Tool Config Generator — Generate config files for multiple AI coding tools.

Reads CLAUDE.md (the canonical config) and creates equivalent files for other tools:
  AGENTS.md      → OpenClaw, generic tools
  CODEX.md       → OpenAI Codex
  .cursorrules   → Cursor
  CONVENTIONS.md → Kilo, Antigravity, others

Usage:
    python scripts/generate_tool_configs.py
    python scripts/generate_tool_configs.py --list     # show what would be created
    python scripts/generate_tool_configs.py --clean     # remove generated files
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import get_postforge_root, load_md


TARGETS = {
    "AGENTS.md": "Auto-generated from CLAUDE.md for OpenClaw and generic AI coding tools.",
    "CODEX.md": "Auto-generated from CLAUDE.md for OpenAI Codex.",
    ".cursorrules": "Auto-generated from CLAUDE.md for Cursor.",
    "CONVENTIONS.md": "Auto-generated from CLAUDE.md for Kilo, Antigravity, and other tools.",
}

HEADER_TEMPLATE = """# {comment}
# Do not edit directly — edit CLAUDE.md and re-run: python scripts/generate_tool_configs.py

"""


def generate_configs():
    root = get_postforge_root()
    source = root / "CLAUDE.md"

    content = load_md(source)
    if not content:
        print("Error: CLAUDE.md not found or empty.")
        sys.exit(1)

    for filename, comment in TARGETS.items():
        target = root / filename
        header = HEADER_TEMPLATE.format(comment=comment)
        target.write_text(header + content, encoding="utf-8")
        print(f"  Generated: {filename}")

    print(f"\n  {len(TARGETS)} config files generated from CLAUDE.md")


def list_targets():
    root = get_postforge_root()
    print("\n  Target files:")
    for filename, comment in TARGETS.items():
        target = root / filename
        status = "exists" if target.exists() else "not created"
        print(f"    {filename} — {comment} [{status}]")


def clean_targets():
    root = get_postforge_root()
    removed = 0
    for filename in TARGETS:
        target = root / filename
        if target.exists():
            content = target.read_text()
            if "Auto-generated from CLAUDE.md" in content:
                target.unlink()
                print(f"  Removed: {filename}")
                removed += 1
            else:
                print(f"  Skipped: {filename} (not auto-generated)")
    print(f"\n  {removed} files removed")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--list":
            list_targets()
        elif sys.argv[1] == "--clean":
            clean_targets()
        else:
            print("Usage: python scripts/generate_tool_configs.py [--list | --clean]")
    else:
        generate_configs()
