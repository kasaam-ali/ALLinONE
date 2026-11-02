// Job: GODMODE Frontend. Purpose: Playwright smoke that checks login and shell render, tries live login, falls back to fixture mode, and saves screenshots.
// Usage: node e2e/smoke.mjs [baseUrl] [outDir]  (needs `playwright` resolvable, e.g. NODE_PATH)
import { chromium } from "playwright";
const base = process.argv[2] || "http://localhost:3010";
const out = process.argv[3] || "/workspace/godmode/refs/ui-after";
const b = await chromium.launch();
const p = await b.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });
await p.goto(base + "/login"); await p.waitForSelector("text=Sign in to Command Center");
await p.screenshot({ path: `${out}/login.png` });
await p.fill("input[type=email]", "admin@godmode.local"); await p.fill("input[type=password]", "godmode123");
await p.click("button[type=submit]"); await p.waitForTimeout(1500);
let mode = "live";
if (p.url().endsWith("/login")) { mode = "fixture"; await p.evaluate(() => localStorage.setItem("gm_fixture_mode", "1")); }
for (const [path, name] of [["/", "dashboard"], ["/tasks", "tasks"], ["/tasks/101", "task-detail"], ["/workforce", "workforce"]]) {
  await p.goto(base + path); await p.waitForSelector(".shell"); await p.waitForTimeout(1200);
  await p.screenshot({ path: `${out}/${name}.png` });
}
console.log(`smoke ok, mode=${mode}, badge=${await p.textContent(".top .chip")}`);
await b.close();
