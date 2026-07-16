import argparse
import itertools
from pathlib import Path

from PIL import Image

from crop_selected_columns_sheet import expanded_crop_box, isolate_largest_component, pad_to_square


def frame_from_cell(image: Image.Image, total_columns: int, row: int, col: int) -> Image.Image:
    width, height = image.size
    cell_width = width // total_columns
    cell_height = height // 3
    left = col * cell_width
    top = row * cell_height
    right = width if col == total_columns - 1 else (col + 1) * cell_width
    bottom = height if row == 2 else (row + 1) * cell_height
    box = expanded_crop_box(width, height, left, top, right, bottom, cell_width, cell_height)
    return pad_to_square(isolate_largest_component(image.crop(box)))


def frame_score(frame: Image.Image) -> float:
    alpha = frame.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return -10_000
    left, top, right, bottom = bbox
    width, height = frame.size
    margins = [left, top, width - right, height - bottom]
    min_margin = min(margins)
    area = (right - left) * (bottom - top)
    # Prefer non-clipped subjects with reasonable size and centered margins.
    score = area / 1000.0 + sum(margins) * 0.5
    if min_margin <= 1:
        score -= 10_000
    elif min_margin <= 4:
        score -= 2_000
    return score


def best_columns(image: Image.Image, total_columns: int, row: int) -> list[int]:
    candidates = list(itertools.combinations(range(total_columns), 3))
    best = None
    best_score = -10_000_000
    for combo in candidates:
        frames = [frame_from_cell(image, total_columns, row, col) for col in combo]
        score = sum(frame_score(frame) for frame in frames)
        # Prefer ordered spread when tied.
        score += (combo[-1] - combo[0]) * 0.1
        if score > best_score:
            best_score = score
            best = list(combo)
    assert best is not None
    return best


def crop_sheet(source: Path, target_dir: Path) -> None:
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    total_columns = 3 if height >= 900 else 5

    rows = ["idle", "eat", "evolve"]
    selections = {scene: best_columns(image, total_columns, row) for row, scene in enumerate(rows)}

    for row, scene in enumerate(rows):
        scene_dir = target_dir / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for out_index, col in enumerate(selections[scene], 1):
            frame = frame_from_cell(image, total_columns, row, col)
            frame.save(scene_dir / f"frame{out_index}.png")

    portrait_col = selections["idle"][0]
    portrait = frame_from_cell(image, total_columns, 0, portrait_col)
    portrait.save(target_dir / "portrait.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    crop_sheet(Path(args.source).resolve(), Path(args.target).resolve())


if __name__ == "__main__":
    main()
