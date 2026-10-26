// Render animated HTML scenes to mp4 clips, deterministically, frame by frame.
//
//   node render.mjs scenes.json outdir [--portrait]
//
// scenes.json: [{ "id": "b01", "html": "<div class='stage'>...</div>", "duration": 7.4 }]
// Each scene's CSS animations are paused and stepped with the Web Animations API, so the output
// does not depend on how fast the machine is. Frames stop once every finite animation has ended;
// the last frame is then held for the rest of the scene.
import { chromium } from "playwright";
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const [, , scenesPath, outDir, ...flags] = process.argv;
const portrait = flags.includes("--portrait");
const W = portrait ? 1080 : 1920, H = portrait ? 1920 : 1080, FPS = 30;
const here = path.dirname(new URL(import.meta.url).pathname);
const css = fs.readFileSync(path.join(here, "theme.css"), "utf8");
const scenes = JSON.parse(fs.readFileSync(scenesPath, "utf8"));
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
const page = await browser.newPage({ viewport: { width: W, height: H } });

for (const s of scenes) {
  const out = path.join(outDir, `${s.id}.mp4`);
  if (fs.existsSync(out) && !flags.includes("--force")) { console.log("skip", s.id); continue; }
  await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${css}</style>
    <style>${s.css || ""}</style></head><body class="${portrait ? "portrait" : ""}">${s.html}
    <div class="brand">PRIYESH VERMA</div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  const animEnd = await page.evaluate(() => {
    let end = 0;
    for (const a of document.getAnimations()) {
      a.pause();
      const t = a.effect.getComputedTiming();
      if (Number.isFinite(t.endTime)) end = Math.max(end, t.endTime);
    }
    return end / 1000;
  });
  const hasLoop = await page.evaluate(() =>
    document.getAnimations().some(a => !Number.isFinite(a.effect.getComputedTiming().endTime)));
  // Looping animations (a blinking cursor) need every frame; otherwise stop at the last build-in.
  const animSecs = hasLoop ? s.duration : Math.min(s.duration, animEnd + 1 / FPS);
  const nFrames = Math.max(1, Math.ceil(animSecs * FPS));

  const ff = spawn("ffmpeg", ["-v", "error", "-y", "-f", "image2pipe", "-framerate", String(FPS),
    "-i", "-", "-vf", `tpad=stop_mode=clone:stop_duration=${Math.max(0, s.duration - nFrames / FPS).toFixed(3)},format=yuv420p`,
    "-r", String(FPS), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", out],
    { stdio: ["pipe", "inherit", "inherit"] });
  for (let f = 0; f < nFrames; f++) {
    const t = (f / FPS) * 1000;
    await page.evaluate(t => document.getAnimations().forEach(a => { a.currentTime = t; }), t);
    const buf = await page.screenshot({ type: "png" });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once("drain", r));
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on("close", c => c === 0 ? res() : rej(new Error(`ffmpeg ${c}`))));
  console.log("rendered", s.id, `${nFrames} frames, ${s.duration.toFixed(1)}s`);
}
await browser.close();
