# Backlog

Post–v3 ideas. v1, v2, and v3 are complete — see [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Post–v3

- **Any repository via CLI**: target a specific GitHub repo directly (e.g. `--repo owner/name` or a repo URL) instead of only navigating from a generic starting point like `https://github.com`. Deferred in v3 — autonomous navigation from `https://github.com` already works.
- **Flexible natural-language queries (output schema)**: let `--prompt` drive open-ended tasks with a flexible **output** shape — e.g. compare releases, summarize changelog highlights, or list key features as free text. Note: `--prompt` already accepts varied phrasing; the fixed eight-field `done` schema is the limitation. Would require new `DoneAction` fields and validation.

## Shipped in v3

- ~~**Action JSON normalization**~~ — `_quote_bare_keys()` in `action_parse.py` handles unquoted keys (`x:620` → `"x":620`). Array coords, missing scroll direction, truncated JSON salvage, and default `reasoning` were already handled.
