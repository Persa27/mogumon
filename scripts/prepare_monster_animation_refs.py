from __future__ import annotations

import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SETTING_DIR = ROOT / "static" / "monsters" / "setting_picture"
OUT_DIR = ROOT / ".chatgpt-output" / "monster_animation_refs"

SHEETS: dict[str, list[str]] = {
    "draup_mature": ["フレアドラグ", "ボルトドラグ", "フロストドラグ", "マグマロック", "シャインドラグ"],
    "draup_final": ["プロメテウス", "インドラ・ドラグ", "アグニヴァ", "ガイアドラグ", "ソル・ドラグニル"],
    "garoron_mature": ["バーストガロ", "ボルトガロ", "アクアガロ", "テラガロ", "ホーリーガロ"],
    "garoron_final": ["イフリート・レオ", "ライデンヴォルフ", "ケルピーヴォルト", "ユグドラビースト", "シリウス・スター"],
    "fishul_mature": ["スチームフィン", "プラズマフィン", "グラキエス", "コーラルガルド", "エンゼルフィン"],
    "fishul_final": ["レヴィア・バーン", "サンダーカイザー", "ポセイドラム", "オケアノス", "セラフィ・アクア"],
    "kororon_mature": ["バーンゴレム", "パルスロック", "スプラッシュテラ", "フォレストガルド", "ルーンゴーレム"],
    "kororon_final": ["タイタン・マグマ", "トール・テラ", "ネプチュン・ロック", "ユグドラシル", "クロノス・テラ"],
    "lumina_mature": ["フレアエテルナ", "ボルトエテルナ", "クリスタルエテルナ", "リーフエテルナ", "エテルナ"],
    "lumina_final": ["フェニックス", "アストラル・ライ", "ダイアモンド・ハロー", "エデン・スピリット", "ゼウス・オメガ"],
}


def find_boxes(sheet_path: Path) -> list[tuple[int, int, int, int]]:
    image = Image.open(sheet_path).convert("RGB")
    width, height = image.size
    boxes: list[tuple[int, int, int, int]] = []
    segment_w = width / 5
    for index in range(5):
        seg_left = round(index * segment_w)
        seg_right = round((index + 1) * segment_w)
        inner_pad_x = round(segment_w * 0.12)
        visited: set[tuple[int, int]] = set()
        best: list[tuple[int, int]] = []
        y_min = 140
        y_max = int(height * 0.76)
        search_left = seg_left + inner_pad_x
        search_right = seg_right - inner_pad_x
        for x in range(search_left, search_right):
            for y in range(y_min, y_max):
                if (x, y) in visited:
                    continue
                r, g, b = image.getpixel((x, y))
                if min(r, g, b) >= 245:
                    continue
                stack = [(x, y)]
                component: list[tuple[int, int]] = []
                visited.add((x, y))
                while stack:
                    cx, cy = stack.pop()
                    component.append((cx, cy))
                    for nx, ny in ((cx - 1, cy), (cx + 1, cy), (cx, cy - 1), (cx, cy + 1)):
                        if not (search_left <= nx < search_right and y_min <= ny < y_max):
                            continue
                        if (nx, ny) in visited:
                            continue
                        nr, ng, nb = image.getpixel((nx, ny))
                        if min(nr, ng, nb) >= 245:
                            continue
                        visited.add((nx, ny))
                        stack.append((nx, ny))
                if len(component) > len(best):
                    best = component
        if best:
            xs = [x for x, _ in best]
            ys = [y for _, y in best]
            pad = 36
            boxes.append(
                (
                    max(0, min(xs) - pad),
                    max(0, min(ys) - pad),
                    min(width, max(xs) + pad + 1),
                    min(height, max(ys) + pad + 1),
                )
            )
    return boxes


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest: list[dict[str, str | int]] = []
    for sheet_id, names in SHEETS.items():
        sheet_path = SETTING_DIR / f"{sheet_id}.png"
        boxes = find_boxes(sheet_path)
        if len(boxes) != 5:
            raise RuntimeError(f"{sheet_id}: expected 5 boxes, got {len(boxes)}")
        image = Image.open(sheet_path).convert("RGBA")
        for index, (name, box) in enumerate(zip(names, boxes), start=1):
            crop = image.crop(box)
            ref_path = OUT_DIR / f"{sheet_id}_{index}.png"
            crop.save(ref_path)
            manifest.append(
                {
                    "sheet_id": sheet_id,
                    "index": index,
                    "name": name,
                    "reference_path": str(ref_path),
                    "remove_mode": "green-diff-merge" if sheet_id.startswith("lumina_") else "standard",
                    "min_padding": 56 if sheet_id.endswith("_final") else 40,
                }
            )
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"prepared {len(manifest)} references")


if __name__ == "__main__":
    main()
