#!/usr/bin/env python3
"""Generate and verify SWIR Progress SVG PRO assets for IPTV Checker."""
from __future__ import annotations

import argparse
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "readme"
PROJECT = "IPTV Checker"
SUMMARY = "No trustworthy product-completion denominator is maintained in this repository."

CARD = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc">
<title id="title">{PROJECT} product progress</title>
<desc id="desc">{PROJECT} product progress is not numerically measured because this repository has no authoritative product roadmap.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient>
  <pattern id="grid" width="26" height="26" patternUnits="userSpaceOnUse"><path d="M26 0H0V26" fill="none" stroke="#62E5FF" stroke-opacity=".05"/></pattern>
</defs>
<rect x="1" y="1" width="1198" height="178" rx="24" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".24"/>
<rect x="1" y="1" width="1198" height="178" rx="24" fill="url(#grid)"/>
<text x="50" y="43" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="17" font-weight="700" letter-spacing="4">SWIR PROGRESS</text>
<text x="50" y="78" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">{PROJECT}</text>
<text x="50" y="105" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="15">Product progress · {SUMMARY}</text>
<text x="1090" y="78" text-anchor="end" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="800">N/A</text>
<text x="1090" y="105" text-anchor="end" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="14" font-weight="700">NO ROADMAP</text>
<rect x="50" y="127" width="1100" height="22" rx="11" fill="#08131F" stroke="#62E5FF" stroke-opacity=".16"/>
<path d="M70 138H1130" stroke="url(#accent)" stroke-width="2" stroke-dasharray="8 12" opacity=".35"/>
<text x="50" y="169" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="12">Counter: not measured · release status is tracked separately</text>
</svg>
'''

MINI = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="72" viewBox="0 0 900 72" role="img" aria-labelledby="title desc">
<title id="title">{PROJECT} compact product progress</title>
<desc id="desc">Product completion is N/A because there is no authoritative roadmap denominator.</desc>
<defs><linearGradient id="accent" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient></defs>
<rect x="1" y="1" width="898" height="70" rx="18" fill="#02050A" stroke="#62E5FF" stroke-opacity=".22"/>
<text x="24" y="27" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="700" letter-spacing="2">SWIR ROADMAP</text>
<text x="24" y="52" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="20" font-weight="800">N/A</text>
<rect x="170" y="24" width="700" height="20" rx="10" fill="#08131F"/>
<path d="M185 34H855" stroke="url(#accent)" stroke-width="2" stroke-dasharray="7 11" opacity=".35"/>
<text x="870" y="58" text-anchor="end" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="12">no authoritative product roadmap</text>
</svg>
'''

TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc">
<title id="title">SWIR Progress SVG PRO template</title>
<desc id="desc">Reusable local template. TEMPLATE ONLY — NOT PROJECT DATA.</desc>
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient>
  <linearGradient id="fill" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient>
</defs>
<rect x="1" y="1" width="1198" height="178" rx="24" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".22"/>
<text x="50" y="46" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="700">SWIR PROGRESS · TEMPLATE ONLY</text>
<text x="50" y="82" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="30" font-weight="800">PROJECT NAME</text>
<text x="50" y="108" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="15">SCOPE · replace from authoritative data</text>
<text x="1090" y="82" text-anchor="end" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="34" font-weight="800">N/A</text>
<rect x="50" y="126" width="1100" height="24" rx="12" fill="#08131F" stroke="#62E5FF" stroke-opacity=".14"/>
<text x="50" y="169" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="12">Do not embed this template as live project progress.</text>
</svg>
'''

EXPECTED = {"progress-card.svg": CARD, "progress-mini.svg": MINI, "progress-template.svg": TEMPLATE}

def validate_svg(text: str) -> None:
    root = ET.fromstring(text)
    if root.tag.split("}")[-1] != "svg":
        raise SystemExit("root element is not svg")
    values = [float(v) for v in root.attrib["viewBox"].split()]
    if any(not (v == v and abs(v) != float("inf")) for v in values):
        raise SystemExit("non-finite viewBox")
    for elem in root.iter():
        for key in ("x", "y", "width", "height", "rx", "ry"):
            if key in elem.attrib:
                value = float(elem.attrib[key])
                if not (value == value and abs(value) != float("inf")):
                    raise SystemExit(f"non-finite {key}")

def render() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in EXPECTED.items():
        validate_svg(text)
        (OUT / name).write_text(text, encoding="utf-8")

def check() -> None:
    for name, expected in EXPECTED.items():
        validate_svg(expected)
        path = OUT / name
        if not path.exists() or path.read_text(encoding="utf-8") != expected:
            raise SystemExit(f"missing or stale {path.relative_to(ROOT)}")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    for name in ("progress-card.svg", "progress-mini.svg"):
        if f"assets/readme/{name}" not in readme:
            raise SystemExit(f"README does not embed {name}")
    if "N/A" not in readme or "no authoritative product roadmap" not in readme.lower():
        raise SystemExit("README must explain N/A product progress")
    print(f"SWIR progress assets verified for {PROJECT}: product progress N/A (no authoritative roadmap).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    check() if args.check else render()
