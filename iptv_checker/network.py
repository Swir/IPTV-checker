from __future__ import annotations

import asyncio
import time
from pathlib import Path
from threading import Event
from urllib.parse import urlparse

import aiohttp

from .models import Channel
from .parser import parse_m3u

USER_AGENT = "SWIR-IPTV-Checker/2.0 (+https://github.com/Swir/IPTV-checker)"


def _is_http_url(value: str) -> bool:
    return urlparse(value).scheme in {"http", "https"}


async def load_sources(sources: list[str], timeout: float = 15.0) -> tuple[list[Channel], list[str]]:
    """Load only playlist sources explicitly supplied by the user."""
    channels: list[Channel] = []
    errors: list[str] = []
    remote_sources = [source for source in sources if _is_http_url(source)]
    local_sources = [source for source in sources if source not in remote_sources]

    for source in local_sources:
        try:
            path = Path(source).expanduser()
            text = await asyncio.to_thread(path.read_text, encoding="utf-8", errors="replace")
            parsed = parse_m3u(text, source=str(path))
            if not parsed:
                errors.append(f"{source}: no M3U entries found")
            channels.extend(parsed)
        except Exception as exc:
            errors.append(f"{source}: {exc}")

    if remote_sources:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout, headers={"User-Agent": USER_AGENT}) as session:
            for source in remote_sources:
                try:
                    async with session.get(source, allow_redirects=True) as response:
                        response.raise_for_status()
                        text = await response.text(errors="replace")
                    parsed = parse_m3u(text, source=source)
                    if not parsed:
                        errors.append(f"{source}: no M3U entries found")
                    channels.extend(parsed)
                except Exception as exc:
                    errors.append(f"{source}: {exc}")

    return channels, errors


async def check_streams(
    channels: list[Channel],
    concurrency: int = 6,
    timeout: float = 8.0,
    cancel_event: Event | None = None,
) -> list[Channel]:
    """Health-check stream URLs that came from the user's loaded playlists.

    The request is intentionally small and bounded; it reads at most 512 bytes per stream.
    """
    cancel_event = cancel_event or Event()
    semaphore = asyncio.Semaphore(max(1, min(int(concurrency), 8)))
    client_timeout = aiohttp.ClientTimeout(total=max(2.0, min(float(timeout), 30.0)))

    async with aiohttp.ClientSession(timeout=client_timeout, headers={"User-Agent": USER_AGENT}) as session:
        async def check(channel: Channel) -> None:
            if cancel_event.is_set():
                channel.status = "cancelled"
                return
            if not _is_http_url(channel.url):
                channel.status = "offline"
                channel.error = "Unsupported stream URL scheme"
                return

            async with semaphore:
                if cancel_event.is_set():
                    channel.status = "cancelled"
                    return
                started = time.perf_counter()
                try:
                    async with session.get(
                        channel.url,
                        allow_redirects=True,
                        headers={"Range": "bytes=0-511", "Accept": "*/*"},
                    ) as response:
                        channel.http_status = response.status
                        channel.content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip()
                        await response.content.read(512)
                        channel.latency_ms = round((time.perf_counter() - started) * 1000)
                        channel.status = "online" if 200 <= response.status < 400 else "offline"
                        channel.error = "" if channel.status == "online" else f"HTTP {response.status}"
                except Exception as exc:
                    channel.latency_ms = round((time.perf_counter() - started) * 1000)
                    channel.status = "offline"
                    channel.error = str(exc)[:180]

        await asyncio.gather(*(check(channel) for channel in channels))

    return channels
