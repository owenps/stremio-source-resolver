from __future__ import annotations

import re
from typing import Any
from urllib.parse import quote

_HASH_RE = re.compile(r"\b[a-fA-F0-9]{40}\b")
_SIZE_RE = re.compile(r"(?:[\w ]*size[: ]*)?([\d.]+)\s*(TB|GB|MB)\b", re.IGNORECASE)
_SEED_RE = re.compile(r"(?:seed(?:er)?s?)\s*[: ]\s*(\d+)", re.IGNORECASE)


def first_line(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text.splitlines()[0].strip()
    return "Unknown source"


def parse_size_bytes(text: str, fallback: Any = None) -> int | None:
    try:
        if fallback:
            n = int(float(fallback))
            if n > 0:
                return n
    except Exception:
        pass

    match = _SIZE_RE.search(text or "")
    if not match:
        return None
    n = float(match.group(1))
    unit = match.group(2).upper()
    if unit == "TB":
        n *= 1024**4
    elif unit == "GB":
        n *= 1024**3
    else:
        n *= 1024**2
    return int(n)


def parse_seeders(text: str) -> int | None:
    match = _SEED_RE.search(text or "")
    return int(match.group(1)) if match else None


def infer_quality(text: str) -> str:
    t = (text or "").lower()
    resolution = "unknown"
    if any(x in t for x in ("2160p", "4k", "uhd")):
        resolution = "2160p"
    elif "1440p" in t:
        resolution = "1440p"
    elif "1080p" in t:
        resolution = "1080p"
    elif "720p" in t:
        resolution = "720p"
    elif "480p" in t:
        resolution = "480p"

    tags: list[str] = []
    if re.search(r"\b(dv|dolby[ .-]?vision)\b", t):
        tags.append("DV")
    if re.search(r"\bhdr(10)?\b", t):
        tags.append("HDR")
    if "remux" in t:
        tags.append("REMUX")
    return " ".join([resolution, *tags]).strip()


def rank_candidate(quality: str, cached: bool, size_bytes: int | None, seeders: int | None, index: int) -> int:
    q = (quality or "").lower()
    score = 1000 - index
    if "2160" in q:
        score += 400
    elif "1440" in q:
        score += 300
    elif "1080" in q:
        score += 250
    elif "720" in q:
        score += 150
    if "remux" in q:
        score += 30
    if "hdr" in q or "dv" in q:
        score += 20
    if cached:
        score += 500
    if seeders:
        score += min(seeders, 200)
    if size_bytes:
        score += min(size_bytes // (1024**3), 100)
    return int(score)


def hash_from_stream(stream: dict[str, Any]) -> str | None:
    info_hash = str(stream.get("infoHash") or stream.get("info_hash") or "").strip()
    if _HASH_RE.fullmatch(info_hash):
        return info_hash.lower()
    url = str(stream.get("url") or "")
    match = _HASH_RE.search(url)
    return match.group(0).lower() if match else None


def magnet_from_stream(stream: dict[str, Any], display_name: str) -> tuple[str | None, str | None]:
    url = str(stream.get("url") or "").strip()
    if url.startswith("magnet:"):
        return url, hash_from_stream(stream)

    info_hash = hash_from_stream(stream)
    if not info_hash:
        return None, None
    return f"magnet:?xt=urn:btih:{info_hash}&dn={quote(display_name)}", info_hash
