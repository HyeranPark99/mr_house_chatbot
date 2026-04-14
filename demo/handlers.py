"""UI event handlers for the demo app."""

from chat import chat_with_house, chat_with_house_full
from config import get_opening_greeting


def user_submit(message, chat_history):
    chat_history = chat_history + [{"role": "user", "content": message}]
    return "", chat_history


def bot_respond(chat_history):
    last = chat_history[-1]
    message = last["content"] if isinstance(last, dict) else last[0]
    history = chat_history[:-1]
    chat_history = chat_history + [{"role": "assistant", "content": ""}]
    for partial in chat_with_house(message, history):
        chat_history[-1]["content"] = partial
        yield chat_history


def clear_chat():
    return [{"role": "assistant", "content": get_opening_greeting()}]


def store_recorded_audio(audio_filepath):
    """Capture finalized microphone recordings for later submission."""
    print(f"[VOICE] store_recorded_audio called, audio={audio_filepath}", flush=True)
    return audio_filepath


def make_voice_submit(transcribe, synthesize):
    """Build the voice-submit handler around optional STT/TTS backends."""

    def voice_submit(audio_filepath, chat_history):
        print(f"[VOICE] voice_submit called, audio={audio_filepath}", flush=True)
        if audio_filepath is None:
            print("[VOICE] No audio filepath received", flush=True)
            return chat_history, None, None, None

        try:
            print(f"[VOICE] Transcribing {audio_filepath}...", flush=True)
            user_text = transcribe(audio_filepath)
            if not user_text:
                print("[VOICE] Transcription returned empty", flush=True)
                return chat_history, None, None, None

            chat_history = chat_history + [{"role": "user", "content": user_text}]
            print(f"[VOICE] Sending to LLM: {user_text}", flush=True)

            response = chat_with_house_full(user_text, chat_history[:-1])
            chat_history = chat_history + [{"role": "assistant", "content": response}]
            print(f"[VOICE] LLM response: {response[:80]}...", flush=True)

            audio_out = synthesize(response)
            print(f"[VOICE] TTS output: {audio_out}", flush=True)
            return chat_history, audio_out, None, None
        except Exception as exc:
            print(f"[VOICE] voice_submit ERROR: {exc}", flush=True)
            import traceback

            traceback.print_exc()
            return chat_history, None, None, audio_filepath

    return voice_submit
