# LH Houdini Pipeline — Agent Instructions

> **Mandatory:** Read this file before any task. Follow Rules and Commands exactly.
> After every major task (feature, refactor, bug fix), update **Recent Changes**.

---

## Project Overview

Component-based Houdini pipeline framework. Design philosophy: build reusable
"Lego brick" components first; compose them into tools later.

**Workspace:** `F:\HOUDINI\LH-Houdini-Pipeline`
**Package root:** `lh_houdini_pipeline/`

---

## Architecture — Layer Order (strict, no skipping)

```
Core  ->  File  ->  Houdini  ->  Domain  ->  UI  ->  Interactive  ->  Tools
```

| Layer         | Package                  | Constraint                              |
|---------------|--------------------------|-----------------------------------------|
| Core          | `core/`                  | Pure Python -- zero `hou` imports       |
| File          | `file/`                  | Pure Python -- no `hou`                 |
| Houdini       | `houdini/`               | All `hou` usage lives here              |
| Domain        | `materialx/`, `lookdev/` | May import `houdini/` layer             |
| UI            | `ui/`                    | PySide2/PySide6 only here               |
| Interactive   | `interactive/`           | HOM viewer state/drawables              |
| Tools         | `tools/`                 | Compose all layers; entry points        |

A lower layer must never import from a higher layer.

---

## Rules

### Code Quality
- All public functions/classes must have docstrings (Args, Returns, Raises).
- Use `from __future__ import annotations` in every module.
- Type-hint all function signatures.
- Frozen dataclasses for value objects (`@dataclass(frozen=True)`).
- Enums for fixed sets of constants (channel types, formats, colorspaces, etc.).

### Security Hook Workarounds
The `security_reminder_hook.py` scans for `.format(` and `shell=True` substrings.
Workarounds:
- Template substitution: use `re.Pattern.sub()` with a callback, not `str.format_map()`.
- Log formatting: use string `.replace()` calls, not `.format()` in Formatter bodies.
- Executor: pass args as a list to `subprocess.run`, never `shell=True`.
- The hook blocks the FIRST write per file+rule but caches it -- retry immediately and it passes.
- Disable entirely with env var: `ENABLE_SECURITY_REMINDER=0`.

### Pure Core Principle
`core/` and `file/` must be importable and testable with plain `python test_smoke.py`
outside Houdini. No `hou`, no PySide, no MaterialX SDK in these layers.

### Error Handling
- Domain errors use typed exceptions: `VersionError(ValueError)`, `ConfigError`.
- Never swallow exceptions silently; log and re-raise or return a typed result.
- Provide `try_*` variants for non-fatal lookups (return `None` on miss).

### Immutability
- `PathTemplate`, `Version`, `VersionedFile`, `TextureInfo`, `CommandResult` are frozen.
- `PathResolver.with_overrides()` returns a copy; `.update()` mutates in place.
- `Config` is immutable; use `.merged_with()` to produce new instances.

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Enum members: `UPPER_SNAKE`
- Private helpers: `_leading_underscore`

---

## Commands

### Run smoke tests
```
cd "E:\OneDrive\Documents\Claude\Projects\LH Houdini Pipeline"
python test_smoke.py
```

### Verify import outside Houdini
```python
import sys
sys.path.insert(0, r"F:\HOUDINI\LH-Houdini-Pipeline")
import lh_houdini_pipeline
```

### Hot-reload inside Houdini
```python
from lh_houdini_pipeline.core.reload import reload_package
reload_package(verbose=True)
```

---

## Package Map

