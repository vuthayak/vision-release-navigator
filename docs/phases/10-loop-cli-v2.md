# Phase 10 — Loop & CLI output (v2)

## Goal

Wire the extended `DoneAction` through `agent/loop.py` and `navigate.py` so success paths emit the full v2 JSON and failure paths detect incomplete extractions.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- Updated `_is_blank_done()` (or equivalent) covering v2 required fields.
- `navigate.py` serializes all v2 fields to stdout / `--output`.
- Optional: bump default `--max-steps` from 25 → 30 to accommodate scroll-heavy extraction.

## Tasks

### `agent/loop.py`

- [x] Extend `_is_blank_done()` to treat these as required for success:
  - v1 fields: `repository`, `latest_release`, `version`, `tag`, `author` (any all-blank → failure)
  - v2 fields: `published_at` and `release_notes` must be non-empty strings
  - `downloads`: empty array is valid **only** when the model's `reasoning` indicates no Assets section (otherwise prefer at least one asset on repos known to ship assets)
- [x] Serialize `downloads` as `[{"name": "...", "url": "..."}, ...]` in debug `step_NN.json` dumps (automatic via `model_dump()`).
- [x] Consider raising default `max_steps` to 30 if phase 09 debug runs exhaust the cap.

### `navigate.py`

- [x] Build output dict from extended `DoneAction` including `published_at`, `release_notes`, `downloads`.
- [x] Ensure `json.dumps` handles nested list cleanly (indent=2).
- [x] Update any inline docstrings / help text referencing "five fields".

### `agent/vision.py` re-exports

- [x] Confirm `DoneAction` / `DownloadAsset` are exported if CLI or tests import them.

## Output JSON shape

Same as [IMPLEMENTATION.md](../IMPLEMENTATION.md) v2 contract. Stdout remains JSON-only; logs on stderr.

## Acceptance criteria

- Stubbed loop test with a hand-rolled v2 `done` returns all fields.
- Blank `published_at` or `release_notes` raises `AgentLoopError` (same exit code 1 as v1 blank done).
- `python navigate.py ...` prints valid extended JSON (manual smoke after phase 09 prompt land).

## Dependencies

- Phase 08 (schema).
- Phase 09 (prompt — needed for meaningful E2E, but wiring can land first with stubbed vision).

## Risks

- **Stricter blank check**: repos with literally no release body are rare on major projects; empty `release_notes` should still fail — document as limitation.
- **Breaking change**: consumers expecting exactly five top-level keys will need to update; note in README (phase 11).

## Notes

- Do not add post-processing that fetches URLs via HTTP or parses the DOM — vision-only extraction end-to-end.
