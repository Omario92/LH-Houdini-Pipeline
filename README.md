# LH Houdini Pipeline

A component-based Houdini pipeline framework. The design philosophy is to build
small, reusable "Lego brick" components first (pure, testable, no Houdini
dependency where possible) and compose them into tools later. All Houdini
(`hou`) and Qt (PySide) usage is isolated to specific layers so the core of the
framework runs and unit-tests with plain `python` outside of Houdini.

Verified live on **Houdini 21.0.631**.

## Architecture

Imports flow downward only -- a lower layer never imports a higher one:

```
Core  ->  File  ->  Houdini  ->  Domain (materialx)  ->  UI  ->  Interactive  ->  Tools
```

| Layer        | Package                  | Rule                                   |
|--------------|--------------------------|----------------------------------------|
| Core         | `core/`                  | Pure Python -- zero `hou` imports      |
| File         | `file/`                  | Pure Python -- no `hou`                |
| Houdini      | `houdini/`               | All `hou` usage lives here (lazy)      |
| Domain       | `materialx/`, `lookdev/` | May import `houdini/`                  |
| UI           | `ui/`, `tools/*/ui.py`   | PySide2/PySide6 only here              |
| Tools        | `tools/`                 | Compose all layers; entry points       |

Each tool follows the same shape:

```
tools/<tool>/
  core.py     # pure planning / data -- no hou, no Qt (unit-tested, dry-run)
  service.py  # hou side-effects (lazy import); delegates plumbing to houdini.lop
  ui.py       # PySide view; no business logic, calls core/service
  launch.py   # shelf entry point
```

## Install

The package root must be on Houdini's `PYTHONPATH`. Pick one:

**A. Houdini package file** (recommended) -- create
`$HOUDINI_USER_PREF_DIR/packages/lh_pipeline.json`:

```json
{
    "env": [
        { "PYTHONPATH": "E:/OneDrive/Documents/Claude/Projects/LH Houdini Pipeline" }
    ]
}
```

**B. Quick test** -- in the Houdini Python Shell:

```python
import sys
sys.path.insert(0, r"E:/OneDrive/Documents/Claude/Projects/LH Houdini Pipeline")
import lh_houdini_pipeline   # should import cleanly
```

**Shelf:** the four tools ship as `scripts/lh_pipeline.shelf`. Copy it into
`$HOUDINI_USER_PREF_DIR/toolbar/` (or import via the shelf dock's *New Shelf*
menu) and restart Houdini. Each tool is also a one-line launch (below).

## Tools

### 1. Tex -> Mtlx  (`tools.tex_to_mtlx`)

Scan a texture folder, parse material / channel / UDIM / colorspace, and build
MaterialX shader networks in `/stage` (Material Library LOP) or `/mat`.
Supported channels: base color, roughness, metalness, normal, displacement.
Includes a threaded **imaketx** `.tx`/`.rat` converter with a progress bar.

```python
from lh_houdini_pipeline.tools.tex_to_mtlx import launch
launch()
```

Headless / scripted:

```python
from lh_houdini_pipeline.tools.tex_to_mtlx import scan_and_plan, build_plans, service
sc = scan_and_plan(r"D:/tex/hero")          # pure; safe outside Houdini (dry-run)
service.convert_textures_to_tx(sc.infos)     # imaketx -> .rat
build_plans(list(sc.plans), force=True)      # MaterialX networks in /stage
```

### 2. LOPs Asset Builder  (`tools.lops_asset_builder`)

Build a USD component asset in `/stage`:
`componentgeometry -> componentmaterial -> componentoutput`, with a
`materiallibrary` built from a texture folder (reuses Tex->Mtlx). Build runs on
the main thread (hou node creation is not thread-safe); the slow **Save** step
uses Houdini's background execution.

```python
from lh_houdini_pipeline.tools.lops_asset_builder import launch
launch()
```

Scripted:

```python
from lh_houdini_pipeline.tools.lops_asset_builder import plan_asset, build_asset, save_asset
plan = plan_asset("HeroProp", geo_path=r"D:/geo/hero.bgeo.sc",
                  tex_folder=r"D:/tex/hero", output_dir=r"D:/usd")
res = build_asset(plan)        # builds the graph
save_asset(res)                # write USD to disk
```

