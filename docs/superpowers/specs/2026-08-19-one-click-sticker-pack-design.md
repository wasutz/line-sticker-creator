# One-click LINE sticker pack: `make-line-sticker-pack`

**Date:** 2026-08-19
**Status:** Approved for planning

## Problem

Today a full pack needs two manual skill invocations chained by hand
(`prepare-line-sticker-metadata` → copy the returned path → `create-line-stickers`),
a prompt that spells out count, language, campaign, and copyright, a human
approval gate on the character/style reference before rendering continues, and
a subjective 1:1 + light/dark visual review of every sticker at the end (see
`skills/create-line-stickers/SKILL.md` steps 1, 19, 25, 32). None of this can
run unattended.

## Goal

A single invocation —

```
$make-line-sticker-pack <character> <theme-word> [<theme-word> ...]
```

— produces a validated, packaged 40-piece pack under `output/<pack>/` with no
mid-run questions and no required human approval step, by wrapping the three
existing skills and adding automated judgment where a human used to look.

Example: `$make-line-sticker-pack bunbun lazy` resolves `bunbun` against
`characters/bunbun/`, matches `lazy` against
`skills/create-line-stickers/references/campaigns/lazy-campaign-2026.md`,
and runs the full pipeline unattended.

## Non-goals

- Replacing the three existing skills or their manual entry points (README
  flows keep working as-is).
- Guaranteeing LINE approval — automated checks remain a proxy, as today's
  completion gate already states.
- Couple-mode auto-detection from more than two character tokens, multi-theme
  campaign conflicts (first campaign match wins; documented, not solved).

## Token resolution

Every token after the skill name is classified independently, order-insensitive:

- Token matches a folder under `characters/` → character. One match = solo
  mode. Two matches = couple mode (partner A = first token position, partner
  B = second).
- Token matches a filename stem under
  `skills/create-line-stickers/references/campaigns/*.md` (e.g. `lazy` →
  `lazy-campaign-2026.md`) → campaign mode turns on, that file is read per
  existing campaign rules in `create-line-stickers/SKILL.md`.
- Every other token joins the theme/wording lens passed to
  `prepare-line-sticker-metadata` as free-text direction.
- Zero character tokens, or a character token with no matching folder → hard
  stop, report the exact path checked (matches existing character-library
  mode error behavior).

## Decision defaults

Replaces the 12-line manual prompt (`README.md` campaign example) with fixed
defaults; nothing here is asked of the user:

| Field | Default |
|---|---|
| Sticker count | 40 |
| Language | Thai wording; bilingual (English + Thai) metadata |
| Pack slug | `<character>-<theme-tokens-joined>-th-40`; on collision with an existing `output/` dir, append `-v2`, `-v3`, ... |
| Copyright | `© WhatAForkStudio` (fixed, matches every existing skill) |
| Campaign | on only if a theme token matched a campaign file; off otherwise |
| Categories | selected at the assemble stage from finished art, not upfront |

## Pipeline stages

1. **Resolve** — classify tokens, build a decision record (character(s),
   theme tokens, campaign file or none, pack slug, count, language). Hard
   stop only here, on unresolvable character token.
2. **Plan** — delegate to `prepare-line-sticker-metadata` with the decision
   record supplied as pre-filled answers, so it asks nothing. Produces
   `metadata.md`.
3. **Reference gate** — if `characters/<name>/reference-sheet.png` (or
   equivalent existing approved reference) exists, reuse it and skip
   generation. Otherwise generate one via `imagegen`, run the vision critic
   against the inherit/delta or character-library brief, retry budget **3**.
   Exhausting the budget is the pipeline's only other hard stop — a bad
   reference poisons all 40 stickers, so the run ends before the expensive
   stage rather than shipping 40 bad stickers.
4. **Render** — delegate to `create-line-stickers`'s rendering steps in
   batches of 8. Each sticker in a batch goes through the critic loop (below)
   before the batch is considered accepted.
5. **Assemble** — derive `main.png`/`tab.png`, finalize bilingual metadata,
   pick categories from `line-categories.json` based on the finished set.
6. **Validate + package** — run `validate_line_stickers.py` (includes the
   crop-seam audit), then the new duplicate-pose check, then build the ZIP.
7. **Report** — write `output/<pack>/auto-run-report.md`: decision record,
   reference-gate outcome, per-sticker accept/retry/unresolved status,
   validator output, and an explicit statement that automated checks are not
   a guarantee of LINE approval (carries forward the existing completion-gate
   language).

