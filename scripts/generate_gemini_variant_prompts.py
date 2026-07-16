import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".gemini-output" / "prompts"

BASE_SUBJECTS = {
    "baby": "a baby monster for a children's virtual pet game, neutral and adorable, soft mint body, tiny horn-like ears, round cheeks, simple silhouette that can grow into many directions",
    "momo": "a pink mochi-like bunny monster with round cheeks, a tiny leaf-like tail, a soft rounded silhouette, and a sweet cheerful face",
    "pafu": "a mint-blue fluffy sheep-like monster with cloud-like wool, a gentle face, rounded ears, and a soft plush silhouette",
    "gabu": "an orange baby dinosaur monster with one tiny fang, a sturdy rounded body, short limbs, and a playful mischievous expression",
    "fuwa": "a pale blue floating spirit monster with a small star motif, a dreamy face, a smooth rounded body, and a gentle magical feeling",
}

DESIGN_RULES = """
Important character design rules:
- do not attach fruit, fish, carrot, or broccoli directly onto the head or body
- express food influence through color, glow, texture, patterns, aura, accessories, props, costume motifs, and tiny abstract motifs
- preserve the same character identity as the pre-evolution form
- keep the same core silhouette and face feeling so it looks like growth, not a different species
- evolved forms should feel rewarding, exciting, and magical at a glance
- it is good to add special accessories such as ribbons, scarves, capes, brooches, staffs, halos, belts, charms, glowing ornaments, and adventure props
- stage 1 should feel clearly more grown-up and exciting than the base form
- stage 2 should feel clearly more mature, more special, and more majestic than stage 1
- the eating row must not contain any food object, fruit, fish, carrot, broccoli, plate, fork, spoon, bowl, or snack in the artwork
- the eating row should communicate eating only through mouth shape, cheeks, hands, pose, and expression
- the evolution row may contain magical rings, stars, bubbles, leaves, flames, ribbons of light, and stronger transformation effects
""".strip()

