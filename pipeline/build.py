#!/usr/bin/env python3
"""build.py - turn a video folder into a finished mp4.

    python3 build.py ../videos/<slug> [--portrait] [--force-render]

The folder holds script.json:
    {"title": "...", "beats": [{"id": "b01", "chapter": "optional", "say": "spoken words",
                                "html": "<div class='stage'>...</div>", "css": "optional"}]}

Steps: voice each beat (tts.py, cloned voice) -> scene length = beat audio + a short breath ->
render scenes (render.mjs) -> mux audio per beat -> concat -> captions aligned to the SCRIPT text
(whisper gives timings, the script gives spelling) -> burn in -> final.mp4 + chapters.txt.
"""
import difflib, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
TTS_PY = "/home/user/ttsenv/bin/python"
BREATH = 0.35  # silence after each beat so cuts do not feel clipped

args = sys.argv[1:]
portrait = "--portrait" in args
vdir = os.path.abspath([a for a in args if not a.startswith("--")][0])
script = json.load(open(os.path.join(vdir, "script.json")))
beats = script["beats"]
work = os.path.join(vdir, "build")
for d in ("audio", "audio_fx", "scenes", "beats"):
    os.makedirs(os.path.join(work, d), exist_ok=True)

def run(cmd, **kw):
    print("+", " ".join(cmd[:4]), "...", flush=True)
    subprocess.run(cmd, check=True, **kw)

def duration(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", path]).strip())

# 1. voice
run([TTS_PY, os.path.join(HERE, "tts.py"), os.path.join(vdir, "script.json"), os.path.join(work, "audio")])

# 1b. voice settings (pitch/tempo) from ../voice/settings.json, applied to every beat
vs = json.load(open(os.path.join(HERE, "..", "voice", "settings.json")))
for b in beats:
    src, dst = (os.path.join(work, d, f"{b['id']}.wav") for d in ("audio", "audio_fx"))
    fx = [] if vs["pitch"] == 1 and vs["tempo"] == 1 else ["-af", f"rubberband=pitch={vs['pitch']}:tempo={vs['tempo']}"]
    run(["ffmpeg", "-v", "error", "-y", "-i", src] + fx + [dst])

# 2. scenes sized to the audio
scenes = []
for b in beats:
    b["dur"] = duration(os.path.join(work, "audio_fx", f"{b['id']}.wav")) + BREATH
    scenes.append({"id": b["id"], "html": b["html"], "css": b.get("css", ""), "duration": b["dur"]})
json.dump(scenes, open(os.path.join(work, "scenes.json"), "w"))
chromium = next((os.path.join(r, f) for r, _, fs in os.walk("/opt/pw-browsers") for f in fs
                 if f == "chrome" and "headless" not in r), None)
env = dict(os.environ, CHROMIUM=chromium or "")
cmd = ["node", os.path.join(HERE, "render.mjs"), os.path.join(work, "scenes.json"), os.path.join(work, "scenes")]
cmd += (["--portrait"] if portrait else []) + (["--force"] if "--force-render" in args else [])
run(cmd, env=env)

# 3. mux each beat, then concat
lst = []
for b in beats:
    out = os.path.join(work, "beats", f"{b['id']}.mp4")
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(work, "scenes", f"{b['id']}.mp4"),
         "-i", os.path.join(work, "audio_fx", f"{b['id']}.wav"),
         "-af", f"apad=whole_dur={b['dur']:.3f},aresample=48000", "-c:v", "copy", "-c:a", "aac",
         "-b:a", "192k", "-t", f"{b['dur']:.3f}", out])
    lst.append(f"file '{out}'")
open(os.path.join(work, "list.txt"), "w").write("\n".join(lst) + "\n")
joined = os.path.join(work, "joined.mp4")
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", os.path.join(work, "list.txt"),
     "-c", "copy", joined])

# 4. captions: whisper timings, script spelling
from faster_whisper import WhisperModel
import numpy as np
model = WhisperModel("small", device="cpu", compute_type="int8")
norm = lambda w: re.sub(r"[^a-z0-9]", "", w.lower())
cues, t0 = [], 0.0
for b in beats:
    wav = os.path.join(work, "audio_fx", f"{b['id']}.wav")
    pcm = subprocess.check_output(["ffmpeg", "-v", "error", "-i", wav, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"])
    segs, _ = model.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, language="en")
    heard = [w for s in segs for w in s.words]
    said = b["say"].split()
    times = [None] * len(said)
    sm = difflib.SequenceMatcher(a=[norm(w) for w in said], b=[norm(w.word) for w in heard], autojunk=False)
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = heard[blk.b + k]; times[blk.a + k] = (w.start, w.end)
    # fill gaps by interpolating between known neighbours
    end = b["dur"] - BREATH
    for i in range(len(said)):
        if times[i] is None:
            prev = next((times[j][1] for j in range(i - 1, -1, -1) if times[j]), 0.0)
            nxt = next(((j, times[j][0]) for j in range(i + 1, len(said)) if times[j]), (len(said), end))
            step = (nxt[1] - prev) / (nxt[0] - i + 1)
            times[i] = (prev, prev + step)
    # phrases of up to 5 words, broken at punctuation
    cur = []
    for i, w in enumerate(said):
        cur.append(i)
        if len(cur) == 5 or re.search(r"[.,?!:;]$", w) or i == len(said) - 1:
            cues.append((t0 + times[cur[0]][0], t0 + times[cur[-1]][1], " ".join(said[j] for j in cur)))
            cur = []
    t0 += b["dur"]

def ts(s):
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
W, H = (1080, 1920) if portrait else (1920, 1080)
size, margin = (64, 420) if portrait else (52, 150)
ass = [f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n",
       "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, "
       "BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV",
       f"Style: C,Inter,{size},&H00FFFFFF,&H00000000,&H99000000,1,4,0,0,2,80,80,{margin}\n",
       "[Events]\nFormat: Layer, Start, End, Style, Text"]
for i, (a, z, text) in enumerate(cues):
    z = max(z, a + 0.4)
    if i + 1 < len(cues): z = min(z, cues[i + 1][0])
    ass.append(f"Dialogue: 0,{ts(a)},{ts(z)},C,{text}")
open(os.path.join(work, "captions.ass"), "w").write("\n".join(ass) + "\n")

final = os.path.join(vdir, "final.mp4")
run(["ffmpeg", "-v", "error", "-y", "-i", joined, "-vf", f"ass={os.path.join(work, 'captions.ass')}",
     "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "copy", "-movflags", "+faststart", final])

# 5. chapters from beats that open one
t, chap = 0.0, []
for b in beats:
    if b.get("chapter"): chap.append(f"{int(t // 60)}:{int(t % 60):02d} {b['chapter']}")
    t += b["dur"]
open(os.path.join(vdir, "chapters.txt"), "w").write("\n".join(chap) + "\n")
words = sum(len(b["say"].split()) for b in beats)
print(f"done: {final}  {t:.1f}s  {words} words  {words / (t / 60):.0f} wpm")