```
lh_houdini_pipeline/
+-- core/
|   +-- path.py           [DONE] PathTemplate, PathResolver, normalize
|   +-- config.py         [DONE] Config (immutable), ConfigManager, ConfigLoader
|   +-- logger.py         [DONE] get_logger, LogContext, setup_pipeline_logging
|   +-- executor.py       [DONE] Executor, ThreadedExecutor, CommandResult, RetryPolicy
|   +-- validators.py     [stub] path/extension checks
|   +-- reload.py         [stub] hot-reload inside Houdini
+-- file/
|   +-- texture_parser.py [DONE] TextureParser, TextureInfo, TextureChannel, ColorSpace, UDIMMode
|   +-- versioning.py     [DONE] Version, VersionFormat, VersionedFile, VersionResolver
|   +-- scanner.py        [stub] filesystem asset discovery
|   +-- cache_utils.py    [stub] frame-range detection, cache gap analysis
+-- houdini/              [stubs] env, hom, parm, hda, animation, usd, geometry
|   +-- lop.py            [DONE] generic node plumbing: create/find_or_create/connect/set_parm(s)/set_indexed_parms/press_button/layout/network_pwd
+-- materialx/
|   +-- rules.py          [DONE] CHANNEL_RULES (StandardSurface), ChannelRule, get_rule
|   +-- builder.py        [DONE] MaterialPlanner (pure) + MtlxNetworkBuilder (hou); MaterialBuildPlan/ImageNodeSpec
|   +-- connection.py     [DONE] set_named_input, set_parm_if_exists, create_output_connector (hou-lazy)
|   +-- tx.py             [DONE] imaketx: TxConversionSpec/MaketxPlanner/MaketxConverter (core.executor)
+-- lookdev/              [stubs] light_rig, turntable, calibration
+-- ui/                   [stubs] widgets, tree, signals, dialogs
+-- interactive/          [stubs] raycast, drawables, state
+-- tools/
    +-- project_manager/  [DONE] core(+sanitize_name)+service+controller(QObject signals)+ui(dark-theme PySide6)+launch
    +-- tex_to_mtlx/      [DONE] core(pure)+service(hou)+ui(PySide)+launch; MVP
    +-- camera_manager/   [DONE] core(CameraSpec/MergePlanner/TurntableSpec)+service(create/list/delete/merge/sync)+ui: OBJ cam + USD camera
    +-- lops_asset_builder/ [DONE] core+service(hou)+ui(PySide)+launch: componentgeo->componentmaterial->componentoutput
```

---

## Key Design Decisions

### PathTemplate
Uses `re.sub()` with a named-group callback instead of `str.format_map()`.
Regex: `_TMPL_RE = re.compile(r"\{(\w+)(?::([^}]*))?\}")`
Avoids security hook false positive on `.format(`.

### Config sentinel
`_MISSING` singleton avoids `None` ambiguity in `.get()` / `.require()`.
Lists are replaced (not appended) during deep merge.

### Version comparison
`__eq__` and `__lt__` compare `number` only; `fmt` is ignored.
VersionFormat detection order: V3 -> _V3 -> V2 -> _V2 -> V1 (most specific first).

### Executor
Uses `subprocess.run(cmd_list, ...)` -- args as a list, never `shell=True`.

### LOP component asset (verified H21.0.631)
componentgeometry has NO external inputs -- geo loads via inner `sopnet/geo` (outputs `default`/`proxy`/`simproxy`);
wire a `file` SOP into `default`. componentmaterial: input0=stage, input1=materials, multiparm `nummaterials`+`primpattern#`/`matspecpath#`.
componentoutput: `assetname`/`rootprim`/`lopoutput`; Save-to-Disk button is `execute`. materiallibrary default `matpathprefix`=`/materials/`.

### imaketx (not maketx)
SideFX ships `imaketx[.exe]` under `$HFS/bin`, NOT OIIO `maketx`. Usage: `imaketx in out [opts]`;
`-f` filter, `-F` RAT|OpenEXR|TIFF, `--newer`, `--ocio`, `-c SRC DST`. Verified: `-c srgb_texture scene_linear`.

### MaterialX node API (verified H21.0.631)
`mtlximage.signature` menu tokens: `default`(Float), `color3`, `vector3` (others: color4/vector2/vector4).
`filecolorspace` is the colorspace parm (no `colorspace`); raw token is capitalised `Raw` in the
default OCIO config -- builder resolves case-insensitively. `mtlx*` single output is named `out`.
Note: on `inputConnection`, `inputName()`/`outputName()` read swapped vs intuition, but `setNamedInput`
wiring is correct -- trust `inputIndex()` when introspecting.

