#!/bin/bash
# Hook: PostToolUse (Edit|Write)
# Validates mr_house_dataset_final.jsonl has correct instruction/output format on every write.
# Exit 0 = success, Exit 2 = block (invalid format detected)

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only validate writes to JSONL dataset files
if [[ "$FILE_PATH" != *"mr_house_dataset"*".jsonl" ]]; then
  exit 0
fi

# Check the file exists
if [[ ! -f "$FILE_PATH" ]]; then
  exit 0
fi

ERRORS=""
LINE_NUM=0

while IFS= read -r line; do
  LINE_NUM=$((LINE_NUM + 1))

  # Skip empty lines
  if [[ -z "$line" ]]; then
    continue
  fi

  # Validate JSON
  if ! echo "$line" | jq empty 2>/dev/null; then
    ERRORS="${ERRORS}Line ${LINE_NUM}: invalid JSON\n"
    continue
  fi

  # Check required keys
  HAS_INSTRUCTION=$(echo "$line" | jq -r 'has("instruction")')
  HAS_OUTPUT=$(echo "$line" | jq -r 'has("output")')

  if [[ "$HAS_INSTRUCTION" != "true" ]]; then
    ERRORS="${ERRORS}Line ${LINE_NUM}: missing 'instruction' key\n"
  fi
  if [[ "$HAS_OUTPUT" != "true" ]]; then
    ERRORS="${ERRORS}Line ${LINE_NUM}: missing 'output' key\n"
  fi

  # Check values are non-empty strings
  INSTRUCTION=$(echo "$line" | jq -r '.instruction // empty')
  OUTPUT=$(echo "$line" | jq -r '.output // empty')

  if [[ -z "$INSTRUCTION" ]]; then
    ERRORS="${ERRORS}Line ${LINE_NUM}: empty instruction\n"
  fi
  if [[ -z "$OUTPUT" ]]; then
    ERRORS="${ERRORS}Line ${LINE_NUM}: empty output\n"
  fi

done < "$FILE_PATH"

if [[ -n "$ERRORS" ]]; then
  echo -e "JSONL validation failed for $FILE_PATH:\n$ERRORS" >&2
  exit 2
fi

# Return context to Claude about the validation
jq -n '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: "JSONL validation passed: all entries have valid instruction/output format."
  }
}'
