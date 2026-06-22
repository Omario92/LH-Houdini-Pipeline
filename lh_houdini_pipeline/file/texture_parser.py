"""
lh_houdini_pipeline.file.texture_parser
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Parse texture filenames into structured metadata.

Handles common naming conventions produced by:
    * Substance Painter  (hero_car_BaseColor_1001.exr, hero_car_Normal_1001.exr)
    * Mari               (hero_car_diff.1001.exr, hero_car_diff.<UDIM>.exr)
    * Hand-rolled pipelines (various separators and abbreviations)

Design
------
* ``TextureChannel``  -- enum of known PBR/LookDev channels
* ``ColorSpace``      -- enum of rendering colorspaces
* ``UDIMMode``        -- enum of tiling / sequence conventions
* ``TextureInfo``     -- frozen dataclass carrying all extracted metadata
* ``TextureParser``   -- configurable parser; one instance, many parses

Pure Python -- no ``hou`` imports.

Channel detection uses an ordered list of ``(pattern, channel)`` rules.
The first regex match wins, making the precedence explicit and easy to
override per project.

Colorspace is *inferred* from channel type via a configurable mapping.
This feeds directly into the MaterialX rules layer (``materialx/rules.py``).

Example
-------
::

    from lh_houdini_pipeline.file.texture_parser import TextureParser

    parser = TextureParser()
    info = parser.parse("/jobs/darkStar/tex/hero_car_BaseColor_1001.exr")

    info.channel      # TextureChannel.BASE_COLOR
    info.colorspace   # ColorSpace.SRGB
    info.udim_mode    # UDIMMode.MARI
    info.udim_token   # "1001"
    info.raw_name     # "hero_car_basecolor"
    info.is_tiled     # True
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

PathLike = Union[str, Path]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TextureChannel(Enum):
    """Known PBR and LookDev texture channels."""
    BASE_COLOR        = "baseColor"
    METALNESS         = "metalness"
    ROUGHNESS         = "roughness"
    SPECULAR          = "specular"
    NORMAL            = "normal"
    BUMP              = "bump"
    DISPLACEMENT      = "displacement"
    EMISSIVE          = "emissive"
    OPACITY           = "opacity"
    AO                = "ambientOcclusion"
    SUBSURFACE_COLOR  = "subsurfaceColor"
    SUBSURFACE_RADIUS = "subsurfaceRadius"
    COAT              = "coat"
    COAT_ROUGHNESS    = "coatRoughness"
    COAT_NORMAL       = "coatNormal"
    SHEEN             = "sheen"
    TRANSMISSION      = "transmission"
    UNKNOWN           = "unknown"


class ColorSpace(Enum):
    """Rendering colorspace for a texture map."""
    SRGB   = "sRGB"      # colour data: BaseColor, Emissive, SubsurfaceColor
    LINEAR = "linear"    # linear float data
    RAW    = "raw"       # non-colour: roughness, metalness, normal, masks
    ACESCG = "ACEScg"    # scene-linear ACEScg


class UDIMMode(Enum):
    """Convention used to encode UDIM tile numbers in the filename."""
    NONE      = "none"       # single texture, no tiling
    MARI      = "mari"       # literal 4-digit tile: 1001, 1002, ...
    MUDBOX    = "mudbox"     # _u0_v0, _u1_v0, ...
    HOUDINI   = "houdini"    # <UDIM> token
    SUBSTANCE = "substance"  # %(UDIM)d token
    SEQUENCE  = "sequence"   # frame sequence: ####, %04d


# ---------------------------------------------------------------------------
# Channel detection patterns
# ---------------------------------------------------------------------------
# List of (compiled_regex, TextureChannel) tuples.
# Evaluated in order; first match wins.
# All patterns are case-insensitive and match against the filename stem.

_RAW_PATTERNS: List[Tuple[str, TextureChannel]] = [
    # Base color (must come before generic 'col' catch-all)
    (r"\b(base[_\-]?col(?:ou?r)?|albedo|diffuse|diff|col)\b",     TextureChannel.BASE_COLOR),
    # Metalness
    (r"\b(metal(?:ness|lic|ic)?|mtl)\b",                           TextureChannel.METALNESS),
    # Roughness
    (r"\b(rough(?:ness)?|rgh)\b",                                  TextureChannel.ROUGHNESS),
    # Specular
    (r"\b(spec(?:ular)?)\b",                                       TextureChannel.SPECULAR),
    # Normal
    (r"\b(nrm|nml|normal[_\-]?(?:map)?|nor)\b",                   TextureChannel.NORMAL),
    # Bump
    (r"\b(bump|bmp)\b",                                            TextureChannel.BUMP),
    # Displacement / Height
    (r"\b(disp(?:lacement)?|height|hgt)\b",                       TextureChannel.DISPLACEMENT),
    # Emissive
    (r"\b(emiss(?:ive)?|emit|glow)\b",                             TextureChannel.EMISSIVE),
    # Opacity / Alpha / Mask
    (r"\b(opac(?:ity)?|alpha|mask|transparency)\b",                TextureChannel.OPACITY),
    # Ambient Occlusion
    (r"\b(ao|ambient[_\-]?occ(?:lusion)?|occ(?:lusion)?)\b",      TextureChannel.AO),
    # Subsurface color (check before bare 'sss')
    (r"\b(sss[_\-]?col(?:ou?r)?|subsurface[_\-]?col(?:ou?r)?)\b", TextureChannel.SUBSURFACE_COLOR),
    # Subsurface radius
    (r"\b(sss[_\-]?radius|subsurface[_\-]?radius)\b",             TextureChannel.SUBSURFACE_RADIUS),
    # Coat roughness (check before bare 'coat')
    (r"\b(coat[_\-]?rough(?:ness)?)\b",                            TextureChannel.COAT_ROUGHNESS),
    # Coat normal (check before bare 'coat')
    (r"\b(coat[_\-]?nrm|coat[_\-]?normal)\b",                     TextureChannel.COAT_NORMAL),
    # Coat
    (r"\b(coat(?:ing)?)\b",                                        TextureChannel.COAT),
    # Sheen
    (r"\b(sheen)\b",                                               TextureChannel.SHEEN),
    # Transmission
    (r"\b(trans(?:mission)?|ior)\b",                               TextureChannel.TRANSMISSION),
]

CHANNEL_PATTERNS: List[Tuple[re.Pattern, TextureChannel]] = [  # type: ignore[type-arg]
    (re.compile(pat, re.IGNORECASE), ch)
    for pat, ch in _RAW_PATTERNS
]

# Default colorspace inference from channel type.
# Channels not listed here default to ColorSpace.RAW.
DEFAULT_COLORSPACE: Dict[TextureChannel, ColorSpace] = {
    TextureChannel.BASE_COLOR:       ColorSpace.SRGB,
    TextureChannel.EMISSIVE:         ColorSpace.SRGB,
    TextureChannel.SUBSURFACE_COLOR: ColorSpace.SRGB,
    TextureChannel.SPECULAR:         ColorSpace.SRGB,
}


# ---------------------------------------------------------------------------
# UDIM / tile detection
# ---------------------------------------------------------------------------
# Each entry: (compiled_regex, UDIMMode, static_token_or_empty)
# When static_token is empty, the matched text itself is used as the token.

_UDIM_PATTERNS: List[Tuple[re.Pattern, UDIMMode, str]] = [  # type: ignore[type-arg]
    # Houdini explicit token  <UDIM>
    (re.compile(r"<UDIM>", re.IGNORECASE),        UDIMMode.HOUDINI,   "<UDIM>"),
    # Houdini hash notation  #### (4+ hashes = UDIM tile, not a frame sequence)
    (re.compile(r"#{4,}"),                         UDIMMode.HOUDINI,   "####"),
    # Substance token  %(UDIM)d
    (re.compile(r"%\(UDIM\)d", re.IGNORECASE),    UDIMMode.SUBSTANCE, "%(UDIM)d"),
    # Mudbox  _u0_v0
    (re.compile(r"_u\d+_v\d+", re.IGNORECASE),   UDIMMode.MUDBOX,    ""),
    # Frame sequence  %04d / %d style (NOT ####, which is handled above)
    (re.compile(r"%0?\d*d"),                       UDIMMode.SEQUENCE,  ""),
    # Mari literal tile 10xx (4-digit, not part of a larger number)
    (re.compile(r"(?<!\d)(10\d{2})(?!\d)"),       UDIMMode.MARI,      ""),
]


# ---------------------------------------------------------------------------
# TextureInfo
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TextureInfo:
    """All metadata extracted from a single texture filename.

    Attributes:
        path:        Resolved (or as-given) ``pathlib.Path`` for this texture.
        stem:        Filename without extension (original, not cleaned).
        extension:   Lowercase extension without leading dot (e.g. ``"exr"``).
        channel:     Detected PBR channel enum value.
        colorspace:  Inferred colorspace for this channel.
        udim_mode:   Tiling / sequence convention found in the filename.
        udim_token:  The matched UDIM substring (``"1001"``, ``"<UDIM>"``, etc.)
                     Empty string when ``udim_mode`` is ``NONE``.
        raw_name:    Stem with UDIM token and trailing noise removed,
                     lowercased.  Useful as a MaterialX node label.
        warnings:    Non-fatal issues noticed during parsing.
    """
    path:       Path
    stem:       str
    extension:  str
    channel:    TextureChannel
    colorspace: ColorSpace
    udim_mode:  UDIMMode
    udim_token: str
    raw_name:   str
    warnings:   Tuple[str, ...] = field(default_factory=tuple)

    @property
    def filename(self) -> str:
        """Full filename including extension."""
        return self.path.name

    @property
    def houdini_path(self) -> str:
        """Forward-slash path string (USD / Houdini compatible)."""
        return self.path.as_posix()

    @property
    def is_tiled(self) -> bool:
        """True if this texture uses any UDIM tiling convention."""
        return self.udim_mode not in {UDIMMode.NONE, UDIMMode.SEQUENCE}

    @property
    def is_sequence(self) -> bool:
        """True if this is a frame sequence rather than a static texture."""
        return self.udim_mode == UDIMMode.SEQUENCE


# ---------------------------------------------------------------------------
# TextureParser
# ---------------------------------------------------------------------------

class TextureParser:
    """Parse texture filenames into :class:`TextureInfo` objects.

    Instantiate once and reuse.  Supply custom patterns at construction time
    to override built-in channel / UDIM detection without monkey-patching.

    Args:
        channel_patterns: Custom ``(compiled_regex, TextureChannel)`` list.
            Defaults to the built-in ``CHANNEL_PATTERNS``.
        colorspace_map:   Custom colorspace inference mapping.
            Defaults to ``DEFAULT_COLORSPACE``.
        udim_patterns:    Custom UDIM detection patterns.
            Defaults to the built-in ``_UDIM_PATTERNS``.

    Example::

        parser = TextureParser()

        # Single file
        info = parser.parse("hero_car_BaseColor_1001.exr")

        # Whole directory
        infos = parser.parse_directory("/jobs/darkStar/tex/hero_car/")
    """

    def __init__(
        self,
        channel_patterns: Optional[List[Tuple[re.Pattern, TextureChannel]]] = None,  # type: ignore[type-arg]
        colorspace_map: Optional[Dict[TextureChannel, ColorSpace]] = None,
        udim_patterns: Optional[List[Tuple[re.Pattern, UDIMMode, str]]] = None,  # type: ignore[type-arg]
    ) -> None:
        self._channel_patterns = channel_patterns if channel_patterns is not None else CHANNEL_PATTERNS
        self._colorspace_map   = colorspace_map   if colorspace_map   is not None else DEFAULT_COLORSPACE
        self._udim_patterns    = udim_patterns    if udim_patterns    is not None else _UDIM_PATTERNS

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, path: PathLike) -> TextureInfo:
        """Parse a single texture path and return a :class:`TextureInfo`.

        The file does not need to exist on disk.

        Args:
            path: Path or filename string to parse.

        Returns:
            :class:`TextureInfo` with all detected metadata populated.
        """
        p = Path(path)
        stem = p.stem
        extension = p.suffix.lstrip(".").lower()
        warnings: List[str] = []

        udim_mode, udim_token, clean_stem = self._detect_udim(stem)
        channel = self._detect_channel(clean_stem)

        if channel is TextureChannel.UNKNOWN:
            warnings.append(
                "Could not detect PBR channel from stem '"
                + stem
                + "'. Add a keyword like 'BaseColor', 'Roughness', or 'Normal'."
            )

        colorspace = self._colorspace_map.get(channel, ColorSpace.RAW)
        raw_name = _clean_stem(clean_stem)

        resolved = p.resolve() if p.is_absolute() else p

        return TextureInfo(
            path=resolved,
            stem=stem,
            extension=extension,
            channel=channel,
            colorspace=colorspace,
            udim_mode=udim_mode,
            udim_token=udim_token,
            raw_name=raw_name,
            warnings=tuple(warnings),
        )

    def parse_many(self, paths: List[PathLike]) -> List[TextureInfo]:
        """Parse a list of texture paths.

        Args:
            paths: Iterable of path strings or ``pathlib.Path`` objects.

        Returns:
            List of :class:`TextureInfo`, one per input path.
        """
        return [self.parse(p) for p in paths]

    def parse_directory(
        self,
        directory: PathLike,
        extensions: Optional[List[str]] = None,
        recursive: bool = False,
    ) -> List[TextureInfo]:
        """Scan *directory* and parse all texture files found.

        Args:
            directory:  Directory to scan.
            extensions: Allowed extensions without leading dot.  Defaults to
                        a standard set of texture formats.
            recursive:  If ``True``, scan subdirectories too.

        Returns:
            List of :class:`TextureInfo` sorted by stem name.

        Raises:
            NotADirectoryError: If *directory* does not exist or is not a dir.
        """
        if extensions is None:
            extensions = [
                "exr", "tx", "tif", "tiff", "png",
                "jpg", "jpeg", "hdr", "rat", "dpx",
            ]

        d = Path(directory)
        if not d.is_dir():
            raise NotADirectoryError(
                "Not a directory (or does not exist): " + str(d)
            )

        glob_pat = "**/*" if recursive else "*"
        results: List[TextureInfo] = []

        for p in d.glob(glob_pat):
            if p.is_file() and p.suffix.lstrip(".").lower() in extensions:
                results.append(self.parse(p))

        results.sort(key=lambda i: i.stem.lower())
        return results

    def group_by_channel(
        self, infos: List[TextureInfo]
    ) -> Dict[TextureChannel, List[TextureInfo]]:
        """Group a list of :class:`TextureInfo` objects by channel.

        Args:
            infos: List of parsed texture infos.

        Returns:
            Dict mapping :class:`TextureChannel` → list of matching infos.
        """
        groups: Dict[TextureChannel, List[TextureInfo]] = {}
        for info in infos:
            groups.setdefault(info.channel, []).append(info)
        return groups

    # ------------------------------------------------------------------
    # Internal detection
    # ------------------------------------------------------------------

    def _detect_channel(self, stem: str) -> TextureChannel:
        """Return the best-matching channel for *stem*, or UNKNOWN.

        Strategy:
        1. Split the stem on common separators (``_``, ``-``, ``.``, space).
        2. Check segments **right-to-left** -- the channel keyword is almost
           always the last named segment (before the UDIM token, which has
           already been stripped).  This prevents a word like ``metal`` in
           ``metal_Roughness`` from matching METALNESS ahead of ROUGHNESS.
        3. Fall back to a full-stem search for camelCase names such as
           ``BaseColor`` where the stem is not split.

        Note: Python's ``\\b`` treats ``_`` as a word character, so a bare
        ``\\bword\\b`` anchor would not fire between ``_`` and a letter.
        Splitting on separators first sidesteps this entirely.
        """
        _SEP = re.compile(r"[_\-. ]+")
        segments = _SEP.split(stem)

        # Pass 1: check each segment right-to-left (channel is the last token).
        for segment in reversed(segments):
            seg = segment.lower()
            if not seg:
                continue
            for pattern, channel in self._channel_patterns:
                if pattern.search(seg):
                    return channel

        # Pass 2: fall back to full-stem search (handles camelCase stems that
        # were not split, e.g. a stem that is just "BaseColor").
        for pattern, channel in self._channel_patterns:
            if pattern.search(stem):
                return channel

        return TextureChannel.UNKNOWN

    def _detect_udim(
        self, stem: str
    ) -> Tuple[UDIMMode, str, str]:
        """Return ``(UDIMMode, matched_token, stem_with_token_removed)``."""
        for pattern, mode, static_token in self._udim_patterns:
            m = pattern.search(stem)
            if m:
                token = static_token if static_token else m.group(0)
                clean = pattern.sub("", stem).strip("_-. ")
                return mode, token, clean
        return UDIMMode.NONE, "", stem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_stem(stem: str) -> str:
    """Normalise a stem to a clean base name (lowercase, no double separators).

    Used for the ``raw_name`` field in :class:`TextureInfo`.
    """
    name = re.sub(r"[_\- ]{2,}", "_", stem)
    return name.strip("_-. ").lower()
