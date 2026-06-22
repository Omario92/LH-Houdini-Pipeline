"""
lh_houdini_pipeline.tools.project_manager.settings
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Persistent user settings for the Project Manager.

This module is pure Python and intentionally small: it owns the JSON file
format, folder presets, validation, and load/save helpers.  The UI can ask for
settings without knowing where they live, while the controller can turn the
selected folders into a ``ProjectTemplate``.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, Union

from lh_houdini_pipeline.core.config import ConfigError
from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.tools.project_manager import core as _core

PathLike = Union[str, Path]
_log = get_logger(__name__)

SETTINGS_VERSION = 1
SETTINGS_FILENAME = "project_manager_settings.json"


@dataclass(frozen=True)
class ProjectManagerSettings:
    """User-configurable Project Manager defaults.

    Attributes:
        project_folders: Folder paths created directly under the project root.
    """

    project_folders: Tuple[str, ...] = _core.DEFAULT_PROJECT_FOLDERS


def default_settings_path() -> Path:
    """Return the JSON path used for persistent Project Manager settings.

    The pipeline-level ``RBW`` environment variable wins when present.  Outside
    a configured pipeline install, settings fall back to the user's home config
    folder so the tool remains usable in tests and local development.

    Returns:
        Path to ``project_manager_settings.json``.
    """
    rbw = os.environ.get("RBW", "").strip()
    if rbw:
        return Path(rbw) / "config" / SETTINGS_FILENAME
    return Path.home() / ".lh_pipeline" / "config" / SETTINGS_FILENAME


def available_folders() -> Tuple[str, ...]:
    """Return every folder exposed in the Settings dialog.

    Returns:
        Folder names/paths in stable display order.
    """
    return _core.DEFAULT_PROJECT_FOLDERS


def preset_full() -> Tuple[str, ...]:
    """Return the complete default Project Manager folder structure.

    Returns:
        All project folders known to the current tool version.
    """
    return available_folders()


def preset_minimal() -> Tuple[str, ...]:
    """Return a compact folder set for small projects.

    Returns:
        Basic project folders for geometry, textures, renders, and caches.
    """
    return _filter_known(("geo", "tex", "render", "cache"))


def preset_lookdev() -> Tuple[str, ...]:
    """Return a lookdev-oriented folder set.

    Returns:
        Folder paths useful for asset lookdev and publish handoff.
    """
    return _filter_known(("houdini", "houdini/scenes", "geo", "tex", "usd", "render", "ref"))


def load_settings(path: PathLike | None = None) -> ProjectManagerSettings:
    """Load user settings from JSON, falling back to defaults when missing.

    Args:
        path: Optional override path for tests or custom deployments.

    Returns:
        Loaded and validated :class:`ProjectManagerSettings`.

    Raises:
        ConfigError: If the file exists but cannot be read or parsed.
    """
    settings_path = Path(path) if path is not None else default_settings_path()
    if not settings_path.exists():
        return ProjectManagerSettings()
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("Cannot load Project Manager settings: " + str(exc)) from exc
    folders = data.get("default_folders", _core.DEFAULT_PROJECT_FOLDERS)
    return ProjectManagerSettings(project_folders=validate_folders(folders))


def save_settings(settings: ProjectManagerSettings, path: PathLike | None = None) -> Path:
    """Write Project Manager settings to JSON.

    Args:
        settings: Settings object to persist.
        path: Optional override path for tests or custom deployments.

    Returns:
        Path that was written.

    Raises:
        ConfigError: If the file cannot be written.
    """
    settings_path = Path(path) if path is not None else default_settings_path()
    payload = {
        "version": SETTINGS_VERSION,
        "default_folders": list(validate_folders(settings.project_folders)),
    }
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        raise ConfigError("Cannot save Project Manager settings: " + str(exc)) from exc
    _log.info("Saved Project Manager settings: " + str(settings_path))
    return settings_path


def reset_settings(path: PathLike | None = None) -> Path:
    """Restore the JSON settings file to the full default folder set.

    Args:
        path: Optional override path for tests or custom deployments.

    Returns:
        Path that was written.
    """
    return save_settings(ProjectManagerSettings(), path=path)


def validate_folders(folders: Iterable[str]) -> Tuple[str, ...]:
    """Return selected folders after filtering unknown/duplicate entries.

    Args:
        folders: Candidate folder paths from user settings or UI checkboxes.

    Returns:
        Known folders in canonical display order.
    """
    selected = {str(folder).strip().replace("\\", "/") for folder in folders if str(folder).strip()}
    return tuple(folder for folder in available_folders() if folder in selected)


def _filter_known(folders: Iterable[str]) -> Tuple[str, ...]:
    """Filter a preset tuple against folders available in this tool version."""
    return validate_folders(folders)
