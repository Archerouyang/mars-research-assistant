#!/usr/bin/env python3
"""Generate a display-first macro / regime mini-panel SVG.

Source Routing Boundary: Longbridge macrodata may provide market and macro time
series when authorized, but policy/news facts still require official /
reputable confirmation before they affect a trading plan.

No live broker reads. No live market data calls.
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from visual_artifacts import (
    coerce_series_points,
    default_display_output,
    manifest_record_from_args,
    save_manifest,
    slugify,
    write_text_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a display-first macro / regime mini-panel artifact."
    )
    parser.add_argument("input_json", help="Normalized macro/regime JSON input")
    parser.add_argument(
        "--display-output",
        help="Output SVG path for transient chat display; defaults to .scratch/visual-artifacts",
    )
    parser.add_argument("--artifact-id", default=None, help="Stable artifact identifier")
    parser.add_argument("--linked-context", default="", help="Plan or note this artifact supports")
    parser.add_argument("--data-source", default=None, help="Authorized or fixture data source label")
    parser.add_argument("--data-as-of", default=None, help="Data timestamp/date")
    parser.add_argument("--decision-summary", default="", help="Short user-facing decision summary")
    parser.add_argument("--manifest", help="Optional durable artifact manifest path")
    parser.add_argument(
        "--save-manifest",
        action="store_true",
        help="Opt in to writing a durable artifact manifest record",
    )
    return parser.parse_args()


def load_payload(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit("input JSON must be an object")
    return payload


def normalize_variables(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("variables") or payload.get("panels") or []
    if not isinstance(raw, list) or not raw:
        raise SystemExit("input JSON must include non-empty variables or panels list")

    variables: list[dict[str, Any]] = []
    for index, variable in enumerate(raw, start=1):
        if not isinstance(variable, dict):
            raise SystemExit(f"variable {index} must be an object")
        name = str(variable.get("name") or variable.get("ticker") or "").strip()
        if not name:
            raise SystemExit(f"variable {index} missing name")
        series = coerce_series_points(variable.get("series") or [], value_key="value")
        latest = variable.get("latest")
        if latest in (None, "") and series:
            latest = series[-1]["value"]
        try:
            latest_value = float(latest)
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"variable {index} has invalid latest value") from exc
        variables.append(
            {
                "name": name,
                "label": str(variable.get("label") or name),
                "unit": str(variable.get("unit") or ""),
                "latest": latest_value,
                "status": str(variable.get("status") or "watch"),
                "interpretation": str(variable.get("interpretation") or ""),
                "series": series,
            }
        )
    return variables


def _svg_escape(value: Any) -> str:
    return escape(str(value), quote=True)


def _status_color(status: str) -> str:
    lowered = status.lower()
    if lowered in {"constructive", "risk-on", "supportive", "benign"}:
        return "#1a7f37"
    if lowered in {"pressure", "warning", "risk-off", "stress"}:
        return "#cf222e"
    if lowered in {"mixed", "balanced", "watch"}:
        return "#9a6700"
    return "#57606a"


def _sparkline(points: list[dict[str, Any]], x: float, y: float, w: float, h: float) -> str:
    if len(points) < 2:
        return ""
    values = [float(point["value"]) for point in points]
    low = min(values)
    high = max(values)
    if high == low:
        high += 1
        low -= 1
    step = w / max(len(points) - 1, 1)
    coords = []
    for index, value in enumerate(values):
        px = x + index * step
        py = y + h - ((value - low) / (high - low)) * h
        coords.append(f"{px:.1f},{py:.1f}")
    return " ".join(coords)


def render_svg(payload: dict[str, Any]) -> str:
    variables = normalize_variables(payload)
    title = str(payload.get("title") or "Macro / Regime Mini-Panel")
    subtitle = str(payload.get("subtitle") or "display-first visual artifact")
    source = str(payload.get("source") or "provided")
    as_of = str(payload.get("as_of") or payload.get("data_as_of") or "")
    notes = payload.get("notes") or []

    width = 1200
    row_h = 86
    top = 104
    height = max(420, top + row_h * len(variables) + 118)
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_svg_escape(title)}">',
        "<style>",
        ".title{font:700 22px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".subtitle{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".label{font:600 14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".muted{font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".value{font:700 19px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="36" y="42">{_svg_escape(title)}</text>',
        f'<text class="subtitle" x="36" y="66">{_svg_escape(subtitle)}</text>',
    ]
    meta = f"source: {source}"
    if as_of:
        meta = f"{meta} | as of: {as_of}"
    svg.append(f'<text class="muted" x="36" y="86">{_svg_escape(meta)}</text>')

    for index, variable in enumerate(variables):
        y = top + index * row_h
        color = _status_color(variable["status"])
        unit = variable["unit"]
        value_label = f'{variable["latest"]:.2f}{unit}'
        svg.extend(
            [
                f'<rect x="36" y="{y}" width="1128" height="70" rx="6" fill="#fbfcfd" stroke="#d8dee4"/>',
                f'<circle cx="58" cy="{y + 35}" r="7" fill="{color}"/>',
                f'<text class="label" x="78" y="{y + 29}">{_svg_escape(variable["name"])}</text>',
                f'<text class="muted" x="78" y="{y + 51}">{_svg_escape(variable["label"])}</text>',
                f'<text class="value" x="246" y="{y + 42}">{_svg_escape(value_label)}</text>',
                f'<text class="muted" x="336" y="{y + 42}">{_svg_escape(variable["status"])}</text>',
            ]
        )
        points = _sparkline(variable["series"], 476, y + 14, 220, 42)
        if points:
            svg.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.2"/>'
            )
        interpretation = variable["interpretation"]
        if len(interpretation) > 76:
            interpretation = interpretation[:73] + "..."
        svg.append(
            f'<text class="muted" x="730" y="{y + 42}">{_svg_escape(interpretation)}</text>'
        )

    note_y = top + row_h * len(variables) + 20
    svg.append(
        f'<text class="muted" x="36" y="{note_y}">Source Routing Boundary: Longbridge macrodata can supply authorized series; policy/news require official / reputable confirmation.</text>'
    )
    for offset, note in enumerate(notes[:3], start=1):
        svg.append(
            f'<text class="muted" x="36" y="{note_y + offset * 22}">{_svg_escape(note)}</text>'
        )
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def main() -> None:
    args = parse_args()
    payload = load_payload(Path(args.input_json))
    title = str(payload.get("title") or "Macro / Regime Mini-Panel")
    artifact_id = args.artifact_id or slugify(title)
    repo_root = Path(__file__).resolve().parents[3]
    display_output = (
        Path(args.display_output)
        if args.display_output
        else default_display_output(repo_root, artifact_id)
    )

    write_text_artifact(display_output, render_svg(payload))
    print(f"display {display_output}")

    if args.save_manifest:
        if not args.manifest:
            raise SystemExit("--save-manifest requires --manifest")
        manifest_path = Path(args.manifest)
        record = manifest_record_from_args(
            artifact_id=artifact_id,
            artifact_type="macro_regime",
            mode="saved",
            linked_context=args.linked_context,
            data_source=args.data_source or str(payload.get("source") or "provided"),
            data_as_of=args.data_as_of or str(payload.get("as_of") or ""),
            image_path=display_output,
            html_path=None,
            decision_summary=args.decision_summary,
        )
        save_manifest(manifest_path, record)
        print(f"manifest {manifest_path}")


if __name__ == "__main__":
    main()
