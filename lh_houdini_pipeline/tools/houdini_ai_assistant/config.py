"""
lh_houdini_pipeline.tools.houdini_ai_assistant.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Configuration helper for the Houdini AI Assistant.
Integrates with the main pipeline's config system and handles saving user preferences.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from lh_houdini_pipeline.core.config import Config, ConfigManager, ConfigLoader
from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)

# Default config dictionary
DEFAULT_CONFIG = {
    "active_provider": "anthropic",
    "providers": {
        "anthropic": {
            "api_key": "",
            "api_key_env": "ANTHROPIC_API_KEY",
            "models": ["claude-opus-4-8", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
            "active_model": "claude-sonnet-4-6",
            "url": "https://api.anthropic.com/v1/messages"
        },
        "openai": {
            "api_key": "",
            "api_key_env": "OPENAI_API_KEY",
            "models": ["gpt-5.5", "gpt-5", "gpt-5-mini", "gpt-4.1"],
            "active_model": "gpt-5.5",
            "url": "https://api.openai.com/v1/chat/completions"
        },
        "gemini": {
            "api_key": "",
            "api_key_env": "GEMINI_API_KEY",
            "models": ["gemini-3.1-pro", "gemini-3.5-flash", "gemini-2.5-pro", "gemini-2.5-flash"],
            "active_model": "gemini-3.5-flash",
            "url": "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        },
        "xai": {
            "api_key": "",
            "api_key_env": "XAI_API_KEY",
            "models": ["grok-4.3", "grok-4", "grok-3"],
            "active_model": "grok-4.3",
            "url": "https://api.x.ai/v1/chat/completions"
        },
        "openrouter": {
            "api_key": "",
            "api_key_env": "OPENROUTER_API_KEY",
            "models": [
                "anthropic/claude-opus-4.6",
                "anthropic/claude-sonnet-4.6",
                "openai/gpt-5.5",
                "google/gemini-3.1-pro",
                "google/gemini-3.5-flash",
                "google/gemma-4-31b-it:free",
                "x-ai/grok-4.3",
                "deepseek/deepseek-v4-flash",
                "deepseek/deepseek-v4-pro",
                "nvidia/nemotron-3-ultra-550b-a55b:free"
            ],
            "active_model": "anthropic/claude-sonnet-4.6",
            "url": "https://openrouter.ai/api/v1/chat/completions"
        },
        "ollama": {
            "api_key": "ollama",  # dummy key
            "api_key_env": "",
            "models": ["llama3.3", "qwen2.5-coder", "deepseek-r1", "mistral"],
            "active_model": "qwen2.5-coder",
            "url": "http://localhost:11434/v1/chat/completions"
        },
        "lm_studio": {
            "api_key": "lm-studio",  # dummy key
            "api_key_env": "",
            "models": ["local-model"],
            "active_model": "local-model",
            "url": "http://localhost:1234/v1/chat/completions"
        }
    },
    "temperature": 0.2,
    "max_tokens": 4096,
    "max_agent_steps": 12,
    "native_tools": True,
    "use_mcp": False,
    "mcp_server_url": "http://localhost:8000"
}


class AssistantConfigManager:
    """Manages AI Assistant settings, keys, and provider configurations."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        if config_dir is None:
            self._config_dir = Path.home() / ".lh_pipeline"
        else:
            self._config_dir = Path(config_dir)
        
        self._config_file = self._config_dir / "ai_assistant.json"
        self._manager = ConfigManager(apply_env=True)
        self._current_config = Config(DEFAULT_CONFIG)
        self.load()

    def load(self) -> Config:
        """Load defaults, merge user overrides, then refresh the provider catalog.

        The provider *catalog* (``models`` + ``url`` + ``api_key_env``) is
        app-managed and always taken from :data:`DEFAULT_CONFIG`, so updating
        the bundled model lists reaches existing users whose saved file would
        otherwise pin a stale ``models`` array (deep-merge replaces lists).
        User-owned data (``api_key``, ``active_model``, ``active_provider``,
        ``temperature`` ...) from the saved file is preserved.
        """
        import copy

        # 1. Start with hardcoded defaults
        cfg = Config(DEFAULT_CONFIG)

        # 2. Merge user overrides from ~/.lh_pipeline/ai_assistant.json
        if self._config_file.exists():
            try:
                user_cfg = ConfigLoader.load(self._config_file)
                cfg = cfg.merged_with(user_cfg)
            except Exception as e:
                _log.warning(f"Failed to load user config from {self._config_file}: {e}")

        # 3. Re-assert the app-managed provider catalog over the user file.
        catalog = {"providers": {}}
        for prov, pdata in DEFAULT_CONFIG["providers"].items():
            catalog["providers"][prov] = {
                "models": list(pdata["models"]),
                "url": pdata["url"],
                "api_key_env": pdata.get("api_key_env", ""),
            }
        cfg = cfg.merged_with(catalog)

        # 4. Heal any active_model that no longer exists in the refreshed list.
        data = copy.deepcopy(cfg.as_dict())
        for prov, pdata in data.get("providers", {}).items():
            models = pdata.get("models", [])
            if models and pdata.get("active_model") not in models:
                default_am = DEFAULT_CONFIG["providers"].get(prov, {}).get("active_model", models[0])
                pdata["active_model"] = default_am if default_am in models else models[0]
        cfg = Config(data)

        self._current_config = cfg
        return cfg

    def save(self, data: Optional[Dict[str, Any]] = None) -> None:
        """Save user overrides back to JSON config file."""
        if data:
            self._current_config = self._current_config.merged_with(data)

        # Ensure dir exists
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(self._current_config.as_dict(), f, indent=4)
            _log.info(f"Saved AI Assistant configuration to {self._config_file}")
        except Exception as e:
            _log.error(f"Failed to save AI Assistant configuration: {e}")

    @property
    def config(self) -> Config:
        """Get the active Config object."""
        return self._current_config

    def get_api_key(self, provider: str) -> str:
        """Resolve API key for *provider*, checking config then environment variables."""
        p_cfg = self._current_config.get(f"providers.{provider}")
        if not p_cfg:
            return ""

        # Check explicitly set key in config
        key = p_cfg.get("api_key", "")
        if key:
            return key

        # Fallback to env var
        env_var = p_cfg.get("api_key_env", "")
        if env_var:
            return os.environ.get(env_var, "")

        return ""

    def get_active_provider(self) -> str:
        """Return the active provider name."""
        return self._current_config.get("active_provider", "anthropic")

    def get_active_model(self) -> str:
        """Return the active model for the active provider."""
        provider = self.get_active_provider()
        return self._current_config.get(f"providers.{provider}.active_model", "")

    def get_active_url(self) -> str:
        """Return the API endpoint URL for the active provider."""
        provider = self.get_active_provider()
        return self._current_config.get(f"providers.{provider}.url", "")
