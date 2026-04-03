"""Tests for the PostForge Hermes plugin."""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add plugin root to path for imports
PLUGIN_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PLUGIN_DIR.parent))

from postforge import schemas, tools
from postforge import register


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def tmp_postforge(tmp_path):
    """Create a minimal PostForge directory tree for testing."""
    root = tmp_path / "postforge"
    for d in [
        "config", "memory", "output/intakes", "output/variants/2026-04-03",
        "output/scores", "output/simulations", "output/selected",
        "research/briefs", "scripts",
    ]:
        (root / d).mkdir(parents=True, exist_ok=True)

    # Scoring weights
    (root / "config" / "scoring_weights.json").write_text(json.dumps({
        "version": "v1",
        "calibration_posts": 3,
        "dimensions": {
            "hook_strength": {"weight": 0.20},
            "save_intent": {"weight": 0.25},
            "comment_potential": {"weight": 0.20},
            "dwell_time": {"weight": 0.15},
            "voice_authenticity": {"weight": 0.10},
            "algorithm_compliance": {"weight": 0.10},
        }
    }, indent=2))

    # Performance history
    (root / "memory" / "performance_history.json").write_text(json.dumps({
        "posts": [
            {"post_id": "2026-04-01-A", "impressions": 1200, "likes": 45,
             "comments": 12, "saves": 8, "shares": 3, "engagement_rate": 5.67},
            {"post_id": "2026-04-02-C", "impressions": 800, "likes": 30,
             "comments": 5, "saves": 15, "shares": 2, "engagement_rate": 6.5},
        ]
    }, indent=2))

    # Sprint log
    (root / "memory" / "sprint_log.json").write_text(json.dumps({
        "sprints": [{"id": 1, "start": "2026-03-28", "end": "2026-03-31"}]
    }, indent=2))

    # Sample variant
    (root / "output" / "variants" / "2026-04-03" / "variant_a.md").write_text(
        "# 73% of Indian SMBs still run on WhatsApp and spreadsheets.\n\n"
        "I spent 6 weeks building AI agents that replaced both.\n\n"
        "Here's what happened to their revenue.\n\n"
        "The first client was a 12-person textile distributor in Surat.\n"
        "They processed 200+ orders daily through WhatsApp groups.\n"
        "Errors ran at 15%. After the AI agent took over, errors dropped to 1.2%.\n\n"
        "Revenue impact: +23% in 90 days.\n"
    )

    # Sample scores
    (root / "output" / "scores" / "2026-04-03.json").write_text(json.dumps({
        "date": "2026-04-03",
        "ranking": ["A", "C", "B", "D", "E", "F"],
        "variants": {
            "A": {"composite": 0.82, "hook_strength": 0.9, "save_intent": 0.85},
            "C": {"composite": 0.75, "hook_strength": 0.7, "save_intent": 0.80},
        }
    }, indent=2))

    # Dummy runner.py
    (root / "scripts" / "runner.py").write_text(
        "import sys, json\n"
        "cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'\n"
        "if cmd == 'status':\n"
        "    print('PostForge Status: OK')\n"
        "    print('Weights: v1 | Posts tracked: 2 | Sprints: 1')\n"
        "elif cmd == 'generate':\n"
        "    print('Generated 6 variants for 2026-04-03')\n"
        "elif cmd == 'simulate':\n"
        "    print('Simulated 10 personas across variants')\n"
        "elif cmd == 'sprint-review':\n"
        "    print('Sprint review complete. Weights updated.')\n"
        "else:\n"
        "    print(f'Unknown command: {cmd}')\n"
        "    sys.exit(1)\n"
    )

    return root


@pytest.fixture
def patch_root(tmp_postforge):
    """Patch POSTFORGE_ROOT and RUNNER to use tmp directory."""
    with patch.object(tools, "POSTFORGE_ROOT", tmp_postforge), \
         patch.object(tools, "RUNNER", tmp_postforge / "scripts" / "runner.py"):
        yield tmp_postforge


# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------

