# Phase 03 — Vision client

## Goal

Build the vision layer: Pydantic action schema, system prompt, and provider clients that turn a screenshot + prompt into a validated `Action`.

## Status

- **State**: Done
- **Started**: 2026-05-28
- **Completed**: 2026-05-30

## Deliverables

- `agent/schema.py` — `Action` discriminated union, `SYSTEM_PROMPT`, `parse_action()`, `build_user_text()`, `action_retry_message()`.
- `agent/ollama_client.py` — `OllamaVisionClient` for Ollama Cloud or local Ollama.
- `agent/gemini_client.py` — `GeminiVisionClient` (optional fallback).
- `agent/vision.py` — `create_vision_client()` factory and `VisionClient` protocol.

> **Current layout (post–v2 refactor):** `SYSTEM_PROMPT` → `prompts.py`; parsing/normalization/retry nudge → `action_parse.py`; `decide_with_retry()` / `parse_action_with_retry()` → `vision_parse.py`; shared defaults → `defaults.py`; `VisionParseError` → `errors.py`. `schema.py` retains Pydantic models and `validate_action()` only.

## File layout

| File | Responsibility |
|---|---|
| `schema.py` | Action types, system prompt, robust JSON parsing |
| `ollama_client.py` | Ollama `chat()` with base64 image, `format=ACTION_JSON_SCHEMA` |
| `gemini_client.py` | Gemini structured output via `response_json_schema` |
| `vision.py` | Provider selection (`ollama` default, `gemini` optional) |

## Action schema

Defined in `agent/schema.py`:

```python
Action = Annotated[
    Union[ClickAction, TypeAction, PressKeyAction, ScrollAction, WaitAction, DoneAction],
    Field(discriminator="action"),
]
```

Each variant includes a `reasoning: str` field (used for logging; may be empty if the model omits it).

## Tasks

- [x] Define the schema in `agent/schema.py`.
- [x] Implement `OllamaVisionClient` with cloud (`https://ollama.com` + API key) and local support.
- [x] Implement `GeminiVisionClient` as optional fallback.
- [x] `decide_next_action`: send system prompt + user text + screenshot; parse and validate response.
- [x] Robust `parse_action()`: strip fences, extract JSON object, repair trailing commas, fill missing `reasoning`.
- [x] Retry once on `JSONDecodeError` or `ValidationError` via `action_retry_message()`.
- [x] Format history compactly — only `action` + `reasoning`; cap reasoning at ~200 chars.
- [x] Expose `SYSTEM_PROMPT` as a module-level constant.
- [x] Update `requirements.txt` (`ollama`, `google-genai`) and `.env.example`.

## System prompt outline

1. **Role**: vision-driven browser agent, one action per turn.
2. **Coordinate convention**: 0–1000 normalized; (500, 500) is center of viewport.
3. **Available actions**: brief list (Pydantic enforces after response).
4. **Task contract**: starting from the given URL, fulfill the user prompt and emit `done` with the five required fields from a **stable** release.
5. **No selectors**: explain you only see pixels; don't reference DOM concepts.
6. **GitHub heuristics** (without hardcoded selectors): search bar at top; visible "Releases" label; skip pre-releases; scroll if needed.
7. **Stop condition**: emit `done` only when all five fields are readable from a stable release.

## Acceptance criteria

- [x] `create_vision_client("ollama", ...).decide_next_action(...)` returns a valid `Action` against Ollama Cloud or local Ollama.
- [x] Schema validation rejects malformed actions.
- [x] No mention of CSS/XPath/`querySelector` in the system prompt source.
- [x] Connection and auth errors surface clearly at CLI (`OllamaConnectionError`).

## Dependencies

- Phase 01 scaffold.
- Ollama Cloud API key or local Ollama with a pulled vision model.

## Risks

- Vision models vary in JSON adherence — tolerant parsing + single retry mitigates most cases.
- Coordinate accuracy varies by model; expose `--model` to swap tags.
- The model may emit `done` prematurely — phase 04 loop rejects blank `done` payloads.

## Notes

- Keep the system prompt in source (not a file) so it's diffable in git.
- Log timing stats per step when `--debug` (`[vision:ollama:cloud]` / `[vision:gemini]` on stderr).