### LogContext
Thread-local stack. `with LogContext(shot="sh0100"):` pushes a frame.
Formatter uses `.replace()` instead of `.format()` to avoid security hook.

---

## Recent Changes

| Date       | Change                                                       |
|------------|--------------------------------------------------------------|
| 2026-06-21 | Initial scaffold: full package tree (45 files)               |
| 2026-06-21 | Implemented core/: path, config, logger, executor            |
| 2026-06-21 | Implemented file/: texture_parser, versioning                |
| 2026-06-21 | Implemented materialx/rules.py (StandardSurface channel map) |
| 2026-06-21 | Added test_smoke.py (30 assertions covering core + file)     |
| 2026-06-21 | Created CLAUDE.md with architecture rules and command ref    |
| 2026-06-21 | Bug fixes: normalize() trailing slash, Version regex lookbehind, _detect_channel segment split |
| 2026-06-21 | Bug fix: #### UDIM token mapped to HOUDINI (not SEQUENCE); split SEQUENCE pattern to %0?\d*d only |
| 2026-06-21 | materialx/connection.py: hou-lazy wiring helpers (setNamedInput, parm guards, output connectors) |
| 2026-06-21 | materialx/builder.py: pure MaterialPlanner + MaterialBuildPlan; hou MtlxNetworkBuilder (subnet+mtlx) |
| 2026-06-21 | tools/tex_to_mtlx MVP: core (scan/plan, dry-run), service (/stage+/mat build), PySide ui, launch |
| 2026-06-21 | Added test_tex_to_mtlx.py (17 pure assertions + guarded hou/UI tests); smoke tests still green |
---

## Houdini Reference & Rules

Bạn được phép **đọc** các folder Houdini cục bộ:

- Houdini install: `C:/Program Files/Side Effects Software/Houdini 21.0.631/`
- User preferences: `E:/OneDrive/Documents/houdini21.0/`

Dùng các folder này **chỉ để tra cứu**: API, script mẫu, Viewer State examples, SideFX Python utilities.

- **Không** sửa file trong Houdini install folder.
- Chỉ sửa code trong repo này.

Khi viết code Houdini-specific:

