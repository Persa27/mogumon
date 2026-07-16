const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const DEBUG_ENDPOINT = "http://127.0.0.1:9222";
const CHATGPT_URL = "https://chatgpt.com/";

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
  const selectors = [
    '#prompt-textarea',
    'textarea',
    '[contenteditable="true"]',
    '[role="textbox"]'
  ];

  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    try {
      await locator.waitFor({ state: "visible", timeout: 5000 });
      return locator;
    } catch (_) {
      // Try next selector.
    }
  }

  throw new Error("ChatGPT input box was not found.");
}

async function openNewChat(page) {
  const candidates = [
    page.getByRole("link", { name: /new chat/i }).first(),
    page.getByRole("button", { name: /new chat/i }).first(),
    page.locator('a[href="/"], a[href="/?model="]').first()
  ];

  for (const candidate of candidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 2500 });
      await candidate.click();
      await page.waitForTimeout(1200);
      return true;
    } catch (_) {
      // Keep trying.
    }
  }

  return false;
}

async function activateImageMode(page) {
  const candidates = [
    page.getByRole("button", { name: /画像を作成|create image/i }).first(),
    page.getByText(/画像を作成|create image/i).first(),
    page.locator('button[aria-label*="画像を作成"], button[aria-label*="Create image"]').first()
  ];

  for (const candidate of candidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 3000 });
      await candidate.click();
      await page.waitForTimeout(1200);
      return true;
    } catch (_) {
      // Try next.
    }
  }

  return false;
}

async function uploadReference(page, referenceFile) {
  const fileChooserPromise = page.waitForEvent("filechooser", { timeout: 5000 }).catch(() => null);
  const uploadButtonCandidates = [
    page.getByRole("button", { name: /attach|upload|plus/i }).first(),
    page.locator('button[aria-label*="Attach"], button[aria-label*="Upload"], button[aria-label*="添付"], button[aria-label*="アップロード"]').first(),
    page.locator('button svg').locator("xpath=..").first()
  ];

  for (const candidate of uploadButtonCandidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 2000 });
      await candidate.click();
      break;
    } catch (_) {
      // Try next.
    }
  }

  let chooser = await fileChooserPromise;
  if (chooser) {
    await chooser.setFiles(path.resolve(referenceFile));
    await page.waitForTimeout(2500);
    return;
  }

  const fileInput = page.locator('input[type="file"]').first();
  await fileInput.setInputFiles(path.resolve(referenceFile));
  await page.waitForTimeout(2500);
}

async function fillComposer(composer, prompt) {
  try {
    await composer.fill(prompt);
    return;
  } catch (_) {
    await composer.click();
    await composer.press("Control+A").catch(() => {});
    await composer.press("Meta+A").catch(() => {});
    await composer.press("Backspace").catch(() => {});
    await composer.type(prompt, { delay: 10 });
  }
}

async function submitPrompt(page, composer) {
  const candidates = [
    page.getByRole("button", { name: /send/i }).first(),
    page.locator('button[data-testid="send-button"]').first(),
    page.locator('button[aria-label*="Send"]').first()
  ];

  for (const candidate of candidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 2000 });
      await candidate.click();
      return;
    } catch (_) {
      // Try next.
    }
  }

  await composer.press("Enter");
}

async function snapshotCurrentImages(page) {
  return await page.locator("main img").evaluateAll((nodes) =>
    nodes
      .map((img) => ({
        src: img.currentSrc || img.src || "",
        width: img.naturalWidth || 0,
        height: img.naturalHeight || 0,
        alt: img.alt || ""
      }))
      .filter((img) => img.src && img.width >= 512 && img.height >= 512)
      .map((img) => img.src)
  );
}

async function waitForGeneratedImage(page, timeoutMs, previousSources) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const target = await page.locator("main img").evaluateAll((nodes, previous) => {
      const candidates = nodes
        .map((img, index) => ({
          index,
          src: img.currentSrc || img.src || "",
          width: img.naturalWidth || 0,
          height: img.naturalHeight || 0,
          alt: img.alt || ""
        }))
        .filter((img) =>
          img.src &&
          img.width >= 512 &&
          img.height >= 512 &&
          !/avatar|profile|icon|logo/i.test(img.alt || "") &&
          !previous.includes(img.src)
        );

      if (!candidates.length) {
        return null;
      }
      return candidates[candidates.length - 1];
    }, previousSources);

    if (target && target.src) {
      await page.waitForTimeout(1500);
      return target;
    }
    await page.waitForTimeout(2500);
  }

  throw new Error("Timed out waiting for generated images.");
}

async function saveImage(page, target, outputFile) {
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
    await page.goto(CHATGPT_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(3000);
    await openNewChat(page);
    await activateImageMode(page);
    const composer = await waitForComposer(page);
    await uploadReference(page, args.referenceFile);
    const previousSources = await snapshotCurrentImages(page);
    await fillComposer(composer, prompt);
    await submitPrompt(page, composer);
    const target = await waitForGeneratedImage(page, args.timeoutMs, previousSources);
    const savedPath = await saveImage(page, target, path.resolve(args.outputFile));
    console.log("Saved file:");
    console.log(savedPath);
  } catch (error) {
    if (page) {
      try {
        const debugPath = path.resolve(args.outputFile).replace(/\.png$/i, ".debug.png");
        fs.mkdirSync(path.dirname(debugPath), { recursive: true });
        await page.screenshot({ path: debugPath, fullPage: true });
        console.error(`Debug screenshot saved: ${debugPath}`);
      } catch (_) {
        // Ignore screenshot failures.
      }
    }
    throw error;
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
