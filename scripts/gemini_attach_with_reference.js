const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const DEBUG_ENDPOINT = "http://127.0.0.1:9222";
const GEMINI_URL = "https://gemini.google.com/app";

function parseArgs(argv) {
  const args = {
    prompt: "",
    promptFile: "",
    referenceFile: "",
    outputFile: "",
    timeoutMs: 300000
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--prompt") {
      args.prompt = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--prompt-file") {
      args.promptFile = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--reference-file") {
      args.referenceFile = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--output-file") {
      args.outputFile = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--timeout-ms") {
      args.timeoutMs = Number(argv[i + 1] || args.timeoutMs);
      i += 1;
    }
  }

  return args;
}

function loadPrompt({ prompt, promptFile }) {
  if (prompt) {
    return prompt.trim();
  }
  if (promptFile) {
    return fs.readFileSync(path.resolve(promptFile), "utf8").trim();
  }
  return "";
}

async function waitForComposer(page) {
  const selectors = ["textarea", '[contenteditable="true"]', '[role="textbox"]'];
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      await locator.waitFor({ state: "visible", timeout: 5000 });
      return locator;
    } catch (_) {
      // Keep trying.
    }
  }
  throw new Error("Gemini input box was not found.");
}

async function openNewChat(page) {
  const candidates = [
    page.getByRole("button", { name: /新しいチャット|New chat/i }).first(),
    page.locator('button[aria-label*="New chat"], button[aria-label*="新しいチャット"]').first()
  ];

  for (const candidate of candidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 3000 });
      await candidate.click();
      await page.waitForTimeout(1500);
      return true;
    } catch (_) {
      // Keep trying.
    }
  }

  return false;
}

async function activateImageMode(page) {
  // Try clicking the "+" button first (current Gemini UI opens a menu)
  const plusCandidates = [
    page.locator('button[aria-label*="追加"], button[aria-label*="Add"], button[aria-label*="plus"]').first(),
    page.locator('button').filter({ hasText: "+" }).first(),
    page.locator('mat-icon').filter({ hasText: "add" }).locator("..").first(),
  ];
  for (const candidate of plusCandidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 3000 });
      await candidate.click();
      await page.waitForTimeout(1000);
      break;
    } catch (_) {
      // Keep trying.
    }
  }

  // After opening the menu (or without it), look for image generation option
  const imageCandidates = [
    page.getByText(/画像を生成|画像の作成|Create image|Generate image/i).first(),
    page.getByRole("button", { name: /画像を生成|画像の作成|Create image|Generate image|image/i }).first(),
    page.getByRole("menuitem", { name: /画像|image/i }).first(),
    page.locator('[role="menuitem"], [role="option"], div, button').filter({ hasText: /画像を生成|画像の作成|Create image/i }).first(),
  ];

  for (const candidate of imageCandidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 4000 });
      await candidate.click();
      await page.waitForTimeout(1200);
      return true;
    } catch (_) {
      // Keep trying.
    }
  }

  // If image mode button not found, press Escape to close any open menu and continue
  // Gemini may auto-detect image generation from the prompt
  await page.keyboard.press("Escape").catch(() => {});
  await page.waitForTimeout(500);
  return false;
}

async function uploadReference(page, referenceFile) {
  const resolvedFile = path.resolve(referenceFile);

  // Step 1: Click "アップロードとツール" button to open the menu
  const toolsBtn = page.locator('button[aria-label="アップロードとツール"]').first();
  await toolsBtn.waitFor({ state: "visible", timeout: 10000 });
  await toolsBtn.click();
  await page.waitForTimeout(1000);

  // Step 2: Click "ファイル" to open the native file chooser
  const chooserPromise = page.waitForEvent("filechooser", { timeout: 15000 });
  const fileBtn = page.getByRole("button", { name: "ファイル" }).first();
  await fileBtn.waitFor({ state: "visible", timeout: 5000 });
  await fileBtn.click();

  // Step 3: Handle the file chooser dialog
  const chooser = await chooserPromise;
  await chooser.setFiles(resolvedFile);
  await page.waitForTimeout(3000);
}

async function fillComposer(composer, prompt) {
  try {
    await composer.fill(prompt);
  } catch (_) {
    await composer.click();
    await composer.press("Control+A").catch(() => {});
    await composer.press("Meta+A").catch(() => {});
    await composer.press("Backspace").catch(() => {});
    await composer.type(prompt, { delay: 10 });
  }
}

