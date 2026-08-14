#!/usr/bin/env python3
"""Render Thai sticker lettering through Pango/HarfBuzz via rsvg-convert."""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--text", required=True, help="Use | for a line break")
    parser.add_argument("--out", required=True)
    parser.add_argument("--width", type=int, default=350)
    parser.add_argument("--height", type=int, default=90)
    parser.add_argument("--font-size", type=float, default=46)
    parser.add_argument("--fill", default="#5b4a47")
    parser.add_argument("--stroke", default="#ffffff")
    parser.add_argument("--stroke-width", type=float, default=4)
    args = parser.parse_args()

    renderer = shutil.which("rsvg-convert")
    if not renderer:
        parser.error("rsvg-convert is required for Thai text shaping")

    lines = args.text.split("|")
    line_height = args.font_size * 1.05
    first_y = args.height / 2 - (len(lines) - 1) * line_height / 2 + args.font_size * 0.34
    tspans = "".join(
        f'<tspan x="{args.width / 2:g}" y="{first_y + i * line_height:g}">{html.escape(line)}</tspan>'
        for i, line in enumerate(lines)
    )
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{args.width}" height="{args.height}" viewBox="0 0 {args.width} {args.height}">
  <text text-anchor="middle" font-family="Mali" font-size="{args.font_size:g}" font-weight="700"
        fill="{html.escape(args.fill)}" stroke="{html.escape(args.stroke)}" stroke-width="{args.stroke_width:g}"
        stroke-linejoin="round" paint-order="stroke fill">{tspans}</text>
</svg>'''
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".svg", encoding="utf-8") as source:
        source.write(svg)
        source.flush()
        subprocess.run([renderer, "-o", str(output), source.name], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
