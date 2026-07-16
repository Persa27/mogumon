from pathlib import Path

from PIL import Image


TARGETS = [
    Path("static/monsters/momo/eat/frame2.png"),
    Path("static/monsters/momo/eat/frame3.png"),
    Path("static/monsters/momo/evolve/frame2.png"),
]


def clean_image(path: Path) -> None:
    image = Image.open(path).convert("RGBA")
    pixels = image.load()
    width, height = image.size

    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]

            if a < 230 and r > 228 and g > 228 and b > 228:
                pixels[x, y] = (0, 0, 0, 0)
            elif a < 255 and r > 245 and g > 245 and b > 245:
                pixels[x, y] = (0, 0, 0, 0)

    for edge in range(3):
        for x in range(width):
            if pixels[x, edge][3] < 255:
                pixels[x, edge] = (0, 0, 0, 0)
            if pixels[x, height - 1 - edge][3] < 255:
                pixels[x, height - 1 - edge] = (0, 0, 0, 0)
        for y in range(height):
            if pixels[edge, y][3] < 255:
                pixels[edge, y] = (0, 0, 0, 0)
            if pixels[width - 1 - edge, y][3] < 255:
                pixels[width - 1 - edge, y] = (0, 0, 0, 0)

    image.save(path)


def main() -> None:
    for path in TARGETS:
        clean_image(path)
        print(f"cleaned {path}")


if __name__ == "__main__":
    main()
