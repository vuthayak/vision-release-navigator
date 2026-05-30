# Phase 05 — CLI wiring & output

## Goal

Turn `navigate.py` into the real entrypoint: parse args, wire the loop, format output, handle exit codes.

## Status

- **State**: Done
- **Started**: 2026-05-28
- **Completed**: 2026-05-30

## Deliverables

- `navigate.py` with full argparse, env loading, orchestration, and JSON output.

## CLI surface

```bash
python navigate.py \
  --url "https://github.com" \
  --prompt "search for openclaw and get the current release and related tags" \
  [--provider ollama|gemini] \
  [--model qwen2.5vl:3b] \
  [--ollama-host https://ollama.com] \
  [--max-steps 25] \
  [--headless | --headed] \
  [--output release.json] \
  [--debug]
```

| Flag | Required | Default | Purpose |
|---|---|---|---|
| `--url` | yes | — | Starting page (typically https://github.com). |
| `--prompt` | yes | — | Free-form natural-language goal. |
| `--provider` | no | `ollama` (or `VISION_PROVIDER`) | `ollama` or `gemini`. |
| `--model` | no | `qwen2.5vl:3b` / `gemini-2.5-flash` | Vision model id for the chosen provider. |
| `--ollama-host` | no | `https://ollama.com` | Ollama API base URL. |
| `--max-steps` | no | 25 | Hard cap on agent loop iterations. |
| `--headless` / `--headed` | no | `--headed` | Browser visibility (mutually exclusive). |
| `--output` | no | — | If set, write JSON here as well as stdout. |
| `--debug` | no | off | Dump screenshots + raw actions to `screenshots/`. |

## Environment variables

Loaded from `.env` via `python-dotenv`:

| Variable | Required when | Purpose |
|---|---|---|
| `VISION_PROVIDER` | — | Default provider (`ollama` or `gemini`) |
| `OLLAMA_HOST` | ollama | API base URL |
| `OLLAMA_API_KEY` | Ollama Cloud | Bearer token |
| `OLLAMA_MODEL` | — | Default Ollama model tag |
| `GOOGLE_API_KEY` | `--provider gemini` | Gemini API key |

## Tasks

- [x] Implement argparse with the table above (`store_true` / mutually exclusive group for `--headless`/`--headed`).
- [x] Load `.env` via `python-dotenv`; error clearly if Ollama Cloud key missing or Gemini key missing.
- [x] Construct `Browser` + vision client via `create_vision_client()`, navigate to `--url`, call `run_agent_loop`.
- [x] On success, extract the five fields from the `DoneAction` and `print(json.dumps(payload, indent=2))`.
- [x] If `--output`, also write to disk (with newline at EOF).
- [x] Exit codes: `0` success, `1` agent failure (max steps / time budget / blank done), `2` config error.
- [x] Always close the browser in a `finally` block.
- [x] Handle `OllamaConnectionError`, Gemini auth errors, and `KeyboardInterrupt`.

## Output JSON shape

```json
{
  "repository": "openclaw/openclaw",
  "latest_release": "OpenClaw 1.0.0",
  "version": "1.0.0",
  "tag": "v1.0.0",
  "author": "Galaxyman0"
}
```

Fields are always strings; empty string (`""`) is allowed only when the agent could not determine that field (and exit code is non-zero).

## Acceptance criteria

- [x] `python navigate.py --url https://github.com --prompt "..."` produces valid JSON on stdout.
- [x] `python navigate.py` (no args) prints usage and exits 2.
- [x] Missing Ollama Cloud key or unreachable Ollama produces a clear error and exit 2.
- [x] Ctrl-C cleanly closes the browser.

## Dependencies

- All previous phases.

## Risks

- Mixing logging with JSON output corrupts stdout. **Convention**: all logs go to stderr. Only the final JSON touches stdout.
- `--headed` mode requires a display server. CI / headless smoke tests must override to `--headless`.

## Notes

- Keep the file readable top-to-bottom; one `main()`, one `run()`, no clever decorators. This is the file reviewers will read first.
