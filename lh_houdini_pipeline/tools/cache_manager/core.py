"""
lh_houdini_pipeline.tools.cache_manager.core
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure orchestration + cleanup policy for the Scene Cache Manager.

No ``hou``, no Qt -- this is the *decision* layer.  It turns raw
:class:`~lh_houdini_pipeline.file.cache_utils.CacheSequence` data into:

* flat **report rows** the UI renders as a table, and
* a **CleanupPlan**: exactly which paths would be deleted and how many bytes
  reclaimed -- computed *before* anything touches the disk (dry-run first is a
  hard rule for destructive tools).

Keeping the policy here means it is unit-testable and the same logic drives
both the UI's checkboxes and any future headless ``--purge`` batch job.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Sequence, Tuple

from lh_houdini_pipeline.file.cache_utils import (
    CacheSequence,
    frame_range_label,
    human_size,
    is_stale,
)


class CacheStatus(str, Enum):
    """Health classification for a single sequence (drives row colour)."""

    OK = "ok"            # complete + fresh
    INCOMPLETE = "incomplete"  # has frame gaps
    STALE = "stale"      # older than policy / source-newer
    EMPTY = "empty"      # zero bytes / no files


@dataclass(frozen=True)
class CleanupPolicy:
    """Rules deciding what counts as a deletion candidate.

    Attributes:
        stale_days:      Age (days) past which a sequence is "stale".
        delete_stale:    Mark stale sequences as candidates.
        delete_incomplete: Mark gappy sequences as candidates.
        delete_empty:    Mark zero-byte sequences as candidates.
    """

    stale_days: float = 14.0
    delete_stale: bool = True
    delete_incomplete: bool = False
    delete_empty: bool = True


@dataclass(frozen=True)
class CacheReportRow:
    """One presentation row -- a sequence plus its computed verdict."""

    sequence: CacheSequence
    status: CacheStatus
    is_candidate: bool

    # Convenience accessors for the UI (keeps Qt code dumb).
    @property
    def name(self) -> str:
        return self.sequence.name

    @property
    def directory(self) -> str:
        return self.sequence.directory

    @property
    def range_label(self) -> str:
        return frame_range_label(self.sequence)

    @property
    def size_label(self) -> str:
        return human_size(self.sequence.total_size)

    @property
    def size_bytes(self) -> int:
        return self.sequence.total_size

    @property
    def file_count(self) -> int:
        return self.sequence.frame_count


@dataclass(frozen=True)
class CleanupPlan:
    """The result of :func:`plan_cleanup` -- a dry-run by construction.

    Attributes:
        rows:           Every sequence with its status/candidate verdict.
        delete_paths:   Flat list of file paths the plan would remove.
        reclaimed_bytes: Total bytes the deletion would free.
    """

    rows: Tuple[CacheReportRow, ...]
    delete_paths: Tuple[str, ...]
    reclaimed_bytes: int

    @property
    def candidate_rows(self) -> List[CacheReportRow]:
        """Rows flagged for deletion."""
        return [r for r in self.rows if r.is_candidate]

    @property
    def reclaimed_label(self) -> str:
        return human_size(self.reclaimed_bytes)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(
    sequence: CacheSequence,
    policy: CleanupPolicy,
    *,
    source_mtime: Optional[float] = None,
    now: Optional[float] = None,
) -> CacheStatus:
    """Return the :class:`CacheStatus` for *sequence* under *policy*.

    Precedence: EMPTY > STALE > INCOMPLETE > OK.  Empty wins because a
    zero-byte cache is the most clearly worthless; staleness outranks gaps
    because a stale-but-complete cache is still purgeable.
    """
    if sequence.frame_count == 0 or sequence.total_size == 0:
        return CacheStatus.EMPTY
    if is_stale(sequence, days=policy.stale_days, source_mtime=source_mtime, now=now):
        return CacheStatus.STALE
    if not sequence.is_complete:
        return CacheStatus.INCOMPLETE
    return CacheStatus.OK


def _is_candidate(status: CacheStatus, policy: CleanupPolicy) -> bool:
    """Map a status to a deletion verdict given the policy switches."""
    if status is CacheStatus.EMPTY:
        return policy.delete_empty
    if status is CacheStatus.STALE:
        return policy.delete_stale
    if status is CacheStatus.INCOMPLETE:
        return policy.delete_incomplete
    return False


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

def plan_cleanup(
    sequences: Sequence[CacheSequence],
    policy: Optional[CleanupPolicy] = None,
    *,
    source_mtime: Optional[float] = None,
    now: Optional[float] = None,
) -> CleanupPlan:
    """Build a :class:`CleanupPlan` from scanned *sequences* (pure / dry-run).

    Nothing is deleted here -- the plan is data the UI shows for confirmation
    and the service later executes.  This separation is the safety guarantee.

    Args:
        sequences:    Scanned cache sequences.
        policy:       Cleanup rules; defaults to :class:`CleanupPolicy`.
        source_mtime: Optional source (HIP) mtime for source-newer staleness.
        now:          Override "now" for deterministic tests.
    """
    policy = policy or CleanupPolicy()
    rows: List[CacheReportRow] = []
    delete_paths: List[str] = []
    reclaimed = 0

    for seq in sequences:
        status = classify(seq, policy, source_mtime=source_mtime, now=now)
        candidate = _is_candidate(status, policy)
        rows.append(CacheReportRow(sequence=seq, status=status, is_candidate=candidate))
        if candidate:
            delete_paths.extend(f.path for f in seq.files)
            reclaimed += seq.total_size

    return CleanupPlan(
        rows=tuple(rows),
        delete_paths=tuple(delete_paths),
        reclaimed_bytes=reclaimed,
    )


def paths_for_sequences(sequences: Sequence[CacheSequence]) -> List[str]:
    """Flatten the file paths of an explicit selection of sequences.

    Used by the UI when the artist hand-picks rows rather than relying on the
    policy's auto-candidates.
    """
    out: List[str] = []
    for seq in sequences:
        out.extend(f.path for f in seq.files)
    return out