### 3. Project Manager  (`tools.project_manager`)

Scaffold a `project / assets / shots` directory tree from a template, list
existing projects, resolve the next work-file version, and point Houdini's
`$JOB` at the project. Directory work is pure Python (runs anywhere).

```python
from lh_houdini_pipeline.tools.project_manager import launch
launch()
```

Scripted:

```python
from lh_houdini_pipeline.tools.project_manager import plan_project, create_project, set_houdini_job
plan = plan_project(r"D:/jobs", "DarkStar", assets=["hero"], shots=["sh0010", "sh0020"])
create_project(plan)                    # mkdir -p the whole tree (idempotent)
set_houdini_job(plan.project_root)      # $JOB -> D:/jobs/DarkStar
```

### 4. Camera Manager  (`tools.camera_manager`)

Create and list cameras in OBJ (`/obj` `cam`) or Solaris (`/stage` `camera`)
from resolution presets, with the correct per-context parameter mapping
(OBJ `focal/aperture/resx/resy` vs USD `focalLength/horizontalAperture/clippingRange`).

```python
from lh_houdini_pipeline.tools.camera_manager import launch
launch()
```

Scripted:

```python
from lh_houdini_pipeline.tools.camera_manager import (
    spec_from_preset, ResolutionPreset, CameraContext, create_camera)
spec = spec_from_preset("shotCam", ResolutionPreset.UHD4K, focal_length=35.0)
create_camera(spec, CameraContext.OBJ)      # or CameraContext.STAGE for USD
```

## Component bricks (reusable)

| Brick                          | Purpose                                                        |
|--------------------------------|----------------------------------------------------------------|
| `core.path`                    | `PathTemplate`, `PathResolver`, `normalize`, `ensure_dir`      |
| `core.config`                  | Immutable `Config`, `ConfigManager`, `ConfigLoader`            |
| `core.logger`                  | `get_logger`, `LogContext`, `setup_pipeline_logging`           |
| `core.executor`                | `Executor` (list-args, never a shell string), `CommandResult`  |
| `file.texture_parser`          | Filename -> `TextureInfo` (channel / UDIM / colorspace)        |
| `file.versioning`              | `Version`, `VersionedFile`, `VersionResolver`                  |
| `houdini.lop`                  | Generic node plumbing: create / connect / set parms / multiparm / layout |
| `materialx.rules`              | Channel -> MaterialX input / colorspace rules                  |
| `materialx.builder`            | `MaterialPlanner` (pure) + `MtlxNetworkBuilder` (hou)          |
| `materialx.connection`         | Named-input wiring helpers for VOP networks                    |
| `materialx.tx`                 | `imaketx` planner + converter over `core.executor`             |

## Testing

Pure layers and tool planning run with plain `python` (no Houdini):

```
cd "E:/OneDrive/Documents/Claude/Projects/LH Houdini Pipeline"
python test_smoke.py                 # core + file (30 assertions)
python test_tex_to_mtlx.py           # parser + plan + (guarded) build
python test_materialx_tx.py          # imaketx planner / converter
python test_lops_asset_builder.py    # asset planning
python test_project_manager.py       # planning + real directory creation
python test_camera_manager.py        # camera spec / parm mapping
```

Houdini-only behaviour (node creation, parm values, `$JOB`, PySide) is verified
inside a live session; `scripts/verify_mtlx_nodes.py` is a standalone `hython`
checker for the MaterialX node-type assumptions.

## Conventions

- `from __future__ import annotations` in every module; type-hint all signatures.
- Frozen dataclasses for value objects; enums for fixed sets.
- Public functions/classes carry docstrings (Args / Returns / Raises).
- Defensive Houdini wrappers: log-and-continue on a missing parm/node rather
  than crashing a half-built network; isolate uncertain node-type / parm names
  so a version change is a one-line edit.
- No `str.format(` and no shell-string subprocess calls (security-hook clean).

See `CLAUDE.md` for the full architecture rules, key design decisions, and the
verified-on-21.0.631 notes.
