from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from PIL import Image


SCENES = ("idle", "eat", "evolve")
REMOVE_CHROMA = Path.home() / ".codex" / "skills" / ".system" / "imagegen" / "scripts" / "remove_chroma_key.py"


def split_sheet(sheet_path: Path, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    image = Image.open(sheet_path).convert("RGBA")
    width, height = image.size
    cell_w = width // 3
    cell_h = height // 3
    saved: list[Path] = []
    for row, scene in enumerate(SCENES):
        scene_dir = outdir / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for col in range(3):
            left = col * cell_w
            top = row * cell_h
            right = width if col == 2 else (col + 1) * cell_w
            bottom = height if row == 2 else (row + 1) * cell_h
            frame = image.crop((left, top, right, bottom))
            frame_path = scene_dir / f"frame{col + 1}.png"
            frame.save(frame_path)
            saved.append(frame_path)
    shutil.copy2(outdir / "idle" / "frame1.png", outdir / "portrait.png")
    return saved + [outdir / "portrait.png"]


def remove_background(paths: list[Path], *, mode: str = "standard", despill: bool = True) -> None:
    for path in paths:
        if mode == "standard":
            command = [
                sys.executable,
                str(REMOVE_CHROMA),
                "--input",
                str(path),
                "--out",
                str(temp_path := path.with_name(f"{path.stem}.transparent.png")),
                "--auto-key",
                "border",
                "--soft-matte",
                "--transparent-threshold",
                "12",
                "--opaque-threshold",
                "220",
            ]
            if despill:
                command.append("--despill")
            subprocess.run(command, check=True)
            temp_path.replace(path)
            continue

        if mode == "green-diff-merge":
            with TemporaryDirectory() as tmpdir:
                temp_path = Path(tmpdir) / "standard.png"
                diff_path = Path(tmpdir) / "green_diff.png"
                command = [
                    sys.executable,
                    str(REMOVE_CHROMA),
                    "--input",
                    str(path),
                    "--out",
                    str(temp_path),
                    "--auto-key",
                    "border",
                    "--soft-matte",
                    "--transparent-threshold",
                    "12",
                    "--opaque-threshold",
                    "220",
                ]
                if despill:
                    command.append("--despill")
                subprocess.run(
                    command,
                    check=True,
                )
                remove_background_green_diff(path, diff_path)
                base = Image.open(temp_path).convert("RGBA")
                extra = Image.open(diff_path).convert("RGBA")
                base_px = base.load()
                extra_px = extra.load()
                for y in range(base.height):
                    for x in range(base.width):
                        _, _, _, base_alpha = base_px[x, y]
                        er, eg, eb, extra_alpha = extra_px[x, y]
                        # Restore pale translucent parts that the standard chroma key
                        # tends to punch holes through, such as soft wings, fins, and glow.
                        if base_alpha < 180 and extra_alpha > 80:
                            base_px[x, y] = (er, eg, eb, extra_alpha)
                base.save(path)
            continue

        raise ValueError(f"Unknown remove mode: {mode}")


def keep_largest_alpha_component(path: Path, *, alpha_threshold: int = 24) -> None:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    width, height = image.size
    pixels = alpha.load()
    visited: set[tuple[int, int]] = set()
    best: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in visited or pixels[x, y] < alpha_threshold:
                continue
            stack = [(x, y)]
            component: list[tuple[int, int]] = []
            visited.add((x, y))
            while stack:
                cx, cy = stack.pop()
                component.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in visited and pixels[nx, ny] >= alpha_threshold:
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            if len(component) > len(best):
                best = component

    if not best:
        return

    keep = set(best)
    rgba = image.load()
    for y in range(height):
        for x in range(width):
            if (x, y) not in keep:
                rgba[x, y] = (rgba[x, y][0], rgba[x, y][1], rgba[x, y][2], 0)
    image.save(path)


def refit_content_with_padding(path: Path, *, min_padding: int = 24) -> None:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return

    left, top, right, bottom = bbox
    width, height = image.size
    margins = (left, top, width - right, height - bottom)
    if all(margin >= min_padding for margin in margins):
        return

    content = image.crop(bbox)
    content_w, content_h = content.size
    max_w = max(1, width - min_padding * 2)
    max_h = max(1, height - min_padding * 2)
    scale = min(max_w / content_w, max_h / content_h, 1.0)
    if scale < 1.0:
        resized = content.resize((max(1, round(content_w * scale)), max(1, round(content_h * scale))), Image.LANCZOS)
    else:
        resized = content

    canvas = Image.new("RGBA", image.size, (0, 0, 0, 0))
    paste_x = (width - resized.width) // 2
    paste_y = (height - resized.height) // 2
    canvas.alpha_composite(resized, (paste_x, paste_y))
    canvas.save(path)


def remove_background_green_diff(input_path: Path, output_path: Path, *, low: int = 20, high: int = 100) -> None:
    image = Image.open(input_path).convert("RGBA")
    out = Image.new("RGBA", image.size)
    src = image.load()
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
    out.save(output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a 3x3 animation sheet and remove chroma background.")
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    parser.add_argument("--min-padding", type=int, default=24)
    parser.add_argument("--remove-mode", choices=("standard", "green-diff-merge"), default="standard")
    parser.add_argument("--no-despill", action="store_true")
    parser.add_argument("--skip-largest-component", action="store_true")
    args = parser.parse_args()

    sheet_target = args.outdir / "sheet.png"
    args.outdir.mkdir(parents=True, exist_ok=True)
    if args.sheet.resolve() != sheet_target.resolve():
        shutil.copy2(args.sheet, sheet_target)
    outputs = split_sheet(sheet_target, args.outdir)
    remove_background(outputs, mode=args.remove_mode, despill=not args.no_despill)
    for output in outputs:
        if not args.skip_largest_component:
            keep_largest_alpha_component(output)
        refit_content_with_padding(output, min_padding=args.min_padding)


if __name__ == "__main__":
    main()
