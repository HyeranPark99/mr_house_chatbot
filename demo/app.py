#!/usr/bin/env python3
"""Mr. House Chatbot demo entrypoint."""

import gradio as gr

from config import PORTRAIT_PATH, get_opening_greeting
from gradio_patch import apply_patch
from handlers import (
    bot_respond,
    clear_chat,
    make_voice_submit,
    store_recorded_audio,
    user_submit,
)
from theme import CUSTOM_CSS


apply_patch()

try:
    from voice import transcribe, synthesize

    VOICE_ENABLED = True
    print("[VOICE] Voice I/O enabled (Whisper STT + Piper TTS)")
except ImportError:
    transcribe = None
    synthesize = None
    VOICE_ENABLED = False
    print("[VOICE] Voice I/O disabled (dependencies not installed)")


def create_demo():
    greeting = get_opening_greeting()
    voice_submit = make_voice_submit(transcribe, synthesize) if VOICE_ENABLED else None

    with gr.Blocks(css=CUSTOM_CSS, title="Mr. House — Lucky 38 Terminal") as demo:
        recorded_audio = gr.State(value=None)

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
                    '<div id="voice-status">[ VOICE COMMS AVAILABLE — RECORD, THEN CLICK TRANSMIT VOICE ]</div>'
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
                voice_output = gr.Audio(
                    label="Mr. House Speaks",
                    elem_id="voice-output",
                    show_label=False,
                    autoplay=True,
                    interactive=False,
                )

            clear_btn = gr.Button("[ DISCONNECT ]", variant="secondary", size="sm")

        msg.submit(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_respond, chatbot, chatbot
        )
        submit_btn.click(user_submit, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_respond, chatbot, chatbot
        )
        clear_btn.click(clear_chat, None, chatbot, queue=False)

        if VOICE_ENABLED:
            mic_input.stop_recording(
                store_recorded_audio,
                mic_input,
                recorded_audio,
                queue=False,
            )
            mic_input.change(
                store_recorded_audio,
                mic_input,
                recorded_audio,
                queue=False,
            )
            voice_btn.click(
                voice_submit,
                [recorded_audio, chatbot],
                [chatbot, voice_output, mic_input, recorded_audio],
                queue=False,
            )

    return demo


if __name__ == "__main__":
    demo = create_demo()
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
