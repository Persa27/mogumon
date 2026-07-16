const { chromium } = require("playwright");

const DEBUG_ENDPOINT = "http://127.0.0.1:9222";
const GEMINI_URL = "https://gemini.google.com/app";

async function main() {
  const browser = await chromium.connectOverCDP(DEBUG_ENDPOINT);
  let page = null;
  try {
    const context = browser.contexts()[0];
    page = await context.newPage();
    await page.goto(GEMINI_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);

    // Click the upload/tools button
    const uploadBtn = page.locator('button[aria-label="アップロードとツール"]').first();
    await uploadBtn.waitFor({ state: "visible", timeout: 5000 });
    await uploadBtn.click();
    await page.waitForTimeout(2000);

    // List all menu items and buttons that appeared
    const items = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('[role="menuitem"], [role="option"], [role="listitem"], button, a'))
        .filter(el => {
          const text = el.textContent?.trim();
          return text && text.length > 0 && text.length < 80;
        })
        .map(el => ({
          tag: el.tagName,
          role: el.getAttribute("role"),
          text: el.textContent?.trim().slice(0, 60),
          ariaLabel: el.getAttribute("aria-label"),
        }));
    });
    console.log("=== Menu items after clicking upload button ===");
    items.forEach(i => console.log(JSON.stringify(i)));

    // Check file inputs
    const fileInputs = await page.evaluate(() => {
      return Array.from(document.querySelectorAll('input[type="file"]')).map(i => ({
        accept: i.getAttribute("accept"),
        id: i.id,
        name: i.name,
        visible: i.offsetWidth > 0 && i.offsetHeight > 0,
      }));
    });
    console.log("\n=== File Inputs ===");
    fileInputs.forEach(i => console.log(JSON.stringify(i)));

  } finally {
    if (page) await page.close().catch(() => {});
    await browser.close();
  }
}

main().catch(e => { console.error(e.message); process.exitCode = 1; });
