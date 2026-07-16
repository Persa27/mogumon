import json
from collections import deque
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
SETTING_DIR = ROOT / "static" / "monsters" / "setting_picture"
OUT_DIR = ROOT / "static" / "monsters"
FRAME_SIZE = 320


CHILD_SHEET_BOXES = {
    "baby": (500, 68, 658, 244),
    "draup": (6, 46, 172, 248),
    "garoron": (978, 52, 1175, 248),
    "fishul": (10, 442, 196, 632),
    "lumina": (510, 440, 656, 628),
    "kororon": (986, 452, 1172, 634),
}


CHARACTERS = [
    {"slug": "baby", "name": "プニュン", "stage": "baby", "sheet": "child.png", "kind": "child_box", "box_key": "baby"},
    {"slug": "draup", "name": "ドラップ", "stage": "child", "sheet": "child.png", "kind": "child_box", "box_key": "draup"},
    {"slug": "garoron", "name": "ガロロン", "stage": "child", "sheet": "child.png", "kind": "child_box", "box_key": "garoron"},
    {"slug": "fishul", "name": "フィシュル", "stage": "child", "sheet": "child.png", "kind": "child_box", "box_key": "fishul"},
    {"slug": "lumina", "name": "ルミナ", "stage": "child", "sheet": "child.png", "kind": "child_box", "box_key": "lumina"},
    {"slug": "kororon", "name": "コロロン", "stage": "child", "sheet": "child.png", "kind": "child_box", "box_key": "kororon"},
    {"slug": "flare_drag", "name": "フレアドラグ", "stage": "mature", "sheet": "draup_mature.png", "kind": "lineup", "index": 0},
    {"slug": "bolt_drag", "name": "ボルトドラグ", "stage": "mature", "sheet": "draup_mature.png", "kind": "lineup", "index": 1},
    {"slug": "frost_drag", "name": "フロストドラグ", "stage": "mature", "sheet": "draup_mature.png", "kind": "lineup", "index": 2},
    {"slug": "magma_rock", "name": "マグマロック", "stage": "mature", "sheet": "draup_mature.png", "kind": "lineup", "index": 3},
    {"slug": "shine_drag", "name": "シャインドラグ", "stage": "mature", "sheet": "draup_mature.png", "kind": "lineup", "index": 4},
    {"slug": "prometheus", "name": "プロメテウス", "stage": "final", "sheet": "draup_final.png", "kind": "lineup", "index": 0},
    {"slug": "indra_drag", "name": "インドラ・ドラグ", "stage": "final", "sheet": "draup_final.png", "kind": "lineup", "index": 1},
    {"slug": "agniva", "name": "アグニヴァ", "stage": "final", "sheet": "draup_final.png", "kind": "lineup", "index": 2},
    {"slug": "gaia_drag", "name": "ガイアドラグ", "stage": "final", "sheet": "draup_final.png", "kind": "lineup", "index": 3},
    {"slug": "sol_dragnir", "name": "ソル・ドラグニル", "stage": "final", "sheet": "draup_final.png", "kind": "lineup", "index": 4},
    {"slug": "burst_garo", "name": "バーストガロ", "stage": "mature", "sheet": "garoron_mature.png", "kind": "lineup", "index": 0},
    {"slug": "bolt_garo", "name": "ボルトガロ", "stage": "mature", "sheet": "garoron_mature.png", "kind": "lineup", "index": 1},
    {"slug": "aqua_garo", "name": "アクアガロ", "stage": "mature", "sheet": "garoron_mature.png", "kind": "lineup", "index": 2},
    {"slug": "terra_garo", "name": "テラガロ", "stage": "mature", "sheet": "garoron_mature.png", "kind": "lineup", "index": 3},
    {"slug": "holy_garo", "name": "ホーリーガロ", "stage": "mature", "sheet": "garoron_mature.png", "kind": "lineup", "index": 4},
    {"slug": "ifrit_leo", "name": "イフリート・レオ", "stage": "final", "sheet": "garoron_final.png", "kind": "lineup", "index": 0},
    {"slug": "raiden_volf", "name": "ライデンヴォルフ", "stage": "final", "sheet": "garoron_final.png", "kind": "lineup", "index": 1},
    {"slug": "kelpie_volt", "name": "ケルピーヴォルト", "stage": "final", "sheet": "garoron_final.png", "kind": "lineup", "index": 2},
    {"slug": "yggdra_beast", "name": "ユグドラビースト", "stage": "final", "sheet": "garoron_final.png", "kind": "lineup", "index": 3},
    {"slug": "sirius_star", "name": "シリウス・スター", "stage": "final", "sheet": "garoron_final.png", "kind": "lineup", "index": 4},
    {"slug": "steam_fin", "name": "スチームフィン", "stage": "mature", "sheet": "fishul_mature.png", "kind": "lineup", "index": 0},
    {"slug": "plasma_fin", "name": "プラズマフィン", "stage": "mature", "sheet": "fishul_mature.png", "kind": "lineup", "index": 1},
    {"slug": "glacies", "name": "グラキエス", "stage": "mature", "sheet": "fishul_mature.png", "kind": "lineup", "index": 2},
    {"slug": "coral_guard", "name": "コーラルガルド", "stage": "mature", "sheet": "fishul_mature.png", "kind": "lineup", "index": 3},
    {"slug": "angel_fin", "name": "エンゼルフィン", "stage": "mature", "sheet": "fishul_mature.png", "kind": "lineup", "index": 4},
    {"slug": "levia_burn", "name": "レヴィア・バーン", "stage": "final", "sheet": "fishul_final.png", "kind": "lineup", "index": 0},
    {"slug": "thunder_kaiser", "name": "サンダーカイザー", "stage": "final", "sheet": "fishul_final.png", "kind": "lineup", "index": 1},
    {"slug": "poseidram", "name": "ポセイドラム", "stage": "final", "sheet": "fishul_final.png", "kind": "lineup", "index": 2},
    {"slug": "okeanos", "name": "オケアノス", "stage": "final", "sheet": "fishul_final.png", "kind": "lineup", "index": 3},
    {"slug": "seraph_aqua", "name": "セラフィ・アクア", "stage": "final", "sheet": "fishul_final.png", "kind": "lineup", "index": 4},
    {"slug": "burn_golem", "name": "バーンゴレム", "stage": "mature", "sheet": "kororon_mature.png", "kind": "lineup", "index": 0},
    {"slug": "pulse_rock", "name": "パルスロック", "stage": "mature", "sheet": "kororon_mature.png", "kind": "lineup", "index": 1},
    {"slug": "splash_terra", "name": "スプラッシュテラ", "stage": "mature", "sheet": "kororon_mature.png", "kind": "lineup", "index": 2},
    {"slug": "forest_guard", "name": "フォレストガルド", "stage": "mature", "sheet": "kororon_mature.png", "kind": "lineup", "index": 3},
    {"slug": "rune_golem", "name": "ルーンゴーレム", "stage": "mature", "sheet": "kororon_mature.png", "kind": "lineup", "index": 4},
    {"slug": "titan_magma", "name": "タイタン・マグマ", "stage": "final", "sheet": "kororon_final.png", "kind": "lineup", "index": 0},
    {"slug": "thor_terra", "name": "トール・テラ", "stage": "final", "sheet": "kororon_final.png", "kind": "lineup", "index": 1},
    {"slug": "neptune_rock", "name": "ネプチュン・ロック", "stage": "final", "sheet": "kororon_final.png", "kind": "lineup", "index": 2},
    {"slug": "yggdrasil", "name": "ユグドラシル", "stage": "final", "sheet": "kororon_final.png", "kind": "lineup", "index": 3},
    {"slug": "chronos_terra", "name": "クロノス・テラ", "stage": "final", "sheet": "kororon_final.png", "kind": "lineup", "index": 4},
    {"slug": "flare_eterna", "name": "フレアエテルナ", "stage": "mature", "sheet": "lumina_mature.png", "kind": "lineup", "index": 0},
    {"slug": "bolt_eterna", "name": "ボルトエテルナ", "stage": "mature", "sheet": "lumina_mature.png", "kind": "lineup", "index": 1},
    {"slug": "crystal_eterna", "name": "クリスタルエテルナ", "stage": "mature", "sheet": "lumina_mature.png", "kind": "lineup", "index": 2},
    {"slug": "leaf_eterna", "name": "リーフエテルナ", "stage": "mature", "sheet": "lumina_mature.png", "kind": "lineup", "index": 3},
    {"slug": "eterna", "name": "エテルナ", "stage": "mature", "sheet": "lumina_mature.png", "kind": "lineup", "index": 4},
    {"slug": "phoenix", "name": "フェニックス", "stage": "final", "sheet": "lumina_final.png", "kind": "lineup", "index": 0},
    {"slug": "astral_rai", "name": "アストラル・ライ", "stage": "final", "sheet": "lumina_final.png", "kind": "lineup", "index": 1},
    {"slug": "diamond_halo", "name": "ダイアモンド・ハロー", "stage": "final", "sheet": "lumina_final.png", "kind": "lineup", "index": 2},
    {"slug": "eden_spirit", "name": "エデン・スピリット", "stage": "final", "sheet": "lumina_final.png", "kind": "lineup", "index": 3},
    {"slug": "zeus_omega", "name": "ゼウス・オメガ", "stage": "final", "sheet": "lumina_final.png", "kind": "lineup", "index": 4},
]


