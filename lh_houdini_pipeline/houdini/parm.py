"""
lh_houdini_pipeline.houdini.parm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parameter get/set helpers with type coercion and batch support.

Production reasoning
--------------------
``node.parm("x").set(v)`` is fine until it isn't: the parm may not exist
(renamed across HDA versions), the value may be the wrong type, or you may want
to set twenty parms transactionally.  These helpers fail *loudly and clearly*
(per the Error-Handling rules in CLAUDE.md) and offer ``try_*`` variants that
return ``None`` on a miss instead of raising -- the pipeline's standard pattern
for non-fatal lookups.

``hou`` is imported lazily; the module imports cleanly outside Houdini.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional

if TYPE_CHECKING:
    import hou


class ParmError(ValueError):
    """Raised when a required parameter is missing or cannot be set."""


# ---------------------------------------------------------------------------
# Get
# ---------------------------------------------------------------------------

def get_parm(node: "hou.Node", name: str) -> Any:
    """Return the evaluated value of parm *name* on *node*.

    Raises:
        ParmError: If the parameter does not exist on the node.
    """
    parm = node.parm(name) or node.parmTuple(name)
    if parm is None:
        raise ParmError(
            "Parm '" + name + "' not found on " + node.path()
            + ". Existing parms: "
            + ", ".join(p.name() for p in node.parms()[:20])
        )
    return parm.eval()


def try_get_parm(node: "hou.Node", name: str, default: Any = None) -> Any:
    """Return parm *name*'s value, or *default* if the parm is absent.

    The non-fatal twin of :func:`get_parm` -- never raises.
    """
    parm = node.parm(name) or node.parmTuple(name)
    return parm.eval() if parm is not None else default


# ---------------------------------------------------------------------------
# Set
# ---------------------------------------------------------------------------

def set_parm(node: "hou.Node", name: str, value: Any) -> bool:
    """Set parm *name* on *node* to *value*.

    Handles both scalar parms (``parm``) and tuple parms (``parmTuple``)
    transparently -- pass a sequence for a tuple parm.

    Returns:
        ``True`` on success.

    Raises:
        ParmError: If the parameter does not exist.
    """
    parm = node.parm(name)
    if parm is not None:
        parm.set(value)
        return True

    ptuple = node.parmTuple(name)
    if ptuple is not None:
        ptuple.set(value)
        return True

    raise ParmError("Cannot set missing parm '" + name + "' on " + node.path())


def try_set_parm(node: "hou.Node", name: str, value: Any) -> bool:
    """Set parm *name* if it exists; return ``False`` (no raise) if it doesn't.

    Ideal for optional/advanced parms that only exist on some HDA versions.
    """
    parm = node.parm(name)
    if parm is not None:
        parm.set(value)
        return True
    ptuple = node.parmTuple(name)
    if ptuple is not None:
        ptuple.set(value)
        return True
    return False


def set_parms(node: "hou.Node", values: Mapping[str, Any], *, strict: bool = True) -> Dict[str, bool]:
    """Batch-set many parms from a ``{name: value}`` mapping.

    Args:
        node:   Target node.
        values: Mapping of parm name -> value.
        strict: If ``True``, a missing parm raises :class:`ParmError`; if
                ``False``, missing parms are skipped and reported as ``False``.

    Returns:
        A ``{name: applied?}`` report dict.
    """
    report: Dict[str, bool] = {}
    for name, value in values.items():
        if strict:
            report[name] = set_parm(node, name, value)
        else:
            report[name] = try_set_parm(node, name, value)
    return report


# ---------------------------------------------------------------------------
# Press buttons
# ---------------------------------------------------------------------------

def press_button(node: "hou.Node", name: str) -> bool:
    """Press a button/callback parm by name.

    Returns:
        ``True`` if pressed.

    Raises:
        ParmError: If the button parm is missing.
    """
    parm = node.parm(name)
    if parm is None:
        raise ParmError("Button parm '" + name + "' not found on " + node.path())
    parm.pressButton()
    return True
