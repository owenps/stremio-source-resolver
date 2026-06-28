from stremio_source_resolver.models import AddonConfig, SourceCandidate
from stremio_source_resolver.parsing import infer_quality, magnet_from_stream, parse_seeders, parse_size_bytes
from stremio_source_resolver.safety import SafetyFilter, SafetyPolicy


def test_addon_manifest_url_normalizes_to_base_url():
    addon = AddonConfig("x", "https://example.invalid/config/manifest.json")
    assert addon.stream_base_url == "https://example.invalid/config"


def test_parse_size_bytes():
    assert parse_size_bytes("Size: 1.5 GB") == int(1.5 * 1024**3)
    assert parse_size_bytes("700 MB") == 700 * 1024**2


def test_parse_seeders():
    assert parse_seeders("seeders: 42") == 42
    assert parse_seeders("Seeds 7") == 7


def test_infer_quality():
    assert infer_quality("Movie 2160p HDR REMUX") == "2160p HDR REMUX"
    assert infer_quality("Movie 1080p") == "1080p"


def test_magnet_from_info_hash():
    h = "a" * 40
    magnet, info_hash = magnet_from_stream({"infoHash": h}, "Test File")
    assert info_hash == h
    assert magnet == f"magnet:?xt=urn:btih:{h}&dn=Test%20File"


def test_safety_filter_rejects_bad_extension():
    candidate = SourceCandidate(
        provider="test",
        display_name="movie.mkv.exe",
        quality="1080p",
        magnet_uri="magnet:?xt=urn:btih:" + "a" * 40,
        size_bytes=1024**3,
    )
    assert not SafetyFilter().allow(candidate)


def test_safety_filter_respects_max_size():
    candidate = SourceCandidate(
        provider="test",
        display_name="movie.mkv",
        quality="1080p",
        magnet_uri="magnet:?xt=urn:btih:" + "a" * 40,
        size_bytes=201 * 1024**3,
    )
    assert not SafetyFilter(SafetyPolicy(max_size_gb=200)).allow(candidate)
