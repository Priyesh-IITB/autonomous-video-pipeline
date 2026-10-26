#!/usr/bin/env python3
"""grade.py - re-light the brand cutout so it sits inside a thumbnail scene instead of on top of it.

    /home/user/ttsenv/bin/python grade.py out.png [--key "#f87171"] [--fill "#38bdf8"] [--side right]

Takes channel/brand/priyesh_cutout.png and applies, in order: a cinematic grade (cool shadows, warm
skin), a coloured key light falling off across the face from --side, a cool fill from the other side,
a rim light on the silhouette edge, and a fade at the bottom so the shoulders dissolve into the scene.
Film grain and the vignette are added later over the whole thumbnail so subject and scene share them.
"""
import sys
import numpy as np
from PIL import Image, ImageFilter

HERE = __file__.rsplit("/", 1)[0]
args = sys.argv[1:]
opt = {"--key": "#f87171", "--fill": "#38bdf8", "--side": "right", "--style": "relight"}
for k in list(opt):
    if k in args:
        i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
out = args[0]
rgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255

im = Image.open(f"{HERE}/../brand/priyesh_cutout.png").convert("RGBA")
# Upscale with a light sharpen so the small source holds up at thumbnail height.
im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS).filter(ImageFilter.UnsharpMask(2, 60, 2))
# Trim the fringe the white studio background leaves on hair edges.
r, g, b, al = im.split()
im = Image.merge("RGBA", (r, g, b, al.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.2))))
a = np.asarray(im, np.float32) / 255
c, alpha = a[..., :3], a[..., 3:4]
h, w = alpha.shape[:2]
luma = (c @ np.array([0.299, 0.587, 0.114], np.float32))[..., None]

# 1. Grade: crush the white-background spill, cool the shadows, keep skin warm.
c = np.clip((c - 0.06) * 1.12, 0, 1)
# Semi-transparent edge pixels still carry white; darken them toward the scene.
c = c * np.clip(alpha * 1.4, 0.35, 1)
shadows = np.clip(1 - luma * 1.8, 0, 1)
c = c + shadows * np.array([-0.03, 0.01, 0.05]) * 1.2
c = c * 0.86 + 0.14 * luma  # pull saturation down slightly, posters read cleaner

# 1b. Duotone poster style: map brightness onto a dark->key->near-white ramp in the scene palette.
if opt["--style"] == "duotone":
    t = np.clip((luma - 0.08) / 0.8, 0, 1) ** 0.9
    t = t * t * (3 - 2 * t)  # smoothstep for punchier contrast
    dark, key_c, hi = np.array([0.03, 0.04, 0.09]), rgb(opt["--key"]), np.array([1.0, 0.93, 0.9])
    c = np.where(t < 0.6, dark + (key_c - dark) * (t / 0.6), key_c + (hi - key_c) * ((t - 0.6) / 0.4))
    c = c * 0.85 + c * (luma / max(luma.max(), 1e-3)) * 0.15  # keep a little tonal detail

# 2. Key and fill light across x.
x = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
k = x if opt["--side"] == "right" else 1 - x
key, fill = rgb(opt["--key"]), rgb(opt["--fill"])
c = c * (0.42 + 0.62 * k) + key * (k ** 1.8) * 0.42 * (0.35 + luma) + fill * ((1 - k) ** 2.0) * 0.20 * (0.3 + luma)

# 3. Rim light: the silhouette edge, strongest on the key side.
amask = Image.fromarray((alpha[..., 0] * 255).astype(np.uint8))
eroded = np.asarray(amask.filter(ImageFilter.MinFilter(15)), np.float32)[..., None] / 255
edge = np.clip(alpha - eroded, 0, 1)
edge = np.asarray(Image.fromarray((edge[..., 0] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)),
                  np.float32)[..., None] / 255
c = c + edge * key * (0.25 + 0.9 * k)

# 4. Shoulders dissolve into the scene.
y = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
alpha = alpha * np.clip((1 - y) / 0.22, 0, 1) ** 1.3

Image.fromarray((np.dstack([np.clip(c, 0, 1), alpha]) * 255).astype(np.uint8), "RGBA").save(out)
print("graded", out, (w, h))
