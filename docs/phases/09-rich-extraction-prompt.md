# Phase 09 — Prompt & extraction heuristics

## Goal

Rewrite `SYSTEM_PROMPT` in `agent/prompts.py` so the vision model reliably gathers **publish date**, **release notes**, and **download assets** from the GitHub releases page before emitting `done` — using scroll actions when content is below the fold.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- Updated `SYSTEM_PROMPT` with v2 field-mapping rules and navigation guidance.
- Clear stop condition: do not emit `done` until all eight payload fields are populated (empty `downloads` only when the Assets section is genuinely absent).

## Prompt additions (spec)

### Publish date (`published_at`)

- Read the date shown on the **stable** release card — typically near the author or title (e.g. `May 6th, 2026`, `on May 6`, or a relative `2 weeks ago`).
- Copy the date string as displayed; do not normalize to ISO unless that exact format is visible.

### Release notes (`release_notes`)

- After identifying the stable release, read the body text below the title — headings, bullet lists, and paragraph text.
- If the body is cut off at the bottom of the viewport, `scroll` down and continue reading until the **Assets** header or the next release entry appears.
- Include markdown-style headings if visible (`## What's Changed`).
- Do not summarize or paraphrase; transcribe what is readable from screenshots.

### Downloads (`downloads`)

- Locate the **Assets** section under the stable release (often `Assets N` with a count).
- For each visible asset row, extract:
  - `name` — filename or label (e.g. `Source code (zip)`, `react-19.2.6.tgz`)
  - `url` — full HTTPS URL only if visible on the page or inferable from standard GitHub release URL patterns shown in the UI
- If Assets are below the fold, scroll before emitting `done`.
- If no Assets section exists for this release, return `"downloads": []`.

### Scroll strategy

- Expected extra steps vs v1: 1–3 scroll actions to expose notes tail and asset list.
- Prefer scrolling **within** the release detail view before scrolling past into older releases.
- If after scrolling the notes are still truncated, include everything read so far — do not stall indefinitely.

## Tasks

- [x] Rewrite GitHub heuristics section in `SYSTEM_PROMPT` with v2 field mapping.
- [x] Update stop condition from "five fields" to all v2 fields (with explicit empty-array rule for missing Assets).
- [x] Add anti-hallucination clause for URLs: "Do not invent download URLs; only include links you can read or that follow visible GitHub release URL patterns on screen."
- [x] Add example `done` JSON snippet in the prompt (abbreviated notes) matching `ACTION_JSON_SCHEMA`.
- [x] Review whether `max_steps` default (25) remains sufficient — **recommend raising to 30** in phase 10; v2 adds 1–3 scroll steps for notes/Assets and may hit the step cap on slower navigation paths.

## Acceptance criteria

- Prompt mentions all eight output fields by name.
- Prompt explicitly ties `published_at`, `release_notes`, and `downloads` to visual regions on the releases page.
- No CSS/XPath/DOM references added.

## Dependencies

- Phase 08 (`DoneAction` schema must exist before prompt references field names).

## Risks

- **Notes length**: models may truncate long changelogs. Accept partial transcription; iteration can tighten "read until Assets header" wording.
- **Asset URLs off-screen**: GitHub often hides full URLs until hover — model may only see filenames. Prompt allows constructing standard archive URLs only when tag and repo are known from page context.
- **Pre-release confusion**: existing stable-release filtering rules must remain; v2 fields apply to the same stable entry as v1.

## Notes

- Domain knowledge stays in the prompt, not in `loop.py` — same architecture as v1.
- After prompt changes, run one `--debug` session on `facebook/react` before phase 10 wiring.
