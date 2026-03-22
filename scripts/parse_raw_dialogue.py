#!/usr/bin/env python3
"""Parse Mr. House wiki dialogue table into instruction/output JSONL."""

import json
import re
import sys

RAW_FILE = "data/mr_house_dataset_raw.txt"
OUTPUT_FILE = "data/mr_house_dataset_final.jsonl"

def clean_text(text: str) -> str:
    """Remove wiki markup, stage directions, and audio tags from text."""
    # Remove HTML comments (audio tags)
    text = re.sub(r'<!--.*?-->', '', text)
    # Remove {{linkable|...}}
    text = re.sub(r'\{\{linkable\|[^}]*\}\}', '', text)
    # Remove {{Inline quote|...}}
    text = re.sub(r'\{\{Inline quote\|[^}]*\}\}', '', text)
    # Remove ''stage directions'' but keep the text around them
    # e.g., ''{devastated}'' -> remove, ''{beat}'' -> remove
    text = re.sub(r"''\{[^}]*\}''", '', text)
    # Remove remaining wiki italic markers
    text = re.sub(r"''", '', text)
    # Remove [SUCCEEDED] / [FAILED] skill check tags
    text = re.sub(r'\[SUCCEEDED\]\s*', '', text)
    text = re.sub(r'\[FAILED\]\s*', '', text)
    # Remove <...> action tags like <Attack Mr. House.>
    text = re.sub(r'<[^>]+>', '', text)
    # Remove Speech/Barter/Science skill check markers
    text = re.sub(r'\{[^}]*Speech[^}]*\}', '', text)
    text = re.sub(r'\{[^}]*Barter[^}]*\}', '', text)
    text = re.sub(r'\{[^}]*Science[^}]*\}', '', text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def parse_dialogue(filepath: str) -> list[dict]:
    """Parse the wiki table format into (prompt, response) pairs."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    current_topic_id = ""
    current_prompt = ""
    current_responses = []
    current_context = ""  # GREETING context like {FIRST, BUNKER}

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect topic ID row: |{{linkable|VDialogueMrHouse...}}
        topic_match = re.match(r'^\|(?:rowspan="\d+"\s*\|)?\s*\{\{linkable\|(VDialogueMrHouse\w+)\}\}', line)
        if topic_match:
            # Save previous entry if we have responses
            if current_responses and current_prompt:
                merged = ' '.join(current_responses)
                merged = clean_text(merged)
                prompt = clean_text(current_prompt)
                if merged and prompt and len(merged) > 10:
                    entries.append({"instruction": prompt, "output": merged})
            current_topic_id = topic_match.group(1)
            current_responses = []
            current_prompt = ""
            current_context = ""
            i += 1
            continue

        # Detect GREETING topic (no topic ID, just "GREETING")
        greeting_match = re.match(r'^\|(?:rowspan="\d+"\s*\|)?GREETING$', line)
        if greeting_match:
            # Save previous entry
            if current_responses and current_prompt:
                merged = ' '.join(current_responses)
                merged = clean_text(merged)
                prompt = clean_text(current_prompt)
                if merged and prompt and len(merged) > 10:
                    entries.append({"instruction": prompt, "output": merged})
            current_topic_id = "GREETING"
            current_responses = []
            current_prompt = ""
            current_context = ""
            i += 1
            continue

        # Detect prompt text (player dialogue line) - comes after topic ID
        # Pattern: |rowspan="N" |prompt text  OR  |prompt text
        prompt_match = re.match(r'^\|(?:rowspan="\d+"\s*\|)?\s*(.+)$', line)
        if prompt_match and not line.startswith('|Neutral') and not line.startswith('|Anger') \
           and not line.startswith('|Happy') and not line.startswith('|Sad') \
           and not line.startswith('|Surprise') and not line.startswith('|Disgust') \
           and not line.startswith('|Fear') and not line.startswith('|Pained') \
           and not line.startswith('|-') and not line.startswith('|{') \
           and not line.startswith('|!') and not line.startswith('|class='):
            candidate = prompt_match.group(1).strip()
            # Skip wiki table markers and non-prompt content
            if candidate and not candidate.startswith('{{linkable') \
               and not candidate.startswith('rowspan') \
               and not candidate.startswith('class=') \
               and '|' not in candidate[:3]:
                # If this looks like a player prompt (not a House response line)
                # Save previous entry if topic changed
                if current_responses:
                    merged = ' '.join(current_responses)
                    merged = clean_text(merged)
                    prompt = clean_text(current_prompt)
                    if merged and prompt and len(merged) > 10:
                        entries.append({"instruction": prompt, "output": merged})
                    current_responses = []
                current_prompt = candidate
                i += 1
                continue

        # Detect response lines (Mr. House's dialogue)
        # Pattern: |Response text after an emotion line
        emotion_match = re.match(r'^\|(Neutral|Anger|Happy|Sad|Surprise|Disgust|Fear|Pained)\s+\d+$', line)
        if emotion_match:
            # Next line should be the actual dialogue
            if i + 1 < len(lines):
                response_line = lines[i + 1].strip()
                if response_line.startswith('|'):
                    response_text = response_line[1:].strip()
                    # Skip linkable-only lines
                    if not re.match(r'^\{\{linkable\|\d+\}\}$', response_text):
                        current_responses.append(response_text)
                i += 2
                continue

        i += 1

    # Don't forget the last entry
    if current_responses and current_prompt:
        merged = ' '.join(current_responses)
        merged = clean_text(merged)
        prompt = clean_text(current_prompt)
        if merged and prompt and len(merged) > 10:
            entries.append({"instruction": prompt, "output": merged})

    return entries


def deduplicate(entries: list[dict]) -> list[dict]:
    """Remove duplicate entries based on output text similarity."""
    seen_outputs = set()
    unique = []
    for entry in entries:
        # Normalize for dedup comparison
        key = entry["output"].lower().strip()[:80]
        if key not in seen_outputs:
            seen_outputs.add(key)
            unique.append(entry)
    return unique


def filter_quality(entries: list[dict]) -> list[dict]:
    """Remove low-quality entries."""
    filtered = []
    skip_patterns = [
        r'^Goodbye\.$',
        r'^\.+$',
        r'^\s*$',
    ]
    for entry in entries:
        output = entry["output"]
        instruction = entry["instruction"]
        # Skip very short responses (likely not useful for training)
        if len(output) < 20:
            continue
        # Skip generic game UI prompts
        if instruction.lower() in ("goodbye.", "goodbye", "no thanks.", "no thanks"):
            continue
        # Skip entries matching skip patterns
        skip = False
        for pat in skip_patterns:
            if re.match(pat, output):
                skip = True
                break
        if skip:
            continue
        filtered.append(entry)
    return filtered


def main():
    print(f"Parsing {RAW_FILE}...")
    entries = parse_dialogue(RAW_FILE)
    print(f"  Raw entries parsed: {len(entries)}")

    entries = deduplicate(entries)
    print(f"  After deduplication: {len(entries)}")

    entries = filter_quality(entries)
    print(f"  After quality filter: {len(entries)}")

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"\nWritten to {OUTPUT_FILE}")
    print(f"Total training examples: {len(entries)}")

    # Validate
    valid = 0
    with open(OUTPUT_FILE, 'r') as f:
        for i, line in enumerate(f, 1):
            obj = json.loads(line)
            assert 'instruction' in obj and 'output' in obj, f"Line {i} missing keys"
            valid += 1
    print(f"Validation passed: {valid} valid entries")


if __name__ == "__main__":
    main()
