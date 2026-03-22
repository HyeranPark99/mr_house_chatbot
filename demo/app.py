#!/usr/bin/env python3
"""Mr. House Chatbot — Lucky 38 Monitor Demo UI"""

import json
import random
import requests

# Monkey-patch gradio_client bug: schema can be a bool, not always a dict
import gradio_client.utils as _gu
_original_json_schema_to_python_type = _gu._json_schema_to_python_type
def _patched_json_schema_to_python_type(schema, defs=None):
    if isinstance(schema, bool):
        return "Any"
    return _original_json_schema_to_python_type(schema, defs)
_gu._json_schema_to_python_type = _patched_json_schema_to_python_type

import gradio as gr

# Voice I/O (optional — gracefully degrades if not installed)
try:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent))
    from voice import transcribe, synthesize
    VOICE_ENABLED = True
    print("[VOICE] Voice I/O enabled (Whisper STT + Piper TTS)")
except ImportError:
    VOICE_ENABLED = False
    print("[VOICE] Voice I/O disabled (dependencies not installed)")

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "mr-house"
GREETINGS_FILE = "data/mr_house_greetings.jsonl"

# Load greeting bank
def load_greetings():
    try:
        with open(GREETINGS_FILE) as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        return [{"output": "You are the first person to step foot inside the Lucky 38 in over 200 years. It was not an invitation I made lightly."}]

GREETINGS = load_greetings()


def get_opening_greeting():
    """Pick a random first-meeting greeting."""
    first_meeting = [g for g in GREETINGS if "first meeting" in g.get("instruction", "")]
    pool = first_meeting if first_meeting else [g for g in GREETINGS if "Hello, Mr. House" in g.get("instruction", "")]
    if pool:
        return random.choice(pool)["output"]
    return "You are the first person to step foot inside the Lucky 38 in over 200 years."


def chat_with_house(message, history):
    """Send message to Ollama and stream response."""
    messages = [{"role": "system", "content": "You are Mr. House. Stay in character at all times."}]

    for h in history:
        messages.append({"role": "user", "content": h[0]})
        if h[1]:
            messages.append({"role": "assistant", "content": h[1]})

    messages.append({"role": "user", "content": message})

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "messages": messages, "stream": True},
            stream=True,
            timeout=120,
        )
        response.raise_for_status()

        partial = ""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "message" in data and "content" in data["message"]:
                    partial += data["message"]["content"]
                    yield partial
    except requests.ConnectionError:
        yield "[ CONNECTION ERROR: Ollama is not running. Start it with: open -a Ollama ]"
    except Exception as e:
        yield f"[ ERROR: {str(e)} ]"


def chat_with_house_full(message, history):
    """Non-streaming version — collects complete response for TTS."""
    full_text = ""
    for partial in chat_with_house(message, history):
        full_text = partial
    return full_text


