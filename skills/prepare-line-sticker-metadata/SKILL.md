---
name: prepare-line-sticker-metadata
description: Prepare metadata.md as the approved creative brief and submission metadata for a static LINE sticker pack before artwork generation. Use when planning LINE sticker wording, intents, character direction, pack naming, categories, bilingual titles and descriptions, reference roles, or an explicitly requested LINE campaign for later use by create-line-stickers.
---

# Prepare LINE Sticker Metadata

Create the pack plan first so `create-line-stickers` can render from a stable, reviewable contract.

## Workflow

1. Inspect the request and workspace for the character folder, supplied references, target language, sticker count, tone, audience, theme, and output location. Read every supported character image when a named local character is requested.
2. Read [../create-line-stickers/references/review-checklist.md](../create-line-stickers/references/review-checklist.md). Read [../create-line-stickers/references/line-categories.json](../create-line-stickers/references/line-categories.json) and choose exactly one listed style category and one listed character category.
3. Establish one conversational job, phrase, expression/action, and composition note for each sticker. Use a valid count: 8, 16, 24, 32, or 40. Preserve user-supplied wording; mark unreadable reference wording unresolved instead of guessing. When wording is not supplied, prioritize natural, short phrases used in everyday chat and include wordless reactions where they communicate better.
4. Treat reference roles explicitly. Extract only abstract visual traits from a style reference. Treat a wording reference as text direction. Use an original or authorized character and exclude reference characters, logos, names, exact drawings, and distinctive protected elements.
5. Add campaign requirements only when the user explicitly requests a campaign. Read the named campaign reference when one exists, record its measurable eligibility target, and tag each qualifying sticker in the plan. Omit the entire campaign section for ordinary packs.
6. Write `<pack-directory>/metadata.md` using [references/metadata-schema.md](references/metadata-schema.md). Default the pack directory to `output/<descriptive-slug>-<language>-<count>/`. Create only the directory and metadata file; leave artwork, ZIP, validation results, and completion claims for `create-line-stickers`.
7. Check that titles and descriptions are natural in each language and fit LINE's counting rule: title ≤40 and description ≤160; Asian-language characters and some symbols may count as two. Use exactly `© WhatAForkStudio`. Confirm that the numbered plan has the selected count, unique jobs, actionable visual direction, valid categories, and no unsupported campaign claims.

## Handoff

Return the exact `metadata.md` path and summarize unresolved decisions. Tell the user to pass that path to `$create-line-stickers`; the file is the source of truth for the approved brief, while generated-asset facts and validation status are filled in after rendering.

## Completion gate

Finish only when the file follows the schema, every planned sticker is numbered once, all requested inputs are represented, optional sections appear only when applicable, and no field claims that ungenerated assets already exist or passed validation.
