"""
lh_houdini_pipeline.houdini.lop
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Generic, defensive helpers for building node networks (LOPs and beyond).

This is the Houdini-layer home for the boilerplate that tool ``service``
modules kept repeating: create-or-replace a node, wire inputs, set parms that
may not exist, populate a multiparm, lay out, and find the current network.

Design
------
* Every function imports ``hou`` lazily (inside the body) so the module loads
  outside Houdini -- only *calling* a helper needs a live session.
* Helpers log-and-continue rather than raise on a missing parm / failed wire,
  so a partially-built network is inspectable instead of a hard crash.
* Pure Houdini layer: no ``materialx`` / ``ui`` / ``tools`` imports (keeps the
  layer order intact -- higher layers import this, never the reverse).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lookup / creation
# ---------------------------------------------------------------------------

def get_node(path: str) -> Optional[Any]:
    """Return ``hou.node(path)`` or ``None`` (never raises)."""
    import hou  # noqa: PLC0415
    return hou.node(path)


def create_node(
    parent: Any,
    type_name: str,
    name: Optional[str] = None,
    force: bool = False,
) -> Optional[Any]:
    """Create a child *type_name* under *parent*, optionally replacing a clash.

    Args:
        parent:    Parent ``hou.Node`` (network).
        type_name: Node type to create (e.g. ``"componentoutput"``).
        name:      Desired node name.  ``None`` lets Houdini auto-name.
        force:     If ``True`` and a same-named child exists, destroy it first;
                   otherwise Houdini yields a uniquely-numbered name.

    Returns:
        The created ``hou.Node``, or ``None`` if creation failed (logged).
    """
    if name and force:
        existing = parent.node(name)
        if existing is not None:
            _log.info("Replacing existing node: " + existing.path())
            existing.destroy()
    try:
        return parent.createNode(type_name, name) if name else parent.createNode(type_name)
    except Exception as exc:  # noqa: BLE001
        label = name or type_name
        _log.error("Failed to create '" + label + "' (" + type_name + "): " + str(exc))
        return None


def find_or_create(parent: Any, type_name: str, name: str) -> Optional[Any]:
    """Return *parent*'s child *name* if it's of *type_name*, else create it.

    Args:
        parent:    Parent ``hou.Node``.
        type_name: Required node type of the child.
        name:      Child name to find or create.

    Returns:
        The found or newly-created ``hou.Node`` (``None`` on create failure).
    """
    existing = parent.node(name)
    if existing is not None and existing.type().name() == type_name:
        _log.debug("Reusing node: " + existing.path())
        return existing
    return create_node(parent, type_name, name)


# ---------------------------------------------------------------------------
# Wiring
# ---------------------------------------------------------------------------

def connect(dst: Any, src: Any, input_index: int = 0, output_index: int = 0) -> bool:
    """Wire ``src`` output into ``dst`` input *input_index* (by index).

    Index wiring is correct for LOP/SOP nodes whose inputs are positional
    (input 0 = stage, input 1 = materials, ...).  For VOP shader inputs that
    have stable *names*, use ``materialx.connection.set_named_input`` instead.

    Args:
        dst:          Destination ``hou.Node``.
        src:          Source ``hou.Node``.
        input_index:  Input slot on *dst*.
        output_index: Output slot on *src*.

    Returns:
        ``True`` on success, ``False`` on failure (logged).
    """
    try:
        dst.setInput(input_index, src, output_index)
        return True
    except Exception as exc:  # noqa: BLE001
        _log.error(
            "connect failed: " + src.path() + " -> " + dst.path()
            + "[" + str(input_index) + "]: " + str(exc)
        )
        return False


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

def set_parm(node: Any, parm_name: str, value: Any) -> bool:
    """Set ``parm_name`` on *node* only if it exists.

    Args:
        node:      Target ``hou.Node``.
        parm_name: Parameter name.
        value:     Value to assign.

    Returns:
        ``True`` if set, ``False`` if the parm is absent or the set failed.
    """
    parm = node.parm(parm_name)
    if parm is None:
        _log.debug("Parm not found, skipping: " + node.path() + "." + parm_name)
        return False
    try:
        parm.set(value)
        return True
    except Exception as exc:  # noqa: BLE001
        _log.warning("Failed to set " + node.path() + "." + parm_name + ": " + str(exc))
        return False


def set_parms(node: Any, values: Dict[str, Any]) -> int:
    """Set several parms from a ``{name: value}`` mapping.

    Args:
        node:   Target ``hou.Node``.
        values: Mapping of parm name to value.

    Returns:
        The number of parms successfully set.
    """
    return sum(1 for name, val in values.items() if set_parm(node, name, val))


def set_indexed_parms(
    node: Any,
    count_parm: str,
    rows: List[Dict[str, Any]],
) -> None:
    """Populate a multiparm: set its count, then ``<base><i>`` for each row.

    Example -- componentmaterial bindings::

        set_indexed_parms(cm, "nummaterials", [
            {"primpattern": "%type:Mesh", "matspecpath": "/materials/hero"},
        ])
    sets ``nummaterials=1``, ``primpattern1``, ``matspecpath1``.

    Args:
        node:       Target ``hou.Node``.
        count_parm: Name of the multiparm count parameter.
        rows:       One dict per instance; keys are the per-instance parm base
                    names (the 1-based index is appended automatically).
    """
    if not set_parm(node, count_parm, len(rows)):
        _log.warning("Multiparm count '" + count_parm + "' missing on " + node.path())
        return
    for i, row in enumerate(rows, start=1):
        for base, val in row.items():
            set_parm(node, base + str(i), val)


def press_button(node: Any, candidates: Iterable[str]) -> Optional[str]:
    """Press the first existing button parm from *candidates*.

    Args:
        node:       Target ``hou.Node``.
        candidates: Button parm names to try in order (e.g.
                    ``("execute", "savetodisk")``).

    Returns:
        The name of the button pressed, or ``None`` if none existed.
    """
    for name in candidates:
        parm = node.parm(name)
        if parm is not None:
            parm.pressButton()
            _log.debug("Pressed " + node.path() + "." + name)
            return name
    _log.warning("No button found on " + node.path() + " among: " + ", ".join(candidates))
    return None


# ---------------------------------------------------------------------------
# Layout / session
# ---------------------------------------------------------------------------

def layout(node: Any) -> None:
    """Lay out *node*'s children, ignoring failures (e.g. headless)."""
    try:
        node.layoutChildren()
    except Exception as exc:  # noqa: BLE001
        _log.debug("layoutChildren skipped on " + node.path() + ": " + str(exc))


def network_pwd() -> Optional[Any]:
    """Return the node shown in the current Network Editor pane, or ``None``.

    Best-effort -- returns ``None`` in headless ``hython`` or when no network
    editor is open.
    """
    import hou  # noqa: PLC0415
    try:
        editors = [
            p for p in hou.ui.paneTabs()
            if p.type() == hou.paneTabType.NetworkEditor
        ]
        if editors:
            return editors[0].pwd()
    except Exception as exc:  # noqa: BLE001
        _log.debug("No network editor pane: " + str(exc))
    return None
