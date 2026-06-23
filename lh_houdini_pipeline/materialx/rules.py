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
from enum import Enum
from typing import Dict, List, Optional, Union

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


# ---------------------------------------------------------------------------
# Texture role classification (colour vs data) for .tx/.rat conversion
# ---------------------------------------------------------------------------
# This is the single source of truth used by ``materialx/tx.py`` to decide how
# ``imaketx`` should treat a texture during ``.rat`` conversion.
#
#   * COLOUR textures (albedo / base colour / diffuse / emissive / SSS colour)
#     carry sRGB-encoded *colour* and must be linearised on conversion:
#         imaketx ... -c srgb_texture scene_linear
#
#   * DATA textures (normal, roughness, metalness, displacement, bump, height,
#     mask/opacity, AO, ...) carry raw *numeric* data.  Applying a colour
#     transform to them corrupts the values -- this is exactly why a converted
#     normal map comes out "wrong" (too dark).  They must be passed through
#     untouched with an identity colour transform:
#         imaketx ... -c Raw Raw          # OCIO data/Raw -> Raw, value-preserving
#
# IMPORTANT: ``imaketx -l 0`` is NOT sufficient -- empirically (H21.0.631) it
# still linearises an 8-bit PNG (mid 0.5 -> 0.214), which darkens normals.  Only
# an explicit identity ``-c Raw Raw`` preserves the source values.  ``-c Raw Raw``
# is also idempotent, so a texture that is accidentally converted twice is not
# corrupted.
#
# NOTE: SideFX ``imaketx`` (NOT OpenImageIO ``maketx``) is the binary in use.
# It does NOT understand ``--raw`` or ``--colorconvert sRGB linear``; the
# correct equivalents are ``-c Raw Raw`` (raw passthrough) and ``-c SRC DST``.


class TextureRole(Enum):
    """Coarse role of a texture for colour-management decisions.

    Attributes:
        COLOUR: sRGB-encoded colour data -- linearise on conversion.
        DATA:   Raw numeric data (normal/rough/metal/disp/mask) -- passthrough.
    """
    COLOUR = "colour"
    DATA   = "data"


#: Channels whose pixels are sRGB-encoded *colour* and need linearisation.
#: Everything else is treated as raw DATA.
COLOUR_CHANNELS: frozenset = frozenset({
    TextureChannel.BASE_COLOR,
    TextureChannel.EMISSIVE,
    TextureChannel.SUBSURFACE_COLOR,
    TextureChannel.SPECULAR,
})


#: Lowercase string tokens that map to the COLOUR role.  Lets callers classify
#: by a free-form ``texture_type`` string (e.g. parsed from a filename) without
#: a :class:`TextureChannel` in hand.
_COLOUR_TOKENS: frozenset = frozenset({
    "color", "colour", "albedo", "base_color", "base_colour", "basecolor",
    "diffuse", "diff", "emissive", "emission", "emit",
    "subsurface_color", "subsurfacecolor", "sss_color", "specular",
})


def classify_channel(channel: TextureChannel) -> TextureRole:
    """Classify a :class:`TextureChannel` as COLOUR or DATA.

    Args:
        channel: The detected PBR channel.

    Returns:
        :attr:`TextureRole.COLOUR` for sRGB colour channels, otherwise
        :attr:`TextureRole.DATA`.  ``UNKNOWN`` falls through to ``DATA`` so an
        unrecognised map is never accidentally colour-converted.
    """
    return TextureRole.COLOUR if channel in COLOUR_CHANNELS else TextureRole.DATA


def classify_texture_type(texture_type: Union[str, TextureChannel]) -> TextureRole:
    """Classify a texture given a :class:`TextureChannel` or a string token.

    Args:
        texture_type: Either a :class:`TextureChannel`, a :class:`TextureRole`,
            or a free-form string such as ``"normal"``, ``"albedo"``,
            ``"roughness"`` or ``"base_color"``.

    Returns:
        The resolved :class:`TextureRole`.  Unknown strings default to
        :attr:`TextureRole.DATA` (safe: raw passthrough).
    """
    if isinstance(texture_type, TextureRole):
        return texture_type
    if isinstance(texture_type, TextureChannel):
        return classify_channel(texture_type)
    token = str(texture_type).strip().lower().replace("-", "_").replace(" ", "_")
    return TextureRole.COLOUR if token in _COLOUR_TOKENS else TextureRole.DATA


def get_imaketx_color_args(
    texture_type: Union[str, TextureChannel, TextureRole],
    scene_linear_token: str = "scene_linear",
    srgb_token: str = "srgb_texture",
    raw_token: str = "Raw",
) -> List[str]:
    """Return the ``imaketx`` colour-management args for a texture type.

    This is the helper requested by the pipeline brief.  It returns *imaketx*
    (SideFX) syntax -- not OpenImageIO ``maketx`` syntax::

        COLOUR -> ["-c", "srgb_texture", "scene_linear"]   # linearise
        DATA   -> ["-c", "Raw", "Raw"]                     # value-preserving

    The DATA branch uses an explicit identity transform (``-c Raw Raw``) rather
    than ``-l 0``: verified on H21.0.631, ``-l 0`` still linearises an 8-bit PNG
    and darkens normal maps, whereas ``-c Raw Raw`` preserves the source values
    exactly and is idempotent (safe against accidental double conversion).

    Args:
        texture_type:       A :class:`TextureChannel`, :class:`TextureRole`, or
            a string token (``"albedo"``, ``"normal"``, ``"roughness"`` ...).
        scene_linear_token: Target colourspace for colour textures.
        srgb_token:         Source colourspace token for colour textures.
        raw_token:          OCIO data/raw colourspace token (default ``"Raw"``).

    Returns:
        A list of ``imaketx`` arguments ready to extend a command list.
    """
    role = classify_texture_type(texture_type)
    if role is TextureRole.COLOUR:
        return ["-c", srgb_token, scene_linear_token]
    return ["-c", raw_token, raw_token]
