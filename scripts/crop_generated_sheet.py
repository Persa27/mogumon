import argparse
from pathlib import Path

from PIL import Image


def crop_sheet(source: Path, target_dir: Path) -> None:
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    cell_width = width // 3
    cell_height = height // 3
    scenes = ["idle", "eat", "evolve"]

    for row, scene in enumerate(scenes):
        scene_dir = target_dir / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for col in range(3):
            left = col * cell_width
            top = row * cell_height
            right = width if col == 2 else (col + 1) * cell_width
            bottom = height if row == 2 else (row + 1) * cell_height
            frame = image.crop((left, top, right, bottom))
            frame.save(scene_dir / f"frame{col + 1}.png")

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
