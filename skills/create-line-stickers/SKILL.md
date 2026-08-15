---
name: create-line-stickers
description: Create, revise, package, or audit static LINE sticker sets for LINE Creators Market from a prompt or a prepared metadata.md brief. Use for LINE sticker concepts, named characters stored in a local characters library, style-only requests that need original high-utility wording, two-reference requests that take visual direction from one LINE Store set and wording from another, expression lists, art-direction sheets, image generation or editing, submission assets, and preflight validation against LINE's static-sticker creation and review guidelines.
---

# Create LINE Stickers

Build a coherent, conversation-ready static sticker set and leave every final deliverable under `<workspace-root>/output/<pack-name>/`.

## Workflow

1. Inspect the workspace for existing characters, sketches, brand rules, fonts, sticker assets, and a user-specified `metadata.md`.
   - **Prepared-metadata mode:** Read the entire file before planning or rendering. Accept both the planning schema's `## Sticker Plan` and completed packs' `## Sticker Intent and Phrase List`. Treat its project brief, wording, numbered plan, reference roles, and explicit campaign section as the approved source of truth. Resolve relative paths from the metadata file's directory, except repository-root paths such as `characters/...`. Copy or adapt the completed metadata to `<workspace-root>/output/<pack-name>/metadata.md`; preserve an input file outside `output/` unless the user explicitly requests an in-place update. Check that its sticker count is valid, its numbered plan is complete, its categories exist in `references/line-categories.json`, and its copyright is `© WhatAForkStudio`. Report contradictions or unresolved questions before generation. Do not add a campaign merely because a campaign reference exists in the repository; apply campaign rules only when the metadata contains `## Campaign` or `## Campaign Eligibility`, or the user's current prompt explicitly requests one. Preserve approved creative fields unless asset reality, validation, or a direct user instruction requires an update.
   Preserve the character's defining traits across the set.
   - **Character-library mode:** Resolve a request to use character `{name}` to `<workspace-root>/characters/{name}/`. Read all `.png`, `.jpg`, `.jpeg`, and `.webp` images in that folder before planning the set. Treat those images as the source of truth for the character's identity and visual design: silhouette, proportions, face, palette, markings, clothing, accessories, linework, and rendering style. Use multiple images together when they provide complementary poses, expressions, or views. If the folder is missing or contains no supported images, report the exact path checked and ask for a valid character name or reference images instead of inventing the named character.
2. Establish the brief from prepared metadata when supplied, then use the current prompt to fill only missing details. Otherwise establish it from available context: audience, language, character, tone, sticker count, and any phrases. Ask only for choices that materially change the result. Default to 8 stickers for an initial set.
   - **Style-only mode:** When the user supplies visual direction but no wording, create the wording without asking for a wording source. Infer the language and social register from the request, locale, and character; otherwise use the user's language and a friendly everyday register. Build a priority-ranked phrase set around frequent chat jobs: greeting, acknowledgment, thanks, apology, agreement, refusal, affection, laughter, encouragement, checking in, waiting, urgency, surprise, confusion, anger, sadness, tiredness, hunger, departure, and good night. Fill smaller sets from the highest-utility jobs first; expand larger sets with tone variants and situation-specific reactions. Keep phrases short, natural, distinct, and legible at chat size. Use locally familiar spelling and particles, but exclude passing memes, copied catchphrases, and claims that the phrases are statistically “most used” unless usage data was actually consulted. Reserve roughly 10–20% of the set for clear wordless reactions when the expression communicates better without text.
   - **Two-reference mode:** When the user supplies a style URL and a wording URL, keep their roles separate. Inspect both pages in the locale supplied by each URL. From the style URL, record only abstract visual traits such as proportions, line weight, palette, shading, composition, lettering treatment, and emotional energy. From the wording URL, transcribe the visible sticker phrases in display order and preserve their language, spelling, punctuation, and intent. If a phrase is unreadable or unavailable, mark it unresolved instead of guessing.
   - Build a phrase-to-design map before rendering. Apply the style traits to an original or user-owned character and new poses/compositions; exclude the reference set's character identity, logos, names, exact drawings, and other distinctive protected elements. Treat the wording source as text/content direction, not visual direction. Report access limitations and rights risks before generation when either page cannot be inspected or the requested reuse appears unauthorized.
