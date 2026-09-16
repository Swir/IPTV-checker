from iptv_checker.parser import build_m3u, deduplicate_channels, parse_m3u, redact_url

SAMPLE = """#EXTM3U
#EXTINF:-1 tvg-id="one" tvg-name="News One" tvg-logo="https://img/logo.png" group-title="News",News One HD
https://example.test/live/one.m3u8
#EXTINF:-1 group-title="Sports",Sport 1
#EXTGRP:Premium Sports
https://example.test/live/sport.ts
"""


def test_parse_m3u_metadata():
    channels = parse_m3u(SAMPLE, source="sample")
    assert len(channels) == 2
    assert channels[0].name == "News One HD"
    assert channels[0].group == "News"
    assert channels[0].tvg_id == "one"
    assert channels[0].logo.endswith("logo.png")
    assert channels[1].group == "Premium Sports"
    assert channels[1].url.endswith("sport.ts")


def test_round_trip_m3u():
    channels = parse_m3u(SAMPLE)
    parsed_again = parse_m3u(build_m3u(channels))
    assert [(c.name, c.url, c.group) for c in parsed_again] == [(c.name, c.url, c.group) for c in channels]


def test_deduplicate():
    channels = parse_m3u(SAMPLE)
    assert len(deduplicate_channels(channels + [channels[0]])) == 2


def test_redact_url_for_display():
    safe = redact_url("http://user:secret@example.test:8080/live/one.m3u8?session=private")
    assert "user" not in safe
    assert "secret" not in safe
    assert "private" not in safe
    assert safe == "http://example.test:8080/live/one.m3u8"
