#!/usr/bin/env python3
"""Offline checks for weather query parsing. Run: python scripts/test_weather.py

Only the parsing is covered — fetch_weather hits the network and is exercised
by --live.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "demo"))

from weather import (  # noqa: E402
    DEFAULT_LOCATION,
    extract_location,
    fetch_weather,
    format_weather_context,
    is_weather_query,
    resolve_location,
)

# (message, is_weather_query, resolve_location)
CASES = [
    ("What's the weather in Seoul?", True, "Seoul"),
    ("How's the weather in Seoul today?", True, "Seoul"),
    ("What is the temperature in New York City right now?", True, "New York City"),
    ("Is it raining in London", True, "London"),
    ("How cold is it in Reykjavik at the moment?", True, "Reykjavik"),
    ("What's the forecast for Paris, France?", True, "Paris, France"),
    # No location named — House reports on his own city
    ("What is the weather like?", True, DEFAULT_LOCATION),
    ("Is it hot outside?", True, DEFAULT_LOCATION),
    ("What's the temperature right now?", True, DEFAULT_LOCATION),
    # In-universe aliases map to the real city
    ("Tell me about the New Vegas climate", True, DEFAULT_LOCATION),
    ("Is it windy on the Strip?", True, DEFAULT_LOCATION),
    ("How hot is the Mojave?", True, DEFAULT_LOCATION),
    # Not weather at all
    ("Who are you?", False, None),
    ("Tell me about the NCR treaty", False, None),
    ("What is your plan for humanity?", False, None),
]


def main() -> int:
    failures = 0

    for message, expect_weather, expect_location in CASES:
        got_weather = is_weather_query(message)
        if got_weather != expect_weather:
            print(f"FAIL is_weather_query({message!r}) = {got_weather}, want {expect_weather}")
            failures += 1
            continue
        if not expect_weather:
            continue
        got_location = resolve_location(message)
        if got_location != expect_location:
            print(
                f"FAIL resolve_location({message!r}) = {got_location!r}, "
                f"want {expect_location!r} (raw extract: {extract_location(message)!r})"
            )
            failures += 1

    if "--live" in sys.argv:
        print("\n-- live wttr.in lookups --")
        for location in ("Seoul", DEFAULT_LOCATION, "Nowhereville XYZQ"):
            weather = fetch_weather(location)
            print(f"{location}: {format_weather_context(weather) if weather else 'no data'}")

    total = sum(1 for _, w, _ in CASES if w) + len(CASES)
    print(f"\n{total - failures}/{total} checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
