"""
lh_houdini_pipeline.houdini.traversal
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Graph-traversal utilities for Houdini node networks (Rebelway Week 01).

Production reasoning
--------------------
Week 01 of the course frames *everything* in production as a graph: a rig, a
city layout, a node network.  Once you see node networks as graphs, the right
tool for "find all X under Y" or "what feeds this node" is a deliberate
traversal -- not an ad-hoc recursive ``for`` loop copy-pasted into every tool.

Big-O discipline
----------------
* ``find_by_type`` prefers ``Node.recursiveGlob("*")`` (evaluated C++-side,
  effectively O(N) with a tiny constant) and only falls back to a Python BFS
  when the API call is unavailable -- the course's "use the fast API path,
  measure, then optimise" mindset.
* Traversals are **iterative** (explicit ``deque``/stack), not recursive, so a
  deep network can never blow the Python recursion limit.
* ``walk_inputs`` guards against cycles with a ``visited`` set -- node graphs
  with feedback (e.g. solver loops) would otherwise loop forever.

hou-lazy
--------
``hou`` is imported lazily inside functions (never at module top) so this
module can be *imported* during unit-test collection outside Houdini; only the
calls themselves require a live session.
"""

from __future__ import annotations

from collections import deque
from typing import TYPE_CHECKING, Callable, Iterator, List, Optional

if TYPE_CHECKING:
    import hou

# A predicate over a node -> bool (e.g. lambda n: n.isBypassed()).
NodePredicate = Callable[["hou.Node"], bool]


# ---------------------------------------------------------------------------
# Children traversal (downward in the network hierarchy)
# ---------------------------------------------------------------------------

def iter_descendants_bfs(root: "hou.Node") -> Iterator["hou.Node"]:
    """Yield every descendant of *root*, breadth-first.

    BFS visits shallow nodes before deep ones -- the natural order when you
    want "the top-level matches first".  Iterative, so depth is unbounded.

    Args:
        root: The network/subnet node to descend into.

    Yields:
        Each descendant ``hou.Node`` exactly once.
    """
    queue: deque = deque(root.children())
    while queue:
        node = queue.popleft()
        yield node
        queue.extend(node.children())


def iter_descendants_dfs(root: "hou.Node") -> Iterator["hou.Node"]:
    """Yield every descendant of *root*, depth-first (pre-order).

    DFS is the right choice when you care about *branch locality* -- e.g.
    "process this subnet fully before moving to the next sibling".

    Args:
        root: The network/subnet node to descend into.

    Yields:
        Each descendant ``hou.Node`` exactly once.
    """
    stack: List = list(reversed(root.children()))
    while stack:
        node = stack.pop()
        yield node
        # Reverse so children are visited in their natural left-to-right order.
        stack.extend(reversed(node.children()))


def find_by_type(
    root: "hou.Node",
    type_name: str,
    *,
    exact: bool = True,
) -> List["hou.Node"]:
    """Return all descendants of *root* whose node-type matches *type_name*.

    Fast path uses ``recursiveGlob`` (C++); on failure (older builds, odd node
    categories) it falls back to a Python BFS so behaviour is never broken,
    only slower -- the CLAUDE.md rule "write a fallback or raise clearly".

    Args:
        root:      Network to search beneath.
        type_name: Node type name, e.g. ``"componentgeometry"`` or
                   ``"cam"``.  Matched against ``node.type().name()``.
        exact:     If ``True``, require an exact type-name match; if ``False``,
                   match when *type_name* is a substring (handy for namespaced
                   types like ``"labs::foo::2.0"``).

    Returns:
        A list of matching nodes (possibly empty).
    """

    def _match(node: "hou.Node") -> bool:
        name = node.type().name()
        return name == type_name if exact else type_name in name

    try:
        # recursiveGlob returns a tuple of all descendants matching a pattern.
        candidates = root.recursiveGlob("*")  # type: ignore[attr-defined]
        return [n for n in candidates if _match(n)]
    except Exception:  # noqa: BLE001 -- API/version fallback
        return [n for n in iter_descendants_bfs(root) if _match(n)]


def find_first(
    root: "hou.Node",
    predicate: NodePredicate,
) -> Optional["hou.Node"]:
    """Return the first descendant satisfying *predicate*, or ``None``.

    Short-circuits on the first hit -- O(k) where k is the index of the match,
    not O(N).  Use this instead of ``find_by_type(...)[0]`` when you only need
    one node and the network is large.
    """
    for node in iter_descendants_bfs(root):
        if predicate(node):
            return node
    return None


# ---------------------------------------------------------------------------
# Input/output traversal (dataflow direction)
# ---------------------------------------------------------------------------

def walk_inputs(node: "hou.Node") -> Iterator["hou.Node"]:
    """Yield all upstream nodes feeding *node*, breadth-first, cycle-safe.

    Walks the *dataflow* graph (``node.inputs()``), not the hierarchy.  A
    ``visited`` set makes feedback loops (solver SOPs, LOP loops) terminate.

    Args:
        node: The node whose upstream dependencies to enumerate.

    Yields:
        Each distinct upstream node once (excluding *node* itself).
    """
    seen = {node}
    queue: deque = deque(i for i in node.inputs() if i is not None)
    while queue:
        cur = queue.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        yield cur
        queue.extend(i for i in cur.inputs() if i is not None)


def walk_outputs(node: "hou.Node") -> Iterator["hou.Node"]:
    """Yield all downstream nodes fed by *node*, breadth-first, cycle-safe.

    The mirror of :func:`walk_inputs`, following ``node.outputs()``.  Useful for
    impact analysis -- "what breaks if I change this node?".
    """
    seen = {node}
    queue: deque = deque(o for o in node.outputs() if o is not None)
    while queue:
        cur = queue.popleft()
        if cur in seen:
            continue
        seen.add(cur)
        yield cur
        queue.extend(o for o in cur.outputs() if o is not None)
