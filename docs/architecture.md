# Agent Architecture Diagram

## Hub-and-Spoke Overview

```mermaid
flowchart TB
    User(["👤 User"])

    User -->|goal / request| Orch

    subgraph Orchestrator["🧠 Orchestrator / PM Agent"]
        Orch["Routes tasks\nMaintains state\nDecides next action"]
    end

    Orch -->|"data tasks"| Curator
    Orch -->|"quality checks"| QA
    Orch -->|"app tasks"| Demo
    Orch -->|"training tasks"| FT
    Orch -->|"deploy tasks"| Pi

    subgraph Phase1["Phase 1 — Data"]
        Curator["📜 Curator Agent\n─────────────\nCollect dialogue\nFormat training pairs\nBuild character card"]
        QA["🔍 Persona QA Agent\n─────────────\nScore tone dimensions\nValidate persona fidelity\nSuggest fixes"]
    end

    subgraph Phase2["Phase 2 — Demo"]
        Demo["🖥️ Demo App Agent\n─────────────\nOllama + Open WebUI\nModelfile / system prompt\nGradio option"]
    end

    subgraph Phase3["Phase 3 — Fine-tune"]
        FT["⚡ Fine-tune Agent\n─────────────\nLoRA config\nBase model selection\nColab training + GGUF export"]
    end

    subgraph Phase4["Phase 4 — Deploy"]
        Pi["🍓 Pi Deploy Agent\n─────────────\nllama.cpp build\nsystemd service\nQuantization tuning"]
    end

    Curator -->|"dataset + card"| QA
    FT -->|"model outputs"| QA

    subgraph State["📁 Shared State"]
        direction LR
        S1["project_state/\nroadmap_status.yaml"]
        S2["data/\nmr_house_dataset.jsonl"]
        S3["persona/\ncharacter_card.md"]
        S4["eval/\npersona_scores.csv"]
        S5["ops/\ndeploy_pi.md"]
    end

    Orch <-->|"read/write"| State
    Curator -->|write| S2
    Curator -->|write| S3
    QA -->|write| S4
    QA -.->|read| S3
    Demo -.->|read| S3
    FT -.->|read| S2
    FT -.->|read| S4
    Pi -->|write| S5

    style Orchestrator fill:#4a90d9,stroke:#2c5f8a,color:#fff
    style Phase1 fill:#f5e6cc,stroke:#d4a843
    style Phase2 fill:#d4edda,stroke:#6db47e
    style Phase3 fill:#e8d5f5,stroke:#9b6dbf
    style Phase4 fill:#f8d7da,stroke:#d96b6b
    style State fill:#fff3cd,stroke:#c9a825
```

## Data Flow (Sequential)

```mermaid
flowchart LR
    subgraph P1["Phase 1"]
        C["Curator"] -->|dataset.jsonl\ncharacter_card.md| PQ1["Persona QA"]
    end

    subgraph P2["Phase 2"]
        D["Demo App"] -->|system prompt\nfrom character_card| Test["Test Chat"]
    end

    subgraph P3["Phase 3"]
        FT["Fine-tune"] -->|model outputs| PQ2["Persona QA"]
        PQ2 -->|approved| Export["GGUF Export"]
    end

    subgraph P4["Phase 4"]
        Deploy["Pi Deploy"] -->|llama.cpp\n+ systemd| Live["Live on Pi 5"]
    end

    PQ1 -->|"✅ gate pass"| D
    Test -->|"feedback"| FT
    Export -->|"model.gguf"| Deploy

    style P1 fill:#f5e6cc,stroke:#d4a843
    style P2 fill:#d4edda,stroke:#6db47e
    style P3 fill:#e8d5f5,stroke:#9b6dbf
    style P4 fill:#f8d7da,stroke:#d96b6b
```

## Demo Runtime — Chat & Voice Pipeline

Updated 2026-07-06 (latency + prompt quick fixes).

```mermaid
flowchart LR
    subgraph Input
        Text["⌨️ Textbox"]
        Mic["🎤 Microphone"]
    end

    Mic -->|WAV| Whisper["Whisper STT\n(base / tiny on Pi)"]
    Whisper -->|transcript| Prompt

    Text --> Prompt["Build messages\npersona from Modelfile\n+ optional weather context"]

    Prompt -->|streaming /api/chat| Ollama["Ollama\nmr-house (llama3.2:3b)\nnum_ctx 8192"]

    Ollama -->|token stream| Buffer["Sentence buffer\n(splits at . ! ? …\nskips Mr./Dr. abbrevs)"]
    Buffer -->|full partials| Chat["🖥️ gr.Chatbot\n(streaming text)"]
    Buffer -->|per sentence| Kokoro["Kokoro TTS\nbm_george, 0.95x"]
    Kokoro -->|"(24kHz, ndarray) chunks"| Audio["🔊 gr.Audio\n(streaming=True, autoplay)"]
```

Key design points:

- **Single source of truth for the persona.** `demo/config.py` parses the
  `SYSTEM """..."""` block out of `demo/Modelfile` at startup and sends it as
  the request-level system message. This matters because Ollama *replaces* the
  Modelfile SYSTEM when a request carries its own system message — before this
  fix the demo silently ran on a 17-word stub prompt instead of the full persona.
- **Sentence-streaming TTS.** `voice.synthesize_chunk()` returns raw
  `(sample_rate, ndarray)` audio. `handlers._stream_reply()` watches the LLM
  token stream, cuts at sentence boundaries (with an abbreviation guard so
  "Mr. House" doesn't split), and synthesizes each sentence as soon as it is
  complete. Playback begins after the first sentence rather than after the
  whole response — the main latency fix.
- **Model preloading.** Whisper and Kokoro load in a background thread at app
  startup instead of lazily on the first voice turn.
- **Weather tool.** Keyword-triggered (`is_weather_query`); live wttr.in data is
  appended to the system prompt before the request. `resolve_location` always
  returns a target — an explicit "in <place>" (with trailing time words like
  "today" stripped, since wttr.in geocodes whatever it is handed), an
  in-universe alias (New Vegas / the Strip / the Mojave → Las Vegas), or Las
  Vegas by default. A failed lookup injects an explicit sensors-offline notice
  so the model reports the gap instead of inventing readings. Both injections
  restate their directive inline rather than relying on the Modelfile alone —
  at 3B the model otherwise leaks "the sensors you've provided" and fabricates
  numbers for uncovered locations. Parsing is covered by
  `scripts/test_weather.py`. Planned upgrade: native Ollama function calling.

## Agent Access Matrix

| Artifact | Orchestrator | Curator | Persona QA | Demo App | Fine-tune | Pi Deploy |
|----------|:-----------:|:-------:|:----------:|:--------:|:---------:|:---------:|
| `roadmap_status.yaml` | R/W | R | R | R | R | R |
| `mr_house_dataset.jsonl` | — | **W** | R | — | R | — |
| `character_card.md` | — | **W** | R | R | R | — |
| `persona_scores.csv` | R | — | **W** | — | R | — |
| `deploy_pi.md` | — | — | — | — | — | **W** |
