#!/usr/bin/env python3
"""Shared presentational shell primitives for purpose-specific research Boards."""

from __future__ import annotations

from html import escape
from typing import Mapping, Sequence


RESEARCH_BRIEF_SHELL_VERSION = "v1"


def render_main_open(board_id: str) -> str:
    """Open a Board root with the stable shared-shell marker."""

    return f'<main id="{escape(board_id)}" data-research-brief-shell="{RESEARCH_BRIEF_SHELL_VERSION}">'


def render_masthead(
    *,
    eyebrow: str,
    title: str,
    question: str,
    snapshot_id: str,
    decision_cutoff: str,
    privacy: str,
) -> str:
    """Render common Board provenance and decision-question framing."""

    return f"""<header class="masthead">
<div><p class="eyebrow">{escape(eyebrow)}</p><h1>{escape(title)}</h1><p class="lede">{escape(question)}</p></div>
<dl class="provenance" aria-label="Provenance">
<div><dt>Provenance</dt><dd>{escape(snapshot_id)}</dd></div>
<div><dt>Decision cutoff</dt><dd>{escape(decision_cutoff)}</dd></div>
<div><dt>Privacy</dt><dd>{escape(privacy)}</dd></div>
</dl>
</header>"""


def render_view_tabs(
    views: Sequence[str], default_view: str, view_ids: Mapping[str, str], aria_label: str
) -> str:
    """Render the common accessible view control row."""

    controls = "".join(
        f'<button type="button" role="tab" id="tab-{escape(view_ids[view])}" '
        f'data-view-target="{escape(view_ids[view])}" aria-controls="view-{escape(view_ids[view])}" '
        f'aria-selected="{str(view == default_view).lower()}">{escape(view)}</button>'
        for view in views
    )
    return f'<nav class="view-tabs" role="tablist" aria-label="{escape(aria_label)}">{controls}</nav>'


def render_summary(
    items: Sequence[tuple[str, str, str | None]], aria_label: str
) -> str:
    """Render a shared summary row while callers retain their decision content."""

    rows = "".join(
        f'<article><span>{escape(label)}</span><strong>{escape(value)}</strong>'
        f'{f"<p>{escape(detail)}</p>" if detail else ""}</article>'
        for label, value, detail in items
    )
    return f'<section class="summary" aria-label="{escape(aria_label)}">{rows}</section>'


def render_decision_framing(label: str, value: str) -> str:
    """Render the common non-prescriptive decision framing surface."""

    return f'<p class="decision-framing"><strong>{escape(label)}:</strong> {escape(value)}</p>'


def render_evidence_rail(
    snapshot: Mapping[str, object],
    modules: Sequence[Mapping[str, object]],
    minimum_evidence: str,
) -> str:
    """Render source coverage and visible gaps from already-validated snapshot data."""

    sources = "".join(
        f'<li><strong>{escape(str(source["alias"]))}</strong><span class="source-time">'
        f'{escape(str(source["priority"]))} · {escape(str(source["freshness_status"]))} · '
        f'{escape(str(source["as_of"]))}</span></li>'
        for source in snapshot["source_registry"]  # type: ignore[index]
    )
    gaps = [
        module
        for module in modules
        if module["evidence_state"] != "complete" or module["gap_reason"]
    ]
    gap_rows = "".join(
        f'<li><strong>{escape(str(module["id"]))}</strong><span class="source-time">'
        f'{escape(str(module["evidence_state"]))} · '
        f'{escape(str(module["gap_reason"]) or "No explicit gap")}</span></li>'
        for module in gaps
    ) or "<li>No evidence gaps in this snapshot.</li>"
    return f"""<aside class="evidence-rail" aria-labelledby="evidence-rail-title">
<h2 id="evidence-rail-title">Evidence rail</h2><ul>{sources}</ul>
<h3>Visible gaps</h3><ul>{gap_rows}</ul>
<p><strong>Minimum evidence:</strong> {escape(minimum_evidence)}</p>
</aside>"""


def render_safety_footer(message: str) -> str:
    """Render the common safety footer."""

    return f"<footer><h2>Safety boundary</h2><p>{escape(message)}</p></footer>"


def shared_shell_styles() -> str:
    """Provide stable shared layout tokens for every Research brief shell."""

    return """
[data-research-brief-shell]{--research-shell-version:v1;}
""".strip()
