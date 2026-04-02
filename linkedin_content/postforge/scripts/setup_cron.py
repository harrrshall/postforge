#!/usr/bin/env python3
"""
PostForge Cron Setup — Install scheduled automation jobs.

Installs 4 cron jobs:
1. Trend scan every 4 hours (6AM, 10AM, 2PM, 6PM, 10PM IST)
2. Sprint review every 3 days at 9PM
3. Voice drift check on 1st, 10th, 19th, 28th at 9PM
4. Daily research brief at 7AM

Usage:
    python scripts/setup_cron.py          # install cron jobs
    python scripts/setup_cron.py --remove # remove PostForge cron jobs
    python scripts/setup_cron.py --list   # list current PostForge cron jobs
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_loader import get_postforge_root


def get_cron_jobs() -> str:
    """Generate PostForge cron job entries."""
    root = get_postforge_root()
    python = sys.executable or "python3"

    jobs = f"""# ─── PostForge Scheduled Automation ───
# Trend scan every 4 hours
0 6,10,14,18,22 * * * cd {root} && {python} scripts/runner.py scan >> logs/scan.log 2>&1

# Sprint review every 3 days at 9PM
0 21 */3 * * cd {root} && {python} scripts/auto_learn.py >> logs/sprint.log 2>&1

# Voice drift detection (1st, 10th, 19th, 28th at 9PM)
0 21 1,10,19,28 * * cd {root} && {python} scripts/runner.py voice-drift >> logs/voice.log 2>&1

# Daily research brief at 7AM
0 7 * * * cd {root} && {python} scripts/runner.py auto-research >> logs/research.log 2>&1
# ─── End PostForge ───
"""
    return jobs


def get_existing_crontab() -> str:
    """Get current crontab contents."""
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        return result.stdout if result.returncode == 0 else ""
    except Exception:
        return ""


def install_cron():
    """Install PostForge cron jobs (preserving existing jobs)."""
    existing = get_existing_crontab()

    # Remove any existing PostForge jobs
    lines = existing.split("\n")
    cleaned = []
    in_postforge = False
    for line in lines:
        if "PostForge Scheduled Automation" in line:
            in_postforge = True
            continue
        if "End PostForge" in line:
            in_postforge = False
            continue
        if not in_postforge:
            cleaned.append(line)

    # Add new PostForge jobs
    new_crontab = "\n".join(cleaned).strip() + "\n\n" + get_cron_jobs()

    # Install
    try:
        subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            text=True,
            check=True,
            timeout=5,
        )
        print("  PostForge cron jobs installed successfully.")
        print()
        list_cron()
    except subprocess.CalledProcessError as e:
        print(f"  Error installing cron jobs: {e}")
        sys.exit(1)


def remove_cron():
    """Remove PostForge cron jobs (preserving other jobs)."""
    existing = get_existing_crontab()

    lines = existing.split("\n")
    cleaned = []
    in_postforge = False
    for line in lines:
        if "PostForge Scheduled Automation" in line:
            in_postforge = True
            continue
        if "End PostForge" in line:
            in_postforge = False
            continue
        if not in_postforge:
            cleaned.append(line)

    new_crontab = "\n".join(cleaned).strip() + "\n"

    try:
        subprocess.run(
            ["crontab", "-"],
            input=new_crontab,
            text=True,
            check=True,
            timeout=5,
        )
        print("  PostForge cron jobs removed.")
    except subprocess.CalledProcessError as e:
        print(f"  Error: {e}")


def list_cron():
    """List PostForge cron jobs."""
    existing = get_existing_crontab()
    lines = [l for l in existing.split("\n") if "postforge" in l.lower() or "PostForge" in l]

    if not lines:
        print("  No PostForge cron jobs found.")
        return

    print("  PostForge cron jobs:")
    for line in lines:
        if line.strip() and not line.strip().startswith("#"):
            # Parse schedule
            parts = line.strip().split()
            if len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command_parts = line.split("&&")
                if len(command_parts) > 1:
                    cmd = command_parts[-1].strip().split(">>")[0].strip()
                else:
                    cmd = " ".join(parts[5:])
                print(f"    {schedule}  →  {cmd}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--remove":
            remove_cron()
        elif sys.argv[1] == "--list":
            list_cron()
        else:
            print("Usage: python scripts/setup_cron.py [--remove|--list]")
    else:
        install_cron()
