#!/usr/bin/env python3
"""
PostForge Pipeline Runner — CLI entry point for all pipeline operations.

Usage:
    python scripts/runner.py status
    python scripts/runner.py generate [--auto-select]
    python scripts/runner.py learn <post_id>
    python scripts/runner.py sprint-review
    python scripts/runner.py scan
    python scripts/runner.py simulate <variant_path>
    python scripts/runner.py auto-research
    python scripts/runner.py voice-drift
    python scripts/runner.py setup-cron
"""

import sys
import json
import glob
from pathlib import Path
from datetime import datetime, timedelta

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent))

from config_loader import (
    get_postforge_root, get_today, ensure_dirs,
    load_json, save_json, load_md, append_md,
    load_performance_history, load_scoring_weights, load_sprint_log,
    load_intake, load_scores, count_tracked_posts, get_last_sprint_date,
)


# ─── Status Command ───

def cmd_status():
    """Show system health dashboard."""
    root = get_postforge_root()
    today = get_today()

    # Load all data
    history = load_performance_history()
    weights = load_scoring_weights()
    sprint_log = load_sprint_log()

    posts = history.get("posts", [])
    sprints = sprint_log.get("sprints", [])
    total_posts = len(posts)
    total_sprints = len(sprints)

    # Calculate stats
    avg_accuracy = None
    total_engagements = 0
    best_format = "N/A"
    best_pillar = "N/A"

    if total_posts > 0:
        accuracies = [p.get("prediction_accuracy", {}).get("engagement_rate", 0) for p in posts if p.get("prediction_accuracy")]
        if accuracies:
            avg_accuracy = sum(accuracies) / len(accuracies)

        total_engagements = sum(
            sum([
                p.get("actual_24h", {}).get("likes", 0),
                p.get("actual_24h", {}).get("comments", 0),
                p.get("actual_24h", {}).get("saves", 0),
                p.get("actual_24h", {}).get("shares", 0),
            ]) for p in posts
        )

        # Best format
        format_engagement = {}
        for p in posts:
            fmt = p.get("format", "unknown")
            rate = p.get("actual_24h", {}).get("engagement_rate", 0)
            if isinstance(rate, str):
                try:
                    rate = float(rate.rstrip("%"))
                except ValueError:
                    rate = 0
            if fmt not in format_engagement:
                format_engagement[fmt] = []
            format_engagement[fmt].append(rate)

        if format_engagement:
            best_format = max(format_engagement, key=lambda k: sum(format_engagement[k]) / len(format_engagement[k]))

        # Best pillar
        pillar_engagement = {}
        for p in posts:
            pillar = p.get("pillar", "unknown")
            rate = p.get("actual_24h", {}).get("engagement_rate", 0)
            if isinstance(rate, str):
                try:
                    rate = float(rate.rstrip("%"))
                except ValueError:
                    rate = 0
            if pillar not in pillar_engagement:
                pillar_engagement[pillar] = []
            pillar_engagement[pillar].append(rate)

        if pillar_engagement:
            best_pillar = max(pillar_engagement, key=lambda k: sum(pillar_engagement[k]) / len(pillar_engagement[k]))

    # Weights info
    weights_version = weights.get("version", 0)
    weights_updated = weights.get("last_updated", "never")
    calibration_posts = weights.get("total_calibration_posts", 0)

    # Days since last sprint
    last_sprint = get_last_sprint_date()
    if last_sprint:
        try:
            days_since = (datetime.now() - datetime.strptime(last_sprint, "%Y-%m-%d")).days
        except ValueError:
            days_since = "?"
    else:
        days_since = "never"

    # Voice profile age
    voice_path = root / "config" / "voice_profile.md"
    voice_content = load_md(voice_path)
    voice_status = "placeholder" if "no corpus data yet" in voice_content.lower() else "active"

    # Count outputs
    variant_dirs = list((root / "output" / "variants").glob("2*"))
    score_files = list((root / "output" / "scores").glob("*.json"))
    sim_files = list((root / "output" / "simulations").glob("*.json"))
    scan_files = list((root / "research" / "scan").glob("*.md"))

    # Cron status
    import subprocess
    try:
        cron_result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        cron_lines = [l for l in cron_result.stdout.split("\n") if "postforge" in l.lower() or "PostForge" in l]
        cron_status = f"{len(cron_lines)} jobs active" if cron_lines else "no jobs"
    except Exception:
        cron_status = "unknown"

    # Print dashboard
    print()
    print("=" * 60)
    print("  POSTFORGE SYSTEM STATUS")
    print("=" * 60)
    print()
    print(f"  Date:                {today}")
    print()
    print("  --- Performance ---")
    print(f"  Posts tracked:       {total_posts}")
    print(f"  Total engagements:   {total_engagements:,}")
    print(f"  Avg prediction acc:  {f'{avg_accuracy:.0%}' if avg_accuracy is not None else 'N/A'}")
    print(f"  Best format:         {best_format}")
    print(f"  Best pillar:         {best_pillar}")
    print()
    print("  --- Learning ---")
    print(f"  Weights version:     {weights_version}")
    print(f"  Weights updated:     {weights_updated}")
    print(f"  Calibration posts:   {calibration_posts}")
    print(f"  Sprints completed:   {total_sprints}")
    print(f"  Days since sprint:   {days_since}")
    print()
    print("  --- Content ---")
    print(f"  Days generated:      {len(variant_dirs)}")
    print(f"  Score files:         {len(score_files)}")
    print(f"  Simulations:         {len(sim_files)}")
    print(f"  Trend scans:         {len(scan_files)}")
    print()
    print("  --- System ---")
    print(f"  Voice profile:       {voice_status}")
    print(f"  Cron:                {cron_status}")
    print()
    print("=" * 60)


