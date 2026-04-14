"""Theme assets for the demo app."""


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
    border: 2px solid #4a4a2a !important;
    border-radius: 8px !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
}

/* Gradio 6 inner chat wrappers */
.bubble-wrap,
.message-wrap,
.panel-wrap {
    background-color: #111100 !important;
}

/* Message bubbles */
.bot, .user, .message-bot, .message-user,
[data-testid="bot"], [data-testid="user"] {
    font-family: 'Courier New', monospace !important;
}

.bot, .bot p, .bot span, .bot *, .message-bot, .message-bot *,
[data-testid="bot"], [data-testid="bot"] * {
    background-color: #1a1a0a !important;
    color: #c8aa32 !important;
    border-color: #3a3a1a !important;
}

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
    border: 2px solid #4a4a2a !important;
    border-radius: 8px !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
    font-family: 'Courier New', monospace !important;
}

textarea::placeholder {
    color: #5a5a2a !important;
}

#msg-input,
#msg-input > label,
#msg-input .input-container,
#msg-input .input-container > div,
#msg-input [data-testid="textbox"],
#msg-input [data-testid="textbox"] textarea,
#msg-input [data-testid="submit-button"],
#msg-input [data-testid="stop-button"] {
    border-color: #4a4a2a !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
}

/* Buttons */
button.primary {
    background-color: #3a3a1a !important;
    color: #c8aa32 !important;
    border: 2px solid #4a4a2a !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
    font-family: 'Courier New', monospace !important;
}

button.secondary {
    background-color: #1a1a0a !important;
    color: #c8aa32 !important;
    border: 2px solid #4a4a2a !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
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
    border: 2px solid #4a4a2a !important;
    border-radius: 4px !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
}

#mic-input,
#mic-input > div,
#mic-input button,
#mic-input [data-testid="block-label"],
#mic-input [data-testid="media-upload"],
#mic-input [data-testid="audio"],
#mic-input .record-button,
#mic-input .stop-button,
#mic-input .device-select-large {
    background-color: #000000 !important;
    color: #c8aa32 !important;
}

#mic-input {
    border: 2px solid #4a4a2a !important;
    border-radius: 8px !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
}

#voice-output,
#voice-output > div,
#voice-output button,
#voice-output .record-button,
#voice-output .stop-button,
#voice-output .device-select-large {
    border: 2px solid #4a4a2a !important;
    border-radius: 8px !important;
    box-shadow: 0 0 20px rgba(200, 170, 50, 0.2) !important;
}

#mic-input .record-button,
#mic-input .stop-button,
#mic-input .device-select-large,
#voice-output .record-button,
#voice-output .stop-button,
#voice-output .device-select-large {
    border: 2px solid #4a4a2a !important;
}

#voice-status {
    color: #5a5a2a;
    background-color: #111100 !important;
    font-size: 0.7em;
    text-align: center;
    padding: 3px;
    letter-spacing: 1px;
}

/* Footer */
footer { display: none !important; }
"""
