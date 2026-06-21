"""
lh_houdini_pipeline.houdini.hom
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Safe wrappers around core Houdini Object Model (HOM) operations.

Provides null-safe node/parm accessors that raise descriptive errors
instead of returning None silently, plus typed helpers for common
node-navigation patterns.

Stub -- to be implemented.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    import hou


def require_node(path: str) -> "hou.Node":
    """Return the node at *path* or raise a descriptive error.

    Args:
        path: Absolute HOM path (e.g. ``"/obj/geo1"``).

    Raises:
        ValueError: If no node exists at *path*.
    """
    import hou
    node = hou.node(path)
    if node is None:
        raise ValueError(
            "Node not found: '" + path + "'. "
            "Check the path and ensure the network is loaded."
        )
    return node


def safe_node(path: str) -> Optional["hou.Node"]:
    """Return the node at *path*, or ``None`` if it does not exist."""
    import hou
    return hou.node(path)


def node_type_name(node: "hou.Node") -> str:
    """Return the node type name (e.g. ``"geo"``, ``"lop/usdimport``)."""
    return node.type().name()
