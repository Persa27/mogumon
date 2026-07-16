import argparse
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


def crop_sheet(source: Path, target_dir: Path) -> None:
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    cell_width = width // 5
    cell_height = height // 3
    scenes = ["idle", "eat", "evolve"]
    selected_columns = {
        "idle": [0, 1, 3],
        "eat": [0, 2, 4],
        "evolve": [0, 2, 4],
    }

    for row, scene in enumerate(scenes):
        scene_dir = target_dir / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for out_index, col in enumerate(selected_columns[scene], 1):
            left = col * cell_width
            top = row * cell_height
            right = width if col == 4 else (col + 1) * cell_width
            bottom = height if row == 2 else (row + 1) * cell_height
            frame = isolate_largest_component(image.crop((left, top, right, bottom)))
            frame.save(scene_dir / f"frame{out_index}.png")

    portrait = image.crop((0, 0, cell_width, cell_height))
    portrait.save(target_dir / "portrait.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    crop_sheet(Path(args.source).resolve(), Path(args.target).resolve())


if __name__ == "__main__":
    main()
