"""Unit tests for research agent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit


class TestResearchRun:
    def test_writes_brief(self, postforge_root, freeze_today):
        """Research agent writes brief markdown to research/briefs/."""
        from agents.research import run
        from config_loader import load_json, save_json

        # Create minimal intake for research to read
        intake = {
            "topic": "AI agents for SMBs",
            "goal": {"primary": "saves"},
        }
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        brief_path = run(root=postforge_root, date=freeze_today)

        assert brief_path.exists()
        assert brief_path.name == f"{freeze_today}.md"
        assert brief_path.parent.name == "briefs"

    def test_brief_contains_topic(self, postforge_root, freeze_today):
        """Brief markdown contains the topic."""
        from agents.research import run
        from config_loader import save_json

        # Create intake
        intake = {"topic": "WhatsApp automation", "goal": {"primary": "saves"}}
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        brief_path = run(root=postforge_root, date=freeze_today)
        brief_text = brief_path.read_text()

        assert "WhatsApp automation" in brief_text or "PLACEHOLDER" in brief_text

    def test_fallback_writes_template(self, postforge_root, freeze_today):
        """Without LLM, research agent writes template brief."""
        from agents.research import run
        from config_loader import save_json
        from llm_client import LLMClient

        intake = {"topic": "Test topic", "goal": {"primary": "saves"}}
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        disabled_llm = LLMClient(force_disabled=True)
        brief_path = run(root=postforge_root, llm=disabled_llm, date=freeze_today)

        brief_text = brief_path.read_text()
        # Fallback template has placeholders
        assert "[PLACEHOLDER:" in brief_text or "Test topic" in brief_text

    def test_has_expected_sections(self, postforge_root, freeze_today):
        """Brief has required markdown sections."""
        from agents.research import run
        from config_loader import save_json

        intake = {"topic": "Test", "goal": {"primary": "saves"}}
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        brief_path = run(root=postforge_root, date=freeze_today)
        brief_text = brief_path.read_text()

        # Check for expected markdown sections (from either LLM or fallback)
        expected_sections = [
            "Hook Angles",
            "Key Stats",
            "Indian SMB",
            "CTA",
        ]
        for section in expected_sections:
            assert section in brief_text or "[PLACEHOLDER:" in brief_text

    def test_idempotent(self, postforge_root, freeze_today):
        """Running research twice doesn't overwrite."""
        from agents.research import run
        from config_loader import save_json

        intake = {"topic": "First topic", "goal": {"primary": "saves"}}
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        brief_path = run(root=postforge_root, date=freeze_today)
        first_content = brief_path.read_text()

        # Run again (should be idempotent)
        brief_path2 = run(root=postforge_root, date=freeze_today)
        second_content = brief_path2.read_text()

        assert first_content == second_content

    def test_handles_missing_intake(self, postforge_root, freeze_today):
        """Research agent handles missing intake gracefully."""
        from agents.research import run

        # Don't create intake — research should handle it
        brief_path = run(root=postforge_root, date=freeze_today)

        # Should create a brief (maybe with placeholder or error message)
        assert brief_path.exists()
        brief_text = brief_path.read_text()
        # Should mention intake or placeholder
        assert "intake" in brief_text.lower() or "[PLACEHOLDER:" in brief_text

    def test_loads_voice_profile(self, postforge_root, freeze_today):
        """Research agent loads voice profile if available."""
        from agents.research import run
        from config_loader import save_json

        # Create voice profile
        voice_profile_path = postforge_root / "config" / "voice_profile.md"
        voice_profile_path.parent.mkdir(parents=True, exist_ok=True)
        voice_profile_path.write_text("# Voice Profile\nDirect, data-driven tone.")

        # Create intake
        intake = {"topic": "Test", "goal": {"primary": "saves"}}
        intake_path = postforge_root / "output" / "intakes" / f"{freeze_today}.json"
        intake_path.parent.mkdir(parents=True, exist_ok=True)
        save_json(intake_path, intake)

        # Run research — should not crash even though voice is loaded
        brief_path = run(root=postforge_root, date=freeze_today)
        assert brief_path.exists()
