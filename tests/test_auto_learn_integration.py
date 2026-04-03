"""Integration tests for AutoLearner — full sprint review with file I/O."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.integration

DIMS = ["hook_strength", "save_worthiness", "comment_worthiness",
        "dwell_time_potential", "voice_authenticity", "algorithm_compliance"]


class TestSprintReviewFullPipeline:
    def test_weights_version_increments(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        weights = config_loader.load_scoring_weights()
        assert weights["version"] == 2

    def test_weights_change_from_input(self, populated_postforge, sample_scoring_weights):
        from auto_learn import AutoLearner
        import config_loader

        old_weights = {d: sample_scoring_weights["dimensions"][d]["weight"] for d in DIMS}

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        new_weights_data = config_loader.load_scoring_weights()
        new_weights = {d: new_weights_data["dimensions"][d]["weight"] for d in DIMS}

        # At least some weights should have changed
        changed = any(abs(new_weights[d] - old_weights[d]) > 0.0001 for d in DIMS)
        assert changed, "No weights changed after sprint review"

    def test_weights_still_sum_to_one(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        weights = config_loader.load_scoring_weights()
        total = sum(weights["dimensions"][d]["weight"] for d in DIMS)
        assert abs(total - 1.0) < 0.001

    def test_sprint_log_gets_new_entry(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        sprint_log = config_loader.load_sprint_log()
        assert len(sprint_log["sprints"]) == 1
        sprint = sprint_log["sprints"][0]
        assert sprint["sprint_number"] == 1
        assert sprint["posts_published"] == 3

    def test_calibration_posts_increments(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        weights = config_loader.load_scoring_weights()
        assert weights["total_calibration_posts"] == 3

    def test_weight_history_grows(self, populated_postforge, sample_scoring_weights):
        from auto_learn import AutoLearner
        import config_loader

        original_history_len = len(sample_scoring_weights["weight_history"])

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        weights = config_loader.load_scoring_weights()
        assert len(weights["weight_history"]) == original_history_len + 1

    def test_underperformed_appends_anti_patterns(self, populated_postforge):
        """The fixture has an UNDERPERFORMED post — anti_patterns.md should grow."""
        from auto_learn import AutoLearner

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        content = (populated_postforge / "memory" / "anti_patterns.md").read_text()
        assert "Anti-Pattern" in content or "UNDERPERFORMED" in content.upper() or "Data-Driven" in content

    def test_too_few_posts_no_changes(self, postforge_root, sample_scoring_weights, freeze_today):
        """With only 1 post, sprint review should not modify anything."""
        from auto_learn import AutoLearner
        import config_loader

        config_loader.save_json(postforge_root / "config" / "scoring_weights.json", sample_scoring_weights)

        history = {
            "posts": [{
                "date_posted": "2026-04-14",
                "dimension_scores_at_time": {d: 50 for d in DIMS},
                "actual_24h": {"engagement_rate": "3%"},
                "outcome": "MATCHED",
                "predicted": {"engagement_rate_range": "3-4%"},
            }],
            "metadata": {},
        }
        config_loader.save_json(postforge_root / "memory" / "performance_history.json", history)
        config_loader.save_json(postforge_root / "memory" / "sprint_log.json",
                                {"sprints": [], "metadata": {"total_sprints": 0, "current_sprint": 0}})

        learner = AutoLearner(root=postforge_root)
        learner.run_sprint_review()  # Should print "not enough" and return

        weights = config_loader.load_scoring_weights()
        assert weights["version"] == 1  # unchanged

    def test_sprint_entry_has_learning_rate(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        sprint_log = config_loader.load_sprint_log()
        sprint = sprint_log["sprints"][0]
        assert "learning_rate_used" in sprint
        assert sprint["learning_rate_used"] == 0.10  # 0 calibration posts → lr=0.10

    def test_sprint_entry_has_prediction_accuracy(self, populated_postforge):
        from auto_learn import AutoLearner
        import config_loader

        learner = AutoLearner(root=populated_postforge)
        posts = learner.get_posts_since_last_sprint()
        learner.run_sprint_review(posts)

        sprint_log = config_loader.load_sprint_log()
        sprint = sprint_log["sprints"][0]
        assert "prediction_accuracy_this_sprint" in sprint
        assert 0 <= sprint["prediction_accuracy_this_sprint"] <= 1
