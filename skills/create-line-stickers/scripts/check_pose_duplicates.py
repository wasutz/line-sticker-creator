#!/usr/bin/env python3
"""Flag near-duplicate sticker poses via an alpha-channel dHash comparison."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from itertools import combinations
from pathlib import Path

PIXEL = re.compile(r"^(\d+),(\d+): \((\d+)")

HASH_WIDTH = 9
HASH_HEIGHT = 8


def alpha_grid(path: Path) -> list[list[int]]:
    result = subprocess.run(
        [
            "magick", str(path),
            "-alpha", "extract",
            "-resize", f"{HASH_WIDTH}x{HASH_HEIGHT}!",
            "-depth", "8",
            "txt:-",
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    grid = [[0] * HASH_WIDTH for _ in range(HASH_HEIGHT)]
    for line in result.stdout.splitlines():
        match = PIXEL.match(line)
        if match:
            x, y, value = map(int, match.groups())
            grid[y][x] = value
    return grid


def dhash(path: Path) -> int:
    grid = alpha_grid(path)
    bits = 0
    for y in range(HASH_HEIGHT):
        for x in range(HASH_WIDTH - 1):
            bits = (bits << 1) | (1 if grid[y][x] > grid[y][x + 1] else 0)
    return bits


def hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Max Hamming distance (of 64 bits) flagged as a near-duplicate pose",
    )
    args = parser.parse_args()

    if not shutil.which("magick"):
        parser.error("ImageMagick `magick` is required")

    paths = sorted(args.directory.glob("[0-9][0-9].png"))
    hashes = {path: dhash(path) for path in paths}

    failures = 0
    for left, right in combinations(paths, 2):
        distance = hamming(hashes[left], hashes[right])
        if distance <= args.threshold:
            failures += 1
            print(f"FAIL: {left.name} and {right.name}: near-duplicate pose (hamming={distance})")
    print(f"Pose-duplicate audit: {failures} suspicious pair(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
