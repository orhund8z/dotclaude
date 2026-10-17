// Renders the squad README images from the HTML sources in this folder.
// Usage (from this folder): node render.mjs   — needs the `playwright` package and a Chromium.
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const images = [
  { src: 'hero.html', out: '../squad-hero.png', width: 1200, height: 675 },
  { src: 'personas.html', out: '../squad-personas.png', width: 1160, height: 560 },
];

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
);
const page = await browser.newPage({ deviceScaleFactor: 2 });
for (const { src, out, width, height } of images) {
  await page.setViewportSize({ width, height });
  await page.goto('file://' + path.join(here, src));
  await page.screenshot({ path: path.join(here, out), clip: { x: 0, y: 0, width, height } });
  console.log('wrote', out);
}
await browser.close();