def remove_white_border_background(image: Image.Image, threshold: int = 242) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    pixels = rgba.load()
    visited = [[False] * width for _ in range(height)]
    queue = deque()

    def is_bg(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        return a > 0 and r >= threshold and g >= threshold and b >= threshold

    for x in range(width):
        queue.append((x, 0))
        queue.append((x, height - 1))
    for y in range(height):
        queue.append((0, y))
        queue.append((width - 1, y))

    while queue:
        x, y = queue.popleft()
        if not (0 <= x < width and 0 <= y < height) or visited[y][x]:
            continue
        visited[y][x] = True
        if not is_bg(x, y):
            continue
        pixels[x, y] = (255, 255, 255, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                queue.append((nx, ny))

    return rgba


def isolate_largest_component(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
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

    cleaned = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    for x, y in best_pixels:
        cleaned.putpixel((x, y), rgba.getpixel((x, y)))
    return cleaned


def trim_image(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def extract_from_lineup(sheet_path: Path, index: int) -> Image.Image:
    image = Image.open(sheet_path).convert("RGBA")
    width, height = image.size
    col_width = width // 5
    left = index * col_width
    right = width if index == 4 else (index + 1) * col_width
    bottom = int(height * (0.78 if height < 400 else 0.82))
    crop = image.crop((left, 0, right, bottom))
    crop = remove_white_border_background(crop)
    crop = isolate_largest_component(crop)
    return trim_image(crop)


def extract_from_child(sheet_path: Path, box_key: str) -> Image.Image:
    image = Image.open(sheet_path).convert("RGBA")
    crop = image.crop(CHILD_SHEET_BOXES[box_key])
    crop = remove_white_border_background(crop)
    crop = isolate_largest_component(crop)
    return trim_image(crop)


def dominant_color(image: Image.Image) -> tuple[int, int, int]:
    rgba = image.convert("RGBA")
    small = rgba.resize((64, 64))
    total = [0, 0, 0]
    count = 0
    for r, g, b, a in small.getdata():
        if a < 32:
            continue
        if r > 245 and g > 245 and b > 245:
            continue
        total[0] += r
        total[1] += g
        total[2] += b
        count += 1
    if count == 0:
        return (180, 220, 255)
    return (total[0] // count, total[1] // count, total[2] // count)


def place_subject(subject: Image.Image, size: int, scale: float = 1.0, offset=(0, 0), rotate: float = 0.0) -> tuple[Image.Image, tuple[int, int, int, int]]:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bbox = subject.getbbox()
    if not bbox:
        return canvas, (0, 0, 0, 0)
    trimmed = subject.crop(bbox)
    target_h = int(size * 0.62 * scale)
    ratio = target_h / trimmed.height
    target_w = max(1, int(trimmed.width * ratio))
    resized = trimmed.resize((target_w, target_h), Image.Resampling.LANCZOS)
    if rotate:
        resized = resized.rotate(rotate, expand=True, resample=Image.Resampling.BICUBIC)
    x = (size - resized.width) // 2 + offset[0]
    y = int(size * 0.18) + offset[1]
    canvas.alpha_composite(resized, (x, y))
    return canvas, (x, y, x + resized.width, y + resized.height)


def draw_soft_shadow(draw: ImageDraw.ImageDraw, bbox: tuple[int, int, int, int], size: int) -> None:
    left, _, right, bottom = bbox
    if right <= left:
        return
    shadow_y = min(size - 22, bottom + 8)
    draw.ellipse((left + 12, shadow_y - 10, right - 12, shadow_y + 10), fill=(0, 0, 0, 28))


def add_eat_overlay(image: Image.Image, bbox: tuple[int, int, int, int]) -> None:
    left, top, right, bottom = bbox
    if right <= left:
        return
    draw = ImageDraw.Draw(image, "RGBA")
    cx = (left + right) // 2
    mouth_y = top + int((bottom - top) * 0.58)
    cheek_y = top + int((bottom - top) * 0.52)
    cheek_dx = max(12, (right - left) // 7)
    draw.ellipse((cx - 16, mouth_y - 5, cx + 16, mouth_y + 11), fill=(70, 25, 35, 150))
    draw.ellipse((cx - cheek_dx - 10, cheek_y - 6, cx - cheek_dx + 8, cheek_y + 8), fill=(255, 170, 190, 88))
    draw.ellipse((cx + cheek_dx - 8, cheek_y - 6, cx + cheek_dx + 10, cheek_y + 8), fill=(255, 170, 190, 88))
    for dx in (-28, 28):
        draw.arc((cx + dx - 10, mouth_y - 26, cx + dx + 10, mouth_y - 6), 210, 330, fill=(90, 90, 90, 110), width=2)


def add_evolve_overlay(image: Image.Image, bbox: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    left, top, right, bottom = bbox
    if right <= left:
        return
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    r, g, b = accent
    radius = max(right - left, bottom - top) // 2 + 24
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=(r, g, b, 130), width=5)
    draw.ellipse((cx - radius - 12, cy - radius - 12, cx + radius + 12, cy + radius + 12), outline=(255, 255, 255, 90), width=3)
    sparkles = [
        (cx - radius + 18, cy - 18),
        (cx + radius - 18, cy - 12),
        (cx - 8, cy - radius + 16),
        (cx + 8, cy + radius - 16),
    ]
    for sx, sy in sparkles:
        draw.line((sx - 7, sy, sx + 7, sy), fill=(255, 255, 255, 150), width=2)
        draw.line((sx, sy - 7, sx, sy + 7), fill=(255, 255, 255, 150), width=2)
    blurred = overlay.filter(ImageFilter.GaussianBlur(4))
    image.alpha_composite(blurred)
    image.alpha_composite(overlay)


def add_idle_highlight(image: Image.Image, bbox: tuple[int, int, int, int], accent: tuple[int, int, int]) -> None:
    left, top, right, bottom = bbox
    if right <= left:
        return
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, "RGBA")
    cx = (left + right) // 2
    top_y = top - 8
    r, g, b = accent
    for dx in (-26, 0, 26):
        draw.ellipse((cx + dx - 4, top_y - 4, cx + dx + 4, top_y + 4), fill=(r, g, b, 120))
    image.alpha_composite(overlay)


def make_frame(subject: Image.Image, scene: str, frame: int, accent: tuple[int, int, int]) -> Image.Image:
    size = FRAME_SIZE
    configs = {
        "idle": [
            {"scale": 1.00, "offset": (0, 0), "rotate": 0},
            {"scale": 1.03, "offset": (0, -6), "rotate": -2},
            {"scale": 0.99, "offset": (0, 2), "rotate": 1},
        ],
        "eat": [
            {"scale": 1.00, "offset": (-4, 0), "rotate": -4},
            {"scale": 0.98, "offset": (0, 3), "rotate": 4},
            {"scale": 1.02, "offset": (4, -1), "rotate": -2},
        ],
        "evolve": [
            {"scale": 1.00, "offset": (0, 0), "rotate": 0},
            {"scale": 1.07, "offset": (0, -6), "rotate": -2},
            {"scale": 1.12, "offset": (0, -10), "rotate": 2},
        ],
    }
    config = configs[scene][frame - 1]
    image, bbox = place_subject(subject, size, config["scale"], config["offset"], config["rotate"])
    draw = ImageDraw.Draw(image, "RGBA")
    draw_soft_shadow(draw, bbox, size)
    if scene == "idle":
        add_idle_highlight(image, bbox, accent)
    elif scene == "eat":
        add_eat_overlay(image, bbox)
    elif scene == "evolve":
        add_evolve_overlay(image, bbox, accent)
    return image


def subject_for_entry(entry: dict) -> Image.Image:
    sheet = SETTING_DIR / entry["sheet"]
    if entry["kind"] == "child_box":
        return extract_from_child(sheet, entry["box_key"])
    return extract_from_lineup(sheet, entry["index"])


def write_assets(entry: dict) -> None:
    subject = subject_for_entry(entry)
    accent = dominant_color(subject)
    target = OUT_DIR / entry["stage"] / entry["slug"]
    for scene in ("idle", "eat", "evolve"):
        scene_dir = target / scene
        scene_dir.mkdir(parents=True, exist_ok=True)
        for frame in (1, 2, 3):
            make_frame(subject, scene, frame, accent).save(scene_dir / f"frame{frame}.png")
    make_frame(subject, "idle", 1, accent).save(target / "portrait.png")


def main() -> None:
    manifest = []
    for entry in CHARACTERS:
        write_assets(entry)
        item = {k: v for k, v in entry.items() if k not in {"kind", "box_key", "index"}}
        item["asset_dir"] = f"{entry['stage']}/{entry['slug']}"
        manifest.append(item)
        print(f"generated {entry['slug']}")
    (OUT_DIR / "generated_character_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
