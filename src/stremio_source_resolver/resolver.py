from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from .models import AddonConfig, SourceCandidate
from .parsing import (
    first_line,
    infer_quality,
    magnet_from_stream,
    parse_seeders,
    parse_size_bytes,
    rank_candidate,
)
from .safety import SafetyFilter, SafetyPolicy


class StremioSourceResolver:
    def __init__(
        self,
        addons: Iterable[AddonConfig | dict[str, Any]],
        *,
        safety_policy: SafetyPolicy | None = None,
        user_agent: str = "stremio-source-resolver/0.1",
    ):
        self.addons = [self._coerce_addon(addon) for addon in addons]
        self.safety_filter = SafetyFilter(safety_policy)
        self.user_agent = user_agent

    async def resolve_movie(self, imdb_id: str, *, limit: int | None = None) -> list[SourceCandidate]:
        if not imdb_id:
            return []

        import aiohttp

        out: list[SourceCandidate] = []
        async with aiohttp.ClientSession(headers=self._headers()) as session:
            for addon in self.addons:
                out.extend(await self._resolve_movie_from_addon(session, addon, imdb_id))

        deduped: dict[str, SourceCandidate] = {}
        for candidate in out:
            if not self.safety_filter.allow(candidate):
                continue
            prior = deduped.get(candidate.fingerprint)
            if prior is None or candidate.rank > prior.rank:
                deduped[candidate.fingerprint] = candidate

        ranked = sorted(deduped.values(), key=lambda c: (c.rank, c.cached, c.size_bytes or 0), reverse=True)
        return ranked[:limit] if limit else ranked

    async def _resolve_movie_from_addon(
        self,
        session: Any,
        addon: AddonConfig,
        imdb_id: str,
    ) -> list[SourceCandidate]:
        url = f"{addon.stream_base_url}/stream/movie/{imdb_id}.json"
        async with session.get(url, timeout=addon.timeout_seconds) as resp:
            if resp.status == 404:
                return []
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"{addon.name} HTTP {resp.status}: {data}")

        streams = data.get("streams") or []
        if not isinstance(streams, list):
            return []

        candidates: list[SourceCandidate] = []
        for index, stream in enumerate(streams):
            if not isinstance(stream, dict):
                continue
            candidate = self._candidate_from_stream(addon, stream, index)
            if candidate:
                candidates.append(candidate)
        return candidates

    def _candidate_from_stream(
        self,
        addon: AddonConfig,
        stream: dict[str, Any],
        index: int,
    ) -> SourceCandidate | None:
        behavior = stream.get("behaviorHints") or {}
        if not isinstance(behavior, dict):
            behavior = {}

        text_blob = "\n".join(
            str(x or "")
            for x in (
                stream.get("title"),
                stream.get("name"),
                stream.get("description"),
                behavior.get("filename"),
            )
        )
        display_name = first_line(
            behavior.get("filename"),
            stream.get("title"),
            stream.get("name"),
            stream.get("description"),
        )
        magnet_uri, info_hash = magnet_from_stream(stream, display_name)
        if not magnet_uri:
            return None

        size_bytes = parse_size_bytes(text_blob, behavior.get("videoSize"))
        seeders = parse_seeders(text_blob)
        quality = infer_quality(text_blob)
        cached = bool(stream.get("cached")) or "cached" in text_blob.lower()

        return SourceCandidate(
            provider=addon.name,
            display_name=display_name[:300],
            quality=quality,
            magnet_uri=magnet_uri,
            rank=rank_candidate(quality, cached, size_bytes, seeders, index),
            size_bytes=size_bytes,
            cached=cached,
            seeders=seeders,
            info_hash=info_hash,
            raw=stream,
        )

    def _headers(self) -> dict[str, str]:
        return {
            "referer": "https://web.stremio.com/",
            "user-agent": self.user_agent,
        }

    @staticmethod
    def _coerce_addon(addon: AddonConfig | dict[str, Any]) -> AddonConfig:
        if isinstance(addon, AddonConfig):
            return addon
        return AddonConfig(
            name=str(addon.get("name") or "stremio"),
            base_url=str(addon.get("base_url") or ""),
            timeout_seconds=int(addon.get("timeout_seconds") or 30),
        )
