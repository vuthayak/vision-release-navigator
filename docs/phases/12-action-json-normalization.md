# Phase 12 — Action JSON normalization (v3)

## Goal

Harden `parse_action_lenient()` for remaining Ollama malformations: unquoted JSON keys (`x:620` → `"x":620`).

## Status

- **State**: Done
- **Started**: 2026-05-30
- **Completed**: 2026-05-30

## Deliverables

- `_quote_bare_keys()` in `agent/action_parse.py`
- Integrated into `_loads_json()` lenient candidate chain
- Unit tests in `tests/test_action_parse.py`

## Tasks

- [x] Add `_quote_bare_keys()` — quotes bare identifier keys after `{` or `,`, outside string literals.
- [x] Wire into lenient parse path before `json.loads`, salvage, and `ast.literal_eval`.
- [x] Parametrized tests for mixed quoted/unquoted keys and fully bare-key objects.
- [x] Existing lenient cases unchanged (14 tests pass).

## Acceptance criteria

- [x] `pytest tests/test_action_parse.py` green.
- [x] Cases like `{"action":"click",x:620,y:85}` and `{action:"click",x:100,y:200}` parse via `parse_action_lenient()`.

## Dependencies

- v2 complete (phases 08–11).

## Notes

- Strict `parse_action()` (Gemini) unchanged — structured output is reliable enough without repair.
