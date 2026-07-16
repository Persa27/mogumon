from __future__ import annotations

from collections import deque
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SETTING_DIR = ROOT / "static" / "monsters" / "setting_picture"
MONSTERS_DIR = ROOT / "static" / "monsters"
BABY_SHEET = MONSTERS_DIR / "baby" / "baby" / "sheet.png"

CHILD_BOXES = {
    "baby": (500, 68, 658, 244),
    "draup": (6, 46, 172, 248),
    "garoron": (978, 52, 1175, 248),
    "fishul": (10, 442, 196, 632),
    "lumina": (510, 440, 656, 628),
    "kororon": (986, 452, 1172, 634),
}

CHARACTERS = [
    {"slug": "baby", "stage": "baby", "kind": "child", "box_key": "baby"},
    {"slug": "draup", "stage": "child", "kind": "child", "box_key": "draup"},
    {"slug": "garoron", "stage": "child", "kind": "child", "box_key": "garoron"},
    {"slug": "fishul", "stage": "child", "kind": "child", "box_key": "fishul"},
    {"slug": "lumina", "stage": "child", "kind": "child", "box_key": "lumina"},
    {"slug": "kororon", "stage": "child", "kind": "child", "box_key": "kororon"},
    {"slug": "flare_drag", "stage": "mature", "kind": "lineup", "sheet_id": "draup_mature", "index": 0},
    {"slug": "bolt_drag", "stage": "mature", "kind": "lineup", "sheet_id": "draup_mature", "index": 1},
    {"slug": "frost_drag", "stage": "mature", "kind": "lineup", "sheet_id": "draup_mature", "index": 2},
    {"slug": "magma_rock", "stage": "mature", "kind": "lineup", "sheet_id": "draup_mature", "index": 3},
    {"slug": "shine_drag", "stage": "mature", "kind": "lineup", "sheet_id": "draup_mature", "index": 4},
    {"slug": "prometheus", "stage": "final", "kind": "lineup", "sheet_id": "draup_final", "index": 0},
    {"slug": "indra_drag", "stage": "final", "kind": "lineup", "sheet_id": "draup_final", "index": 1},
    {"slug": "agniva", "stage": "final", "kind": "lineup", "sheet_id": "draup_final", "index": 2},
    {"slug": "gaia_drag", "stage": "final", "kind": "lineup", "sheet_id": "draup_final", "index": 3},
    {"slug": "sol_dragnir", "stage": "final", "kind": "lineup", "sheet_id": "draup_final", "index": 4},
    {"slug": "burst_garo", "stage": "mature", "kind": "lineup", "sheet_id": "garoron_mature", "index": 0},
    {"slug": "bolt_garo", "stage": "mature", "kind": "lineup", "sheet_id": "garoron_mature", "index": 1},
    {"slug": "aqua_garo", "stage": "mature", "kind": "lineup", "sheet_id": "garoron_mature", "index": 2},
    {"slug": "terra_garo", "stage": "mature", "kind": "lineup", "sheet_id": "garoron_mature", "index": 3},
    {"slug": "holy_garo", "stage": "mature", "kind": "lineup", "sheet_id": "garoron_mature", "index": 4},
    {"slug": "ifrit_leo", "stage": "final", "kind": "lineup", "sheet_id": "garoron_final", "index": 0},
    {"slug": "raiden_volf", "stage": "final", "kind": "lineup", "sheet_id": "garoron_final", "index": 1},
    {"slug": "kelpie_volt", "stage": "final", "kind": "lineup", "sheet_id": "garoron_final", "index": 2},
    {"slug": "yggdra_beast", "stage": "final", "kind": "lineup", "sheet_id": "garoron_final", "index": 3},
    {"slug": "sirius_star", "stage": "final", "kind": "lineup", "sheet_id": "garoron_final", "index": 4},
    {"slug": "steam_fin", "stage": "mature", "kind": "lineup", "sheet_id": "fishul_mature", "index": 0},
    {"slug": "plasma_fin", "stage": "mature", "kind": "lineup", "sheet_id": "fishul_mature", "index": 1},
    {"slug": "glacies", "stage": "mature", "kind": "lineup", "sheet_id": "fishul_mature", "index": 2},
    {"slug": "coral_guard", "stage": "mature", "kind": "lineup", "sheet_id": "fishul_mature", "index": 3},
    {"slug": "angel_fin", "stage": "mature", "kind": "lineup", "sheet_id": "fishul_mature", "index": 4},
    {"slug": "levia_burn", "stage": "final", "kind": "lineup", "sheet_id": "fishul_final", "index": 0},
    {"slug": "thunder_kaiser", "stage": "final", "kind": "lineup", "sheet_id": "fishul_final", "index": 1},
    {"slug": "poseidram", "stage": "final", "kind": "lineup", "sheet_id": "fishul_final", "index": 2},
    {"slug": "okeanos", "stage": "final", "kind": "lineup", "sheet_id": "fishul_final", "index": 3},
    {"slug": "seraph_aqua", "stage": "final", "kind": "lineup", "sheet_id": "fishul_final", "index": 4},
    {"slug": "burn_golem", "stage": "mature", "kind": "lineup", "sheet_id": "kororon_mature", "index": 0},
    {"slug": "pulse_rock", "stage": "mature", "kind": "lineup", "sheet_id": "kororon_mature", "index": 1},
    {"slug": "splash_terra", "stage": "mature", "kind": "lineup", "sheet_id": "kororon_mature", "index": 2},
    {"slug": "forest_guard", "stage": "mature", "kind": "lineup", "sheet_id": "kororon_mature", "index": 3},
    {"slug": "rune_golem", "stage": "mature", "kind": "lineup", "sheet_id": "kororon_mature", "index": 4},
    {"slug": "titan_magma", "stage": "final", "kind": "lineup", "sheet_id": "kororon_final", "index": 0},
    {"slug": "thor_terra", "stage": "final", "kind": "lineup", "sheet_id": "kororon_final", "index": 1},
    {"slug": "neptune_rock", "stage": "final", "kind": "lineup", "sheet_id": "kororon_final", "index": 2},
    {"slug": "yggdrasil", "stage": "final", "kind": "lineup", "sheet_id": "kororon_final", "index": 3},
    {"slug": "chronos_terra", "stage": "final", "kind": "lineup", "sheet_id": "kororon_final", "index": 4},
    {"slug": "flare_eterna", "stage": "mature", "kind": "lineup", "sheet_id": "lumina_mature", "index": 0},
    {"slug": "bolt_eterna", "stage": "mature", "kind": "lineup", "sheet_id": "lumina_mature", "index": 1},
    {"slug": "crystal_eterna", "stage": "mature", "kind": "lineup", "sheet_id": "lumina_mature", "index": 2},
    {"slug": "leaf_eterna", "stage": "mature", "kind": "lineup", "sheet_id": "lumina_mature", "index": 3},
    {"slug": "eterna", "stage": "mature", "kind": "lineup", "sheet_id": "lumina_mature", "index": 4},
    {"slug": "phoenix", "stage": "final", "kind": "lineup", "sheet_id": "lumina_final", "index": 0},
    {"slug": "astral_rai", "stage": "final", "kind": "lineup", "sheet_id": "lumina_final", "index": 1},
    {"slug": "diamond_halo", "stage": "final", "kind": "lineup", "sheet_id": "lumina_final", "index": 2},
    {"slug": "eden_spirit", "stage": "final", "kind": "lineup", "sheet_id": "lumina_final", "index": 3},
    {"slug": "zeus_omega", "stage": "final", "kind": "lineup", "sheet_id": "lumina_final", "index": 4},
]

