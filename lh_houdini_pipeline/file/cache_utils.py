"""
lh_houdini_pipeline.file.cache_utils
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure-Python model + analysis of on-disk scene caches (BGEO/VDB/USD/ABC).

Production reasoning
--------------------
A Scene Cache Manager lives or dies on three honest questions an artist asks:

    1. "Is this sequence complete, or did the farm drop frames?"  -> gap detection
    2. "Which of these are dead weight I can reclaim?"            -> staleness + size
    3. "How big is the damage if I delete it?"                   -> size reporting

All of that is *pure data analysis* and belongs in the ``file/`` layer: no
``hou``, no Qt, fully unit-testable with ``python test_cache_manager.py``.
The Houdini/UI layers sit on top and only supply *where to look* and *do the
delete*.

Cache-naming reality
--------------------
Houdini caches are usually ``base.$F4.bgeo.sc`` -> ``smoke.0042.bgeo.sc``.
Two wrinkles this module handles that a naive ``str.split('.')`` does not:

* **Compound extensions** -- ``.bgeo.sc`` is one logical format, not ``.sc``.
* **Version-in-base** -- ``pyro_v003.0042.bgeo.sc`` must group by
  ``pyro_v003`` (the *version is part of the identity*, not the frame).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

PathLike = Union[str, Path]

#: Multi-part extensions that must be treated as a single logical format.
_COMPOUND_EXTS = (".bgeo.sc", ".bgeo.gz", ".vdb.gz")

#: Trailing frame token: a ``.`` or ``_`` separator then 1-8 digits at the end
#: of the *frame-bearing* stem.  Anchored to end so a version like ``v003`` in
#: the middle is never mistaken for the frame.
_FRAME_RE = re.compile(r"^(?P<base>.*?)[._](?P<frame>\d{1,8})$")


# ---------------------------------------------------------------------------
# Filename parsing
# ---------------------------------------------------------------------------

def split_compound_suffix(name: str) -> Tuple[str, str]:
    """Split *name* into ``(stem, ext)`` honouring compound extensions.

    Examples::

        "smoke.0042.bgeo.sc" -> ("smoke.0042", ".bgeo.sc")
        "city.usd"           -> ("city", ".usd")
        "noext"              -> ("noext", "")
    """
    lower = name.lower()
    for ext in _COMPOUND_EXTS:
        if lower.endswith(ext):
            return name[: -len(ext)], name[-len(ext):]
    p = Path(name)
    return p.stem, p.suffix


def parse_frame(stem: str) -> Tuple[str, Optional[int]]:
    """Split a frame-bearing *stem* into ``(base, frame)``.

    Returns ``(stem, None)`` when there is no trailing frame token, so single
    (non-sequence) caches like ``city.usd`` pass through unchanged.

    Examples::

        "smoke.0042"      -> ("smoke", 42)
        "pyro_v003.0100"  -> ("pyro_v003", 100)   # version kept in base
        "city"            -> ("city", None)
    """
    m = _FRAME_RE.match(stem)
    if not m:
        return stem, None
    return m.group("base"), int(m.group("frame"))


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CacheFile:
    """One cache file on disk (frozen value object).

    Attributes:
        path:  Absolute path as a string.
        frame: Frame number, or ``None`` for a single-file cache.
        size:  Size in bytes.
        mtime: Modification time (epoch seconds).
    """

    path: str
    frame: Optional[int]
    size: int
    mtime: float


@dataclass(frozen=True)
class CacheSequence:
    """A group of cache files sharing ``(directory, base, ext)``.

    A single-file cache (``city.usd``) is just a sequence of length 1 whose
    sole file has ``frame is None``.
    """

    directory: str
    base: str
    ext: str
    files: Tuple[CacheFile, ...]

    # -- identity -------------------------------------------------------
    @property
    def name(self) -> str:
        """Display name, e.g. ``"smoke.bgeo.sc"`` or ``"city.usd"``."""
        return self.base + self.ext

    @property
    def is_sequence(self) -> bool:
        """True if this holds framed files (more than a single static file)."""
        return any(f.frame is not None for f in self.files)

    # -- frames ---------------------------------------------------------
    @property
    def frames(self) -> List[int]:
        """Sorted list of present frame numbers (empty for static caches)."""
        return sorted(f.frame for f in self.files if f.frame is not None)

    @property
    def start(self) -> Optional[int]:
        """First frame, or ``None`` if not a sequence."""
        fr = self.frames
        return fr[0] if fr else None

    @property
    def end(self) -> Optional[int]:
        """Last frame, or ``None`` if not a sequence."""
        fr = self.frames
        return fr[-1] if fr else None

    @property
    def missing_frames(self) -> List[int]:
        """Frames absent between ``start`` and ``end`` (the gap list).

        Assumes step 1 (the overwhelmingly common case for sim/geo caches).
        Empty list means a contiguous, complete range.
        """
        fr = self.frames
        if len(fr) < 2:
            return []
        present = set(fr)
        return [f for f in range(fr[0], fr[-1] + 1) if f not in present]

    @property
    def is_complete(self) -> bool:
        """True if a sequence has no internal gaps (or is a static file)."""
        return not self.missing_frames

    # -- size / time ----------------------------------------------------
    @property
    def total_size(self) -> int:
        """Total bytes across all files in the sequence."""
        return sum(f.size for f in self.files)

    @property
    def latest_mtime(self) -> float:
        """Newest modification time across the sequence (0.0 if empty)."""
        return max((f.mtime for f in self.files), default=0.0)

    @property
    def frame_count(self) -> int:
        """Number of files in the sequence."""
        return len(self.files)


# ---------------------------------------------------------------------------
# Scanning
# ---------------------------------------------------------------------------

def _matches_formats(ext: str, formats: Optional[Tuple[str, ...]]) -> bool:
    """Return True if *ext* (e.g. ``.bgeo.sc``) is in the allowed *formats*."""
    if not formats:
        return True
    e = ext.lower().lstrip(".")
    return any(e == f.lower().lstrip(".") for f in formats)


def scan_directory(
    directory: PathLike,
    formats: Optional[Tuple[str, ...]] = None,
    recursive: bool = False,
) -> List[CacheSequence]:
    """Scan *directory* and group cache files into :class:`CacheSequence` objects.

    Args:
        directory: Folder to scan.
        formats:   Allowed extensions (e.g. ``("bgeo.sc", "vdb")``).  ``None``
                   accepts everything.  Matches compound extensions.
        recursive: Recurse into sub-directories when ``True``.

    Returns:
        Sequences sorted by directory then name.  Missing dir -> empty list
        (non-fatal: a not-yet-cached node is normal, not an error).
    """
    root = Path(directory)
    if not root.is_dir():
        return []

    walker = root.rglob("*") if recursive else root.glob("*")
    # Group key: (directory, base, ext) -> list[CacheFile]
    groups: Dict[Tuple[str, str, str], List[CacheFile]] = {}

    for p in walker:
        if not p.is_file():
            continue
        stem, ext = split_compound_suffix(p.name)
        if not _matches_formats(ext, formats):
            continue
        base, frame = parse_frame(stem)
        try:
            st = p.stat()
            size, mtime = st.st_size, st.st_mtime
        except OSError:
            size, mtime = 0, 0.0
        key = (str(p.parent), base, ext)
        groups.setdefault(key, []).append(
            CacheFile(path=str(p), frame=frame, size=size, mtime=mtime)
        )

    sequences = [
        CacheSequence(directory=d, base=b, ext=e, files=tuple(files))
        for (d, b, e), files in groups.items()
    ]
    sequences.sort(key=lambda s: (s.directory, s.name))
    return sequences


# ---------------------------------------------------------------------------
# Staleness + presentation helpers
# ---------------------------------------------------------------------------

def is_stale(
    sequence: CacheSequence,
    *,
    days: Optional[float] = None,
    source_mtime: Optional[float] = None,
    now: Optional[float] = None,
) -> bool:
    """Decide whether *sequence* is stale.

    Two independent, OR-combined criteria:

    * **Age**: newest file older than *days* days.
    * **Source-newer**: a source file (*source_mtime*, e.g. the HIP) is newer
      than the cache -- the classic "cache out of date" signal.

    Args:
        sequence:     The sequence to test.
        days:         Age threshold in days; ``None`` disables the age check.
        source_mtime: mtime of the source the cache derives from; ``None``
                      disables the source-newer check.
        now:          Override "current time" (epoch secs) for deterministic
                      tests.  Defaults to ``time.time()``.

    Returns:
        ``True`` if stale by either criterion.
    """
    now = time.time() if now is None else now
    latest = sequence.latest_mtime

    if source_mtime is not None and source_mtime > latest:
        return True
    if days is not None and latest > 0.0:
        age_days = (now - latest) / 86400.0
        if age_days > days:
            return True
    return False


def human_size(num_bytes: float) -> str:
    """Format a byte count as a human-readable string (e.g. ``"1.4 GB"``)."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024.0 or unit == "TB":
            return (str(int(size)) + " " + unit) if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def frame_range_label(sequence: CacheSequence) -> str:
    """Human label for a sequence's frame coverage.

    Examples: ``"1001-1100"``, ``"1001-1100 (3 missing)"``, ``"single file"``.
    """
    if not sequence.is_sequence:
        return "single file"
    miss = sequence.missing_frames
    base = str(sequence.start) + "-" + str(sequence.end)
    if miss:
        return base + " (" + str(len(miss)) + " missing)"
    return base


# ---------------------------------------------------------------------------
# Back-compat: original stub signature
# ---------------------------------------------------------------------------

def detect_frame_range(
    directory: PathLike,
    pattern: str,
) -> Optional[Tuple[int, int]]:
    """Detect ``(first, last)`` frame for files matching *pattern* in *directory*.

    Retained for backward compatibility.  New code should prefer
    :func:`scan_directory`, which groups by sequence and reports gaps.
    """
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
