"""End-to-end tests for the PostForge self-improving loop.

Tests the full cycle: learn metrics → sprint review → weight update → verify adaptation.
"""

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.e2e

DIMS = ["hook_strength", "save_worthiness", "comment_worthiness",
        "dwell_time_potential", "voice_authenticity", "algorithm_compliance"]


def _make_post_entry(post_id, date, engagement_rate_pct, dimension_scores,
                     outcome="MATCHED", pred_range="3.0-5.0%",
                     impressions=10000, variant_type="Data Story", fmt="text", pillar="proof"):
    """Create a post entry with controlled values."""
    total_eng = int(impressions * engagement_rate_pct / 100)
    likes = int(total_eng * 0.5)
    comments = int(total_eng * 0.25)
    saves = int(total_eng * 0.15)
    shares = total_eng - likes - comments - saves

    pred_parts = pred_range.replace("%", "").split("-")
    pred_mid = (float(pred_parts[0]) + float(pred_parts[1])) / 2
    rate_acc = max(0, 1 - abs(engagement_rate_pct - pred_mid) / max(pred_mid, 0.01))

    return {
        "post_id": post_id,
        "date_posted": date,
        "variant_type": variant_type,
        "format": fmt,
        "pillar": pillar,
        "hook_text": f"Test hook for {post_id}",
        "posting_time": "manual entry",
        "predicted": {
            "engagement_rate_range": pred_range,
            "expected_comments": "10-20",
            "expected_saves": "5-15",
        },
        "actual_24h": {
            "impressions": impressions,
            "likes": likes,
            "comments": comments,
            "saves": saves,
            "shares": shares,
            "profile_visits": 50,
            "engagement_rate": f"{engagement_rate_pct:.2f}%",
            "first_hour_comments": comments // 2,
            "comment_quality": "substantive",
        },
        "actual_7d": None,
        "prediction_accuracy": {
            "engagement_rate": round(rate_acc, 3),
            "comments": 0.7,
            "saves": 0.8,
        },
        "outcome": outcome,
        "dimension_scores_at_time": dimension_scores,
    }


def _setup_fresh_system(root, weights_v1, posts, sprint_log=None):
    """Write clean state to the filesystem."""
    import config_loader
    config_loader.save_json(root / "config" / "scoring_weights.json", weights_v1)
    config_loader.save_json(root / "memory" / "performance_history.json", {
        "posts": posts,
        "metadata": {"total_posts_tracked": len(posts), "total_engagements": 0},
    })
    config_loader.save_json(root / "memory" / "sprint_log.json",
                            sprint_log or {"sprints": [], "metadata": {"total_sprints": 0, "current_sprint": 0}})
    (root / "memory" / "winning_hooks.md").write_text("# Winning Hooks\n")
    (root / "memory" / "anti_patterns.md").write_text("# Anti-Patterns\n")


def _make_v1_weights():
    return {
        "version": 1,
        "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
        "learning_rate": 0.20,
        "total_calibration_posts": 0,
        "weight_history": [{"version": 1, "date": "2026-04-01", "weights": {d: round(1/6, 4) for d in DIMS}, "reason": "Initial"}],
    }


# ─── Full Feedback Loop ───