# Custom CSS for Lucky 38 monitor aesthetic
CUSTOM_CSS = """
/* Main container - dark terminal look */
.gradio-container {
    background-color: #0a0a0a !important;
    max-width: 900px !important;
    margin: auto !important;
    font-family: 'Courier New', monospace !important;
}

/* Monitor frame */
#monitor-frame {
    background: linear-gradient(180deg, #1a1a0a 0%, #0d0d00 100%);
    border: 3px solid #3a3a1a;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 0 30px rgba(200, 170, 50, 0.15), inset 0 0 60px rgba(0, 0, 0, 0.8);
}

/* Mr. House image area */
#house-portrait {
    text-align: center;
    padding: 20px 0;
}

#house-portrait img {
    max-height: 400px;
    border: 2px solid #4a4a2a;
    border-radius: 8px;
    filter: sepia(30%) brightness(0.85) contrast(1.1);
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2);
}

/* Title styling */
#title-bar {
    text-align: center;
    color: #c8aa32 !important;
    font-family: 'Courier New', monospace;
    text-shadow: 0 0 10px rgba(200, 170, 50, 0.5);
    border-bottom: 1px solid #3a3a1a;
    padding-bottom: 10px;
    margin-bottom: 15px;
}

#title-bar h1 {
    color: #c8aa32 !important;
    font-size: 1.4em !important;
    letter-spacing: 3px;
    margin: 0 !important;
}

#subtitle {
    color: #8a7a2a !important;
    font-size: 0.75em;
    letter-spacing: 2px;
}

/* Chat area */
.chatbot {
    background-color: #0d0d00 !important;
    border: 1px solid #3a3a1a !important;
    border-radius: 8px !important;
}

/* Message bubbles — Gradio 4.x selectors */
.bot, .user, .message-bot, .message-user,
[data-testid="bot"], [data-testid="user"] {
    font-family: 'Courier New', monospace !important;
}

/* Bot (Mr. House) messages — golden */
.bot, .bot p, .bot span, .bot *, .message-bot, .message-bot *,
[data-testid="bot"], [data-testid="bot"] * {
    background-color: #1a1a0a !important;
    color: #c8aa32 !important;
    border-color: #3a3a1a !important;
}

/* User messages — green terminal */
.user, .user p, .user span, .user *, .message-user, .message-user *,
[data-testid="user"], [data-testid="user"] * {
    background-color: #0d1a0d !important;
    color: #7acc7a !important;
    border-color: #2a3a2a !important;
}

/* Input box */
textarea {
    background-color: #111100 !important;
    color: #c8aa32 !important;
    border: 1px solid #3a3a1a !important;
    font-family: 'Courier New', monospace !important;
}

textarea::placeholder {
    color: #5a5a2a !important;
}

/* Buttons */
button.primary {
    background-color: #3a3a1a !important;
    color: #c8aa32 !important;
    border: 1px solid #5a5a2a !important;
    font-family: 'Courier New', monospace !important;
}

button.primary:hover {
    background-color: #4a4a2a !important;
}

/* Status indicator */
#status-line {
    color: #5a5a2a;
    font-size: 0.7em;
    text-align: center;
    padding: 5px;
    letter-spacing: 1px;
}

/* Voice components */
audio {
    background-color: #111100 !important;
    border: 1px solid #3a3a1a !important;
    border-radius: 4px !important;
}

#voice-status {
    color: #5a5a2a;
    font-size: 0.7em;
    text-align: center;
    padding: 3px;
    letter-spacing: 1px;
}

/* Footer */
footer { display: none !important; }
"""

# Mr. House ASCII portrait for when no image is available
HOUSE_ASCII = """
```
    ╔══════════════════════════════════════╗
    ║                                      ║
    ║         ┌──────────────────┐         ║
    ║         │   ██████████████ │         ║
    ║         │   ██  LUCKY  ██ │         ║
    ║         │   ██   38    ██ │         ║
    ║         │   ██████████████ │         ║
    ║         │                  │         ║
    ║         │  ┌──────────┐   │         ║
    ║         │  │ MR. HOUSE│   │         ║
    ║         │  │  ◉    ◉  │   │         ║
    ║         │  │    ──    │   │         ║
    ║         │  │   ════   │   │         ║
    ║         │  └──────────┘   │         ║
    ║         │                  │         ║
    ║         └──────────────────┘         ║
    ║                                      ║
    ║   ROBCO INDUSTRIES UNIFIED OS        ║
    ║   COPYRIGHT 2075-2281                ║
    ║   LUCKY 38 EXECUTIVE SUITE           ║
    ║   [ CONNECTION ESTABLISHED ]          ║
    ║                                      ║
    ╚══════════════════════════════════════╝
```
"""


