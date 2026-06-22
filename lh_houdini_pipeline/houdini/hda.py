"""
lh_houdini_pipeline.houdini.hda
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
HDA definition inspection, installation, packaging, and management.

This module provides clean, defensive programmatic wrappers for packaging
Houdini Digital Assets (HDAs), including defining dynamic parameter templates,
writing HDA python modules, and setting up event script handlers.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from lh_houdini_pipeline.core.logger import get_logger

_log = get_logger(__name__)


def create_hda_from_subnet(
    subnet_node: Any,
    hda_path: str,
    asset_name: str,
    asset_label: Optional[str] = None,
) -> Optional[Any]:
    """Create a new HDA from a subnet node, save and install it.

    Args:
        subnet_node: The subnet-like ``hou.Node`` to package.
        hda_path:    The destination file path for the HDA (e.g. ``.hda``).
        asset_name:  The unique name for the HDA node type (e.g. ``"my_tool"``).
        asset_label: The user-facing label.  Defaults to name capitalized.

    Returns:
        The ``hou.HDADefinition`` for the created HDA, or ``None`` if failed.
    """
    import hou  # noqa: PLC0415
    try:
        # Ensure directories exist
        os.makedirs(os.path.dirname(os.path.abspath(hda_path)), exist_ok=True)

        # Remove existing file if it exists to allow fresh creation
        if os.path.exists(hda_path):
            try:
                os.remove(hda_path)
            except Exception as exc:  # noqa: BLE001
                _log.warning(f"Could not remove existing HDA file {hda_path}: {exc}")

        label = asset_label or asset_name.replace("_", " ").title()
        
        # Convert the subnet into a digital asset
        hda_node = subnet_node.createDigitalAsset(
            name=asset_name,
            hda_file_name=hda_path,
            description=label,
            change_node_type=True,
        )
        
        definition = hda_node.type().definition()
        _log.info(f"Successfully created HDA '{asset_name}' at {hda_path}")
        return definition
    except Exception as exc:  # noqa: BLE001
        _log.error(f"Failed to create HDA from subnet: {exc}")
        return None


def set_hda_section(definition: Any, section_name: str, contents: str) -> bool:
    """Add or update a text section inside the HDA definition.

    Args:
        definition:   The ``hou.HDADefinition`` of the asset.
        section_name: The name of the section (e.g. ``"PythonModule"`` or ``"OnCreated"``).
        contents:     The text contents to save in the section.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    try:
        if definition.hasSection(section_name):
            section = definition.sections()[section_name]
            section.setContents(contents)
        else:
            definition.addSection(section_name, contents)
        _log.info(f"Set section '{section_name}' contents in HDA {definition.nodeTypeName()}")
        return True
    except Exception as exc:  # noqa: BLE001
        _log.error(f"Failed to set section '{section_name}' on HDA: {exc}")
        return False


def set_hda_python_module(definition: Any, code: str) -> bool:
    """Set the PythonModule section in the HDA definition.

    This automatically configures the extra file options so Houdini knows
    the section is a Python script.

    Args:
        definition: The ``hou.HDADefinition`` of the asset.
        code:       The python code string.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    ok = set_hda_section(definition, "PythonModule", code)
    if ok:
        try:
            definition.setExtraFileOption("PythonModule/IsPython", True)
            definition.setExtraFileOption("PythonModule/IsScript", True)
            definition.setExtraFileOption("PythonModule/IsExpr", False)
        except Exception as exc:  # noqa: BLE001
            _log.warning(f"Failed to set extra file options for PythonModule: {exc}")
    return ok


def set_hda_event_script(definition: Any, event_name: str, code: str) -> bool:
    """Set an event handler script in the HDA definition (e.g. OnCreated, OnLoaded).

    This automatically configures the extra file options so Houdini runs the
    event handler as a Python script instead of the default Hscript.

    Args:
        definition: The ``hou.HDADefinition`` of the asset.
        event_name: The event handler name (e.g. ``"OnCreated"``, ``"OnLoaded"``).
        code:       The Python script code.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    ok = set_hda_section(definition, event_name, code)
    if ok:
        try:
            definition.setExtraFileOption(f"{event_name}/IsPython", True)
            definition.setExtraFileOption(f"{event_name}/IsScript", True)
            definition.setExtraFileOption(f"{event_name}/IsExpr", False)
        except Exception as exc:  # noqa: BLE001
            _log.warning(f"Failed to set extra file options for event script '{event_name}': {exc}")
    return ok


def set_hda_parm_template_group(definition: Any, parm_group: Any) -> bool:
    """Set the parameter template group (layout) on the HDA definition.

    Args:
        definition: The ``hou.HDADefinition`` of the asset.
        parm_group: The ``hou.ParmTemplateGroup`` object defining the UI.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    try:
        definition.setParmTemplateGroup(parm_group)
        _log.info(f"Updated Parameter Template Group for HDA {definition.nodeTypeName()}")
        return True
    except Exception as exc:  # noqa: BLE001
        _log.error(f"Failed to set parameter template group on HDA: {exc}")
        return False


def save_and_reload_hda(definition: Any, template_node: Optional[Any] = None) -> bool:
    """Save HDA changes to the library file and reload it in the session.

    Args:
        definition:    The ``hou.HDADefinition`` to save.
        template_node: Optional ``hou.Node`` to serialize contents from.

    Returns:
        ``True`` if successful, ``False`` otherwise.
    """
    import hou  # noqa: PLC0415
    try:
        hda_path = definition.libraryFilePath()
        definition.save(hda_path, template_node)
        hou.hda.reloadFile(hda_path)
        _log.info(f"Saved and reloaded HDA at {hda_path}")
        return True
    except Exception as exc:  # noqa: BLE001
        _log.error(f"Failed to save and reload HDA: {exc}")
        return False
