"""
lh_houdini_pipeline.file
~~~~~~~~~~~~~~~~~~~~~~~~~
Filesystem and asset-scanning layer.  No ``hou`` imports anywhere in this package.
"""

from lh_houdini_pipeline.file.texture_parser import TextureParser, TextureInfo, TextureChannel, ColorSpace, UDIMMode
from lh_houdini_pipeline.file.versioning import VersionResolver, Version, VersionedFile, VersionFormat

__all__ = [
    "TextureParser",
    "TextureInfo",
    "TextureChannel",
    "ColorSpace",
    "UDIMMode",
    "VersionResolver",
    "Version",
    "VersionedFile",
    "VersionFormat",
]