# ─── Learn Command ───

def cmd_learn(post_id: str):
    """Input metrics for a published post and update performance history."""
    root = get_postforge_root()

    # Parse post_id: expected format YYYY-MM-DD-X (e.g., 2026-04-02-D)
    parts = post_id.rsplit("-", 1)
    if len(parts) != 2 or len(parts[0]) != 10:
        print(f"Error: Invalid post_id format '{post_id}'. Expected: YYYY-MM-DD-X (e.g., 2026-04-02-D)")
        sys.exit(1)

    date_str = parts[0]
    variant_letter = parts[1].upper()

    # Load predicted scores
    scores = load_scores(date_str)
    predicted = None
    variant_type = "unknown"
    variant_format = "text"
    pillar = "unknown"
    dimension_scores = {}
    hook_text = ""

    if scores and "variants" in scores:
        for v in scores["variants"]:
            if v.get("id", "").upper() == variant_letter:
                predicted = v.get("predicted_engagement", {})
                variant_type = v.get("type", "unknown")
                variant_format = v.get("format", "text")
                dimension_scores = {k: v2.get("score", 0) for k, v2 in v.get("dimension_scores", {}).items()}
                break

    # Load variant to get hook and pillar
    variant_path = root / "output" / "variants" / date_str / f"variant_{variant_letter.lower()}.md"
    if variant_path.exists():
        variant_content = load_md(variant_path)
        for line in variant_content.split("\n"):
            if line.startswith("- Pillar:"):
                pillar = line.split(":", 1)[1].strip()
            if line.startswith("- First 150 chars:"):
                hook_text = line.split(":", 1)[1].strip().strip('"')

    # Collect metrics from user
    print(f"\n  Enter metrics for post {post_id}")
    print(f"  Variant: {variant_type} ({variant_format})")
    print(f"  Date: {date_str}")
    print()

    try:
        impressions = int(input("  Impressions: "))
        likes = int(input("  Likes: "))
        comments = int(input("  Comments: "))
        saves = int(input("  Saves: "))
        shares = int(input("  Shares: "))
        profile_visits = int(input("  Profile visits: "))
        first_hour_comments = int(input("  First hour comments: "))
        comment_quality = input("  Comment quality [substantive/short/mixed]: ").strip().lower()
    except (ValueError, EOFError) as e:
        print(f"\nError: Invalid input — {e}")
        sys.exit(1)

    # Calculate engagement rate
    total_engagement = likes + comments + saves + shares
    engagement_rate = (total_engagement / impressions * 100) if impressions > 0 else 0

    # Calculate prediction accuracy
    prediction_accuracy = {}
    if predicted:
        # Parse predicted engagement rate range (e.g., "3.5-5.5%")
        pred_rate_str = predicted.get("engagement_rate_range", "0-0%")
        try:
            pred_parts = pred_rate_str.replace("%", "").split("-")
            pred_low = float(pred_parts[0])
            pred_high = float(pred_parts[1]) if len(pred_parts) > 1 else pred_low
            pred_mid = (pred_low + pred_high) / 2
            prediction_accuracy["engagement_rate"] = max(0, 1 - abs(engagement_rate - pred_mid) / max(pred_mid, 0.01))
        except (ValueError, IndexError):
            pass

        # Parse predicted comments range (e.g., "10-22")
        pred_comments_str = predicted.get("expected_comments", "0-0")
        try:
            pred_parts = str(pred_comments_str).split("-")
            pred_low = int(pred_parts[0])
            pred_high = int(pred_parts[1]) if len(pred_parts) > 1 else pred_low
            pred_mid = (pred_low + pred_high) / 2
            prediction_accuracy["comments"] = max(0, 1 - abs(comments - pred_mid) / max(pred_mid, 1))
        except (ValueError, IndexError):
            pass

        # Parse predicted saves range
        pred_saves_str = predicted.get("expected_saves", "0-0")
        try:
            pred_parts = str(pred_saves_str).split("-")
            pred_low = int(pred_parts[0])
            pred_high = int(pred_parts[1]) if len(pred_parts) > 1 else pred_low
            pred_mid = (pred_low + pred_high) / 2
            prediction_accuracy["saves"] = max(0, 1 - abs(saves - pred_mid) / max(pred_mid, 1))
        except (ValueError, IndexError):
            pass

    # Classify outcome
    avg_acc = sum(prediction_accuracy.values()) / max(len(prediction_accuracy), 1) if prediction_accuracy else 0
    if avg_acc > 0.80:
        outcome = "MATCHED"
    elif engagement_rate > (pred_mid * 1.2 if predicted else 999):
        outcome = "OUTPERFORMED"
    else:
        outcome = "UNDERPERFORMED"

    # Build post entry
    post_entry = {
        "post_id": post_id,
        "date_posted": date_str,
        "variant_type": variant_type,
        "format": variant_format,
        "pillar": pillar,
        "hook_text": hook_text,
        "posting_time": "manual entry",
        "predicted": predicted or {},
        "actual_24h": {
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "shares": shares,
            "profile_visits": profile_visits,
            "engagement_rate": f"{engagement_rate:.2f}%",
            "first_hour_comments": first_hour_comments,
            "comment_quality": comment_quality,
        },
        "actual_7d": None,
        "prediction_accuracy": prediction_accuracy,
        "outcome": outcome,
        "dimension_scores_at_time": dimension_scores,
    }

    # Append to performance history
    history = load_performance_history()
    history.setdefault("posts", []).append(post_entry)
    history.setdefault("metadata", {})
    history["metadata"]["total_posts_tracked"] = len(history["posts"])
    history["metadata"]["total_engagements"] = history["metadata"].get("total_engagements", 0) + total_engagement

    # Recalculate avg accuracy
    all_accs = [p.get("prediction_accuracy", {}).get("engagement_rate", 0) for p in history["posts"] if p.get("prediction_accuracy")]
    if all_accs:
        history["metadata"]["avg_prediction_accuracy"] = sum(all_accs) / len(all_accs)

    save_json(root / "memory" / "performance_history.json", history)

    # Print results
    print()
    print("  --- Results ---")
    print(f"  Engagement rate:     {engagement_rate:.2f}%")
    print(f"  Outcome:             {outcome}")
    if prediction_accuracy:
        for metric, acc in prediction_accuracy.items():
            print(f"  Prediction acc ({metric}): {acc:.0%}")
    print()
    print(f"  Saved to performance_history.json (total posts: {len(history['posts'])})")

    # Check if sprint review is ready
    posts_since_last = _count_posts_since_last_sprint(history)
    if posts_since_last >= 3:
        print(f"\n  Sprint review ready ({posts_since_last} posts since last review).")
        print("  Run: python scripts/runner.py sprint-review")


