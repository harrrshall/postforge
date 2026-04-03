#!/usr/bin/env python3
"""
PostForge LLM Client — Provider-agnostic LLM abstraction.

Supports Anthropic, OpenAI, and any OpenAI-compatible API.
Reads config/provider.json for model mappings.
Falls back gracefully if no SDK or API key is available.
"""

import os
import re
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config_loader import load_provider_config


class LLMClient:
    """Provider-agnostic LLM client. Never raises — degrades to unavailable."""

    def __init__(self, force_disabled: bool = False):
        self.available = False
        self.provider_name = None
        self.provider_config = None
        self.models = {}
        self._client = None
        self._sdk_type = None  # "anthropic" or "openai"

        if force_disabled:
            return

        config = load_provider_config()
        if not config or "providers" not in config:
            return

        # Resolve provider: env var override or default
        provider_name = os.environ.get("LLM_PROVIDER", config.get("default_provider", ""))
        if provider_name not in config["providers"]:
            return

        provider = config["providers"][provider_name]
        self.provider_name = provider_name
        self.provider_config = provider
        self.models = provider.get("models", {})

        # Check API key
        api_key_env = provider.get("api_key_env", "")
        api_key = os.environ.get(api_key_env, "") if api_key_env else ""
        if not api_key:
            return

        # Import and initialize SDK
        sdk = provider.get("sdk", provider_name)
        try:
            if sdk == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(api_key=api_key)
                self._sdk_type = "anthropic"
                self.available = True
            elif sdk == "openai":
                import openai
                kwargs = {"api_key": api_key}
                base_url_env = provider.get("base_url_env", "")
                if base_url_env:
                    base_url = os.environ.get(base_url_env, "")
                    if base_url:
                        kwargs["base_url"] = base_url
                self._client = openai.OpenAI(**kwargs)
                self._sdk_type = "openai"
                self.available = True
        except (ImportError, Exception):
            pass

    def complete(self, tier: str, prompt: str, max_tokens: int = 300) -> str | None:
        """Send a completion request. Returns response text or None."""
        if not self.available or not self._client:
            return None

        model = self.models.get(tier, self.models.get("fast", ""))
        if not model:
            return None

        try:
            if self._sdk_type == "anthropic":
                response = self._client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.content[0].text.strip()

            elif self._sdk_type == "openai":
                response = self._client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content.strip()

        except Exception:
            return None

        return None
