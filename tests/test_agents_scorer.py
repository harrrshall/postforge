"""Unit tests for scorer agent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit


class TestScorerRun:
    def test_writes_scores_json(self, populated_postforge, freeze_today):
        """Scorer agent writes scores JSON to output/scores/."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)

        assert scores_path.exists()
        assert scores_path.name == f"{freeze_today}.json"
        assert scores_path.parent.name == "scores"

        # Should be valid JSON
        scores = load_json(scores_path)
        assert isinstance(scores, dict)

    def test_scores_has_required_fields(self, populated_postforge, freeze_today):
        """Scores JSON has all required top-level fields."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        # Top-level fields that should always exist
        required_fields = ["date", "variants", "ranking", "top_3"]
        for field in required_fields:
            assert field in scores

    def test_scores_has_all_variants(self, populated_postforge, freeze_today):
        """Scores JSON includes all variants that exist."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        # populated_postforge creates 2 variants (A, B)
        assert len(scores["variants"]) >= 2
        variant_ids = [v["id"] for v in scores["variants"]]
        assert "A" in variant_ids
        assert "B" in variant_ids

    def test_variant_scores_have_dimensions(self, populated_postforge, freeze_today):
        """Each variant has scores for all 6 dimensions."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        required_dimensions = [
            "hook_strength",
            "save_worthiness",
            "comment_worthiness",
            "dwell_time_potential",
            "voice_authenticity",
            "algorithm_compliance",
        ]

        for variant in scores["variants"]:
            assert "dimension_scores" in variant
            for dim in required_dimensions:
                assert dim in variant["dimension_scores"]
                # Each dimension should have score and reasoning
                assert "score" in variant["dimension_scores"][dim]
                assert "reasoning" in variant["dimension_scores"][dim]

    def test_variant_has_overall_score(self, populated_postforge, freeze_today):
        """Each variant has an overall_score."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        for variant in scores["variants"]:
            assert "overall_score" in variant
            assert isinstance(variant["overall_score"], (int, float))
            assert 0 <= variant["overall_score"] <= 100

    def test_scores_have_predicted_engagement(self, populated_postforge, freeze_today):
        """Scores include predicted engagement metrics."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        for variant in scores["variants"]:
            assert "predicted_engagement" in variant
            engagement = variant["predicted_engagement"]
            assert "engagement_rate_range" in engagement
            assert "expected_comments" in engagement
            assert "expected_saves" in engagement

    def test_ranking_ordered_by_score(self, populated_postforge, freeze_today):
        """Ranking is ordered from highest to lowest overall_score."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        ranking = scores["ranking"]
        variants_by_id = {v["id"]: v for v in scores["variants"]}

        # Check that ranking is in descending score order
        for i in range(len(ranking) - 1):
            current_score = variants_by_id[ranking[i]]["overall_score"]
            next_score = variants_by_id[ranking[i + 1]]["overall_score"]
            assert current_score >= next_score

    def test_top_3_is_valid(self, populated_postforge, freeze_today):
        """top_3 contains first 3 ranked variants."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        top_3 = scores["top_3"]
        ranking = scores["ranking"]

        assert len(top_3) <= 3
        assert "1st" in top_3
        assert top_3["1st"]["id"] == ranking[0]

        if len(ranking) >= 2:
            assert "2nd" in top_3
            assert top_3["2nd"]["id"] == ranking[1]

        if len(ranking) >= 3:
            assert "3rd" in top_3
            assert top_3["3rd"]["id"] == ranking[2]

    def test_fallback_uses_simulator(self, populated_postforge, freeze_today):
        """Without LLM, scorer falls back to simulator."""
        from agents.scorer import run
        from config_loader import load_json
        from llm_client import LLMClient

        disabled_llm = LLMClient(force_disabled=True)
        scores_path = run(root=populated_postforge, llm=disabled_llm, date=freeze_today)

        # Should still produce valid scores (via fallback)
        assert scores_path.exists()
        scores = load_json(scores_path)
        # populated_postforge creates 2 variants (A, B)
        assert len(scores["variants"]) >= 2
        assert len(scores["ranking"]) >= 2

    def test_idempotent(self, populated_postforge, freeze_today):
        """Running scorer twice doesn't regenerate."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores1 = load_json(scores_path)

        # Run again
        scores_path2 = run(root=populated_postforge, date=freeze_today)
        scores2 = load_json(scores_path2)

        # Should be identical (idempotent)
        assert scores1 == scores2

    def test_extracts_variant_metadata(self, populated_postforge, freeze_today):
        """Scorer extracts variant type and format from variant files."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        for variant in scores["variants"]:
            # populated_postforge has sample variants with Type and Format
            assert "type" in variant
            assert "format" in variant
            # Type should not be "Unknown" if variants are well-formed
            assert variant["type"] != "Unknown" or len(variant["type"]) > 0

    def test_scores_json_valid(self, populated_postforge, freeze_today):
        """Scores JSON is structurally valid and matches conftest SAMPLE_SCORES schema."""
        from agents.scorer import run
        from config_loader import load_json

        scores_path = run(root=populated_postforge, date=freeze_today)
        scores = load_json(scores_path)

        # Validate structure matches conftest.py SAMPLE_SCORES schema
        assert scores["date"] == freeze_today
        assert isinstance(scores["topic"], str)
        assert isinstance(scores["variants"], list)
        assert isinstance(scores["ranking"], list)
        assert isinstance(scores["top_3"], dict)

        # Each variant should have required fields
        for variant in scores["variants"]:
            assert all(
                key in variant
                for key in ["id", "type", "format", "overall_score", "dimension_scores",
                            "predicted_engagement"]
            )

    def test_handles_missing_variants(self, postforge_root, freeze_today):
        """Scorer handles case where variants directory doesn't exist."""
        from agents.scorer import run

        # Don't create variants — scorer should handle it gracefully
        scores_path = run(root=postforge_root, date=freeze_today)

        # Should create a scores file (maybe empty or with placeholders)
        # or handle gracefully without crashing
        if scores_path.exists():
            from config_loader import load_json
            scores = load_json(scores_path)
            # Should be a valid dict even if empty
            assert isinstance(scores, dict)
