from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MONSTER_DIR = ROOT / "static" / "monsters"


def defringe_image(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]

            if a <= 96 and r >= 230 and g >= 230 and b >= 230:
                pixels[x, y] = (0, 0, 0, 0)
            elif a <= 140 and r >= 240 and g >= 240 and b >= 240:
                pixels[x, y] = (r, g, b, max(0, a - 80))

    image.save(path)


def main() -> None:
    for path in sorted(MONSTER_DIR.glob("**/*.png")):
        defringe_image(path)
        print(f"defringed {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