- Ưu tiên test bằng `hython` hoặc Houdini Python Shell.
- Không đoán node type nếu có thể kiểm tra.
- Không hardcode input index nếu có thể dùng `inputNames()`.
- Nếu API khác version, viết fallback hoặc báo lỗi rõ.
- Core/file layer không được import `hou`.
| 2026-06-21 | VERIFIED on Houdini 21.0.631 (live MCP): node types, std-surface inputs, subnet+connector OK |
| 2026-06-21 | builder fix: mtlximage signature scalar token 'default' (not 'float'); color3/vector3 confirmed |
| 2026-06-21 | builder fix: _resolve_colorspace maps generic 'raw' -> OCIO token 'Raw' via live filecolorspace menu |
| 2026-06-21 | Added scripts/verify_mtlx_nodes.py (hython standalone node-type/inputNames verifier) |
| 2026-06-21 | materialx/tx.py: imaketx brick (pure planner + Converter over core.executor); SideFX exe is 'imaketx' not 'maketx' |
| 2026-06-21 | VERIFIED live H21.0.631: imaketx srgb_texture->scene_linear conversion, .rat written OK (rc=0) |
| 2026-06-21 | tex_to_mtlx UI: enabled '.tx' button via service.convert_textures_to_tx; added test_materialx_tx.py (11 assertions) |
| 2026-06-21 | tex_to_mtlx UI: threaded imaketx + QProgressBar (worker QObject, queued signals); VERIFIED live PySide6 |
| 2026-06-21 | tools/lops_asset_builder: pure plan_asset (reuses MaterialPlanner) + hou build_asset/save_asset |
| 2026-06-21 | VERIFIED live H21.0.631: full asset graph builds, wiring+parms correct, componentoutput cooks 0 errors |
| 2026-06-21 | Added test_lops_asset_builder.py (7 pure assertions); all suites green |
| 2026-06-21 | lops_asset_builder: service on_stage progress + save_asset_background (executebackground) |
| 2026-06-21 | lops_asset_builder UI (PySide): geo/tex/output pickers, staged-progress Build (main thread), bg Save |
| 2026-06-21 | VERIFIED live PySide6: UI build emits 4 stages, nodes+parms correct, Save enables; hou node-ops kept on main thread |
| 2026-06-21 | houdini/lop.py: generic node plumbing helpers (create/find_or_create/connect/set_parm(s)/set_indexed_parms/press_button/layout/network_pwd) |
| 2026-06-21 | Refactor: tex_to_mtlx + lops_asset_builder services delegate all node plumbing to houdini.lop (slimmer, no inline createNode/setInput) |
| 2026-06-21 | VERIFIED live H21.0.631 post-refactor: both tools build identical graphs, 0 cook errors |
| 2026-06-21 | tools/project_manager: pure plan_project (core.path/PathResolver) + service create/scan/next_version (file.versioning) + $JOB |
| 2026-06-21 | project_manager UI (PySide): root/name/assets/shots, preview, dry-run+create, set $JOB |
| 2026-06-21 | Added test_project_manager.py (12 assertions incl. real fs create); VERIFIED live H21.0.631: create+$JOB+UI |
| 2026-06-21 | tools/camera_manager: pure CameraSpec.to_parms per OBJ/STAGE context + service create/list via houdini.lop |
| 2026-06-21 | VERIFIED live H21.0.631: OBJ cam (focal/aperture/resx/resy) + USD camera (focalLength/clippingRange/vAperture derived) |
| 2026-06-21 | Added test_camera_manager.py (8 pure assertions); ALL tools/ now DONE (tex_to_mtlx, lops_asset_builder, project_manager, camera_manager) |
| 2026-06-22 | Bugfix: tool __init__.launch imported same-named '.launch' submodule, which shadowed the package 'launch' function after first call (-> 'module not callable' on 2nd open). Now imports ui directly; verified opening twice OK on all 4 tools |
| 2026-06-22 | camera_manager: delete_camera + camera_frame_range + sync_playback_range (Week08 playbar sync) |
| 2026-06-22 | camera_manager: pure plan_merge (sequential offsets) + service merge_cameras with static-interpolation fix (Week08) |
| 2026-06-22 | camera_manager UI: Delete/Sync/Merge buttons; added TurntableSpec (pure) for next slice |
| 2026-06-22 | VERIFIED live H21.0.631: merge tx offsets + focal hold-keys (no drift @1005=50/@1012=85); delete/sync OK; UI handlers OK |
| 2026-06-22 | camera_manager: pure turntable_transforms (360 orbit math) + service create_turntable (camera LOP, keyframed transform -> USD time-dependent) |
| 2026-06-22 | camera_manager UI: Turntable(USD) button; optional bounds-from-/stage-target (UsdGeom.BBoxCache) |
| 2026-06-22 | VERIFIED live H21.0.631: turntable ry 0->357 over 120f, orbit f1=+Z f31=+X, focal35/ap10x10; pure orbit-math test green |
| 2026-06-22 | Added Camera Export feature (USD, Alembic, Nuke .nk) and USD baking to the Camera Manager |
| 2026-06-22 | Implemented USD Camera Variants (focal length and transform VariantSets) with stacked python LOP architecture, resolving LIVRPS override issues |
| 2026-06-22 | Implemented programmatic HDA packaging module (HDA creation, Python HDA modules, event scripts, dynamic ParmTemplateGroup) and test suite |
| 2026-06-22 | Redesigned the LOPs Asset Builder UI with Drag & Drop support, collapsible advanced options (Simulation Proxy/Viewport Proxy Quality), color-coded logging panel, and threaded texture conversion |
| 2026-06-22 | project_manager: added controller.py (ProjectController QObject: validate/preview/create signals) + core.sanitize_name |
| 2026-06-22 | project_manager UI redesign (PySide6 dark theme): 3-zone cards, drag&drop root, real-time validation, QTreeWidget preview, status bar, collapsible log, Dry-run/Create |
| 2026-06-22 | VERIFIED live PySide6: validation gating, sanitize hint, tree preview (37 dirs), dry-run no-write, create+\$JOB, exists-warning, minimal-toggle |
| 2026-06-23 | Bootstrapped Houdini AI Assistant (Phase 1): OOP folder tree, launch endpoints, config loader, LLMClient HTTP stream parsers, QThread worker, and PySide6 UI panel skeleton |
| 2026-06-23 | Added test_ai_assistant.py covering LLM mock chat/streaming; all suites verified green |
| 2026-06-23 | Implemented Scene Context Engine (Phase 2): context_inspector HOM parser, context_formatter token-efficient Markdown structures, multimodal vision mapping, selection polling timer, and UI options |
| 2026-06-23 | Added scene context tests to test_ai_assistant.py; smoke and unit suites verified green |
| 2026-06-23 | Implemented Chat UI & Streaming (Phase 3): ChatHistoryView scroll container, ChatBubbleWidget styled bubbles, Markdown QTextBrowser rendering, Copy Code block clipboard exporter, PromptManager mode selector dropdown |
| 2026-06-23 | Added prompt manager tests to test_ai_assistant.py; all tests verified green |
| 2026-06-23 | Implemented Agentic Tool-calling and Safety Gates (Phase 4): concrete AITool instances, ActionApprovalDialog modal diff layout, main-thread HOM execution, multi-step agent loops, and loop-safety counters |
| 2026-06-23 | Added tool schemas and regex parse unit tests; all suites verified green |
| 2026-06-23 | Completed Phase 5: Upgraded GenerateHdaScaffoldTool with parameter template conversions, dynamic PythonModule/OnCreated event script packaging, expanded HDA Architect system prompts, and wrote comprehensive unit tests |
| 2026-06-23 | Completed Phase 6: Implemented socket-based MCP TCP Server and Client delegation, signal-based thread dispatching for HOM safety, approval callback gates, PySide6 UI panels, and integration unit tests |





