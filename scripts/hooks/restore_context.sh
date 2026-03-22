#!/bin/bash
# Hook: SessionStart (compact)
# Re-injects project state after context compaction so Claude doesn't lose track.
# Outputs the current roadmap state as context for the new compacted session.

STATE_FILE="project_state/roadmap_status.yaml"

# Try to find the state file relative to CWD or in known locations
if [[ ! -f "$STATE_FILE" ]]; then
  INPUT=$(cat)
  CWD=$(echo "$INPUT" | jq -r '.cwd // empty')
  if [[ -n "$CWD" && -f "$CWD/$STATE_FILE" ]]; then
    STATE_FILE="$CWD/$STATE_FILE"
  else
    echo "Warning: Could not find roadmap_status.yaml after compaction" >&2
    exit 1
  fi
fi

# Output the state — this gets injected as context Claude can see
echo "=== PROJECT STATE (restored after compaction) ==="
cat "$STATE_FILE"
echo ""
echo "=== REMINDERS ==="
echo "- All agents must read roadmap_status.yaml before working"
echo "- character_card.md is the single source of truth for Mr. House persona"
echo "- Persona QA is a gate between phases"
echo "- Training data: data/mr_house_dataset_final.jsonl (204 entries)"
echo "- Greetings: data/mr_house_greetings.jsonl (70 entries, kept separate)"
echo "- Hooks are installed in .claude/settings.json"