STAGE_NOTES = {
    "baby": "Keep the monster tiny, simple, soft, and very childlike.",
    "child": "Keep the monster playful, young, friendly, and easy to read.",
    "mature": "Keep the monster clearly more developed and confident, but still cute and collectible.",
    "final": "Keep the monster clearly more majestic and powerful, but still cute and creature-like rather than humanoid.",
}

SUBJECT_BOX_OVERRIDES = {
    "sirius_star": (2110, 300, 2735, 1100),
    "thunder_kaiser": (112, 42, 208, 170),
    "pulse_rock": (108, 20, 196, 166),
}


def remove_white_border_background(image: Image.Image, threshold: int = 245) -> Image.Image:
    rgba = image.convert("RGBA")
    width, height = rgba.size
    px = rgba.load()
    visited = [[False] * width for _ in range(height)]
    queue = deque()

    def is_bg(x: int, y: int) -> bool:
        r, g, b, a = px[x, y]
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
        px[x, y] = (255, 255, 255, 0)
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < width and 0 <= ny < height and not visited[ny][nx]:
                queue.append((nx, ny))

    return rgba


def trim_image(image: Image.Image) -> Image.Image:
    bbox = image.getbbox()
    return image.crop(bbox) if bbox else image


def add_safe_padding(image: Image.Image, min_pad: int = 56, ratio: float = 0.18) -> Image.Image:
    width, height = image.size
    pad_x = max(min_pad, int(width * ratio))
    pad_y = max(min_pad, int(height * ratio))
    padded = Image.new("RGBA", (width + pad_x * 2, height + pad_y * 2), (0, 0, 0, 0))
    padded.alpha_composite(image, (pad_x, pad_y))
    return padded