def _count_posts_since_last_sprint(history: dict) -> int:
    """Count posts added since the last sprint review."""
    sprint_log = load_sprint_log()
    sprints = sprint_log.get("sprints", [])

    if not sprints:
        return len(history.get("posts", []))

    last_sprint_end = sprints[-1].get("dates", "").split(" to ")[-1]
    count = 0
    for post in history.get("posts", []):
        if post.get("date_posted", "") > last_sprint_end:
            count += 1
    return count


# ─── Sprint Review Command ───

def cmd_sprint_review():
    """Run sprint analysis and weight update."""
    # Import auto_learn
    try:
        from auto_learn import AutoLearner
    except ImportError:
        print("Error: auto_learn.py not found. Build Phase 2 first.")
        sys.exit(1)

    learner = AutoLearner(get_postforge_root())
    learner.run()


# ─── Main CLI ───

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/runner.py <command> [args]")
        print()
        print("Commands:")
        print("  status              System health dashboard")
        print("  generate            Full pipeline: intake → research → write → score → present")
        print("  learn <post_id>     Input metrics for a published post")
        print("  sprint-review       Run sprint analysis + weight update")
        print("  scan                Run trend scan")
        print("  simulate <path>     Deep multi-agent simulation on a post variant")
        print("  auto-research       Non-interactive daily research (for cron)")
        print("  voice-drift         Check voice drift (for cron)")
        print("  setup-cron          Install cron jobs")
        sys.exit(0)

    command = sys.argv[1]
    ensure_dirs()

    if command == "status":
        cmd_status()
    elif command == "learn":
        if len(sys.argv) < 3:
            print("Usage: python scripts/runner.py learn <post_id>")
            print("Example: python scripts/runner.py learn 2026-04-02-D")
            sys.exit(1)
        cmd_learn(sys.argv[2])
    elif command == "sprint-review":
        cmd_sprint_review()
    elif command == "generate":
        print("Generate command: not yet implemented (Phase 4)")
    elif command == "scan":
        print("Scan command: not yet implemented (Phase 5)")
    elif command == "simulate":
        print("Simulate command: not yet implemented (Phase 3)")
    elif command == "auto-research":
        print("Auto-research command: not yet implemented (Phase 5)")
    elif command == "voice-drift":
        print("Voice-drift command: not yet implemented (Phase 5)")
    elif command == "setup-cron":
        print("Setup-cron command: not yet implemented (Phase 5)")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
