#!/usr/bin/env bash
# Install voice I/O dependencies for Mr. House chatbot
# STT: OpenAI Whisper | TTS: Piper TTS
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VOICE_DIR="$PROJECT_DIR/demo/voices"

echo "=== Mr. House Voice Setup ==="

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "Python executable not found: $PYTHON_BIN" >&2
    exit 1
fi

echo "Using Python: $(command -v "$PYTHON_BIN")"

# 1. Install Whisper (STT)
echo "[1/3] Installing openai-whisper..."
"$PYTHON_BIN" -m pip install openai-whisper

# 2. Install Piper TTS
echo "[2/3] Installing piper-tts..."
"$PYTHON_BIN" -m pip install piper-tts

# 3. Download Piper voice model (en_US-lessac-medium)
echo "[3/3] Downloading Piper voice model..."
mkdir -p "$VOICE_DIR"

VOICE_BASE="https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium"
ONNX_FILE="$VOICE_DIR/en_US-lessac-medium.onnx"
JSON_FILE="$VOICE_DIR/en_US-lessac-medium.onnx.json"

if [ ! -f "$ONNX_FILE" ]; then
    echo "  Downloading voice model (~100MB)..."
    curl -L -o "$ONNX_FILE" "$VOICE_BASE/en_US-lessac-medium.onnx"
    curl -L -o "$JSON_FILE" "$VOICE_BASE/en_US-lessac-medium.onnx.json"
else
    echo "  Voice model already exists, skipping download."
fi

echo ""
echo "=== Voice setup complete ==="
echo "  Whisper: installed (will download model on first use)"
echo "  Piper:   installed"
echo "  Voice:   $ONNX_FILE"
echo ""
echo "Run the demo with: $PYTHON_BIN demo/app.py"
