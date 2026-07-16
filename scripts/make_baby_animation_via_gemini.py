from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
SETTING_SHEET = ROOT / "static" / "monsters" / "setting_picture" / "child.png"
MONSTER_DIR = ROOT / "static" / "monsters" / "baby" / "baby"
TMP_DIR = ROOT / ".gemini-output" / "baby_animation"
BABY_BOX = (500, 68, 658, 244)
DEBUG_ENDPOINT = "http://127.0.0.1:9222"

PROMPT = """Create one polished sprite sheet image for a children's web game character.

Reference image:
- use the attached baby monster as the exact base character identity
- preserve the same face feeling, body proportions, white jelly body, soft round shape, blush cheeks, and tiny cute charm

Layout:
- exactly 9 panels in a clean 3x3 grid
- equal spacing and equal panel sizes
- no text, no labels, no watermark
- pure white background only
- keep the full body visible in every panel
- keep the character centered and large inside each panel
- same art style and same proportions in every panel

Rows:
- row 1 = idle animation frames 1 to 3
- row 2 = eating animation frames 1 to 3
- row 3 = evolution animation frames 1 to 3

Animation direction:
- idle row: a waiting pose with gentle blinking, tiny bobbing, calm smile
- eating row: the character is happily chomping with a wide readable mouth; leave open space in front of the mouth so a separate food prop can be composited in front; do not draw any food object
- evolution row: the same baby monster glows brighter, slightly stretches upward, with sparkles and magical energy around the body

Style:
- premium Japanese casual mobile game illustration
- safe and cheerful for children ages 3 to 7
- soft shading
- crisp silhouette
- readable at small size

Output:
- output only the sprite sheet image""".strip()


def ensure_dirs() -> None:
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    MONSTER_DIR.mkdir(parents=True, exist_ok=True)
    for scene in ("idle", "eat", "evolve"):
        (MONSTER_DIR / scene).mkdir(parents=True, exist_ok=True)


def crop_baby_reference() -> Path:
    image = Image.open(SETTING_SHEET).convert("RGBA")
    crop = image.crop(BABY_BOX)
    out = TMP_DIR / "baby_reference.png"
    crop.save(out)
    return out


def run_gemini(reference_path: Path) -> Path:
    prompt_path = TMP_DIR / "baby_sheet_prompt.txt"
    prompt_path.write_text(PROMPT, encoding="utf-8")
    output_path = TMP_DIR / "baby_sheet.png"
    cmd = [
        "node",
        str(ROOT / "scripts" / "gemini_attach_with_reference.js"),
        "--prompt-file",
        str(prompt_path),
        "--reference-file",
        str(reference_path),
        "--output-file",
        str(output_path),
        "--timeout-ms",
        "480000",
    ]
    subprocess.run(cmd, cwd=ROOT, check=True)
    return output_path


def crop_frames(sheet_path: Path) -> list[Path]:
    image = Image.open(sheet_path).convert("RGBA")
    width, height = image.size
    cell_w = width // 3
    cell_h = height // 3
    saved: list[Path] = []
    scenes = ["idle", "eat", "evolve"]
    for row, scene in enumerate(scenes):
        for col in range(3):
            left = col * cell_w
            top = row * cell_h
            right = width if col == 2 else (col + 1) * cell_w
            bottom = height if row == 2 else (row + 1) * cell_h
            frame = image.crop((left, top, right, bottom))
            out = MONSTER_DIR / scene / f"frame{col + 1}.png"
            frame.save(out)
            saved.append(out)
    portrait = image.crop((0, 0, cell_w, cell_h))
    portrait.save(MONSTER_DIR / "portrait.png")
    return saved


def remove_background_via_web_service(frame_paths: list[Path]) -> None:
    # Web service assumption: remove.bg public upload flow.
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(DEBUG_ENDPOINT)
        context = browser.contexts[0]
        page = context.new_page()
        try:
            for frame_path in frame_paths:
                page.goto("https://www.remove.bg/upload", wait_until="domcontentloaded")
                page.wait_for_timeout(4000)

                file_input = page.locator('input[type="file"]').first
                file_input.set_input_files(str(frame_path))

                page.wait_for_timeout(12000)

                download_button = page.get_by_role("link", name="Download").first
                if download_button.count() == 0:
                    download_button = page.get_by_role("button", name="Download").first
                if download_button.count() == 0:
                    raise RuntimeError(f"remove.bg download button not found for {frame_path.name}")

                with page.expect_download(timeout=60000) as download_info:
                    download_button.click()
                download = download_info.value
                tmp_download = TMP_DIR / f"{frame_path.stem}_transparent.png"
                download.save_as(str(tmp_download))
                Image.open(tmp_download).convert("RGBA").save(frame_path)
                page.wait_for_timeout(1500)
        finally:
            page.close()
            browser.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-gemini", action="store_true")
    args = parser.parse_args()

    ensure_dirs()
    reference_path = crop_baby_reference()
    if args.skip_gemini:
        sheet_path = TMP_DIR / "baby_sheet.png"
    else:
        sheet_path = run_gemini(reference_path)
    frame_paths = crop_frames(sheet_path)
    remove_background_via_web_service(frame_paths)
    manifest = {
        "reference": str(reference_path),
        "sheet": str(sheet_path),
        "frames": [str(path) for path in frame_paths],
    }
    (TMP_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("finished baby animation pipeline")


if __name__ == "__main__":
    main()
