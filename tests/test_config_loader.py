"""Unit tests for config_loader.py — all file I/O primitives."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import config_loader


pytestmark = pytest.mark.unit


# ─── get_postforge_root ───


class TestGetPostforgeRoot:
    def test_returns_path(self):
        result = config_loader.get_postforge_root()
        assert isinstance(result, Path)

    def test_parent_of_scripts(self):
        result = config_loader.get_postforge_root()
        assert (result / "scripts").is_dir()


# ─── load_json ───


class TestLoadJson:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"key": "value", "num": 42}')
        result = config_loader.load_json(f)
        assert result == {"key": "value", "num": 42}

    def test_missing_file(self, tmp_path):
        result = config_loader.load_json(tmp_path / "nonexistent.json")
        assert result == {}

    def test_malformed_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid json content")
        result = config_loader.load_json(f)
        assert result == {}

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.json"
        f.write_text("")
        result = config_loader.load_json(f)
        assert result == {}

    def test_nested_structure(self, tmp_path):
        data = {"a": {"b": [1, 2, 3]}, "c": None}
        f = tmp_path / "nested.json"
        f.write_text(json.dumps(data))
        assert config_loader.load_json(f) == data

    def test_unicode_content(self, tmp_path):
        data = {"price": "₹4,999", "city": "मुंबई"}
        f = tmp_path / "unicode.json"
        f.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        assert config_loader.load_json(f) == data


# ─── save_json ───


class TestSaveJson:
    def test_basic_write(self, tmp_path):
        f = tmp_path / "out.json"
        config_loader.save_json(f, {"hello": "world"})
        assert json.loads(f.read_text()) == {"hello": "world"}

    def test_creates_parent_dirs(self, tmp_path):
        f = tmp_path / "deep" / "nested" / "dir" / "out.json"
        config_loader.save_json(f, {"created": True})
        assert f.exists()
        assert json.loads(f.read_text()) == {"created": True}

    def test_overwrites_existing(self, tmp_path):
        f = tmp_path / "overwrite.json"
        config_loader.save_json(f, {"v": 1})
        config_loader.save_json(f, {"v": 2})
        assert json.loads(f.read_text()) == {"v": 2}

    def test_round_trip(self, tmp_path):
        data = {"dims": {"hook": 0.25}, "list": [1, 2, 3], "unicode": "₹"}
        f = tmp_path / "roundtrip.json"
        config_loader.save_json(f, data)
        assert config_loader.load_json(f) == data

    def test_preserves_unicode(self, tmp_path):
        f = tmp_path / "uni.json"
        config_loader.save_json(f, {"text": "₹4,999"})
        raw = f.read_text(encoding="utf-8")
        assert "₹" in raw  # ensure_ascii=False


# ─── load_md ───


class TestLoadMd:
    def test_existing_file(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Hello\nContent here")
        assert config_loader.load_md(f) == "# Hello\nContent here"

    def test_missing_file(self, tmp_path):
        assert config_loader.load_md(tmp_path / "missing.md") == ""

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.md"
        f.write_text("")
        assert config_loader.load_md(f) == ""


# ─── append_md ───


class TestAppendMd:
    def test_append_to_existing(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("# Header")
        config_loader.append_md(f, "New content")
        content = f.read_text()
        assert "# Header" in content
        assert "New content" in content

    def test_creates_file_if_missing(self, tmp_path):
        f = tmp_path / "new.md"
        config_loader.append_md(f, "First content")
        assert f.exists()
        assert "First content" in f.read_text()

    def test_creates_parent_dirs(self, tmp_path):
        f = tmp_path / "deep" / "dir" / "new.md"
        config_loader.append_md(f, "Content")
        assert f.exists()

    def test_prepends_newline(self, tmp_path):
        f = tmp_path / "doc.md"
        f.write_text("Line1")
        config_loader.append_md(f, "Line2")
        content = f.read_text()
        assert content == "Line1\nLine2"


# ─── ensure_dirs ───


class TestEnsureDirs:
    def test_creates_all_dirs(self, postforge_root):
        # postforge_root fixture already creates dirs, but test via ensure_dirs
        config_loader.ensure_dirs()
        root = config_loader.get_postforge_root()
        expected = [
            "config", "config/voice_samples", "memory",
            "research/scan", "research/briefs",
            "output/variants", "output/scores", "output/selected",
            "output/intakes", "output/simulations",
            "logs", "tests",
        ]
        for d in expected:
            assert (root / d).is_dir(), f"Missing dir: {d}"

    def test_idempotent(self, postforge_root):
        config_loader.ensure_dirs()
        config_loader.ensure_dirs()  # should not raise


# ─── Convenience Loaders ───


class TestConvenienceLoaders:
    def test_load_performance_history_empty(self, postforge_root):
        result = config_loader.load_performance_history()
        assert result == {}

    def test_load_performance_history_with_data(self, postforge_root, sample_performance_history):
        path = postforge_root / "memory" / "performance_history.json"
        path.write_text(json.dumps(sample_performance_history))
        result = config_loader.load_performance_history()
        assert result["metadata"]["total_posts_tracked"] == 3

    def test_load_scoring_weights_empty(self, postforge_root):
        assert config_loader.load_scoring_weights() == {}

    def test_load_scoring_weights_with_data(self, postforge_root, sample_scoring_weights):
        path = postforge_root / "config" / "scoring_weights.json"
        path.write_text(json.dumps(sample_scoring_weights))
        result = config_loader.load_scoring_weights()
        assert result["version"] == 1
        assert len(result["dimensions"]) == 6

    def test_load_sprint_log_empty(self, postforge_root):
        assert config_loader.load_sprint_log() == {}

    def test_load_intake_with_date(self, postforge_root):
        intake = {"topic": "AI agents", "date": "2026-04-15"}
        path = postforge_root / "output" / "intakes" / "2026-04-15.json"
        path.write_text(json.dumps(intake))
        result = config_loader.load_intake("2026-04-15")
        assert result["topic"] == "AI agents"

    def test_load_intake_missing(self, postforge_root):
        assert config_loader.load_intake("2099-01-01") == {}

    def test_load_scores_with_date(self, postforge_root):
        scores = {"date": "2026-04-15", "variants": []}
        path = postforge_root / "output" / "scores" / "2026-04-15.json"
        path.write_text(json.dumps(scores))
        result = config_loader.load_scores("2026-04-15")
        assert result["date"] == "2026-04-15"


# ─── count_tracked_posts ───


class TestCountTrackedPosts:
    def test_zero_when_empty(self, postforge_root):
        assert config_loader.count_tracked_posts() == 0

    def test_correct_count(self, postforge_root, sample_performance_history):
        path = postforge_root / "memory" / "performance_history.json"
        path.write_text(json.dumps(sample_performance_history))
        assert config_loader.count_tracked_posts() == 3


# ─── get_last_sprint_date ───


class TestGetLastSprintDate:
    def test_none_when_no_sprints(self, postforge_root):
        assert config_loader.get_last_sprint_date() is None

    def test_none_when_empty_sprint_log(self, postforge_root, sample_sprint_log_empty):
        path = postforge_root / "memory" / "sprint_log.json"
        path.write_text(json.dumps(sample_sprint_log_empty))
        assert config_loader.get_last_sprint_date() is None

    def test_returns_end_date(self, postforge_root, sample_sprint_log_with_one):
        path = postforge_root / "memory" / "sprint_log.json"
        path.write_text(json.dumps(sample_sprint_log_with_one))
        result = config_loader.get_last_sprint_date()
        assert result == "2026-04-03"

    def test_parses_date_range(self, postforge_root):
        log = {
            "sprints": [{"dates": "2026-04-01 to 2026-04-05"}],
            "metadata": {},
        }
        path = postforge_root / "memory" / "sprint_log.json"
        path.write_text(json.dumps(log))
        assert config_loader.get_last_sprint_date() == "2026-04-05"
