"""
lh_houdini_pipeline.materialx.builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Build MaterialX shader networks from parsed ``TextureInfo`` objects.

Two clearly separated halves:

1. **Planning layer (pure Python, no ``hou``)**
   ``MaterialPlanner`` groups a flat list of :class:`TextureInfo` into one
   :class:`MaterialBuildPlan` per material, resolving each channel to its
   MaterialX input / colorspace / signature via ``materialx.rules``.
   This half is fully unit-testable outside Houdini and powers the tool's
   "dry-run" mode.

2. **Construction layer (``hou``, lazily imported)**
   ``MtlxNetworkBuilder`` consumes a plan and creates the actual VOP nodes
   (``mtlxstandard_surface``, ``mtlximage``, ``mtlxnormalmap``,
   ``mtlxdisplacement``) inside a ``subnet`` material container, wiring them
   by **named input** through ``materialx.connection``.

The split keeps all `hou` usage out of import time so ``core``/``file`` and
the dry-run path stay pure (CLAUDE.md "Pure Core Principle").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.file.texture_parser import (
    CHANNEL_PATTERNS,
    ColorSpace,
    TextureChannel,
    TextureInfo,
    UDIMMode,
)
from lh_houdini_pipeline.materialx import connection as _conn
from lh_houdini_pipeline.materialx.rules import ChannelRule, get_rule

_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# MVP scope
# ---------------------------------------------------------------------------

#: Channels the TexToMtlx MVP is allowed to build.  Anything else parsed from a
#: directory is reported and skipped (not silently dropped).
MVP_CHANNELS: Tuple[TextureChannel, ...] = (
    TextureChannel.BASE_COLOR,
    TextureChannel.ROUGHNESS,
    TextureChannel.METALNESS,
    TextureChannel.NORMAL,
    TextureChannel.DISPLACEMENT,
)


class MtlxSignature(Enum):
    """MaterialX ``mtlximage`` output signature (data type of the texture)."""
    COLOR3 = "color3"   # base color, emissive -- 3-channel colour
    FLOAT  = "default"  # roughness, metalness, displacement -- scalar (mtlximage token "default")
    VECTOR3 = "vector3" # normal -- 3-channel vector data


#: Signature per channel.  Channels absent here default to FLOAT.
_CHANNEL_SIGNATURE: Dict[TextureChannel, MtlxSignature] = {
    TextureChannel.BASE_COLOR:       MtlxSignature.COLOR3,
    TextureChannel.EMISSIVE:         MtlxSignature.COLOR3,
    TextureChannel.SUBSURFACE_COLOR: MtlxSignature.COLOR3,
    TextureChannel.NORMAL:           MtlxSignature.VECTOR3,
}


# ---------------------------------------------------------------------------
# Plan value objects (frozen / immutable)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImageNodeSpec:
    """Plan for one ``mtlximage`` node feeding a single shader input.

    Attributes:
        channel:     Source PBR channel.
        file_path:   Houdini-friendly texture path (UDIM token normalised to
                     ``<UDIM>`` where applicable), forward slashes.
        colorspace:  Colorspace token to write to the image node
                     (from :class:`ChannelRule`, e.g. ``"srgb_texture"``).
        signature:   MaterialX image signature token (``"color3"`` etc.).
        mtlx_input:  Destination input name on the standard surface
                     (e.g. ``"base_color"``).
        is_udim:     ``True`` if this texture is UDIM-tiled.
        node_name:   Safe node name for the created image node.
    """
    channel:    TextureChannel
    file_path:  str
    colorspace: str
    signature:  str
    mtlx_input: str
    is_udim:    bool
    node_name:  str


@dataclass(frozen=True)
class MaterialBuildPlan:
    """A complete, hou-free description of one material to build.

    Attributes:
        name:    Sanitised material name (also the subnet node name).
        images:  Image-node specs, sorted by channel for stable output.
        warnings: Non-fatal notes gathered while planning this material.
    """
    name:     str
    images:   Tuple[ImageNodeSpec, ...]
    warnings: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def channels(self) -> Tuple[TextureChannel, ...]:
        """Channels covered by this plan, in image order."""
        return tuple(img.channel for img in self.images)

    @property
    def has_displacement(self) -> bool:
        """``True`` if the plan includes a displacement map."""
        return any(img.channel is TextureChannel.DISPLACEMENT for img in self.images)

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-friendly dict (handy for dry-run printing / tests)."""
        return {
            "name": self.name,
            "images": [
                {
                    "channel": img.channel.value,
                    "mtlx_input": img.mtlx_input,
                    "colorspace": img.colorspace,
                    "signature": img.signature,
                    "is_udim": img.is_udim,
                    "file_path": img.file_path,
                }
                for img in self.images
            ],
            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Planner (pure)
# ---------------------------------------------------------------------------

_SEP_RE = re.compile(r"[_\-. ]+")
_NAME_SAFE_RE = re.compile(r"[^A-Za-z0-9_]+")


class MaterialPlanner:
    """Group :class:`TextureInfo` objects into :class:`MaterialBuildPlan`s.

    Pure Python -- no ``hou``.  Construct once and reuse.

    Args:
        channels: Channels to include.  Defaults to :data:`MVP_CHANNELS`.
                  Pass a wider tuple to plan beyond the MVP scope.

    Example::

        planner = MaterialPlanner()
        plans = planner.plan_from_infos(parser.parse_directory(folder))
        for p in plans:
            print(p.name, p.channels)
    """

    def __init__(self, channels: Optional[Tuple[TextureChannel, ...]] = None) -> None:
        self._channels = tuple(channels) if channels is not None else MVP_CHANNELS

    # -- public ---------------------------------------------------------

    def plan_from_infos(self, infos: List[TextureInfo]) -> List[MaterialBuildPlan]:
        """Build one plan per material from a flat list of texture infos.

        Grouping key is the material name derived from each filename
        (channel keyword + UDIM token stripped).  When several UDIM tiles of
        the same material+channel are present, the first tile wins and its
        path is normalised to a ``<UDIM>`` token.

        Args:
            infos: Parsed :class:`TextureInfo` objects (e.g. from
                   ``TextureParser.parse_directory``).

        Returns:
            Plans sorted by material name.  Materials with no usable channel
            are omitted.
        """
        # material -> {channel -> TextureInfo}  (first occurrence wins)
        grouped: Dict[str, Dict[TextureChannel, TextureInfo]] = {}

        for info in infos:
            if info.channel is TextureChannel.UNKNOWN:
                _log.warning("Skipping unrecognised texture: " + info.stem)
                continue
            if info.channel not in self._channels:
                _log.debug(
                    "Channel " + info.channel.value
                    + " outside MVP scope, skipping: " + info.stem
                )
                continue
            mat = self._material_name(info)
            chan_map = grouped.setdefault(mat, {})
            if info.channel not in chan_map:
                chan_map[info.channel] = info

        plans: List[MaterialBuildPlan] = []
        for mat_name in sorted(grouped):
            chan_map = grouped[mat_name]
            specs: List[ImageNodeSpec] = []
            warnings: List[str] = []
            for channel, info in chan_map.items():
                rule = get_rule(channel)
                if rule is None:
                    warnings.append("No MaterialX rule for channel " + channel.value)
                    continue
                specs.append(self._spec_for(mat_name, channel, info, rule))
            if not specs:
                continue
            specs.sort(key=lambda s: s.channel.value)
            plans.append(
                MaterialBuildPlan(
                    name=mat_name,
                    images=tuple(specs),
                    warnings=tuple(warnings),
                )
            )
        return plans

    # -- internal -------------------------------------------------------

    def _spec_for(
        self,
        mat_name: str,
        channel: TextureChannel,
        info: TextureInfo,
        rule: ChannelRule,
    ) -> ImageNodeSpec:
        """Build the :class:`ImageNodeSpec` for one channel of a material."""
        signature = _CHANNEL_SIGNATURE.get(channel, MtlxSignature.FLOAT)
        node_name = _safe_name("tex_" + channel.value)
        return ImageNodeSpec(
            channel=channel,
            file_path=houdini_texture_path(info),
            colorspace=rule.colorspace,
            signature=signature.value,
            mtlx_input=rule.mtlx_input,
            is_udim=info.is_tiled,
            node_name=node_name,
        )

    def _material_name(self, info: TextureInfo) -> str:
        """Derive a material name from a texture by stripping the channel token.

        Only the *single* segment that matches the texture's detected channel
        is removed (right-to-left), so a prefix like ``metal_ball`` survives
        even though ``metal`` looks like a channel keyword.

        Falls back to the parent directory name, then ``"material"``.
        """
        segments = [s for s in _SEP_RE.split(info.raw_name) if s]

        removed = False
        for i in range(len(segments) - 1, -1, -1):
            if self._segment_channel(segments[i]) is info.channel:
                del segments[i]
                removed = True
                break
        if not removed and segments:
            # camelCase stems (e.g. "BaseColor") never split -- drop last token.
            if self._segment_channel(segments[-1]) is not None:
                segments.pop()

        name = "_".join(segments).strip("_")
        if not name:
            parent = info.path.parent.name
            name = parent if parent and parent not in (".", "/", "\\") else "material"
        return _safe_name(name)

    @staticmethod
    def _segment_channel(segment: str) -> Optional[TextureChannel]:
        """Return the channel a single name segment maps to, or ``None``."""
        seg = segment.lower()
        for pattern, channel in CHANNEL_PATTERNS:
            if pattern.search(seg):
                return channel
        return None


# ---------------------------------------------------------------------------
# Path helpers (pure)
# ---------------------------------------------------------------------------

def houdini_texture_path(info: TextureInfo) -> str:
    """Return a Houdini-friendly texture path with a normalised UDIM token.

    Non-tiled textures are returned as a forward-slash path unchanged.  For
    tiled textures the tile token in the *filename* is replaced with
    ``<UDIM>`` so a single image node covers the whole set:

        ``/tex/hero_basecolor_1001.exr`` -> ``/tex/hero_basecolor_<UDIM>.exr``

    Mudbox-style ``_u#_v#`` tiling is left as-is (handled per-tile) and noted
    by the caller; full Mudbox support is out of MVP scope.

    Args:
        info: A parsed :class:`TextureInfo`.

    Returns:
        Forward-slash path string suitable for an ``mtlximage`` ``file`` parm.
    """
    posix = info.path.as_posix()
    if not info.is_tiled or not info.udim_token:
        return posix

    if info.udim_mode in (UDIMMode.HOUDINI, UDIMMode.SUBSTANCE):
        # Token already an explicit placeholder in the name; normalise to <UDIM>.
        return posix.replace(info.udim_token, "<UDIM>")
    if info.udim_mode is UDIMMode.MARI:
        # Replace only within the filename (avoid clobbering a dir named 1001).
        parent = info.path.parent.as_posix()
        name = info.path.name.replace(info.udim_token, "<UDIM>")
        return (parent + "/" + name) if parent not in ("", ".") else name
    # MUDBOX or anything else: leave untouched.
    return posix


def _safe_name(name: str) -> str:
    """Sanitise *name* into a valid Houdini node name."""
    safe = _NAME_SAFE_RE.sub("_", name).strip("_")
    if not safe:
        return "material"
    if safe[0].isdigit():
        safe = "m_" + safe
    return safe


def _set_material_flag(node: Any) -> None:
    """Enable Houdini's material flag on a VOP material container if present."""
    try:
        node.setMaterialFlag(True)
    except Exception as exc:  # noqa: BLE001
        _log.debug("Material flag unavailable on " + node.path() + ": " + str(exc))


# ---------------------------------------------------------------------------
# Network builder (hou -- lazily imported)
# ---------------------------------------------------------------------------

# Houdini VOP node types.  Isolated here so a version change is a one-line edit.
# NOTE: validated for Houdini 19.5 / 20.x Karma MaterialX.  Verify on your build.
_NT_SUBNET       = "subnet"
_NT_STD_SURFACE  = "mtlxstandard_surface"
_NT_IMAGE        = "mtlximage"
_NT_NORMAL_MAP   = "mtlxnormalmap"
_NT_DISPLACEMENT = "mtlxdisplacement"


@dataclass
class BuildResult:
    """Outcome of building one material network.

    Attributes:
        material_name: Plan name that was built.
        node_path:     Full path to the created subnet, or ``""`` on failure.
        created:       ``True`` if a network was created.
        connected:     Channels that were successfully wired to the shader.
        skipped:       Channels that could not be wired (logged).
    """
    material_name: str
    node_path:     str = ""
    created:       bool = False
    connected:     Tuple[str, ...] = field(default_factory=tuple)
    skipped:       Tuple[str, ...] = field(default_factory=tuple)


class MtlxNetworkBuilder:
    """Create MaterialX VOP networks inside a parent from build plans.

    All ``hou`` calls live in the methods (lazy import), so importing this
    class never requires Houdini.  The parent may be a ``materiallibrary``
    LOP (in ``/stage``) or a material network (in ``/mat``) -- both host the
    same ``mtlx*`` VOP node types, so one code path covers both contexts.

    Args:
        force: If ``True``, an existing child with the same name is destroyed
               and rebuilt.  If ``False``, Houdini's name-collision handling
               yields a uniquely numbered node.
    """

    def __init__(self, force: bool = False) -> None:
        self._force = force

    def build_all(self, parent: Any, plans: List[MaterialBuildPlan]) -> List[BuildResult]:
        """Build every plan under *parent* and lay the parent out.

        Args:
            parent: Destination ``hou.Node`` (materiallibrary LOP or matnet).
            plans:  Plans produced by :class:`MaterialPlanner`.

        Returns:
            One :class:`BuildResult` per plan.
        """
        results = [self.build_one(parent, p) for p in plans]
        try:
            parent.layoutChildren()
        except Exception as exc:  # noqa: BLE001
            _log.debug("parent.layoutChildren() skipped: " + str(exc))
        return results

    def build_one(self, parent: Any, plan: MaterialBuildPlan) -> BuildResult:
        """Build a single material subnet for *plan* under *parent*.

        Args:
            parent: Destination ``hou.Node``.
            plan:   The material plan to realise.

        Returns:
            A :class:`BuildResult` describing what was created and wired.
        """
        result = BuildResult(material_name=plan.name)

        subnet = self._make_container(parent, plan.name)
        if subnet is None:
            return result
        result.node_path = subnet.path()
        result.created = True

        surface = subnet.createNode(_NT_STD_SURFACE, "standard_surface")

        connected: List[str] = []
        skipped: List[str] = []
        disp_spec: Optional[ImageNodeSpec] = None

        for spec in plan.images:
            if spec.channel is TextureChannel.DISPLACEMENT:
                disp_spec = spec
                continue
            if self._build_channel(subnet, surface, spec):
                connected.append(spec.channel.value)
            else:
                skipped.append(spec.channel.value)

        # Surface output connector turns the subnet into a USD material.
        _conn.create_output_connector(subnet, "surface", "surface", surface, "out")

        # Displacement is wired to its own terminal output.
        if disp_spec is not None:
            if self._build_displacement(subnet, disp_spec):
                connected.append(disp_spec.channel.value)
            else:
                skipped.append(disp_spec.channel.value)

        try:
            subnet.layoutChildren()
        except Exception as exc:  # noqa: BLE001
            _log.debug("subnet.layoutChildren() skipped: " + str(exc))

        result.connected = tuple(connected)
        result.skipped = tuple(skipped)
        _log.info(
            "Built material '" + plan.name + "' at " + subnet.path()
            + " (connected: " + ", ".join(connected) + ")"
        )
        return result

    # -- internal -------------------------------------------------------

    def _make_container(self, parent: Any, name: str) -> Optional[Any]:
        """Create (or replace) the material subnet container."""
        existing = parent.node(name)
        if existing is not None:
            if self._force:
                _log.info("Replacing existing material: " + existing.path())
                existing.destroy()
            else:
                _log.warning(
                    "Material '" + name + "' already exists; creating a unique copy."
                )
        try:
            subnet = parent.createNode(_NT_SUBNET, name)
            _set_material_flag(subnet)
            return subnet
        except Exception as exc:  # noqa: BLE001
            _log.error("Failed to create subnet '" + name + "': " + str(exc))
            return None

    def _make_image(self, subnet: Any, spec: ImageNodeSpec) -> Any:
        """Create and configure one ``mtlximage`` node from a spec."""
        img = subnet.createNode(_NT_IMAGE, spec.node_name)
        _conn.set_parm_if_exists(img, "file", spec.file_path)
        _conn.set_parm_if_exists(img, "signature", spec.signature)
        # Resolve the generic rule token (e.g. "raw") to the exact OCIO menu
        # token for this build/config (e.g. "Raw") before writing it.
        cs = self._resolve_colorspace(img, spec.colorspace)
        if not _conn.set_parm_if_exists(img, "filecolorspace", cs):
            _conn.set_parm_if_exists(img, "colorspace", cs)
        return img

    @staticmethod
    def _resolve_colorspace(img: Any, token: str) -> str:
        """Map a generic colorspace *token* to a valid ``filecolorspace`` menu
        entry on *img* (case-insensitive).  Returns *token* unchanged if no
        menu / match is found, so a custom OCIO config still gets *something*.
        """
        parm = img.parm("filecolorspace")
        if parm is None:
            return token
        try:
            items = list(parm.menuItems())
        except Exception:  # noqa: BLE001
            return token
        if token in items:
            return token
        low = token.lower()
        for it in items:
            if it.lower() == low:
                return it
        # generic 'raw'/'linear' -> config's raw entry (often capitalised 'Raw')
        if low in ("raw", "linear"):
            for it in items:
                if it.lower() == "raw":
                    return it
        return token

    def _build_channel(self, subnet: Any, surface: Any, spec: ImageNodeSpec) -> bool:
        """Create the image (+ normal map) and wire it to the shader by name."""
        img = self._make_image(subnet, spec)

        if spec.channel is TextureChannel.NORMAL:
            nmap = subnet.createNode(_NT_NORMAL_MAP, "normal_map")
            _conn.set_named_input(nmap, "in", img, "out")
            return _conn.set_named_input(surface, spec.mtlx_input, nmap, "out")

        return _conn.set_named_input(surface, spec.mtlx_input, img, "out")

    def _build_displacement(self, subnet: Any, spec: ImageNodeSpec) -> bool:
        """Wire a displacement image through ``mtlxdisplacement`` to an output."""
        img = self._make_image(subnet, spec)
        disp = subnet.createNode(_NT_DISPLACEMENT, "displacement")
        wired = _conn.set_named_input(disp, "displacement", img, "out")
        _conn.create_output_connector(subnet, "displacement", "displacement", disp, "out")
        return wired
