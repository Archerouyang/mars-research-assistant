#!/usr/bin/env python3
"""Shared Board visual seam backed by purpose-specific adapters."""

from __future__ import annotations

import copy
from typing import Any, Mapping

from board_visual_contract import BoardVisualAdapter, BoardVisualError, required_text
import instrument_board_visual
import macro_board_visual
import portfolio_board_visual
import price_action_board_visual


ADAPTERS: Mapping[str, BoardVisualAdapter] = {
    "macro": BoardVisualAdapter(macro_board_visual.normalize, macro_board_visual.render),
    "instrument": BoardVisualAdapter(
        instrument_board_visual.normalize,
        instrument_board_visual.render,
    ),
    "portfolio": BoardVisualAdapter(
        portfolio_board_visual.normalize,
        portfolio_board_visual.render,
    ),
    "price_action": BoardVisualAdapter(
        price_action_board_visual.normalize,
        price_action_board_visual.render,
    ),
}


def normalize_board_visual(value: Any, result_kind: str) -> dict[str, Any] | None:
    """Normalize a visual through its registered purpose-specific adapter."""

    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise BoardVisualError("visual_invalid")
    visual = copy.deepcopy(dict(value))
    adapter_name = required_text(visual, "adapter")
    adapter = ADAPTERS.get(adapter_name)
    if adapter is None or adapter_name != result_kind:
        raise BoardVisualError("visual_adapter_invalid")
    return adapter.normalize(visual)


def render_board_visual(visual: Mapping[str, Any] | None, privacy: str) -> bytes | None:
    """Render a normalized visual without inspecting its purpose payload."""

    if visual is None:
        return None
    adapter = ADAPTERS.get(str(visual.get("adapter")))
    if adapter is None:
        raise BoardVisualError("visual_adapter_invalid")
    return adapter.render(visual, privacy)
