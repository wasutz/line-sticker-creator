---
name: research-line-sticker-concepts
description: Research source-backed character opportunities, Thai sticker wording, or both, and save a dated Markdown brief for the create-line-stickers workflow. Use when choosing what LINE sticker character to build, finding high-utility or trending Thai phrases, refreshing stale wording evidence, comparing character niches, or preparing reusable research under skills/create-line-stickers/references/research/ before artwork planning.
---

# Research LINE Sticker Concepts

Produce a reusable research brief, not sticker artwork. Keep observed market evidence separate from creative recommendations.

## Workflow

1. Resolve the scope from the request:
   - **Character**: research character archetypes, visual niches, audience fit, and differentiation.
   - **Wording**: research everyday chat jobs, current Thai phrasing, trend freshness, and review risk.
   - **Both**: research the two branches independently, then connect them in one recommendation.
2. Read `skills/create-line-stickers/references/thai-wording-trends.md` for Thai wording work and `skills/create-line-stickers/references/review-checklist.md` for every brief.
3. Browse current sources. Use the live Thai LINE Creators Market rankings and individual sticker pages as the primary market evidence. Cross-check slang meaning or usage with reputable Thai-language sources when needed. Record the access date and direct URL for every source used.
4. Inspect actual sticker artwork when making visual or wording claims. Titles and descriptions alone do not establish a visual trait or phrase. Mark inaccessible or unreadable evidence unresolved instead of guessing.
5. Synthesize rather than copy:
   - Describe shared visual traits and market gaps; never recommend another set's character identity, exact drawings, name, or distinctive protected elements.
   - Treat short everyday phrases as shared language, but do not reproduce another creator's ordered phrase list.
   - Label time-sensitive slang and recommend a durable utility core around it.
6. Write one Markdown file to `skills/create-line-stickers/references/research/YYYY-MM-DD-<topic-slug>.md`. Use lowercase hyphen-case for `<topic-slug>`. If that path exists, add `-v2`, `-v3`, and so on; preserve prior research.
7. Verify the file against the completion gate and return its path plus a one-paragraph recommendation.

## Brief Schema

Use only sections relevant to the selected scope:

```markdown
# LINE Sticker Concept Research: <topic>

**Researched:** YYYY-MM-DD
**Scope:** Character | Wording | Character and wording
**Locale:** <locale>
**Downstream skill:** create-line-stickers

## Executive Recommendation
<what to build or say, target audience, and why>

## Evidence
| Source | Observed evidence | How it informs the recommendation |
|---|---|---|

## Character Opportunity
### Audience and chat persona
### Original design direction
### Silhouette, palette, texture, and expression range
### Differentiation and crowded niches
### Props and conversation scenarios
### Rights and review risks

## Wording Recommendation
### Register and tone
### Coverage targets
### Recommended phrase pool
| Phrase | Chat job | Tier | Freshness or evidence note |
|---|---|---|---|
### Redundancies and phrases to avoid
### Spelling, particles, and layout notes

## Handoff to create-line-stickers
- Recommended sticker count: <valid LINE count>
- Character brief: <compact generation-ready identity>
- Wording selection rule: <how to choose the final numbered set>
- Required invariants: <originality, legibility, policy, and consistency>
- Open questions: <only unresolved choices that materially affect production>

## Sources
- <descriptive title>: <direct URL> (accessed YYYY-MM-DD)
```

For a requested sticker count, provide at least that many distinct phrase/wordless candidates and map every candidate to a chat job. For an open-ended wording study, default to a 40-slot recommendation with roughly 40% daily utility, 35% mood, 15% current slang, and 10% wordless reactions.

## Completion Gate

Finish only when:

- Every market claim has dated source support or is explicitly labeled an inference.
- Character recommendations are original and exclude copied identities or drawings.
- Wording covers routine replies and emotional reactions without semantic duplicates.
- Time-sensitive slang is labeled with freshness and limited to a minority of the pool.
- Review risks cover rights, profanity, self-harm, gambling, substances, politics, religion, brands, and metadata promotion when relevant.
- The handoff is specific enough for `create-line-stickers` to build a numbered plan without repeating the research.
- The output exists under `skills/create-line-stickers/references/research/` and no previous brief was overwritten.
