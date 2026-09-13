# Mr. House Chatbot

A local LLM chatbot that speaks as Mr. House from *Fallout: New Vegas*. The eventual target is a Pip-Boy–style device running on a Raspberry Pi 5.

The project covers the full small-model workflow: curating a dialogue dataset, scoring it for persona consistency, LoRA fine-tuning Llama 3.2 3B, and serving the model through Ollama in a Gradio app with optional voice I/O. Development runs as a multi-agent pipeline built on Claude Code, with an orchestrator agent, five specialist agents, and hooks that enforce shared project state.

## What it does

- **Chat UI**: a Gradio app styled like a Lucky 38 terminal. It streams responses from a local Ollama model and opens with a greeting drawn from a bank of in-game lines.
- **Persona model**: Llama 3.2 3B, shaped by a character card and system prompt ([`demo/Modelfile`](demo/Modelfile)) and LoRA-fine-tuned on curated dialogue pairs.
- **Voice I/O (optional)**: Whisper handles speech-to-text and Kokoro handles text-to-speech (British male voice). Stage directions are stripped before synthesis.
- **Live context**: weather questions are detected, and current conditions from [wttr.in](https://wttr.in) are injected into the prompt.

## How it's built

### Data and evaluation pipeline

| Step | Code | Output |
|---|---|---|
| Parse and deduplicate raw wiki dialogue | [`scripts/parse_raw_dialogue.py`](scripts/parse_raw_dialogue.py), [`scripts/clean_dataset.py`](scripts/clean_dataset.py) | 204 instruction/response pairs (JSONL) |
| Extract opening greetings | [`scripts/extract_greetings.py`](scripts/extract_greetings.py) | 70 greeting entries |
| Score persona fidelity on 5 dimensions; flag out-of-character, short, and duplicate entries | [`scripts/persona_qa.py`](scripts/persona_qa.py) | [`eval/persona_scores.csv`](eval/persona_scores.csv), [`eval/qa_report.md`](eval/qa_report.md) |

The dataset itself is not committed because it is copyrighted game dialogue.

### Fine-tuning

[`training/colab_finetune.ipynb`](training/colab_finetune.ipynb) runs LoRA fine-tuning with Unsloth and TRL's `SFTTrainer` on a free Colab T4. The configuration lives in [`training/lora_config.yaml`](training/lora_config.yaml):

- Base model: `unsloth/Llama-3.2-3B-Instruct`, loaded in 4-bit
- LoRA: r=16, alpha=32, dropout 0.05, applied to all attention and MLP projections
- Training: 3 epochs, effective batch size 8, learning rate 2e-4 with cosine schedule, max sequence length 512
- Export: merged GGUF in `q4_k_m` (~2 GB) and `q5_k_m` for llama.cpp and Ollama

Model weights are not committed (`*.gguf` and `*.safetensors` are gitignored).

### Multi-agent development workflow

Development is coordinated by Claude Code agents defined in [`.claude/skills/`](.claude/skills/). The orchestrator reads [`project_state/roadmap_status.yaml`](project_state/roadmap_status.yaml) and routes each task to a specialist:

| Agent | Responsibility |
|---|---|
| Orchestrator | Maintains roadmap state and decides the next action |
| Curator | Collects and formats dialogue data; maintains the character card |
| Persona QA | Scores persona fidelity and gates the transitions from data to demo and from fine-tuning to deployment |
| Demo App | Builds the Gradio/Ollama app |
| Fine-tune | Handles LoRA configuration, training, and GGUF export |
| Pi Deploy | Handles llama.cpp builds, quantization tuning, and the systemd service |

Hooks in [`.claude/settings.json`](.claude/settings.json) validate JSONL on every write, protect the character card from unapproved edits, require agents to read project state before editing, and restore that state after context compaction. See [`docs/architecture.md`](docs/architecture.md) for the full diagram.

## Stack

Python · Ollama · Llama 3.2 3B · Unsloth / TRL / PEFT (LoRA) · Gradio · Whisper · Kokoro TTS · Claude Code (agents and hooks)

## Running it

**Requirements:** Python 3.10+ and [Ollama](https://ollama.com).

```bash
# 1. Create the persona model from the Modelfile (base model + character prompt)
ollama pull llama3.2:3b
ollama create mr-house -f demo/Modelfile

# 2. Install dependencies and start the app
pip install -r requirements.txt
python demo/app.py
```

Open http://localhost:7860.

**Voice I/O (optional):** install `ffmpeg`, then run:

```bash
pip install -r requirements-voice.txt
```

**Using fine-tuned weights:** run the Colab notebook with your own `mr_house_dataset_final.jsonl` and download the GGUF file. Then point the `FROM` line of `demo/Modelfile` at that file and run `ollama create mr-house -f demo/Modelfile` again. The app always talks to the model named `mr-house`.

## Roadmap

- [x] Dataset curation, character card, and persona QA
- [x] Gradio demo on Ollama with voice I/O and live weather
- [x] LoRA fine-tuning of Llama 3.2 3B on Colab (Unsloth)
- [ ] Raspberry Pi 5 deployment: llama.cpp build, quantization and thread tuning for 8 GB RAM, systemd auto-start, deployment runbook

## Disclaimer

This is a non-commercial fan project. Mr. House and all *Fallout* content are the property of Bethesda Softworks. Training data and model weights are not included.
