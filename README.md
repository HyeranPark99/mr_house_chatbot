# Mr. House Chatbot

> *"I have no interest in abusing others, just as I have no interest in being abused."*
> — Robert Edwin House, Fallout: New Vegas

An AI chatbot that embodies Mr. House's personality from Fallout: New Vegas — calculating, eloquent, and obsessed with technological progress. Built using a multi-agent pipeline, LoRA fine-tuning, and deployed on a Raspberry Pi.

---

## Architecture

This project uses a **hub-and-spoke multi-agent** pattern. An Orchestrator coordinates six specialist agents:

- **Curator** — collects and formats dialogue data
- **Persona QA** — evaluates character authenticity (gates Phase 1→2 and Phase 3→4)
- **Demo App** — manages the Gradio/Ollama demo
- **Fine-tune** — handles LoRA training and GGUF export
- **Pi Deploy** — manages Raspberry Pi deployment

## Quick Start

**Requirements:** [Ollama](https://ollama.com) installed

```bash
# Pull a base model
ollama pull llama3.2:3b

# Create the Mr. House persona
ollama create mr-house -f demo/Modelfile

# Run the Gradio web app
pip install -r requirements.txt
python demo/app.py
```

Open `http://localhost:7860` in your browser.

## Tech Stack

- **Inference:** [Ollama](https://ollama.com) + [llama.cpp](https://github.com/ggerganov/llama.cpp)
- **Demo UI:** [Gradio](https://gradio.app)
- **Fine-tuning:** [Unsloth](https://unsloth.ai) (LoRA on Google Colab)
- **Base model:** Llama 3.2 3B
- **Deployment target:** Raspberry Pi 5 (8GB)
- **Agent framework:** [Claude Code](https://claude.ai/claude-code)

## Disclaimer

This project is a fan-made AI experiment. Mr. House and all related Fallout content are the property of Bethesda Softworks. Training data is not included in this repository.
