# LH Houdini Pipeline

A component-based Houdini pipeline framework. The design philosophy is to build
small, reusable "Lego brick" components first -- pure, testable, with no Houdini
dependency where possible -- and compose them into tools later. All Houdini
(`hou`) and Qt (PySide) usage is isolated to specific layers, so the core of the
framework runs and unit-tests with plain `python` outside of Houdini.

Verified live on **Houdini 21.0.631**. Built following the Rebelway
*Python for Production* curriculum (CS fundamentals, USD/Solaris automation,
performance, packaging).

---

## Architecture

Imports flow downward only -- a lower layer never imports a higher one:

```
Core -> File -> Houdini -> Domain (materialx, lookdev) -> UI -> Interactive -> Tools
```

| Layer        | Package                      | Rule                                    |
|--------------|------------------------------|-----------------------------------------|
| Core         | `core/`                      | Pure Python -- zero `hou` imports       |
| File         | `file/`                      | Pure Python -- no `hou`                 |
| Houdini      | `houdini/`                   | All `hou` usage lives here (lazy)       |
| Domain       | `materialx/`, `lookdev/`     | May import `houdini/`                    |
| UI           | `ui/`, `tools/*/ui.py`       | PySide2/PySide6 only here               |
| Tools        | `tools/`                     | Compose all layers; entry points        |

Each tool follows the same shape:

```
tools/<tool>/
  core.py     # pure planning / data -- no hou, no Qt (unit-tested, dry-run)
  service.py  # hou side-effects (lazy import); delegates plumbing to houdini.lop
  ui.py       # PySide view; no business logic, calls core/service
  launch.py   # shelf entry point
```

---

## Install

The package ships a **Houdini package file** that wires everything (Python
import path, the OS drag-and-drop hook, and the tool shelf) in one go.

**1. Package** -- copy `packages/lh_pipeline.json` into your Houdini user
packages dir (e.g. `houdini21.0/packages/`). It sets:

```json
{
  "enable": true,
  "env": [
    { "LH_PIPELINE_ROOT": "F:/HOUDINI/LH-Houdini-Pipeline" },
    { "PYTHONPATH": { "value": "$LH_PIPELINE_ROOT", "method": "prepend" } }
  ],
  "path": "$LH_PIPELINE_ROOT"
}
```

`path` puts the repo on `HOUDINI_PATH`, which makes Houdini auto-discover both
`scripts/externaldragdrop.py` (drag-and-drop) and `toolbar/lh_pipeline.shelf`
(the **LH Pipeline** shelf with all 7 tools). **Restart Houdini** to activate.

**2. Quick test** -- in the Houdini Python Shell:

```python
import sys
sys.path.insert(0, r"F:/HOUDINI/LH-Houdini-Pipeline")
import lh_houdini_pipeline   # should import cleanly
```

Optional: `pip install pyyaml send2trash` into Houdini's Python for YAML config
and recoverable (trash-first) cache deletion.

---

## Tools

### 1. Lookdev Builder  (`tools.lookdev_builder`) -- one-click super tool

Assembles a complete lookdev scene in `/stage` from a single click: USD
component **asset** + 3-point **light rig** + 360 **turntable camera** +
**calibration plates** (chrome / 18% grey / Macbeth ColorChecker). Each stage
is framed to the asset's world bounds and isolated so one failure still leaves a
valid result. Composes the asset builder, `lookdev.light_rig`, the camera
turntable, and `lookdev.calibration` -- no duplicated USD authoring.

```python
from lh_houdini_pipeline.tools.lookdev_builder import launch; launch()
```

```python
from lh_houdini_pipeline.tools.lookdev_builder import LookdevConfig, build_lookdev
build_lookdev(LookdevConfig(geo_path=r"D:/geo/hero.fbx", turntable_frames=120))
```

### 2. Asset Ingestion + Drag & Drop  (`tools.asset_ingest`)

Drop FBX/OBJ/ABC/USD (or a whole folder) from the OS file browser onto a Solaris
network and each file is auto-built into a clean USD component. Derives the asset
name (strips version/date noise: `Hero Rock_v003.obj` -> `Hero_Rock`), finds the
texture folder, and reuses the LOPs Asset Builder per item with per-file failure
isolation. Also available as an explicit batch window.

