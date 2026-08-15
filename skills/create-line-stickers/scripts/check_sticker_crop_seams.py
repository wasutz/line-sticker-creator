#!/usr/bin/env python3
"""Detect suspicious straight crop seams within rendered sticker artwork."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from collections import deque
from pathlib import Path

PIXEL = re.compile(r"^(\d+),(\d+): \((\d+)")


def longest_run(values: list[int]) -> int:
    best = current = 0
    previous: int | None = None
    for value in sorted(values):
        current = current + 1 if previous is not None and value == previous + 1 else 1
        best = max(best, current)
        previous = value
    return best


def opaque_pixels(path: Path) -> set[tuple[int, int]]:
    result = subprocess.run(
        ["magick", str(path), "-alpha", "extract", "-threshold", "1%", "txt:-"],
        check=True,
        text=True,
        capture_output=True,
    )
    pixels = set()
    for line in result.stdout.splitlines():
        match = PIXEL.match(line)
        if match:
            x, y, alpha = map(int, match.groups())
            if alpha > 0:
                pixels.add((x, y))
    return pixels


def connected_components(pixels: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(pixels)
    found = []
    neighbors = [
        (-1, -1), (0, -1), (1, -1),
        (-1, 0),           (1, 0),
        (-1, 1),  (0, 1),  (1, 1),
    ]
    while remaining:
        seed = remaining.pop()
        component = {seed}
        queue = deque([seed])
        while queue:
            x, y = queue.popleft()
            for dx, dy in neighbors:
                candidate = (x + dx, y + dy)
                if candidate in remaining:
                    remaining.remove(candidate)
                    component.add(candidate)
                    queue.append(candidate)
        found.append(component)
    return found


def suspicious_seams(path: Path, minimum_area: int, minimum_run: int) -> list[str]:
    seams = []
    for component in connected_components(opaque_pixels(path)):
        if len(component) < minimum_area:
            continue
        xs = [x for x, _ in component]
        ys = [y for _, y in component]
        top, bottom = min(ys), max(ys)
        edges = {
            f"top y={top}": [x for x, y in component if y == top],
            f"bottom y={bottom}": [x for x, y in component if y == bottom],
        }
        for label, positions in edges.items():
            run = longest_run(positions)
            if run >= minimum_run:
                seams.append(f"{label} run={run}px")
    return seams


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--minimum-area", type=int, default=700)
    parser.add_argument("--minimum-run", type=int, default=60)
    args = parser.parse_args()

    if not shutil.which("magick"):
        parser.error("ImageMagick `magick` is required")

    failures = 0
    for path in sorted(args.directory.glob("[0-9][0-9].png")):
        seams = suspicious_seams(path, args.minimum_area, args.minimum_run)
        if seams:
            failures += 1
            print(f"FAIL: {path.name}: suspicious straight artwork edge ({', '.join(seams)})")
    print(f"Crop-seam audit: {failures} suspicious sticker(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
