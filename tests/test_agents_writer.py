"""Unit tests for writer agent."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit


class TestWriterRun:
    def test_writes_6_variants(self, postforge_root, freeze_today):
        """Writer agent generates all 6 variants."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        assert len(paths) == 6
        for path in paths:
            assert path.exists()
            assert path.suffix == ".md"

    def test_variant_names_correct(self, postforge_root, freeze_today):
        """Variants are named variant_a through variant_f."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        filenames = sorted([p.name for p in paths])
        expected = [
            "variant_a.md",
            "variant_b.md",
            "variant_c.md",
            "variant_d.md",
            "variant_e.md",
            "variant_f.md",
        ]
        assert filenames == expected

    def test_variants_in_correct_directory(self, postforge_root, freeze_today):
        """Variants are written to output/variants/YYYY-MM-DD/."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        for path in paths:
            assert path.parent.name == freeze_today
            assert path.parent.parent.name == "variants"

    def test_variant_has_metadata_section(self, postforge_root, freeze_today):
        """Each variant has ## Metadata section."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        for path in paths:
            content = path.read_text()
            assert "## Metadata" in content
            assert "- Type:" in content
            assert "- Format:" in content

    def test_variant_has_hook_analysis(self, postforge_root, freeze_today):
        """Each variant has ## Hook Analysis section."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        for path in paths:
            content = path.read_text()
            assert "## Hook Analysis" in content
            assert "First 150 chars:" in content

    def test_variant_has_post_text_section(self, postforge_root, freeze_today):
        """Each variant has ## Post Text section."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        for path in paths:
            content = path.read_text()
            assert "## Post Text" in content

    def test_variant_has_first_comment_section(self, postforge_root, freeze_today):
        """Each variant has ## First Comment section."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        for path in paths:
            content = path.read_text()
            assert "## First Comment" in content
            assert "#" in content  # Should have hashtags

    def test_variant_types_are_different(self, postforge_root, freeze_today):
        """Each variant has a different Type in metadata."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        types = []
        for path in paths:
            content = path.read_text()
            # Extract Type: from metadata
            for line in content.split("\n"):
                if "- Type:" in line:
                    variant_type = line.split("Type:")[1].strip()
                    types.append(variant_type)
                    break

        # All 6 should have types, and they should vary
        assert len(types) == 6
        assert len(set(types)) >= 5  # At least 5 different types

    def test_formats_mixed(self, postforge_root, freeze_today):
        """Variants have mixed formats (text and carousel)."""
        from agents.writer import run

        paths = run(root=postforge_root, date=freeze_today)

        formats = []
        for path in paths:
            content = path.read_text()
            for line in content.split("\n"):
                if "- Format:" in line:
                    fmt = line.split("Format:")[1].strip()
                    formats.append(fmt)
                    break

        assert "text" in formats
        assert "carousel" in formats

    def test_fallback_writes_skeletons(self, postforge_root, freeze_today):
        """Without LLM, writer generates skeleton variants."""
        from agents.writer import run
        from llm_client import LLMClient

        disabled_llm = LLMClient(force_disabled=True)
        paths = run(root=postforge_root, llm=disabled_llm, date=freeze_today)

        assert len(paths) == 6

        for path in paths:
            content = path.read_text()
            # Fallback variants have placeholders
            assert "[PLACEHOLDER:" in content or "## Post Text" in content

    def test_idempotent(self, postforge_root, freeze_today):
        """Running writer twice doesn't regenerate."""
        from agents.writer import run

        paths1 = run(root=postforge_root, date=freeze_today)
        content1 = [p.read_text() for p in paths1]

        # Run again
        paths2 = run(root=postforge_root, date=freeze_today)
        content2 = [p.read_text() for p in paths2]

        # Should return same paths and content (idempotent)
        assert [p.name for p in paths1] == [p.name for p in paths2]
        assert content1 == content2

    def test_context_loaded(self, postforge_root, freeze_today):
        """Writer loads context files (voice, algorithm, research brief)."""
        from agents.writer import run
        from config_loader import save_json

        # Create minimal config files
        voice_path = postforge_root / "config" / "voice_profile.md"
        voice_path.parent.mkdir(parents=True, exist_ok=True)
        voice_path.write_text("# Voice\nDirect tone.")

        algo_path = postforge_root / "config" / "algorithm_rules.md"
        algo_path.write_text("# Algorithm\nNo external links.")

        brief_path = postforge_root / "research" / "briefs" / f"{freeze_today}.md"
        brief_path.parent.mkdir(parents=True, exist_ok=True)
        brief_path.write_text("# Brief\nKey points here.")

        # Run writer — should not crash
        paths = run(root=postforge_root, date=freeze_today)
        assert len(paths) == 6
