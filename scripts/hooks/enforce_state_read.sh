#!/bin/bash
# Hook: PreToolUse (Edit|Write)
# Blocks writes to shared artifacts unless roadmap_status.yaml was read first in this session.
# Exit 0 = allow, Exit 2 = deny

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Define shared artifact paths that require state-read-first
SHARED_PATTERNS=(
  "mr_house_dataset"
  "character_card.md"
  "persona_scores.csv"
  "deploy_pi.md"
  "roadmap_status.yaml"
)

# Check if the file being written is a shared artifact
IS_SHARED=false
for pattern in "${SHARED_PATTERNS[@]}"; do
  if [[ "$FILE_PATH" == *"$pattern"* ]]; then
    IS_SHARED=true
    break
  fi
done

# If not a shared artifact, allow freely
if [[ "$IS_SHARED" != "true" ]]; then
  exit 0
fi

# Check the transcript for evidence that roadmap_status.yaml was read
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  if grep -q "roadmap_status.yaml" "$TRANSCRIPT_PATH" 2>/dev/null; then
    # State was read — allow the write
    exit 0
  fi
fi

# State was not read — block the write
echo "Workflow rule: You must read project_state/roadmap_status.yaml before writing to shared artifacts. Read the state file first, then retry." >&2
exit 2