def find_lineup_boxes(sheet_path: Path) -> list[tuple[int, int, int, int]]:
    image = Image.open(sheet_path).convert("RGB")
    width, height = image.size
    # Search almost the full character area so tall horns/wings at the top are preserved,
    # but stop before the lower label band.
    y_min = max(0, int(height * 0.12))
    y_max = int(height * 0.82)
    counts = [0] * width
    pixel_rows: list[list[int]] = [[] for _ in range(width)]

    for x in range(width):
        for y in range(y_min, y_max):
            r, g, b = image.getpixel((x, y))
            if min(r, g, b) >= 245:
                continue
            counts[x] += 1
            pixel_rows[x].append(y)

    occupied = [x for x, count in enumerate(counts) if count > 0]
    if not occupied:
        return []

    def weighted_quantile_x(rank: int, total: int) -> int:
        target = sum(counts) * rank / total
        acc = 0
        for x, count in enumerate(counts):
            acc += count
            if acc >= target:
                return x
        return occupied[-1]

    centers = [float(weighted_quantile_x(i, 6)) for i in range(1, 6)]

    for _ in range(16):
        groups = [[] for _ in range(5)]
        for x in occupied:
            closest = min(range(5), key=lambda idx: abs(x - centers[idx]))
            groups[closest].append(x)
        new_centers = []
        for idx, group in enumerate(groups):
            if not group:
                new_centers.append(centers[idx])
                continue
            weight_sum = sum(counts[x] for x in group)
            new_centers.append(sum(x * counts[x] for x in group) / weight_sum)
        if max(abs(a - b) for a, b in zip(centers, new_centers)) < 0.5:
            centers = new_centers
            break
        centers = new_centers

    columns_by_group = [[] for _ in range(5)]
    for x in occupied:
        closest = min(range(5), key=lambda idx: abs(x - centers[idx]))
        columns_by_group[closest].append(x)

    boxes_with_center: list[tuple[float, tuple[int, int, int, int]]] = []
    for idx, columns in enumerate(columns_by_group):
        if not columns:
            continue
        xs = columns
        ys = [y for x in columns for y in pixel_rows[x]]
        pad = 36
        boxes_with_center.append(
            (
                centers[idx],
                (
                    max(0, min(xs) - pad),
                    max(0, min(ys) - pad),
                    min(width, max(xs) + pad + 1),
                    min(height, max(ys) + pad + 1),
                ),
            )
        )

    boxes_with_center.sort(key=lambda item: item[0])
    return [box for _, box in boxes_with_center]


def extract_subject(entry: dict, lineup_cache: dict[str, list[tuple[int, int, int, int]]]) -> Image.Image:
    if entry["kind"] == "child":
        image = Image.open(SETTING_DIR / "child.png").convert("RGBA")
        crop = image.crop(CHILD_BOXES[entry["box_key"]])
    else:
        sheet_path = SETTING_DIR / f"{entry['sheet_id']}.png"
        image = Image.open(sheet_path).convert("RGBA")
        override = SUBJECT_BOX_OVERRIDES.get(entry["slug"])
        if override:
            crop = image.crop(override)
        else:
            if entry["sheet_id"] not in lineup_cache:
                lineup_cache[entry["sheet_id"]] = find_lineup_boxes(sheet_path)
            crop = image.crop(lineup_cache[entry["sheet_id"]][entry["index"]])
    crop = remove_white_border_background(crop)
    crop = trim_image(crop)
    return add_safe_padding(crop)


