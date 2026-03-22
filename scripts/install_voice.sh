#!/usr/bin/env bash
# Install voice I/O dependencies for Mr. House chatbot
# STT: OpenAI Whisper | TTS: Piper TTS
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VOICE_DIR="$PROJECT_DIR/demo/voices"

echo "=== Mr. House Voice Setup ==="

# 1. Install Whisper (STT)
echo "[1/3] Installing openai-whisper..."
pip3 install openai-whisper

# 2. Install Piper TTS
echo "[2/3] Installing piper-tts..."
pip3 install piper-tts

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
echo "Run the demo with: python3 demo/app.py"
