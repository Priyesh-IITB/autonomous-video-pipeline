#!/usr/bin/env python3
"""poster.py - an AI-generated poster scene around Priyesh's real face, for thumbnails.

    /home/user/imgenv/bin/python poster.py ../videos/<slug> [--seed 7] [--steps 15]

Reads <slug>/poster.json: {"prompt": "...", "negative": "...", "side": "right"}.
Writes <slug>/poster.png (1344x768, no text; thumb.html adds the text on top).

How: the brand cutout is placed on a dark canvas; SDXL inpainting (OpenRAIL++, commercial use
allowed) regenerates everything except the face and hair: clothes, body, scene, light. The real face
is then pasted back with a feathered mask and colour-matched to the generated light, so it stays
recognisably him. Every upload using it carries YouTube's altered/synthetic content label.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageFilter

os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
import torch
from diffusers import StableDiffusionXLInpaintPipeline, DPMSolverMultistepScheduler

HERE = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
opt = {"--seed": "7", "--steps": "15", "--strength": "0.92"}
for k in list(opt):
    if k in args:
        i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
vdir = os.path.abspath(args[0])
cfg = json.load(open(os.path.join(vdir, "poster.json")))
W, H = 1344, 768

# 1. Canvas: person on one side, dark scene elsewhere.
cut = Image.open(os.path.join(HERE, "..", "brand", "priyesh_cutout.png")).convert("RGBA")
scale = cfg.get("person_height", 700) / cut.height
cut = cut.resize((round(cut.width * scale), round(cut.height * scale)), Image.LANCZOS)
x = W - cut.width - 60 if cfg.get("side", "right") == "right" else 60
y = cfg.get("top", 40)
canvas = Image.new("RGB", (W, H), (12, 14, 22))
canvas.paste(cut, (x, y), cut)

# 2. Keep mask = face and hair only (top of the cutout, above the jacket line).
alpha = np.zeros((H, W), np.float32)
a = np.asarray(cut.split()[3], np.float32) / 255
ch = a.shape[0]
a[int(ch * cfg.get("keep_ratio", 0.80)):, :] = 0  # below the beard: regenerate (clothes, body)
alpha[y:y + ch, x:x + a.shape[1]] = a[: H - y, :]
keep = Image.fromarray((alpha * 255).astype(np.uint8))
keep_core = keep.filter(ImageFilter.MinFilter(9))                     # what the model must not touch
regen = Image.eval(keep_core, lambda v: 255 - v).filter(ImageFilter.GaussianBlur(4))

# 3. Inpaint the scene.
torch.set_num_threads(os.cpu_count() or 4)
# Two loads: (1) text encoders alone, encode the prompts once, free them; (2) UNet + VAE in bf16.
# fp32 would be faster on this CPU (no native bf16) but the UNet alone is ~10 GB in fp32 and the
# job gets OOM-killed on a 15 GB box, so bf16 it is: slow (~2 min/step) but it fits. Hence the
# DPM++ sampler and low default step count.
MODEL = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
enc = StableDiffusionXLInpaintPipeline.from_pretrained(MODEL, variant="fp16", torch_dtype=torch.bfloat16,
                                                       unet=None, vae=None)
with torch.no_grad():
    pe, npe, ppe, nppe = enc.encode_prompt(prompt=cfg["prompt"], negative_prompt=cfg.get("negative", ""),
                                           device="cpu", do_classifier_free_guidance=True)
emb = dict(prompt_embeds=pe, negative_prompt_embeds=npe, pooled_prompt_embeds=ppe, negative_pooled_prompt_embeds=nppe)
del enc
import gc; gc.collect()
pipe = StableDiffusionXLInpaintPipeline.from_pretrained(MODEL, variant="fp16", torch_dtype=torch.bfloat16,
                                                        text_encoder=None, text_encoder_2=None)
pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config, use_karras_sigmas=True)
pipe.set_progress_bar_config(disable=True)
pipe.enable_attention_slicing(); pipe.enable_vae_tiling()  # keep peak memory under the 15 GB limit
gen = torch.Generator().manual_seed(int(opt["--seed"]))
img = pipe(**emb, image=canvas, mask_image=regen,
           width=W, height=H, num_inference_steps=int(opt["--steps"]), strength=float(opt["--strength"]),
           guidance_scale=7.0, generator=gen).images[0].resize((W, H))

# 4. Paste the real face back, colour-matched to the generated light around it.
out = np.asarray(img, np.float32) / 255
orig = np.asarray(canvas, np.float32) / 255
m = np.asarray(keep.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(5)), np.float32)[..., None] / 255
ring = np.asarray(keep.filter(ImageFilter.MaxFilter(41)), np.float32) / 255 - np.asarray(keep, np.float32) / 255
ring = ring > 0.5
face = (np.asarray(keep, np.float32) / 255) > 0.9
mt = float(cfg.get("match", 0.45))  # how far to pull the face toward the scene's light
mu_s, mu_f = out[ring].mean(0), orig[face].mean(0)
# Borrow the scene light's colour (tint), not its brightness: the background is darker than a face.
tint = (mu_s / max(mu_s.mean(), 1e-3)) / (mu_f / max(mu_f.mean(), 1e-3))
graded = np.clip(orig * tint ** mt * 0.92, 0, 1)
res = graded * m + out * (1 - m)
# 5. Blend pass: a light img2img over the WHOLE frame so face and scene share light and texture,
#    then pull the real face back in part-way so it stays recognisably him.
blend = float(cfg.get("blend", 0.28))
if blend > 0:
    full = Image.new("L", (W, H), 255)
    soft = pipe(**emb, image=Image.fromarray((res * 255).astype(np.uint8)), mask_image=full, width=W, height=H,
                num_inference_steps=int(opt["--steps"]), strength=blend, guidance_scale=6.0,
                generator=torch.Generator().manual_seed(int(opt["--seed"]) + 1)).images[0].resize((W, H))
    soft = np.asarray(soft, np.float32) / 255
    keep_id = float(cfg.get("identity", 0.55))  # share of the real face kept after the blend pass
    res = soft * (1 - m * keep_id) + res * (m * keep_id)

# 6. One grade over everything: teal shadows, warm-red highlights, vignette.
l = res.mean(-1, keepdims=True)
res = res + (1 - l) ** 2 * np.array([-0.02, 0.01, 0.04]) + l ** 2 * np.array([0.05, -0.01, -0.03])
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.45 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)[..., None] ** 1.5
res = np.clip(res * np.clip(vig, 0.4, 1), 0, 1)
Image.fromarray((res * 255).astype(np.uint8)).save(os.path.join(vdir, "poster.png"))
print("poster", os.path.join(vdir, "poster.png"))