async function clickGenerate(page, composer) {
  const buttonCandidates = [
    page.getByRole("button", { name: /send|submit|run|create|generate|送信|作成/i }).first(),
    page.locator('button[aria-label*="Send"], button[aria-label*="send"], button[aria-label*="送信"], button[aria-label*="作成"]').first(),
    page.locator('button[type="submit"]').first()
  ];

  for (const candidate of buttonCandidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 3000 });
      await candidate.click();
      return;
    } catch (_) {
      // Keep trying.
    }
  }

  await composer.press("Enter");
}

async function snapshotCurrentImages(page) {
  return await page.locator("img").evaluateAll((nodes) =>
    nodes
      .map((img) => ({
        src: img.currentSrc || img.src || "",
        width: img.naturalWidth || 0,
        height: img.naturalHeight || 0
      }))
      .filter((img) => img.src && img.width >= 512 && img.height >= 512)
      .map((img) => img.src)
  );
}

async function waitForGeneratedImage(page, timeoutMs, previousSources) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const found = await page.locator("img").evaluateAll((nodes, previous) => {
      const candidates = nodes
        .map((img, index) => ({
          index,
          src: img.currentSrc || img.src || "",
          width: img.naturalWidth || 0,
          height: img.naturalHeight || 0
        }))
        .filter((img) => img.src && img.width >= 512 && img.height >= 512 && !previous.includes(img.src));

      if (!candidates.length) {
        return null;
      }

      return candidates[candidates.length - 1];
    }, previousSources);

    if (found) {
      await page.waitForTimeout(1500);
      return found;
    }

    await page.waitForTimeout(2500);
  }

  throw new Error("Timed out waiting for generated images.");
}

async function saveLargestImage(page, outputFile, previousSources) {
  const target = await page.locator("img").evaluateAll((nodes, previous) => {
    const candidates = nodes
      .map((img, index) => ({
        index,
        src: img.currentSrc || img.src || "",
        width: img.naturalWidth || 0,
        height: img.naturalHeight || 0
      }))
      .filter((img) => img.width >= 512 && img.height >= 512 && !previous.includes(img.src));

    if (!candidates.length) {
      return null;
    }

    return candidates.sort((a, b) => (b.width * b.height) - (a.width * a.height))[0];
  }, previousSources);

  if (!target || !target.src) {
    throw new Error("No generated image could be extracted.");
  }

  let buffer = null;
  try {
    if (target.src.startsWith("data:image/")) {
      buffer = Buffer.from(target.src.split(",")[1], "base64");
    } else if (target.src.startsWith("blob:")) {
      const base64 = await page.evaluate(async (src) => {
        const response = await fetch(src);
        const blob = await response.blob();
        return await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = () => reject(new Error("Failed to read blob image."));
          reader.readAsDataURL(blob);
        });
      }, target.src);
      buffer = Buffer.from(base64, "base64");
    } else if (target.src.startsWith("http")) {
      const response = await page.request.get(target.src);
      if (response.ok()) {
        buffer = await response.body();
      }
    }
  } catch (_) {
    buffer = null;
  }

  fs.mkdirSync(path.dirname(outputFile), { recursive: true });
  if (buffer) {
    fs.writeFileSync(outputFile, buffer);
    return outputFile;
  }

  await page.locator("img").nth(target.index).screenshot({ path: outputFile });
  return outputFile;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const prompt = loadPrompt(args);
  if (!prompt) {
    throw new Error("No prompt was provided.");
  }
  if (!args.referenceFile) {
    throw new Error("No reference file was provided.");
  }
  if (!args.outputFile) {
    throw new Error("No output file was provided.");
  }

  const browser = await chromium.connectOverCDP(DEBUG_ENDPOINT);
  let page = null;
  try {
    const context = browser.contexts()[0];
    if (!context) {
      throw new Error("No browser context found at the debugging endpoint.");
    }

    page = await context.newPage();
    await page.goto(GEMINI_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await openNewChat(page);
    await activateImageMode(page);
    await uploadReference(page, args.referenceFile);
    const previousSources = await snapshotCurrentImages(page);
    const composer = await waitForComposer(page);
    await fillComposer(composer, prompt);
    await clickGenerate(page, composer);
    await waitForGeneratedImage(page, args.timeoutMs, previousSources);
    const savedPath = await saveLargestImage(page, path.resolve(args.outputFile), previousSources);
    console.log("Saved file:");
    console.log(savedPath);
  } finally {
    if (page) {
      await page.close().catch(() => {});
    }
    await browser.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
