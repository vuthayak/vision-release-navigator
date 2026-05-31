"""Tests for lenient action JSON parsing and normalization."""

from __future__ import annotations

import pytest

from agent.action_parse import parse_action, parse_action_lenient
from agent.schema import ClickAction, ScrollAction


@pytest.mark.parametrize(
    ("raw", "expected_action", "expected_fields"),
    [
        (
            '{"action":"click","x":620,"y":85,"reasoning":"open search"}',
            "click",
            {"x": 620, "y": 85, "reasoning": "open search"},
        ),
    ],
)
def test_parse_action_strict(raw: str, expected_action: str, expected_fields: dict) -> None:
    action = parse_action(raw)
    assert action.action == expected_action
    dumped = action.model_dump()
    for key, value in expected_fields.items():
        assert dumped[key] == value


def test_parse_action_strict_rejects_invalid_json() -> None:
    with pytest.raises(Exception):
        parse_action("not json")


@pytest.mark.parametrize(
    ("raw", "expected_action", "expected_fields"),
    [
        (
            '```json\n{"action":"click","x":100,"y":200}\n```',
            "click",
            {"x": 100, "y": 200, "reasoning": ""},
        ),
        (
            '{"action":"click","x":620,"y":85,"reasoning":"open search"}',
            "click",
            {"x": 620, "y": 85, "reasoning": "open search"},
        ),
        (
            '{"action":"click","x":620,"y":85,',
            "click",
            {"x": 620, "y": 85, "reasoning": ""},
        ),
        (
            '{"action":"wait","ms":500',
            "wait",
            {"ms": 500, "reasoning": ""},
        ),
        (
            "{'action': 'click', 'x': 50, 'y': 75, 'reasoning': 'tap'}",
            "click",
            {"x": 50, "y": 75, "reasoning": "tap"},
        ),
        (
            '{"action":"click","x":[830,45],"reasoning":"menu"}',
            "click",
            {"x": 830, "y": 45, "reasoning": "menu"},
        ),
        (
            '{"action":"scroll","amount":2,"reasoning":"read notes"}',
            "scroll",
            {"direction": "down", "amount": 2, "reasoning": "read notes"},
        ),
        (
            '{"action":"click",x:620,y:85,"reasoning":"tap"}',
            "click",
            {"x": 620, "y": 85, "reasoning": "tap"},
        ),
        (
            '{"action":"scroll",direction:"down",amount:2,"reasoning":"read notes"}',
            "scroll",
            {"direction": "down", "amount": 2, "reasoning": "read notes"},
        ),
        (
            '{"action":"scroll","amount":-1,"reasoning":"scroll up"}',
            "scroll",
            {"direction": "up", "amount": 1, "reasoning": "scroll up"},
        ),
        (
            '{action:"click",x:100,y:200}',
            "click",
            {"x": 100, "y": 200, "reasoning": ""},
        ),
        (
            '{"action":"click","x":40, 149,"reasoning":"tap"}',
            "click",
            {"x": 40, "y": 149, "reasoning": "tap"},
        ),
        (
            '{"action":"click","x":112, y":129,"reasoning":"sidebar"}',
            "click",
            {"x": 112, "y": 129, "reasoning": "sidebar"},
        ),
    ],
)
def test_parse_action_lenient(raw: str, expected_action: str, expected_fields: dict) -> None:
    action = parse_action_lenient(raw)
    assert action.action == expected_action
    dumped = action.model_dump()
    for key, value in expected_fields.items():
        assert dumped[key] == value


def test_parse_action_lenient_click_types() -> None:
    action = parse_action_lenient('{"action":"click","x":[830,45],"reasoning":"menu"}')
    assert isinstance(action, ClickAction)
    assert action.x == 830
    assert action.y == 45


def test_parse_action_lenient_scroll_default_direction() -> None:
    action = parse_action_lenient('{"action":"scroll","amount":1,"reasoning":"down"}')
    assert isinstance(action, ScrollAction)
    assert action.direction == "down"
