"""Voice I/O module for Mr. House chatbot.

STT: OpenAI Whisper (base on Mac, tiny on Pi 5)
TTS: Kokoro (bm_george British male voice)
"""

import os
import platform
import subprocess
import tempfile
import threading
from importlib.util import find_spec
from pathlib import Path
from typing import Optional

# Fail fast at import so app.py disables voice when deps are missing,
# instead of every lazy import failing silently at synthesis time.
_missing = [m for m in ("whisper", "kokoro", "soundfile") if find_spec(m) is None]
if _missing:
    raise ImportError(
        f"Voice deps missing from this Python env: {', '.join(_missing)}. "
        "Run: pip install openai-whisper kokoro soundfile"
    )

# Ensure Homebrew binaries (ffmpeg) are on PATH for subprocess calls
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

# ---------------------------------------------------------------------------
# STT (Speech-to-Text) via Whisper
# ---------------------------------------------------------------------------

_whisper_model = None
_whisper_lock = threading.Lock()


def get_whisper_model():
    """Lazy-load Whisper model. Uses 'tiny' on ARM (Pi 5), 'base' elsewhere."""
    global _whisper_model
    with _whisper_lock:  # preload thread and first request may race
        if _whisper_model is None:
            import whisper
            model_size = "tiny" if platform.machine() == "aarch64" else "base"
            print(f"[VOICE] Loading Whisper '{model_size}' model...", flush=True)
            _whisper_model = whisper.load_model(model_size)
            print(f"[VOICE] Whisper ready.", flush=True)
    return _whisper_model


def transcribe(audio_filepath: str) -> str:
    """Transcribe audio file to text using Whisper.

    Args:
        audio_filepath: Path to WAV/MP3 file from Gradio's gr.Audio.

    Returns:
        Transcribed text string, or empty string on failure.
    """
    if audio_filepath is None:
        return ""
    try:
        model = get_whisper_model()
        result = model.transcribe(audio_filepath, language="en")
        text = result.get("text", "").strip()
        print(f"[VOICE] Transcribed: {text}", flush=True)
        return text
    except Exception as e:
        print(f"[VOICE] Transcription error: {e}", flush=True)
        return ""


# ---------------------------------------------------------------------------
# TTS (Text-to-Speech) via Kokoro — bm_george (British male)
# ---------------------------------------------------------------------------

KOKORO_VOICE = "bm_george"
KOKORO_SPEED = 0.95   # slightly slower = more deliberate/authoritative

_kokoro_pipeline = None
_kokoro_lock = threading.Lock()


def _get_kokoro_pipeline():
    global _kokoro_pipeline
    with _kokoro_lock:  # preload thread and first request may race
        if _kokoro_pipeline is None:
            from kokoro import KPipeline
            print("[VOICE] Loading Kokoro pipeline (British English)...", flush=True)
            _kokoro_pipeline = KPipeline(lang_code="b")  # 'b' = British English
            print("[VOICE] Kokoro ready.", flush=True)
    return _kokoro_pipeline


def clean_for_tts(text: str) -> str:
    """Strip stage directions and action descriptions before synthesis.

    Removes patterns like ((leaning forward)), (smiles), *nods*, _quietly_.
    """
    import re
    text = re.sub(r'\(\(.*?\)\)', '', text)   # ((double parens))
    text = re.sub(r'\(.*?\)', '', text)        # (single parens)
    text = re.sub(r'\*.*?\*', '', text)        # *asterisks*
    text = re.sub(r'_.*?_', '', text)          # _underscores_
    return re.sub(r'\s{2,}', ' ', text).strip()


KOKORO_SAMPLE_RATE = 24000


def synthesize_chunk(text: str):
    """Convert a piece of text (typically one sentence) to raw audio.

    Args:
        text: The text to speak.

    Returns:
        (sample_rate, np.ndarray) tuple for streaming playback, or None.
    """
    text = clean_for_tts(text)
    if not text:
        return None

    try:
        import numpy as np

        pipeline = _get_kokoro_pipeline()
        chunks = []
        for _, _, audio in pipeline(text, voice=KOKORO_VOICE, speed=KOKORO_SPEED):
            chunks.append(audio)

        if not chunks:
            print("[VOICE] Kokoro produced no audio chunks", flush=True)
            return None

        # int16 keeps Gradio from re-normalizing each chunk by its own peak,
        # which would make quiet sentences suddenly loud between chunks.
        audio = np.concatenate(chunks)
        audio = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        return KOKORO_SAMPLE_RATE, audio
    except ImportError:
        print("[VOICE] kokoro not installed. Run: pip install kokoro soundfile", flush=True)
        return None
    except Exception as e:
        print(f"[VOICE] TTS error: {e}", flush=True)
        return None


def synthesize(text: str) -> Optional[str]:
    """Convert text to speech and write it to a WAV file.

    Args:
        text: The text to speak (Mr. House's response).

    Returns:
        Path to output WAV file, or None on failure.
    """
    chunk = synthesize_chunk(text)
    if chunk is None:
        return None

    sample_rate, audio = chunk
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        import soundfile as sf

        sf.write(tmp_path, audio, sample_rate)
        print(f"[VOICE] TTS generated: {tmp_path}", flush=True)
        return tmp_path
    except Exception as e:
        print(f"[VOICE] TTS error: {e}", flush=True)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return None


def preload():
    """Eagerly load the Whisper and Kokoro models to avoid first-turn lag."""
    try:
        get_whisper_model()
        _get_kokoro_pipeline()
    except Exception as e:
        print(f"[VOICE] Preload error: {e}", flush=True)
