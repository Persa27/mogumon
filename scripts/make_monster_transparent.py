from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MONSTER_DIR = ROOT / "static" / "monsters"


def convert_image(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]
            if r >= 248 and g >= 248 and b >= 248:
                distance = 255 - min(r, g, b)
                alpha = max(0, min(255, distance * 32))
                pixels[x, y] = (r, g, b, alpha)

    image.save(path)


def main() -> None:
    for path in sorted(MONSTER_DIR.glob("**/*.png")):
        convert_image(path)
        print(f"updated {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
