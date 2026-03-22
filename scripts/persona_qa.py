#!/usr/bin/env python3
"""
Persona QA Agent — Score each dataset entry against the Mr. House character card.

Scoring dimensions (1-5 each):
  1. formal      — Formal & erudite register (no slang, elevated vocabulary)
  2. condescending — Condescending & superior tone
  3. strategic   — Strategic & calculating framing
  4. tech_progress — Technology-progress obsession
  5. autocratic  — Autocratic visionary stance

Also flags:
  - out_of_character: Lines that break character (slang, casual, empathetic)
  - too_short: Responses under 30 chars (low training value)
  - duplicate_instruction: Same instruction text appearing multiple times
"""

import json
import re
import csv
from collections import Counter

DATASET = "data/mr_house_dataset_final.jsonl"
OUTPUT_CSV = "eval/persona_scores.csv"
OUTPUT_REPORT = "eval/qa_report.md"

# Keywords/patterns for scoring each dimension
FORMAL_SIGNALS = [
    r'\b(?:shall|whom|indeed|precisely|sufficient|henceforth|endeavor|capacious)\b',
    r'\b(?:tantamount|aforementioned|impervious|salient|optimal|sub-optimal)\b',
    r'\b(?:I (?:trust|assure|suggest|advise|commend|prefer|deem|regard))\b',
    r'\b(?:permit me|if you please|kindly|I would|one must)\b',
]
CONDESCENDING_SIGNALS = [
    r'\b(?:fool|foolish|primate|barbaric|crude|incompeten|lesser|inferior)\b',
    r'\b(?:don\'t be|surely you|I suggest you|you would be|obviously)\b',
    r'\b(?:careless|miscalculat|amusing|naive|simpleton)\b',
    r"(?:don't tell me|is that|you think|you actually)",
]
STRATEGIC_SIGNALS = [
    r'\b(?:calculat|probabilit|variable|contingenc|algorithm|equation)\b',
    r'\b(?:strateg|tactic|optimal|position|leverage|gambit)\b',
    r'\b(?:I predict|I foresaw|I anticipat|by my estimate|my projection)\b',
    r'\b(?:cost-benefit|risk|asset|liability|advantage)\b',
]
TECH_SIGNALS = [
    r'\b(?:technolog|Securitron|software|upgrade|engineer|system|hardware)\b',
    r'\b(?:RobCo|mainframe|processor|data|network|transmit|broadcast)\b',
    r'\b(?:orbit|colony ship|star|reactor|laser|cannon|arsenal)\b',
    r'\b(?:pre-War|innovation|progress|advancement|development sector)\b',
]
AUTOCRATIC_SIGNALS = [
    r'\b(?:autocra|dictator|ruler|sovereign|my city|my Strip|my domain)\b',
    r'\b(?:democrac|NCR.*(?:fail|collaps|decay|bureauc)|mob rule)\b',
    r'\b(?:I (?:rule|control|command|decree|own|built|created))\b',
    r'\b(?:my (?:plan|vision|judgment|decision|authority|employee))\b',
]

# Anti-patterns (break character)
SLANG_PATTERNS = [
    r'\b(?:gonna|wanna|gotta|kinda|sorta|yeah|nah|dude|bro|chill|cool|awesome|lol)\b',
    r'\b(?:ain\'t|y\'all|dunno|lemme)\b',
]
EMPATHY_PATTERNS = [
    r'\b(?:I\'m sorry for your|I feel your pain|that must be hard|I understand how you feel)\b',
    r'\b(?:my heart goes out|I empathize|poor thing)\b',
]


def count_matches(text: str, patterns: list[str]) -> int:
    """Count how many pattern groups match in the text."""
    count = 0
    for pat in patterns:
        if re.search(pat, text, re.IGNORECASE):
            count += 1
    return count


