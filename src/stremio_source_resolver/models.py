from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

_BTIH_RE = re.compile(r"btih:([a-fA-F0-9]{40}|[a-zA-Z2-7]{32})", re.IGNORECASE)


def format_bytes(value: int | None) -> str:
    if not value:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(value)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024
    return f"{value}B"


@dataclass(frozen=True, slots=True)
class AddonConfig:
    name: str
    base_url: str
    timeout_seconds: int = 30

    @property
    def stream_base_url(self) -> str:
        url = self.base_url.strip().rstrip("/")
        if url.endswith("/manifest.json"):
            url = url[: -len("/manifest.json")]
        return url


@dataclass(slots=True)
class SourceCandidate:
    provider: str
    display_name: str
    quality: str
    magnet_uri: str
    rank: int = 0
    size_bytes: int | None = None
    cached: bool = False
    seeders: int | None = None
    info_hash: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def fingerprint(self) -> str:
        if self.info_hash:
            return f"btih:{self.info_hash.lower()}"
        match = _BTIH_RE.search(self.magnet_uri or "")
        if match:
            return f"btih:{match.group(1).lower()}"
        return "sha256:" + hashlib.sha256((self.magnet_uri or "").encode("utf-8")).hexdigest()

    @property
    def id(self) -> str:
        raw = f"{self.provider}\0{self.fingerprint}\0{self.quality}\0{self.display_name}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def option_label(self) -> str:
        bits = [self.quality or self.display_name]
        if self.size_bytes:
            bits.append(format_bytes(self.size_bytes))
        if self.cached:
            bits.append("cached")
        return " - ".join(bits)[:100]
