"""Unit tests for intake agent."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit


class TestIntakeRun:
    def test_writes_intake_json(self, postforge_root, freeze_today):
        """Intake agent writes structured JSON to output/intakes/."""
        from agents.intake import run
        from config_loader import load_json

        intake_path = run(
            root=postforge_root,
            date=freeze_today,
            topic="AI agents for Indian SMBs",
            goal="saves",
            format_="text"
        )

        assert intake_path.exists()
        assert intake_path.name == f"{freeze_today}.json"

        intake = load_json(intake_path)
        assert intake["date"] == freeze_today
        assert intake["topic"] == "AI agents for Indian SMBs"
        assert intake["goal"]["primary"] == "saves"
        assert intake["format"] == "text"

    def test_topic_stored(self, postforge_root, freeze_today):
        """Topic from CLI args is stored in intake."""
        from agents.intake import run
        from config_loader import load_json

        run(root=postforge_root, date=freeze_today, topic="WhatsApp automation")
        intake = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")
        assert intake["topic"] == "WhatsApp automation"

    def test_goal_defaults_to_saves(self, postforge_root, freeze_today):
        """If goal not specified, defaults to 'saves'."""
        from agents.intake import run
        from config_loader import load_json

        run(root=postforge_root, date=freeze_today, topic="test")
        intake = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")
        assert intake["goal"]["primary"] == "saves"

    def test_format_persisted(self, postforge_root, freeze_today):
        """Format is stored in intake."""
        from agents.intake import run
        from config_loader import load_json

        run(root=postforge_root, date=freeze_today, topic="test", format_="carousel")
        intake = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")
        assert intake["format"] == "carousel"

    def test_idempotent(self, postforge_root, freeze_today):
        """Running intake twice with same date doesn't overwrite."""
        from agents.intake import run
        from config_loader import load_json

        # First call
        run(root=postforge_root, date=freeze_today, topic="First topic")
        intake1 = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")

        # Second call with different topic
        run(root=postforge_root, date=freeze_today, topic="Second topic")
        intake2 = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")

        # Should be unchanged (idempotent)
        assert intake1 == intake2
        assert intake2["topic"] == "First topic"

    def test_pillar_detected_from_goal(self, postforge_root, freeze_today):
        """Pillar is auto-detected from goal."""
        from agents.intake import run, detect_pillar

        # Test goal -> pillar mapping directly
        test_cases = [
            ("saves", "proof"),
            ("comments", "shift"),
            ("velocity", "trend"),
            ("authority", "proof"),
            ("leads", "build"),
        ]

        for goal, expected_pillar in test_cases:
            pillar = detect_pillar(goal)
            assert pillar == expected_pillar

        # Also verify through intake agent
        intake_path = run(root=postforge_root, date=freeze_today, topic="test", goal="saves")
        from config_loader import load_json
        intake = load_json(intake_path)
        assert intake["pipeline_hints"]["pillar"] == "proof"

    def test_works_without_llm(self, postforge_root, freeze_today):
        """Intake agent works with disabled LLM."""
        from agents.intake import run
        from llm_client import LLMClient
        from config_loader import load_json

        disabled_llm = LLMClient(force_disabled=True)
        assert not disabled_llm.available

        intake_path = run(
            root=postforge_root,
            llm=disabled_llm,
            date=freeze_today,
            topic="test",
            goal="comments"
        )

        assert intake_path.exists()
        intake = load_json(intake_path)
        assert intake["goal"]["primary"] == "comments"

    def test_context_stored(self, postforge_root, freeze_today):
        """User-provided context is stored."""
        from agents.intake import run
        from config_loader import load_json

        context = "We just deployed in Mumbai clinic"
        run(root=postforge_root, date=freeze_today, topic="test", context=context)
        intake = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")
        assert intake["context"]["user_provided"] == context

    def test_pipeline_hints_computed(self, postforge_root, freeze_today):
        """Pipeline hints are computed and stored."""
        from agents.intake import run
        from config_loader import load_json

        run(root=postforge_root, date=freeze_today, topic="test", goal="saves")
        intake = load_json(postforge_root / "output" / "intakes" / f"{freeze_today}.json")
        hints = intake["pipeline_hints"]

        assert "variant_emphasis" in hints
        assert "scoring_boost_dimension" in hints
        assert "scoring_boost_multiplier" in hints
        assert hints["scoring_boost_dimension"] == "save_worthiness"
        assert hints["scoring_boost_multiplier"] == 1.20
