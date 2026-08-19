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

    def test_ignores_non_numbered_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            draw(directory / "01.png", "circle 150,150 150,60")
            draw(directory / "main.png", "circle 150,150 150,60")
            result = run_script(directory)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
