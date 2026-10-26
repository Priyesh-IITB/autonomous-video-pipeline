# Autonomous video pipeline

Turns a topic into a finished, sourced, narrated video — **research → script → voice →
motion graphics → thumbnail → captions → publish** — running **entirely on a CPU with no
paid inference APIs**.

Built as the production engine behind a weekly AI/security explainer channel. The narration
is an AI clone of the creator's *own* voice, and every upload discloses that it was made with
AI. This repo is the engine and a worked example; the raw personal assets (reference voice
clip, portrait) are intentionally not included — bring your own.

---

## Pipeline

```
 topic ─▶ script ─▶ voice ─▶ scenes ─▶ assemble ─▶ package
         (beats,    (clone,   (HTML/CSS  (mux +      (poster +
          scored     CPU)      animated,  Whisper-    thumbnail)
          hook)                captured)  aligned
                                          captions)
```

| Stage | What happens | File |
| --- | --- | --- |
| **Script** | Each video is a list of *beats*; a beat has spoken text, an optional phonetic `tts` override (so "dsh" is read "D S H"), and an HTML scene. A small builder emits `script.json`. | `examples/sandbox-cve/make_script.py` |
| **Voice** | Zero-shot voice clone ([Chatterbox](https://github.com/resemble-ai/chatterbox), MIT) from a ~20s reference clip. Pacing is tuned with the model's cfg weight — no pitch post-processing (that sounds robotic). Only changed beats are re-voiced. | `pipeline/tts.py` |
| **Scenes** | Every beat is an HTML/CSS scene on a shared theme. A headless Chromium steps the Web Animations API **frame-by-frame**, so capture is deterministic regardless of machine speed. | `pipeline/render.mjs`, `pipeline/theme.css` |
| **Assemble** | Scenes are sized to each beat's audio, muxed, concatenated; then captions are produced by re-transcribing the TTS (faster-whisper) and **snapping the timings back onto the exact script text** — perfect spelling, real timing. Chapters fall out of the beats. | `pipeline/build.py` |
| **Package** | Thumbnails/posters keep the creator's real face and let SDXL inpainting generate everything else (scene, clothing, light), then colour-match the face into it. | `pipeline/poster.py`, `pipeline/grade.py`, `pipeline/thumb.mjs` |
| **QA** | Each rendered line is re-transcribed and diffed against the script; mismatched beats are re-voiced before anything ships. | in `build.py` |

## Stack (all local, all CPU, all commercially licensed)

- **Voice:** Chatterbox TTS (MIT) — zero-shot cloning.
- **Imagery:** Stable Diffusion XL inpainting (OpenRAIL++) via `diffusers`; `rembg` for the cutout.
- **Captions / QA:** `faster-whisper` for transcription + alignment.
- **Render:** Playwright + Chromium (frame capture) and `ffmpeg` (encode); 1440p master for upload quality.

Licences were checked end to end so the whole chain is usable commercially (non-commercial
face-detector weights were deliberately avoided).

## Layout

```
pipeline/            the engine (voice, scenes, assemble, posters)
examples/
  sandbox-cve/       one video as data: its beat script + the fact pack behind it
  demo/              a benign, reproducible test harness used on-screen
```

## Worked example — `examples/sandbox-cve/`

A published video explaining a real agent-sandbox CVE. `make_script.py` is the whole script as
code (beats → `script.json`); `sources.md` is the fact pack, where every claim keeps its URL or
`file:line`. `examples/demo/netcheck.sh` is the kind of on-screen "demo" this channel uses — a
*benign* capability check (does a sandbox profile confine the network?), never an exploit.

## Running it

```bash
# voice + captions + cutout
python3 -m venv ~/ttsenv
~/ttsenv/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
~/ttsenv/bin/pip install chatterbox-tts faster-whisper "rembg[cpu]"

# image posters (separate venv: needs a different transformers pin)
python3 -m venv ~/imgenv
~/imgenv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
~/imgenv/bin/pip install diffusers "transformers<5" accelerate safetensors pillow numpy

npm i -g playwright     # Chromium; plus system ffmpeg

# supply your own: a ~20s reference voice clip and a portrait cutout
# (paths are referenced in pipeline/tts.py and pipeline/poster.py)

python3 pipeline/build.py examples/sandbox-cve
```

## Principles

- **Everything is sourced.** Claims trace to a URL or a `file:line`; unverifiable ones are cut.
- **Synthetic media is disclosed** on every upload.
- **Security work is read-only and responsible.** Findings come from reading public code; any
  not-yet-public vulnerability is reported privately and held under embargo before it is
  discussed. On-screen demos are benign capability checks, never exploits, never run against
  third parties.
