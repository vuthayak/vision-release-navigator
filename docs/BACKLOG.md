# Backlog

Post–v2 ideas. v1 and v2 milestones are complete — see [IMPLEMENTATION.md](IMPLEMENTATION.md).

## Post–v2

- **Action JSON normalization** — harden `parse_action()` / `_normalize_action_payload()` for remaining Ollama malformations: unquoted keys (`y:666` → `"y":666`). Array coords and missing scroll `direction` are already handled in `action_parse.py`.
- **Any repository via CLI**: target a specific GitHub repo directly (e.g. `--repo owner/name` or a repo URL) instead of only navigating from a generic starting point like `https://github.com`.
- **Flexible natural-language queries**: let `--prompt` drive open-ended tasks, not just “latest release + tags” — e.g. *“find the latest release of openclaw and list its key features”*, compare releases, or summarize changelog highlights.
