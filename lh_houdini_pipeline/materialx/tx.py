"""
lh_houdini_pipeline.materialx.tx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Texture -> mip-mapped ``.tx``/``.rat`` conversion via SideFX **imaketx**.

SideFX ships ``imaketx`` (NOT the OpenImageIO ``maketx``) at
``$HFS/bin/imaketx[.exe]`` -- verified on Houdini 21.0.631.  Usage::

    imaketx [infile] [outfile] [options]
      -v / --verbose        progress
      -f / --filter NAME     box gauss point sinc bartlett blackman catrom hanning mitchell
      -F / --format NAME     OpenEXR | RAT | TIFF
      --newer                only rebuild if the source is newer
      --ocio                 use OCIO to detect input/output colour spaces
      -c / --colorconvert SRC DST   explicit colour conversion
      -l / --linearize 0|1|2        sRGB linearization control (0 = off)

Two halves, mirroring ``builder.py``:

* **Pure** (`TxFormat`, `TxConversionSpec`, `MaketxPlanner`, ``default_imaketx_exe``)
  -- no ``hou``, build commands + plan output paths, fully unit-testable and
  dry-run friendly.
* **Runner** (`MaketxConverter`) -- drives :class:`core.executor.Executor`
  (list-based args, no shell string).  ``resolve_imaketx`` reads
  ``$HFS`` via a lazy ``hou`` import so the module loads outside Houdini.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, List, Optional, Tuple, Union

from lh_houdini_pipeline.core.executor import CommandResult, Executor
from lh_houdini_pipeline.core.logger import get_logger
from lh_houdini_pipeline.file.texture_parser import ColorSpace, TextureInfo

PathLike = Union[str, Path]
_log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Output format
# ---------------------------------------------------------------------------

class TxFormat(Enum):
    """Output texture format understood by ``imaketx -F``.

    The value is the ``imaketx`` ``-F`` token; :pyattr:`extension` is the file
    suffix to use for the output path.
    """
    RAT  = "RAT"       # Houdini's native tiled mipmap (fast for Karma/Mantra)
    EXR  = "OpenEXR"   # OpenEXR-based ``.tx``
    TIFF = "TIFF"

    @property
    def extension(self) -> str:
        """File extension (no dot) for this format."""
        return {"RAT": "rat", "OpenEXR": "tx", "TIFF": "tif"}[self.value]


#: imaketx ``-f`` filters that exist on H21 (used to validate planner input).
VALID_FILTERS: Tuple[str, ...] = (
    "box", "gauss", "point", "sinc", "bartlett",
    "blackman", "catrom", "hanning", "mitchell",
)


# ---------------------------------------------------------------------------
# Conversion spec (pure, frozen)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TxConversionSpec:
    """A single source -> output conversion request.

    Attributes:
        source:      Input texture path.
        output:      Target ``.tx``/``.rat`` path.
        tx_format:   Output :class:`TxFormat`.
        filter:      Downscale filter name (must be in :data:`VALID_FILTERS`).
        only_newer:  Pass ``--newer`` so unchanged sources are skipped.
        src_colorspace: Explicit source colourspace for ``-c`` (or ``None``).
        dst_colorspace: Explicit target colourspace for ``-c`` (or ``None``).
        use_ocio:    Pass ``--ocio`` for automatic colourspace detection when
                     no explicit ``-c`` pair is given.
        linearize:   Optional ``imaketx -l`` mode. ``0`` disables automatic
                     sRGB linearization for RAW/data textures such as normals.
    """
    source:    Path
    output:    Path
    tx_format: TxFormat = TxFormat.RAT
    filter:    str      = "catrom"
    only_newer: bool    = True
    src_colorspace: Optional[str] = None
    dst_colorspace: Optional[str] = None
    use_ocio:  bool     = True
    linearize: Optional[int] = None

    @property
    def does_colorconvert(self) -> bool:
        """``True`` if an explicit ``-c SRC DST`` pair will be emitted."""
        return bool(self.src_colorspace and self.dst_colorspace)

    def build_command(self, exe: str) -> List[str]:
        """Return the full ``imaketx`` argument list for this spec.

        Args:
            exe: Path to the ``imaketx`` executable.

        Returns:
            A command list ready for :meth:`Executor.run` (never shell-joined).
        """
        cmd: List[str] = [exe, str(self.source), str(self.output), "-v"]
        if self.only_newer:
            cmd.append("--newer")
        cmd += ["-f", self.filter, "-F", self.tx_format.value]
        if self.does_colorconvert:
            # -c takes two positional args: source then target colourspace.
            cmd += ["-c", str(self.src_colorspace), str(self.dst_colorspace)]
        elif self.use_ocio:
            cmd.append("--ocio")
        if self.linearize is not None:
            cmd += ["-l", str(self.linearize)]
        return cmd


# ---------------------------------------------------------------------------
# Planner (pure)
# ---------------------------------------------------------------------------

class MaketxPlanner:
    """Turn textures / :class:`TextureInfo` into :class:`TxConversionSpec`s.

    Pure Python -- no ``hou``.  Colour textures (sRGB) get an explicit
    ``-c <src> scene_linear`` conversion; data textures (raw) are passed
    through with OCIO auto-detection.  This default is conservative and easy
    to override per call.

    Args:
        tx_format:  Output format for all specs (default ``RAT``).
        filter:     Downscale filter (validated against :data:`VALID_FILTERS`).
        only_newer: Default ``--newer`` behaviour.
        scene_linear_token: Target colourspace name for colour textures.

    Raises:
        ValueError: If *filter* is not a valid imaketx filter.
    """

    def __init__(
        self,
        tx_format: TxFormat = TxFormat.RAT,
        filter: str = "catrom",
        only_newer: bool = True,
        scene_linear_token: str = "scene_linear",
    ) -> None:
        if filter not in VALID_FILTERS:
            raise ValueError(
                "Unknown imaketx filter '" + filter + "'. Valid: "
                + ", ".join(VALID_FILTERS)
            )
        self._format = tx_format
        self._filter = filter
        self._only_newer = only_newer
        self._scene_linear = scene_linear_token

    def plan_path(
        self,
        source: PathLike,
        colorspace: ColorSpace = ColorSpace.RAW,
        out_dir: Optional[PathLike] = None,
    ) -> TxConversionSpec:
        """Plan a conversion for a bare texture *source* path.

        Args:
            source:     Input texture path (need not exist for planning).
            colorspace: Colour role of the texture (drives ``-c`` decision).
            out_dir:    Directory for the output; defaults to the source's
                        own directory.

        Returns:
            A :class:`TxConversionSpec`.
        """
        src = Path(source)
        out_directory = Path(out_dir) if out_dir is not None else src.parent
        output = out_directory / (src.stem + "." + self._format.extension)

        src_cs: Optional[str] = None
        dst_cs: Optional[str] = None
        use_ocio = False
        linearize: Optional[int] = None
        if colorspace is ColorSpace.SRGB:
            src_cs = "srgb_texture"
            dst_cs = self._scene_linear
        elif colorspace is not ColorSpace.RAW:
            use_ocio = True
        else:
            linearize = 0

        return TxConversionSpec(
            source=src,
            output=output,
            tx_format=self._format,
            filter=self._filter,
            only_newer=self._only_newer,
            src_colorspace=src_cs,
            dst_colorspace=dst_cs,
            use_ocio=use_ocio,
            linearize=linearize,
        )

    def plan_info(
        self, info: TextureInfo, out_dir: Optional[PathLike] = None
    ) -> TxConversionSpec:
        """Plan a conversion from a parsed :class:`TextureInfo`.

        Uses the info's detected ``colorspace`` to decide colour conversion.

        Args:
            info:    Parsed texture info.
            out_dir: Optional output directory.

        Returns:
            A :class:`TxConversionSpec`.  UDIM tiles are converted per-file;
            batch-tile handling is out of MVP scope (noted in the log).
        """
        if info.is_tiled:
            _log.debug(
                "Tiled texture planned per-file (no UDIM batching in MVP): "
                + info.stem
            )
        return self.plan_path(info.path, info.colorspace, out_dir)

    def plan_many(
        self, infos: List[TextureInfo], out_dir: Optional[PathLike] = None
    ) -> List[TxConversionSpec]:
        """Plan conversions for a list of texture infos."""
        return [self.plan_info(i, out_dir) for i in infos]


# ---------------------------------------------------------------------------
# Executable resolution
# ---------------------------------------------------------------------------

def default_imaketx_exe(hfs: PathLike) -> str:
    """Return the platform ``imaketx`` path under *hfs* (pure, no ``hou``).

    Args:
        hfs: Houdini install root (``$HFS``).

    Returns:
        Full path string to ``imaketx`` (``.exe`` on Windows).
    """
    name = "imaketx.exe" if os.name == "nt" else "imaketx"
    return str(Path(hfs) / "bin" / name)


def resolve_imaketx() -> str:
    """Resolve ``imaketx`` from the live Houdini ``$HFS`` (lazy ``hou`` import).

    Returns:
        Full path to ``imaketx``.

    Raises:
        ImportError:    If called outside a Houdini Python session.
        FileNotFoundError: If the executable cannot be found under ``$HFS``.
    """
    import hou  # noqa: PLC0415
    hfs = hou.getenv("HFS")
    if not hfs:
        raise FileNotFoundError("$HFS is not set in this Houdini session.")
    exe = default_imaketx_exe(hfs)
    if not Path(exe).exists():
        raise FileNotFoundError("imaketx not found at: " + exe)
    return exe


# ---------------------------------------------------------------------------
# Converter (runner)
# ---------------------------------------------------------------------------

@dataclass
class TxResult:
    """Pairing of a spec with the :class:`CommandResult` of running it."""
    spec:   TxConversionSpec
    result: CommandResult

    @property
    def success(self) -> bool:
        """``True`` if the conversion command succeeded (or was a dry-run)."""
        return self.result.success or self.result.dry_run


class MaketxConverter:
    """Run :class:`TxConversionSpec`s through ``imaketx``.

    Args:
        exe:      Explicit path to ``imaketx``.  If ``None``, it is resolved
                  lazily from ``$HFS`` on first use (requires Houdini).
        executor: A configured :class:`Executor`.  If ``None``, a default with
                  a 10-minute timeout is created.
        dry_run:  Build and log commands without spawning processes.

    Example::

        conv = MaketxConverter(dry_run=True)
        specs = MaketxPlanner().plan_many(infos)
        results = conv.convert_many(specs)
    """

    def __init__(
        self,
        exe: Optional[str] = None,
        executor: Optional[Executor] = None,
        dry_run: bool = False,
    ) -> None:
        self._exe = exe
        self._executor = executor or Executor(timeout=600, dry_run=dry_run)

    def _exe_path(self) -> str:
        """Return the cached / resolved imaketx path."""
        if self._exe is None:
            self._exe = resolve_imaketx()
        return self._exe

    def convert(self, spec: TxConversionSpec) -> TxResult:
        """Convert a single spec; ensures the output directory exists first.

        Args:
            spec: The conversion to run.

        Returns:
            A :class:`TxResult` (never raises; inspect ``.success``).
        """
        try:
            spec.output.parent.mkdir(parents=True, exist_ok=True)
        except Exception as exc:  # noqa: BLE001
            _log.warning("Could not create output dir: " + str(exc))
        cmd = spec.build_command(self._exe_path())
        result = self._executor.run(cmd)
        if not (result.success or result.dry_run):
            _log.warning("imaketx failed for " + str(spec.source))
        return TxResult(spec=spec, result=result)

    def convert_many(
        self,
        specs: List[TxConversionSpec],
        on_each: Optional[Callable[[int, int, "TxResult"], None]] = None,
    ) -> List[TxResult]:
        """Convert a batch of specs sequentially, with optional progress.

        Args:
            specs:   Conversion specs.
            on_each: Called after every conversion as
                     ``on_each(done_count, total, tx_result)`` -- ideal for a
                     progress bar.  Exceptions from the callback are swallowed
                     (logged) so a UI hiccup can't abort the batch.

        Returns:
            One :class:`TxResult` per spec, in order.
        """
        results: List[TxResult] = []
        total = len(specs)
        for i, spec in enumerate(specs, start=1):
            res = self.convert(spec)
            results.append(res)
            if on_each is not None:
                try:
                    on_each(i, total, res)
                except Exception as exc:  # noqa: BLE001
                    _log.debug("on_each progress callback raised: " + str(exc))
        return results
