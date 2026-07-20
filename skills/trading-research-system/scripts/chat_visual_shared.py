#!/usr/bin/env python3
"""Small styling and serialization helpers shared by chat visual adapters."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _public_fixture_attr(privacy: Any) -> str:
    return ' data-public-fixture="true"' if privacy == "public_fixture" else ""


def _public_fixture_badge(privacy: Any) -> str:
    if privacy != "public_fixture":
        return ""
    return '<span class="viz-badge">演示数据，不可用于交易</span>'


def _base_css(root: str) -> str:
    return f"""
    #{root}{{width:100%;display:grid;gap:12px;color:var(--foreground)}}
    #{root} .viz-row{{justify-content:flex-start;gap:10px}}
    #{root} .viz-grid{{grid-template-columns:repeat(3,minmax(0,1fr))}}
    #{root} .viz-stat-value{{display:block}}
    #{root} .chart{{display:grid;gap:9px}}
    #{root} .bar-row{{display:grid;grid-template-columns:minmax(84px,.42fr) minmax(110px,1fr) minmax(64px,.28fr);align-items:center;gap:9px;cursor:pointer}}
    #{root} .bar-label{{font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
    #{root} .bar-track{{height:14px;overflow:hidden;background:var(--muted)}}
    #{root} .bar-fill{{width:var(--w);height:100%;min-width:2px;background:var(--series)}}
    #{root} .bar-value{{text-align:right;font-variant-numeric:tabular-nums}}
    #{root} .selected-detail{{min-height:22px;padding-top:8px;border-top:1px solid var(--border)}}
    #{root} table{{width:100%;border-collapse:collapse}}
    #{root} th,#{root} td{{padding:7px 8px;text-align:left;border-bottom:1px solid var(--border)}}
    #{root} th{{color:var(--muted-foreground);font-weight:500}}
    #{root} .compact-list{{margin:0;padding-left:20px}}
    @media(max-width:520px){{#{root} .viz-grid{{grid-template-columns:1fr}}#{root} .bar-row{{grid-template-columns:72px minmax(70px,1fr) 58px;gap:6px}}}}
  """.strip()



def _root_id(adapter: str, value: Mapping[str, Any]) -> str:
    encoded = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    return f"dailytrades-{adapter}-inline-{hashlib.sha256(encoded).hexdigest()[:10]}"


def _script_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _latest_value(points: Any) -> float | None:
    if not isinstance(points, list) or not points:
        return None
    try:
        return float(points[-1]["value"])
    except (KeyError, TypeError, ValueError):
        return None



def _num(value: Any) -> str:
    return f"{float(value):,.2f}".rstrip("0").rstrip(".")
