#!/usr/bin/env python3
"""Clean up the parsed JSONL dataset - fix remaining markup and bad instructions."""

import json
import re

INPUT = "data/mr_house_dataset_final.jsonl"

def clean_stage_directions(text: str) -> str:
    """Remove any remaining {stage direction} patterns."""
    text = re.sub(r'\s*\{[^}]*\}\s*', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_internal_topic_id(instruction: str) -> bool:
    """Check if instruction is a wiki internal topic ID, not a real prompt."""
    return bool(re.match(r'^v?[Dd]ialogue', instruction))

entries = []
with open(INPUT) as f:
    for line in f:
        obj = json.loads(line)
        # Clean stage directions from both fields
        obj["output"] = clean_stage_directions(obj["output"])
        obj["instruction"] = clean_stage_directions(obj["instruction"])
        entries.append(obj)

# Separate good entries from internal-ID entries
good = []
internal = []
for e in entries:
    if is_internal_topic_id(e["instruction"]):
        internal.append(e)
    else:
        good.append(e)

# Map internal topic IDs to natural prompts where the output is interesting
topic_rewrites = {
    "vDialogueMrHouseControlPissed": None,  # combat bark, skip
    "vDialogueMrHouseElevatorAlert": None,  # system alert, skip
    "vDialogueMrHouseFirstTalk": None,  # ambient bark, skip
    "vDialogueMrHouseLastWillTestament": None,  # death trigger, skip
    "vDialogueMrHousePenthousePissed": None,  # combat bark, skip
}

# Filter out internal-ID entries (combat barks, alerts, ambient lines)
# These don't make good training pairs since they lack conversational context

with open(INPUT, 'w') as f:
    for entry in good:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

print(f"Kept: {len(good)} entries")
print(f"Removed {len(internal)} internal topic ID entries (combat barks, alerts, ambient lines)")

# Validate
errors = 0
with open(INPUT) as f:
    for i, line in enumerate(f, 1):
        obj = json.loads(line)
        out = obj["output"]
        ins = obj["instruction"]
        if '{' in out and '}' in out:
            print(f"  WARN line {i}: possible leftover markup in output: {out[:60]}")
            errors += 1
        if not ins or not out:
            print(f"  WARN line {i}: empty field")
            errors += 1

print(f"Validation: {errors} warnings")
