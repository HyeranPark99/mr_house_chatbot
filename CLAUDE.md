# Mr. House Chatbot — Project Instructions

## Agent Architecture

This project uses a hub-and-spoke multi-agent pattern. The Orchestrator coordinates all work through specialist agents. All agents share state through common artifact files.

### Agent Routing

| User Request | Route To | Skill |
|-------------|----------|-------|
| "What should I work on next?" | Orchestrator | `/orchestrator` |
| "Collect Mr. House dialogue" | Curator | `/curator` |
| "Check if this sounds like Mr. House" | Persona QA | `/persona-qa` |
| "Set up the demo" | Demo App | `/demo-app` |
| "Prepare fine-tuning" | Fine-tune | `/finetune` |
| "Deploy to Raspberry Pi" | Pi Deploy | `/pi-deploy` |

### Shared State (mandatory)

All agents MUST read from and write to these shared artifacts:

```
project_state/roadmap_status.yaml  — Project progress (read/write by all)
data/mr_house_dataset.jsonl        — Training data (write: curator, read: finetune, persona-qa)
persona/character_card.md          — Character definition (write: curator, read: all)
eval/persona_scores.csv            — QA scores (write: persona-qa, read: orchestrator, finetune)
ops/deploy_pi.md                   — Deployment runbook (write: pi-deploy)
```

### Workflow Rules

1. **Always read state first.** Before doing any work, read `project_state/roadmap_status.yaml`.
2. **Always update state after.** After completing work, update the YAML with new task statuses and `next_action`.
3. **Persona QA is a gate.** Data (Phase 1) and fine-tuned outputs (Phase 3) must pass QA before moving to the next phase.
4. **Character card is ground truth.** All agents that generate or evaluate Mr. House content must reference `persona/character_card.md`.
5. **Don't skip phases.** Follow the phase order unless explicitly told otherwise.

## Project Phases

1. **Phase 1 — Data** (Curator + Persona QA): Collect dialogue, build dataset, create character card
2. **Phase 2 — Demo** (Demo App): Ollama + Open WebUI or Gradio demo
3. **Phase 3 — Fine-tune** (Fine-tune + Persona QA): LoRA training on Colab, GGUF export
4. **Phase 4 — Deploy** (Pi Deploy): llama.cpp on Raspberry Pi 5
