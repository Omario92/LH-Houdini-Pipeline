"""
lh_houdini_pipeline
~~~~~~~~~~~~~~~~~~~
Component-based Houdini pipeline framework.

Layer order (import dependency flows downward only):

    Core        -- pure Python utilities (no hou)
    File        -- filesystem / asset scanning (no hou)
    Houdini     -- hou-specific wrappers
    MaterialX   -- MaterialX graph building
    LookDev     -- lighting / lookdev domain
    UI          -- Qt widgets
    Interactive -- Houdini viewport states
    Tools       -- thin composition / controller layer
"""

__version__ = "0.1.0"
__author__ = "LH Pipeline"
