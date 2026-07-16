from pathlib import Path

from PIL import Image


TARGETS = [
    Path("public/static/monsters/momo/eat/frame2.png"),
    Path("public/static/monsters/momo/eat/frame3.png"),
    Path("public/static/monsters/momo/evolve/frame2.png"),
    Path("public/static/monsters/momo/idle/frame2.png"),
]


def clear_outer_border(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size

    for x in range(width):
        for y in (0, height - 1):
            r, g, b, a = pixels[x, y]
            if a < 250:
                pixels[x, y] = (0, 0, 0, 0)

    for y in range(height):
        for x in (0, width - 1):
            r, g, b, a = pixels[x, y]
            if a < 250:
                pixels[x, y] = (0, 0, 0, 0)

    image.save(path)


def main() -> None:
    for path in TARGETS:
        clear_outer_border(path)
        print(f"cleaned {path}")


if __name__ == "__main__":
    main()
