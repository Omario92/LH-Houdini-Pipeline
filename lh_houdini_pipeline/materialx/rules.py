"""
lh_houdini_pipeline.materialx.rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Channel-to-MaterialX-port mapping rules.

This module is the single source of truth for:

    * Which TextureChannel maps to which MaterialX input port name
    * Which colorspace token to apply per channel
    * Which MaterialX node signature to use (image vs tiledimage)
    * The target shader type (UsdPreviewSurface, StandardSurface, etc.)

The ``CHANNEL_RULES`` dict is consumed by ``materialx/builder.py`` when
constructing texture networks automatically from ``TextureInfo`` objects.

Design: plain data (dicts + dataclasses), no hou imports, easy to test.

Stub -- mapping table to be expanded.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from lh_houdini_pipeline.file.texture_parser import TextureChannel, ColorSpace


@dataclass(frozen=True)
class ChannelRule:
    """Mapping rule for a single texture channel.

    Attributes:
        mtlx_input:    MaterialX input port name on the shader node.
        colorspace:    Colorspace token to write into the image node.
        signature:     MaterialX image node signature (``"filename"`` for
                       single, ``"tiledimage"`` for UDIM).
        scale:         Optional multiplicative scale applied to the channel
                       (useful for normal map remapping 0-1 → -1 to 1).
        invert:        Whether to invert the channel value.
        fallback:      Default value when no texture is connected.
    """
    mtlx_input: str
    colorspace:  str           = "raw"
    signature:   str           = "filename"
    scale:       Optional[float] = None
    invert:      bool          = False
    fallback:    Optional[str] = None


# ---------------------------------------------------------------------------
# StandardSurface channel rules
# ---------------------------------------------------------------------------

STANDARD_SURFACE_RULES: Dict[TextureChannel, ChannelRule] = {
    TextureChannel.BASE_COLOR: ChannelRule(
        mtlx_input="base_color",
        colorspace="srgb_texture",
        fallback="0.8, 0.8, 0.8, 1.0",
    ),
    TextureChannel.METALNESS: ChannelRule(
        mtlx_input="metalness",
        colorspace="raw",
        fallback="0.0",
    ),
    TextureChannel.ROUGHNESS: ChannelRule(
        mtlx_input="specular_roughness",
        colorspace="raw",
        fallback="0.5",
    ),
    TextureChannel.NORMAL: ChannelRule(
        mtlx_input="normal",
        colorspace="raw",
        signature="filename",
    ),
    TextureChannel.EMISSIVE: ChannelRule(
        mtlx_input="emission_color",
        colorspace="srgb_texture",
        fallback="0.0, 0.0, 0.0",
    ),
    TextureChannel.OPACITY: ChannelRule(
        mtlx_input="opacity",
        colorspace="raw",
        fallback="1.0",
    ),
    TextureChannel.DISPLACEMENT: ChannelRule(
        mtlx_input="displacement",
        colorspace="raw",
    ),
    TextureChannel.SUBSURFACE_COLOR: ChannelRule(
        mtlx_input="subsurface_color",
        colorspace="srgb_texture",
    ),
    TextureChannel.COAT: ChannelRule(
        mtlx_input="coat",
        colorspace="raw",
    ),
    TextureChannel.COAT_ROUGHNESS: ChannelRule(
        mtlx_input="coat_roughness",
        colorspace="raw",
    ),
    TextureChannel.SHEEN: ChannelRule(
        mtlx_input="sheen",
        colorspace="raw",
    ),
    TextureChannel.TRANSMISSION: ChannelRule(
        mtlx_input="transmission",
        colorspace="raw",
    ),
}

# Default rule set (swap this to target a different shader)
CHANNEL_RULES = STANDARD_SURFACE_RULES


def get_rule(channel: TextureChannel) -> Optional[ChannelRule]:
    """Return the :class:`ChannelRule` for *channel*, or ``None`` if unknown."""
    return CHANNEL_RULES.get(channel)
