# Post-Training Validation Checklist

## Pre-Training Checks
- [x] Dataset passed Persona QA (task 1.4) — 204 entries, 0 out-of-character
- [x] Base model selected: Llama 3.2 3B Instruct
- [x] LoRA config reviewed: r=16, alpha=32, 3 epochs
- [x] GGUF export targets: Q4_K_M (primary), Q5_K_M (backup)

## During Training
- [ ] Training loss decreases steadily (no spikes)
- [ ] Final training loss < 1.0 (expected ~0.5-0.8 for 204 examples)
- [ ] No CUDA OOM errors (batch_size=4 should fit T4)
- [ ] All 3 epochs complete (~15-20 min estimated)

## Post-Training Model Tests (Step 7 in notebook)
Run these 5 test prompts and verify Mr. House persona:

| Test Prompt | Expected Behavior | Pass? |
|-------------|-------------------|-------|
| "Who are you?" | Identifies as Robert Edwin House, mentions Lucky 38 / RobCo / New Vegas | [ ] |
| "What do you think about democracy?" | Dismisses democracy, references mob rule or failed experiment | [ ] |
| "Hey dude, what's up?" | Rejects casual speech, responds formally | [ ] |
| "Tell me about the Platinum Chip." | Explains strategic importance, decades of planning | [ ] |
| "What is your plan for New Vegas?" | Vision: technology, space colonization, autocratic governance | [ ] |

## Persona QA Gate (Task 3.5)
- [ ] Save test outputs to `eval/finetune_test_outputs.jsonl`
- [ ] Run `scripts/persona_qa.py` on fine-tuned outputs
- [ ] Overall persona score >= 2.0
- [ ] Zero out-of-character flags (no slang, no empathy)
- [ ] Results saved to `eval/persona_scores.csv`

## GGUF Export Checks
- [ ] Q4_K_M file exists and is ~1.5-2GB
- [ ] Q5_K_M file exists and is ~2-2.5GB
- [ ] Test Q4_K_M locally with Ollama before Pi deployment

## Local Ollama Verification
After downloading GGUF, test locally:
```bash
# Create new Modelfile pointing to fine-tuned GGUF
ollama create mr-house-finetuned -f demo/Modelfile.finetuned

# Quick test
curl http://localhost:11434/api/generate -d '{
  "model": "mr-house-finetuned",
  "prompt": "Who are you?",
  "stream": false
}'
```

## Sign-Off
- [ ] All test prompts pass persona check
- [ ] Persona QA script passes
- [ ] GGUF file size is within expected range
- [ ] Ready for Phase 4 (Pi 5 deployment)
