"""Chat transport helpers for the demo app."""

import json

import requests

from config import MODEL_NAME, OLLAMA_URL, SYSTEM_PROMPT
from weather import extract_location, fetch_weather, format_weather_context, is_weather_query


def normalize_text(content):
    """Normalize Gradio content (string or list of blocks) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return str(content) if content is not None else ""


def build_messages(message, history):
    """Build an Ollama-compatible chat payload from Gradio history.

    If the message is a weather query with a location, injects live weather
    data into the system prompt before sending to Ollama.
    """
    system_prompt = SYSTEM_PROMPT
    text = normalize_text(message)

    if is_weather_query(text):
        location = extract_location(text)
        if location:
            weather = fetch_weather(location)
            if weather:
                system_prompt += "\n\n" + format_weather_context(weather)
                print(f"[WEATHER] Injected: {format_weather_context(weather)}", flush=True)
            else:
                print(f"[WEATHER] Could not fetch weather for '{location}'", flush=True)

    messages = [{"role": "system", "content": system_prompt}]

    for item in history:
        if isinstance(item, dict):
            messages.append(
                {"role": item["role"], "content": normalize_text(item["content"])}
            )
            continue

        if item[0]:
            messages.append({"role": "user", "content": normalize_text(item[0])})
        if item[1]:
            messages.append({"role": "assistant", "content": normalize_text(item[1])})

    messages.append({"role": "user", "content": normalize_text(message)})
    return messages


def chat_with_house(message, history):
    """Send a streaming request to Ollama."""
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "messages": build_messages(message, history), "stream": True},
            stream=True,
            timeout=120,
        )
        response.raise_for_status()

        partial = ""
        for line in response.iter_lines():
            if not line:
                continue
            data = json.loads(line)
            if "message" in data and "content" in data["message"]:
                partial += data["message"]["content"]
                yield partial
    except requests.ConnectionError:
        yield "[ CONNECTION ERROR: Ollama is not running. Start it with: open -a Ollama ]"
    except requests.HTTPError as exc:
        yield f"[ ERROR: {str(exc)} | body: {exc.response.text} ]"
    except Exception as exc:
        yield f"[ ERROR: {str(exc)} ]"


def chat_with_house_full(message, history):
    """Collect a full response from the streaming generator."""
    full_text = ""
    for partial in chat_with_house(message, history):
        full_text = partial
    return full_text
