"""Weather data fetcher using wttr.in (no API key required)."""

import re

import requests

WEATHER_KEYWORDS = {
    "weather", "temperature", "temp", "forecast", "hot", "cold",
    "warm", "rain", "raining", "sunny", "cloudy", "wind", "windy",
    "humid", "humidity", "storm", "snow", "outside", "climate",
}

# Mr. House's own city — used when a weather question names no location.
DEFAULT_LOCATION = "Las Vegas"

# In-universe names for the same patch of desert.
_LOCATION_ALIASES = {
    "new vegas": DEFAULT_LOCATION,
    "vegas": DEFAULT_LOCATION,
    "the strip": DEFAULT_LOCATION,
    "lucky 38": DEFAULT_LOCATION,
    "the mojave": DEFAULT_LOCATION,
    "mojave": DEFAULT_LOCATION,
    "goodsprings": DEFAULT_LOCATION,
    "freeside": DEFAULT_LOCATION,
}

# "weather in Seoul", "is it raining in London", "how hot is it at Camp McCarran"
_LOCATION_RE = re.compile(
    r"\b(?:in|for|at|near|around|over)\s+([A-Za-z][A-Za-z\s,.'-]*)",
    re.IGNORECASE,
)

# Words that trail a place name in speech but are not part of it —
# "Seoul today", "New York City right now" would otherwise be geocoded whole.
_TRAILING_FILLER = {
    "today", "tonight", "tomorrow", "now", "currently", "right", "moment",
    "please", "outside", "there", "like", "this", "week", "weekend",
    "morning", "afternoon", "evening", "at", "the", "is", "it", "and",
    "weather", "temperature", "temp", "forecast", "climate", "area", "lately",
}
_LEADING_FILLER = {"the", "a", "an"}

WTTR_URL = "https://wttr.in/{location}?format=j1"


def is_weather_query(text: str) -> bool:
    """Return True if the message appears to be asking about weather."""
    lowered = text.lower()
    return any(kw in lowered for kw in WEATHER_KEYWORDS)


def _clean_location(raw: str) -> str:
    """Trim filler words off a captured place name.

    wttr.in geocodes whatever it is handed, so "Seoul today" silently
    resolves to some unrelated district. Strip the noise first.
    """
    words = raw.replace(",", " , ").split()
    while words and words[0].lower().strip(",.") in _LEADING_FILLER:
        words.pop(0)
    while words and (
        words[-1].lower().strip(",.") in _TRAILING_FILLER or words[-1] == ","
    ):
        words.pop()
    return " ".join(words).replace(" , ", ", ").strip(" ,.")


def extract_location(text: str) -> str:
    """Extract an explicit location from a weather query, or "" if none given."""
    for match in _LOCATION_RE.finditer(text):
        location = _clean_location(match.group(1))
        if location:
            return location
    return ""


def resolve_location(text: str) -> str:
    """Pick the location to report on: explicit, in-universe alias, or home.

    Always returns something — a bare "what's the weather?" gets New Vegas,
    which is the only forecast Mr. House considers his business anyway.
    """
    lowered = text.lower()
    location = extract_location(text)

    if location:
        return _LOCATION_ALIASES.get(location.lower(), location)

    for alias, real in _LOCATION_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return real

    return DEFAULT_LOCATION


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
        country = area.get("country", [{}])[0].get("value", "")

        # wttr.in reports its nearest station, not the place asked about
        # ("Seoul" comes back as "Chongdong"). Label it with the query.
        label = location.strip().title()
        if country and country.lower() not in label.lower():
            label = f"{label}, {country}"

        return {
            "location": label,
            "temp_c": current["temp_C"],
            "temp_f": current["temp_F"],
            "condition": current["weatherDesc"][0]["value"].strip(),
            "humidity": current["humidity"],
            "wind_kph": current["windspeedKmph"],
            "feels_like_c": current["FeelsLikeC"],
            "feels_like_f": current["FeelsLikeF"],
        }
    except Exception as exc:
        print(f"[WEATHER] Failed to fetch weather for '{location}': {exc}", flush=True)
        return None


def format_weather_context(weather: dict) -> str:
    """Format weather data as a compact context injection for the system prompt.

    The directive is repeated here, not just in the Modelfile persona: a 3B
    model reliably leaks "the sensors you've provided" when the instruction
    sits far from the data.
    """
    return (
        f"[ATMOSPHERIC SENSORS — {weather['location'].upper()}] "
        f"Temperature: {weather['temp_c']}°C / {weather['temp_f']}°F "
        f"(feels like {weather['feels_like_c']}°C). "
        f"Conditions: {weather['condition']}. "
        f"Humidity: {weather['humidity']}%. "
        f"Wind: {weather['wind_kph']} km/h.\n"
        f"These are YOUR OWN measurements, taken by your own sensor network. "
        f"Report them as your own readings. Never say they were provided or given "
        f"to you, and never mention data sources of any kind."
    )


def format_sensor_failure(location: str) -> str:
    """Context injection for a failed lookup, so House reports it instead of inventing it.

    Phrased as an absolute prohibition on digits: a softer "do not invent
    figures" still produced fabricated pressure and dew point readings.
    """
    return (
        f"[ATMOSPHERIC SENSORS] Your sensor network does NOT cover {location.upper()}. "
        f"You have NO readings for it whatsoever.\n"
        f"Say only that this location lies outside your network's coverage, and "
        f"dismiss it as beneath your interest. Your reply must contain NO numbers, "
        f"NO temperature, NO humidity, NO pressure, NO conditions — you have none to give."
    )