## Critic loop

Applied to the reference sheet (stage 3) and every rendered sticker
(stage 4), cheapest checks first:

1. **Existing scripts** — `validate_line_stickers.py`,
   `check_sticker_crop_seams.py` for structural failures (dimensions, crop
   seams).
2. **New script — duplicate pose** — `check_pose_duplicates.py`: perceptual
   hash (dHash) over each sticker's alpha silhouette, pairwise Hamming
   distance against previously accepted stickers in the pack; flags near-
   identical poses. Enforces the "avoid near-duplicate poses" rule in
   `create-line-stickers/SKILL.md` step 4, currently unenforced.
3. **New script flag — Thai headroom** — `render_thai_text.py --verify`:
   after rendering, checks whether ink touches the layer edge (proxy for
   clipped tone marks/vowels); fails the render rather than silently shipping
   it. Enforces the clipped-mark warning in `SKILL.md` steps 28 and 32,
   currently unenforced.
4. **Vision critic** — read the candidate PNG at 1:1 against the accepted
   reference sheet (and, in couple mode, the pairing reference). Judge:
   character identity drift, expression/pose reads as intended, text legible
   and unclipped, ~10px breathing room, pose distinct from already-accepted
   stickers in this pack. Any failure triggers a re-render with a targeted
   correction note describing what failed.

**Retry budget:** 2 re-renders per numbered sticker (3 attempts total), 3
re-renders for `main.png`/`tab.png` (4 attempts total, since they represent
the whole pack in the store listing), 3 re-renders for the reference sheet
(stage 3, hard stop on exhaustion as noted above).

**Budget exhaustion (non-reference stickers only):** keep the best-scoring
attempt, mark it `unresolved` in the run report, continue the pipeline. Never
mark an unresolved sticker as passed.

## Context management

The orchestrator's own context carries only: the decision record, the
accepted reference sheet, and the list of accepted-pose hashes (not full
critic transcripts). Per-sticker vision-critic detail is dropped once a
sticker is accepted or marked unresolved — only the outcome and any
unresolved note persists into the report. Render batches run sequentially at
8 stickers each; parallel subagent batches are an available future
optimization if context pressure is observed in practice, not part of this
implementation.

## New code

- `skills/create-line-stickers/scripts/check_pose_duplicates.py` — new
  script, same style as `check_sticker_crop_seams.py` (argparse, `magick`
  subprocess, no PIL/numpy dependency). Computes a dHash per sticker from
  `magick`'s alpha-channel pixel dump, reports pairwise Hamming distances
  below a threshold as failures. CLI: `check_pose_duplicates.py <directory>
  [--threshold N]`.
- `skills/create-line-stickers/scripts/render_thai_text.py` — add `--verify`
  flag: after rendering, sample the output edge pixels for non-transparent
  ink and exit non-zero if found, using the same `magick` subprocess pattern
  already in the file.
- `skills/make-line-sticker-pack/SKILL.md` — new skill: token resolution,
  decision defaults, pipeline stages, critic loop, retry budgets, as
  specified above. Delegates to the three existing skills; does not
  duplicate their internal instructions.
- `skills/make-line-sticker-pack/agents/openai.yaml` — matches the pattern in
  the other two skills' `agents/openai.yaml`.
- `README.md` — add a one-click section at the top pointing to the new
  skill; existing manual-flow sections stay unchanged below it.

## Testing

- TDD for both script changes: `check_pose_duplicates.py` against a
  synthetic pair of near-identical PNGs (expect FAIL) and a pair of clearly
  distinct PNGs (expect PASS); `render_thai_text.py --verify` against a
  known edge-clipped render (expect FAIL) and a known clean render (expect
  PASS).
- End-to-end verification: one real run of
  `$make-line-sticker-pack bunbun lazy` (character and campaign file both
  already exist in the repo), output compared against the existing
  hand-built packs in `output/` for structural parity (folder layout,
  metadata schema, validator pass).

## Completion gate

Finish only when: both new/modified scripts pass their TDD cases; the new
skill's `SKILL.md` and `agents/openai.yaml` exist and follow the existing
two skills' structure; the end-to-end `bunbun lazy` run produces a pack that
passes `validate_line_stickers.py` with zero errors and produces a non-empty
`auto-run-report.md`; README documents the one-click entry point; no
existing skill's behavior changes for its current manual invocations.
