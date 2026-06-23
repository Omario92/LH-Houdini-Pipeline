# AI Agent Guide

## Rules
- Follow architectural guidelines specified in CLAUDE.md.
- Ensure all public functions/classes have docstrings.
- Ensure proper type-hinting and immutable structures where requested.

## Commands
- Run smoke tests: `python test_smoke.py`

## Recent Changes
- Created README.md and initialized Git repository to push code to GitHub.
- Added Camera Export feature (USD, Alembic, Nuke .nk) and USD baking to the Camera Manager.
- Added USD Camera Variants feature (VariantSets for focal lengths and angle transforms) to the Camera Manager.
- Added programmatic HDA packaging module (HDA creation, Python HDA modules, event scripts, dynamic ParmTemplateGroup) and test suite.
- Redesigned the LOPs Asset Builder UI with Drag & Drop support, collapsible advanced options (Simulation Proxy/Viewport Proxy Quality), color-coded logging panel, and threaded texture conversion.
- Bootstrapped Houdini AI Assistant (Phase 1-4): OOP folder tree, async streaming client, scene context inspector, markdown chat UI, main-thread HOM tool execution, and modal Action Approval dialog.
- Completed Phase 5: Upgraded programmatic HDA scaffolding tool with parameter template conversions, dynamic PythonModule/OnCreated event script packaging, expanded HDA Architect system prompts, and wrote comprehensive unit tests.
- Completed Phase 6: Implemented socket-based MCP TCP Server and Client delegation, signal-based thread dispatching for HOM safety, approval callback gates, PySide6 UI panels, and integration unit tests.
- Completed Phase 7: Integrated pipeline tool bindings (Project Manager create project & Camera Manager turntable orbit), added AI Assistant to lh_pipeline.shelf, polished UI elements and bubbles using theme style tokens, hardened MCP client/server error handling and timeouts, and generated detailed user documentation.
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
@CLAUDE.md
