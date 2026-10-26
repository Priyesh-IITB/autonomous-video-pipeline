// Render a 1280x720 thumbnail from an HTML fragment that uses theme.css.
//   node thumb.mjs thumb.html out.png [photo.png]
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
const [, , src, out, photoPath] = process.argv;
const here = path.dirname(new URL(import.meta.url).pathname);
const css = fs.readFileSync(path.join(here, "theme.css"), "utf8");
// {{PHOTO}} in the HTML becomes photo.png (default: the brand cutout) as a data URI.
const photo = "data:image/png;base64," +
  fs.readFileSync(photoPath || path.join(here, "..", "brand", "priyesh_cutout.png")).toString("base64");
const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
await page.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head>
  <body>${fs.readFileSync(src, "utf8").replaceAll("{{PHOTO}}", photo)}</body></html>`);
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: out, type: "png" });
await browser.close();
