#!/usr/bin/env python3
"""Extract Mr. House greeting responses from raw wiki data for conversation openers."""

import json
import re

RAW_FILE = "data/mr_house_dataset_raw.txt"
OUTPUT_FILE = "data/mr_house_greetings.jsonl"

def clean_text(text: str) -> str:
    """Remove wiki markup, stage directions, and audio tags."""
    text = re.sub(r'<!--.*?-->', '', text)
    text = re.sub(r'\{\{linkable\|[^}]*\}\}', '', text)
    text = re.sub(r'\{\{Inline quote\|[^}]*\}\}', '', text)
    text = re.sub(r"''\{[^}]*\}''", '', text)
    text = re.sub(r"''", '', text)
    text = re.sub(r'\[SUCCEEDED\]\s*', '', text)
    text = re.sub(r'\[FAILED\]\s*', '', text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_context(text: str) -> str:
    """Extract game state context like {FIRST, BUNKER} from stage directions."""
    match = re.search(r'\{([A-Z][A-Z, ]+[A-Z])\}', text)
    if match:
        return match.group(1).strip()
    return ""


def parse_greetings(filepath: str) -> list[dict]:
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    greetings = []
    in_greeting_block = False
    buffer = []
    context = ""

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect GREETING topic
        is_greeting = re.match(r'^\|(?:rowspan="\d+"\s*\|)?GREETING$', line) or \
                      re.match(r'^\|rowspan="\d+"\s*\|\{\{linkable\|GREETING\}\}', line)

        # Detect non-GREETING topic (end of greeting section)
        is_other_topic = re.match(r'^\|(?:rowspan="\d+"\s*\|)?\{\{linkable\|(VDialogue\w+)\}\}', line)

        if is_greeting:
            # Save previous buffer
            if buffer:
                merged = clean_text(' '.join(buffer))
                if merged and len(merged) > 25:
                    greetings.append({
                        "context": context,
                        "response": merged
                    })
            buffer = []
            context = ""
            in_greeting_block = True
            i += 1
            continue

        if is_other_topic:
            if buffer:
                merged = clean_text(' '.join(buffer))
                if merged and len(merged) > 25:
                    greetings.append({
                        "context": context,
                        "response": merged
                    })
            buffer = []
            in_greeting_block = False
            i += 1
            continue

        if in_greeting_block:
            # Try to extract context from this line
            ctx = extract_context(line)
            if ctx:
                context = ctx

            # Detect emotion + response
            emotion_match = re.match(
                r'^\|(Neutral|Anger|Happy|Sad|Surprise|Disgust|Fear|Pained)\s+\d+$', line
            )
            if emotion_match and i + 1 < len(lines):
                response_line = lines[i + 1].strip()
                if response_line.startswith('|'):
                    text = response_line[1:].strip()
                    if not re.match(r'^\{\{linkable\|\d+\}\}$', text):
                        buffer.append(text)
                i += 2
                continue

        i += 1

    # Last buffer
    if buffer:
        merged = clean_text(' '.join(buffer))
        if merged and len(merged) > 25:
            greetings.append({"context": context, "response": merged})

    return greetings


def categorize_greeting(context: str, response: str) -> str:
    """Assign a chatbot-friendly instruction based on the game context."""
    resp_lower = response.lower()

    # First meeting
    if "first" in context.lower() or "this meeting has been a long time" in resp_lower \
       or "first person to set foot" in resp_lower:
        return "Hello, Mr. House. This is our first meeting."

    # Returning after mission success
    if "fort secs up" in context.lower() or "your work here is done" in resp_lower \
       or "bright future" in resp_lower or "foundation is laid" in resp_lower:
        return "I'm back. The mission is complete."

    # Returning after mission failure / betrayal
    if "fort secs dest" in context.lower() or "slightest idea of what you've done" in resp_lower \
       or "doomed vegas" in resp_lower:
        return "I've decided to work against you, Mr. House."

    # Chip delivery
    if "chip" in context.lower() or "platinum chip" in resp_lower:
        return "I have the Platinum Chip for you."

    # Impatient / follow-up
    if "stop wasting" in resp_lower or "stop dragging" in resp_lower \
       or "what is the purpose of this delay" in resp_lower:
        return "I'm back, but I haven't finished the job yet."

    # Quest briefing
    if "boomers" in resp_lower or "omertas" in resp_lower \
       or "brotherhood" in resp_lower or "kimball" in resp_lower:
        return "What should I do next?"

    # General return
    if "later" in context.lower() or "shall we get to work" in resp_lower \
       or "what did you wish to know" in resp_lower:
        return "Hello again, Mr. House."

    # Securitron / upgrade related
    if "securitron" in resp_lower or "upgrade" in resp_lower:
        return "Tell me about the current situation."

    # Battle / endgame
    if "dam" in resp_lower or "battle" in resp_lower or "legion" in resp_lower:
        return "The battle is approaching. What's the plan?"

    # Default
    return "Hello, Mr. House."


def main():
    print(f"Extracting greetings from {RAW_FILE}...")
    greetings = parse_greetings(RAW_FILE)
    print(f"  Raw greetings extracted: {len(greetings)}")

    # Deduplicate
    seen = set()
    unique = []
    for g in greetings:
        key = g["response"][:80].lower()
        if key not in seen:
            seen.add(key)
            unique.append(g)
    greetings = unique
    print(f"  After deduplication: {len(greetings)}")

    # Convert to instruction/output JSONL format
    entries = []
    for g in greetings:
        instruction = categorize_greeting(g["context"], g["response"])
        entries.append({
            "instruction": instruction,
            "output": g["response"],
            "context": g["context"] if g["context"] else "general"
        })

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print(f"\nWritten to {OUTPUT_FILE}")
    print(f"Total greeting examples: {len(entries)}")

    # Stats
    by_instruction = {}
    for e in entries:
        by_instruction.setdefault(e["instruction"], []).append(e)
    print(f"\nGreeting categories:")
    for inst, items in sorted(by_instruction.items(), key=lambda x: -len(x[1])):
        print(f"  [{len(items):2d}] {inst}")


if __name__ == "__main__":
    main()
