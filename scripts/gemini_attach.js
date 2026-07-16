const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = process.cwd();
const OUTPUT_DIR = path.join(ROOT, ".gemini-output");
const DEFAULT_PROMPT_PATH = path.join(ROOT, "docs", "ai-image-generation.md");
const DEBUG_ENDPOINT = "http://127.0.0.1:9222";
const GEMINI_URL = "https://gemini.google.com/app";

function parseArgs(argv) {
  const args = {
    prompt: "",
    promptFile: "",
    outDir: OUTPUT_DIR,
    outputFile: "",
    timeoutMs: 240000
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--prompt") {
      args.prompt = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--prompt-file") {
      args.promptFile = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--out-dir") {
      args.outDir = argv[i + 1] || OUTPUT_DIR;
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
  if (fs.existsSync(DEFAULT_PROMPT_PATH)) {
    return fs.readFileSync(DEFAULT_PROMPT_PATH, "utf8").trim();
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
    page.locator('button[aria-label*="新しいチャット"]').first(),
    page.locator('button[aria-label*="New chat"]').first()
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
  const candidates = [
    page.getByRole("button", { name: /画像の作成|create image|image/i }).first(),
    page.locator('button[aria-label*="画像の作成"], button[aria-label*="Create image"], button[aria-label*="image"]').first(),
    page.locator('.card-zero-state').filter({ hasText: "画像の作成" }).first(),
    page.locator('[aria-label*="画像の作成"]').first()
  ];

  for (const candidate of candidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 4000 });
      await candidate.click();
      await page.waitForTimeout(1200);
      return true;
    } catch (_) {
      // Keep trying.
    }
  }

  // Gemini's home screen cards are sometimes rendered as non-button surfaces.
  // The viewport is stable in this workflow, so use a conservative coordinate fallback.
  try {
    await page.mouse.click(180, 330);
    await page.waitForTimeout(1500);
    return true;
  } catch (_) {
    // Ignore and fall through.
  }

  return false;
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

async function clickGenerate(page) {
  const buttonCandidates = [
    page.getByRole("button", { name: /send|submit|run|create|generate|送信|プロンプトを送信/i }).first(),
    page.locator('button[aria-label*="Send"], button[aria-label*="send"], button[aria-label*="送信"], button[aria-label*="プロンプトを送信"]').first(),
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

  throw new Error("Gemini submit button was not found.");
}

async function waitForGeneratedImage(page, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const found = await page.locator("img").evaluateAll((nodes) =>
      nodes.some((img) => (img.naturalWidth || 0) >= 512 && (img.naturalHeight || 0) >= 512)
    );
    if (found) {
      await page.waitForTimeout(1500);
      return;
    }
    await page.waitForTimeout(2500);
  }
  throw new Error("Timed out waiting for generated images.");
}

async function saveLargestImage(page, outputFile) {
  const target = await page.locator("img").evaluateAll((nodes) => {
    const candidates = nodes
      .map((img, index) => ({
        index,
        src: img.currentSrc || img.src || "",
        width: img.naturalWidth || 0,
        height: img.naturalHeight || 0
      }))
      .filter((img) => img.width >= 512 && img.height >= 512)
      .map((img) => ({
        index: img.index,
        src: img.src,
        width: img.width,
        height: img.height
      }));

    if (candidates.length === 0) {
      return null;
    }

    return candidates.sort((a, b) => (b.width * b.height) - (a.width * a.height))[0];
  });

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
      if (!response.ok()) {
        throw new Error("Failed to download generated image.");
      }
      buffer = await response.body();
    }
  } catch (_) {
    buffer = null;
  }

  if (!buffer) {
    fs.mkdirSync(path.dirname(outputFile), { recursive: true });
    await page.locator("img").nth(target.index).screenshot({ path: outputFile });
    return outputFile;
  }

  fs.mkdirSync(path.dirname(outputFile), { recursive: true });
  fs.writeFileSync(outputFile, buffer);
  return outputFile;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const prompt = loadPrompt(args);
  if (!prompt) {
    throw new Error("No prompt was provided. Use --prompt, --prompt-file, or create docs/ai-image-generation.md.");
  }

  const outputFile = args.outputFile
    ? path.resolve(args.outputFile)
    : path.resolve(args.outDir, "gemini-image.png");

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

    const composer = await waitForComposer(page);
    await fillComposer(composer, prompt);
    await clickGenerate(page);
    await waitForGeneratedImage(page, args.timeoutMs);

    const savedPath = await saveLargestImage(page, outputFile);
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
