# `metadata.md` schema

Use the headings and field labels below. Replace placeholders and omit sections marked optional when they do not apply.

```markdown
# Metadata

## Project Brief
**Pack Name:** <folder-safe descriptive slug>
**Sticker Count:** <8, 16, 24, 32, or 40> static stickers
**Primary Language:** <language used on stickers>
**Character:** <character name and local folder, or original character description>
**Audience and Tone:** <short creative direction>
**Visual Direction:** <identity traits, style, palette, lettering, and consistency rules>

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

## References
- <role>: <URL or local path, plus the permitted abstraction or use>

## Sticker Plan

1. **<phrase or “wordless”>** — Job: <chat intent>; Expression/action: <renderable direction>; Composition: <layout and lettering>; Tags: <useful tags>

## Campaign
**Name:** <campaign name>
**Requirements Source:** <local reference or authoritative URL>
**Eligibility Target:** <measurable requirement>
**Planned Qualifying Stickers:** <indices and count>
**Main Image Direction:** <how main.png will clearly qualify>

## Open Questions
- <only unresolved decisions; write “None” when complete>

## Production Status
Planning complete. Artwork and submission package not yet generated or validated.
```

Keep `## References`; write `- None` when no external or local reference is used. Keep `## Open Questions` so the handoff cannot hide uncertainty. Omit `## Campaign` unless the user explicitly requested one.

Add another localized title/description section when the user requests a language other than English or Thai. Keep English and Thai by default because the downstream sticker skill prepares bilingual submission metadata.
