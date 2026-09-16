from __future__ import annotations

import re
from collections.abc import Iterable
from urllib.parse import urlsplit, urlunsplit
from .models import Channel

ATTR_RE = re.compile(r'([\w-]+)="([^"]*)"')


def parse_extinf(line: str) -> tuple[dict[str, str], str]:
    payload = line[len("#EXTINF:") :] if line.startswith("#EXTINF:") else line
    attrs = {key.lower(): value for key, value in ATTR_RE.findall(payload)}
    name = payload.rsplit(",", 1)[-1].strip() if "," in payload else attrs.get("tvg-name", "")
    return attrs, name or attrs.get("tvg-name", "Unnamed channel") or "Unnamed channel"


def parse_m3u(text: str, source: str = "") -> list[Channel]:
    channels: list[Channel] = []
    pending_attrs: dict[str, str] = {}
    pending_name = ""
    pending_group = ""
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#EXTINF:"):
            pending_attrs, pending_name = parse_extinf(line)
            pending_group = pending_attrs.get("group-title", "")
            continue
        if line.startswith("#EXTGRP:"):
            pending_group = line.partition(":")[2].strip() or pending_group
            continue
        if line.startswith("#"):
            continue
        if pending_name or pending_attrs or pending_group:
            channels.append(Channel(name=pending_name or pending_attrs.get("tvg-name", "Unnamed channel"), url=line, group=pending_group or pending_attrs.get("group-title", "Ungrouped"), tvg_id=pending_attrs.get("tvg-id", ""), tvg_name=pending_attrs.get("tvg-name", ""), logo=pending_attrs.get("tvg-logo", ""), source=source, attributes=dict(pending_attrs)))
            pending_attrs = {}
            pending_name = ""
            pending_group = ""
    return channels


def deduplicate_channels(channels: Iterable[Channel]) -> list[Channel]:
    seen: set[tuple[str, str]] = set()
    result: list[Channel] = []
    for channel in channels:
        key = (channel.url.strip(), channel.name.strip().casefold())
        if key not in seen:
            seen.add(key)
            result.append(channel)
    return result


def build_m3u(channels: Iterable[Channel]) -> str:
    lines = ["#EXTM3U"]
    for channel in channels:
        attrs = []
        if channel.tvg_id:
            attrs.append(f'tvg-id="{channel.tvg_id}"')
        if channel.tvg_name:
            attrs.append(f'tvg-name="{channel.tvg_name}"')
        if channel.logo:
            attrs.append(f'tvg-logo="{channel.logo}"')
        attrs.append(f'group-title="{channel.display_group}"')
        lines.append(f"#EXTINF:-1 {' '.join(attrs)},{channel.name}")
        lines.append(channel.url)
    return "\n".join(lines) + "\n"


def redact_url(url: str) -> str:
    """Hide user-info and query data from the URL shown in the table."""
    try:
        parts = urlsplit(url)
        host = parts.netloc.rsplit("@", 1)[-1]
        return urlunsplit((parts.scheme, host, parts.path, "", ""))
    except Exception:
        return url
