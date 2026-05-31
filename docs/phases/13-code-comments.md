# Phase 13 — Line-level code comments (v3)

## Goal

Add inline comments on non-obvious logic so a reviewer can follow the agent loop and parsing pipeline without guessing intent.

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- Inline comments in core `agent/` modules and `navigate.py` (no behavior changes).

## Files annotated

| File | Focus |
|---|---|
| `agent/loop.py` | Per-iteration flow, stale detection, history cap, incomplete `done` rejection |
| `agent/action_parse.py` | Repair/salvage pipeline in `_loads_json`, normalization rules |
| `agent/vision_parse.py` | Single-retry contract, debug logging |
| `agent/browser.py` | Coordinate denorm clamping, networkidle swallow, scroll delta |
| `agent/schema.py` | Discriminated union, `is_incomplete_extraction` heuristics |
| `agent/ollama_client.py` / `agent/gemini_client.py` | Structured output, lenient vs strict parse choice |
| `agent/vision.py` | Factory routing |
| `navigate.py` | CLI → browser → loop → emit sections |

Skipped (already self-explanatory): `defaults.py`, `errors.py`, `__init__.py`.

## Tasks

- [x] Annotate loop orchestration and constants.
- [x] Annotate JSON repair pipeline and normalization.
- [x] Annotate browser coordinate and navigation waits.
- [x] Annotate schema validation heuristics.
- [x] Annotate vision backend wiring.
- [x] Full test suite still passes (41 tests).

## Acceptance criteria

- [x] Comments explain *why*, not restate obvious assignments.
- [x] No functional changes introduced by commenting pass.

## Dependencies

- Phase 12 (normalization code commented as part of this pass).
