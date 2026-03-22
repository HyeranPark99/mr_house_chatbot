# Mr. House Chatbot — Project Roadmap

> *"I have no interest in abusing others, just as I have no interest in being abused."*
> — Robert Edwin House, Fallout: New Vegas

---

## Project Overview

Build an AI chatbot that embodies Mr. House's personality from Fallout: New Vegas — calculating, eloquent, condescending toward perceived inferiors, obsessed with technological progress, and speaking like a pre-war corporate titan.

The project follows a phased approach: start with a quick web demo, then optionally fine-tune a model, and finally deploy to a Raspberry Pi as a standalone device.

---

## Phase 1: Gather Mr. House's Dialogue

**Goal:** Build a clean dataset of Mr. House's dialogue for both prompt context and fine-tuning.

**Dialogue Sources:**

- [MrHouse.txt — Fallout Wiki (Fandom)](https://fallout.fandom.com/wiki/MrHouse.txt) — raw dialogue file from the game
- [Robert House's Dialogue — Fallout Archive Wiki](https://fallout-archive.fandom.com/wiki/Robert_House%27s_dialogue) — structured tables with context
- [Mr. House Dialogue — fallout.wiki](https://fallout.wiki/wiki/Mr._House/Mr._House_(Fallout:_New_Vegas)/Dialogue) — organized by quest and topic

**Tasks:**

- [ ] Scrape or copy all Mr. House dialogue lines
- [ ] Format into question-answer pairs (Player prompt → Mr. House response)
- [ ] Write a character card summarizing his personality traits, speech patterns, and worldview
- [ ] Save as structured JSON for training and as plain text for prompt context

**Character Card Notes:**

Mr. House's key traits to capture:

- Genius-level intellect; founder of RobCo Industries
- Speaks with the authority and detachment of a pre-war CEO
- Views democracy and tribalism as inefficient
- Obsessed with preserving and advancing civilization through technology
- Condescending but rarely emotional; treats conversations as negotiations
- Uses formal, precise language with occasional dry wit

**Estimated Time:** 1–2 weeks (mostly manual data formatting)

---

## Phase 2: Website Demo (Start Here)

**Goal:** Get a working chatbot running on your computer with a browser-based interface. No coding or training required for Option A.

### Option A: Ollama + Open WebUI (No Code)

This is the fastest path to a working demo.

1. **Install Ollama** — [ollama.com](https://ollama.com) (one-click install for Mac/Windows/Linux)
2. **Pull a small model:**
   ```bash
   ollama pull llama3.2:3b
   ```
3. **Create a Modelfile** that injects Mr. House's personality:
   ```
   FROM llama3.2:3b
   SYSTEM """
   You are Mr. House (Robert Edwin House), the founder of RobCo Industries
   and the ruler of New Vegas. You survived the Great War by sealing yourself
   in a life-support chamber beneath the Lucky 38 casino. You are calculating,
   eloquent, and condescending toward those you see as inferior. You speak
   like a pre-war corporate titan and view democracy as inefficient. You are
   obsessed with technological progress and humanity's future among the stars.
   Respond in character at all times.
   """
   ```
4. **Create the custom model:**
   ```bash
   ollama create mr-house -f Modelfile
   ollama run mr-house
   ```
5. **Install Open WebUI** for a ChatGPT-like interface:
   ```bash
   docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway \
     -v open-webui:/app/backend/data --name open-webui \
     ghcr.io/open-webui/open-webui:main
   ```
   Then open `http://localhost:3000` in your browser.

**Estimated Time:** 1 afternoon

### Option B: Simple Python Web App (Light Coding)

For a more customizable interface using Gradio:

1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install gradio ollama
   ```
3. Write a ~20-line Python script that connects Gradio's chat UI to your Ollama model
4. Run it and get a shareable demo link

**Estimated Time:** 1–2 days

---

## Phase 3: Fine-Tune with LoRA (Level Up)

**Goal:** Bake Mr. House's personality directly into the model weights for more authentic responses.

**Why Fine-Tune?**

Prompt engineering (Phase 2) gets you ~80% of the way, but the model still "sounds like itself wearing a costume." Fine-tuning makes the personality intrinsic — the model naturally produces Mr. House-like phrasing, tone, and reasoning patterns.

### Choosing a Base Model

All open-source and free:

| Model | Size | Pi-Friendly? | Notes |
|-------|------|:---:|-------|
| TinyLlama 1.1B | ~700MB quantized | Yes | [Research paper proves it works for character dialogue](https://www.researchgate.net/publication/393513549_Efficient_Fine-Tuning_of_TinyLlama_for_Character-Specific_Dialogue_Generation_Using_LoRA) |
| Llama 3.2 1B | ~700MB quantized | Yes | Meta's latest, strong quality for size |
| Llama 3.2 3B | ~2GB quantized | Yes (Pi 5 8GB) | Best balance of quality and size |
| Qwen2.5 3B | ~2GB quantized | Yes (Pi 5 8GB) | Strong alternative from Alibaba |

### Training Tools

- [Unsloth](https://unsloth.ai) — easiest option, has free Google Colab notebooks (no GPU needed on your machine)
- [LLaMA Factory](https://github.com/hiyouga/LlamaFactory) — more features, supports role-playing fine-tuning specifically

### Training Process (Step by Step)

1. **Format your dialogue data** into the expected JSON structure:
   ```json
   [
     {
       "instruction": "What is your plan for New Vegas?",
       "output": "I have no interest in abusing others, just as I have no interest in being abused. I want to restore Las Vegas as a city of progress..."
     }
   ]
   ```
2. **Open an Unsloth notebook** in [Google Colab](https://colab.research.google.com) (free tier provides a GPU)
3. **Load your base model**, point it at your dataset, configure LoRA parameters
4. **Train** — typically 30–60 minutes on Colab's free GPU
5. **Export to GGUF format** (the format llama.cpp and the Pi need):
   ```python
   model.save_pretrained_gguf("mr-house-model", tokenizer, quantization_method="q4_k_m")
   ```
6. **Test the result** in Ollama or llama.cpp before deploying

**Key Insight:** You do NOT train on the Raspberry Pi. You train for free in the cloud, then deploy the small result file to the Pi.

**Estimated Time:** 2–3 weeks (including learning curve)

---

## Phase 4: Deploy to Raspberry Pi

**Goal:** Run Mr. House as a standalone, always-on chatbot on a Raspberry Pi.

### Hardware Requirements

| Component | Recommendation | Approx. Cost |
|-----------|---------------|:---:|
| Raspberry Pi 5 | **8GB RAM** (4GB won't work) | ~$80 |
| Storage | 32GB+ microSD or NVMe SSD via HAT | ~$15–40 |
| Power Supply | Official Pi 5 27W USB-C | ~$12 |
| Case | Any Pi 5 case with cooling | ~$10–15 |

**Total: ~$120–150**

### Expected Performance

On a Pi 5 (8GB) with 4-bit quantized models via llama.cpp:

- **1B model:** ~7–10 tokens/second (roughly 2–3 sentences/sec)
- **3B model:** ~4–7 tokens/second (roughly 1–2 sentences/sec)

Noticeably slower than ChatGPT, but absolutely usable for a chatbot.

### Setup Steps

1. **Install Raspberry Pi OS** (64-bit, Bookworm or newer)
2. **Install build dependencies:**
   ```bash
   sudo apt update && sudo apt install -y build-essential cmake git
   ```
3. **Build llama.cpp:**
   ```bash
   git clone https://github.com/ggerganov/llama.cpp
   cd llama.cpp
   cmake -B build -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS
   cmake --build build --config Release
   ```
4. **Copy your GGUF model** to the Pi (via USB, SCP, etc.)
5. **Run the built-in web server:**
   ```bash
   ./build/bin/llama-server -m mr-house-q4.gguf -c 2048 --host 0.0.0.0 --port 8080
   ```
6. **Access from any device** on your network at `http://<pi-ip>:8080`

### Optional: Auto-Start on Boot

Create a systemd service so the chatbot starts automatically when the Pi powers on:

```bash
sudo nano /etc/systemd/system/mrhouse.service
```

```ini
[Unit]
Description=Mr. House Chatbot
After=network.target

[Service]
ExecStart=/home/pi/llama.cpp/build/bin/llama-server -m /home/pi/models/mr-house-q4.gguf -c 2048 --host 0.0.0.0 --port 8080
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mrhouse
sudo systemctl start mrhouse
```

**Estimated Time:** 1 week

---

## Recommended Timeline

| Week | Milestone |
|:---:|-----------|
| 1–2 | Gather and format Mr. House dialogue data |
| 2 | Get Ollama + Open WebUI demo running (Phase 2A) |
| 3–4 | Fine-tune with LoRA on Google Colab (Phase 3) |
| 5 | Set up Raspberry Pi and deploy (Phase 4) |
| 6+ | Iterate — improve training data, tweak personality, build custom UI |

---

## Key Resources

| Resource | Link |
|----------|------|
| Ollama | [ollama.com](https://ollama.com) |
| Open WebUI | [github.com/open-webui/open-webui](https://github.com/open-webui/open-webui) |
| Unsloth (fine-tuning) | [unsloth.ai](https://unsloth.ai) |
| LLaMA Factory | [github.com/hiyouga/LlamaFactory](https://github.com/hiyouga/LlamaFactory) |
| llama.cpp | [github.com/ggerganov/llama.cpp](https://github.com/ggerganov/llama.cpp) |
| ARM Pi 5 LLM Guide | [learn.arm.com](https://learn.arm.com/learning-paths/embedded-and-microcontrollers/llama-python-cpu/) |
| TinyLlama Character LoRA Paper | [ResearchGate](https://www.researchgate.net/publication/393513549) |
| Mr. House Dialogue | [Fallout Wiki](https://fallout.fandom.com/wiki/MrHouse.txt) |

---

## Difficulty Honest Assessment

| Phase | Difficulty | Notes |
|-------|:---:|-------|
| Dialogue gathering | Easy | Tedious but straightforward copy-paste and formatting |
| Ollama demo | Easy | No coding, just install and configure |
| Fine-tuning | Medium | Colab notebooks handle the hard parts; data formatting is the real work |
| Pi deployment | Medium | Mostly following guides; troubleshooting is the main challenge |

The hardest part of this entire project is preparing clean, well-formatted training data. Everything else has good tooling and documentation.

---

*Project created: February 2026*
