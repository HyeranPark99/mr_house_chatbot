"""Weather data fetcher using wttr.in (no API key required)."""

import re

import requests

WEATHER_KEYWORDS = {
    "weather", "temperature", "temp", "forecast", "hot", "cold",
    "warm", "rain", "raining", "sunny", "cloudy", "wind", "windy",
    "humid", "humidity", "storm", "snow", "outside", "climate",
}

# Patterns like "weather in Seoul", "temperature in New York", "forecast for London"
_LOCATION_RE = re.compile(
    r"(?:weather|temperature|temp|forecast|climate)\s+(?:in|for|at|of)\s+([A-Za-z\s,]+?)(?:\?|$|\.|\s*$)",
    re.IGNORECASE,
)

WTTR_URL = "https://wttr.in/{location}?format=j1"


def is_weather_query(text: str) -> bool:
    """Return True if the message appears to be asking about weather."""
    lowered = text.lower()
    return any(kw in lowered for kw in WEATHER_KEYWORDS)


def extract_location(text: str) -> str:
    """Extract a location name from a weather query, or empty string if not found."""
    match = _LOCATION_RE.search(text)
    if match:
        return match.group(1).strip()
    return ""


def fetch_weather(location: str) -> dict | None:
    """Fetch current weather for a location from wttr.in.

    Returns a dict with keys: location, temp_c, temp_f, condition, humidity,
    wind_kph, feels_like_c — or None on failure.
    """
    if not location or not location.strip():
        return None

    try:
        response = requests.get(
            WTTR_URL.format(location=location.strip().replace(" ", "+")),
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        current = data["current_condition"][0]
        area = data.get("nearest_area", [{}])[0]
        area_name = area.get("areaName", [{}])[0].get("value", location)
        country = area.get("country", [{}])[0].get("value", "")

        return {
            "location": f"{area_name}, {country}".strip(", "),
            "temp_c": current["temp_C"],
            "temp_f": current["temp_F"],
            "condition": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"],
            "wind_kph": current["windspeedKmph"],
            "feels_like_c": current["FeelsLikeC"],
            "feels_like_f": current["FeelsLikeF"],
        }
    except Exception as exc:
        print(f"[WEATHER] Failed to fetch weather for '{location}': {exc}", flush=True)
        return None


def format_weather_context(weather: dict) -> str:
    """Format weather data as a compact context injection for the system prompt."""
    return (
        f"[ATMOSPHERIC SENSORS — {weather['location'].upper()}] "
        f"Temperature: {weather['temp_c']}°C / {weather['temp_f']}°F "
        f"(feels like {weather['feels_like_c']}°C). "
        f"Conditions: {weather['condition']}. "
        f"Humidity: {weather['humidity']}%. "
        f"Wind: {weather['wind_kph']} km/h."
    )