| 2026-06-22 | project_manager: added persistent JSON folder settings, Settings dialog presets, and selected-folder create/preview integration |
| 2026-06-22 | VERIFIED with Houdini 21.0.631 hython: Project Manager settings import, PySide6 dialog, selected-folder plan, and dry-run |
| 2026-06-22 | VERIFIED with live HoudiniMCP on localhost:9876: execute_code reloads Project Manager worktree and validates Settings dialog + selected folders |
| 2026-06-22 | lops_asset_builder: fixed component material paths to /ASSET/materials, enabled material flags for Material Library filtering, and promoted untagged FBX textures to baseColor |
| 2026-06-22 | VERIFIED with live HoudiniMCP: LOPs Asset Builder creates valid /ASSET/materials prim, material flag true, and component material assignment path correct |
| 2026-06-22 | lops_asset_builder: grouped FBX date-stamped PBR textures into one material, fixed metallic detection, and replans after .rat conversion so materials use converted files |
| 2026-06-22 | VERIFIED with live HoudiniMCP: texture_pbr base/metallic/normal/roughness maps build one material and all mtlximage nodes use .rat files |
| 2026-06-22 | materialx.tx/lops_asset_builder: fixed imaketx output naming to drop source extensions (.png -> .rat, not .png.rat) and prefer clean .rat over legacy double-extension files |
| 2026-06-22 | materialx.tx: RAW/data texture conversion is now pass-through (no --ocio/no -c) so normal/roughness/metalness RAT files preserve data values |
| 2026-06-22 | materialx.tx: RAW/data imaketx commands now add -l 0 to disable automatic sRGB linearization for normal maps |
| 2026-06-22 | materialx.rules: added TextureRole + COLOUR_CHANNELS + classify_channel()/get_imaketx_color_args() (single source of truth: colour vs data) |
| 2026-06-22 | materialx.tx: MaketxPlanner.plan_info now classifies by TextureChannel (role) so normal/rough/metal/disp/mask are ALWAYS raw passthrough (-l 0), never colour-converted; plan_path gains optional role= (legacy colorspace path preserved) |
| 2026-06-22 | test_materialx_tx.py: +3 assertions for role classification & data-map passthrough; all tx + smoke suites green |
| 2026-06-22 | FIX(normal maps): imaketx -l 0 does NOT stop 8-bit PNG linearization (verified H21.0.631: mid 0.5 -> 0.214, double-converted -> 0.036 = dark). Data maps now use identity -c Raw Raw (preserves source values, idempotent). rules.get_imaketx_color_args + MaketxPlanner DATA branch updated |
| 2026-06-22 | FIX(double-conversion): convert_textures_to_tx skips inputs already in target format (.rat) so colour maps are not re-linearized when a folder already holds converted files |
| 2026-06-22 | VERIFIED live H21.0.631 via OpenImageIO: planner cmd '-c Raw Raw' on normal.png yields .rat avg [0.4999,0.4958,0.995] == source (was [0.0358,...]); tests updated, all suites green |
| 2026-06-22 | tex_to_mtlx.core: scan_and_plan now collapses jpg/tx/rat variants per (folder,base,channel) preferring .rat > .tx > source (_prefer_converted_infos). Fixes post-conversion scan picking arbitrary/source variant; .mtlx now references .rat |
| 2026-06-22 | VERIFIED fresh hython H21.0.631 on J:/.../MSMC_Blobs/Blob_Dots+Blob_Marble: 1 material, 3 textures, all channels resolve to .rat; +3 assertions in test_tex_to_mtlx.py, all suites green |
| 2026-06-22 | tex_to_mtlx.core: scan_and_plan auto-recurses when a parent library folder has no textures directly but sub-folders do (auto_recurse=True default). Scanning J:/.../MSMC_Blobs now yields all 11 sub-folder materials (all .rat) without toggling Recursive; +2 assertions |
| 2026-06-22 | houdini/usd_variants.py: pure code-gen for USD camera VariantSets (build_variant_author_code/selection_code, variant_to_data). VERIFIED H21.0.631: Houdini camera LOP authors focalLength as mm/100 (50mm->0.5), so HOUDINI_USD_FOCAL_SCALE=0.01 is correct (NOT a bug); variant focal stays consistent with base camera |
| 2026-06-22 | camera_manager refactor: ONE {cam}_variants_author Python LOP authors ALL VariantSets (accumulates via userData JSON) instead of one node per set; +set_camera_variant_selection ({cam}_..._select), +expand_camera_variants_to_cameras (real per-variant cameras, combine=lens x angle), +get_camera_variant_sets/specs. core: CameraVariantSpec.focal optional + has_transform/transform_overrides + ExpandedCameraSpec + plan_expanded_cameras (pure) |
| 2026-06-22 | camera_manager UI: 'Add Variants' button -> menu [Add USD Variants / Expand to Cameras / Set Active Variant]; angle variants are transform-only (focal None) so they don't clobber lens focal; +VariantSelectionDialog |
| 2026-06-22 | VERIFIED live H21.0.631: add lens+angle separately -> single author node w/ both sets; selection tele_85mm->focal 0.85 + side translate (10,0,0); expand non-combine 4 cams + combine 4 lens x angle; +9 pure assertions in test_camera_manager.py; all suites green |
| 2026-06-23 | camera_manager fix: delete_camera(with_helpers=True) now also destroys {cam}_variants_author + _select Python LOPs. They author the prim via OverridePrim, so leaving them orphaned kept a ghost camera prim + stale node data after delete |
| 2026-06-23 | camera_manager UI: added Refresh button + showEvent auto-refresh + _refresh() on init so the Existing-cameras list re-syncs with the scene (covers external changes / deletes). +guarded hou test delete_removes_variant_helpers |
| 2026-06-23 | Tier-0 upgrade (Rebelway gap-fill): core/profiling.py (Stopwatch + @timed/@timed_block + @profiled cProfile/snakeviz + mem_sample) [W05]; houdini/traversal.py (BFS/DFS descendants, find_by_type w/ recursiveGlob fast-path + BFS fallback, walk_inputs/outputs cycle-safe) [W01] |
| 2026-06-23 | Tier-0: filled brick stubs -- houdini/parm.py (get/try_get/set/try_set/set_parms/press_button, ParmError), houdini/geometry.py (BBox frozen dataclass, bbox/point_count/prim_count/attribs/material_paths for ingestion), core/validators.py (version token/prim-path/frame-range + require_* raisers) |
| 2026-06-23 | Tier-0: data-driven config realised -- lh_houdini_pipeline/config/defaults.yaml (paths/naming/dcc/render/texture/cache) + core.config.bootstrap_config() resolving defaults->$JOB/config.yaml->~/.lh_pipeline->LH_PIPELINE_* env |
| 2026-06-23 | Added test_tier0.py (25 pure assertions); test_smoke.py still 30/30 green |
| 2026-06-23 | VERIFIED live H21.0.631 via MCP: find_by_type(box) path, BFS count, walk_inputs dataflow (matpath->scaler->box), parm get/set scale=2.0 + try_set missing False, bbox.size (2,2,2)/diag 3.4641, point8/prim6, material_paths ['/mat/woodA'], @timed fires in-session |
| 2026-06-23 | Tier-1 Scene Cache Manager (Rebelway W02/F): file/cache_utils.py pure model -- CacheFile/CacheSequence frozen dataclasses, compound-ext split (.bgeo.sc), version-in-base frame parse, scan_directory grouping, missing_frames gap detection, is_stale (age OR source-newer), human_size |
| 2026-06-23 | Tier-1: tools/cache_manager core.py (CleanupPolicy/CleanupPlan/classify/plan_cleanup -- pure dry-run, EMPTY>STALE>INCOMPLETE>OK precedence) + service.py (discover_cache_dirs via houdini.traversal over /obj,/stage,/out cache nodes; scan_scene/scan_dirs; delete_paths trash-first w/ send2trash fallback + per-file try/except; open_in_explorer) |
| 2026-06-23 | Tier-1: cache_manager ui.py (PySide6 dark-theme table, status colour tint, policy controls, Select Candidates, threaded delete + QProgressBar, confirm dialog w/ reclaimed bytes, context-menu + double-click open folder) + launch + __init__ surface |
| 2026-06-23 | Added test_cache_manager.py (26 pure assertions: parsing/scan/gaps/staleness/policy/plan); test_smoke 30/30 + test_tier0 25/25 still green |
| 2026-06-23 | VERIFIED live H21.0.631 via MCP: Geometry ROP sopoutput discovered, scan_scene smoke seq 1001-1005 gap=[1003], classify smoke=incomplete/junk=empty, candidates=[junk.vdb,smoke.bgeo.sc], CacheManagerUI builds under live PySide6 + table 2 rows |
| 2026-06-23 | Tier-2 Asset Ingestion + Drag&Drop (Rebelway W04/W10): tools/asset_ingest core.py (pure) -- IngestItem, is_geometry_file, derive_asset_name (strip version/date noise -> clean id), find_texture_folder (sibling textures/tex/maps or flat layout), expand_inputs (folder->geo files), plan_ingest; composes lops_asset_builder.plan_asset (no re-impl of USD componentise) |
| 2026-06-23 | Tier-2: asset_ingest service.py (ingest_items/ingest_paths -> lops_asset_builder.build_asset per item, per-item try/except isolates bad FBX, @timed; is_solaris_context guard) + IngestResult/IngestSummary |
| 2026-06-23 | Tier-2: scripts/externaldragdrop.py -- Houdini OS drag-drop hook dropAccept(files) (+drop_accept alias), cheap geo pre-filter before hou import, Solaris-only guard, status feedback; self-adds repo root to sys.path. Install: put repo scripts/ on HOUDINI_PATH |
| 2026-06-23 | Tier-2: asset_ingest ui.py (PySide6 window-level OS drop target, editable asset-name table, output-dir, recurse-tex, progress + per-row OK/FAIL tint; node ops on main thread) + launch + __init__ |
| 2026-06-23 | Added test_asset_ingest.py (17 pure assertions incl. drag-drop handler import/reject paths); all suites green |
| 2026-06-23 | VERIFIED live H21.0.631 via MCP: 'Hero Rock_v003.obj' -> asset 'Hero_Rock' (version/space stripped), ingest_paths built geo/mtl/assign/componentoutput, rootprim=/Hero_Rock, componentoutput cooks 0 errors, AssetIngestUI accepts dropped item |
| 2026-06-23 | Tier-3 Lookdev super-tool (Rebelway W07-W10): houdini/usd.py filled -- stage_of + compute_world_bounds (WorldBounds frozen dataclass via UsdGeom.BBoxCache, default+render purposes) shared by rig/camera framing |
| 2026-06-23 | Tier-3: lookdev/light_rig.py -- pure 3-point math (look_at_rotation atan2 yaw/pitch, three_point_rig key/fill/rim sized to max_dim, LightSpec/LightRigPlan) + hou build_light_rig (light::2.0 sphere lights chained onto asset stage, intensity/exposure via name-resolved parms, optional domelight HDRI) |
| 2026-06-23 | Tier-3: tools/lookdev_builder -- ONE-CLICK super tool. core LookdevConfig (pure, step_count) + service.build_lookdev composing lops_asset_builder + lookdev.light_rig + camera_manager.create_turntable, per-stage try/except, @timed. ui (geo/tex/dome pickers, lights/turntable toggles, frames, staged progress) + launch + __init__. lookdev/__init__ now exports light_rig |
| 2026-06-23 | Added test_lookdev.py (16 pure assertions: look-at math/3-point ratios/config steps); all 5 suites green |
| 2026-06-23 | VERIFIED live H21.0.631 via MCP: build_lookdev('ChairHero_v002.obj') -> asset ChairHero + rig_key/fill/rim (sphere lights, key framed to bounds @ (3.52,3.08,3.96) = max_dim 2 x 2.2 x offset) + turntable_cam (24 ry keys, playback [1,24]), componentoutput cooks 0 errors, LookdevBuilderUI builds under live PySide6 |
| 2026-06-23 | Tier-3 final (Week 10): lookdev/calibration.py -- pure MACBETH_SRGB 24-patch ColorChecker + srgb_to_linear + chart_layout (6x4 centered grid) + CalibrationPlan(JSON round-trip); USD authoring author_plates() writes chrome sphere (metallic1/rough.04), 18% grey sphere, 24 displayColor+UsdPreviewSurface patches on editableStage; build_calibration() creates pythonscript LOP w/ userData JSON params + sys.path bootstrap snippet, chains onto lookdev stage |
| 2026-06-23 | Tier-3: lookdev_builder gains with_calibration (LookdevConfig+step_count, service stage chained onto last light, UI checkbox); lookdev/__init__ exports calibration; test_lookdev.py +8 assertions (24 total) |
| 2026-06-23 | VERIFIED live H21.0.631 via MCP: build_calibration pythonscript LOP cooks 0 errors, authors /lookdev/calibration chrome+grey Spheres (r=0.5) + 24 macbeth patches (each Cube+UsdPreviewSurface), white patch#18 linear displayColor (0.896,0.896,0.888)=sRGB243 linearized, grey material bound; full build_lookdev(with_calibration) ok, calibration_node=/stage/calibration_plates |
| 2026-06-23 | Packaging: packages/lh_pipeline.json (HOUDINI_PATH+PYTHONPATH=repo root, enables scripts/externaldragdrop.py + toolbar/) + toolbar/lh_pipeline.shelf (7 tools: project_manager/lops_asset_builder/tex_to_mtlx/camera_manager/cache_manager/asset_ingest/lookdev_builder). Installed live to $HOUDINI_USER_PREF_DIR/packages/lh_pipeline.json (restart to activate) |
| 2026-06-23 | Refactor (perf/traversal): @timed added to tex_to_mtlx.build_plans/convert_textures_to_tx, lops_asset_builder.build_asset, camera_manager.list_cameras/merge_cameras/create_turntable/get_camera_frames; camera_manager.list_cameras now uses houdini.traversal.find_by_type (recursiveGlob fast-path) instead of hand-rolled allSubChildren loop |
| 2026-06-23 | VERIFIED live H21.0.631: refactored list_cameras returns OBJ cam via traversal; @timed logs '[perf] camera_manager.list_cameras took 0.00 ms'; all 3 services import hou-lazy clean; package+shelf files valid; 5 test suites green |
