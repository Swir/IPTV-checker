<div align="center">

<img src="assets/icon.svg" width="120" alt="IPTV Checker icon" />

# IPTV Checker 2.0

### Modern M3U/M3U8 inspector, real stream health checker and VLC launcher

**Python 3.11–3.14 • Qt 6 / PySide6 • aiohttp • Windows / Linux / macOS • EN / PL / NO**

![Python](https://img.shields.io/badge/Python-3.11--3.14-0D1117?style=for-the-badge&logo=python&logoColor=00A6FF)
![Qt](https://img.shields.io/badge/GUI-PySide6%20%7C%20Qt6-0D1117?style=for-the-badge&logo=qt&logoColor=00A6FF)
![aiohttp](https://img.shields.io/badge/NETWORK-aiohttp-0D1117?style=for-the-badge&logo=python&logoColor=00A6FF)
![VLC](https://img.shields.io/badge/PLAYBACK-VLC-0D1117?style=for-the-badge&logo=vlcmediaplayer&logoColor=00A6FF)

[![Profile](https://img.shields.io/badge/Author-Swir-0088FF?style=flat-square&logo=github)](https://github.com/Swir)
[![Stars](https://img.shields.io/github/stars/Swir/IPTV-checker?style=flat-square&color=0088FF)](https://github.com/Swir/IPTV-checker/stargazers)

</div>

---

## What's new in 2.0

IPTV Checker has been rebuilt from the old PyQt5 single-file utility into a current Qt6 application. Version 2.0 parses real stream URLs and M3U metadata, performs bounded health checks in a background worker, keeps the GUI responsive and combines the supported languages in one application.

### Highlights

- Multiple remote M3U/M3U8 playlist sources.
- Drag & drop local `.m3u` and `.m3u8` files.
- Metadata parser for channel name, group, `tvg-id`, `tvg-name` and `tvg-logo`.
- Real per-stream health status instead of marking every parsed entry as working.
- HTTP status, response latency and content type.
- Live filter by channel name, group and status.
- Duplicate detection/removal.
- Export current results to CSV or JSON.
- Save the filtered result as a clean M3U playlist.
- Open the selected stream directly in VLC.
- Automatic VLC discovery plus saved VLC path.
- Configurable timeout and up to 8 bounded parallel checks.
- Matrix Blue Qt6 interface.
- Automatic system-language detection: Polish, Norwegian or English fallback.
- Display-safe stream URLs: user-info and query data are hidden in the table.
- Windows EXE build workflow with a dedicated IPTV Checker icon.
- CI tests for Python 3.11, 3.12, 3.13 and 3.14.

> Use IPTV Checker only with playlists and streams you are authorized to access. The project does not provide subscription content, credentials, accounts, or third-party access.

---

## Quick start

```bash
git clone https://github.com/Swir/IPTV-checker.git
cd IPTV-checker
python -m pip install -r requirements.txt
python run.py
```

Alternative launcher:

```bash
python -m iptv_checker
```

The legacy `checker.py` and `checker english.py` filenames remain as compatibility launchers. Version 2 detects the system language automatically, so separate Polish and English applications are no longer necessary.

---

## How stream checking works

Checks run only for stream URLs found in playlists you explicitly load. The checker uses a small bounded request, follows normal redirects, records status/latency/content type and reads at most 512 bytes from each stream. The interface caps parallel checks at 8 and the timeout at 30 seconds.

A successful health check means the endpoint responded at the time of the test. It does not guarantee continuous playback or codec compatibility.

---

## Project structure

```text
IPTV-checker/
├── iptv_checker/
│   ├── app.py
│   ├── i18n.py
│   ├── models.py
│   ├── network.py
│   ├── parser.py
│   ├── theme.py
│   └── __main__.py
├── assets/
│   └── icon.svg
├── scripts/
│   └── make_icon.py
├── tests/
│   └── test_parser.py
├── .github/workflows/
│   ├── ci.yml
│   └── build-windows.yml
├── run.py
├── checker.py
├── checker english.py
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Build Windows EXE

GitHub Actions includes **Build Windows EXE**. It can be started manually from Actions or automatically from a version tag such as `v2.0.0`.

Local build:

```bash
python -m pip install -r requirements-dev.txt
python scripts/make_icon.py
pyinstaller --noconfirm --clean --onefile --windowed --name IPTV-Checker --icon assets/icon.ico --add-data "assets/icon.svg;assets" run.py
```

---

## Next improvements

- Optional channel-logo preview cache.
- Check history and run-to-run comparison.
- Playlist diff: added / removed / changed channels.
- Optional scheduled re-checks inside the app.
- Release packaging and signed checksums.
- Additional translations without separate source files.

---

<div align="center">

### `LOAD • FILTER • CHECK • EXPORT • PLAY`

**by Swir** · [GitHub profile](https://github.com/Swir)

</div>
