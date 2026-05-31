"""Retry orchestration for vision model action parsing."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable

from pydantic import ValidationError

from agent.action_parse import action_retry_message, parse_action
from agent.schema import Action


def _log_invalid_action_json(
    provider: str,
    err: Exception,
    raw: str,
    *,
    after_retry: bool = False,
) -> None:
    suffix = " after retry" if after_retry else ""
    preview = raw.replace("\n", "\\n")[:300]
    print(
        f"[vision:{provider}] invalid JSON{suffix}: {err} raw={preview!r}",
        file=sys.stderr,
    )


def parse_action_with_retry(
    raw: str,
    *,
    provider: str,
    retry_fn: Callable[[str], str],
    parse_fn: Callable[[str], Action] = parse_action,
    debug: bool = False,
    make_error: Callable[[Exception], Exception],
) -> Action:
    """Parse model output, retrying once via *retry_fn* when JSON or schema validation fails."""
    try:
        return parse_fn(raw)
    except (json.JSONDecodeError, ValidationError) as first_err:
        if debug:
            _log_invalid_action_json(provider, first_err, raw)
        retry_raw = retry_fn(action_retry_message(raw, first_err))
        try:
            return parse_fn(retry_raw)
        except (json.JSONDecodeError, ValidationError) as retry_err:
            if debug:
                _log_invalid_action_json(provider, retry_err, retry_raw, after_retry=True)
            raise make_error(retry_err) from retry_err


def decide_with_retry(
    *,
    provider: str,
    call_initial: Callable[[], tuple[str, object | None]],
    call_retry: Callable[[str, str], tuple[str, object | None]],
    log_debug: Callable[[object], None] | None,
    parse_fn: Callable[[str], Action],
    debug: bool,
    make_error: Callable[[Exception], Exception],
) -> Action:
    """Shared vision-backend skeleton: initial model call, optional debug log, parse with retry."""
    raw, debug_ctx = call_initial()
    if debug and log_debug is not None and debug_ctx is not None:
        log_debug(debug_ctx)

    def retry_fn(retry_text: str) -> str:
        retry_raw, retry_debug_ctx = call_retry(raw, retry_text)
        if debug and log_debug is not None and retry_debug_ctx is not None:
            log_debug(retry_debug_ctx)
        return retry_raw

    return parse_action_with_retry(
        raw,
        provider=provider,
        retry_fn=retry_fn,
        parse_fn=parse_fn,
        debug=debug,
        make_error=make_error,
    )
