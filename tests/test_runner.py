"""Tests for runner.py CLI commands."""

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.integration


# ─── cmd_learn ───


class TestCmdLearn:
    def _mock_inputs(self, impressions=10000, likes=200, comments=30, saves=40,
                     shares=10, profile_visits=50, first_hour=15, quality="substantive"):
        """Return an iterator of input() responses."""
        return iter([
            str(impressions), str(likes), str(comments), str(saves),
            str(shares), str(profile_visits), str(first_hour), quality,
        ])

    def test_engagement_rate_calculation(self, populated_postforge, freeze_today):
        import runner

        inputs = self._mock_inputs(impressions=10000, likes=200, comments=30, saves=40, shares=10)
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        import config_loader
        history = config_loader.load_performance_history()
        post = history["posts"][-1]

        # engagement = (200+30+40+10)/10000 * 100 = 2.80%
        assert post["actual_24h"]["engagement_rate"] == "2.80%"

    def test_prediction_accuracy(self, populated_postforge, freeze_today):
        import runner

        # Predicted for variant A: engagement_rate_range "3.0-5.0%", midpoint=4.0
        inputs = self._mock_inputs(impressions=10000, likes=200, comments=30, saves=40, shares=10)
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        import config_loader
        history = config_loader.load_performance_history()
        post = history["posts"][-1]

        # actual rate = 2.80%, predicted midpoint = 4.0%
        # accuracy = max(0, 1 - |2.8 - 4.0| / 4.0) = max(0, 1 - 0.3) = 0.7
        assert abs(post["prediction_accuracy"]["engagement_rate"] - 0.7) < 0.01

    def test_outcome_underperformed(self, populated_postforge, freeze_today):
        import runner

        # Low engagement → UNDERPERFORMED
        inputs = self._mock_inputs(impressions=10000, likes=50, comments=5, saves=3, shares=1)
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        import config_loader
        history = config_loader.load_performance_history()
        post = history["posts"][-1]
        assert post["outcome"] == "UNDERPERFORMED"

    def test_post_appended_to_history(self, populated_postforge, freeze_today):
        import runner
        import config_loader

        history_before = config_loader.load_performance_history()
        count_before = len(history_before.get("posts", []))

        inputs = self._mock_inputs()
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        history_after = config_loader.load_performance_history()
        assert len(history_after["posts"]) == count_before + 1
        assert history_after["posts"][-1]["post_id"] == "2026-04-15-A"

    def test_metadata_updated(self, populated_postforge, freeze_today):
        import runner

        inputs = self._mock_inputs()
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        import config_loader
        history = config_loader.load_performance_history()
        assert history["metadata"]["total_posts_tracked"] == len(history["posts"])

    def test_invalid_post_id_exits(self, populated_postforge):
        import runner
        with pytest.raises(SystemExit):
            runner.cmd_learn("bad-id")

    def test_zero_impressions_no_crash(self, populated_postforge, freeze_today):
        import runner

        inputs = self._mock_inputs(impressions=0, likes=0, comments=0, saves=0, shares=0)
        with patch("builtins.input", side_effect=inputs):
            runner.cmd_learn("2026-04-15-A")

        import config_loader
        history = config_loader.load_performance_history()
        post = history["posts"][-1]
        assert post["actual_24h"]["engagement_rate"] == "0.00%"


# ─── cmd_status ───


class TestCmdStatus:
    def test_runs_on_empty_data(self, postforge_root, freeze_today):
        import runner
        runner.cmd_status()

    def test_runs_on_populated_data(self, populated_postforge, freeze_today):
        import runner
        runner.cmd_status()


# ─── _count_posts_since_last_sprint ───


class TestCountPostsSinceLastSprint:
    def test_all_posts_when_no_sprints(self, postforge_root):
        import runner
        import config_loader
        config_loader.save_json(
            postforge_root / "memory" / "sprint_log.json",
            {"sprints": [], "metadata": {}}
        )
        history = {"posts": [{"date_posted": "2026-04-10"}, {"date_posted": "2026-04-11"}]}
        assert runner._count_posts_since_last_sprint(history) == 2

    def test_filters_after_sprint(self, postforge_root):
        import runner
        import config_loader
        config_loader.save_json(
            postforge_root / "memory" / "sprint_log.json",
            {"sprints": [{"dates": "2026-04-01 to 2026-04-05"}], "metadata": {}}
        )
        history = {
            "posts": [
                {"date_posted": "2026-04-03"},
                {"date_posted": "2026-04-06"},
                {"date_posted": "2026-04-07"},
            ]
        }
        assert runner._count_posts_since_last_sprint(history) == 2


# ─── cmd_generate ───


class TestCmdGenerate:
    def test_no_content_shows_instructions(self, postforge_root, freeze_today, capsys):
        """With no variants for today, should show instructions."""
        import runner
        runner.cmd_generate(auto_select=False)
        captured = capsys.readouterr()
        assert "No content generated" in captured.out or "intake_agent" in captured.out

    def test_existing_content_shows_scores(self, populated_postforge, freeze_today, capsys):
        import runner
        runner.cmd_generate(auto_select=False)
        captured = capsys.readouterr()
        assert "already generated" in captured.out.lower() or "Variant" in captured.out
