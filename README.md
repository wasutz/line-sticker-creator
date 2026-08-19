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

Create and review the pack brief first:

```text
Use $prepare-line-sticker-metadata to plan a 40-piece Thai sticker pack using the character "mochi-bear". Save it under output/mochi-bear-daily-th-40/metadata.md.
```

Or with Campaign

```
Use $prepare-line-sticker-metadata to plan a 40-piece Thai sticker pack.
Save it under output/colorful-character/metadata.md. This set of sticker is for "Colorful Stickers Campaign": Read `skills/create-line-stickers/references/campaigns/colorful-campaign-2026.md` and ensure the pack satisfies every campaign requirement.
```

Then render directly from that contract:

```text
Use $create-line-stickers with output/mochi-bear-daily-th-40/metadata.md and prepare the submission-ready pack.
```


## How to use it

```
Use $create-line-stickers to create an 8-piece sticker set featuring a cute golden retriever. Use Thai phrases and prepare submission-ready PNGs.
```

## With a style reference only

```
Use $create-line-stickers to create a 40-piece sticker set using the style from "https://store.line.me/stickershop/product/35168861/th". The character will be a cute orange cat. Create original Thai wording based on high-utility emotions and phrases people often use in everyday chats, then prepare submission-ready PNGs.
```

## With a saved character

Store one or more reference images under `characters/<name>/`, for example:

```text
characters/
└── mochi/
    ├── front.png
    ├── side.png
    └── expressions.webp
```

Then refer to the character by its folder name:

```
Use $create-line-stickers to create a 24-piece sticker set using the character "mochi" from the characters folder. Preserve Mochi's appearance and drawing style from every reference image in characters/mochi. Create original Thai wording for everyday chats and prepare submission-ready PNGs.
```

## With two characters as a couple

Store each character in its own folder, then name both characters and require them together:

```text
Use $create-line-stickers to create a 16-piece Thai couple sticker set using "mochi-bear" from characters/mochi-bear/ as partner A and "bunbun" from characters/bunbun/ as partner B. Show both partners in every sticker, preserve each character's appearance and their relative scale, and create affectionate, teasing, apologetic, and supportive everyday-chat moments. Prepare submission-ready PNGs.
```

## With a character variant

Use a saved character as the visual source and describe only what should change:

```text
Use $create-line-stickers to create a female-presenting variant of "bunbun" from characters/bunbun/. Preserve Bunbun's rabbit silhouette, proportions, facial construction, linework, and rendering style. Give the variant a distinct soft coral accent, a small left-ear flower accessory, and subtly longer eyelashes. Create and approve her reusable character reference first, then use it for a 40-piece Thai everyday-chat sticker set.
```

The same pattern can create a sibling, seasonal outfit, alternate colorway, or a second partner derived from an existing character. Name the traits to preserve and the traits to change whenever you already know them.

## With two reference links

```
Use $create-line-stickers to create a 40-piece sticker set. Use the style from "https://store.line.me/stickershop/product/8336222/th" and the wording from "https://store.line.me/stickershop/product/31396074/th". The character will be a cute white rabbit. Prepare submission-ready PNGs.
```

With reference document.
```
 Use $create-line-stickers to create a 40-piece sticker set. Use the style from "https://store.line.me/stickershop/product/8336222/th" and the wording/phrasing from "https://store.line.me/stickershop/product/31396074/th". The character will be a cute white rabbit. Review the trending Thai phrases provided in /references/thai-wording-trends. Replace outdated or redundant phrases from the baseline set with these trending terms to ensure high social media relevance and engagement. Prepare submission-ready PNGs.
```

## With Campaign

```
Use $create-line-stickers to create a 40-piece static sticker set for LINE’s 2026 Lazy Stickers Campaign.

  Use the existing character from `characters/mochi-bear/` and preserve Mochi Bear’s established appearance and style.

  Read `skills/create-line-stickers/references/campaigns/lazy-campaign-2026.md` and ensure the pack satisfies every campaign requirement. At least 20 of
  the 40 numbered stickers, plus `main.png`, must clearly communicate lazy actions, feelings, or wording.

  Create original, natural Thai phrases about procrastinating, resting, avoiding work, staying in bed, having no energy, and wanting to get rich without
  working. Avoid particular-name content and previously released artwork.

  Prepare the standard bilingual metadata, use `© WhatAForkStudio`, select valid LINE categories, package the final images using the required outer-
  folder structure, and run both standard and campaign eligibility checks.  Prepare submission-ready PNGs.
  ```
