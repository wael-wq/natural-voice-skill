---
name: natural-voice
description: Make an ElevenLabs voiceover sound like a person instead of a robot - rewrite the script for the ear, direct it with audio tags, set stability and speed, generate seeded takes and pick the one that flows. Use when a TTS or AI voiceover sounds robotic, choppy, flat, "too AI" or has no emotion, pauses in the wrong places, when writing a voiceover script for ElevenLabs, or before paying for a long generation.
---

# natural-voice

Most "robotic" ElevenLabs voiceovers are not a voice problem. They are a script
problem. The model reads exactly what it is given, and a script written for the
eye (headlines, full-stop fragments, digits, dashes) comes back staccato no
matter which voice reads it.

Three tools in this folder actually run. Use them; do not judge flow by reading
the text.

```bash
python3 speakable.py script.txt                  # is this written for the ear?
python3 takes.py script.txt --voice VOICE_ID     # seeded takes (paid, asks first)
python3 gaps.py takes/                           # rank the takes by mid-sentence gaps
```

All three are plain Python 3.9+ with no packages. `gaps.py` uses ffmpeg if it is
on the PATH to confirm gaps against the audio itself.

## The loop

**1. Diagnose before you change anything.** If there is already a take, run
`gaps.py` on it. A gap over 0.2 s *inside* a sentence (not after a comma or a
full stop) is what people hear as "AI". In our own before take the voice
stopped 0.3 s before "run" and again before "Instagram", in the middle of the
hook. Nothing in our editing caused it: the gaps were in the raw file.

**2. Rewrite for the ear.** Run `speakable.py` and fix every flag. The rules:

- **Sentences, not headlines.** "13 free Claude skills now run your Instagram."
  is a title. "Thirteen free Claude skills run your whole Instagram." is
  something a person says.
- **Lists take commas, not full stops.** "Reels. Captions. Carousels." makes the
  model stop three times. "reels, captions, carousels, stories" flows.
- **Numbers as words** in the spoken line: "eighty-four out of a hundred", not
  "84 out of 100". The on-screen text can keep the digits.
- **Contractions** (you've, it's, we'll). Nobody says "you have" out loud.
- **Join the fragments** with "so", "and", "then". A connective is a cue for
  the model to keep going.
- **No dashes.** ElevenLabs treats a dash as a short pause and says itself it is
  "less consistent". Use a comma to keep going, or an ellipsis for a beat.
- **No SSML.** `<break time="1s"/>` is not supported on Eleven v4 or v3.

**3. Direct it.** Eleven v4 takes audio tags in square brackets. Put one tag at
the start of a beat, not on every line, and make it match what the line is
doing. See `tags.md` for the list. `speakable.py` flags tags it does not know,
because an unknown tag can be read as a sound effect.

```
[excited] Thirteen free Claude skills run your whole Instagram.
[mischievously] So we let it write this Reel...
```

Punctuation is direction too. An ellipsis adds a pause with weight, an
exclamation mark adds energy, and CAPITALS add emphasis (use them once, on the
word that matters).

**4. Settings.** On `eleven_v4`:

| setting | use | why |
|---|---|---|
| stability | 0.30 to 0.40 | Lower gives "broader emotional range"; the 0.5 default is flatter. Below 0.3 a take can drift. |
| similarity_boost | 0.75 | the default; keeps the voice itself |
| style | 0 | the default; anything else adds latency |
| speed | 1.0 to 1.08 | the allowed range is 0.7 to 1.2; social voiceover sits just above 1 |

**5. Three takes, same text, different seeds.** One take is a coin toss. Run
`takes.py` with seeds 1, 2 and 3, then `gaps.py` to rank them. Listen to the top
two and pick by ear. Keep the seed: it makes a re-run close to the same take
(ElevenLabs calls it "best effort", not guaranteed).

**6. Edit gently.** If your editor trims silences, keep about a second after
sentences and most of a second after commas. Pauses clipped to the same short
length every time are the other thing that sounds machine-made.

**7. Still sounds generated?** Stop turning knobs. Record yourself saying the
line on your phone and run it through ElevenLabs' Voice Changer
(speech-to-speech) into the voice you want. Your timing, emphasis and emotion
carry over; only the voice changes.

## What we measured

On one of our own Reels (the files are in `examples/`):

| | before | after |
|---|---|---|
| script | written for the eye: fragments, digits | written for the ear: `speakable.py` clean |
| tags | none | `[excited]`, `[mischievously]` |
| settings | stability 0.5, speed 1.0 | stability 0.35, speed 1.05 |
| takes | 1 | 3 seeds, picked by `gaps.py` then by ear |
| `speakable.py` | 65, REWRITE (a list in full stops, digits, no tags) | 100, SPEAKABLE |
| gaps inside sentences | 0.34 s between "now" and "run", in the hook | none |

The voice changed too (Will to Chris), so this is not a lab test of one
setting. The script rewrite made the biggest difference we could hear.

## Rules

- **Never send a paid request without saying what it costs.** `takes.py` prints
  the character count and stops unless you pass `--yes`.
- **Never print or commit the API key.** `takes.py` reads `ELEVENLABS_API_KEY`
  from the environment and nothing else.
- **Label it.** If the voice is generated, turn on the platform's AI label.
