"""
Rebuild garoron's gemini_reference.png from the new portrait.png.
Run this before using gemini_attach_with_reference.js.
"""
from collections import deque
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PORTRAIT_PATH = ROOT / "static" / "monsters" / "child" / "garoron" / "portrait.png"
BABY_SHEET_PATH = ROOT / "static" / "monsters" / "baby" / "baby" / "sheet.png"
OUT_PATH = ROOT / "static" / "monsters" / "child" / "garoron" / "gemini_reference.png"


def remove_green_background(image: Image.Image, low: int = 20, high: int = 100) -> Image.Image:
    out = Image.new("RGBA", image.size)
    src = image.convert("RGBA").load()
    dst = out.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, _ = src[x, y]
            score = g - max(r, b)
            if score <= low:
                alpha = 255
            elif score >= high:
                alpha = 0
            else:
                alpha = round(255 * (1 - (score - low) / (high - low)))
            dst[x, y] = (r, g, b, alpha)
    return out


def keep_largest_component(image: Image.Image, threshold: int = 24) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    alpha = rgba.getchannel("A")
    visited = set()
    best: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in visited or alpha.getpixel((x, y)) < threshold:
                continue
            queue = deque([(x, y)])
            visited.add((x, y))
            component: list[tuple[int, int]] = []
            while queue:
                cx, cy = queue.popleft()
                component.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited and alpha.getpixel((nx, ny)) >= threshold:
                        visited.add((nx, ny))
                        queue.append((nx, ny))
            if len(component) > len(best):
                best = component

    keep = set(best)
    px = rgba.load()
    for y in range(height):
        for x in range(width):
            if (x, y) not in keep:
                px[x, y] = (px[x, y][0], px[x, y][1], px[x, y][2], 0)
    return rgba


def add_padding(image: Image.Image, min_pad: int = 56) -> Image.Image:
    bbox = image.getbbox()
    if not bbox:
        return image
    trimmed = image.crop(bbox)
    pad = min_pad
    canvas = Image.new("RGBA", (trimmed.width + pad * 2, trimmed.height + pad * 2), (0, 0, 0, 0))
    canvas.alpha_composite(trimmed, (pad, pad))
    return canvas


def make_reference_canvas(subject: Image.Image, baby_sheet: Image.Image) -> Image.Image:
    canvas_w = 1800
    canvas_h = 1280
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

    scale_subject = min(440 / subject.width, 920 / subject.height)
    subject_r = subject.resize(
        (max(1, int(subject.width * scale_subject)), max(1, int(subject.height * scale_subject))),
        Image.LANCZOS,
    )

    scale_baby = min(1120 / baby_sheet.width, 1120 / baby_sheet.height)
    baby_r = baby_sheet.resize(
        (max(1, int(baby_sheet.width * scale_baby)), max(1, int(baby_sheet.height * scale_baby))),
        Image.LANCZOS,
    )

    canvas.alpha_composite(subject_r, (120, (canvas_h - subject_r.height) // 2))
    canvas.alpha_composite(baby_r, (620, (canvas_h - baby_r.height) // 2))
    return canvas


def main() -> None:
    print("Loading portrait...")
    portrait = Image.open(PORTRAIT_PATH)

    print("Removing green background...")
    transparent = remove_green_background(portrait)
    transparent = keep_largest_component(transparent)
    transparent = add_padding(transparent)

    print("Saving transparent portrait...")
    portrait_out = PORTRAIT_PATH.parent / "portrait.png"
    transparent.save(portrait_out)
    print(f"  -> {portrait_out}")

    print("Building gemini_reference.png...")
    baby_sheet = Image.open(BABY_SHEET_PATH).convert("RGBA")
    reference = make_reference_canvas(transparent, baby_sheet)
    reference.save(OUT_PATH)
    print(f"  -> {OUT_PATH}")

    print("Done. Next steps:")
    print("  1. Run Gemini: node scripts/gemini_attach_with_reference.js \\")
    print(f"       --reference-file {OUT_PATH} \\")
    print(f"       --prompt-file public/static/monsters/child/garoron/gemini_prompt.txt \\")
    print(f"       --output-file public/static/monsters/child/garoron/sheet.png")
    print("  2. Remove background: node scripts/browser_remove_background.js \\")
    print(f"       --input public/static/monsters/child/garoron/sheet.png \\")
    print(f"       --output public/static/monsters/child/garoron/sheet_transparent.png")
    print("  3. Split frames: python scripts/process_animation_sheet.py \\")
    print(f"       --sheet public/static/monsters/child/garoron/sheet_transparent.png \\")
    print(f"       --outdir public/static/monsters/child/garoron")


if __name__ == "__main__":
    main()
