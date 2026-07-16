import argparse
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
TARGET_DIR = ROOT / "static" / "monsters"
MONSTERS = ["momo", "pafu", "gabu", "fuwa"]
SCENES = ["idle", "eat", "evolve"]


def crop_sheet(source_dir: Path, monster: str) -> None:
    source = source_dir / f"{monster}-sheet.png"
    image = Image.open(source).convert("RGBA")
    width, height = image.size
    cell_width = width // 3
    cell_height = height // 3

    for row, scene in enumerate(SCENES):
        scene_dir = TARGET_DIR / monster / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for col in range(3):
            left = col * cell_width
            top = row * cell_height
            right = width if col == 2 else (col + 1) * cell_width
            bottom = height if row == 2 else (row + 1) * cell_height
            frame = image.crop((left, top, right, bottom))
            frame.save(scene_dir / f"frame{col + 1}.png")

    portrait = image.crop((0, 0, cell_width, cell_height))
    portrait.save(TARGET_DIR / monster / "portrait.png")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", default=str(ROOT / ".gemini-output" / "raw"))
    args = parser.parse_args()
    source_dir = Path(args.source_dir).resolve()

    for monster in MONSTERS:
        crop_sheet(source_dir, monster)
        print(f"cropped {monster}")


if __name__ == "__main__":
    main()
