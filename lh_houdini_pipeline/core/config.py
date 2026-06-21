"""
lh_houdini_pipeline.core.config
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Layered, deep-merging configuration system.

Priority (lowest → highest):
    1. Pipeline defaults  -- shipped with the package
    2. Project config     -- per-project YAML / JSON
    3. User config        -- ``~/.lh_pipeline/config.yaml``
    4. Environment vars   -- ``LH_PIPELINE_<SECTION>_<KEY>=value``

Design
------
* ``Config``        -- immutable dot-access wrapper around a plain dict.
  Modification always returns a *new* Config (safe to share across threads).
* ``ConfigLoader``  -- loads YAML or JSON files; deep-merges multiple layers.
  YAML preferred but optional (``pyyaml``); falls back to JSON automatically.
* ``ConfigManager`` -- named registry of Config objects + automatic
  ``LH_PIPELINE_*`` environment-variable overlay.

Pure Python -- no ``hou`` imports.

Example
-------
::

    from lh_houdini_pipeline.core.config import ConfigManager

    mgr = ConfigManager()
    mgr.load("pipeline", "/pipeline/defaults.yaml")
    mgr.load("project",  "/jobs/darkStar/config.yaml", required=False)

    cfg = mgr.get("project")
    cfg.project.fps          # 24
    cfg.get("render.engine") # "karma"
    cfg.require("project.name")  # raises ConfigError if missing
"""

from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class ConfigError(Exception):
    """Raised for config loading, parsing, or validation failures."""


# ---------------------------------------------------------------------------
# Internal sentinel
# ---------------------------------------------------------------------------

class _MissingType:
    """Sentinel distinguishing 'not found' from ``None`` values in config."""
    _instance: Optional["_MissingType"] = None

    def __new__(cls) -> "_MissingType":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "<MISSING>"


_MISSING = _MissingType()


# ---------------------------------------------------------------------------
# Deep-merge helper
# ---------------------------------------------------------------------------

def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge *override* into a copy of *base*.

    * Dict values are merged recursively; *override* wins on leaf conflicts.
    * Lists are **replaced** (not appended) -- simpler and more predictable.
    * Both inputs are left unmodified.

    Args:
        base:     The lower-priority source.
        override: The higher-priority source.

    Returns:
        A new dict containing the merged result.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

