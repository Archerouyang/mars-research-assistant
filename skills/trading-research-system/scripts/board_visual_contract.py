#!/usr/bin/env python3
"""Small shared contract for purpose-specific Board visual adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping


class BoardVisualError(ValueError):
    """Fail-closed Board visual error with a stable public code."""


@dataclass(frozen=True)
class BoardVisualAdapter:
    """Validation/normalization and rendering owned by one visual purpose."""

    normalize: Callable[[Mapping[str, Any]], dict[str, Any]]
    render: Callable[[Mapping[str, Any], str], bytes]


def required_text(value: Mapping[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise BoardVisualError(f"{key}_invalid")
    return item


def exact_fields(value: Mapping[str, Any], allowed: set[str], code: str) -> None:
    if set(value) - allowed:
        raise BoardVisualError(code)
