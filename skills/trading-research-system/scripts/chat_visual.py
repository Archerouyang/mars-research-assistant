#!/usr/bin/env python3
"""Shared chat visual seam backed by purpose-specific adapters."""

from __future__ import annotations

import copy
from typing import Any, Mapping

from chat_visual_contract import ChatVisualAdapter, ChatVisualError, required_text
import instrument_chat_visual
import macro_chat_visual
import portfolio_chat_visual
import price_action_chat_visual


ADAPTERS: Mapping[str, ChatVisualAdapter] = {
    "macro": ChatVisualAdapter(macro_chat_visual.normalize, macro_chat_visual.render),
    "instrument": ChatVisualAdapter(
        instrument_chat_visual.normalize,
        instrument_chat_visual.render,
    ),
    "portfolio": ChatVisualAdapter(
        portfolio_chat_visual.normalize,
        portfolio_chat_visual.render,
    ),
    "price_action": ChatVisualAdapter(
        price_action_chat_visual.normalize,
        price_action_chat_visual.render,
    ),
}


def normalize_chat_visual(value: Any, result_kind: str) -> dict[str, Any] | None:
    """Normalize a visual through its registered purpose-specific adapter."""

    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ChatVisualError("visual_invalid")
    visual = copy.deepcopy(dict(value))
    adapter_name = required_text(visual, "adapter")
    adapter = ADAPTERS.get(adapter_name)
    if adapter is None or adapter_name != result_kind:
        raise ChatVisualError("visual_adapter_invalid")
    return adapter.normalize(visual)


def render_chat_visual(visual: Mapping[str, Any] | None, privacy: str) -> bytes | None:
    """Render a normalized visual without inspecting its purpose payload."""

    if visual is None:
        return None
    adapter = ADAPTERS.get(str(visual.get("adapter")))
    if adapter is None:
        raise ChatVisualError("visual_adapter_invalid")
    return adapter.render(visual, privacy)
