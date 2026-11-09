# natural-voice

A Claude Code skill that makes ElevenLabs voiceovers sound like a person.

Most robotic AI voiceovers are a script problem, not a voice problem. This skill
rewrites the script for the ear, directs it with audio tags, sets stability and
speed, generates seeded takes and ranks them by the gaps people hear as "AI".

Listen to [`examples/before/take.mp3`](examples/before/take.mp3) and
[`examples/after/take.mp3`](examples/after/take.mp3).

## Install

```bash
git clone https://github.com/wael-wq/natural-voice-skill ~/.claude/skills/natural-voice
```

Then in Claude Code, type `/natural-voice`, or just say "my voiceover sounds
robotic" with your script.

## What is inside

| file | what it does |
|---|---|
| `SKILL.md` | the method: diagnose, rewrite for the ear, direct, settings, takes, edit gently, Voice Changer |
| `speakable.py` | flags a script written for the eye: full-stop lists, digits, dashes, SSML, stacked or unknown tags |
| `takes.py` | seeded takes from the ElevenLabs API with word timings; prints the cost and sends nothing without `--yes` |
| `gaps.py` | ranks takes by silences inside sentences, confirmed against the audio with ffmpeg |
| `tags.md` | the audio tags worth using in a voiceover, and how to place them |

Python 3.9 or later, no packages (on Windows, type `python` for `python3`). ffmpeg is optional (it makes `gaps.py` check
the audio, not just the timings). `takes.py` needs `ELEVENLABS_API_KEY` in your
environment and costs ElevenLabs characters.

## Use it without Claude

```bash
python3 speakable.py script.txt
python3 takes.py script.txt --voice YOUR_VOICE_ID          # shows the cost
python3 takes.py script.txt --voice YOUR_VOICE_ID --yes    # seeds 1, 2, 3
python3 gaps.py takes/
```

## Sources

The settings and tag advice follow ElevenLabs' own prompting guide
(elevenlabs.io/docs/best-practices/prompting) and API reference. The
measurements are from our own Reels. Not affiliated with ElevenLabs.

MIT licence. Made by [Developers4U](https://developers4you.com.au).
