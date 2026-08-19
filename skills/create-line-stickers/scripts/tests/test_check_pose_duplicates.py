#!/usr/bin/env python3
"""Tests for check_pose_duplicates.py — run directly, no pytest required."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check_pose_duplicates.py"


def run_script(directory: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(directory)],
        capture_output=True,
        text=True,
    )


def draw(path: Path, draw_command: str) -> None:
    subprocess.run(
        ["magick", "-size", "300x300", "xc:none", "-fill", "black", "-draw", draw_command, str(path)],
        check=True,
    )


class CheckPoseDuplicatesTest(unittest.TestCase):
    def test_flags_identical_poses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            draw(directory / "01.png", "circle 150,150 150,60")
            draw(directory / "02.png", "circle 150,150 150,60")
            result = run_script(directory)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("near-duplicate pose", result.stdout)

    def test_passes_distinct_poses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            draw(directory / "01.png", "circle 150,150 150,60")
            draw(directory / "02.png", "rectangle 10,10 60,60")
            result = run_script(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_passes_similarly_composed_but_distinct_poses(self) -> None:
        """Two stickers sharing the same overall layout (top text block, centered
        body) but with a distinguishing accent shape near opposite canvas edges —
        the shape of every real sticker pack. This is the case the unnormalized
        whole-canvas dHash used to false-flag: it hashed near-identical (hamming=5
        of 64) under the old algorithm despite depicting clearly different poses.
        """
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            common = [
                "-size", "370x320", "xc:none", "-fill", "black",
                "-draw", "rectangle 60,20 310,55",
                "-draw", "circle 185,200 185,120",
            ]
            subprocess.run(
                ["magick", *common, "-draw", "circle 30,150 30,115", str(directory / "01.png")],
                check=True,
            )
            subprocess.run(
                ["magick", *common, "-draw", "circle 340,150 340,115", str(directory / "02.png")],
                check=True,
            )
            result = run_script(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_directory_reports_error(self) -> None:
        result = run_script(Path("/nonexistent-pose-duplicate-check-directory"))
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("not a directory", result.stderr.lower())

    def test_ignores_non_numbered_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            draw(directory / "01.png", "circle 150,150 150,60")
            draw(directory / "main.png", "circle 150,150 150,60")
            result = run_script(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
