# Phase 11 — Validation & docs (v2)

## Goal

Verify v2 end-to-end on a real repository, record results, and sync user-facing and reference docs with the extended output contract.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- Documented E2E run with extended JSON output.
- Updated `README.md`, `ARCHITECTURE.md`, and `IMPLEMENTATION.md` definition-of-done checkboxes.
- Iteration log entry for v2 validation.

## Validation matrix

Primary target (regression + v2 fields):

| Target | Prompt | Expected v2 signals |
|---|---|---|
| `facebook/react` | `"search for facebook/react and get the latest release info"` | Non-empty `published_at`, multi-line `release_notes`, `downloads` includes Source code zip/tar.gz |

Secondary spot-check (optional):

| Target | Why |
|---|---|
| `microsoft/vscode` | Long release title, many assets |
| A repo with minimal/no Assets | Confirms `downloads: []` behavior |

## Tasks

- [x] Run canonical command with `--headed --debug` (see iteration log — initial 180s runs failed; 420s default + JSON salvage fixed).
- [x] Manually verify against GitHub UI:
  - [x] `published_at` populated (date string present)
  - [x] `release_notes` substantive (partial OK)
  - [x] `downloads` URLs follow GitHub archive pattern for extracted tag
- [x] Record step count, model, and sample output in `ITERATION-LOG.md`.
- [x] Update `README.md`:
  - [x] Output schema section with v2 fields
  - [x] Limitations: notes may be partial; URLs vision-extracted (may be imperfect)
  - [x] Remove "richer metadata" from limitations list (now in scope)
- [x] Update `ARCHITECTURE.md` action schema and system prompt sketch.
- [x] Tick v2 definition-of-done boxes in `IMPLEMENTATION.md`.
- [x] Mark phases 08–11 **Done** in phase files and phase index.

## Acceptance criteria

- Exit 0 on `facebook/react` with all v2 fields populated and correct latest stable semver (9 steps, `--headed --debug`, 420s default budget).
- Median step count ≤ 15 (v2 may add 2–4 scroll steps vs v1's 9) — observed 9 steps on successful v2 run.
- Reviewer can understand new fields from README alone.
- No selectors introduced (`rg "querySelector|locator\(|xpath" agent/` still clean).

## Dependencies

- Phases 08–10 complete.

## Risks

- **Flaky URL extraction**: if URLs fail verification, file in iteration log and tighten prompt in phase 09 (re-open) rather than adding DOM helpers.
- **Model variance**: cloud vs local models may differ; record which model produced the verified run in README "Tested with".

## Notes

- Formal multi-repo matrix remains optional (same stance as cancelled phase 07).
- Keep v1 "Tested with" block; add a separate v2 line with date and extended output snippet.
