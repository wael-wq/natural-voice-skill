#!/usr/bin/env python3
"""Generates seeded ElevenLabs takes of one script, with word timings, so you can pick the best.

Usage: python3 takes.py script.txt --voice VOICE_ID                  (prints the cost, sends nothing)
       python3 takes.py script.txt --voice VOICE_ID --yes            (sends, seeds 1,2,3)
       python3 takes.py script.txt --voice VOICE_ID --seeds 4,5 --stability 0.4 --yes

Needs ELEVENLABS_API_KEY in the environment. Each take is saved to takes/seed-N/ (take.mp3,
alignment.json, request.json). A take already on disk is never sent again; change the text,
a setting or the seed to get a new one. Then run: python3 gaps.py takes/
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io/v1/text-to-speech/{voice}/with-timestamps?output_format=mp3_44100_128"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", help="the script, plain text, audio tags allowed")
    ap.add_argument("--voice", required=True, help="ElevenLabs voice id")
    ap.add_argument("--model", default="eleven_v4")
    ap.add_argument("--seeds", default="1,2,3")
    ap.add_argument("--stability", type=float, default=0.35)
    ap.add_argument("--similarity", type=float, default=0.75)
    ap.add_argument("--speed", type=float, default=1.05)
    ap.add_argument("--out", default="takes")
    ap.add_argument("--yes", action="store_true", help="actually send (paid)")
    a = ap.parse_args()

    text = open(a.file, encoding="utf-8").read().strip()
    seeds = [int(s) for s in a.seeds.split(",") if s.strip()]
    if not 0.7 <= a.speed <= 1.2:
        sys.exit("speed must be between 0.7 and 1.2")

    todo = [s for s in seeds if not os.path.exists(os.path.join(a.out, f"seed-{s}", "take.mp3"))]
    print(f"{len(text)} characters x {len(todo)} new take(s) = {len(text) * len(todo)} characters "
          f"(voice {a.voice}, {a.model}, stability {a.stability}, speed {a.speed})")
    for s in seeds:
        if s not in todo:
            print(f"  seed {s}: already on disk, not sent")
    if not todo:
        return
    if not a.yes:
        print("Nothing sent. Check your plan's character balance, then add --yes.")
        return
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("Set ELEVENLABS_API_KEY first (it is read from the environment and never printed).")

    for seed in todo:
        body = {
            "text": text,
            "model_id": a.model,
            "seed": seed,
            "voice_settings": {"stability": a.stability, "similarity_boost": a.similarity, "speed": a.speed},
        }
        req = urllib.request.Request(
            API.format(voice=a.voice),
            data=json.dumps(body).encode(),
            headers={"xi-api-key": key, "content-type": "application/json"},
        )
        print(f"  seed {seed}: sending...", end=" ", flush=True)
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                data = json.load(resp)
                request_id = resp.headers.get("request-id")
        except urllib.error.HTTPError as e:
            sys.exit(f"ElevenLabs returned {e.code}: {e.read().decode(errors='replace')[:300]}")
        folder = os.path.join(a.out, f"seed-{seed}")
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "take.mp3"), "wb") as f:
            f.write(base64.b64decode(data["audio_base64"]))
        alignment = data.get("alignment") or data.get("normalized_alignment")
        json.dump(alignment, open(os.path.join(folder, "alignment.json"), "w", encoding="utf-8"))
        json.dump({**body, "voice_id": a.voice, "request_id": request_id}, open(os.path.join(folder, "request.json"), "w", encoding="utf-8"), indent=2)
        print(f"saved {folder}")
    print(f"Next: python3 gaps.py {a.out}")


if __name__ == "__main__":
    main()
