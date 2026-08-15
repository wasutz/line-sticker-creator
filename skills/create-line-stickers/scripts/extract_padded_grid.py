#!/usr/bin/env python3
"""Extract a sticker grid with overlap while discarding neighboring-cell fragments."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

COMPONENT = re.compile(
    r"^\s+(\d+): (\d+)x(\d+)\+(\d+)\+(\d+) ([\d.]+),([\d.]+) (\d+) "
)


def dimensions(path: Path) -> tuple[int, int]:
    result = subprocess.run(
        ["magick", "identify", "-format", "%w %h", str(path)],
        check=True,
        text=True,
        capture_output=True,
    )
    width, height = result.stdout.split()
    return int(width), int(height)


def components(path: Path) -> list[tuple[int, int, int, int, int, float, float, int]]:
    result = subprocess.run(
        [
            "magick", str(path), "-alpha", "extract", "-threshold", "1%",
            "-define", "connected-components:verbose=true", "-connected-components", "8", "null:",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    parsed = []
    for line in result.stdout.splitlines():
        match = COMPONENT.match(line)
        if match:
            ident, width, height, x, y, cx, cy, area = match.groups()
            parsed.append((int(ident), int(width), int(height), int(x), int(y), float(cx), float(cy), int(area)))
    return parsed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=2)
    parser.add_argument("--rows", type=int, default=5)
    parser.add_argument("--padding", type=int, default=36)
    parser.add_argument("--prefix", default="cell")
    args = parser.parse_args()

    if not shutil.which("magick"):
        parser.error("ImageMagick `magick` is required")

    sheet_width, sheet_height = dimensions(args.input)
    cell_width = sheet_width / args.columns
    cell_height = sheet_height / args.rows
    args.out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temporary:
        temporary_dir = Path(temporary)
        index = 0
        for row in range(args.rows):
            for column in range(args.columns):
                core_left = round(column * cell_width)
                core_top = round(row * cell_height)
                core_right = round((column + 1) * cell_width)
                core_bottom = round((row + 1) * cell_height)
                left = max(0, core_left - args.padding)
                top = max(0, core_top - args.padding)
                right = min(sheet_width, core_right + args.padding)
                bottom = min(sheet_height, core_bottom + args.padding)
                crop = temporary_dir / f"crop-{index}.png"
                cleaned = args.out_dir / f"{args.prefix}-{index}.png"

                subprocess.run(
                    [
                        "magick", str(args.input), "-crop", f"{right-left}x{bottom-top}+{left}+{top}",
                        "+repage", "-alpha", "on", "-fuzz", "16%", "-transparent", "#00ff00", str(crop),
                    ],
                    check=True,
                )

                local_core = (
                    core_left - left,
                    core_top - top,
                    core_right - left,
                    core_bottom - top,
                )
                remove_boxes = []
                for ident, width, height, x, y, cx, cy, area in components(crop):
                    if ident == 0 or area < 12:
                        continue
                    inside = local_core[0] <= cx < local_core[2] and local_core[1] <= cy < local_core[3]
                    if not inside:
                        remove_boxes.append((width, height, x, y))

                command = ["magick", str(crop)]
                for width, height, x, y in remove_boxes:
                    command.extend([
                        "-region", f"{width}x{height}+{x}+{y}",
                        "-channel", "A", "-evaluate", "set", "0", "+channel", "+region",
                    ])
                command.extend(["-trim", "+repage", str(cleaned)])
                subprocess.run(command, check=True)
                index += 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
