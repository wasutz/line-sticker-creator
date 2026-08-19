# One-Click LINE Sticker Pack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `make-line-sticker-pack` skill that runs the existing two-skill pipeline (`prepare-line-sticker-metadata` → `create-line-stickers`) unattended from just a character name and theme words, with automated defaults, a reference-sheet critic gate, and a per-sticker critic loop replacing today's human approval and visual-review steps.

**Architecture:** Two small standalone ImageMagick-based scripts (pose-duplicate detector, Thai-text edge-clip verifier) slot into the existing scripts/ directory next to `check_sticker_crop_seams.py`. A new orchestrator skill's `SKILL.md` documents token resolution, fixed defaults, the 7-stage pipeline, and the critic loop, and delegates to the two existing skills' own instructions rather than duplicating them. No existing file's behavior changes for its current callers.

**Tech Stack:** Python 3 (stdlib only — argparse, subprocess, pathlib), ImageMagick (`magick` CLI), `rsvg-convert`, `unittest` (stdlib test runner; no pytest in this repo).

**Spec:** `docs/superpowers/specs/2026-08-19-one-click-sticker-pack-design.md`

## Global Constraints

- No PIL/numpy/new pip dependencies — every existing script in `skills/create-line-stickers/scripts/` shells out to `magick`; new scripts must match that pattern exactly.
- No pytest in this repo — tests use stdlib `unittest`, invoked as standalone scripts (not as an importable package, since `create-line-stickers` is a hyphenated directory name and cannot be `import`ed as a Python package).
- Copyright is always exactly `© WhatAForkStudio` (verbatim, all skills).
- Default sticker count is 40; valid counts elsewhere in the repo are only 8, 16, 24, 32, 40.
- Existing skills (`create-line-stickers`, `prepare-line-sticker-metadata`, `research-line-sticker-concepts`) must not change behavior for their current manual invocations — the new skill only adds a layer on top.
- Retry budgets (from spec): 2 re-renders per numbered sticker, 3 re-renders for `main.png`/`tab.png`, 3 re-renders for the reference sheet (hard stop on exhaustion).

---

## File Structure

```
skills/create-line-stickers/scripts/
├── check_pose_duplicates.py          # NEW — dHash near-duplicate pose detector
├── render_thai_text.py               # MODIFIED — add --verify edge-clip check
└── tests/
    ├── test_check_pose_duplicates.py # NEW
    └── test_render_thai_text_verify.py # NEW

skills/make-line-sticker-pack/
├── SKILL.md                          # NEW — orchestrator skill
└── agents/
    └── openai.yaml                   # NEW

README.md                             # MODIFIED — one-click section added at top
```

---

## Task 1: Pose-duplicate detector script

**Files:**
- Create: `skills/create-line-stickers/scripts/check_pose_duplicates.py`
- Test: `skills/create-line-stickers/scripts/tests/test_check_pose_duplicates.py`

**Interfaces:**
- Produces: CLI `check_pose_duplicates.py <directory> [--threshold N]` — exit 0 if no pair of numbered stickers (`[0-9][0-9].png` in `<directory>`) has an alpha-channel dHash Hamming distance `<= threshold` (default 10, out of 64 bits); exit 1 and one `FAIL: ...` line per offending pair otherwise, plus a summary line `Pose-duplicate audit: N suspicious pair(s)`. Matches the existing print/exit-code contract of `check_sticker_crop_seams.py`.

- [ ] **Step 1: Write the failing tests**

Create `skills/create-line-stickers/scripts/tests/test_check_pose_duplicates.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 skills/create-line-stickers/scripts/tests/test_check_pose_duplicates.py -v`
Expected: FAIL — `check_pose_duplicates.py` does not exist (`FileNotFoundError` / non-zero from `run_script`, surfaced as an assertion failure since `SCRIPT` path is missing).

- [ ] **Step 3: Write the implementation**

Create `skills/create-line-stickers/scripts/check_pose_duplicates.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 skills/create-line-stickers/scripts/tests/test_check_pose_duplicates.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/create-line-stickers/scripts/check_pose_duplicates.py skills/create-line-stickers/scripts/tests/test_check_pose_duplicates.py
git commit -m "Add pose-duplicate detector script for sticker QA"
```

---

## Task 2: Thai-text edge-clip verification

**Files:**
- Modify: `skills/create-line-stickers/scripts/render_thai_text.py`
- Test: `skills/create-line-stickers/scripts/tests/test_render_thai_text_verify.py`

