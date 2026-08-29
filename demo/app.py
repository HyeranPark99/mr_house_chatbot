#!/usr/bin/env python3
"""Mr. House Chatbot demo entrypoint."""

import gradio as gr

import threading

from config import PORTRAIT_PATH, get_opening_greeting
from gradio_patch import apply_patch
from handlers import (
    clear_chat,
    log_mic_change,
    make_respond_stream,
    make_voice_submit,
    user_submit,
)
from theme import CUSTOM_CSS


apply_patch()

try:
    from voice import preload, synthesize_chunk, transcribe

    VOICE_ENABLED = True
    print("[VOICE] Voice I/O enabled (Whisper STT + Kokoro TTS)")
    # Load Whisper/Kokoro in the background so the first turn isn't slow
    threading.Thread(target=preload, daemon=True).start()
except ImportError as exc:
    transcribe = None
    synthesize_chunk = None
    VOICE_ENABLED = False
    print(f"[VOICE] Voice I/O disabled — {exc}")


def create_demo():
    greeting = get_opening_greeting()
    respond_stream = make_respond_stream(synthesize_chunk if VOICE_ENABLED else None)
    voice_submit = make_voice_submit(transcribe, synthesize_chunk) if VOICE_ENABLED else None

    with gr.Blocks(css=CUSTOM_CSS, title="Mr. House — Lucky 38 Terminal") as demo:
        with gr.Column(elem_id="monitor-frame"):
            gr.HTML(
                """
                <div id="title-bar">
                    <h1>LUCKY 38 EXECUTIVE TERMINAL</h1>
                    <div id="subtitle">ROBCO INDUSTRIES UNIFIED OPERATING SYSTEM v.85.2.1</div>
                </div>
                """
            )

            gr.Image(
                value=str(PORTRAIT_PATH),
                elem_id="house-portrait",
                show_label=False,
                container=False,
                interactive=False,
            )

            gr.HTML('<div id="status-line">[ SECURE CONNECTION — LUCKY 38 PENTHOUSE ]</div>')

            chatbot = gr.Chatbot(
                value=[{"role": "assistant", "content": greeting}],
                height=350,
                show_label=False,
                container=False,
            )

            with gr.Row():
                msg = gr.Textbox(
                    placeholder="Speak to Mr. House...",
                    elem_id="msg-input",
                    show_label=False,
                    scale=9,
                    container=False,
                )
                submit_btn = gr.Button("TRANSMIT", variant="primary", scale=1)

            if VOICE_ENABLED:
                gr.HTML(
                    '<div id="voice-status">[ VOICE COMMS AVAILABLE — RECORD AND PRESS STOP TO TRANSMIT ]</div>'
                )
                with gr.Row():
                    mic_input = gr.Audio(
                        sources=["microphone"],
                        type="filepath",
                        label="Voice Input",
                        elem_id="mic-input",
                        show_label=False,
                        scale=7,
                    )
                    voice_btn = gr.Button("TRANSMIT\nVOICE", variant="primary", scale=2)

            clear_btn = gr.Button("[ DISCONNECT ]", variant="secondary", size="sm")

            # Single shared audio output for both text and voice responses.
            # streaming=True plays sentence chunks as they are synthesized.
            tts_audio = gr.Audio(
                elem_id="tts-output",
                show_label=False,
                streaming=True,
                autoplay=True,
                interactive=False,
                visible=VOICE_ENABLED,
            )

        msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            respond_stream, chatbot, [chatbot, tts_audio]
        )
        submit_btn.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            respond_stream, chatbot, [chatbot, tts_audio]
        )
        clear_btn.click(clear_chat, None, chatbot, queue=False)

        if VOICE_ENABLED:
            # Diagnostic only — confirms recordings reach the server
            mic_input.change(log_mic_change, mic_input, None)
            # Auto-submit when the recording is finalized (.input fires on
            # user-made changes only, so clearing the mic from voice_submit's
            # own output does not re-trigger it). The button stays as a
            # manual fallback; both read the mic component directly.
            mic_input.input(
                voice_submit,
                [mic_input, chatbot],
                [chatbot, tts_audio, mic_input],
            )
            voice_btn.click(
                voice_submit,
                [mic_input, chatbot],
                [chatbot, tts_audio, mic_input],
            )

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
