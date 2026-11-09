#!/usr/bin/env python3
"""Ranks voice takes by the gaps people hear as "AI": silences in the middle of a sentence.

Usage: python3 gaps.py takes/                  (every takes/*/alignment.json)
       python3 gaps.py a/alignment.json b/alignment.json
       python3 gaps.py takes/ --threshold 0.15

Reads the character alignment ElevenLabs returns from /with-timestamps. Expressive models report
word ends early (the sound often carries on past the reported end), so a gap in the timings is not
always silence. When ffmpeg is on the PATH and the take's audio sits next to its alignment, each gap
is confirmed against the audio and only real silences are counted.
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess

AUDIO_NAMES = ("take.mp3", "narration.raw.mp3", "audio.mp3")


def load_alignment(path):
    data = json.load(open(path, encoding="utf-8"))
    a = data.get("alignment") or data.get("normalized_alignment") or data
    chars = a["characters"]
    starts = a.get("character_start_times_seconds") or a.get("startSeconds")
    ends = a.get("character_end_times_seconds") or a.get("endSeconds")
    return chars, starts, ends


def words_of(chars, starts, ends):
    words, cur, in_tag = [], None, False
    for c, t0, t1 in zip(chars, starts, ends):
        if c == "[":
            in_tag = True
        if in_tag:
            in_tag = c != "]"
            continue
        if c.isspace():
            if cur:
                words.append(cur)
            cur = None
            continue
        if cur is None:
            cur = [c, t0, t1]
        else:
            cur[0] += c
            cur[2] = t1
    if cur:
        words.append(cur)
    return words


def silences(audio, threshold):
    """Silent ranges measured in the audio (ffmpeg silencedetect)."""
    out = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", audio, "-af", f"silencedetect=noise=-42dB:d={threshold / 2}", "-f", "null", "-"],
        capture_output=True, text=True,
    ).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", out)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", out)]
    return list(zip(starts, ends))


def analyse(path, threshold):
    chars, starts, ends = load_alignment(path)
    words = words_of(chars, starts, ends)
    folder = os.path.dirname(path)
    audio = next((os.path.join(folder, n) for n in AUDIO_NAMES if os.path.exists(os.path.join(folder, n))), None)
    measured = silences(audio, threshold) if audio and shutil.which("ffmpeg") else None

    gaps = []
    for prev, word in zip(words, words[1:]):
        if re.search(r"[.?!,;:…]['\"”’)]*$", prev[0]):
            continue  # a pause after punctuation is phrasing, not a glitch
        start, end = prev[2], word[1]
        if end - start <= threshold:
            continue
        if measured is not None:
            # keep only the part of the gap that is actually silent
            silent = sum(max(0, min(end, e) - max(start, s)) for s, e in measured)
            if silent <= threshold:
                continue
            gap = silent
        else:
            gap = end - start
        gaps.append((f"{prev[0]} | {word[0]}", round(gap, 2)))
    return {
        "take": folder or path,
        "seconds": round(words[-1][2], 2) if words else 0,
        "words": len(words),
        "gaps": gaps,
        "checked": "audio" if measured is not None else "timings only",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--threshold", type=float, default=0.2, help="seconds; default 0.2")
    a = ap.parse_args()

    files = []
    for p in a.paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "*", "alignment.json"))) or sorted(glob.glob(os.path.join(p, "alignment.json")))
        else:
            files.append(p)
    if not files:
        ap.error("no alignment.json found")

    results = sorted((analyse(f, a.threshold) for f in files), key=lambda r: (len(r["gaps"]), sum(g for _, g in r["gaps"])))
    print(f"Gaps over {a.threshold} s inside a sentence (best take first)")
    print("-" * 62)
    for i, r in enumerate(results, 1):
        flag = "FLOWS" if not r["gaps"] else f"{len(r['gaps'])} GAP{'S' if len(r['gaps']) > 1 else ''}"
        print(f"{i}. {r['take']}   {r['seconds']} s, {r['words']} words   {flag}   ({r['checked']})")
        for where, gap in r["gaps"]:
            print(f"     {gap:.2f} s   {where}")
    print("-" * 62)
    print("Listen to the top two and pick by ear. The numbers find the glitches; your ear finds the feeling.")


if __name__ == "__main__":
    main()
