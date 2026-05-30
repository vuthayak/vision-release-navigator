#!/usr/bin/env python3
"""CLI entrypoint for the vision-driven GitHub release navigator."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.genai import errors as genai_errors

from agent.browser import Browser
from agent.loop import AgentLoopError, run_agent_loop
from agent.ollama_client import OllamaConnectionError
from agent.schema import DoneAction
from agent.vision import (
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OLLAMA_HOST,
    DEFAULT_OLLAMA_MODEL,
    create_vision_client,
    ollama_requires_api_key,
)


class ConfigError(Exception):
    """Missing or invalid configuration."""


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Navigate a website with a vision model and extract GitHub release metadata.",
    )
    parser.add_argument("--url", required=True, help="Starting page URL (e.g. https://github.com)")
    parser.add_argument("--prompt", required=True, help="Natural-language navigation goal")
    parser.add_argument(
        "--provider",
        choices=["ollama", "gemini"],
        default=os.environ.get("VISION_PROVIDER", "ollama"),
        help="Vision backend (default: ollama, or VISION_PROVIDER env)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model id (default: qwen2.5vl:3b for ollama, gemini-2.5-flash for gemini)",
    )
    parser.add_argument(
        "--ollama-host",
        default=os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST),
        help=f"Ollama base URL (default: {DEFAULT_OLLAMA_HOST} for cloud; use http://localhost:11434 for local)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=25,
        help="Maximum agent loop iterations (default: 25)",
    )
    visibility = parser.add_mutually_exclusive_group()
    visibility.add_argument("--headless", action="store_true", help="Run browser headless")
    visibility.add_argument("--headed", action="store_true", help="Show browser window (default)")
    parser.add_argument(
        "--output",
        metavar="PATH",
        help="Also write final JSON to this file",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save step screenshots and actions under screenshots/",
    )
    return parser


def _resolve_model(provider: str, cli_model: str | None) -> str:
    if cli_model:
        return cli_model
    if provider == "ollama":
        return os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
    return DEFAULT_GEMINI_MODEL


def _done_payload(done: DoneAction) -> dict[str, str]:
    return {
        "repository": done.repository,
        "latest_release": done.latest_release,
        "version": done.version,
        "tag": done.tag,
        "author": done.author,
    }


def _emit_result(payload: dict[str, str], output_path: str | None) -> None:
    text = json.dumps(payload, indent=2)
    print(text)
    if output_path:
        Path(output_path).write_text(text + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> int:
    load_dotenv()
    provider = args.provider.strip().lower()
    model = _resolve_model(provider, args.model)

    api_key = os.environ.get("GOOGLE_API_KEY", "").strip()
    ollama_api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if provider == "gemini" and not api_key:
        raise ConfigError(
            "GOOGLE_API_KEY is not set. Add it to .env or use --provider ollama."
        )
    if provider == "ollama" and ollama_requires_api_key(args.ollama_host) and not ollama_api_key:
        raise ConfigError(
            "OLLAMA_API_KEY is not set. Create a key at https://ollama.com/settings/keys "
            "and add it to .env for Ollama Cloud."
        )

    headless = bool(args.headless)
    debug_dir = Path("screenshots") if args.debug else None

    try:
        vision = create_vision_client(
            provider,
            model=model,
            api_key=api_key or None,
            ollama_host=args.ollama_host,
            ollama_api_key=ollama_api_key or None,
        )
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc

    browser = Browser()
    try:
        browser.start(headless=headless)
        browser.goto(args.url)
        done = run_agent_loop(
            browser,
            vision,
            user_prompt=args.prompt,
            max_steps=args.max_steps,
            debug_dir=debug_dir,
            debug_vision=args.debug,
        )
    finally:
        browser.close()

    payload = _done_payload(done)
    _emit_result(payload, args.output)
    return 0


def main() -> None:
    load_dotenv()
    parser = _build_parser()
    args = parser.parse_args()
    try:
        code = run(args)
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    except OllamaConnectionError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
    except genai_errors.ClientError as exc:
        if exc.code == 400 and "API key not valid" in str(exc):
            print(
                "Gemini rejected GOOGLE_API_KEY (invalid or revoked). "
                "Create a new key at https://aistudio.google.com/apikey and update .env:\n"
                "  GOOGLE_API_KEY=your_key_with_no_quotes_or_spaces",
                file=sys.stderr,
            )
            sys.exit(2)
        print(f"Gemini API error: {exc}", file=sys.stderr)
        sys.exit(1)
    except AgentLoopError as exc:
        print(f"Agent failed: {exc}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(code)


if __name__ == "__main__":
    main()