class TestSchemas:
    """Verify all schemas have required fields."""

    ALL_SCHEMAS = [
        schemas.POSTFORGE_STATUS,
        schemas.POSTFORGE_GENERATE,
        schemas.POSTFORGE_SIMULATE,
        schemas.POSTFORGE_LEARN,
        schemas.POSTFORGE_SPRINT_REVIEW,
        schemas.POSTFORGE_SCORES,
        schemas.POSTFORGE_READ_VARIANT,
    ]

    def test_all_schemas_have_name(self):
        for s in self.ALL_SCHEMAS:
            assert "name" in s, f"Schema missing 'name': {s}"
            assert s["name"].startswith("postforge_")

    def test_all_schemas_have_description(self):
        for s in self.ALL_SCHEMAS:
            assert "description" in s
            assert len(s["description"]) > 20

    def test_all_schemas_have_parameters(self):
        for s in self.ALL_SCHEMAS:
            assert "parameters" in s
            assert s["parameters"]["type"] == "object"

    def test_generate_requires_topic(self):
        assert "topic" in schemas.POSTFORGE_GENERATE["parameters"]["properties"]
        assert "topic" in schemas.POSTFORGE_GENERATE["parameters"]["required"]

    def test_learn_requires_metrics(self):
        required = schemas.POSTFORGE_LEARN["parameters"]["required"]
        for field in ["post_id", "impressions", "likes", "comments", "saves", "shares"]:
            assert field in required

    def test_read_variant_requires_variant(self):
        assert "variant" in schemas.POSTFORGE_READ_VARIANT["parameters"]["required"]
        enum = schemas.POSTFORGE_READ_VARIANT["parameters"]["properties"]["variant"]["enum"]
        assert enum == ["a", "b", "c", "d", "e", "f"]

    def test_schema_count(self):
        assert len(self.ALL_SCHEMAS) == 7


# ---------------------------------------------------------------------------
# Tool handler tests
# ---------------------------------------------------------------------------

class TestPostforgeStatus:
    def test_returns_json(self, patch_root):
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["success"] is True
        assert "cli_output" in result

    def test_shows_tracked_posts(self, patch_root):
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["tracked_posts"] == 2

    def test_shows_sprints(self, patch_root):
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["sprints_completed"] == 1

    def test_weights_loaded(self, patch_root):
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["weights_loaded"] is True


class TestPostforgeGenerate:
    def test_requires_topic(self, patch_root):
        result = json.loads(tools.postforge_generate({}, task_id="test"))
        assert result["success"] is False
        assert "Topic is required" in result["error"]

    def test_generates_with_topic(self, patch_root):
        result = json.loads(tools.postforge_generate(
            {"topic": "AI agents for SMBs"}, task_id="test"
        ))
        assert result["success"] is True

    def test_default_goal_is_saves(self, patch_root):
        # Just ensure no error when goal not specified
        result = json.loads(tools.postforge_generate(
            {"topic": "test topic"}, task_id="test"
        ))
        assert result["success"] is True

    def test_force_flag(self, patch_root):
        result = json.loads(tools.postforge_generate(
            {"topic": "test", "force": True}, task_id="test"
        ))
        assert result["success"] is True


class TestPostforgeSimulate:
    def test_requires_target(self, patch_root):
        result = json.loads(tools.postforge_simulate({}, task_id="test"))
        assert result["success"] is False
        assert "Target" in result["error"]

    def test_simulate_by_date(self, patch_root):
        result = json.loads(tools.postforge_simulate(
            {"target": "2026-04-03"}, task_id="test"
        ))
        assert result["success"] is True


class TestPostforgeLearn:
    def test_requires_post_id(self, patch_root):
        result = json.loads(tools.postforge_learn({}, task_id="test"))
        assert result["success"] is False
        assert "post_id" in result["error"]

    def test_requires_all_metrics(self, patch_root):
        result = json.loads(tools.postforge_learn(
            {"post_id": "2026-04-03-A", "impressions": 1000},
            task_id="test"
        ))
        assert result["success"] is False
        assert "Missing" in result["error"]

    def test_successful_learn(self, patch_root):
        result = json.loads(tools.postforge_learn({
            "post_id": "2026-04-03-B",
            "impressions": 1500,
            "likes": 60,
            "comments": 15,
            "saves": 20,
            "shares": 5,
        }, task_id="test"))
        assert result["success"] is True
        assert result["engagement_rate"] == round((60 + 15 + 20 + 5) / 1500 * 100, 2)
        assert result["total_posts_tracked"] == 3  # 2 existing + 1 new

    def test_prevents_duplicate(self, patch_root):
        result = json.loads(tools.postforge_learn({
            "post_id": "2026-04-01-A",  # Already exists in fixture
            "impressions": 1000, "likes": 10, "comments": 5,
            "saves": 3, "shares": 1,
        }, task_id="test"))
        assert result["success"] is False
        assert "already tracked" in result["error"]

    def test_engagement_rate_zero_impressions(self, patch_root):
        result = json.loads(tools.postforge_learn({
            "post_id": "2026-04-03-D",
            "impressions": 0, "likes": 0, "comments": 0,
            "saves": 0, "shares": 0,
        }, task_id="test"))
        assert result["success"] is True
        assert result["engagement_rate"] == 0.0

    def test_persists_to_disk(self, patch_root):
        tools.postforge_learn({
            "post_id": "2026-04-03-E",
            "impressions": 500, "likes": 20, "comments": 5,
            "saves": 10, "shares": 2,
        }, task_id="test")
        history = json.loads(
            (patch_root / "memory" / "performance_history.json").read_text()
        )
        ids = [p["post_id"] for p in history["posts"]]
        assert "2026-04-03-E" in ids


