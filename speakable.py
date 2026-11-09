#!/usr/bin/env python3
"""Is this script written for the ear? Flags what makes ElevenLabs read it like a robot.

Usage: python3 speakable.py script.txt
       python3 speakable.py --text "one line to check"

Exit code 1 when anything is flagged as FIX, so it can gate a pipeline.
"""
import argparse
import re
import sys

# Voice tags from ElevenLabs' prompting guide (see tags.md). Anything else may come out as a sound effect.
KNOWN_TAGS = {
    "excited", "curious", "sarcastic", "mischievously", "happy", "professional", "sympathetic",
    "reassuring", "questioning", "cute", "laughs", "laughs harder", "starts laughing", "giggles",
    "sighs", "sigh", "exhales", "pauses", "whispers", "happy gasp", "frustrated sigh",
}
CONTRACTION = re.compile(r"\b\w+'(s|re|ve|ll|d|t|m)\b", re.I)
TAG = re.compile(r"\[([^\]]+)\]")


def sentences(text):
    """Sentences with their tags removed, split on . ! ? and ellipses."""
    plain = TAG.sub("", text)
    parts = re.split(r"(?<=[.!?…])\s+", plain.strip())
    return [p.strip() for p in parts if p.strip()]


def check(text):
    found = []  # (level, rule, detail)

    def add(level, rule, detail):
        found.append((level, rule, detail))

    if re.search(r"<\s*break\b", text, re.I):
        add("FIX", "ssml", "SSML <break> is not supported on Eleven v4 or v3. Use an ellipsis or [pauses].")

    tags = TAG.findall(text)
    for tag in tags:
        if tag.strip().lower() not in KNOWN_TAGS:
            add("WARN", "unknown-tag", f"[{tag}] is not a known voice tag and may be read as a sound effect.")
    for m in re.finditer(r"(\[[^\]]+\]\s*){2,}", text):
        add("FIX", "stacked-tags", f"{m.group(0).strip()} stacks tags. One tag per beat.")

    sents = sentences(text)
    words = re.findall(r"[A-Za-z0-9'’]+", TAG.sub("", text))
    if not sents:
        add("FIX", "empty", "No text.")
        return found, 0

    # A run of three or more tiny sentences is a list written with full stops: the model stops on each one.
    run = []
    for s in sents + [""]:
        if s and len(s.split()) <= 3:
            run.append(s)
            continue
        if len(run) >= 3:
            add("FIX", "fragments", f"{' '.join(run)}  ->  a list in full stops. Join it with commas.")
        run = []

    for s in sents:
        n = len(s.split())
        if re.search(r"\s[-–—]\s|—|–|--", s):
            add("FIX", "dash", f"\"{s}\"  ->  a dash is an inconsistent pause. Use a comma or an ellipsis.")
        if re.search(r"\d", s):
            add("WARN", "digits", f"\"{s}\"  ->  write spoken numbers as words (on-screen text can keep digits).")
        if re.search(r"[&%+/→#@]", s):
            add("WARN", "symbols", f"\"{s}\"  ->  spell symbols out the way you would say them.")
        if n > 28 and "," not in s:
            add("WARN", "no-breath", f"\"{s[:60]}...\"  ->  {n} words with nowhere to breathe. Add a comma.")
        caps = [w for w in s.split() if len(w) > 2 and w.isupper()]
        if len(caps) > 2:
            add("WARN", "caps", f"\"{s}\"  ->  CAPITALS add emphasis. Keep it to the one word that matters.")

    first = sents[0]
    if not re.search(r"\b(is|are|was|were|be|been|'s|'re|run|runs|do|does|did|have|has|had|can|will|we|you|i|it)\b", first, re.I):
        add("WARN", "headline", f"\"{first}\"  ->  reads like a title. Say it as a sentence with a verb.")

    if len(words) >= 40 and not CONTRACTION.search(text):
        add("WARN", "no-contractions", "No contractions in 40+ words. People say you've, it's, we'll.")
    if not tags and len(words) >= 25:
        add("INFO", "no-direction", "No audio tags. One tag at the start of a beat gives the model an emotion to play.")
    elif tags and len(tags) > max(2, len(sents) // 2):
        add("WARN", "too-many-tags", f"{len(tags)} tags in {len(sents)} sentences. One per beat is plenty.")

    penalty = sum({"FIX": 15, "WARN": 6, "INFO": 2}[lvl] for lvl, _, _ in found)
    return found, max(0, 100 - penalty)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--text")
    a = ap.parse_args()
    if a.text is None and not a.file:
        ap.error("pass a script file or --text")
    text = a.text if a.text is not None else open(a.file, encoding="utf-8").read()

    found, score = check(text)
    words = len(re.findall(r"[A-Za-z0-9'’]+", TAG.sub("", text)))
    print(f"{words} words, {len(sentences(text))} sentences, {len(TAG.findall(text))} audio tags, {len(text)} characters")
    print("-" * 62)
    for level, rule, detail in found:
        print(f"  {level:<5} {rule:<16} {detail}")
    if not found:
        print("  nothing to fix")
    print("-" * 62)
    fixes = sum(1 for lvl, _, _ in found if lvl == "FIX")
    verdict = "SPEAKABLE" if fixes == 0 and score >= 80 else "REWRITE"
    print(f"  SCORE {score}   {verdict}")
    sys.exit(1 if fixes else 0)


if __name__ == "__main__":
    main()
