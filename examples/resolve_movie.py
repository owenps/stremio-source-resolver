from __future__ import annotations

import asyncio
import os

from stremio_source_resolver import AddonConfig, StremioSourceResolver


async def main() -> None:
    addon_url = os.environ["STREMIO_ADDON_URL"]
    imdb_id = os.environ.get("IMDB_ID", "tt0111161")

    resolver = StremioSourceResolver([
        AddonConfig(name="authorized-addon", base_url=addon_url),
    ])
    candidates = await resolver.resolve_movie(imdb_id, limit=10)
    for candidate in candidates:
        print(f"{candidate.option_label} | {candidate.display_name}")


if __name__ == "__main__":
    asyncio.run(main())
