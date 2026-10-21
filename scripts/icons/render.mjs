// Renders each plugin's marketplace icon (square PNG, 1024 px) from icons.html.
// Usage (from this folder): node render.mjs — needs the `playwright` package and a Chromium.
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const icons = { squad: 'squad', storm: 'storm-analyzer', job: 'job-evaluator' };

const browser = await chromium.launch(
  process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {},
);
const page = await browser.newPage({ viewport: { width: 512, height: 512 }, deviceScaleFactor: 2 });
await page.goto('file://' + path.join(here, 'icons.html'));
for (const [id, plugin] of Object.entries(icons)) {
  const out = path.join(here, '../../plugins', plugin, '.claude-plugin/icon.png');
  await page.locator('#' + id).screenshot({ path: out, omitBackground: true });
  console.log('wrote', out);
}
await browser.close();
