"""
lh_houdini_pipeline.tools.houdini_ai_assistant.core.context_formatter
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure Python module to format raw extracted scene context data into a
highly token-efficient, clear, and structured Markdown context block.

Does not import 'hou'.
"""

from __future__ import annotations

from typing import Any, Dict, List


def format_scene_context(context_data: Dict[str, Any]) -> str:
    """Format raw scene context dictionaries into token-efficient Markdown.

    Args:
        context_data: Raw dictionaries returned by get_full_scene_context().

    Returns:
        A Markdown string.
    """
    md = []
    md.append("## HOUDINI SCENE CONTEXT OVERVIEW")
    md.append(f"- **Active Layout/Desktop**: {context_data.get('desktop', 'Unknown')}")
    md.append(f"- **Current Network path**: `{context_data.get('network_path', '/')}`")
    md.append("")

    selected_nodes = context_data.get("selected_nodes", [])
    if not selected_nodes:
        md.append("> [!NOTE]")
        md.append("> No nodes are currently selected. The assistant is focused on the active network path listed above.")
        return "\n".join(md)

    md.append(f"### Selected Nodes ({len(selected_nodes)}):")
    md.append("")

    for node in selected_nodes:
        path = node.get("path", "")
        name = node.get("name", "")
        type_name = node.get("type", "")
        
        md.append(f"#### Node: `{name}` (Type: `{type_name}`)")
        md.append(f"- **Path**: `{path}`")
        
        # Connections
        inputs = node.get("inputs", [])
        if inputs:
            conns = [f"Input {conn['index']} ({conn['input_name']}) connected to `{conn['connected_to']}`" for conn in inputs]
            md.append("- **Inputs**:")
            for c in conns:
                md.append(f"  - {c}")
        
        outputs = node.get("outputs", [])
        if outputs:
            conns = [f"Output {conn['index']} connects to `{conn['connected_to']}`" for conn in outputs]
            # Truncate outputs if too many
            if len(conns) > 5:
                conns = conns[:5] + [f"... and {len(conns) - 5} more outputs"]
            md.append("- **Outputs**:")
            for c in conns:
                md.append(f"  - {c}")

        # Errors & Warnings
        errors = node.get("errors", "")
        if errors:
            md.append(f"- **ERRORS**:\n```\n{errors.strip()}\n```")
        
        warnings = node.get("warnings", "")
        if warnings:
            md.append(f"- **WARNINGS**:\n```\n{warnings.strip()}\n```")

        # Geometry Attributes & Groups
        geom = node.get("geometry", {})
        if geom:
            md.append(f"- **Geometry Info**: {geom.get('points_count', 0)} points, {geom.get('prims_count', 0)} primitives")
            attribs = geom.get("attributes", {})
            active_attribs = []
            for attr_type, attr_names in attribs.items():
                if attr_names:
                    active_attribs.append(f"{attr_type}: `{', '.join(attr_names)}`")
            if active_attribs:
                md.append("  - **Attributes**:")
                for attr_str in active_attribs:
                    md.append(f"    - {attr_str}")
            
            groups = geom.get("groups", {})
            active_groups = []
            for grp_type, grp_names in groups.items():
                if grp_names:
                    active_groups.append(f"{grp_type}: `{', '.join(grp_names)}`")
            if active_groups:
                md.append("  - **Groups**:")
                for grp_str in active_groups:
                    md.append(f"    - {grp_str}")

        # USD Info
        usd = node.get("usd", {})
        if usd:
            active_layer = usd.get("active_layer", "Anonymous")
            md.append(f"- **USD Active Layer**: `{active_layer}`")
            root_prims = usd.get("root_prims", [])
            if root_prims:
                md.append(f"  - **Root Prims**: `{', '.join(root_prims)}`")

        # Parameter Expressions
        expressions = node.get("expressions", [])
        if expressions:
            md.append("- **Active Parameter Expressions**:")
            for expr in expressions:
                md.append(f"  - `{expr['name']}` ({expr['label']}) = `{expr['expression']}`  (evaluates to `{expr['value']}`)")

        # Modified Parameters (limit to 10 to save tokens, only list if non-empty)
        modified = node.get("modified_parms", {})
        if modified:
            md.append("- **Modified Parameters (Non-Default)**:")
            keys = sorted(modified.keys())
            truncated = len(keys) > 10
            display_keys = keys[:10]
            for k in display_keys:
                p_info = modified[k]
                md.append(f"  - `{k}` ({p_info['label']}) = `{p_info['value']}`")
            if truncated:
                md.append(f"  - *... and {len(keys) - 10} more modified parameters*")
        
        md.append("") # spacer

    return "\n".join(md).strip()
