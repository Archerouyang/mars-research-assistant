#!/usr/bin/env python3
"""Render a display-first position-risk SVG from explicit exposure inputs.

Missing dimensions remain visibly unavailable. The renderer never imputes
positions, weights, broker exposure, or account totals.

No live broker reads. No order actions.
"""

from __future__ import annotations

import argparse
from html import escape
import json
from pathlib import Path
from typing import Any

from visual_artifacts import (
    default_display_output,
    manifest_record_from_args,
    save_manifest,
    slugify,
    write_text_artifact,
)


DIMENSIONS = (
    ("concentration", "concentration"),
    ("instrument", "instrument / product"),
    ("theme", "theme exposure"),
    ("broker", "broker exposure"),
)
BAR_COLORS = ("#24292f", "#57606a", "#8c959f", "#afb8c1", "#d0d7de")
FLAG_COLORS = {
    "risk": ("#cf222e", "#ffebe9"),
    "attention": ("#9a6700", "#fff8c5"),
    "ok": ("#1a7f37", "#dafbe1"),
    "info": ("#57606a", "#f6f8fa"),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_json", help="Explicit position-risk JSON input")
    parser.add_argument("--display-output", help="Output SVG path")
    parser.add_argument("--artifact-id", default=None)
    parser.add_argument("--linked-context", default="")
    parser.add_argument("--data-source", default=None)
    parser.add_argument("--data-as-of", default=None)
    parser.add_argument("--decision-summary", default="")
    parser.add_argument("--manifest")
    parser.add_argument("--save-manifest", action="store_true")
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("input JSON must be an object")
    return payload


def xml(value: Any) -> str:
    return escape(str(value), quote=True)


def clip(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + "..."


def normalize_rows(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    raw = payload.get(key)
    if raw in (None, ""):
        return []
    if not isinstance(raw, list):
        raise SystemExit(f"{key} must be a list when provided")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"{key} row {index} must be an object")
        label = str(item.get("label") or "").strip()
        if not label:
            raise SystemExit(f"{key} row {index} missing label")
        try:
            weight = float(item["weight"])
        except KeyError as exc:
            raise SystemExit(f"{key} row {index} missing weight") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"{key} row {index} has invalid weight") from exc
        if not 0 <= weight <= 1:
            raise SystemExit(f"{key} row {index} weight must be between 0 and 1")
        rows.append({"label": label, "weight": weight})
    return rows


def normalize_flags(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw = payload.get("risk_flags") or []
    if not isinstance(raw, list):
        raise SystemExit("risk_flags must be a list when provided")
    flags: list[dict[str, str]] = []
    for index, item in enumerate(raw, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"risk flag {index} must be an object")
        label = str(item.get("label") or "").strip()
        if not label:
            raise SystemExit(f"risk flag {index} missing label")
        severity = str(item.get("severity") or "info").lower()
        if severity not in FLAG_COLORS:
            raise SystemExit(f"risk flag {index} has unsupported severity")
        flags.append(
            {
                "severity": severity,
                "label": label,
                "detail": str(item.get("detail") or "").strip(),
            }
        )
    return flags


def render_empty_panel(svg: list[str], *, x: int, y: int, width: int, height: int) -> None:
    svg.extend(
        [
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="#f6f8fa" stroke="#d0d7de"/>',
            f'<text class="muted" x="{x + 18}" y="{y + height // 2 + 5}">Not provided</text>',
        ]
    )


def render_concentration(
    svg: list[str], rows: list[dict[str, Any]], *, x: int, y: int, width: int
) -> None:
    svg.append(f'<text class="section" x="{x}" y="{y}">concentration</text>')
    panel_y = y + 16
    panel_h = 244
    if not rows:
        render_empty_panel(svg, x=x, y=panel_y, width=width, height=panel_h)
        return
    svg.append(
        f'<rect x="{x}" y="{panel_y}" width="{width}" height="{panel_h}" rx="6" fill="#ffffff" stroke="#d0d7de"/>'
    )
    max_weight = max(row["weight"] for row in rows) or 1
    shown = rows[:6]
    for index, row in enumerate(shown):
        row_y = panel_y + 26 + index * 34
        bar_x = x + 138
        bar_w = int((width - 214) * row["weight"] / max_weight)
        svg.extend(
            [
                f'<text class="label" x="{x + 16}" y="{row_y + 13}">{xml(clip(row["label"], 18))}</text>',
                f'<rect x="{bar_x}" y="{row_y}" width="{width - 214}" height="16" rx="3" fill="#eaeef2"/>',
                f'<rect x="{bar_x}" y="{row_y}" width="{bar_w}" height="16" rx="3" fill="#24292f"/>',
                f'<text class="value" x="{x + width - 62}" y="{row_y + 13}">{row["weight"]:.1%}</text>',
            ]
        )


def render_stacked(
    svg: list[str],
    title: str,
    rows: list[dict[str, Any]],
    *,
    x: int,
    y: int,
    width: int,
) -> None:
    svg.append(f'<text class="section" x="{x}" y="{y}">{xml(title)}</text>')
    panel_y = y + 16
    panel_h = 104
    if not rows:
        render_empty_panel(svg, x=x, y=panel_y, width=width, height=panel_h)
        return
    svg.append(
        f'<rect x="{x}" y="{panel_y}" width="{width}" height="{panel_h}" rx="6" fill="#ffffff" stroke="#d0d7de"/>'
    )
    total = sum(row["weight"] for row in rows)
    scale = max(total, 1.0)
    bar_x = x + 16
    bar_y = panel_y + 18
    bar_w = width - 32
    cursor = bar_x
    for index, row in enumerate(rows):
        segment = bar_w * row["weight"] / scale
        svg.append(
            f'<rect x="{cursor:.1f}" y="{bar_y}" width="{segment:.1f}" height="20" fill="{BAR_COLORS[index % len(BAR_COLORS)]}"/>'
        )
        cursor += segment
    legend_y = panel_y + 58
    col_width = max((width - 32) // min(len(rows), 3), 1)
    for index, row in enumerate(rows[:3]):
        lx = x + 16 + index * col_width
        svg.extend(
            [
                f'<rect x="{lx}" y="{legend_y}" width="10" height="10" fill="{BAR_COLORS[index % len(BAR_COLORS)]}"/>',
                f'<text class="muted" x="{lx + 16}" y="{legend_y + 9}">{xml(clip(row["label"], 14))} {row["weight"]:.1%}</text>',
            ]
        )


def render_flags(
    svg: list[str], flags: list[dict[str, str]], *, x: int, y: int, width: int
) -> None:
    svg.append(f'<text class="section" x="{x}" y="{y}">material risk flags</text>')
    panel_y = y + 16
    if not flags:
        render_empty_panel(svg, x=x, y=panel_y, width=width, height=76)
        return
    card_gap = 14
    card_w = (width - card_gap * (min(len(flags), 3) - 1)) / min(len(flags), 3)
    for index, flag in enumerate(flags[:3]):
        card_x = x + index * (card_w + card_gap)
        stroke, fill = FLAG_COLORS[flag["severity"]]
        svg.extend(
            [
                f'<rect x="{card_x:.1f}" y="{panel_y}" width="{card_w:.1f}" height="76" rx="6" fill="{fill}" stroke="{stroke}"/>',
                f'<text class="flag" x="{card_x + 14:.1f}" y="{panel_y + 25}" style="fill:{stroke}">{xml(clip(flag["label"], 34))}</text>',
                f'<text class="muted" x="{card_x + 14:.1f}" y="{panel_y + 50}">{xml(clip(flag["detail"], 54))}</text>',
            ]
        )


def render_svg(payload: dict[str, Any]) -> str:
    rows = {key: normalize_rows(payload, key) for key, _title in DIMENSIONS}
    flags = normalize_flags(payload)
    title = str(payload.get("title") or "Position Risk")
    subtitle = str(payload.get("subtitle") or "Explicit exposure inputs only")
    status = str(payload.get("data_status") or "partial")
    source = str(payload.get("source") or "provided")
    as_of = str(payload.get("as_of") or "")
    any_exposure = any(rows.values())

    width = 1200
    height = 670
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{xml(title)}">',
        "<style>",
        ".title{font:700 24px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2328}",
        ".subtitle{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".section{font:700 14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2328}",
        ".label{font:600 12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2328}",
        ".value{font:600 12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#1f2328}",
        ".muted{font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".flag{font:700 13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="36" y="42">{xml(title)}</text>',
        f'<text class="subtitle" x="36" y="67">{xml(subtitle)}</text>',
        f'<text class="subtitle" x="36" y="90">source: {xml(source)} | status: {xml(status)}{xml(" | as of: " + as_of) if as_of else ""}</text>',
    ]
    if not any_exposure:
        svg.append('<text class="section" x="36" y="122">No exposure data provided</text>')

    render_concentration(svg, rows["concentration"], x=36, y=148, width=548)
    render_stacked(svg, "instrument / product", rows["instrument"], x=616, y=148, width=548)
    render_stacked(svg, "theme exposure", rows["theme"], x=616, y=282, width=548)
    render_stacked(svg, "broker exposure", rows["broker"], x=616, y=416, width=548)
    render_flags(svg, flags, x=36, y=548, width=1128)
    svg.append(
        '<text class="muted" x="36" y="656">Decision support only. Missing dimensions remain unavailable. No live broker reads. No order actions.</text>'
    )
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main() -> None:
    args = parse_args()
    payload = load_payload(Path(args.input_json))
    title = str(payload.get("title") or "Position Risk")
    artifact_id = args.artifact_id or slugify(title)
    repo_root = Path(__file__).resolve().parents[3]
    output = (
        Path(args.display_output)
        if args.display_output
        else default_display_output(repo_root, artifact_id)
    )
    write_text_artifact(output, render_svg(payload))
    print(f"display {output}")

    if args.save_manifest:
        if not args.manifest:
            raise SystemExit("--save-manifest requires --manifest")
        save_manifest(
            Path(args.manifest),
            manifest_record_from_args(
                artifact_id=artifact_id,
                artifact_type="position_risk",
                mode="saved",
                linked_context=args.linked_context,
                data_source=args.data_source or str(payload.get("source") or "provided"),
                data_as_of=args.data_as_of or str(payload.get("as_of") or ""),
                image_path=output,
                html_path=None,
                decision_summary=args.decision_summary,
            ),
        )
        print(f"manifest {args.manifest}")


if __name__ == "__main__":
    main()