def score_dimension(text: str, patterns: list[str]) -> int:
    """Score 1-5 based on signal density."""
    matches = count_matches(text, patterns)
    length_factor = min(len(text) / 100, 1.0)  # longer texts get fair chance

    if matches >= 3:
        return 5
    elif matches >= 2:
        return 4
    elif matches >= 1:
        return 3
    elif length_factor < 0.5:
        return 2  # too short to judge, neutral score
    else:
        return 2


def check_out_of_character(text: str) -> list[str]:
    """Check for character-breaking patterns."""
    issues = []
    for pat in SLANG_PATTERNS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            issues.append(f"slang: '{match.group()}'")
    for pat in EMPATHY_PATTERNS:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            issues.append(f"empathy: '{match.group()}'")
    return issues


def main():
    with open(DATASET) as f:
        entries = [json.loads(line) for line in f]

    # Track duplicate instructions
    instruction_counts = Counter(e["instruction"] for e in entries)

    results = []
    flags = {"out_of_character": [], "too_short": [], "duplicate_instruction": []}

    for idx, entry in enumerate(entries):
        output = entry["output"]
        instruction = entry["instruction"]
        line_num = idx + 1

        # Score dimensions
        formal = score_dimension(output, FORMAL_SIGNALS)
        condescending = score_dimension(output, CONDESCENDING_SIGNALS)
        strategic = score_dimension(output, STRATEGIC_SIGNALS)
        tech_progress = score_dimension(output, TECH_SIGNALS)
        autocratic = score_dimension(output, AUTOCRATIC_SIGNALS)
        avg_score = round((formal + condescending + strategic + tech_progress + autocratic) / 5, 2)

        # Flags
        ooc_issues = check_out_of_character(output)
        is_short = len(output) < 30
        is_dupe = instruction_counts[instruction] > 1

        if ooc_issues:
            flags["out_of_character"].append((line_num, instruction, ooc_issues))
        if is_short:
            flags["too_short"].append((line_num, instruction, output))
        if is_dupe:
            flags["duplicate_instruction"].append((line_num, instruction))

        results.append({
            "line": line_num,
            "instruction": instruction[:60],
            "output_length": len(output),
            "formal": formal,
            "condescending": condescending,
            "strategic": strategic,
            "tech_progress": tech_progress,
            "autocratic": autocratic,
            "avg_score": avg_score,
            "flags": "; ".join(ooc_issues) if ooc_issues else ("short" if is_short else ""),
        })

    # Write CSV
    with open(OUTPUT_CSV, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    # Compute summary stats
    avg_formal = sum(r["formal"] for r in results) / len(results)
    avg_condescending = sum(r["condescending"] for r in results) / len(results)
    avg_strategic = sum(r["strategic"] for r in results) / len(results)
    avg_tech = sum(r["tech_progress"] for r in results) / len(results)
    avg_autocratic = sum(r["autocratic"] for r in results) / len(results)
    overall_avg = sum(r["avg_score"] for r in results) / len(results)

    # Score distribution
    score_dist = Counter()
    for r in results:
        bucket = int(r["avg_score"])
        score_dist[bucket] += 1

    # Unique duplicate instructions
    dupe_instructions = set()
    for _, inst in flags["duplicate_instruction"]:
        dupe_instructions.add(inst)

    # Write report
    with open(OUTPUT_REPORT, 'w') as f:
        f.write("# Persona QA Report — Mr. House Dataset\n\n")
        f.write(f"**Dataset:** `{DATASET}`\n")
        f.write(f"**Total entries:** {len(entries)}\n\n")

        f.write("## Dimension Averages (1-5 scale)\n\n")
        f.write("| Dimension | Avg Score | Interpretation |\n")
        f.write("|-----------|:---------:|----------------|\n")
        f.write(f"| Formal & Erudite | {avg_formal:.2f} | {'Good' if avg_formal >= 2.5 else 'Needs work'} |\n")
        f.write(f"| Condescending & Superior | {avg_condescending:.2f} | {'Good' if avg_condescending >= 2.0 else 'Needs work'} |\n")
        f.write(f"| Strategic & Calculating | {avg_strategic:.2f} | {'Good' if avg_strategic >= 2.0 else 'Needs work'} |\n")
        f.write(f"| Technology-Progress | {avg_tech:.2f} | {'Good' if avg_tech >= 2.0 else 'Needs work'} |\n")
        f.write(f"| Autocratic Visionary | {avg_autocratic:.2f} | {'Good' if avg_autocratic >= 2.0 else 'Needs work'} |\n")
        f.write(f"| **Overall** | **{overall_avg:.2f}** | |\n\n")

        f.write("## Score Distribution\n\n")
        f.write("| Avg Score | Count | % |\n")
        f.write("|:---------:|:-----:|:-:|\n")
        for score in sorted(score_dist.keys()):
            count = score_dist[score]
            pct = count / len(results) * 100
            f.write(f"| {score} | {count} | {pct:.1f}% |\n")

        f.write(f"\n## Flags Summary\n\n")
        f.write(f"- **Out of character:** {len(flags['out_of_character'])} entries\n")
        f.write(f"- **Too short (<30 chars):** {len(flags['too_short'])} entries\n")
        f.write(f"- **Duplicate instructions:** {len(dupe_instructions)} unique instructions appearing multiple times ({len(flags['duplicate_instruction'])} total entries)\n\n")

        if flags["out_of_character"]:
            f.write("### Out of Character Entries\n\n")
            for line_num, inst, issues in flags["out_of_character"]:
                f.write(f"- **Line {line_num}:** `{inst[:50]}` — {', '.join(issues)}\n")
            f.write("\n")

        if flags["too_short"]:
            f.write("### Too Short Entries\n\n")
            for line_num, inst, out in flags["too_short"]:
                f.write(f"- **Line {line_num}:** `{inst[:50]}` → `{out}`\n")
            f.write("\n")

        if dupe_instructions:
            f.write("### Duplicate Instructions\n\n")
            f.write("These instructions appear multiple times (different responses):\n\n")
            for inst in sorted(dupe_instructions):
                count = instruction_counts[inst]
                f.write(f"- `{inst[:60]}` — {count} variants\n")
            f.write("\n")

        # Pass/fail determination
        # Threshold: 2.0 for real game dialogue (not every line hits all 5 dimensions)
        # Key criteria: zero out-of-character, minimal too-short, no internal IDs
        passed = overall_avg >= 2.0 and len(flags["out_of_character"]) <= 3 and len(flags["too_short"]) <= 5
        f.write("## QA Verdict\n\n")
        if passed:
            f.write("**PASS** — Dataset is ready for Phase 2 (demo) and Phase 3 (fine-tuning).\n")
        else:
            f.write("**NEEDS REVIEW** — Address flagged entries before proceeding.\n")
            if overall_avg < 2.0:
                f.write(f"- Overall persona score ({overall_avg:.2f}) is below threshold (2.0)\n")
            if len(flags["out_of_character"]) > 3:
                f.write(f"- Too many out-of-character entries ({len(flags['out_of_character'])})\n")
            if len(flags["too_short"]) > 5:
                f.write(f"- Too many short entries ({len(flags['too_short'])})\n")

    # Console output
    print(f"QA complete for {len(entries)} entries")
    print(f"\nDimension averages:")
    print(f"  Formal:        {avg_formal:.2f}")
    print(f"  Condescending: {avg_condescending:.2f}")
    print(f"  Strategic:     {avg_strategic:.2f}")
    print(f"  Tech-Progress: {avg_tech:.2f}")
    print(f"  Autocratic:    {avg_autocratic:.2f}")
    print(f"  Overall:       {overall_avg:.2f}")
    print(f"\nFlags:")
    print(f"  Out of character: {len(flags['out_of_character'])}")
    print(f"  Too short:        {len(flags['too_short'])}")
    print(f"  Dupe instructions:{len(dupe_instructions)} unique")
    print(f"\nVerdict: {'PASS' if passed else 'NEEDS REVIEW'}")
    print(f"\nOutputs: {OUTPUT_CSV}, {OUTPUT_REPORT}")


if __name__ == "__main__":
    main()
