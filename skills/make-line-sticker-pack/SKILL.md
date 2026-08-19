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
- Every non-character token is a theme token — unconditionally, whether or not it also matches a campaign file. Theme tokens drive the wording/theme lens and the pack slug; nothing removes a token from this list.
- Separately, check the same theme-token list against filename stems under `skills/create-line-stickers/references/campaigns/` (e.g. `lazy` matches `lazy-campaign-2026.md`). A match turns on campaign mode for that file in addition to the token's normal role as a theme token. If more than one theme token matches a campaign file, use the first match in invocation order and note the others were ignored in the run report.
- Zero character-token matches, or a character token with no matching folder under `characters/`: **hard stop.** Report the exact path checked (`characters/<token>/`) and do not proceed.

Build a decision record before continuing:

| Field | Value |
|---|---|
| Character(s) | resolved folder path(s) |
| Theme tokens | all non-character tokens, in invocation order (a token also matching a campaign file stays in this list) |
| Campaign | matched campaign file path, or none |
| Sticker count | 40 |
| Language | Thai wording; bilingual (English + Thai) metadata |
| Pack slug | Solo mode: `<character>-<theme-tokens-joined-by-hyphen>-th-40`. Couple mode: `<characterA>-<characterB>-<theme-tokens-joined-by-hyphen>-th-40`. If `output/<slug>/` already exists, append `-v2`, `-v3`, ... until free |
| Copyright | `© WhatAForkStudio` |

## 2. Plan

Follow `skills/prepare-line-sticker-metadata/SKILL.md`'s workflow, supplying the decision record as the answers to every question it would otherwise ask (character(s), count, language, theme, output location, campaign). Do not stop to ask the user anything the decision record already answers. This produces `metadata.md` at the pack directory it resolves to (`output/<pack-slug>/metadata.md` given the pack slug above).

This orchestrator drives `create-line-stickers` but does not replace its own completion gate. Before rendering, still do what `create-line-stickers/SKILL.md` steps 3 and 4 require: read `references/line-static-spec.md` (and `references/review-checklist.md` when the work touches text, metadata, or recognizable people/brands) before creating or validating assets, and draft or verify/adopt the numbered set plan — the automated reference gate and critic loop replace manual approval, not this required reading and planning.

## 3. Reference gate

Before rendering any numbered sticker:

- If `characters/<name>/reference-sheet.png` (or another already-approved reference image serving that role in the character's folder) exists, reuse it directly. Skip generation for this stage.
- Otherwise, generate one approved character/style reference exactly as `create-line-stickers/SKILL.md` step 5 describes (pairing reference for couple mode), then run it through the critic loop (Section 5 below) against the character-library or inherit-and-delta brief.
- Retry budget for the reference sheet is **3** re-generations (4 attempts total). If it still fails the critic loop after budget is exhausted: **hard stop.** Do not proceed to rendering — a failed reference would be inherited by all 40 stickers. Report which checks failed on the final attempt.

## 4. Render

Follow `create-line-stickers/SKILL.md` step 6 (rendering, grid extraction, Thai typography) in batches of 8 numbered stickers at a time. Run every sticker in a batch through the critic loop (Section 5) before treating the batch as accepted and moving to the next batch.

## 5. Critic loop

Applied to the reference sheet (Section 3), every rendered numbered sticker (Section 4), and `main.png`/`tab.png` composites (Section 6), cheapest checks first, stopping at the first failure:

1. Run per-file structural checks only — dimensions ≤370×320, even width/height, has an alpha channel, and no suspicious straight crop seam via `python3 <skill-directory>/../create-line-stickers/scripts/check_sticker_crop_seams.py <pack-directory>/<pack-name>-stickers`. Do **not** run `validate_line_stickers.py` here: it is a pack-level preflight (total sticker count in {8,16,24,32,40}, `main.png`/`tab.png` presence, metadata fields, ZIP existence) that will always fail against a pack with only some stickers rendered — it belongs only in Section 7, run once against the finished pack. For the reference sheet, skip this step entirely (a single reference image has no crop-seam or pack-count convention to check); go straight to the vision check.
2. For a rendered numbered sticker, run `python3 <skill-directory>/../create-line-stickers/scripts/check_pose_duplicates.py <pack-directory>/<pack-name>-stickers` against the stickers already accepted in this pack (near-duplicate pose, alpha-silhouette dHash). Treat a flag as advisory input to the vision check in step 4 below rather than an automatic failure on its own — confirm with the 1:1 read whether the poses are actually indistinguishable before triggering a re-render. Skip this step for `main.png`/`tab.png` (not applicable to composite representatives).
3. If the sticker carries rendered Thai lettering produced via `render_thai_text.py`, that render must have used `--verify` and passed (edge-clipped ink is a failure here, not a separate re-check). Skip this step for `main.png`/`tab.png` (not applicable to composites).
4. Read the candidate image at 1:1 against the accepted reference sheet (and pairing reference, in couple mode). Judge: character identity drift from the reference, expression/pose reads as the plan intends, text (if any) is legible, ~10px transparent breathing room around the composition. For numbered stickers, also confirm pose is visually distinct from every already-accepted sticker in this pack (resolve any step-2 flag here) and check the composite against both a light and a dark chat background — white-keyline Thai lettering from `render_thai_text.py` can pass on one background and wash out on the other. For `main.png`/`tab.png`, confirm the composite faithfully represents the full pack's character and mood.

Any failure at any step: re-render that one sticker (or the reference sheet, in Section 3) with a targeted correction note describing exactly what failed, and try again against the same retry budget.

**Retry budgets:** 2 re-renders per numbered sticker (3 attempts total). 3 re-renders for `main.png`/`tab.png` (4 attempts total — they represent the whole pack in the store listing). 3 re-renders for the reference sheet, per Section 3 (hard stop on exhaustion).

**Budget exhaustion for a numbered sticker or main/tab (not the reference sheet):** keep the best-scoring attempt, record it as `unresolved` with the specific failed check(s) in the run report, and continue the pipeline. Never mark an unresolved sticker as passed.

## 6. Assemble

Follow `create-line-stickers/SKILL.md` step 7 for `main.png`/`tab.png`, then step 8 for finalizing bilingual metadata and selecting exactly one style category and one character category from `references/line-categories.json` based on the finished set.

## 7. Validate, package, and report

Follow `create-line-stickers/SKILL.md` step 9: run `python3 <skill-directory>/../create-line-stickers/scripts/validate_line_stickers.py <pack-directory>` (the full pack-level preflight — sticker count, `main.png`/`tab.png`, metadata fields, ZIP contents — now that every sticker is rendered) and create the ZIP. Also run `python3 <skill-directory>/../create-line-stickers/scripts/check_pose_duplicates.py <pack-directory>/<pack-name>-stickers` across the full finished set as a final pass. Resolve every validator error; for warnings and any remaining `unresolved` stickers, carry them into the report rather than resolving them silently.

The automated critic loop does not supersede `create-line-stickers/SKILL.md` step 10's content-policy check: before writing the report, confirm the finished set has no recognizable real people/brands, no rights-infringing reuse, and nothing else that content review would flag — the vision checks in Section 5 judge identity/legibility/composition, not policy compliance.

*Note: the `<skill-directory>/../create-line-stickers/...` paths above assume `make-line-sticker-pack` and `create-line-stickers` remain installed as sibling skill directories; adjust them if relocated.*

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
