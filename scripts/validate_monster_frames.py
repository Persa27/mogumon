import argparse
from pathlib import Path

from PIL import Image


def analyze_image(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if not bbox:
        return {"path": str(path), "status": "empty"}
    left, top, right, bottom = bbox
    width, height = image.size
    margins = {
        "left": left,
        "top": top,
        "right": width - right,
        "bottom": height - bottom,
    }
    min_margin = min(margins.values())
    area = (right - left) * (bottom - top)
    issues = []
    if min_margin <= 1:
        issues.append("touching_edge")
    elif min_margin <= 4:
        issues.append("near_edge")
    if area < (width * height * 0.1):
        issues.append("too_small")
    return {
        "path": str(path),
        "status": "ok" if not issues else ",".join(issues),
        "margins": margins,
        "area": area,
        "size": f"{width}x{height}",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    root = Path(args.root)
    for path in sorted(root.rglob("*.png")):
        result = analyze_image(path)
        if result["status"] != "ok":
            print(result)


if __name__ == "__main__":
    main()
