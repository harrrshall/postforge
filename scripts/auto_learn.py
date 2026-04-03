#!/usr/bin/env python3
"""
PostForge Auto-Learner — Self-improving sprint review + weight calibration.

Runs every 3 days (via cron or manual). Analyzes post performance,
updates scoring weights via EMA, extracts winning patterns and anti-patterns.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import (
    get_postforge_root, get_today, load_json, save_json, load_md, append_md,
    load_performance_history, load_scoring_weights, load_sprint_log,
)


class AutoLearner:
    def __init__(self, root: Path = None):
        self.root = root or get_postforge_root()
        self.history = load_performance_history()
        self.weights = load_scoring_weights()
        self.sprint_log = load_sprint_log()

    def get_effective_learning_rate(self) -> float:
        """Damped learning rate based on total tracked posts."""
        total_posts = self.weights.get("total_calibration_posts", 0)
        if total_posts < 10:
            return 0.10  # Cautious: sprints 1-3
        elif total_posts < 20:
            return 0.15  # Moderate: sprints 4-7
        else:
            return 0.20  # Full speed: sprint 8+

    def get_posts_since_last_sprint(self) -> list:
        """Get all posts added since the last sprint review."""
        sprints = self.sprint_log.get("sprints", [])
        posts = self.history.get("posts", [])

        if not sprints:
            return posts  # No prior sprints — all posts are new

        last_sprint_end = sprints[-1].get("dates", "").split(" to ")[-1].strip()
        return [p for p in posts if p.get("date_posted", "") > last_sprint_end]

    def should_run_sprint_review(self) -> bool:
        """Check if enough new data since last sprint review."""
        new_posts = self.get_posts_since_last_sprint()
        if len(new_posts) < 2:
            return False

        # Check days since last sprint
        sprints = self.sprint_log.get("sprints", [])
        if sprints:
            last_end = sprints[-1].get("dates", "").split(" to ")[-1].strip()
            try:
                days_since = (datetime.now() - datetime.strptime(last_end, "%Y-%m-%d")).days
                if days_since < 2:
                    return False
            except ValueError:
                pass

        return True

    def calculate_dimension_correlations(self, sprint_posts: list) -> dict:
        """Calculate how well each scoring dimension correlated with actual performance."""
        dimensions = list(self.weights.get("dimensions", {}).keys())
        correlations = {}

        # For small sample sizes (3-5 posts), use normalized importance scoring
        for dim in dimensions:
            weighted_sum = 0
            total_weight = 0

            for post in sprint_posts:
                dim_score = post.get("dimension_scores_at_time", {}).get(dim, 50)
                actual_rate_str = post.get("actual_24h", {}).get("engagement_rate", "0%")

                # Parse engagement rate
                try:
                    if isinstance(actual_rate_str, str):
                        actual_rate = float(actual_rate_str.rstrip("%"))
                    else:
                        actual_rate = float(actual_rate_str)
                except (ValueError, TypeError):
                    actual_rate = 0

                # Normalized importance: high dim score + high actual = strong correlation
                weighted_sum += (dim_score / 100) * actual_rate
                total_weight += 1

            correlations[dim] = weighted_sum / max(total_weight, 1)

        # Normalize correlations to sum to 1.0
        total = sum(correlations.values())
        if total > 0:
            correlations = {k: v / total for k, v in correlations.items()}
        else:
            # Fallback: equal weights
            correlations = {k: 1.0 / len(dimensions) for k in dimensions}

        return correlations

    def update_weights_ema(self, actual_correlations: dict) -> dict:
        """Apply EMA formula to update scoring weights."""
        learning_rate = self.get_effective_learning_rate()
        old_weights = {d: self.weights["dimensions"][d]["weight"] for d in self.weights["dimensions"]}

        new_weights = {}
        for dim in old_weights:
            old_w = old_weights[dim]
            actual_w = actual_correlations.get(dim, old_w)
            new_weights[dim] = (1 - learning_rate) * old_w + learning_rate * actual_w

        # Normalize to sum to 1.0
        total = sum(new_weights.values())
        if total > 0:
            new_weights = {d: round(w / total, 4) for d, w in new_weights.items()}

        return new_weights

    def extract_winners(self, sprint_posts: list):
        """Find outperforming posts and extract patterns."""
        winners = []
        for post in sprint_posts:
            if post.get("outcome") == "OUTPERFORMED":
                winners.append(post)
            else:
                # Check if engagement rate exceeded predicted range midpoint by >20%
                pred = post.get("predicted", {})
                pred_rate_str = pred.get("engagement_rate_range", "0-0%")
                try:
                    parts = pred_rate_str.replace("%", "").split("-")
                    pred_mid = (float(parts[0]) + float(parts[1])) / 2 if len(parts) > 1 else float(parts[0])
                    actual_str = post.get("actual_24h", {}).get("engagement_rate", "0%")
                    actual = float(actual_str.rstrip("%")) if isinstance(actual_str, str) else float(actual_str)
                    if pred_mid > 0 and actual > pred_mid * 1.2:
                        winners.append(post)
                except (ValueError, IndexError):
                    pass

        # Append to winning_hooks.md
        if winners:
            hooks_content = ""
            for w in winners:
                hooks_content += f"\n### {w.get('date_posted', '?')} — {w.get('actual_24h', {}).get('engagement_rate', '?')}\n"
                hooks_content += f"Hook: \"{w.get('hook_text', 'N/A')}\"\n"
                hooks_content += f"Format: {w.get('format', '?')}\n"
                hooks_content += f"Pillar: {w.get('pillar', '?')}\n"
                hooks_content += f"Type: {w.get('variant_type', '?')}\n"
                hooks_content += f"Why it worked: Outperformed prediction — actual engagement exceeded expected by >20%\n"

            append_md(self.root / "memory" / "winning_hooks.md", hooks_content)

        return winners

    def extract_anti_patterns(self, sprint_posts: list):
        """Find underperforming posts and extract anti-patterns."""
        losers = []
        for post in sprint_posts:
            if post.get("outcome") == "UNDERPERFORMED":
                losers.append(post)
            else:
                pred = post.get("predicted", {})
                pred_rate_str = pred.get("engagement_rate_range", "0-0%")
                try:
                    parts = pred_rate_str.replace("%", "").split("-")
                    pred_mid = (float(parts[0]) + float(parts[1])) / 2 if len(parts) > 1 else float(parts[0])
                    actual_str = post.get("actual_24h", {}).get("engagement_rate", "0%")
                    actual = float(actual_str.rstrip("%")) if isinstance(actual_str, str) else float(actual_str)
                    if pred_mid > 0 and actual < pred_mid * 0.8:
                        losers.append(post)
                except (ValueError, IndexError):
                    pass

        if losers:
            patterns_content = "\n## Data-Driven Anti-Patterns (Sprint Review)\n"
            for l in losers:
                patterns_content += f"\n### {l.get('date_posted', '?')} — {l.get('actual_24h', {}).get('engagement_rate', '?')}\n"
                patterns_content += f"**What went wrong:** Underperformed prediction\n"
                patterns_content += f"**Hook:** \"{l.get('hook_text', 'N/A')}\"\n"
                patterns_content += f"**Format:** {l.get('format', '?')}\n"
                patterns_content += f"**Pattern to avoid:** {l.get('variant_type', '?')} type with this hook structure underperformed\n"

            append_md(self.root / "memory" / "anti_patterns.md", patterns_content)

        return losers

    def run_sprint_review(self, sprint_posts: list = None):
        """Full sprint review pipeline."""
        if sprint_posts is None:
            sprint_posts = self.get_posts_since_last_sprint()

        if len(sprint_posts) < 2:
            print("  Not enough posts for sprint review (need at least 2).")
            return

        sprint_number = len(self.sprint_log.get("sprints", [])) + 1
        today = get_today()

        print()
        print("=" * 60)
        print(f"  SPRINT {sprint_number} REVIEW")
        print("=" * 60)

        # 1. Analyze
        total_engagements = sum(
            sum([
                p.get("actual_24h", {}).get("likes", 0),
                p.get("actual_24h", {}).get("comments", 0),
                p.get("actual_24h", {}).get("saves", 0),
                p.get("actual_24h", {}).get("shares", 0),
            ]) for p in sprint_posts
        )

        engagement_rates = []
        for p in sprint_posts:
            rate_str = p.get("actual_24h", {}).get("engagement_rate", "0%")
            try:
                rate = float(rate_str.rstrip("%")) if isinstance(rate_str, str) else float(rate_str)
                engagement_rates.append((p, rate))
            except (ValueError, TypeError):
                engagement_rates.append((p, 0))

        best_post = max(engagement_rates, key=lambda x: x[1]) if engagement_rates else (None, 0)
        worst_post = min(engagement_rates, key=lambda x: x[1]) if engagement_rates else (None, 0)
        avg_rate = sum(r for _, r in engagement_rates) / max(len(engagement_rates), 1)

        print(f"\n  Posts: {len(sprint_posts)} | Engagements: {total_engagements:,} | Avg rate: {avg_rate:.1f}%")

        if best_post[0]:
            print(f"  Best:  {best_post[0].get('post_id', '?')} — {best_post[1]:.1f}% ({best_post[0].get('variant_type', '?')})")
        if worst_post[0]:
            print(f"  Worst: {worst_post[0].get('post_id', '?')} — {worst_post[1]:.1f}% ({worst_post[0].get('variant_type', '?')})")

        # 2. Calculate correlations
        correlations = self.calculate_dimension_correlations(sprint_posts)

        # 3. Update weights
        old_weights = {d: self.weights["dimensions"][d]["weight"] for d in self.weights["dimensions"]}
        new_weights = self.update_weights_ema(correlations)

        weight_changes = {}
        for dim in new_weights:
            old_val = old_weights.get(dim, 0)
            new_val = new_weights[dim]
            change = new_val - old_val
            weight_changes[dim] = f"{'+' if change >= 0 else ''}{change:.4f}"

            # Update in weights data
            self.weights["dimensions"][dim]["weight"] = new_val

        self.weights["version"] = self.weights.get("version", 1) + 1
        self.weights["last_updated"] = today
        self.weights["total_calibration_posts"] = self.weights.get("total_calibration_posts", 0) + len(sprint_posts)

        # Add to weight history
        self.weights.setdefault("weight_history", []).append({
            "version": self.weights["version"],
            "date": today,
            "weights": new_weights,
            "reason": f"Sprint {sprint_number} review: {len(sprint_posts)} posts analyzed, learning_rate={self.get_effective_learning_rate()}"
        })

        save_json(self.root / "config" / "scoring_weights.json", self.weights)

        print(f"\n  Scoring Weight Updates (v{self.weights['version']}, lr={self.get_effective_learning_rate()}):")
        for dim, change in weight_changes.items():
            print(f"    {dim}: {old_weights[dim]:.4f} → {new_weights[dim]:.4f} ({change})")

        # 4. Extract patterns
        winners = self.extract_winners(sprint_posts)
        losers = self.extract_anti_patterns(sprint_posts)
        print(f"\n  Patterns: {len(winners)} winners extracted, {len(losers)} anti-patterns logged")

        # 5. Calculate prediction accuracy
        accs = []
        for p in sprint_posts:
            pa = p.get("prediction_accuracy", {})
            if "engagement_rate" in pa:
                accs.append(pa["engagement_rate"])
        avg_acc = sum(accs) / max(len(accs), 1) if accs else 0

        # 6. Log sprint
        dates = sorted([p.get("date_posted", "") for p in sprint_posts])
        sprint_entry = {
            "sprint_number": sprint_number,
            "dates": f"{dates[0]} to {dates[-1]}" if dates else today,
            "posts_published": len(sprint_posts),
            "total_engagements": total_engagements,
            "avg_engagement_rate": f"{avg_rate:.1f}%",
            "best_performing": {
                "post_id": best_post[0].get("post_id", "?") if best_post[0] else "N/A",
                "engagement_rate": f"{best_post[1]:.1f}%",
                "why": f"{best_post[0].get('variant_type', '?')} {best_post[0].get('format', '?')}" if best_post[0] else "N/A"
            },
            "worst_performing": {
                "post_id": worst_post[0].get("post_id", "?") if worst_post[0] else "N/A",
                "engagement_rate": f"{worst_post[1]:.1f}%",
                "why": f"{worst_post[0].get('variant_type', '?')} {worst_post[0].get('format', '?')}" if worst_post[0] else "N/A"
            },
            "scoring_weight_changes": weight_changes,
            "patterns_extracted": {
                "winning_hooks": len(winners),
                "anti_patterns": len(losers),
            },
            "prediction_accuracy_this_sprint": round(avg_acc, 2),
            "learning_rate_used": self.get_effective_learning_rate(),
        }

        self.sprint_log.setdefault("sprints", []).append(sprint_entry)
        self.sprint_log["metadata"]["total_sprints"] = len(self.sprint_log["sprints"])
        self.sprint_log["metadata"]["current_sprint"] = sprint_number
        save_json(self.root / "memory" / "sprint_log.json", self.sprint_log)

        print(f"\n  Prediction accuracy: {avg_acc:.0%}")
        print(f"\n  Sprint {sprint_number} logged to sprint_log.json")
        print()
        print("=" * 60)

    def run(self):
        """Entry point — check if review is needed, run if so."""
        if self.should_run_sprint_review():
            sprint_posts = self.get_posts_since_last_sprint()
            self.run_sprint_review(sprint_posts)
        else:
            new_posts = self.get_posts_since_last_sprint()
            print(f"  Not ready for sprint review ({len(new_posts)} posts since last, need 2+).")


# ─── CLI Entry ───

if __name__ == "__main__":
    learner = AutoLearner()
    if len(sys.argv) > 1 and sys.argv[1] == "--force":
        # Force run with all available posts
        posts = learner.get_posts_since_last_sprint()
        if posts:
            learner.run_sprint_review(posts)
        else:
            print("No posts to review.")
    else:
        learner.run()
