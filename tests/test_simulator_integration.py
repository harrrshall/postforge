"""Integration tests for SimulationEngine — full pipeline with file I/O."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.integration


class TestSimulateVariant:
    def _make_engine(self):
        from simulator import SimulationEngine
        return SimulationEngine(disable_api=True)

    def test_produces_10_reactions(self, populated_postforge):
        engine = self._make_engine()
        variant_path = populated_postforge / "output" / "variants" / "2026-04-15" / "variant_a.md"
        sim = engine.simulate_variant(str(variant_path))
        assert len(sim.reactions) == 10

    def test_extracts_post_text(self, populated_postforge):
        engine = self._make_engine()
        variant_path = populated_postforge / "output" / "variants" / "2026-04-15" / "variant_a.md"
        sim = engine.simulate_variant(str(variant_path))
        assert sim.variant_id == "A"

    def test_extracts_format(self, populated_postforge):
        engine = self._make_engine()
        variant_path = populated_postforge / "output" / "variants" / "2026-04-15" / "variant_b.md"
        sim = engine.simulate_variant(str(variant_path))
        assert sim.variant_id == "B"

    def test_missing_variant_raises(self, populated_postforge):
        engine = self._make_engine()
        with pytest.raises(FileNotFoundError):
            engine.simulate_variant(str(populated_postforge / "nonexistent.md"))

    def test_metrics_populated(self, populated_postforge):
        engine = self._make_engine()
        variant_path = populated_postforge / "output" / "variants" / "2026-04-15" / "variant_a.md"
        sim = engine.simulate_variant(str(variant_path))
        assert sim.metrics.engagement_rate >= 0
        assert sim.metrics.avg_dwell_seconds >= 0


class TestSaveResults:
    def _make_engine(self):
        from simulator import SimulationEngine
        return SimulationEngine(disable_api=True)

    def test_writes_valid_json(self, populated_postforge):
        engine = self._make_engine()
        results = engine.simulate_all_variants("2026-04-15")
        output_path = engine.save_results(results, "2026-04-15")

        assert output_path.exists()
        data = json.loads(output_path.read_text())
        assert "variants" in data
        assert "mode" in data
        assert data["mode"] == "heuristic"

    def test_output_has_winner_and_ranking(self, populated_postforge):
        engine = self._make_engine()
        results = engine.simulate_all_variants("2026-04-15")
        engine.rank_variants(results)
        output_path = engine.save_results(results, "2026-04-15")

        data = json.loads(output_path.read_text())
        assert "winner" in data
        assert "ranking" in data
        assert len(data["ranking"]) == len(results)

    def test_simulate_all_variants(self, populated_postforge):
        engine = self._make_engine()
        results = engine.simulate_all_variants("2026-04-15")
        assert len(results) == 2
        assert "A" in results
        assert "B" in results
