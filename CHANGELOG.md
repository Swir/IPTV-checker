# Changelog

## 2.0.0

- Migrated the desktop UI from PyQt5 to Qt 6 / PySide6.
- Replaced separate PL/EN scripts with automatic EN/PL/NO language selection and English fallback.
- Added real M3U/M3U8 metadata parsing and stream URL storage.
- Added bounded per-stream health checks with HTTP status, latency and content type.
- Added local playlist drag & drop.
- Added live search, group filter and health-status filter.
- Added duplicate removal.
- Added filtered M3U export plus CSV/JSON reports.
- Improved VLC detection, selected-stream playback and persistent settings.
- Added Matrix Blue UI and a dedicated application icon.
- Added Python 3.11–3.14 CI and a Windows EXE build workflow.
- Kept legacy launcher filenames for compatibility.