class TestFullFeedbackLoop:
    def test_weights_change_after_sprint_review(self, postforge_root, freeze_today):
        """Start → add 3 posts → sprint review → weights change, version increments."""
        from auto_learn import AutoLearner
        import config_loader

        v1 = _make_v1_weights()
        posts = [
            _make_post_entry("2026-04-10-A", "2026-04-10", 5.0,
                             {d: (90 if d == "hook_strength" else 50) for d in DIMS}),
            _make_post_entry("2026-04-11-B", "2026-04-11", 3.0,
                             {d: (90 if d == "save_worthiness" else 50) for d in DIMS}),
            _make_post_entry("2026-04-12-C", "2026-04-12", 2.0,
                             {d: 50 for d in DIMS}, outcome="UNDERPERFORMED"),
        ]
        _setup_fresh_system(postforge_root, v1, posts)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts)

        # Reload from disk
        weights = config_loader.load_scoring_weights()
        assert weights["version"] == 2
        assert weights["total_calibration_posts"] == 3
        assert abs(sum(weights["dimensions"][d]["weight"] for d in DIMS) - 1.0) < 0.001

        sprint_log = config_loader.load_sprint_log()
        assert len(sprint_log["sprints"]) == 1
        assert sprint_log["sprints"][0]["posts_published"] == 3

    def test_weights_reflect_performance_signal(self, postforge_root, freeze_today):
        """When hook_strength correlates with high engagement, its weight should increase."""
        from auto_learn import AutoLearner
        import config_loader

        v1 = _make_v1_weights()
        # Posts where high hook_strength → high engagement
        posts = [
            _make_post_entry("2026-04-10-A", "2026-04-10", 8.0,
                             {"hook_strength": 95, "save_worthiness": 30,
                              "comment_worthiness": 40, "dwell_time_potential": 35,
                              "voice_authenticity": 50, "algorithm_compliance": 50}),
            _make_post_entry("2026-04-11-B", "2026-04-11", 7.5,
                             {"hook_strength": 90, "save_worthiness": 25,
                              "comment_worthiness": 35, "dwell_time_potential": 30,
                              "voice_authenticity": 45, "algorithm_compliance": 55}),
            _make_post_entry("2026-04-12-C", "2026-04-12", 1.5,
                             {"hook_strength": 20, "save_worthiness": 80,
                              "comment_worthiness": 70, "dwell_time_potential": 75,
                              "voice_authenticity": 85, "algorithm_compliance": 90}),
        ]
        _setup_fresh_system(postforge_root, v1, posts)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts)

        weights = config_loader.load_scoring_weights()
        hook_w = weights["dimensions"]["hook_strength"]["weight"]
        save_w = weights["dimensions"]["save_worthiness"]["weight"]

        # hook_strength should have increased (correlated with high engagement)
        assert hook_w > round(1/6, 4), f"hook_strength ({hook_w}) should exceed initial ({round(1/6, 4)})"


class TestLearningRateProgression:
    def test_lr_increases_with_posts(self, postforge_root, freeze_today):
        """Learning rate should progress: 0.10 → 0.15 → 0.20 as posts accumulate."""
        from auto_learn import AutoLearner
        import config_loader

        v1 = _make_v1_weights()

        # Sprint 1: 5 posts (0 → 5 calibration posts)
        posts_s1 = [
            _make_post_entry(f"2026-04-{10+i}-A", f"2026-04-{10+i}", 4.0 + i * 0.5,
                             {d: 50 + i * 5 for d in DIMS})
            for i in range(5)
        ]
        _setup_fresh_system(postforge_root, v1, posts_s1)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts_s1)

        sprint_log = config_loader.load_sprint_log()
        assert sprint_log["sprints"][0]["learning_rate_used"] == 0.10

        # Sprint 2: 5 more posts (5 → 10)
        weights_after_s1 = config_loader.load_scoring_weights()
        posts_s2 = [
            _make_post_entry(f"2026-04-{20+i}-B", f"2026-04-{20+i}", 3.0 + i * 0.3,
                             {d: 60 for d in DIMS})
            for i in range(5)
        ]
        history = config_loader.load_performance_history()
        history["posts"].extend(posts_s2)
        history["metadata"]["total_posts_tracked"] = len(history["posts"])
        config_loader.save_json(postforge_root / "memory" / "performance_history.json", history)

        learner2 = AutoLearner(root=postforge_root)
        learner2.run_sprint_review(posts_s2)

        sprint_log = config_loader.load_sprint_log()
        assert sprint_log["sprints"][1]["learning_rate_used"] == 0.15

        # Sprint 3: 10 more posts (10 → 20)
        weights_after_s2 = config_loader.load_scoring_weights()
        posts_s3 = [
            _make_post_entry(f"2026-05-{1+i}-C", f"2026-05-{1+i:02d}", 5.0,
                             {d: 70 for d in DIMS})
            for i in range(10)
        ]
        history = config_loader.load_performance_history()
        history["posts"].extend(posts_s3)
        history["metadata"]["total_posts_tracked"] = len(history["posts"])
        config_loader.save_json(postforge_root / "memory" / "performance_history.json", history)

        learner3 = AutoLearner(root=postforge_root)
        learner3.run_sprint_review(posts_s3)

        sprint_log = config_loader.load_sprint_log()
        assert sprint_log["sprints"][2]["learning_rate_used"] == 0.20