class Config:
    """Immutable dict-like configuration object with dot-notation access.

    Nested dicts are accessible via chained attribute access or a dotted key
    string::

        cfg = Config({"project": {"name": "darkStar", "fps": 24}})
        cfg.project.name       # "darkStar"
        cfg["project.fps"]     # 24
        cfg.get("render.engine", "karma")  # "karma" if not set

    Mutation raises ``TypeError``.  Use :py:meth:`merged_with` to produce a
    modified copy.

    Args:
        data: Flat or nested dict of configuration values.  ``None`` is treated
              as an empty config.
    """

    def __init__(self, data: Optional[Dict[str, Any]] = None) -> None:
        # Deep copy at construction so callers cannot mutate our internals.
        object.__setattr__(self, "_data", copy.deepcopy(data or {}))

    # ------------------------------------------------------------------
    # Internal navigation
    # ------------------------------------------------------------------

    def _get_nested(
        self,
        key: str,
        data: Dict[str, Any],
    ) -> Any:
        """Navigate a dotted-key path through nested dicts.

        Returns ``_MISSING`` if any segment is absent.
        """
        head, _, tail = key.partition(".")
        value = data.get(head, _MISSING)
        if value is _MISSING:
            return _MISSING
        if tail:
            if isinstance(value, dict):
                return self._get_nested(tail, value)
            return _MISSING
        return value

    # ------------------------------------------------------------------
    # Access
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value at dotted *key*, or *default* if absent.

        Nested dicts are wrapped in a child :class:`Config` automatically.

        Args:
            key:     Dot-separated key path, e.g. ``"project.fps"``.
            default: Returned when the key is missing.

        Examples:
            >>> cfg = Config({"project": {"fps": 24}})
            >>> cfg.get("project.fps")
            24
            >>> cfg.get("project.missing", 48)
            48
        """
        result = self._get_nested(key, self._data)
        if result is _MISSING:
            return default
        if isinstance(result, dict):
            return Config(result)
        return result

    def require(self, key: str) -> Any:
        """Like :py:meth:`get` but raises :exc:`ConfigError` if the key is absent.

        Use this for mandatory pipeline settings where a missing value should
        crash loudly rather than silently returning ``None``.

        Args:
            key: Dot-separated key path.

        Raises:
            ConfigError: If *key* is not present in the config.
        """
        result = self._get_nested(key, self._data)
        if result is _MISSING:
            raise ConfigError(
                f"Required configuration key is missing: '{key}'. "
                f"Top-level keys available: {sorted(self._data.keys())}."
            )
        if isinstance(result, dict):
            return Config(result)
        return result

    def as_dict(self) -> Dict[str, Any]:
        """Return a deep copy of the underlying plain dict."""
        return copy.deepcopy(self._data)

    def keys(self) -> List[str]:
        """Top-level keys (not recursive)."""
        return list(self._data.keys())

    def merged_with(
        self, other: Union["Config", Dict[str, Any]]
    ) -> "Config":
        """Return a new Config that is *self* deep-merged with *other*.

        *other* takes priority on all conflicts.  Neither *self* nor *other*
        is modified.

        Args:
            other: A :class:`Config` or plain dict to merge on top of *self*.

        Returns:
            A new :class:`Config` with the merged values.
        """
        other_dict = other.as_dict() if isinstance(other, Config) else other
        return Config(_deep_merge(self.as_dict(), other_dict))

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        value = self.get(name, _MISSING)
        if value is _MISSING:
            raise AttributeError(
                f"Config has no attribute '{name}'. "
                f"Available top-level keys: {self.keys()}."
            )
        return value

    def __setattr__(self, name: str, value: Any) -> None:
        raise TypeError(
            "Config is immutable. "
            "Use cfg.merged_with({'key': value}) to create a modified copy."
        )

    def __getitem__(self, key: str) -> Any:
        result = self.get(key, _MISSING)
        if result is _MISSING:
            raise KeyError(key)
        return result

    def __contains__(self, key: str) -> bool:
        return self._get_nested(key, self._data) is not _MISSING

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __bool__(self) -> bool:
        return bool(self._data)

    def __repr__(self) -> str:
        return f"Config(keys={self.keys()})"


# ---------------------------------------------------------------------------
# ConfigLoader
# ---------------------------------------------------------------------------

class ConfigLoader:
    """Loads YAML or JSON config files and produces :class:`Config` objects.

    YAML is preferred (more human-friendly for pipeline TDs and artists).
    ``pyyaml`` is a soft dependency -- a clear :exc:`ConfigError` is raised
    if a ``.yaml`` file is requested and the library is not installed.

    All methods are static; :class:`ConfigLoader` is a namespace rather than
    a stateful object.
    """

    @staticmethod
    def load(path: Union[str, Path]) -> "Config":
        """Load a single YAML or JSON file and return a :class:`Config`.

        The file format is determined by the file extension (``.yaml``,
        ``.yml``, or ``.json``).  Files with other extensions are tried as
        YAML first, then JSON.

        Args:
            path: Path to the configuration file.

        Returns:
            A :class:`Config` populated with the file's contents.

        Raises:
            ConfigError: File not found, unreadable, or unparseable.
        """
        p = Path(path)
        if not p.exists():
            raise ConfigError(f"Config file not found: '{p}'")
        if not p.is_file():
            raise ConfigError(f"Config path is not a file: '{p}'")

        try:
            raw = p.read_text(encoding="utf-8")
        except OSError as exc:
            raise ConfigError(f"Cannot read config file '{p}': {exc}") from exc

        suffix = p.suffix.lower()

        if suffix in {".yaml", ".yml"}:
            return Config(ConfigLoader._parse_yaml(raw, p))
        if suffix == ".json":
            return Config(ConfigLoader._parse_json(raw, p))

        # Unknown extension: try YAML, fall back to JSON.
        for parser in (ConfigLoader._parse_yaml, ConfigLoader._parse_json):
            try:
                return Config(parser(raw, p))
            except ConfigError:
                continue

        raise ConfigError(
            f"Cannot parse '{p}': not valid YAML or JSON. "
            "Use a .yaml, .yml, or .json extension."
        )

    @staticmethod
    def merge_files(paths: List[Union[str, Path]]) -> "Config":
        """Load multiple files and deep-merge them in order.

        Later files override earlier ones.  Files that do not exist are
        **silently skipped** so that optional user-level configs can be
        listed without requiring them to be present.

        Args:
            paths: Ordered list of file paths.

        Returns:
            A single merged :class:`Config`.

        Raises:
            ConfigError: If a file *exists* but cannot be parsed.
        """
        merged: Dict[str, Any] = {}
        for p in paths:
            if not Path(p).exists():
                continue
            layer = ConfigLoader.load(p).as_dict()
            merged = _deep_merge(merged, layer)
        return Config(merged)

    # ------------------------------------------------------------------
    # Internal parsers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_yaml(text: str, path: Path) -> Dict[str, Any]:
        try:
            import yaml  # type: ignore[import]
        except ImportError as exc:
            raise ConfigError(
                "pyyaml is required to load YAML configuration files. "
                "Install it with:  pip install pyyaml"
            ) from exc

        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ConfigError(
                f"YAML parse error in '{path}': {exc}"
            ) from exc

        if data is None:
            return {}
        if not isinstance(data, dict):
            raise ConfigError(
                f"Config file '{path}' must contain a YAML mapping at the "
                f"top level, but got {type(data).__name__}."
            )
        return data

    @staticmethod
    def _parse_json(text: str, path: Path) -> Dict[str, Any]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ConfigError(
                f"JSON parse error in '{path}': {exc}"
            ) from exc

        if not isinstance(data, dict):
            raise ConfigError(
                f"Config file '{path}' must be a JSON object at the top level."
            )
        return data


# ---------------------------------------------------------------------------
# ConfigManager
# ---------------------------------------------------------------------------

# Env-var prefix and pattern for auto-overlay.
_ENV_PREFIX = "LH_PIPELINE_"
_ENV_SECTION_RE = re.compile(r"^" + _ENV_PREFIX + r"([A-Z][A-Z0-9_]+)$")


class ConfigManager:
    """Registry of named :class:`Config` objects with environment-variable overlay.

    Maintains a dict of named configs (``"pipeline"``, ``"project"``, etc.)
    and optionally overlays ``LH_PIPELINE_*`` environment variables on top.

    Environment variable convention::

        LH_PIPELINE_PROJECT_NAME=darkStar
            → config["project"]["name"] = "darkStar"

        LH_PIPELINE_RENDER_ENGINE=karma
            → config["render"]["engine"] = "karma"

    The section name is the first ``_``-delimited segment after the prefix
    (lower-cased).  The remainder becomes the sub-key.

    .. note::
        Env-var values are always strings.  If a field is expected to be an
        integer or float, parse it explicitly at the call site.

    Args:
        apply_env: If ``True`` (default), overlay ``LH_PIPELINE_*`` env vars
                   when loading configs.
    """

    def __init__(self, apply_env: bool = True) -> None:
        self._configs: Dict[str, Config] = {}
        self._apply_env = apply_env

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------

    def load(
        self,
        name: str,
        *paths: Union[str, Path],
        required: bool = True,
    ) -> "ConfigManager":
        """Load one or more files, merge them, and register under *name*.

        Args:
            name:     Registry key (e.g. ``"pipeline"``, ``"project"``).
            *paths:   Config file paths merged in order (later wins).
            required: If ``True`` and **none** of the paths exist, raise
                      :exc:`ConfigError`.

        Returns:
            ``self``, for method chaining.

        Raises:
            ConfigError: If *required* is ``True`` and no files are found.
        """
        existing = [p for p in paths if Path(p).exists()]
        if required and not existing:
            raise ConfigError(
                f"Config '{name}': none of the provided paths exist: "
                f"{[str(p) for p in paths]}"
            )
        cfg = ConfigLoader.merge_files(list(paths))
        if self._apply_env:
            overlay = self._env_overlay()
            if overlay:
                cfg = cfg.merged_with(overlay)
        self._configs[name] = cfg
        return self

    def register(self, name: str, config: "Config") -> "ConfigManager":
        """Register a pre-built :class:`Config` under *name*.

        Args:
            name:   Registry key.
            config: Pre-built Config object.

        Returns:
            ``self``, for method chaining.
        """
        self._configs[name] = config
        return self

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, name: str) -> "Config":
        """Return the named :class:`Config`.

        Raises:
            KeyError: If *name* has not been registered.
        """
        if name not in self._configs:
            raise KeyError(
                f"Config '{name}' not registered. "
                f"Registered configs: {sorted(self._configs.keys())}."
            )
        return self._configs[name]

    def get_or_empty(self, name: str) -> "Config":
        """Return the named Config, or an empty Config if not registered."""
        return self._configs.get(name, Config())

    def registered_names(self) -> List[str]:
        """Sorted list of all registered config names."""
        return sorted(self._configs.keys())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _env_overlay(self) -> Dict[str, Any]:
        """Build a nested dict from ``LH_PIPELINE_SECTION_KEY=value`` env vars.

        Example::

            LH_PIPELINE_PROJECT_FPS=48
            → {"project": {"fps": "48"}}   # value is always a string

        Single-segment vars (``LH_PIPELINE_DEBUG=1``) are placed at the
        top level (``{"debug": "1"}``).
        """
        overlay: Dict[str, Any] = {}
        for env_key, env_val in os.environ.items():
            m = _ENV_SECTION_RE.match(env_key)
            if not m:
                continue
            remainder = m.group(1).lower()
            # Split into at most two parts: section + subkey
            parts = remainder.split("_", 1)
            if len(parts) == 2:
                section, subkey = parts
                overlay.setdefault(section, {})[subkey] = env_val
            else:
                overlay[parts[0]] = env_val
        return overlay

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"ConfigManager(registered={self.registered_names()})"
