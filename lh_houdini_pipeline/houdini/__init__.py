"""
lh_houdini_pipeline.houdini
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Houdini-specific wrappers.  All ``hou`` imports are contained here.

Modules:
    env      -- $HIP / $JOB / $HFS environment helpers
    hom      -- safe hou.node / hou.parm access wrappers
    parm     -- parameter get/set with type coercion
    hda      -- HDA definition inspection and management
    animation -- channel / keyframe utilities
    usd      -- LOP / USD stage helpers
    lop      -- LOPs network builder helpers
    geometry -- SOP geometry inspection
"""
