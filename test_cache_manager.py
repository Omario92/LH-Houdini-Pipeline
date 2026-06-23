"""
test_cache_manager.py -- pure assertions for the Scene Cache Manager.

Covers file.cache_utils (parsing/scan/gaps/staleness) and
tools.cache_manager.core (classify/plan_cleanup). Runs outside Houdini.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, ".")

from lh_houdini_pipeline.file import cache_utils as CU
from lh_houdini_pipeline.tools.cache_manager import core as CM

_count = 0


def check(label: str, cond: bool) -> None:
    global _count
    _count += 1
    print("  " + label.ljust(46) + ("OK" if cond else "FAIL"))
    assert cond, label


def _make_caches(d: str) -> None:
    # smoke: 1001-1005 missing 1003
    for f in (1001, 1002, 1004, 1005):
        with open(os.path.join(d, "smoke." + str(f) + ".bgeo.sc"), "wb") as fh:
            fh.write(b"\0" * 1024)
    # pyro_v003: complete 1-3
    for f in ("0001", "0002", "0003"):
        with open(os.path.join(d, "pyro_v003." + f + ".bgeo.sc"), "wb") as fh:
            fh.write(b"\0" * 2048)
    # static usd
    with open(os.path.join(d, "city.usd"), "wb") as fh:
        fh.write(b"\0" * 4096)
    # empty vdb
    open(os.path.join(d, "fog.0001.vdb"), "wb").close()


def test_parsing() -> None:
    print("=== cache_utils parsing ===")
    check("compound .bgeo.sc", CU.split_compound_suffix("a.0001.bgeo.sc") == ("a.0001", ".bgeo.sc"))
    check("simple .usd", CU.split_compound_suffix("city.usd") == ("city", ".usd"))
    check("frame split", CU.parse_frame("smoke.0042") == ("smoke", 42))
    check("version stays in base", CU.parse_frame("pyro_v003.0100") == ("pyro_v003", 100))
    check("no frame -> None", CU.parse_frame("city") == ("city", None))


def test_scan_and_gaps() -> None:
    print("=== scan + gap detection ===")
    with tempfile.TemporaryDirectory() as d:
        _make_caches(d)
        seqs = {s.name: s for s in CU.scan_directory(d, formats=("bgeo.sc", "vdb", "usd"))}
        check("4 sequences found", len(seqs) == 4)
        check("smoke gap = [1003]", seqs["smoke.bgeo.sc"].missing_frames == [1003])
        check("smoke not complete", not seqs["smoke.bgeo.sc"].is_complete)
        check("pyro complete", seqs["pyro_v003.bgeo.sc"].is_complete)
        check("city not a sequence", not seqs["city.usd"].is_sequence)
        check("smoke size 4KB", seqs["smoke.bgeo.sc"].total_size == 4096)
        check("fog empty (0 bytes)", seqs["fog.vdb"].total_size == 0)


def test_staleness() -> None:
    print("=== staleness ===")
    with tempfile.TemporaryDirectory() as d:
        _make_caches(d)
        seqs = {s.name: s for s in CU.scan_directory(d, formats=("bgeo.sc",))}
        smoke = seqs["smoke.bgeo.sc"]
        now = smoke.latest_mtime
        check("fresh -> not stale", not CU.is_stale(smoke, days=14, now=now))
        check("aged -> stale", CU.is_stale(smoke, days=14, now=now + 15 * 86400))
        check("source newer -> stale", CU.is_stale(smoke, days=None, source_mtime=now + 100, now=now))


def test_policy_and_plan() -> None:
    print("=== core classify + plan_cleanup ===")
    with tempfile.TemporaryDirectory() as d:
        _make_caches(d)
        seqs = CU.scan_directory(d, formats=("bgeo.sc", "vdb", "usd"))
        now = max(s.latest_mtime for s in seqs)

        pol = CM.CleanupPolicy(stale_days=14, delete_stale=True,
                               delete_incomplete=True, delete_empty=True)
        plan = CM.plan_cleanup(seqs, pol, now=now)
        by = {r.name: r for r in plan.rows}
        check("empty fog classified EMPTY", by["fog.vdb"].status == CM.CacheStatus.EMPTY)
        check("smoke classified INCOMPLETE", by["smoke.bgeo.sc"].status == CM.CacheStatus.INCOMPLETE)
        check("pyro OK", by["pyro_v003.bgeo.sc"].status == CM.CacheStatus.OK)
        check("fog is candidate", by["fog.vdb"].is_candidate)
        check("smoke is candidate (gaps on)", by["smoke.bgeo.sc"].is_candidate)
        check("pyro not candidate", not by["pyro_v003.bgeo.sc"].is_candidate)
        check("plan has delete paths", len(plan.delete_paths) >= 4)

        # turn off incomplete -> smoke no longer a candidate
        pol2 = CM.CleanupPolicy(delete_stale=True, delete_incomplete=False, delete_empty=True)
        plan2 = CM.plan_cleanup(seqs, pol2, now=now)
        by2 = {r.name: r for r in plan2.rows}
        check("smoke not candidate when gaps off", not by2["smoke.bgeo.sc"].is_candidate)


def test_human_size() -> None:
    print("=== human_size ===")
    check("bytes", CU.human_size(512) == "512 B")
    check("KB", CU.human_size(1536) == "1.5 KB")
    check("MB", CU.human_size(5 * 1024 * 1024) == "5.0 MB")


if __name__ == "__main__":
    test_parsing()
    test_scan_and_gaps()
    test_staleness()
    test_policy_and_plan()
    test_human_size()
    print("\nAll " + str(_count) + " Cache Manager assertions passed.")