**Interfaces:**
- Consumes: `opaque_pixels(path: Path) -> set[tuple[int, int]]` from `skills/create-line-stickers/scripts/check_sticker_crop_seams.py` (already defined, already imported elsewhere in this codebase by `validate_line_stickers.py`).
- Produces: new `--verify` flag on `render_thai_text.py`. When passed, after rendering the script checks whether any opaque pixel touches the canvas border (`x == 0`, `y == 0`, `x == width - 1`, `y == height - 1`); if so it prints a `FAIL: ...` line and returns 1, otherwise it prints a pass line and returns 0. Without `--verify`, behavior is unchanged (always returns 0 after rendering, as today).

- [ ] **Step 1: Write the failing tests**

Create `skills/create-line-stickers/scripts/tests/test_render_thai_text_verify.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python3 skills/create-line-stickers/scripts/tests/test_render_thai_text_verify.py -v`
Expected: `test_flags_edge_clipped_render` and `test_passes_clean_render` FAIL with `error: unrecognized arguments: --verify` (argparse exits 2); `test_no_verify_flag_always_passes` PASSES already (existing behavior).

- [ ] **Step 3: Write the implementation**

Edit `skills/create-line-stickers/scripts/render_thai_text.py`. Add the import (after the existing `from pathlib import Path` line):

```python
from pathlib import Path

from check_sticker_crop_seams import opaque_pixels
```

Add the `--verify` argument (after the `--stroke-width` argument):

```python
    parser.add_argument("--stroke-width", type=float, default=4)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Fail if rendered ink touches the canvas edge (proxy for clipped tone marks/vowels)",
    )
    args = parser.parse_args()
```

