#!/usr/bin/env python3
"""tts.py - speak each beat of a script in Priyesh's cloned voice.

    /home/user/ttsenv/bin/python tts.py script.json outdir [--ref ../voice/ref_normal.wav] [--cfg 0.35] [--exag 0.45]

--cfg lower = slower, more deliberate pacing; --exag higher = more expressive delivery.

script.json: {"beats": [{"id": "b01", "say": "spoken text", "tts": "optional phonetic version"}, ...]}
"say" is what captions show; "tts", when present, is what the voice reads (e.g. "D S H" for "dsh").
Writes outdir/<id>.wav (24 kHz mono). Existing files are kept, so a re-run only voices changed
beats (delete a wav to redo it). Uses Chatterbox (MIT licence) zero-shot cloning from a short
reference clip of the real voice. Every upload made with this audio is flagged as synthetic media.
"""
import json, os, re, sys

os.environ.setdefault("TQDM_DISABLE", "1")
import torch, torchaudio
from chatterbox.tts import ChatterboxTTS

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
opts = {"--ref": os.path.join(HERE, "..", "voice", "ref_normal.wav"), "--cfg": "0.35", "--exag": "0.45"}
for k in list(opts):
    if k in args:
        i = args.index(k); opts[k] = args[i + 1]; del args[i:i + 2]
ref, cfg, exag = opts["--ref"], float(opts["--cfg"]), float(opts["--exag"])
script, out = args[0], args[1]
os.makedirs(out, exist_ok=True)
torch.set_num_threads(os.cpu_count() or 4)

model = ChatterboxTTS.from_pretrained(device="cpu")
model.prepare_conditionals(ref, exaggeration=exag)

def chunks(text, limit=240):
    # Chatterbox drifts on long inputs; voice sentence groups under ~240 chars and join them.
    parts, cur = [], ""
    for s in re.split(r"(?<=[.?!])\s+", text.strip()):
        if cur and len(cur) + len(s) > limit:
            parts.append(cur); cur = s
        else:
            cur = f"{cur} {s}".strip()
    return parts + ([cur] if cur else [])

for beat in json.load(open(script))["beats"]:
    path = os.path.join(out, f"{beat['id']}.wav")
    if os.path.exists(path):
        continue
    gap = torch.zeros(1, int(model.sr * 0.18))
    pieces = []
    for c in chunks(beat.get("tts") or beat["say"]):
        pieces += [model.generate(c, temperature=0.7, cfg_weight=cfg, exaggeration=exag), gap]
    torchaudio.save(path, torch.cat(pieces[:-1], dim=1), model.sr)
    print("voiced", beat["id"], flush=True)
