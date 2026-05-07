#!/usr/bin/env python3
"""Generate MVP monster SVG assets (4 monsters x idle/eat/evolve + portrait)."""
from pathlib import Path

MONSTERS = {
    "momo": {"body": "#ff9ec9", "accent": "#ffd166", "eye": "#3a2d3c", "bg": "#fff6fb"},
    "pafu": {"body": "#8bd3ff", "accent": "#a8e6a1", "eye": "#2b3440", "bg": "#f4f8ff"},
    "gabu": {"body": "#ffb86b", "accent": "#ff7f50", "eye": "#3e2a1f", "bg": "#fffaf0"},
    "fuwa": {"body": "#c7f9cc", "accent": "#bde0fe", "eye": "#2d3a2f", "bg": "#f7fff7"},
}


def render_svg(c: dict, state: str) -> str:
    mouth = {
        "idle": '<path d="M104 168 Q128 180 152 168" stroke="{eye}" stroke-width="7" fill="none" stroke-linecap="round"/>',
        "eat": '<ellipse cx="128" cy="170" rx="16" ry="10" fill="#ffffff"/><path d="M112 162 H144" stroke="{eye}" stroke-width="6"/>',
        "evolve": '<path d="M104 168 Q128 188 152 168" stroke="{eye}" stroke-width="7" fill="none" stroke-linecap="round"/>',
    }[state].format(eye=c["eye"])

    sparkle = ""
    if state == "evolve":
        sparkle = (
            '<path d="M32 32 v20 M22 42 h20" stroke="#ffd700" stroke-width="4"/>'
            '<path d="M210 36 v18 M201 45 h18" stroke="#ffd700" stroke-width="4"/>'
            '<path d="M124 14 v16 M116 22 h16" stroke="#ffd700" stroke-width="4"/>'
        )

    bounce = -4 if state == "idle" else 0
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="40" fill="{c['bg']}"/>
  <ellipse cx="128" cy="{150 + bounce}" rx="72" ry="64" fill="{c['body']}"/>
  <circle cx="98" cy="{135 + bounce}" r="10" fill="{c['eye']}"/>
  <circle cx="158" cy="{135 + bounce}" r="10" fill="{c['eye']}"/>
  {mouth}
  <ellipse cx="128" cy="{80 + bounce}" rx="38" ry="26" fill="{c['accent']}"/>
  <circle cx="86" cy="{105 + bounce}" r="18" fill="{c['body']}"/>
  <circle cx="170" cy="{105 + bounce}" r="18" fill="{c['body']}"/>
  {sparkle}
</svg>
'''


def main() -> int:
    for name, colors in MONSTERS.items():
        root = Path("static/monsters") / name
        for state in ["idle", "eat", "evolve"]:
            out = root / state / "frame1.svg"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(render_svg(colors, state), encoding="utf-8")
        (root / "portrait.svg").write_text(render_svg(colors, "idle"), encoding="utf-8")
    print("Generated SVG monster assets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