(remove the old standalone `args = parser.parse_args()` line that followed `--stroke-width` so it isn't duplicated)

Replace the final two lines of `main()`:

```python
        subprocess.run([renderer, "-o", str(output), source.name], check=True)
    return 0
```

with:

```python
        subprocess.run([renderer, "-o", str(output), source.name], check=True)

    if args.verify:
        pixels = opaque_pixels(output)
        edge_pixels = [
            (x, y)
            for x, y in pixels
            if x == 0 or y == 0 or x == args.width - 1 or y == args.height - 1
        ]
        if edge_pixels:
            print(f"FAIL: {output}: rendered ink touches canvas edge ({len(edge_pixels)}px) — likely clipped mark")
            return 1
        print(f"Text headroom check passed: {output}")
    return 0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 skills/create-line-stickers/scripts/tests/test_render_thai_text_verify.py -v`
Expected: all 3 tests PASS.

Also confirm the unmodified existing call pattern (no `--verify`) still works standalone:
Run: `python3 skills/create-line-stickers/scripts/render_thai_text.py --text "สวัสดี" --out /tmp/smoke.png`
Expected: exit 0, `/tmp/smoke.png` created, no output printed (matches pre-change behavior).

- [ ] **Step 5: Commit**

```bash
git add skills/create-line-stickers/scripts/render_thai_text.py skills/create-line-stickers/scripts/tests/test_render_thai_text_verify.py
git commit -m "Add --verify edge-clip check to render_thai_text.py"
```

---

## Task 3: `make-line-sticker-pack` orchestrator skill

**Files:**
- Create: `skills/make-line-sticker-pack/SKILL.md`

**Interfaces:**
- Consumes: `skills/prepare-line-sticker-metadata/SKILL.md` workflow (unmodified), `skills/create-line-stickers/SKILL.md` workflow (unmodified), `skills/create-line-stickers/scripts/validate_line_stickers.py`, `skills/create-line-stickers/scripts/check_sticker_crop_seams.py` (unmodified), `skills/create-line-stickers/scripts/check_pose_duplicates.py` (Task 1), `skills/create-line-stickers/scripts/render_thai_text.py --verify` (Task 2), `skills/create-line-stickers/references/campaigns/*.md`, `characters/*/`.
- Produces: `output/<pack-name>/auto-run-report.md` (new artifact type — this skill's addition to the standard deliverables), plus the standard `create-line-stickers` deliverables (`metadata.md`, image directory, ZIP) at the same paths that skill already uses.

- [ ] **Step 1: Write `skills/make-line-sticker-pack/SKILL.md`**

```markdown
---
name: make-line-sticker-pack
description: One-click orchestrator for a full static LINE sticker pack. Takes only a character name and one or more theme words, applies fixed defaults, and runs prepare-line-sticker-metadata then create-line-stickers back to back with no mid-run questions and no required human approval, using an automated reference-sheet gate and per-sticker critic loop in place of manual review. Use when the user wants a complete pack built end-to-end from a short prompt, e.g. "$make-line-sticker-pack bunbun lazy".
---

# Make LINE Sticker Pack (one-click)

Run the full pipeline unattended from `$make-line-sticker-pack <character> <theme-word> [<theme-word> ...]` and leave a validated, packaged pack under `<workspace-root>/output/<pack-name>/`, exactly as `create-line-stickers` does, plus an `auto-run-report.md` documenting every automated decision.

This skill does not replace `prepare-line-sticker-metadata` or `create-line-stickers`; it drives them with defaults so neither has to ask a question. Read this skill's referenced sections of both before running their workflows — do not duplicate their instructions here, follow them.

## 1. Resolve

Classify every token after the skill name, independent of order:

- A token matching a folder name under `characters/` is a character. One match is solo mode. Two matches is couple mode: the token appearing first in the invocation is partner A, the second is partner B.
- A token matching a filename stem under `skills/create-line-stickers/references/campaigns/` (e.g. `lazy` matches `lazy-campaign-2026.md`) turns on campaign mode for that file. If more than one theme token matches a campaign file, use the first match in invocation order and note the others were ignored in the run report.
- Every other token joins a free-text theme/wording lens passed to `prepare-line-sticker-metadata` as creative direction (equivalent to what a user would otherwise type by hand).
- Zero character-token matches, or a character token with no matching folder under `characters/`: **hard stop.** Report the exact path checked (`characters/<token>/`) and do not proceed.

Build a decision record before continuing:

| Field | Value |
|---|---|
| Character(s) | resolved folder path(s) |
| Theme tokens | the non-character tokens, in invocation order |
| Campaign | matched campaign file path, or none |
| Sticker count | 40 |
| Language | Thai wording; bilingual (English + Thai) metadata |
| Pack slug | `<character>-<theme-tokens-joined-by-hyphen>-th-40`; if `output/<slug>/` already exists, append `-v2`, `-v3`, ... until free |
| Copyright | `© WhatAForkStudio` |

## 2. Plan

Follow `skills/prepare-line-sticker-metadata/SKILL.md`'s workflow, supplying the decision record as the answers to every question it would otherwise ask (character(s), count, language, theme, output location, campaign). Do not stop to ask the user anything the decision record already answers. This produces `metadata.md` at the pack directory it resolves to (`output/<pack-slug>/metadata.md` given the pack slug above).

## 3. Reference gate

Before rendering any numbered sticker:

- If `characters/<name>/reference-sheet.png` (or another already-approved reference image serving that role in the character's folder) exists, reuse it directly. Skip generation for this stage.
- Otherwise, generate one approved character/style reference exactly as `create-line-stickers/SKILL.md` step 5 describes (pairing reference for couple mode), then run it through the critic loop (Section 5 below) against the character-library or inherit-and-delta brief.
- Retry budget for the reference sheet is **3** re-generations (4 attempts total). If it still fails the critic loop after budget is exhausted: **hard stop.** Do not proceed to rendering — a failed reference would be inherited by all 40 stickers. Report which checks failed on the final attempt.

## 4. Render

Follow `create-line-stickers/SKILL.md` steps 6-7 (rendering, grid extraction, Thai typography) in batches of 8 numbered stickers at a time. Run every sticker in a batch through the critic loop (Section 5) before treating the batch as accepted and moving to the next batch.

## 5. Critic loop

Applied to the reference sheet (Section 3) and to every rendered numbered sticker (Section 4), cheapest checks first, stopping at the first failure:

1. Run `python3 <skill-directory>/../create-line-stickers/scripts/validate_line_stickers.py` and `check_sticker_crop_seams.py` (structural failures: dimensions, crop seams). For the reference sheet, skip these two (they check pack-level and numbered-sticker conventions that don't apply to a single reference image); go straight to the vision check.
2. For a rendered numbered sticker, run `check_pose_duplicates.py` against the stickers already accepted in this pack (near-duplicate pose).
3. If the sticker carries rendered Thai lettering produced via `render_thai_text.py`, that render must have used `--verify` and passed (edge-clipped ink is a failure here, not a separate re-check).
4. Read the candidate image at 1:1 against the accepted reference sheet (and pairing reference, in couple mode). Judge: character identity drift from the reference, expression/pose reads as the plan intends, text (if any) is legible, ~10px transparent breathing room around the composition, pose is visually distinct from every already-accepted sticker in this pack.

Any failure at any step: re-render that one sticker (or the reference sheet, in Section 3) with a targeted correction note describing exactly what failed, and try again against the same retry budget.

**Retry budgets:** 2 re-renders per numbered sticker (3 attempts total). 3 re-renders for `main.png`/`tab.png` (4 attempts total — they represent the whole pack in the store listing). 3 re-renders for the reference sheet, per Section 3 (hard stop on exhaustion).

**Budget exhaustion for a numbered sticker or main/tab (not the reference sheet):** keep the best-scoring attempt, record it as `unresolved` with the specific failed check(s) in the run report, and continue the pipeline. Never mark an unresolved sticker as passed.

## 6. Assemble

Follow `create-line-stickers/SKILL.md` step 7 for `main.png`/`tab.png`, then step 8 for finalizing bilingual metadata and selecting exactly one style category and one character category from `references/line-categories.json` based on the finished set.

## 7. Validate, package, and report

Follow `create-line-stickers/SKILL.md` step 9 (`validate_line_stickers.py`, ZIP packaging) plus `check_pose_duplicates.py` across the full finished set as a final pass. Resolve every validator error; for warnings and any remaining `unresolved` stickers, carry them into the report rather than resolving them silently.

Write `<workspace-root>/output/<pack-name>/auto-run-report.md`:

```markdown
# Auto-run report: <pack-name>

## Decision record
<the table from Section 1, as resolved>

## Reference gate
<reused existing reference-sheet.png | generated in N attempt(s) | which checks failed on earlier attempts>

## Sticker outcomes
| Sticker | Status | Notes |
|---|---|---|
| 01.png | accepted (attempt 1) | |
| 02.png | unresolved | failed: pose-duplicate vs 07.png on all 3 attempts |
...

## Validator result
<validate_line_stickers.py output summary>

## Human-review risks
<anything unresolved, plus the standing statement that automated checks cannot guarantee LINE approval>
```

## Completion gate

Finish only when: the decision record resolved with no unanswered field; the reference gate passed (reused or generated) or the run stopped there with a clear report of why; every numbered sticker plus `main.png`/`tab.png` is either accepted or explicitly `unresolved` in the report; the selected count is 40; the exact outer-pack structure exists at `output/<pack-name>/` per `create-line-stickers/SKILL.md`'s Deliverables section; `validate_line_stickers.py` and the crop-seam audit report zero errors; `auto-run-report.md` exists and is non-empty; and the report states plainly that automated checks cannot guarantee LINE approval.
```

- [ ] **Step 2: Verify structure against the spec**

Confirm the file: has YAML frontmatter with `name` and `description`; documents all 7 stages from the spec (Resolve, Plan, Reference gate, Render, Assemble, Validate+package, Report) — here Section 5 (Critic loop) is factored out as its own section referenced by both Section 3 and Section 4, so check content coverage rather than a literal 7-heading count; states both hard-stop conditions (unresolvable character token; reference-gate budget exhaustion); states all three retry budgets (2 / 3 / 3); references `check_pose_duplicates.py` and `render_thai_text.py --verify` from Tasks 1-2. No open step should be needed — this is a read-through check, not a script run.

- [ ] **Step 3: Commit**

```bash
git add skills/make-line-sticker-pack/SKILL.md
git commit -m "Add make-line-sticker-pack orchestrator skill"
```

---

## Task 4: Skill metadata and README entry point

**Files:**
- Create: `skills/make-line-sticker-pack/agents/openai.yaml`
- Modify: `README.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks — this is the final documentation/wiring task.

- [ ] **Step 1: Create `skills/make-line-sticker-pack/agents/openai.yaml`**

Matches the existing pattern in `skills/create-line-stickers/agents/openai.yaml` and `skills/research-line-sticker-concepts/agents/openai.yaml`:

```yaml
interface:
  display_name: "Make LINE Sticker Pack"
  short_description: "One-click LINE sticker pack from a character and theme"
  default_prompt: "Use $make-line-sticker-pack to build, validate, and package a complete static LINE sticker pack unattended from just a character name and theme words."
```

- [ ] **Step 2: Add a one-click section to `README.md`**

Read the current `README.md` first (it starts with a "Plan metadata before creating artwork" section). Insert a new section at the very top, before the `# Line Sticker Creator Skill` heading's first existing subsection, so the file becomes:

```markdown
# Line Sticker Creator Skill

## One-click: character + theme, no questions asked

```text
Use $make-line-sticker-pack to build a pack for "bunbun" with theme "lazy".
```

Or the equivalent short form once the skill is installed:

```text
$make-line-sticker-pack bunbun lazy
```

Resolves the character against `characters/bunbun/`, matches `lazy` against `skills/create-line-stickers/references/campaigns/lazy-campaign-2026.md` if present, and otherwise treats every non-character token as wording direction. Runs `prepare-line-sticker-metadata` then `create-line-stickers` back to back with fixed defaults (40 stickers, Thai + English bilingual metadata, `© WhatAForkStudio`), an automated reference-sheet check, and a per-sticker critic loop in place of manual approval. Delivers the same `output/<pack-name>/` structure as the manual flow below, plus `auto-run-report.md` documenting what was auto-decided and any sticker that needed manual follow-up.

For planning-only control, prepared-metadata workflows, or any of the modes below (couples, variants, style-only, two-reference), use the manual flow.

## Plan metadata before creating artwork
```

(the rest of the existing file follows unchanged after this insertion point — do not otherwise modify existing sections)

- [ ] **Step 3: Commit**

```bash
git add skills/make-line-sticker-pack/agents/openai.yaml README.md
git commit -m "Wire up make-line-sticker-pack skill metadata and README entry point"
```

---

## Task 5: End-to-end verification run

**Files:**
- None created or modified by this task — this task exercises Tasks 1-4's output against a real invocation.

**Interfaces:**
- Consumes: `$make-line-sticker-pack bunbun lazy` (the full skill built in Tasks 1-4), the existing `characters/bunbun/` folder, the existing `skills/create-line-stickers/references/campaigns/lazy-campaign-2026.md` campaign file.
- Produces: a real pack under `output/bunbun-lazy-th-40/` (or the next free `-vN` suffix if that slug is already taken) for manual/human inspection; this task's own deliverable is the verification report below, not new code.

**Note:** this task requires actually invoking the `make-line-sticker-pack` skill in a live Claude Code session with image-generation (`imagegen`) tool access — it cannot be run as a plain shell command by a coding-only subagent. If the executor lacks that access, stop after Tasks 1-4, report that Task 5 needs to be run by an operator with `imagegen` access, and hand back the exact command below.

- [ ] **Step 1: Run the skill**

In a Claude Code session with access to this repository and the `imagegen` skill, run:

```
$make-line-sticker-pack bunbun lazy
```

Let it run to completion without answering any questions (per the completion gate in Task 3, it should not ask any).

- [ ] **Step 2: Check the deliverables against the completion gate**

Verify, in order:

1. `output/bunbun-lazy-th-40/` (or the actual resolved slug) exists with the exact structure from `create-line-stickers/SKILL.md`'s Deliverables section: `metadata.md`, `<pack-name>-stickers/` containing `main.png`, `tab.png`, `01.png`...`40.png`, and `<pack-name>-stickers.zip`.
2. `output/<pack-name>/auto-run-report.md` exists and is non-empty, with all five sections from Task 3 Section 7's template present.
3. Run: `python3 skills/create-line-stickers/scripts/validate_line_stickers.py output/<pack-name>`
   Expected: zero errors reported.
4. Run: `python3 skills/create-line-stickers/scripts/check_pose_duplicates.py output/<pack-name>/<pack-name>-stickers`
   Expected: zero suspicious pairs, or every flagged pair is already listed as `unresolved` in `auto-run-report.md`.
5. Open a handful of numbered PNGs and compare against `characters/bunbun/reference-sheet.png` (or whichever reference the run used) to sanity-check the critic loop actually caught character drift rather than rubber-stamping.
6. Confirm `metadata.md`'s copyright field is exactly `© WhatAForkStudio` and its sticker count is 40.

- [ ] **Step 3: Report the outcome**

Summarize pass/fail against each of the 6 checks above. If every check passes, the plan is complete. If any check fails, that is a bug in Tasks 1-4 (not a plan gap) — fix the relevant script or `SKILL.md` section, re-run from Step 1, and do not consider the plan complete until this task passes end to end.

No commit for this task unless Step 3 required a fix, in which case commit that fix separately with a message describing what the end-to-end run caught.

---

## Self-Review Notes

- **Spec coverage:** token resolution (Task 3 §1), decision defaults table (Task 3 §1), reference gate + reuse-if-exists + hard stop (Task 3 §3), render batching (Task 3 §4), critic loop with all three retry budgets (Task 3 §5), assemble/categories (Task 3 §6), validate+package+report (Task 3 §7), new scripts (Tasks 1-2), README/yaml wiring (Task 4), end-to-end test (Task 5) — every spec section maps to a task.
- **Type/name consistency checked:** `check_pose_duplicates.py <directory> [--threshold N]` (Task 1) matches the call in Task 3 §5/§7. `render_thai_text.py --verify` (Task 2) matches the requirement referenced in Task 3 §5.3. `opaque_pixels` imported from `check_sticker_crop_seams` in Task 2 matches its actual existing signature in that file.
- **No placeholders:** all code blocks are complete, runnable content; the `SKILL.md` in Task 3 is the full file text, not a summary.
