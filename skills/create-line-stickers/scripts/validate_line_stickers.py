#!/usr/bin/env python3
"""Preflight a directory of static LINE sticker PNGs without dependencies."""

from __future__ import annotations

import argparse
import binascii
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ALLOWED_COUNTS = {8, 16, 24, 32, 40}
MAX_BYTES = 1_000_000
MAX_ZIP_BYTES = 60_000_000
COPYRIGHT = "© WhatAForkStudio"


def line_count(value: str) -> int:
    return sum(1 if ord(character) < 128 else 2 for character in value)


def metadata_field(markdown: str, section: str, field: str) -> str | None:
    match = re.search(
        rf"^## {re.escape(section)}\s*$([\s\S]*?)(?=^## |\Z)",
        markdown,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    field_match = re.search(
        rf"^\*\*{re.escape(field)}:\*\*\s*(.+?)\s*$",
        match.group(1),
        flags=re.MULTILINE,
    )
    return field_match.group(1).strip() if field_match else None


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
    parser.add_argument(
        "directory",
        type=Path,
        help="outer pack folder (preferred) or legacy folder containing sticker PNGs",
    )
    args = parser.parse_args()
    folder = args.directory
    errors: list[str] = []
    warnings: list[str] = []

    if not folder.is_dir():
        print(f"ERROR: not a directory: {folder}")
        return 2

    expected_image_folder = folder / f"{folder.name}-stickers"
    package_mode = expected_image_folder.is_dir()
    image_folder = expected_image_folder if package_mode else folder
    metadata_path = folder / "metadata.md"
    zip_path = folder / f"{folder.name}-stickers.zip"

    if package_mode:
        allowed_root_names = {expected_image_folder.name, "metadata.md", zip_path.name}
        unexpected_root = sorted(path.name for path in folder.iterdir() if path.name not in allowed_root_names)
        if unexpected_root:
            errors.append(f"unexpected pack-root entries: {', '.join(unexpected_root)}")
        non_files = sorted(path.name for path in image_folder.iterdir() if not path.is_file())
        if non_files:
            errors.append(f"sticker image directory contains non-files: {', '.join(non_files)}")

    all_files = [path for path in image_folder.iterdir() if path.is_file()]
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
    non_pngs = sorted(path.name for path in all_files if path.suffix.lower() != ".png")
    if package_mode and non_pngs:
        errors.append(f"sticker image directory contains non-PNG files: {', '.join(non_pngs)}")

    if not metadata_path.is_file():
        (errors if package_mode else warnings).append("metadata.md is missing")
    elif package_mode:
        markdown = metadata_path.read_text(encoding="utf-8")
        required_fields = [
            ("English", "Title", 40),
            ("English", "Description", 160),
            ("Thai", "Title", 40),
            ("Thai", "Description", 160),
        ]
        for section, field, maximum in required_fields:
            value = metadata_field(markdown, section, field)
            if not value:
                errors.append(f"metadata missing {section} {field}")
            elif line_count(value) > maximum:
                errors.append(
                    f"metadata {section} {field} counts as {line_count(value)}; maximum is {maximum}"
                )

        categories_path = Path(__file__).parent.parent / "references" / "line-categories.json"
        categories = json.loads(categories_path.read_text(encoding="utf-8"))
        style = metadata_field(markdown, "Categories", "Style Category")
        character = metadata_field(markdown, "Categories", "Character Category")
        if style not in categories["style_categories"]:
            errors.append(f"invalid or missing Style Category: {style or 'none'}")
        if character not in categories["character_categories"]:
            errors.append(f"invalid or missing Character Category: {character or 'none'}")

        copyright_match = re.search(r"^## Copyright\s*$\n([^\n]+)", markdown, flags=re.MULTILINE)
        if not copyright_match or copyright_match.group(1).strip() != COPYRIGHT:
            errors.append(f"copyright must be exactly: {COPYRIGHT}")

    if package_mode:
        if not zip_path.is_file():
            errors.append(f"missing {zip_path.name}")
        elif zip_path.stat().st_size > MAX_ZIP_BYTES:
            errors.append(f"{zip_path.name}: exceeds 60 MB")
        else:
            try:
                with zipfile.ZipFile(zip_path) as archive:
                    archived = sorted(name for name in archive.namelist() if not name.endswith("/"))
                    expected_archived = sorted(path.name for path in all_files)
                    if archived != expected_archived:
                        errors.append("ZIP contents do not exactly match the sticker image directory")
                    corrupt = archive.testzip()
                    if corrupt:
                        errors.append(f"ZIP contains a corrupt file: {corrupt}")
            except (OSError, zipfile.BadZipFile) as exc:
                errors.append(f"invalid ZIP: {exc}")

    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    print(f"Checked {len(numbered)} stickers: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
