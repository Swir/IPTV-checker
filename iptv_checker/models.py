from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Channel:
    name: str
    url: str
    group: str = "Ungrouped"
    tvg_id: str = ""
    tvg_name: str = ""
    logo: str = ""
    source: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    status: str = "untested"  # untested | online | offline | cancelled
    http_status: int | None = None
    latency_ms: int | None = None
    content_type: str = ""
    error: str = ""

    @property
    def display_group(self) -> str:
        return self.group.strip() or "Ungrouped"
