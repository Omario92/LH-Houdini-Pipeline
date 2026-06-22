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
