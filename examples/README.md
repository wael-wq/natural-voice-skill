# Before and after

Two real takes from one of our Reels, with the word timings ElevenLabs returned.
Listen to `before/take.mp3`, then `after/take.mp3`.

| | before | after |
|---|---|---|
| script | [before.txt](before.txt) | [after.txt](after.txt) |
| voice | Will | Chris |
| model | eleven_v4 | eleven_v4 |
| stability, speed | 0.5, 1.0 | 0.35, 1.05 |
| tags | none | `[excited]`, `[mischievously]` |
| takes | 1 | 3 seeds, this is seed 1 |

Try the tools on them:

```bash
python3 speakable.py examples/before.txt     # 65, REWRITE
python3 speakable.py examples/after.txt      # 100, SPEAKABLE
python3 gaps.py examples/before examples/after
```

```
1. examples/after    28.56 s, 82 words   FLOWS   (audio)
2. examples/before   29.84 s, 73 words   1 GAP   (audio)
     0.34 s   now | run
```

The before take stops for a third of a second in the middle of its first
sentence ("13 free Claude skills now ... run your Instagram"). That is the
moment people decide a voice is AI.

The voice changed between the two, so this is not a controlled test of one
setting. It is what fixed a real Reel.
