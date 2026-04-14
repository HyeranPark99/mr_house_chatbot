"""Configuration and static data helpers for the demo app."""

import json
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mr-house"
GREETINGS_FILE = PROJECT_ROOT / "data" / "mr_house_greetings.jsonl"
PORTRAIT_PATH = BASE_DIR / "house_portrait.png"
SYSTEM_PROMPT = (
    "You are Mr. House. Stay in character at all times. "
    "Keep every response under 75 words - make your point once, with authority."
)
DEFAULT_GREETING = (
    "You are the first person to step foot inside the Lucky 38 in over 200 years. "
    "It was not an invitation I made lightly."
)


def load_greetings():
    """Load greeting examples used for the opening message."""
    try:
        with GREETINGS_FILE.open() as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        return [{"output": DEFAULT_GREETING}]


GREETINGS = load_greetings()


def get_opening_greeting():
    """Pick a random first-meeting greeting."""
    first_meeting = [
        greeting
        for greeting in GREETINGS
        if "first meeting" in greeting.get("instruction", "")
    ]
    pool = first_meeting or [
        greeting
        for greeting in GREETINGS
        if "Hello, Mr. House" in greeting.get("instruction", "")
    ]
    if pool:
        return random.choice(pool)["output"]
    return DEFAULT_GREETING
