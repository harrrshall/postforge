"""Unit tests for AutoLearner — math verification, no file I/O."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit

DIMS = ["hook_strength", "save_worthiness", "comment_worthiness",
        "dwell_time_potential", "voice_authenticity", "algorithm_compliance"]


def _make_learner(postforge_root, weights_override=None, history_override=None,
                  sprint_log_override=None):
    """Create an AutoLearner with controlled data in tmp dir."""
    from auto_learn import AutoLearner

    weights = weights_override or {
        "version": 1,
        "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
        "learning_rate": 0.20,
        "total_calibration_posts": 0,
        "weight_history": [],
    }
    history = history_override or {"posts": [], "metadata": {}}
    sprint_log = sprint_log_override or {"sprints": [], "metadata": {"total_sprints": 0, "current_sprint": 0}}

    import config_loader
    config_loader.save_json(postforge_root / "config" / "scoring_weights.json", weights)
    config_loader.save_json(postforge_root / "memory" / "performance_history.json", history)
    config_loader.save_json(postforge_root / "memory" / "sprint_log.json", sprint_log)

    return AutoLearner(root=postforge_root)


# ─── Learning Rate ───


class TestEffectiveLearningRate:
    @pytest.mark.parametrize("posts,expected_lr", [
        (0, 0.10), (1, 0.10), (9, 0.10),
        (10, 0.15), (15, 0.15), (19, 0.15),
        (20, 0.20), (50, 0.20), (100, 0.20),
    ])
    def test_learning_rate_thresholds(self, postforge_root, posts, expected_lr):
        weights = {
            "version": 1,
            "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
            "learning_rate": 0.20,
            "total_calibration_posts": posts,
            "weight_history": [],
        }
        learner = _make_learner(postforge_root, weights_override=weights)
        assert learner.get_effective_learning_rate() == expected_lr


# ─── Posts Since Last Sprint ───


class TestPostsSinceLastSprint:
    def test_no_sprints_returns_all(self, postforge_root):
        history = {
            "posts": [
                {"date_posted": "2026-04-01"},
                {"date_posted": "2026-04-02"},
            ],
            "metadata": {},
        }
        learner = _make_learner(postforge_root, history_override=history)
        result = learner.get_posts_since_last_sprint()
        assert len(result) == 2

    def test_filters_after_sprint_end(self, postforge_root):
        history = {
            "posts": [
                {"date_posted": "2026-04-01"},
                {"date_posted": "2026-04-03"},
                {"date_posted": "2026-04-05"},
            ],
            "metadata": {},
        }
        sprint_log = {
            "sprints": [{"dates": "2026-04-01 to 2026-04-03"}],
            "metadata": {"total_sprints": 1, "current_sprint": 1},
        }
        learner = _make_learner(postforge_root, history_override=history, sprint_log_override=sprint_log)
        result = learner.get_posts_since_last_sprint()
        # Only "2026-04-05" is > "2026-04-03"
        assert len(result) == 1
        assert result[0]["date_posted"] == "2026-04-05"

    def test_sprint_end_date_excluded(self, postforge_root):
        """Posts on the exact sprint end date should be excluded (string > comparison)."""
        history = {
            "posts": [{"date_posted": "2026-04-03"}],
            "metadata": {},
        }
        sprint_log = {
            "sprints": [{"dates": "2026-04-01 to 2026-04-03"}],
            "metadata": {"total_sprints": 1, "current_sprint": 1},
        }
        learner = _make_learner(postforge_root, history_override=history, sprint_log_override=sprint_log)
        result = learner.get_posts_since_last_sprint()
        assert len(result) == 0


# ─── Should Run Sprint Review ───


class TestShouldRunSprintReview:
    def test_fewer_than_2_posts(self, postforge_root):
        history = {"posts": [{"date_posted": "2026-04-10"}], "metadata": {}}
        learner = _make_learner(postforge_root, history_override=history)
        assert learner.should_run_sprint_review() is False

    def test_enough_posts_no_prior_sprint(self, postforge_root):
        history = {
            "posts": [
                {"date_posted": "2026-04-10"},
                {"date_posted": "2026-04-11"},
            ],
            "metadata": {},
        }
        learner = _make_learner(postforge_root, history_override=history)
        assert learner.should_run_sprint_review() is True

    def test_enough_posts_but_too_soon(self, postforge_root, freeze_today):
        """2+ posts but sprint ended today — too soon."""
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        history = {
            "posts": [
                {"date_posted": today},
                {"date_posted": today},
                {"date_posted": today},
            ],
            "metadata": {},
        }
        sprint_log = {
            "sprints": [{"dates": f"2026-04-01 to {today}"}],
            "metadata": {"total_sprints": 1, "current_sprint": 1},
        }
        learner = _make_learner(postforge_root, history_override=history, sprint_log_override=sprint_log)
        # All posts are on sprint end date, so 0 posts since last sprint
        assert learner.should_run_sprint_review() is False


# ─── Dimension Correlations ───


class TestDimensionCorrelations:
    def test_complementary_scores_equal_weights(self, postforge_root):
        """Two posts with complementary dim scores should produce equal correlations."""
        posts = [
            {
                "dimension_scores_at_time": {d: (100 if d == "hook_strength" else 50) for d in DIMS},
                "actual_24h": {"engagement_rate": "10%"},
            },
            {
                "dimension_scores_at_time": {d: (100 if d == "save_worthiness" else 50) for d in DIMS},
                "actual_24h": {"engagement_rate": "10%"},
            },
        ]
        learner = _make_learner(postforge_root)
        correlations = learner.calculate_dimension_correlations(posts)

        # All dims should sum to 1.0
        assert abs(sum(correlations.values()) - 1.0) < 0.001

        # hook_strength and save_worthiness should be equal (both have 100 in one post, 50 in other)
        assert abs(correlations["hook_strength"] - correlations["save_worthiness"]) < 0.001

    def test_all_zero_engagement_fallback(self, postforge_root):
        """All zero engagement rates should fall back to equal weights."""
        posts = [
            {
                "dimension_scores_at_time": {d: 50 for d in DIMS},
                "actual_24h": {"engagement_rate": "0%"},
            },
            {
                "dimension_scores_at_time": {d: 50 for d in DIMS},
                "actual_24h": {"engagement_rate": "0%"},
            },
        ]
        learner = _make_learner(postforge_root)
        correlations = learner.calculate_dimension_correlations(posts)
        assert abs(sum(correlations.values()) - 1.0) < 0.001
        for v in correlations.values():
            assert abs(v - 1/6) < 0.001

    def test_string_engagement_rate_parsed(self, postforge_root):
        """Engagement rates as strings like '3.5%' should be parsed."""
        posts = [
            {
                "dimension_scores_at_time": {d: 80 for d in DIMS},
                "actual_24h": {"engagement_rate": "3.5%"},
            },
        ]
        learner = _make_learner(postforge_root)
        correlations = learner.calculate_dimension_correlations(posts)
        assert all(v > 0 for v in correlations.values())
        assert abs(sum(correlations.values()) - 1.0) < 0.001

    def test_single_post_valid_output(self, postforge_root):
        posts = [{
            "dimension_scores_at_time": {d: 90 for d in DIMS},
            "actual_24h": {"engagement_rate": "5%"},
        }]
        learner = _make_learner(postforge_root)
        correlations = learner.calculate_dimension_correlations(posts)
        assert len(correlations) == 6
        assert abs(sum(correlations.values()) - 1.0) < 0.001

    def test_high_dim_high_engagement_gets_higher_weight(self, postforge_root):
        """A dimension with consistently high scores alongside high engagement should get higher weight."""
        posts = [
            {
                "dimension_scores_at_time": {"hook_strength": 100, "save_worthiness": 10,
                    "comment_worthiness": 50, "dwell_time_potential": 50,
                    "voice_authenticity": 50, "algorithm_compliance": 50},
                "actual_24h": {"engagement_rate": "10%"},
            },
            {
                "dimension_scores_at_time": {"hook_strength": 100, "save_worthiness": 10,
                    "comment_worthiness": 50, "dwell_time_potential": 50,
                    "voice_authenticity": 50, "algorithm_compliance": 50},
                "actual_24h": {"engagement_rate": "8%"},
            },
        ]
        learner = _make_learner(postforge_root)
        correlations = learner.calculate_dimension_correlations(posts)
        assert correlations["hook_strength"] > correlations["save_worthiness"]


# ─── EMA Weight Update ───


class TestUpdateWeightsEMA:
    def test_stable_when_actual_equals_old(self, postforge_root):
        """EMA with actual=old should produce same weights."""
        old_weights = {d: round(1/6, 4) for d in DIMS}
        weights_data = {
            "version": 1,
            "dimensions": {d: {"weight": old_weights[d], "description": d} for d in DIMS},
            "total_calibration_posts": 0,
            "learning_rate": 0.20,
            "weight_history": [],
        }
        learner = _make_learner(postforge_root, weights_override=weights_data)
        result = learner.update_weights_ema(old_weights)
        for d in DIMS:
            assert abs(result[d] - old_weights[d]) < 0.002  # rounding tolerance

    def test_extreme_actual_shifts_weights(self, postforge_root):
        """If actual gives all weight to one dim, EMA should shift toward it."""
        weights_data = {
            "version": 1,
            "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
            "total_calibration_posts": 0,
            "learning_rate": 0.20,
            "weight_history": [],
        }
        learner = _make_learner(postforge_root, weights_override=weights_data)

        actual = {d: 0.0 for d in DIMS}
        actual["hook_strength"] = 1.0

        result = learner.update_weights_ema(actual)

        # hook_strength should increase
        assert result["hook_strength"] > round(1/6, 4)
        # Others should decrease
        for d in DIMS:
            if d != "hook_strength":
                assert result[d] < round(1/6, 4)

    def test_output_sums_to_one(self, postforge_root):
        weights_data = {
            "version": 1,
            "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
            "total_calibration_posts": 5,
            "learning_rate": 0.20,
            "weight_history": [],
        }
        learner = _make_learner(postforge_root, weights_override=weights_data)
        actual = {"hook_strength": 0.5, "save_worthiness": 0.3, "comment_worthiness": 0.1,
                  "dwell_time_potential": 0.05, "voice_authenticity": 0.03, "algorithm_compliance": 0.02}
        result = learner.update_weights_ema(actual)
        assert abs(sum(result.values()) - 1.0) < 0.001

    def test_weights_rounded_to_4_decimals(self, postforge_root):
        weights_data = {
            "version": 1,
            "dimensions": {d: {"weight": round(1/6, 4), "description": d} for d in DIMS},
            "total_calibration_posts": 0,
            "learning_rate": 0.20,
            "weight_history": [],
        }
        learner = _make_learner(postforge_root, weights_override=weights_data)
        actual = {d: 0.1 + i * 0.03 for i, d in enumerate(DIMS)}
        total = sum(actual.values())
        actual = {d: v / total for d, v in actual.items()}

        result = learner.update_weights_ema(actual)
        for d, w in result.items():
            decimal_places = len(str(w).split(".")[-1]) if "." in str(w) else 0
            assert decimal_places <= 4

    def test_ema_formula_correctness(self, postforge_root):
        """Verify the exact EMA formula: new = (1-lr)*old + lr*actual."""
        old_w = {"hook_strength": 0.25, "save_worthiness": 0.25,
                 "comment_worthiness": 0.20, "dwell_time_potential": 0.15,
                 "voice_authenticity": 0.10, "algorithm_compliance": 0.05}
        weights_data = {
            "version": 1,
            "dimensions": {d: {"weight": old_w[d], "description": d} for d in DIMS},
            "total_calibration_posts": 0,  # lr = 0.10
            "learning_rate": 0.20,
            "weight_history": [],
        }
        actual = {"hook_strength": 0.40, "save_worthiness": 0.20,
                  "comment_worthiness": 0.15, "dwell_time_potential": 0.10,
                  "voice_authenticity": 0.10, "algorithm_compliance": 0.05}

        learner = _make_learner(postforge_root, weights_override=weights_data)
        lr = learner.get_effective_learning_rate()  # 0.10
        result = learner.update_weights_ema(actual)

        # Manually compute expected (before normalization)
        raw = {}
        for d in DIMS:
            raw[d] = (1 - lr) * old_w[d] + lr * actual[d]
        total = sum(raw.values())
        expected = {d: round(v / total, 4) for d, v in raw.items()}

        for d in DIMS:
            assert abs(result[d] - expected[d]) < 0.001, f"{d}: {result[d]} != {expected[d]}"


# ─── Extract Winners ───


class TestExtractWinners:
    def test_outperformed_always_winner(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{"outcome": "OUTPERFORMED", "hook_text": "test", "date_posted": "2026-04-10",
                  "actual_24h": {"engagement_rate": "5%"}, "format": "text", "pillar": "proof",
                  "variant_type": "Data Story", "predicted": {"engagement_rate_range": "3-4%"}}]
        # Create the memory file
        (postforge_root / "memory" / "winning_hooks.md").write_text("# Hooks\n")
        winners = learner.extract_winners(posts)
        assert len(winners) == 1

    def test_matched_but_exceeds_120pct(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{
            "outcome": "MATCHED",
            "predicted": {"engagement_rate_range": "3.0-5.0%"},  # midpoint 4.0
            "actual_24h": {"engagement_rate": "5.5%"},  # 5.5 > 4.0 * 1.2 = 4.8
            "hook_text": "test", "date_posted": "2026-04-10",
            "format": "text", "pillar": "proof", "variant_type": "Data Story",
        }]
        (postforge_root / "memory" / "winning_hooks.md").write_text("# Hooks\n")
        winners = learner.extract_winners(posts)
        assert len(winners) == 1

    def test_matched_within_range_not_winner(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{
            "outcome": "MATCHED",
            "predicted": {"engagement_rate_range": "3.0-5.0%"},  # midpoint 4.0
            "actual_24h": {"engagement_rate": "4.0%"},  # 4.0 < 4.0 * 1.2 = 4.8
            "hook_text": "test", "date_posted": "2026-04-10",
            "format": "text", "pillar": "proof", "variant_type": "Data Story",
        }]
        (postforge_root / "memory" / "winning_hooks.md").write_text("# Hooks\n")
        winners = learner.extract_winners(posts)
        assert len(winners) == 0

    def test_zero_predicted_no_crash(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{
            "outcome": "MATCHED",
            "predicted": {"engagement_rate_range": "0-0%"},
            "actual_24h": {"engagement_rate": "3%"},
            "hook_text": "test", "date_posted": "2026-04-10",
            "format": "text", "pillar": "proof", "variant_type": "Data Story",
        }]
        (postforge_root / "memory" / "winning_hooks.md").write_text("# Hooks\n")
        winners = learner.extract_winners(posts)  # should not crash


# ─── Extract Anti-Patterns ───


class TestExtractAntiPatterns:
    def test_underperformed_always_antipattern(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{"outcome": "UNDERPERFORMED", "hook_text": "test", "date_posted": "2026-04-10",
                  "actual_24h": {"engagement_rate": "1%"}, "format": "text", "pillar": "proof",
                  "variant_type": "Data Story", "predicted": {"engagement_rate_range": "3-5%"}}]
        (postforge_root / "memory" / "anti_patterns.md").write_text("# Anti-Patterns\n")
        losers = learner.extract_anti_patterns(posts)
        assert len(losers) == 1

    def test_below_80pct_predicted(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{
            "outcome": "MATCHED",
            "predicted": {"engagement_rate_range": "5.0-7.0%"},  # midpoint 6.0
            "actual_24h": {"engagement_rate": "4.0%"},  # 4.0 < 6.0 * 0.8 = 4.8
            "hook_text": "test", "date_posted": "2026-04-10",
            "format": "text", "pillar": "proof", "variant_type": "Data Story",
        }]
        (postforge_root / "memory" / "anti_patterns.md").write_text("# Anti-Patterns\n")
        losers = learner.extract_anti_patterns(posts)
        assert len(losers) == 1

    def test_malformed_range_no_crash(self, postforge_root):
        learner = _make_learner(postforge_root)
        posts = [{
            "outcome": "MATCHED",
            "predicted": {"engagement_rate_range": "5%"},  # no dash
            "actual_24h": {"engagement_rate": "3%"},
            "hook_text": "test", "date_posted": "2026-04-10",
            "format": "text", "pillar": "proof", "variant_type": "Data Story",
        }]
        (postforge_root / "memory" / "anti_patterns.md").write_text("# Anti-Patterns\n")
        learner.extract_anti_patterns(posts)  # should not crash
