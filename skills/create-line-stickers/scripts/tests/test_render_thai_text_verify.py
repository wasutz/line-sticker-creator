#!/usr/bin/env python3
"""Tests for render_thai_text.py --verify — run directly, no pytest required."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "render_thai_text.py"


def run_render(out_path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--text", "ทดสอบ", "--out", str(out_path), *extra_args],
        capture_output=True,
        text=True,
    )


class RenderThaiTextVerifyTest(unittest.TestCase):
    def test_flags_edge_clipped_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "clipped.png"
            result = run_render(
                out_path,
                "--width", "200",
                "--height", "20",
                "--font-size", "80",
                "--verify",
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("clipped", result.stdout.lower())

    def test_passes_clean_render(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "clean.png"
            result = run_render(
                out_path,
                "--width", "350",
                "--height", "120",
                "--font-size", "30",
                "--verify",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_verify_flag_always_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_path = Path(tmp) / "unverified.png"
            result = run_render(out_path, "--width", "200", "--height", "20", "--font-size", "80")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