def make_reference_canvas(subject: Image.Image, baby_sheet: Image.Image) -> Image.Image:
    canvas_w = 1800
    canvas_h = 1280
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (255, 255, 255, 255))

    # Reserve explicit top/bottom padding so the subject never looks cropped in the reference.
    scale_subject = min(440 / subject.width, 920 / subject.height)
    subject_r = subject.resize(
        (max(1, int(subject.width * scale_subject)), max(1, int(subject.height * scale_subject))),
        Image.LANCZOS,
    )

    scale_baby = min(1120 / baby_sheet.width, 1120 / baby_sheet.height)
    baby_r = baby_sheet.resize(
        (max(1, int(baby_sheet.width * scale_baby)), max(1, int(baby_sheet.height * scale_baby))),
        Image.LANCZOS,
    )

    canvas.alpha_composite(subject_r, (120, (canvas_h - subject_r.height) // 2))
    canvas.alpha_composite(baby_r, (620, (canvas_h - baby_r.height) // 2))
    return canvas


def build_prompt(slug: str, stage: str) -> str:
    return "\n".join(
        [
            "Create one polished 3x3 animation sheet image for a children's monster-raising web game.",
            f"Use the attached reference image as the exact identity of the monster {slug}.",
            "The attached reference image also includes a baby animation sheet example.",
            "Preserve the exact face feeling, body proportions, silhouette, colors, markings, appendages, and overall charm from the reference.",
            f"Follow the baby sheet's row meaning very closely, while drawing only {slug}.",
            STAGE_NOTES[stage],
            "",
            "Layout:",
            "- output exactly one image",
            "- exact 3 columns x 3 rows sheet",
            "- row 1 = idle frames 1 to 3",
            "- row 2 = eating frames 1 to 3",
            "- row 3 = evolution frames 1 to 3",
            "- no text, no labels, no watermark, no panel lines",
            "- perfectly flat solid #00ff00 background only",
            "- keep full body visible in every panel",
            "- generous empty margins on all four sides in every panel",
            "- do not let any horns, ears, wings, tails, fins, halos, sparkles, aura rings, or effects touch or cross panel edges",
            "- do not use #00ff00 inside the character",
            "- no food object in the eating row",
            "",
            "Style:",
            "- premium Japanese casual game illustration",
            "- cute, clean, readable, collectible monster feel",
            "- soft shading, crisp outline, child-friendly",
            "- consistent proportions across all nine panels",
            "",
            "Very important row separation:",
            "- match the clarity of the baby reference sheet, where each row instantly reads as a different animation category",
            "- row 1 must clearly look like normal idle animation only",
            "- row 2 must clearly look like eating animation in all three panels, not just one panel",
            "- row 3 must clearly look like evolution-in-progress animation in all three panels, not idle, walking, sleeping, or jumping",
            "- each row must be visually distinguishable at a glance",
            "",
            "Row details:",
            "- idle row: use the baby reference row 1 as the motion template, meaning subtle pose changes only, gentle blink, soft smile, tiny breathing motion, same calm readable stance, no large action, no aura",
            "- eating row: use the baby reference row 2 as the motion template, meaning all three panels are clearly happy eating faces with mouth opening and chewing progression; adapt that idea to this monster with cute chomping, mouth movement, hands or paws or fins near the mouth area when appropriate, and a clear munching sequence in every panel",
            "- evolution row: use the baby reference row 3 as the motion template, meaning all three panels clearly show transformation energy building around the body; adapt that idea to this monster with magical glow, sparkles, aura rings, stronger presence, and obvious mid-evolution energy in every panel",
            "",
            "Negative constraints:",
            "- do not make row 2 look like waving, celebrating, attacking, or using an elemental attack",
            "- do not make row 3 look like ordinary standing, smiling, sleeping, walking, or simple hopping",
            "- do not use a single repeated pose with tiny changes across different rows",
            "",
            "Output only the image.",
        ]
    )


def main() -> None:
    baby_sheet = Image.open(BABY_SHEET).convert("RGBA")
    lineup_cache: dict[str, list[tuple[int, int, int, int]]] = {}
    count = 0
    for entry in CHARACTERS:
        target_dir = MONSTERS_DIR / entry["stage"] / entry["slug"]
        target_dir.mkdir(parents=True, exist_ok=True)
        subject = extract_subject(entry, lineup_cache)
        reference = make_reference_canvas(subject, baby_sheet)
        (target_dir / "gemini_reference.png").unlink(missing_ok=True)
        reference.save(target_dir / "gemini_reference.png")
        (target_dir / "gemini_prompt.txt").write_text(build_prompt(entry["slug"], entry["stage"]), encoding="utf-8")
        count += 1
        print(f"prepared {entry['stage']}/{entry['slug']}")
    print(f"prepared {count} gemini animation input sets")


if __name__ == "__main__":
    main()