def create_demo():
    greeting = get_opening_greeting()

    with gr.Blocks(css=CUSTOM_CSS, title="Mr. House — Lucky 38 Terminal") as demo:

        # Monitor frame
        with gr.Column(elem_id="monitor-frame"):

            # Title bar
            gr.HTML("""
                <div id="title-bar">
                    <h1>LUCKY 38 EXECUTIVE TERMINAL</h1>
                    <div id="subtitle">ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM v.85.2.1</div>
                </div>
            """)

            # Mr. House portrait area
            gr.Image(
                value="demo/house_portrait.png",
                elem_id="house-portrait",
                show_label=False,
                show_download_button=False,
                container=False,
                interactive=False,
            )

            # Status line
            gr.HTML('<div id="status-line">[ SECURE CONNECTION — LUCKY 38 PENTHOUSE ]</div>')

            # Chat interface
            chatbot = gr.Chatbot(
                value=[[None, greeting]],
                height=350,
                show_label=False,
                container=False,
            )

            # Input area
            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Speak to Mr. House...",
                    show_label=False,
                    scale=9,
                    container=False,
                )
                submit_btn = gr.Button("TRANSMIT", variant="primary", scale=1)

            # Voice input/output (if dependencies installed)
            if VOICE_ENABLED:
                gr.HTML('<div id="voice-status">[ VOICE COMMS AVAILABLE — RECORD, THEN CLICK TRANSMIT VOICE ]</div>')
                with gr.Row():
                    mic_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Voice Input",
                        show_label=False,
                        scale=7,
                    )
                    voice_btn = gr.Button("TRANSMIT\nVOICE", variant="primary", scale=2)
                voice_output = gr.Audio(
                    label="Mr. House Speaks",
                    show_label=False,
                    autoplay=True,
                    interactive=False,
                )

            # Clear button
            clear_btn = gr.Button("[ DISCONNECT ]", variant="secondary", size="sm")

        # Event handlers
        def user_submit(message, chat_history):
            chat_history = chat_history + [[message, None]]
            return "", chat_history

        def bot_respond(chat_history):
            message = chat_history[-1][0]
            history = chat_history[:-1]
            chat_history[-1][1] = ""
            for partial in chat_with_house(message, history):
                chat_history[-1][1] = partial
                yield chat_history

        def clear_chat():
            new_greeting = get_opening_greeting()
            return [[None, new_greeting]]

        def voice_submit(audio_filepath, chat_history):
            """Handle voice input: transcribe → chat → TTS → audio reply."""
            print(f"[VOICE] voice_submit called, audio={audio_filepath}", flush=True)
            if audio_filepath is None:
                print("[VOICE] No audio filepath received", flush=True)
                return chat_history, None, None

            try:
                # STT: audio → text
                print(f"[VOICE] Transcribing {audio_filepath}...", flush=True)
                user_text = transcribe(audio_filepath)
                if not user_text:
                    print("[VOICE] Transcription returned empty", flush=True)
                    return chat_history, None, None

                # Add user message to chat history
                chat_history = chat_history + [[user_text, None]]
                print(f"[VOICE] Sending to LLM: {user_text}", flush=True)

                # Get Mr. House response (non-streaming for TTS)
                history_for_llm = chat_history[:-1]
                response = chat_with_house_full(user_text, history_for_llm)
                chat_history[-1][1] = response
                print(f"[VOICE] LLM response: {response[:80]}...", flush=True)

                # TTS: response text → audio
                audio_out = synthesize(response)
                print(f"[VOICE] TTS output: {audio_out}", flush=True)

                return chat_history, audio_out, None  # None clears mic
            except Exception as e:
                print(f"[VOICE] voice_submit ERROR: {e}", flush=True)
                import traceback
                traceback.print_exc()
                return chat_history, None, None

        # Wire up events
        msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_respond, chatbot, chatbot
        )
        submit_btn.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_respond, chatbot, chatbot
        )
        clear_btn.click(clear_chat, None, chatbot, queue=False)

        # Voice events — use manual button click (most reliable in Gradio 4.31.5)
        # Both 'stop_recording' and 'change' events fail to fire from the frontend
        if VOICE_ENABLED:
            voice_btn.click(
                voice_submit,
                [mic_input, chatbot],
                [chatbot, voice_output, mic_input],
                queue=False,
            )

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
