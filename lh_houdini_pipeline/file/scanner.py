"""
lh_houdini_pipeline.file.scanner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Filesystem scanning utilities for discovering pipeline assets.

Planned:
    * AssetScanner  -- scan a show directory for assets / shots
    * CacheScanner  -- discover USD / Alembic caches for a given context
    * PublishScanner -- enumerate published versions of an asset

Stub -- to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List, Optional, Union

PathLike = Union[str, Path]


def find_files(
    directory: PathLike,
    pattern: str = "*",
    recursive: bool = False,
) -> List[Path]:
    """Return all files in *directory* matching *pattern*.

    Args:
        directory: Root directory to search.
        pattern:   Glob pattern (e.g. ``"*.usd"``, ``"**/*.hip"``).
        recursive: If True and *pattern* doesn't start with ``**``,
                   prepend ``**`` to search recursively.

    Returns:
        Sorted list of matching ``pathlib.Path`` objects.
    """
    d = Path(directory)
    if not d.is_dir():
        return []
    glob = ("**/" + pattern) if recursive and not pattern.startswith("**") else pattern
    return sorted(p for p in d.glob(glob) if p.is_file())
