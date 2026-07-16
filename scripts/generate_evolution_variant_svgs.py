#!/usr/bin/env python3
"""Generate placeholder SVG assets for stage 1/2 evolution variants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "static" / "monsters"

BASES = {
    "momo": {
        "body": "#ff9cc5",
        "outline": "#7d4665",
        "eye": "#402638",
        "motif": "round",
        "accent": "#ffd166",
        "cheek": "#ff7fa0",
    },
    "pafu": {
        "body": "#a8ecff",
        "outline": "#43748c",
        "eye": "#253341",
        "motif": "cloud",
        "accent": "#a8e6a1",
        "cheek": "#ffc3d6",
    },
    "gabu": {
        "body": "#ffbe76",
        "outline": "#8a5532",
        "eye": "#342219",
        "motif": "spike",
        "accent": "#ff8f5e",
        "cheek": "#ffcf92",
    },
    "fuwa": {
        "body": "#bfe7ff",
        "outline": "#4a6d94",
        "eye": "#263248",
        "motif": "spirit",
        "accent": "#ffe16d",
        "cheek": "#ffd3ea",
    },
}

VARIANTS = {
    "apple": {"accent": "#ff5f7a", "extra": "#8cff9f", "symbol": "apple"},
    "carrot": {"accent": "#ff9f43", "extra": "#7ed957", "symbol": "carrot"},
    "fish": {"accent": "#4d96ff", "extra": "#9ad7ff", "symbol": "fish"},
    "broccoli": {"accent": "#4caf50", "extra": "#7fdc72", "symbol": "broccoli"},
    "balance": {"accent": "#c77dff", "extra": "#ffd166", "symbol": "star"},
    "standard": {"accent": "#ffd166", "extra": "#ffffff", "symbol": "dot"},
    "specialist": {"accent": "#ffe066", "extra": "#ffffff", "symbol": "burst"},
    "switch": {"accent": "#7bdff2", "extra": "#ff9f1c", "symbol": "crescent"},
    "harmony": {"accent": "#ff8fab", "extra": "#b8f2e6", "symbol": "ring"},
    "glow": {"accent": "#b8f2e6", "extra": "#fff3b0", "symbol": "spark"},
}

STAGE1_KEYS = ["apple", "carrot", "fish", "broccoli", "balance", "standard"]
STAGE2_KEYS = ["specialist", "switch", "harmony", "glow"]


def symbol_svg(symbol: str, accent: str, extra: str, x: int, y: int) -> str:
    if symbol == "apple":
        return f'<circle cx="{x}" cy="{y}" r="11" fill="{accent}"/><ellipse cx="{x+6}" cy="{y-10}" rx="5" ry="3" fill="{extra}"/>'
    if symbol == "carrot":
        return f'<path d="M{x-6} {y-10} L{x+8} {y} L{x-2} {y+14} Z" fill="{accent}"/><path d="M{x-2} {y-14} q6 2 8 8 M{x-8} {y-12} q6 2 8 8" stroke="{extra}" stroke-width="4" fill="none" stroke-linecap="round"/>'
    if symbol == "fish":
        return f'<ellipse cx="{x}" cy="{y}" rx="15" ry="9" fill="{accent}"/><path d="M{x+12} {y} l12 -8 v16 Z" fill="{extra}"/><circle cx="{x-6}" cy="{y-1}" r="2.5" fill="#fff"/>'
    if symbol == "broccoli":
        return f'<circle cx="{x}" cy="{y-6}" r="10" fill="{accent}"/><circle cx="{x-8}" cy="{y-2}" r="8" fill="{accent}"/><circle cx="{x+8}" cy="{y-2}" r="8" fill="{accent}"/><rect x="{x-3}" y="{y+4}" width="6" height="10" rx="2" fill="{extra}"/>'
    if symbol == "star":
        return f'<path d="M{x} {y-14} l4 9 10 1 -8 7 2 10 -8 -5 -8 5 2 -10 -8 -7 10 -1 Z" fill="{accent}" stroke="{extra}" stroke-width="2"/>'
    if symbol == "burst":
        return f'<path d="M{x} {y-16} v12 M{x} {y+4} v12 M{x-16} {y} h12 M{x+4} {y} h12 M{x-11} {y-11} l8 8 M{x+3} {y+3} l8 8 M{x+11} {y-11} l-8 8 M{x-11} {y+11} l8 -8" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>'
    if symbol == "crescent":
        return f'<path d="M{x+6} {y-14} q-18 8 -8 28 q-12 -4 -12 -16 q0 -12 14 -18 q2 4 6 6 Z" fill="{accent}"/><circle cx="{x-4}" cy="{y-2}" r="4" fill="{extra}"/>'
    if symbol == "ring":
        return f'<circle cx="{x}" cy="{y}" r="15" fill="none" stroke="{accent}" stroke-width="6"/><circle cx="{x}" cy="{y}" r="6" fill="{extra}"/>'
    if symbol == "spark":
        return f'<path d="M{x} {y-14} l4 10 10 4 -10 4 -4 10 -4 -10 -10 -4 10 -4 Z" fill="{accent}" stroke="{extra}" stroke-width="2"/>'
    return f'<circle cx="{x}" cy="{y}" r="8" fill="{accent}"/>'


def body_path(motif: str) -> str:
    if motif == "round":
        return "M74 150 C74 96, 104 56, 150 56 C196 56, 224 96, 220 152 C216 198, 188 216, 148 216 C104 216, 72 196, 74 150 Z"
    if motif == "cloud":
        return "M62 154 C62 120, 88 86, 120 86 C130 58, 152 48, 176 54 C194 58, 212 72, 218 98 C234 102, 244 116, 244 134 C244 162, 222 182, 196 182 H96 C76 182, 62 170, 62 154 Z"
    if motif == "spike":
        return "M72 168 C68 118, 92 74, 136 62 C160 34, 196 42, 208 70 C226 82, 236 102, 232 138 C228 184, 196 214, 146 214 C102 214, 76 196, 72 168 Z"
    return "M86 168 C72 126, 84 82, 126 60 C170 36, 214 74, 214 124 C214 182, 176 216, 132 216 C106 216, 92 198, 86 168 Z"


def ear_svg(base: str, frame: int, outline: str, body: str) -> str:
    wobble = [-2, 2, 0][frame - 1]
    if base == "momo":
        return f'<path d="M106 64 q-6 -30 12 -46 q12 16 10 42" fill="{body}" stroke="{outline}" stroke-width="5"/><path d="M152 62 q8 -28 30 -34 q4 20 -8 42" fill="{body}" stroke="{outline}" stroke-width="5"/>'
    if base == "pafu":
        return f'<circle cx="90" cy="{102 + wobble}" r="22" fill="{body}" stroke="{outline}" stroke-width="5"/><circle cx="180" cy="{98 - wobble}" r="24" fill="{body}" stroke="{outline}" stroke-width="5"/>'
    if base == "gabu":
        return f'<path d="M120 62 l16 -28 12 28" fill="{body}" stroke="{outline}" stroke-width="5"/><path d="M156 68 l18 -24 10 24" fill="{body}" stroke="{outline}" stroke-width="5"/>'
    return f'<path d="M122 44 l10 -18 10 18 -10 10 Z" fill="{body}" stroke="{outline}" stroke-width="5"/>'


def mouth_svg(state: str, eye: str, accent: str) -> str:
    if state == "eat":
        return f'<ellipse cx="140" cy="164" rx="22" ry="16" fill="#fff"/><path d="M120 160 H160" stroke="{eye}" stroke-width="6"/><path d="M130 174 q10 8 20 0" stroke="{accent}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    if state == "evolve":
        return f'<path d="M116 166 q24 18 48 0" stroke="{eye}" stroke-width="7" fill="none" stroke-linecap="round"/>'
    return f'<path d="M120 164 q20 12 40 0" stroke="{eye}" stroke-width="7" fill="none" stroke-linecap="round"/>'


def eye_svg(state: str, eye: str) -> str:
    if state == "idle":
        return f'<circle cx="114" cy="138" r="7" fill="{eye}"/><circle cx="164" cy="138" r="7" fill="{eye}"/>'
    if state == "eat":
        return f'<path d="M104 136 q10 -8 20 0" stroke="{eye}" stroke-width="6" fill="none" stroke-linecap="round"/><path d="M154 136 q10 -8 20 0" stroke="{eye}" stroke-width="6" fill="none" stroke-linecap="round"/>'
    return f'<circle cx="114" cy="138" r="7" fill="{eye}"/><circle cx="164" cy="138" r="7" fill="{eye}"/><circle cx="114" cy="138" r="2.5" fill="#fff"/><circle cx="164" cy="138" r="2.5" fill="#fff"/>'


def aura_svg(state: str, accent: str, extra: str, frame: int) -> str:
    if state != "evolve":
        return ""
    sizes = [74, 82, 90]
    radius = sizes[frame - 1]
    return (
        f'<circle cx="138" cy="144" r="{radius}" fill="none" stroke="{accent}" stroke-width="5" opacity=".55"/>'
        f'<circle cx="138" cy="144" r="{radius - 18}" fill="none" stroke="{extra}" stroke-width="3" opacity=".65"/>'
    )


def variant_svg(base_name: str, variant_key: str, state: str, frame: int) -> str:
    base = BASES[base_name]
    variant = VARIANTS[variant_key]
    y_shift = [0, -4, 2][frame - 1] if state == "idle" else [0, 2, -2][frame - 1]
    body_path_d = body_path(base["motif"])
    symbols = (
        symbol_svg(variant["symbol"], variant["accent"], variant["extra"], 84, 78)
        + symbol_svg(variant["symbol"], variant["accent"], variant["extra"], 190, 92)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="none"/>
  {aura_svg(state, variant["accent"], variant["extra"], frame)}
  <g transform="translate(0 {y_shift})">
    <path d="{body_path_d}" fill="{base['body']}" stroke="{base['outline']}" stroke-width="6"/>
    {ear_svg(base_name, frame, base["outline"], base["body"])}
    <ellipse cx="126" cy="182" rx="22" ry="16" fill="{base['cheek']}" opacity=".65"/>
    <ellipse cx="178" cy="182" rx="20" ry="14" fill="{base['cheek']}" opacity=".65"/>
    <path d="M116 96 q18 -20 38 -16 q18 4 28 22" fill="none" stroke="{variant['accent']}" stroke-width="7" stroke-linecap="round"/>
    {symbols}
    {eye_svg(state, base["eye"])}
    {mouth_svg(state, base["eye"], variant["accent"])}
  </g>
</svg>
"""


def write_variant(base_name: str, evolution_id: str, variant_key: str) -> None:
    root = OUT / evolution_id
    for state in ["idle", "eat", "evolve"]:
        scene = root / state
        scene.mkdir(parents=True, exist_ok=True)
        for frame in [1, 2, 3]:
            (scene / f"frame{frame}.svg").write_text(variant_svg(base_name, variant_key, state, frame), encoding="utf-8")
    (root / "portrait.svg").write_text(variant_svg(base_name, variant_key, "idle", 1), encoding="utf-8")


def main() -> int:
    for base_name in BASES:
        for key in STAGE1_KEYS:
            write_variant(base_name, f"{base_name}_1_{key}", key)
        for key in STAGE2_KEYS:
            write_variant(base_name, f"{base_name}_2_{key}", key)
    print("Generated evolution variant SVG assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
