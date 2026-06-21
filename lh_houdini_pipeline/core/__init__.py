"""
lh_houdini_pipeline.core
~~~~~~~~~~~~~~~~~~~~~~~~~
Pure-Python foundation layer.  No ``hou`` imports anywhere in this package.

Public re-exports for convenience:

    from lh_houdini_pipeline.core import get_logger, PathResolver, Config
"""

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.core.path import PathResolver, PathTemplate, normalize
from lh_houdini_pipeline.core.config import Config, ConfigManager, ConfigLoader

__all__ = [
    "get_logger",
    "PathResolver",
    "PathTemplate",
    "normalize",
    "Config",
    "ConfigManager",
    "ConfigLoader",
]
