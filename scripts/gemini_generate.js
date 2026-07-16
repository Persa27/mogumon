const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = process.cwd();
const PROFILE_DIR = path.join(ROOT, ".gemini-profile");
const OUTPUT_DIR = path.join(ROOT, ".gemini-output");
const DEFAULT_PROMPT_PATH = path.join(ROOT, "docs", "ai-image-generation.md");
const GEMINI_URL = "https://gemini.google.com/app";

function parseArgs(argv) {
  const args = {
    openOnly: false,
    prompt: "",
    promptFile: "",
    outDir: OUTPUT_DIR,
    timeoutMs: 180000
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--open-only") {
      args.openOnly = true;
    } else if (arg === "--prompt") {
      args.prompt = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--prompt-file") {
      args.promptFile = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--out-dir") {
      args.outDir = argv[i + 1] || OUTPUT_DIR;
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
  const selectors = [
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
      // Try the next selector.
    }
  }

  throw new Error("Gemini input box was not found.");
}

async function fillComposer(composer, prompt) {
  try {
    await composer.fill(prompt);
    return;
  } catch (_) {
    await composer.press("Control+A").catch(() => {});
    await composer.press("Meta+A").catch(() => {});
    await composer.press("Backspace").catch(() => {});
    await composer.type(prompt, { delay: 10 });
  }
}

async function clickGenerate(page) {
  const buttonCandidates = [
    page.getByRole("button", { name: /send|submit|run|create|generate/i }).first(),
    page.locator('button[aria-label*="Send"], button[aria-label*="送信"]').first(),
    page.locator('button[type="submit"]').first()
  ];

  for (const candidate of buttonCandidates) {
    try {
      await candidate.waitFor({ state: "visible", timeout: 3000 });
      await candidate.click();
      return;
    } catch (_) {
      // Try the next selector.
    }
  }

  throw new Error("Gemini submit button was not found.");
}

async function waitForImages(page, timeoutMs) {
  const start = Date.now();

  while (Date.now() - start < timeoutMs) {
    const imageInfos = await page.locator("img").evaluateAll((nodes) =>
      nodes
        .map((img) => ({
          src: img.currentSrc || img.src || "",
          width: img.naturalWidth || 0,
          height: img.naturalHeight || 0,
          alt: img.alt || ""
        }))
        .filter((img) => img.src && img.width >= 256 && img.height >= 256)
    );

    if (imageInfos.length > 0) {
      return imageInfos;
    }

    await page.waitForTimeout(2500);
  }

  throw new Error("Timed out waiting for generated images.");
}

async function saveImages(page, imageInfos, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const pageRef = page;
  const saved = [];

  for (let i = 0; i < imageInfos.length; i += 1) {
    const info = imageInfos[i];
    const filePath = path.join(outDir, `gemini-image-${i + 1}.png`);

    if (info.src.startsWith("data:image/")) {
      const base64 = info.src.split(",")[1];
      fs.writeFileSync(filePath, Buffer.from(base64, "base64"));
      saved.push(filePath);
      continue;
    }

    if (info.src.startsWith("blob:")) {
      const base64 = await page.evaluate(async (src) => {
        const response = await fetch(src);
        const blob = await response.blob();
        return await new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onloadend = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = () => reject(new Error("Failed to read blob image."));
          reader.readAsDataURL(blob);
        });
      }, info.src);
      fs.writeFileSync(filePath, Buffer.from(base64, "base64"));
      saved.push(filePath);
      continue;
    }

    if (info.src.startsWith("http")) {
      const response = await pageRef.request.get(info.src);
      if (response.ok()) {
        fs.writeFileSync(filePath, await response.body());
        saved.push(filePath);
      }
    }
  }

  if (saved.length === 0) {
    const screenshotPath = path.join(outDir, "gemini-page-fallback.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });
    saved.push(screenshotPath);
  }

  return saved;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const prompt = loadPrompt(args);

  const context = await chromium.launchPersistentContext(PROFILE_DIR, {
    channel: "msedge",
    headless: false,
    viewport: { width: 1440, height: 1024 }
  });

  try {
    const page = context.pages()[0] || (await context.newPage());
    await page.goto(GEMINI_URL, { waitUntil: "domcontentloaded" });

    if (args.openOnly) {
      console.log("Gemini opened. Complete login in the browser window, then close it when done.");
      await page.waitForTimeout(args.timeoutMs);
      return;
    }

    if (!prompt) {
      throw new Error("No prompt was provided. Use --prompt, --prompt-file, or create docs/ai-image-generation.md.");
    }

    const composer = await waitForComposer(page);
    await composer.click();
    await fillComposer(composer, prompt);
    await clickGenerate(page);

    const imageInfos = await waitForImages(page, args.timeoutMs);
    const savedPaths = await saveImages(page, imageInfos, path.resolve(args.outDir));

    console.log("Saved files:");
    for (const filePath of savedPaths) {
      console.log(filePath);
    }
  } finally {
    await context.close();
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
