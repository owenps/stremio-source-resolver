from __future__ import annotations

import re
from dataclasses import dataclass, field

from .models import SourceCandidate


@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    min_size_mb: int = 300
    max_size_gb: int = 200
    reject_terms: tuple[str, ...] = ("cam", "hdcam", "telesync", "ts", "scr", "screener")
    reject_extensions: tuple[str, ...] = (
        ".exe",
        ".bat",
        ".cmd",
        ".msi",
        ".scr",
        ".js",
        ".vbs",
        ".ps1",
        ".zip",
        ".rar",
        ".7z",
        ".iso",
    )
    require_magnet: bool = True
    extra_reject_terms: tuple[str, ...] = field(default_factory=tuple)


class SafetyFilter:
    def __init__(self, policy: SafetyPolicy | None = None):
        self.policy = policy or SafetyPolicy()

    def allow(self, candidate: SourceCandidate) -> bool:
        if self.policy.require_magnet and not candidate.magnet_uri.startswith("magnet:"):
            return False

        label = (candidate.display_name or "").lower()
        quality = (candidate.quality or "").lower()
        haystack = f"{label} {quality}"

        if any(ext.lower() in label for ext in self.policy.reject_extensions):
            return False

        for term in (*self.policy.reject_terms, *self.policy.extra_reject_terms):
            term = str(term).lower().strip()
            if term and re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", haystack):
                return False

        size = candidate.size_bytes or 0
        if size:
            if size < self.policy.min_size_mb * 1024 * 1024:
                return False
            if size > self.policy.max_size_gb * 1024 * 1024 * 1024:
                return False

        return True
