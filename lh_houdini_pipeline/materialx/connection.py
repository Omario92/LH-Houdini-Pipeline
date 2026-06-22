"""
lh_houdini_pipeline.materialx.connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Low-level node connection helpers for MaterialX VOP networks.

This module is the *only* place in the MaterialX layer that touches the
``hou`` API for wiring nodes together.  Every function imports ``hou`` lazily
(inside the function body) so the module stays importable outside Houdini --
``materialx/builder.py`` plans networks without needing these calls.

Design goals
------------
* Connect by **named input**, never by raw port index, wherever Houdini
  exposes input names (``setNamedInput``).  The single exception is the
  ``subnetconnector`` input, which has only one slot -- documented inline.
* Defensive: every helper checks that the node / parm / input actually
  exists and logs (rather than raises) on a miss, returning a status flag.
  A half-built material is easier to debug than a hard crash mid-build.

.. note::
   Node-type and port names (``mtlximage``, output ``"out"``, connector
   ``parmtype`` tokens, etc.) are validated against Houdini 19.5 / 20.x
   Karma MaterialX.  If your build differs, these are the wrappers to adjust
   -- the planning layer above is version-independent.
"""

from __future__ import annotations

from typing import Any, Optional

from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)


def set_parm_if_exists(node: Any, parm_name: str, value: Any) -> bool:
    """Set ``parm_name`` on *node* to *value* only if that parm exists.

    Args:
        node:      A ``hou.Node`` instance.
        parm_name: Parameter name to set.
        value:     Value to assign (str / float / int).

    Returns:
        ``True`` if the parm existed and was set, ``False`` otherwise.
    """
    parm = node.parm(parm_name)
    if parm is None:
        _log.debug("Parm not found, skipping: " + node.path() + "." + parm_name)
        return False
    try:
        parm.set(value)
        return True
    except Exception as exc:  # noqa: BLE001 - report and continue, never crash a build
        _log.warning(
            "Failed to set parm " + node.path() + "." + parm_name + ": " + str(exc)
        )
        return False


def set_named_input(
    dst: Any,
    input_name: str,
    src: Any,
    output_name: str = "out",
) -> bool:
    """Connect ``src.<output_name>`` into ``dst.<input_name>`` by name.

    Uses ``hou.Node.setNamedInput`` so the connection is robust to port
    re-ordering between Houdini versions.

    Args:
        dst:         Destination ``hou.Node`` (the consumer).
        input_name:  Named input on *dst* (e.g. ``"base_color"``, ``"normal"``).
        src:         Source ``hou.Node`` (the producer).
        output_name: Named output on *src*.  Defaults to ``"out"`` which is the
                     standard single output of ``mtlx*`` VOP nodes.

    Returns:
        ``True`` on a successful connection, ``False`` if the input or output
        name was not found (logged, not raised).
    """
    if not _has_named_input(dst, input_name):
        _log.warning(
            "Input '" + input_name + "' not found on " + dst.path()
            + " -- skipping connection from " + src.path()
        )
        return False
    try:
        dst.setNamedInput(input_name, src, output_name)
        _log.debug(
            "Connected " + src.path() + "[" + output_name + "] -> "
            + dst.path() + "[" + input_name + "]"
        )
        return True
    except Exception as exc:  # noqa: BLE001
        _log.warning(
            "setNamedInput failed (" + input_name + "): " + str(exc)
            + " -- retrying with output index 0"
        )
        # Fallback: some node outputs are unnamed; connect output index 0.
        try:
            dst.setNamedInput(input_name, src, 0)
            return True
        except Exception as exc2:  # noqa: BLE001
            _log.error("Connection fully failed: " + str(exc2))
            return False


def connect_to_output_index(
    dst: Any, input_index: int, src: Any, src_output: int = 0
) -> bool:
    """Connect by raw index -- only for single-input nodes like subnetconnector.

    ``subnetconnector`` exposes exactly one input ('Connector Input') with no
    stable public name across versions, so an index connection is intentional
    here.  Documented separately from :func:`set_named_input` so the index use
    is explicit and greppable.

    Args:
        dst:         Destination ``hou.Node``.
        input_index: Input slot index on *dst* (almost always ``0``).
        src:         Source ``hou.Node``.
        src_output:  Output slot index on *src*.

    Returns:
        ``True`` on success, ``False`` on failure (logged).
    """
    try:
        dst.setInput(input_index, src, src_output)
        return True
    except Exception as exc:  # noqa: BLE001
        _log.error(
            "setInput(" + str(input_index) + ") failed on " + dst.path()
            + ": " + str(exc)
        )
        return False


def create_output_connector(
    subnet: Any,
    parm_name: str,
    parm_type: str,
    src: Any,
    src_output: str = "out",
    label: Optional[str] = None,
) -> Optional[Any]:
    """Create a ``subnetconnector`` output on *subnet* fed by *src*.

    This is what turns a plain VOP subnet into a USD material: a connector of
    ``parmtype`` ``surface`` (or ``displacement``) becomes the material's
    terminal output.

    Args:
        subnet:     The container ``hou.Node`` (a VOP ``subnet``).
        parm_name:  Output name, e.g. ``"surface"`` or ``"displacement"``.
        parm_type:  VOP type token for the connector (``"surface"`` /
                    ``"displacement"``).
        src:        Shader node whose output feeds this connector.
        src_output: Named output on *src* (default ``"out"``).
        label:      UI label; defaults to a title-cased *parm_name*.

    Returns:
        The created connector ``hou.Node``, or ``None`` on failure.
    """
    try:
        conn = subnet.createNode("subnetconnector", parm_name + "_output")
    except Exception as exc:  # noqa: BLE001
        _log.error("Could not create subnetconnector: " + str(exc))
        return None

    set_parm_if_exists(conn, "connectorkind", "output")
    set_parm_if_exists(conn, "parmname", parm_name)
    set_parm_if_exists(conn, "parmlabel", label or parm_name.replace("_", " ").title())
    set_parm_if_exists(conn, "parmtype", parm_type)

    # subnetconnector has a single input -- index connection is intentional.
    connect_to_output_index(conn, 0, src, _output_index(src, src_output))
    return conn


# ---------------------------------------------------------------------------
# Internal introspection helpers
# ---------------------------------------------------------------------------

def _has_named_input(node: Any, input_name: str) -> bool:
    """Return ``True`` if *node* exposes an input called *input_name*."""
    try:
        return input_name in node.inputNames()
    except Exception:  # noqa: BLE001 - older API / odd node, assume present
        return True


def _output_index(node: Any, output_name: str) -> int:
    """Resolve a named output to its index, defaulting to 0 on any miss."""
    try:
        names = node.outputNames()
        if output_name in names:
            return names.index(output_name)
    except Exception:  # noqa: BLE001
        pass
    return 0
