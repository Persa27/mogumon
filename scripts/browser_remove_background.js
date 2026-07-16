const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const DEBUG_ENDPOINT = "http://127.0.0.1:9222";
const TOOL_URL = "https://www.remove.live/";

function parseArgs(argv) {
  const args = {
    input: "",
    output: "",
    timeoutMs: 240000
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--input") {
      args.input = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--output") {
      args.output = argv[i + 1] || "";
      i += 1;
    } else if (arg === "--timeout-ms") {
      args.timeoutMs = Number(argv[i + 1] || args.timeoutMs);
      i += 1;
    }
  }

  return args;
}

async function waitForProcessedImage(page, timeoutMs) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    const imageData = await page.evaluate(() => {
      const images = Array.from(document.images)
        .map((img) => ({
          src: img.currentSrc || img.src || "",
          width: img.naturalWidth || 0,
          height: img.naturalHeight || 0
        }))
        .filter((img) => img.width >= 512 && img.height >= 256);

      const best = images.find((img) => img.src.startsWith("data:image/")) || null;
      return best;
    });

    if (imageData) {
      return imageData;
    }
    await page.waitForTimeout(1500);
  }

  throw new Error("Processed image did not appear.");
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.input || !args.output) {
    throw new Error("Usage: node scripts/browser_remove_background.js --input <file> --output <file>");
  }

  const inputPath = path.resolve(args.input);
  const outputPath = path.resolve(args.output);

  const browser = await chromium.connectOverCDP(DEBUG_ENDPOINT);
  let page = null;
  try {
    const context = browser.contexts()[0];
    if (!context) {
      throw new Error("No browser context found.");
    }

    page = await context.newPage();
    await page.goto(TOOL_URL, { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(2000);

    const fileInput = page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(inputPath);

    const processedImage = await waitForProcessedImage(page, args.timeoutMs);
    const base64 = processedImage.src.split(",")[1];
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
    fs.writeFileSync(outputPath, Buffer.from(base64, "base64"));

    console.log(outputPath);
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
