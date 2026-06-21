"""
lh_houdini_pipeline.file.versioning
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Version string parsing, comparison, and disk-aware resolution.

Supports the following version token formats:

    v001     -- zero-padded 3-digit (most common in VFX)
    v01      -- zero-padded 2-digit
    v1       -- unpadded
    _v001    -- underscore-prefixed 3-digit variant

Design
------
* ``VersionFormat``   -- enum carrying the regex, padding, and glob stub for
  each supported format.  Adding a new convention is one enum member + no
  other changes.
* ``Version``         -- comparable, hashable value object.  Implements
  ``__lt__`` / ``__eq__`` based on the integer number alone (format-agnostic
  comparison), so ``sorted()`` and ``max()`` work naturally across mixed-
  format lists.
* ``VersionedFile``   -- pairs a ``Version`` with its ``pathlib.Path``.
* ``VersionResolver`` -- disk-scanning resolver for a specific file glob.
  Provides ``find_latest``, ``next_version``, and ``history``.

Pure Python -- no ``hou`` imports.

Example
-------
::

    from lh_houdini_pipeline.file.versioning import VersionResolver

    r = VersionResolver(
        directory="/jobs/darkStar/houdini/sh0100/work/fx/",
        pattern="fx_sh0100_v*.hip",
    )
    r.find_latest()    # VersionedFile(path=..., version=Version('v007'))
    r.next_version()   # Version('v008')
    r.history()        # [VersionedFile(v001), ..., VersionedFile(v007)]
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterator, List, Optional, Union

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------

class VersionError(ValueError):
    """Raised when a version string cannot be parsed or an operation fails."""


# ---------------------------------------------------------------------------
# VersionFormat
# ---------------------------------------------------------------------------

class VersionFormat(Enum):
    """Convention for encoding a version number in a filename.

    Each member stores:
        prefix     -- string before the digits (``"v"`` or ``"_v"``)
        pattern    -- compiled regex with a named group ``ver`` for the digits
        padding    -- zero-pad width (0 = no padding)
        glob_stub  -- glob wildcard fragment (e.g. ``"v???"`` for V3)

    Detection order matters: members are tried from most-specific (V3) to
    least-specific (V1) in :py:meth:`Version.parse`.
    """

    V3  = ("v",  r"(?<!\d)v(?P<ver>\d{3})(?!\d)", 3, "v???")
    V2  = ("v",  r"(?<!\d)v(?P<ver>\d{2})(?!\d)", 2, "v??")
    V1  = ("v",  r"(?<!\d)v(?P<ver>\d+)(?!\d)",   0, "v*")
    _V3 = ("_v", r"_v(?P<ver>\d{3})(?!\d)",             3, "_v???")
    _V2 = ("_v", r"_v(?P<ver>\d{2})(?!\d)",             2, "_v??")

    def __init__(
        self,
        prefix: str,
        pattern_str: str,
        padding: int,
        glob_stub: str,
    ) -> None:
        self.prefix    = prefix
        self.pattern   = re.compile(pattern_str)
        self.padding   = padding
        self.glob_stub = glob_stub

    def format_number(self, number: int) -> str:
        """Return the version string for *number* in this format.

        Examples:
            >>> VersionFormat.V3.format_number(7)
            'v007'
            >>> VersionFormat.V1.format_number(7)
            'v7'
        """
        digits = str(number)
        if self.padding:
            digits = digits.zfill(self.padding)
        return self.prefix + digits


# Evaluation order for auto-detection: most specific first.
_DETECT_ORDER: List[VersionFormat] = [
    VersionFormat.V3,
    VersionFormat._V3,
    VersionFormat.V2,
    VersionFormat._V2,
    VersionFormat.V1,
]


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Version:
    """A parsed version number carrying its source format.

    Comparison operators are based on :attr:`number` alone -- format is
    ignored -- so ``Version(7, V3) == Version(7, V1)`` is ``True`` and
    ``max([...])`` works correctly on mixed-format lists.

    Args:
        number: The integer version number (>= 0).
        fmt:    The :class:`VersionFormat` to use when rendering to a string.

    Example::

        v = Version.parse("fx_sh0100_v007.hip")
        v.number    # 7
        v.string    # "v007"
        v.next()    # Version(number=8, fmt=VersionFormat.V3)
    """

    number: int
    fmt:    VersionFormat = VersionFormat.V3

    # Override auto-generated comparison to ignore ``fmt``.
    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.number < other.number

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.number <= other.number

    def __gt__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.number > other.number

    def __ge__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.number >= other.number

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self.number == other.number

    def __hash__(self) -> int:
        return hash(self.number)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def string(self) -> str:
        """Version as it would appear in a filename, e.g. ``"v007"``."""
        return self.fmt.format_number(self.number)

    # ------------------------------------------------------------------
    # Mutation (returns new instances -- Version is frozen)
    # ------------------------------------------------------------------

    def next(self, increment: int = 1) -> "Version":
        """Return the next version (same format, number + *increment*).

        Args:
            increment: How many versions to advance.  Must be >= 1.

        Raises:
            VersionError: If *increment* < 1.
        """
        if increment < 1:
            raise VersionError(
                "increment must be >= 1, got " + str(increment)
            )
        return Version(self.number + increment, self.fmt)

    def prev(self) -> "Version":
        """Return the previous version.

        Raises:
            VersionError: If this version is already at 1 (or 0).
        """
        if self.number <= 1:
            raise VersionError(
                "Cannot go below version 1 (current: " + str(self.number) + ")"
            )
        return Version(self.number - 1, self.fmt)

    def with_number(self, number: int) -> "Version":
        """Return a new Version with a different number but the same format."""
        if number < 0:
            raise VersionError("Version number must be >= 0, got " + str(number))
        return Version(number, self.fmt)

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, text: str, fmt: Optional[VersionFormat] = None) -> "Version":
        """Extract a version number from *text*.

        Scans the entire string; the first matching token is used.
        Auto-detects the format if *fmt* is not specified.

        Args:
            text: A filename, path stem, or any string containing a version
                  token (e.g. ``"fx_sh0100_v007.hip"``).
            fmt:  Force a specific :class:`VersionFormat`.  If ``None``,
                  the most specific matching format is chosen automatically.

        Returns:
            A :class:`Version` instance.

        Raises:
            VersionError: If no version token is found in *text*.

        Examples:
            >>> Version.parse("fx_sh0100_v007.hip")
            Version('v007')
            >>> Version.parse("render_v03.exr").number
            3
        """
        candidates = [fmt] if fmt else _DETECT_ORDER
        for candidate in candidates:
            m = candidate.pattern.search(text)
            if m:
                return cls(number=int(m.group("ver")), fmt=candidate)
        raise VersionError(
            "No version token found in '"
            + text
            + "'. Expected format like 'v001', '_v001', 'v01', or 'v1'."
        )

    @classmethod
    def from_int(
        cls, number: int, fmt: VersionFormat = VersionFormat.V3
    ) -> "Version":
        """Create a :class:`Version` from an integer and a format.

        Args:
            number: Version number (>= 0).
            fmt:    Desired format.  Defaults to V3 (most common in VFX).
        """
        if number < 0:
            raise VersionError("Version number must be >= 0, got " + str(number))
        return cls(number=number, fmt=fmt)

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return "Version(" + repr(self.string) + ")"

    def __str__(self) -> str:
        return self.string


# ---------------------------------------------------------------------------
# VersionedFile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VersionedFile:
    """A file on disk paired with its parsed :class:`Version`.

    Supports sorting so ``sorted(versioned_files)`` works directly.

    Attributes:
        path:    ``pathlib.Path`` to the file.
        version: Parsed :class:`Version` for this file.
    """
    path:    Path
    version: Version

    @property
    def name(self) -> str:
        """Filename (no directory)."""
        return self.path.name

    @property
    def stem(self) -> str:
        """Filename without extension."""
        return self.path.stem

    def __lt__(self, other: "VersionedFile") -> bool:
        return self.version < other.version

    def __gt__(self, other: "VersionedFile") -> bool:
        return self.version > other.version

    def __le__(self, other: "VersionedFile") -> bool:
        return self.version <= other.version

    def __ge__(self, other: "VersionedFile") -> bool:
        return self.version >= other.version

    def __repr__(self) -> str:
        return "VersionedFile(" + repr(self.path.name) + ", " + repr(self.version) + ")"


# ---------------------------------------------------------------------------
# VersionResolver
# ---------------------------------------------------------------------------

class VersionResolver:
    """Disk-aware version scanner for a specific file glob pattern.

    Scans *directory* for files matching *pattern*, parses their version
    tokens, and provides query methods.

    Args:
        directory: Directory to scan.
        pattern:   Glob pattern with the version wildcard replaced by ``*``
                   (e.g. ``"fx_sh0100_v*.hip"``).  If ``None``, all files
                   whose names contain a parseable version token are included.
        fmt:       Preferred :class:`VersionFormat` for newly generated version
                   strings.  If ``None``, inferred from existing files or
                   defaults to :attr:`VersionFormat.V3`.

    Example::

        r = VersionResolver(
            directory="/jobs/darkStar/houdini/sh0100/work/fx/",
            pattern="fx_sh0100_v*.hip",
        )
        latest = r.find_latest()         # VersionedFile or None
        next_v = r.next_version()        # Version
        history = r.history()            # [VersionedFile, ...]
        count = r.version_count()        # int
    """

    def __init__(
        self,
        directory: PathLike,
        pattern: Optional[str] = None,
        fmt: Optional[VersionFormat] = None,
    ) -> None:
        self._directory = Path(directory)
        self._pattern   = pattern
        self._fmt       = fmt

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def history(self, reverse: bool = False) -> List[VersionedFile]:
        """Return all versioned files sorted by version number.

        Args:
            reverse: If ``True``, highest version first.

        Returns:
            Sorted list of :class:`VersionedFile`.
        """
        files = list(self._scan())
        files.sort(reverse=reverse)
        return files

    def find_latest(self) -> Optional[VersionedFile]:
        """Return the highest-versioned file, or ``None`` if none exist."""
        files = self.history()
        return files[-1] if files else None

    def find_version(self, number: int) -> Optional[VersionedFile]:
        """Return the :class:`VersionedFile` for a specific version number.

        Returns ``None`` if that version does not exist on disk.
        """
        for vf in self._scan():
            if vf.version.number == number:
                return vf
        return None

    def next_version(self) -> Version:
        """Return the :class:`Version` that should be used for the next save.

        * If no files exist: returns ``Version(1, detected_fmt)``.
        * If files exist: returns ``latest.version.next()``.
        """
        fmt = self._effective_fmt()
        latest = self.find_latest()
        if latest is None:
            return Version.from_int(1, fmt)
        return latest.version.next()

    def latest_path(self) -> Optional[Path]:
        """Convenience: return just the ``pathlib.Path`` of the latest file."""
        vf = self.find_latest()
        return vf.path if vf else None

    def version_count(self) -> int:
        """Total number of versioned files found in the directory."""
        return sum(1 for _ in self._scan())

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def inject_version(template: str, version: Version) -> str:
        """Replace the version token in *template* with *version*.

        Tries each known :class:`VersionFormat` in detection order.
        Falls back to substituting a literal ``{version}`` placeholder.

        Args:
            template: Filename or path string containing a version token.
            version:  The :class:`Version` to inject.

        Returns:
            *template* with the version token replaced.

        Example::

            VersionResolver.inject_version(
                "fx_sh0100_v001.hip",
                Version.from_int(7),
            )
            # "fx_sh0100_v007.hip"
        """
        for fmt in _DETECT_ORDER:
            if fmt.pattern.search(template):
                return fmt.pattern.sub(version.string, template, count=1)
        # Fall back to {version} placeholder
        return template.replace("{version}", version.string)

    @staticmethod
    def try_parse(path: PathLike) -> Optional[Version]:
        """Attempt to parse a :class:`Version` from *path*'s filename.

        Returns ``None`` instead of raising if no token is found.
        """
        try:
            return Version.parse(Path(path).name)
        except VersionError:
            return None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _scan(self) -> Iterator[VersionedFile]:
        """Yield a :class:`VersionedFile` for each matching file."""
        if not self._directory.is_dir():
            return

        glob_pat = self._pattern or "*"
        for p in self._directory.glob(glob_pat):
            if not p.is_file():
                continue
            try:
                version = Version.parse(p.name)
            except VersionError:
                continue
            yield VersionedFile(path=p, version=version)

    def _effective_fmt(self) -> VersionFormat:
        """Determine the :class:`VersionFormat` for new version strings.

        Priority: explicit ``self._fmt`` → format of most recent file → V3.
        """
        if self._fmt:
            return self._fmt
        latest = self.find_latest()
        if latest:
            return latest.version.fmt
        return VersionFormat.V3
