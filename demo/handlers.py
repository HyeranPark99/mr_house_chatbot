"""UI event handlers for the demo app."""

import re

import gradio as gr

from chat import chat_with_house
from config import get_opening_greeting

# Sentence endings we can safely speak at: terminal punctuation, optional
# closing quote/bracket, followed by whitespace.
_SENTENCE_END = re.compile(r'[.!?…]["\')\]]*\s')
_ABBREVIATIONS = {"mr", "mrs", "ms", "dr", "st", "vs", "etc", "e.g", "i.e"}


def _silence():
    """A short silent chunk (10ms) for streams that produced no speech.

    Gradio's streaming Audio raises KeyError at end_stream() if an event
    run never yields a real chunk, so every run must emit at least one.
    int16 zeros skip Gradio's float32 normalization (0/0 NaN warnings).
    """
    import numpy as np

    return 24000, np.zeros(240, dtype=np.int16)


def _speakable_boundary(text, start):
    """Return the index just past the last complete sentence after `start`.

    Returns `start` when no full sentence has streamed in yet. Skips false
    boundaries after abbreviations like "Mr." so "Mr. House" stays intact.
    """
    end = start
    for match in _SENTENCE_END.finditer(text, start):
        preceding = text[: match.start()].split()
        last_word = preceding[-1].lower() if preceding else ""
        if last_word in _ABBREVIATIONS:
            continue
        end = match.end()
    return end


def _stream_reply(message, history, chat_history, synthesize_chunk):
    """Stream the assistant reply into chat_history, speaking each sentence.

    Yields (chat_history, audio_chunk) — audio_chunk is a (sample_rate,
    ndarray) tuple whenever a new complete sentence is ready, else None.
    Speaking sentence-by-sentence means playback starts after the first
    sentence instead of after the whole response.
    """
    spoken = 0
    final = ""
    for partial in chat_with_house(message, history):
        final = partial
        chat_history[-1]["content"] = partial
        audio = None
        # Error banners like "[ CONNECTION ERROR ... ]" are not speech
        if synthesize_chunk and not partial.startswith("["):
            boundary = _speakable_boundary(partial, spoken)
            if boundary > spoken:
                audio = synthesize_chunk(partial[spoken:boundary])
                spoken = boundary
        yield chat_history, audio

    if synthesize_chunk and not final.startswith("["):
        rest = final[spoken:].strip()
        if rest:
            audio = synthesize_chunk(rest)
            if audio is not None:
                yield chat_history, audio


def user_submit(message, chat_history):
    chat_history = chat_history + [{"role": "user", "content": message}]
    return "", chat_history


def make_respond_stream(synthesize_chunk=None):
    """Build the text-path handler: stream the reply, speak it as it arrives."""

    def respond_stream(chat_history):
        last = chat_history[-1]
        message = last["content"] if isinstance(last, dict) else last[0]
        history = chat_history[:-1]
        chat_history = chat_history + [{"role": "assistant", "content": ""}]
        emitted = False
        for chat_history, audio in _stream_reply(
            message, history, chat_history, synthesize_chunk
        ):
            emitted = emitted or audio is not None
            yield chat_history, (audio if audio is not None else gr.skip())
        if not emitted:
            yield chat_history, _silence()

    return respond_stream


def clear_chat():
    return [{"role": "assistant", "content": get_opening_greeting()}]


def log_mic_change(audio_filepath):
    """Diagnostic: shows whether mic recordings reach the server at all."""
    print(f"[VOICE] mic value changed: {audio_filepath}", flush=True)


def make_voice_submit(transcribe, synthesize_chunk):
    """Build the voice-path handler around the STT/TTS backends.

    Takes the mic component's value directly — no State relay. Bound to
    both mic_input.input (auto-submit on stop) and the manual button.
    """

    def voice_submit(audio_filepath, chat_history):
        print(f"[VOICE] voice_submit called, audio={audio_filepath}", flush=True)
        if audio_filepath is None:
            print("[VOICE] No audio filepath received", flush=True)
            yield chat_history, _silence(), gr.skip()
            return

        emitted = False
        try:
            print(f"[VOICE] Transcribing {audio_filepath}...", flush=True)
            user_text = transcribe(audio_filepath)
            if not user_text:
                print("[VOICE] Transcription returned empty", flush=True)
                yield chat_history, _silence(), None
                return

            history = chat_history
            chat_history = chat_history + [{"role": "user", "content": user_text}]
            # Show the transcription right away and clear the mic
            yield chat_history, gr.skip(), None

            print(f"[VOICE] Sending to LLM: {user_text}", flush=True)
            chat_history = chat_history + [{"role": "assistant", "content": ""}]
            for chat_history, audio in _stream_reply(
                user_text, history, chat_history, synthesize_chunk
            ):
                emitted = emitted or audio is not None
                yield (
                    chat_history,
                    audio if audio is not None else gr.skip(),
                    gr.skip(),
                )
            if not emitted:
                yield chat_history, _silence(), gr.skip()
        except Exception as exc:
            print(f"[VOICE] voice_submit ERROR: {exc}", flush=True)
            import traceback

            traceback.print_exc()
            audio_out = gr.skip() if emitted else _silence()
            yield chat_history, audio_out, gr.skip()

    return voice_submit
