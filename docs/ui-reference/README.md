# Host Terminal UI Reference

This directory preserves the Host Terminal draft as a visual and interaction
reference for the Mr. House chatbot. It is a concept artifact, not the current
Gradio implementation.

## Open the interactive draft

Open [`host-terminal.html`](host-terminal.html) in a modern browser. The file is
self-contained and does not require a development server.

The panel is authored on a 480 × 320 pixel grid and enlarged for desktop
preview. The reference demonstrates:

- a five-layer reactive portrait with eased expressions and blinking;
- six text response prompts with typed replies and trust/signal changes;
- a simulated push-to-talk voice mode and audio meter;
- green, amber, and blue phosphor tints;
- optional scanlines, glitch effects, zoom, and portrait motion.

## Implementation notes

The voice interaction is simulated and does not access a microphone. A real
voice implementation can replace the draft's `startTalk` and `stopTalk` path
with microphone capture, transcription, and response selection while retaining
the existing meter and interaction states.

The portrait image was supplied by the project owner and is retained here for
personal, non-commercial reference. Mr. House and related Fallout material are
the property of Bethesda Softworks.