```python
from lh_houdini_pipeline.tools.asset_ingest import launch; launch()
# or scripted:
from lh_houdini_pipeline.tools.asset_ingest import ingest_paths
ingest_paths([r"D:/marketplace/props"])     # folder -> N components
```

The OS hook lives in `scripts/externaldragdrop.py` (`dropAccept`), enabled by
the package file above.

### 3. Scene Cache Manager  (`tools.cache_manager`)

Discovers cache nodes in the scene (`filecache`, `rop_geometry`, ...), scans
their output directories, and reports each sequence with **frame-gap detection**,
**staleness** (age or source-newer), and reclaimable **size**. Safe cleanup is
dry-run first, trash-first (`send2trash` fallback to hard delete), with per-file
error isolation and a threaded delete + progress.

```python
from lh_houdini_pipeline.tools.cache_manager import launch; launch()
# or scripted:
from lh_houdini_pipeline.tools.cache_manager import scan_scene, plan_cleanup
plan = plan_cleanup(scan_scene())            # pure, nothing deleted
```

### 4. LOPs Asset Builder  (`tools.lops_asset_builder`)

Build a USD component asset in `/stage`:
`componentgeometry -> componentmaterial -> componentoutput`, with a
`materiallibrary` built from a texture folder (reuses Tex->Mtlx). Node creation
runs on the main thread; the slow **Save** uses background execution.

```python
from lh_houdini_pipeline.tools.lops_asset_builder import plan_asset, build_asset, save_asset
res = build_asset(plan_asset("HeroProp", geo_path=r"D:/geo/hero.bgeo.sc",
                             tex_folder=r"D:/tex/hero", output_dir=r"D:/usd"))
save_asset(res)
```

### 5. Tex -> Mtlx  (`tools.tex_to_mtlx`)

Scan a texture folder, parse material / channel / UDIM / colorspace, and build
MaterialX shader networks in `/stage` or `/mat`. Includes a threaded **imaketx**
`.tx`/`.rat` converter that correctly keeps data maps (normal/rough/metal) raw
and only colour-converts colour maps.

```python
from lh_houdini_pipeline.tools.tex_to_mtlx import scan_and_plan, build_plans, service
sc = scan_and_plan(r"D:/tex/hero")           # pure, dry-run safe
service.convert_textures_to_tx(sc.infos)      # imaketx -> .rat
build_plans(list(sc.plans), force=True)       # MaterialX networks
```

### 6. Camera Manager  (`tools.camera_manager`)

Create / list / delete / merge cameras in OBJ or Solaris with correct
per-context parm mapping; build a USD **turntable**, author **camera VariantSets**
(lens / angle), expand variants to real cameras, and export to USD / Alembic /
Nuke `.nk`.

```python
from lh_houdini_pipeline.tools.camera_manager import launch; launch()
```

### 7. Project Manager  (`tools.project_manager`)

Scaffold a `project / assets / shots` tree from a template, list projects,
resolve the next work-file version, and set `$JOB`. Pure-Python directory work
with a dark-theme PySide UI (drag-drop root, live validation, tree preview).

```python
from lh_houdini_pipeline.tools.project_manager import launch; launch()
```

---

## Component bricks (reusable)