VARIANT_DESCRIPTIONS = {
    "baby": "beginner baby form, neutral, simple, and versatile, clearly younger and smaller than the evolved monsters",
    "momo": "base evolution of the baby into Momo, a pink mochi-like bunny monster, cheerful and sweet, simple and iconic, clearly older than the baby but still compact and childlike",
    "pafu": "base evolution of the baby into Pafu, a mint-blue fluffy sheep-like monster, soft and comforting, still rounded and childlike but more distinct than the baby form",
    "gabu": "base evolution of the baby into Gabu, an orange playful dinosaur child, energetic and mischievous, stronger and more defined than the baby form",
    "fuwa": "base evolution of the baby into Fuwa, a pale blue floating spirit child, dreamy and magical, still simple and rounded but more expressive than the baby form",
    "momo_1_apple": "stage 1 evolution of Momo, glossy deeper pink to red body, juicy translucent highlights on cheeks and belly, sweet reward feeling, still the same rounded bunny-mochi silhouette",
    "momo_1_carrot": "stage 1 evolution of Momo, bright orange accent lighting, sunny energetic feeling, slightly more lively hair-like ear motion, same cute round body",
    "momo_1_fish": "stage 1 evolution of Momo, pink and cool blue translucent body, soft wave and water ripple patterns, calm floating feeling, same sweet bunny face",
    "momo_1_broccoli": "stage 1 evolution of Momo, tender leaf-green gradients, tiny forest-light particles, natural and gentle mood, same rounded silhouette and cheeks",
    "momo_1_balance": "stage 1 evolution of Momo, pastel rainbow highlights, milky dreamy palette, happy all-rounder feeling, same recognizable Momo silhouette",
    "momo_1_standard": "stage 1 evolution of Momo, straightforward growth of the original form, richer shine, cleaner outline, same character with slightly more mature charm",
    "momo_2_specialist": "stage 2 evolution of Momo, refined princess-like sweet evolution, jewel-like gloss, stronger gradients, premium reward feeling, clearly evolved from stage 1 sweet Momo",
    "momo_2_switch": "stage 2 evolution of Momo, transformed into a new theme while keeping traces of the previous colors, elegant color-shift growth, same round face and bunny silhouette",
    "momo_2_harmony": "stage 2 evolution of Momo, warm multi-color harmony form, soft floral and starry sparkles, full and satisfied aura, same adorable Momo identity",
    "momo_2_glow": "stage 2 evolution of Momo, polished luminous growth form, boosted transparency and gentle sparkle, simple but clearly more mature than stage 1",
    "pafu_1_apple": "stage 1 evolution of Pafu, fluffy candy-like sheen in red pink tones, sweet and glossy but no literal fruit parts, same plush sheep silhouette",
    "pafu_1_carrot": "stage 1 evolution of Pafu, warm cream and orange sunlight palette, comforting and energetic, same soft wool and rounded ears",
    "pafu_1_fish": "stage 1 evolution of Pafu, pale aqua and white sea-breeze coloring, flowing lines through the wool, light and airy, same gentle expression",
    "pafu_1_broccoli": "stage 1 evolution of Pafu, herbal green healing palette, delicate leaf-vein-like patterns, nap-in-the-forest feeling, same cuddly wool shape",
    "pafu_1_balance": "stage 1 evolution of Pafu, pastel rainbow fluff, dreamy all-food harmony vibe, floating tiny lights, same rounded plush body and ears",
    "pafu_1_standard": "stage 1 evolution of Pafu, straightforward grown-up fluffy version, fuller wool, richer expression, still clearly the same Pafu",
    "pafu_2_specialist": "stage 2 evolution of Pafu, luxurious perfected fluffy form, bigger elegant wool shape, serene and reassuring presence, direct growth from stage 1",
    "pafu_2_switch": "stage 2 evolution of Pafu, magical transformation feeling with changed main palette, old theme faintly inside and new theme on the outside, same soft face and plush silhouette",
    "pafu_2_harmony": "stage 2 evolution of Pafu, fantasy dream-cloud form with soft nebula colors and bubbles of light, maximal comfort and harmony while keeping the same Pafu body plan",
    "pafu_2_glow": "stage 2 evolution of Pafu, bright polished growth form with glowing wool edges and clean charm, simple but clearly advanced",
    "gabu_1_apple": "stage 1 evolution of Gabu, fiery red-orange gradients, playful hot-blooded energy, stronger brows and action lines, same compact dinosaur kid silhouette",
    "gabu_1_carrot": "stage 1 evolution of Gabu, vitamin-color speedster feeling, sharper motion lines, active and healthy, same sturdy rounded body and playful fang",
    "gabu_1_fish": "stage 1 evolution of Gabu, deep blue aqua tones, streamlined water patterns, cool hunter mood, same young dinosaur identity",
    "gabu_1_broccoli": "stage 1 evolution of Gabu, deep and bright green camouflage-like patterns, soft vine or leaf motifs, forest guardian feeling, same friendly chibi power",
    "gabu_1_balance": "stage 1 evolution of Gabu, leader-like all-rounder form, bold chest or forehead emblem feel without literal crown, same mischievous grin and compact body",
    "gabu_1_standard": "stage 1 evolution of Gabu, direct healthy growth of the base form, slightly more athletic, stronger limbs and tail motion, same playful character",
    "gabu_2_specialist": "stage 2 evolution of Gabu, powerful perfected specialist form, dramatic shading and chest-out posture, reliable strength, still clearly descended from stage 1 Gabu",
    "gabu_2_switch": "stage 2 evolution of Gabu, dramatic two-theme transformation, old and new colors colliding in a cohesive way, same stout body and dinosaur face",
    "gabu_2_harmony": "stage 2 evolution of Gabu, radiant sun-hero form, warm golden glow and hopeful strength, combines toughness and kindness while preserving Gabu's core silhouette",
    "gabu_2_glow": "stage 2 evolution of Gabu, clean and straightforward ultimate growth, minimal ornament, maximum presence, same recognizable Gabu shape matured further",
    "fuwa_1_apple": "stage 1 evolution of Fuwa, pink-red sparkles and sweet lucky-star feeling, no literal fruit, same floating rounded spirit body and dreamy face",
    "fuwa_1_carrot": "stage 1 evolution of Fuwa, sunrise orange and cream glow, warm optimistic atmosphere, same cloudlike floating silhouette",
    "fuwa_1_fish": "stage 1 evolution of Fuwa, moonlight and water translucency, blue-white calm magical mood, same round spirit form",
    "fuwa_1_broccoli": "stage 1 evolution of Fuwa, woodland healing green light, tiny drifting leaflike light pieces, same soft floating body",
    "fuwa_1_balance": "stage 1 evolution of Fuwa, cosmic pastel glow with nebula gradients and round light particles, balanced and wondrous, same gentle face and silhouette",
    "fuwa_1_standard": "stage 1 evolution of Fuwa, simple polished growth with increased transparency and light particles, same familiar Fuwa personality",
    "fuwa_2_specialist": "stage 2 evolution of Fuwa, star-constellation inspired perfected form, fine lines of light and tiny stars around it, same round gentle body grown more mystical",
    "fuwa_2_switch": "stage 2 evolution of Fuwa, smoothly shifting color-time evolution, old and new themes blending across the body, same dreamy Fuwa silhouette",
    "fuwa_2_harmony": "stage 2 evolution of Fuwa, galaxy harmony form with soft multicolor nebula aura and huge emotional warmth, clearly evolved but still unmistakably Fuwa",
    "fuwa_2_glow": "stage 2 evolution of Fuwa, clean sacred light form with platinum glow and crisp silhouette, simple and luminous, same rounded spirit core",
}

