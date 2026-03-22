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

## Agent Access Matrix

| Artifact | Orchestrator | Curator | Persona QA | Demo App | Fine-tune | Pi Deploy |
|----------|:-----------:|:-------:|:----------:|:--------:|:---------:|:---------:|
| `roadmap_status.yaml` | R/W | R | R | R | R | R |
| `mr_house_dataset.jsonl` | — | **W** | R | — | R | — |
| `character_card.md` | — | **W** | R | R | R | — |
| `persona_scores.csv` | R | — | **W** | — | R | — |
| `deploy_pi.md` | — | — | — | — | — | **W** |
