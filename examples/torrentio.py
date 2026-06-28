from __future__ import annotations

import asyncio
import os

from stremio_source_resolver import AddonConfig, StremioSourceResolver


async def main() -> None:
    manifest_url = os.environ["TORRENTIO_MANIFEST_URL"]
    imdb_id = os.environ.get("IMDB_ID", "tt0062622")

    resolver = StremioSourceResolver([
        AddonConfig(name="torrentio", base_url=manifest_url),
    ])

    candidates = await resolver.resolve_movie(imdb_id, limit=10)
    for candidate in candidates:
        print(f"{candidate.option_label} | {candidate.display_name}")


if __name__ == "__main__":
    asyncio.run(main())
