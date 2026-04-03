"""Unit tests for llm_client.py — provider-agnostic LLM abstraction."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

pytestmark = pytest.mark.unit


class TestLLMClientDisabled:
    def test_force_disabled(self, postforge_root):
        from llm_client import LLMClient
        client = LLMClient(force_disabled=True)
        assert client.available is False

    def test_complete_returns_none_when_disabled(self, postforge_root):
        from llm_client import LLMClient
        client = LLMClient(force_disabled=True)
        assert client.complete("fast", "test prompt") is None

    def test_provider_name_none_when_disabled(self, postforge_root):
        from llm_client import LLMClient
        client = LLMClient(force_disabled=True)
        assert client.provider_name is None


class TestLLMClientNoApiKey:
    def test_unavailable_without_api_key(self, postforge_root, monkeypatch):
        """Without API key in env, client should be unavailable."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)

        from llm_client import LLMClient
        client = LLMClient()
        assert client.available is False

    def test_complete_returns_none_without_key(self, postforge_root, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from llm_client import LLMClient
        client = LLMClient()
        assert client.complete("fast", "hello") is None


class TestLLMClientProviderResolution:
    def test_reads_default_provider(self, postforge_root, monkeypatch):
        """Should resolve provider from config's default_provider field."""
        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from llm_client import LLMClient
        client = LLMClient()
        # Provider name should be set even if API key is missing
        assert client.provider_name == "anthropic"

    def test_env_override_provider(self, postforge_root, monkeypatch):
        """LLM_PROVIDER env var should override config default."""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Write provider.json with openai config
        provider_config = {
            "default_provider": "anthropic",
            "providers": {
                "anthropic": {"sdk": "anthropic", "api_key_env": "ANTHROPIC_API_KEY",
                              "models": {"fast": "test"}},
                "openai": {"sdk": "openai", "api_key_env": "OPENAI_API_KEY",
                           "models": {"fast": "gpt-test"}},
            },
        }
        import config_loader
        config_loader.save_json(postforge_root / "config" / "provider.json", provider_config)

        from llm_client import LLMClient
        client = LLMClient()
        assert client.provider_name == "openai"

    def test_unknown_provider_unavailable(self, postforge_root, monkeypatch):
        """An unknown provider name should result in unavailable."""
        monkeypatch.setenv("LLM_PROVIDER", "nonexistent_provider")

        from llm_client import LLMClient
        client = LLMClient()
        assert client.available is False


class TestLLMClientTierMapping:
    def test_models_loaded_from_config(self, postforge_root, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from llm_client import LLMClient
        client = LLMClient()
        assert "fast" in client.models
        assert "reasoning" in client.models
        assert "writing" in client.models


class TestLLMClientNoConfig:
    def test_missing_provider_json(self, tmp_path, monkeypatch):
        """Without provider.json, client should be unavailable."""
        # Create empty dir structure without provider.json
        (tmp_path / "config").mkdir()

        import config_loader
        monkeypatch.setattr(config_loader, "get_postforge_root", lambda: tmp_path)

        # Also patch llm_client's reference
        try:
            import llm_client as llm_mod
            if hasattr(llm_mod, "load_provider_config"):
                original = llm_mod.load_provider_config
                monkeypatch.setattr(llm_mod, "load_provider_config", config_loader.load_provider_config)
        except ImportError:
            pass

        from llm_client import LLMClient
        client = LLMClient()
        assert client.available is False


class TestLLMClientGracefulDegradation:
    def test_no_crash_on_any_input(self, postforge_root, monkeypatch):
        """LLMClient should never crash during construction."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("LLM_API_KEY", raising=False)
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        from llm_client import LLMClient
        # Should not raise
        client = LLMClient()
        assert isinstance(client.available, bool)

    def test_complete_with_invalid_tier(self, postforge_root):
        from llm_client import LLMClient
        client = LLMClient(force_disabled=True)
        assert client.complete("nonexistent_tier", "prompt") is None
