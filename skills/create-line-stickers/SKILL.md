---
name: create-line-stickers
description: Create, revise, package, or audit static LINE sticker sets for LINE Creators Market. Use for LINE sticker concepts, two-reference requests that take visual direction from one LINE Store set and wording from another, expression lists, art-direction sheets, image generation or editing, metadata, submission assets, and preflight validation against LINE's static-sticker creation and review guidelines.
---

# Create LINE Stickers

Build a coherent, conversation-ready static sticker set and leave it in a submission-ready folder.

## Workflow

1. Inspect the workspace for existing characters, sketches, brand rules, fonts, and sticker assets. Preserve the character's defining traits across the set.
2. Establish the brief from available context: audience, language, character, tone, sticker count, and any phrases. Ask only for choices that materially change the result. Default to 8 stickers for an initial set.
   - **Two-reference mode:** When the user supplies a style URL and a wording URL, keep their roles separate. Inspect both pages in the locale supplied by each URL. From the style URL, record only abstract visual traits such as proportions, line weight, palette, shading, composition, lettering treatment, and emotional energy. From the wording URL, transcribe the visible sticker phrases in display order and preserve their language, spelling, punctuation, and intent. If a phrase is unreadable or unavailable, mark it unresolved instead of guessing.
   - Build a phrase-to-design map before rendering. Apply the style traits to an original or user-owned character and new poses/compositions; exclude the reference set's character identity, logos, names, exact drawings, and other distinctive protected elements. Treat the wording source as text/content direction, not visual direction. Report access limitations and rights risks before generation when either page cannot be inspected or the requested reuse appears unauthorized.
3. Read [references/line-static-spec.md](references/line-static-spec.md) before creating or validating assets. If the work includes concept selection, text, metadata, recognizable people/brands, or submission review, also read [references/review-checklist.md](references/review-checklist.md).
4. Draft a set plan before rendering. Give every sticker a distinct conversational job, readable pose/expression, phrase if any, and composition note. In two-reference mode, include the source phrase index and the abstract style traits applied to each design. Cover a useful mix such as greeting, thanks, apology, agreement, refusal, delight, sadness, and encouragement. Avoid near-duplicate poses.
5. Create one approved character/style reference first. When generating raster art, invoke the `imagegen` skill and use the reference for consistency. Generate or edit in small batches when that makes consistency easier to inspect.
6. Prepare each sticker as an RGB/RGBA PNG on a transparent canvas, with an even-numbered width and height no larger than 370 × 320 px. Keep roughly 10 px of breathing room around visible content. Favor bold silhouettes, large expressions, and short high-contrast lettering that remains legible at chat size.
   - **Thai typography option — rounded handwritten:** Use `scripts/render_thai_text.py` with Mali Bold, dark warm-gray fill (`#5b4a47`), and a white keyline. The script renders through Pango/HarfBuzz so stacked vowels and tone marks retain correct Thai shaping. Use `|` for an intentional line break. Verify the result on both light and dark chat backgrounds before applying it to the full set.
7. Derive `main.png` at exactly 240 × 240 px and `tab.png` at exactly 96 × 74 px from representative set artwork. Use `01.png`, `02.png`, and so on for sticker images, preserving leading zeros.
8. Write submission metadata and count it using LINE's counting rule: creator ≤50, title ≤40, description ≤160, copyright ≤50; Asian-language characters and some symbols may count as two. Treat the web form as the final authority for borderline counts.
9. Run `python3 <skill-directory>/scripts/validate_line_stickers.py <set-directory>`. Resolve every error. Review warnings visually and resolve or explicitly report each one.
10. Inspect the full set as a contact sheet or thumbnails against both light and dark chat backgrounds. Confirm legibility, transparent edges, visual variety, spelling, metadata alignment, and that `main.png`/`tab.png` honestly represent the set.

## Deliverables

Use this package layout:

```text
set-name/
├── main.png
├── tab.png
├── 01.png
├── 02.png
├── ...
└── metadata.md
```

In `metadata.md`, include creator, title, description, copyright, language, sticker count, and a numbered intent/phrase list. For two-reference mode, also identify the style URL and wording URL by role, record any unresolved phrases, and state that the artwork uses an original or authorized character. End with the validator result and any remaining human review risks.

## Completion gate

Finish only when the selected count is one of 8, 16, 24, 32, or 40; every required PNG is present; the validator reports zero errors; every warning has been reviewed; and the set passes a visual and content-policy check. State clearly that automated checks cannot guarantee LINE approval.
