# stremio-source-resolver

[![tests](https://github.com/owenps/stremio-source-resolver/actions/workflows/test.yml/badge.svg)](https://github.com/owenps/stremio-source-resolver/actions/workflows/test.yml)

Small Python library for resolving movie source candidates from authorized Stremio addon endpoints.

It calls standard Stremio stream endpoints:

```text
{addon_base_url}/stream/movie/{imdb_id}.json
```

and normalizes returned streams into ranked source candidates with quality, size, cache status, seeders, info hash, and magnet URI.

## Scope

- movie sources only
- caller supplies authorized addon URLs
- no hardcoded public addon URLs
- no TorBox/Discord/Nuvio integration
- no downloading

## Install locally

```bash
pip install -e .
```

## Example

```python
import asyncio
from stremio_source_resolver import AddonConfig, StremioSourceResolver

async def main():
    resolver = StremioSourceResolver([
        AddonConfig(name="authorized-addon", base_url="https://example.invalid/addon-config")
    ])
    candidates = await resolver.resolve_movie("tt0062622")
    for c in candidates[:5]:
        print(c.option_label, c.display_name)

asyncio.run(main())
```


## Torrentio-compatible example

Use the [Torrentio configure page](https://torrentio.strem.fun/configure) to generate your own manifest URL, then pass it via env var. Do not commit private/debrid tokens.

```bash
export TORRENTIO_MANIFEST_URL="https://torrentio.example/config/manifest.json"
export IMDB_ID="tt0062622"
python examples/torrentio.py
```

## Notes

Use only with content and providers you are authorized to access.