| Brick                  | Purpose                                                              |
|------------------------|---------------------------------------------------------------------|
| `core.path`            | `PathTemplate`, `PathResolver`, `normalize`, `ensure_dir`           |
| `core.config`          | Immutable `Config` + `ConfigManager`; `bootstrap_config()` (YAML)   |
| `core.logger`          | `get_logger`, `LogContext`, `setup_pipeline_logging`                |
| `core.executor`        | `Executor` (list-args, never a shell string), `CommandResult`       |
| `core.profiling`       | `@timed` / `timed_block`, `@profiled` (cProfile/snakeviz), `Stopwatch`, `mem_sample` |
| `core.validators`      | path / version-token / USD prim-path / frame-range + `require_*`    |
| `file.texture_parser`  | Filename -> `TextureInfo` (channel / UDIM / colorspace)             |
| `file.versioning`      | `Version`, `VersionedFile`, `VersionResolver`                       |
| `file.cache_utils`     | `CacheSequence` model, gap detection, staleness, `human_size`       |
| `houdini.lop`          | Generic node plumbing: create / connect / set parms / multiparm / layout |
| `houdini.traversal`    | BFS/DFS, `find_by_type` (recursiveGlob fast-path), cycle-safe input/output walks |
| `houdini.parm`         | Typed get/set, batch, `try_*`, `ParmError`                          |
| `houdini.geometry`     | `BBox`, point/prim counts, `material_paths` (for ingestion)         |
| `houdini.usd`          | `stage_of`, `compute_world_bounds` (`WorldBounds` via BBoxCache)    |
| `materialx.*`          | Channel rules, `MtlxNetworkBuilder`, connection helpers, `imaketx`  |
| `lookdev.light_rig`    | Pure 3-point math (`look_at_rotation`, `three_point_rig`) + hou builder |
| `lookdev.calibration`  | Macbeth ColorChecker + sRGB->linear + chrome/grey/chart authoring   |

---

## Performance

Instrument any heavy function with the profiling bricks (Rebelway Week 05):

```python
from lh_houdini_pipeline.core.profiling import timed, timed_block, profiled

@timed("build_asset")            # logs "[perf] build_asset took 12.3 ms"
def build_asset(...): ...

with timed_block("scan caches"): ...

@profiled(dump_path="build.prof")   # open in: snakeviz build.prof
def heavy(...): ...
```

Graph work prefers the C++-side fast path:

```python
from lh_houdini_pipeline.houdini import traversal as T
cams = T.find_by_type(hou.node("/stage"), "camera")   # recursiveGlob, not a Python loop
```

Heavy services (`build_asset`, `build_plans`, `convert_textures_to_tx`,
`list_cameras`, `merge_cameras`, `create_turntable`, `get_camera_frames`,
`ingest_items`, `build_lookdev`) are `@timed`.

---

## Configuration (data-driven)

Studio-wide defaults live in `lh_houdini_pipeline/config/defaults.yaml`, never
hardcoded in Python. Layers merge in order (later wins):

```
defaults.yaml  ->  $JOB/config.yaml  ->  ~/.lh_pipeline/config.yaml  ->  LH_PIPELINE_* env
```

```python
from lh_houdini_pipeline.core.config import bootstrap_config
cfg = bootstrap_config().get("pipeline")
cfg.get("render.engine")          # "karma"
cfg.get("cache.stale_after_days") # 14
```

---

## Testing

Pure layers and tool planning run with plain `python` (no Houdini):

```
python test_smoke.py            # core + file               (30 assertions)
python test_tier0.py            # profiling/validators/config (25)
python test_cache_manager.py    # cache parsing/gaps/policy   (26)
python test_asset_ingest.py     # ingest naming/textures/drop (17)
python test_lookdev.py          # light-rig math + calibration(24)
python test_tex_to_mtlx.py  test_materialx_tx.py  test_lops_asset_builder.py
python test_project_manager.py  test_camera_manager.py
```

Houdini-only behaviour (node creation, parm values, USD authoring, PySide) is
verified inside a live 21.0.631 session via the Houdini MCP bridge; every entry
in `CLAUDE.md`'s change log marked **VERIFIED** was run against the live DCC.

---

## Conventions

- `from __future__ import annotations` in every module; type-hint all signatures.
- Frozen dataclasses for value objects; enums for fixed sets.
- Public functions/classes carry docstrings (Args / Returns / Raises).
- `hou` imported lazily inside functions so domain/file layers import for tests.
- Defensive Houdini wrappers: log-and-continue on a missing parm/node rather than
  crashing a half-built network; uncertain node-type / parm names are resolved or
  isolated so a version change is a one-line edit.
- No `str.format(` and no shell-string subprocess calls (security-hook clean).

See `CLAUDE.md` for the full architecture rules, key design decisions, and the
verified-on-21.0.631 change log.
