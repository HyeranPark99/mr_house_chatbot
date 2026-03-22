#!/bin/bash
# Hook: PreToolUse (Edit|Write)
# Only the Curator agent can modify character_card.md.
# Blocks writes from other contexts.
# Exit 0 = allow, Exit 2 = deny

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only guard character_card.md
if [[ "$FILE_PATH" != *"character_card.md" ]]; then
  exit 0
fi

# Check the transcript for curator context
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
  # Look for evidence that /curator skill was invoked in this session
  if grep -q "curator" "$TRANSCRIPT_PATH" 2>/dev/null; then
    # Curator context detected — allow the write
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        permissionDecisionReason: "Curator agent context detected — character_card.md write permitted."
      }
    }'
    exit 0
  fi
fi

# No curator context — warn but allow with context (soft enforcement)
# Hard block would use exit 2, but for now we warn since skill detection is imperfect
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    permissionDecision: "ask",
    permissionDecisionReason: "character_card.md should only be modified by the Curator agent. Are you sure you want to edit it?"
  }
}'
