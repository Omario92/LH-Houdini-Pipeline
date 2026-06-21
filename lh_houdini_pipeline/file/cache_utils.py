"""
lh_houdini_pipeline.file.cache_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Utilities for managing scene cache files (USD, Alembic, BGEO).

Planned:
    * CacheManifest -- track what frame ranges exist on disk
    * gap detection (missing frames in a sequence)
    * cache size reporting
    * staleness checks (cache older than source HIP)

Stub -- to be implemented.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple, Union

PathLike = Union[str, Path]


def detect_frame_range(
    directory: PathLike,
    pattern: str,
) -> Optional[Tuple[int, int]]:
    """Detect the first and last frame numbers present for a cache sequence.

    Args:
        directory: Directory containing the cache files.
        pattern:   Glob pattern with ``*`` where the frame number appears.

    Returns:
        ``(first_frame, last_frame)`` tuple, or ``None`` if no files found.
    """
    import re
    d = Path(directory)
    if not d.is_dir():
        return None

    frame_re = re.compile(r"(\d+)")
    frames: List[int] = []

    for p in d.glob(pattern):
        nums = frame_re.findall(p.stem)
        if nums:
            frames.append(int(nums[-1]))

    if not frames:
        return None
    return min(frames), max(frames)
