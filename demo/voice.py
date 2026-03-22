"""Voice I/O module for Mr. House chatbot.

STT: OpenAI Whisper (base on Mac, tiny on Pi 5)
TTS: Piper TTS (en_US-lessac-medium voice)
"""

import os
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

# Ensure Homebrew binaries (ffmpeg) are on PATH for subprocess calls
os.environ["PATH"] = "/opt/homebrew/bin:" + os.environ.get("PATH", "")

# ---------------------------------------------------------------------------
# STT (Speech-to-Text) via Whisper
# ---------------------------------------------------------------------------

_whisper_model = None


def get_whisper_model():
    """Lazy-load Whisper model. Uses 'tiny' on ARM (Pi 5), 'base' elsewhere."""
    global _whisper_model
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
# TTS (Text-to-Speech) via Piper
# ---------------------------------------------------------------------------

VOICE_DIR = Path(__file__).parent / "voices"
PIPER_VOICE = "en_US-lessac-medium"


def synthesize(text: str) -> Optional[str]:
    """Convert text to speech using Piper TTS.

    Args:
        text: The text to speak (Mr. House's response).

    Returns:
        Path to output WAV file, or None on failure.
    """
    if not text or not text.strip():
        return None

    voice_model = VOICE_DIR / f"{PIPER_VOICE}.onnx"
    voice_config = VOICE_DIR / f"{PIPER_VOICE}.onnx.json"

    if not voice_model.exists():
        print(f"[VOICE] Piper voice not found at {voice_model}", flush=True)
        print("[VOICE] Run: bash scripts/install_voice.sh", flush=True)
        return None

    # Create temp WAV file for output
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        # Use piper Python API — synthesize() is a generator of AudioChunks
        from piper import PiperVoice

        voice = PiperVoice.load(str(voice_model), config_path=str(voice_config))

        import wave
        with wave.open(tmp_path, "wb") as wav_file:
            wav_file.setnchannels(1)        # mono
            wav_file.setsampwidth(2)         # 16-bit PCM
            wav_file.setframerate(voice.config.sample_rate)
            for chunk in voice.synthesize(text):
                wav_file.writeframes(chunk.audio_int16_bytes)

        if os.path.getsize(tmp_path) > 0:
            print(f"[VOICE] TTS generated: {tmp_path}", flush=True)
            return tmp_path
        else:
            print("[VOICE] TTS produced empty file", flush=True)
            return None

    except ImportError:
        print("[VOICE] piper-tts not installed. Run: bash scripts/install_voice.sh", flush=True)
        return None
    except Exception as e:
        print(f"[VOICE] TTS error: {e}", flush=True)
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return None