3. Read [references/thai-wording-trends.md](references/thai-wording-trends.md) whenever the set needs Thai wording, whether original or gap-filling. Read [references/line-static-spec.md](references/line-static-spec.md) before creating or validating assets. If the work includes concept selection, text, metadata, recognizable people/brands, or submission review, also read [references/review-checklist.md](references/review-checklist.md).
4. Draft a set plan before rendering, or verify and adopt the numbered plan from prepared metadata. Give every sticker a distinct conversational job, readable pose/expression, phrase if any, and composition note. In style-only mode, list the phrases in priority order and check that the set covers both routine replies and emotional reactions without semantic duplicates. In two-reference mode, include the source phrase index and the abstract style traits applied to each design. Avoid near-duplicate poses.
5. Create one approved character/style reference first. In character-library mode, use the library images directly as image references; create a new reference sheet only when the supplied views do not adequately define the character. When generating raster art, invoke the `imagegen` skill and include the relevant character images in every generation or edit that supports references. Generate or edit in small batches when that makes consistency easier to inspect. For multi-sticker sheets, require generous gutters and keep every figure, prop, effect, ear, limb, and outline visibly inside its cell; reject a sheet when any artwork touches or crosses an implied cell boundary.
6. Prepare each sticker as an RGB/RGBA PNG on a transparent canvas, with an even-numbered width and height no larger than 370 × 320 px. Keep roughly 10 px of breathing room around visible content. Favor bold silhouettes, large expressions, and short high-contrast lettering that remains legible at chat size.
   - **Grid extraction:** Extract sheet cells with overlap padding rather than a destructive fixed crop. Use `scripts/extract_padded_grid.py` for rectangular grids; it retains connected artwork crossing the nominal cell edge and removes components centered in neighboring cells. Never use blanket `-shave`, fixed-edge erasure, or an equivalent operation on every cell. Replace a source pose with a clean standalone render when padded extraction cannot recover the complete silhouette.
   - **Thai typography option — rounded handwritten:** Use `scripts/render_thai_text.py` with Mali Bold, dark warm-gray fill (`#5b4a47`), and a white keyline. The script renders through Pango/HarfBuzz so stacked vowels and tone marks retain correct Thai shaping. Use `|` for an intentional line break. Verify the result on both light and dark chat backgrounds before applying it to the full set.
7. Derive `main.png` at exactly 240 × 240 px and `tab.png` at exactly 96 × 74 px from representative set artwork. Use `01.png`, `02.png`, and so on for sticker images, preserving leading zeros.
8. Write or finalize bilingual submission metadata at `<workspace-root>/output/<pack-name>/metadata.md`. When prepared metadata exists, retain its approved brief and sticker plan in this output copy. Create or verify catchy, natural English and Thai titles and polished descriptions grounded in the actual character, visual style, theme, expressions, and chat use. Write each language natively rather than translating literally. Count each localized title and description using LINE's rule: title ≤40 and description ≤160; Asian-language characters and some symbols may count as two. Always set copyright to `© WhatAForkStudio`. Read [references/line-categories.json](references/line-categories.json), analyze the finished set, and select exactly one closest style category and one closest character category from that file. Replace the planning production status with actual validator results and remaining human-review risks. Treat the live submission form as final authority for borderline counts and category changes.
9. Run `python3 <skill-directory>/scripts/validate_line_stickers.py <pack-directory>`. The validator includes a straight crop-seam audit when ImageMagick is available. Resolve every error. Review warnings visually and resolve or explicitly report each one. Create `<pack-name>-stickers.zip` from the contents of the image directory without an enclosing directory, and keep metadata out of the archive.
10. Inspect every numbered PNG individually at 1:1 scale, then inspect the full set as a contact sheet against both light and dark chat backgrounds. Confirm that no head, ear, limb, prop, effect, outline, or shadow is cut by a straight edge; no fragment from an adjacent sheet cell remains; roughly 10 px of transparent breathing room surrounds the intended composition; lettering is legible; poses are varied; spelling and metadata align; and `main.png`/`tab.png` honestly represent the set. A contact sheet alone does not satisfy this check because scaling can hide crop seams.

## Deliverables

Use an outer pack folder inside the repository-root `output/` directory and keep submission metadata separate from uploadable images:

```text
output/
└── pack-name/
    ├── pack-name-stickers/
    │   ├── main.png
    │   ├── tab.png
    │   ├── 01.png
    │   ├── 02.png
    │   └── ...
    ├── metadata.md
    └── pack-name-stickers.zip
```

The image directory contains only the numbered stickers, `main.png`, and `tab.png`. The ZIP contains those files at its root and excludes `metadata.md`.

Use this core `metadata.md` schema:

```markdown
# Metadata

## English
**Title:** <natural English title>
**Description:** <natural English description>

## Thai
**Title:** <natural Thai title>
**Description:** <natural Thai description>

## Categories
**Style Category:** <exact value from line-categories.json>
**Character Category:** <exact value from line-categories.json>

## Copyright
© WhatAForkStudio
```

After the core fields, include sticker count and a numbered intent/phrase list. For two-reference mode, also identify each URL by role, record unresolved phrases, and state that the artwork uses an original or authorized character. End with the validator result and remaining human-review risks.

Keep reusable character references at the repository root:

```text
characters/
└── {name}/
    ├── front.png
    ├── side.png
    └── expressions.webp
```

## Completion gate

Finish only when the selected count is one of 8, 16, 24, 32, or 40; the exact outer-pack structure exists at `<workspace-root>/output/<pack-name>/`; every required PNG is present; the ZIP contains only the image-directory contents; bilingual metadata uses valid categories and the fixed copyright; the validator and crop-seam audit report zero errors; every warning has been reviewed; every numbered PNG has passed the individual 1:1 crop check plus light/dark contact-sheet review; and the set passes a content-policy check. State clearly that automated checks cannot guarantee LINE approval.