class TestWeightsConverge:
    def test_consistent_signal_shifts_weights(self, postforge_root, freeze_today):
        """Run 3 sprint reviews with consistent signal — weights should move further each time."""
        from auto_learn import AutoLearner
        import config_loader

        v1 = _make_v1_weights()
        initial_hook_w = round(1/6, 4)

        hook_weights = [initial_hook_w]

        for sprint_num in range(3):
            base_date = 10 + sprint_num * 5
            posts = [
                _make_post_entry(
                    f"2026-04-{base_date+i}-X", f"2026-04-{base_date+i}",
                    engagement_rate_pct=8.0,
                    dimension_scores={"hook_strength": 95, "save_worthiness": 30,
                                      "comment_worthiness": 30, "dwell_time_potential": 30,
                                      "voice_authenticity": 30, "algorithm_compliance": 30},
                )
                for i in range(3)
            ]

            if sprint_num == 0:
                _setup_fresh_system(postforge_root, v1, posts)
            else:
                history = config_loader.load_performance_history()
                history["posts"].extend(posts)
                history["metadata"]["total_posts_tracked"] = len(history["posts"])
                config_loader.save_json(postforge_root / "memory" / "performance_history.json", history)

            learner = AutoLearner(root=postforge_root)
            learner.run_sprint_review(posts)

            weights = config_loader.load_scoring_weights()
            hook_weights.append(weights["dimensions"]["hook_strength"]["weight"])

        # hook_strength should be monotonically increasing (consistent positive signal)
        for i in range(1, len(hook_weights)):
            assert hook_weights[i] >= hook_weights[i-1], \
                f"hook_strength should increase: {hook_weights}"


class TestMemoryFlow:
    def test_winners_populate_hooks_md(self, postforge_root, freeze_today):
        from auto_learn import AutoLearner

        v1 = _make_v1_weights()
        posts = [
            _make_post_entry("2026-04-10-A", "2026-04-10", 8.0,
                             {d: 80 for d in DIMS}, outcome="OUTPERFORMED"),
            _make_post_entry("2026-04-11-B", "2026-04-11", 5.0,
                             {d: 60 for d in DIMS}),
        ]
        _setup_fresh_system(postforge_root, v1, posts)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts)

        hooks = (postforge_root / "memory" / "winning_hooks.md").read_text()
        assert "2026-04-10" in hooks

    def test_antipatterns_populate_md(self, postforge_root, freeze_today):
        from auto_learn import AutoLearner

        v1 = _make_v1_weights()
        posts = [
            _make_post_entry("2026-04-10-A", "2026-04-10", 1.0,
                             {d: 40 for d in DIMS}, outcome="UNDERPERFORMED"),
            _make_post_entry("2026-04-11-B", "2026-04-11", 5.0,
                             {d: 70 for d in DIMS}),
        ]
        _setup_fresh_system(postforge_root, v1, posts)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts)

        patterns = (postforge_root / "memory" / "anti_patterns.md").read_text()
        assert "2026-04-10" in patterns or "Data-Driven" in patterns


class TestSimulationToRanking:
    def test_full_simulation_ranking_flow(self, populated_postforge):
        """Write variants → simulate → rank → winner has highest composite."""
        from simulator import SimulationEngine

        engine = SimulationEngine(disable_api=True)
        results = engine.simulate_all_variants("2026-04-15")
        rankings = engine.rank_variants(results)

        assert len(rankings) == 2
        # Winner should have highest score
        assert rankings[0][1] >= rankings[1][1]
        # Composite scores should be valid
        for vid, score in rankings:
            assert 0 <= score <= 1.0


class TestDataSchemaIntegrity:
    def test_all_output_schemas_valid_after_loop(self, postforge_root, freeze_today):
        """After a full loop, every output file should have the expected schema."""
        from auto_learn import AutoLearner
        import config_loader

        v1 = _make_v1_weights()
        posts = [
            _make_post_entry(f"2026-04-{10+i}-X", f"2026-04-{10+i}", 4.0 + i,
                             {d: 50 + i * 10 for d in DIMS})
            for i in range(3)
        ]
        _setup_fresh_system(postforge_root, v1, posts)

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review(posts)

        # Validate performance_history schema
        history = config_loader.load_performance_history()
        assert "posts" in history
        assert "metadata" in history
        for post in history["posts"]:
            assert "post_id" in post
            assert "actual_24h" in post
            assert "prediction_accuracy" in post
            assert "dimension_scores_at_time" in post

        # Validate scoring_weights schema
        weights = config_loader.load_scoring_weights()
        assert "version" in weights
        assert "dimensions" in weights
        assert len(weights["dimensions"]) == 6
        for dim_data in weights["dimensions"].values():
            assert "weight" in dim_data
            assert 0 <= dim_data["weight"] <= 1
        assert "weight_history" in weights
        assert "total_calibration_posts" in weights

        # Validate sprint_log schema
        sprint_log = config_loader.load_sprint_log()
        assert "sprints" in sprint_log
        for sprint in sprint_log["sprints"]:
            assert "sprint_number" in sprint
            assert "dates" in sprint
            assert "posts_published" in sprint
            assert "scoring_weight_changes" in sprint
            assert "learning_rate_used" in sprint
            assert "prediction_accuracy_this_sprint" in sprint