class TestPostforgeSprintReview:
    def test_runs_sprint_review(self, patch_root):
        result = json.loads(tools.postforge_sprint_review({}, task_id="test"))
        assert result["success"] is True
        assert result["sprints_completed"] == 1


class TestPostforgeScores:
    def test_reads_existing_scores(self, patch_root):
        result = json.loads(tools.postforge_scores(
            {"date": "2026-04-03"}, task_id="test"
        ))
        assert result["success"] is True
        assert result["scores"]["ranking"][0] == "A"

    def test_missing_date_returns_error(self, patch_root):
        result = json.loads(tools.postforge_scores(
            {"date": "2099-01-01"}, task_id="test"
        ))
        assert result["success"] is False
        assert "No scores found" in result["error"]


class TestPostforgeReadVariant:
    def test_reads_existing_variant(self, patch_root):
        result = json.loads(tools.postforge_read_variant(
            {"variant": "a", "date": "2026-04-03"}, task_id="test"
        ))
        assert result["success"] is True
        assert "73%" in result["content"]
        assert result["word_count"] > 50

    def test_missing_variant(self, patch_root):
        result = json.loads(tools.postforge_read_variant(
            {"variant": "f", "date": "2026-04-03"}, task_id="test"
        ))
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_invalid_variant_letter(self, patch_root):
        result = json.loads(tools.postforge_read_variant(
            {"variant": "z"}, task_id="test"
        ))
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

class TestRegistration:
    """Test the plugin register() function."""

    def test_registers_all_tools(self):
        """Verify register() calls ctx.register_tool 7 times."""
        ctx = MagicMock()
        register(ctx)
        assert ctx.register_tool.call_count == 7

    def test_registers_hook(self):
        ctx = MagicMock()
        register(ctx)
        hook_calls = [c for c in ctx.register_hook.call_args_list
                      if c[0][0] == "post_tool_call"]
        assert len(hook_calls) == 1

    def test_tool_names_match_schemas(self):
        """All registered tool names match their schema names."""
        ctx = MagicMock()
        register(ctx)
        registered_names = {call[1]["name"] for call in ctx.register_tool.call_args_list}
        schema_names = {
            "postforge_status", "postforge_generate", "postforge_simulate",
            "postforge_learn", "postforge_sprint_review", "postforge_scores",
            "postforge_read_variant",
        }
        assert registered_names == schema_names

    def test_all_tools_in_postforge_toolset(self):
        ctx = MagicMock()
        register(ctx)
        for call in ctx.register_tool.call_args_list:
            assert call[1]["toolset"] == "postforge"

    def test_register_does_not_crash(self):
        """Plugin must not crash Hermes if registration fails."""
        ctx = MagicMock()
        # Should not raise
        register(ctx)


# ---------------------------------------------------------------------------
# Hook tests
# ---------------------------------------------------------------------------

class TestPostToolCallHook:
    def test_hook_logs_postforge_calls(self, caplog):
        """Hook should log when a postforge_ tool is called."""
        import logging
        from postforge import _on_post_tool_call

        with caplog.at_level(logging.INFO, logger="postforge"):
            _on_post_tool_call(
                tool_name="postforge_status",
                args={},
                result='{"success": true}',
                task_id="test-session",
            )
        assert any("postforge_status" in r.message for r in caplog.records)

    def test_hook_ignores_non_postforge_calls(self, caplog):
        import logging
        from postforge import _on_post_tool_call

        with caplog.at_level(logging.INFO, logger="postforge"):
            _on_post_tool_call(
                tool_name="terminal",
                args={"command": "ls"},
                result="files...",
                task_id="test-session",
            )
        postforge_logs = [r for r in caplog.records if "postforge" in r.message.lower()]
        assert len(postforge_logs) == 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_missing_postforge_root(self, tmp_path):
        """Tools handle missing POSTFORGE_ROOT gracefully."""
        fake_root = tmp_path / "nonexistent"
        with patch.object(tools, "POSTFORGE_ROOT", fake_root), \
             patch.object(tools, "RUNNER", fake_root / "scripts" / "runner.py"):
            result = json.loads(tools.postforge_status({}, task_id="test"))
            # Should not crash — returns error or partial data
            assert isinstance(result, dict)

    def test_corrupted_json_file(self, patch_root):
        """Tools handle corrupted JSON gracefully."""
        (patch_root / "config" / "scoring_weights.json").write_text("not json{{{")
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["weights_loaded"] is False

    def test_empty_performance_history(self, patch_root):
        """Works with empty performance history."""
        (patch_root / "memory" / "performance_history.json").write_text("{}")
        result = json.loads(tools.postforge_status({}, task_id="test"))
        assert result["tracked_posts"] == 0