ASSET_TARGETS = [
    "baby",
    "momo",
    "pafu",
    "gabu",
    "fuwa",
    *[f"{base}_1_{kind}" for base in ["momo", "pafu", "gabu", "fuwa"] for kind in ["apple", "carrot", "fish", "broccoli", "balance", "standard"]],
    *[f"{base}_2_{kind}" for base in ["momo", "pafu", "gabu", "fuwa"] for kind in ["specialist", "switch", "harmony", "glow"]],
]


def growth_direction(asset_id: str) -> str:
    if asset_id == "baby":
        return "make this the youngest and simplest form, very small and neutral"
    if "_" not in asset_id:
        return "make this clearly older and more defined than the baby form, but still childlike and iconic"
    if "_1_" in asset_id:
        return "make this stage 1 form noticeably taller, larger, and more mature than the base form while staying cute"
    if "_2_" in asset_id:
        return "make this stage 2 form clearly more mature, taller, more decorated, and more spectacular than stage 1"
    return ""


def excitement_direction(asset_id: str) -> str:
    if asset_id == "baby":
        return "keep accessories minimal because this is a beginner form"
    if "_" not in asset_id:
        return "add one small signature accessory or motif so the first evolution already feels special"

    variant = asset_id.split("_")[-1]
    directions = {
        "apple": "add sweet reward-like excitement with jewel sparkles, candy-like ribbons, glossy ornaments, or a cute prize accessory",
        "carrot": "add adventure and energy with a scarf, pouch, badge, sun charm, or sporty travel accessory",
        "fish": "add magical water wonder with droplet ornaments, moon charms, wave rings, bubble halos, or elegant sea-themed props",
        "broccoli": "add forest adventure wonder with leaf capes, vine trims, acorn charms, bark-like brooches, or woodland accessories",
        "balance": "add all-rounder wonder with rainbow charms, star staffs, festival ornaments, or mixed magical accessories",
        "standard": "add subtle but exciting growth details like a chest charm, tail ribbon, shoulder ornament, or polished signature accessory",
        "specialist": "add premium final-form excitement with crown-like halos, royal brooches, hero capes, staffs, or high-status magical accessories",
        "switch": "add dramatic transformation excitement with asymmetrical accessories, dual-color props, transformation gear, or split-theme ornaments",
        "harmony": "add celebratory harmony wonder with rainbow rings, star garlands, flower-like glow ornaments, or festival accessories",
        "glow": "add sacred glowing wonder with light veils, holy charms, sparkling halos, and refined luminous accessories",
    }
    return directions.get(variant, "add one memorable magical accessory that makes the evolution feel special")


def build_prompt(asset_id: str) -> str:
    if asset_id == "baby":
        subject = BASE_SUBJECTS["baby"]
    elif "_" not in asset_id:
        subject = BASE_SUBJECTS[asset_id]
    else:
        subject = BASE_SUBJECTS[asset_id.split("_", 1)[0]]

    variant_description = VARIANT_DESCRIPTIONS[asset_id]
    growth_note = growth_direction(asset_id)
    excitement_note = excitement_direction(asset_id)

    return f"""
Create one polished sprite sheet for a children's web game called MoguMoguMonster.

Character:
- {subject}
- {variant_description}
- make it look like a natural evolution of the same monster family, not a different unrelated creature
- {growth_note}
- {excitement_note}

{DESIGN_RULES}

Layout:
- output one image only
- exact sprite sheet layout: 3 columns x 3 rows
- each cell contains one full character pose with generous margins
- no cropping, no cut-off ears, no cut-off sparkles, no cut-off shadows, no text
- plain pure white background only
- keep the character centered in every cell

Rows:
- row 1: idle animation, blinking and subtle body motion
- row 2: eating animation, big happy eating face, designed so any separate food prop can be composited in front of the mouth, but draw no food object in the image itself
- row 3: evolution animation, magical glowing transformation pose

Columns:
- three distinct frames for each row

Style:
- cute high-quality 2D Japanese game illustration
- soft shading, clear silhouette, expressive face
- suitable for toddlers and young children
- keep proportions consistent across all nine cells

Important:
- preserve the same character identity across all frames
- make the evolution feel exciting and rewarding for children
- output only the sprite sheet image
""".strip()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for asset_id in ASSET_TARGETS:
        prompt = build_prompt(asset_id)
        path = OUT_DIR / f"{asset_id}.txt"
        path.write_text(prompt, encoding="utf-8")
        manifest[asset_id] = str(path)
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"generated {len(manifest)} prompt files")


if __name__ == "__main__":
    main()
