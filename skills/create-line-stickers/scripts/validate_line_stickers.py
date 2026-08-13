#!/usr/bin/env python3
"""Preflight a directory of static LINE sticker PNGs without dependencies."""

from __future__ import annotations

import argparse
import binascii
import re
import struct
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ALLOWED_COUNTS = {8, 16, 24, 32, 40}
MAX_BYTES = 1_000_000


def png_header(path: Path) -> tuple[int, int, int]:
    with path.open("rb") as handle:
        signature = handle.read(8)
        length_data = handle.read(4)
        chunk_type = handle.read(4)
        data = handle.read(13)
        crc_data = handle.read(4)
    if signature != PNG_SIGNATURE or len(length_data) != 4:
        raise ValueError("not a PNG")
    length = struct.unpack(">I", length_data)[0]
    if chunk_type != b"IHDR" or length != 13 or len(data) != 13 or len(crc_data) != 4:
        raise ValueError("invalid PNG IHDR")
    expected_crc = struct.unpack(">I", crc_data)[0]
    if binascii.crc32(chunk_type + data) & 0xFFFFFFFF != expected_crc:
        raise ValueError("corrupt PNG IHDR")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data
    )
    if width == 0 or height == 0 or compression != 0 or filtering != 0:
        raise ValueError("unsupported or invalid PNG header")
    return width, height, color_type


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, help="folder containing main.png, tab.png, and numbered PNGs")
    args = parser.parse_args()
    folder = args.directory
    errors: list[str] = []
    warnings: list[str] = []

    if not folder.is_dir():
        print(f"ERROR: not a directory: {folder}")
        return 2

    all_files = [path for path in folder.iterdir() if path.is_file()]
    pngs = {path.name: path for path in all_files if path.suffix.lower() == ".png"}
    numbered = sorted(
        (path for name, path in pngs.items() if re.fullmatch(r"\d{2}\.png", name)),
        key=lambda path: path.name,
    )

    if len(numbered) not in ALLOWED_COUNTS:
        errors.append(f"sticker count is {len(numbered)}; expected one of {sorted(ALLOWED_COUNTS)}")
    expected_names = [f"{index:02d}.png" for index in range(1, len(numbered) + 1)]
    actual_names = [path.name for path in numbered]
    if actual_names != expected_names:
        errors.append(f"numbered stickers must be contiguous from 01.png; found {', '.join(actual_names) or 'none'}")

    required: list[tuple[str, tuple[int, int] | None]] = [
        ("main.png", (240, 240)),
        ("tab.png", (96, 74)),
    ] + [(path.name, None) for path in numbered]

    for name, exact_size in required:
        path = pngs.get(name)
        if path is None:
            errors.append(f"missing {name}")
            continue
        if path.stat().st_size > MAX_BYTES:
            errors.append(f"{name}: {path.stat().st_size} bytes exceeds 1 MB")
        try:
            width, height, color_type = png_header(path)
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")
            continue
        if exact_size and (width, height) != exact_size:
            errors.append(f"{name}: {width}x{height}; expected {exact_size[0]}x{exact_size[1]}")
        if exact_size is None:
            if width > 370 or height > 320:
                errors.append(f"{name}: {width}x{height} exceeds 370x320")
            if width % 2 or height % 2:
                errors.append(f"{name}: width and height must both be even")
        if color_type not in (4, 6):
            errors.append(f"{name}: PNG color type {color_type} has no alpha channel")

    known = {name for name, _ in required}
    unexpected_pngs = sorted(set(pngs) - known)
    if unexpected_pngs:
        warnings.append(f"unrecognized PNG files: {', '.join(unexpected_pngs)}")
    if not (folder / "metadata.md").is_file():
        warnings.append("metadata.md is missing")

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    print(f"Checked {len(numbered)} stickers: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
