import argparse
import json
from collections import deque
from pathlib import Path

from PIL import Image


def isolate_largest_component(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    width, height = rgba.size
    alpha = rgba.getchannel("A")
    visited = [[False] * width for _ in range(height)]
    best_pixels = []

    for y in range(height):
        for x in range(width):
            if visited[y][x] or alpha.getpixel((x, y)) == 0:
                continue
            queue = deque([(x, y)])
            visited[y][x] = True
            pixels = []
            while queue:
                cx, cy = queue.popleft()
                pixels.append((cx, cy))
                for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                    if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx] and alpha.getpixel((nx, ny)) > 0:
                        visited[ny][nx] = True
                        queue.append((nx, ny))
            if len(pixels) > len(best_pixels):
                best_pixels = pixels

    if not best_pixels:
        return rgba

    cleaned = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    for x, y in best_pixels:
        cleaned.putpixel((x, y), rgba.getpixel((x, y)))
    return cleaned


def pad_to_square(frame: Image.Image) -> Image.Image:
    rgba = frame.convert("RGBA")
    width, height = rgba.size
    size = max(width, height)
    padded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    offset_x = (size - width) // 2
    offset_y = (size - height) // 2
    padded.paste(rgba, (offset_x, offset_y))
    return padded


def expanded_crop_box(
    width: int,
    height: int,
    left: int,
    top: int,
    right: int,
    bottom: int,
    cell_width: int,
    cell_height: int,
) -> tuple[int, int, int, int]:
    expand_x = max(8, cell_width // 8)
    expand_y = max(8, cell_height // 8)
    return (
        max(0, left - expand_x),
        max(0, top - expand_y),
        min(width, right + expand_x),
        min(height, bottom + expand_y),
    )


def crop_sheet(source: Path, target_dir: Path, total_columns: int, selected_columns: dict[str, list[int]]) -> None:
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    cell_width = width // total_columns
    cell_height = height // 3
    scenes = ["idle", "eat", "evolve"]

    for row, scene in enumerate(scenes):
        scene_dir = target_dir / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for out_index, col in enumerate(selected_columns[scene], 1):
            left = col * cell_width
            top = row * cell_height
            right = width if col == total_columns - 1 else (col + 1) * cell_width
            bottom = height if row == 2 else (row + 1) * cell_height
            crop_box = expanded_crop_box(width, height, left, top, right, bottom, cell_width, cell_height)
            frame = pad_to_square(isolate_largest_component(image.crop(crop_box)))
            frame.save(scene_dir / f"frame{out_index}.png")

    portrait_col = selected_columns["idle"][0]
    portrait_left = portrait_col * cell_width
    portrait_right = width if portrait_col == total_columns - 1 else (portrait_col + 1) * cell_width
    portrait_box = expanded_crop_box(width, height, portrait_left, 0, portrait_right, cell_height, cell_width, cell_height)
    portrait = pad_to_square(isolate_largest_component(image.crop(portrait_box)))
    portrait.save(target_dir / "portrait.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--columns", required=True, type=int)
    parser.add_argument("--mapping", required=True, help='JSON like {"idle":[0,2,4],"eat":[0,1,2],"evolve":[0,2,4]}')
    args = parser.parse_args()
    mapping = json.loads(args.mapping)
    crop_sheet(Path(args.source).resolve(), Path(args.target).resolve(), args.columns, mapping)


if __name__ == "__main__":
    main()
