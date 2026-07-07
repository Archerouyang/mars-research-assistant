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
        thresholds = normalize_thresholds(variable, index)
        variables.append(
            {
                "name": name,
                "label": str(variable.get("label") or name),
                "unit": str(variable.get("unit") or ""),
                "latest": latest_value,
                "status": str(variable.get("status") or "watch"),
                "interpretation": str(variable.get("interpretation") or ""),
                "impact_path": str(variable.get("impact_path") or variable.get("impact") or ""),
                "thresholds": thresholds,
                "series": series,
            }
        )
    return variables


def normalize_thresholds(variable: dict[str, Any], variable_index: int) -> list[dict[str, Any]]:
    raw = variable.get("thresholds") or []
    if not isinstance(raw, list):
        raise SystemExit(f"variable {variable_index} thresholds must be a list when provided")

    thresholds: list[dict[str, Any]] = []
    for index, threshold in enumerate(raw, start=1):
        if not isinstance(threshold, dict):
            raise SystemExit(f"variable {variable_index} threshold {index} must be an object")
        try:
            value = float(threshold["value"])
        except KeyError as exc:
            raise SystemExit(f"variable {variable_index} threshold {index} missing value") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"variable {variable_index} threshold {index} has invalid value") from exc
        thresholds.append(
            {
                "value": value,
                "label": str(threshold.get("label") or value),
                "kind": str(threshold.get("kind") or "watch"),
            }
        )
    return thresholds


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


def _threshold_color(kind: str) -> str:
    lowered = kind.lower()
    if lowered in {"pressure", "risk", "stress", "upper"}:
        return "#cf222e"
    if lowered in {"support", "constructive", "lower", "risk-on"}:
        return "#1a7f37"
    return "#6f42c1"


def _format_value(value: float, unit: str) -> str:
    if abs(value) >= 100:
        rendered = f"{value:.0f}"
    elif abs(value) >= 10:
        rendered = f"{value:.2f}"
    else:
        rendered = f"{value:.3f}".rstrip("0").rstrip(".")
    return f"{rendered}{unit}"


def _delta_label(points: list[dict[str, Any]], unit: str) -> str:
    if len(points) < 2:
        return "delta n/a"
    delta = float(points[-1]["value"]) - float(points[0]["value"])
    sign = "+" if delta > 0 else ""
    return f"delta {sign}{_format_value(delta, unit)}"


def _wrap_text(text: str, max_chars: int, max_lines: int) -> list[str]:
    if not text:
        return []
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
    if lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1][: max(0, max_chars - 3)] + "..."
    return lines


def _clip(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 3)] + "..."


def _threshold_summary(variable: dict[str, Any]) -> str:
    unit = str(variable.get("unit") or "")
    parts = []
    for threshold in variable["thresholds"]:
        label = str(threshold["label"])
        value = _format_value(float(threshold["value"]), unit)
        parts.append(f"{label} ({value})")
    return "; ".join(parts) or "n/a"


def _sparkline(
    points: list[dict[str, Any]],
    x: float,
    y: float,
    w: float,
    h: float,
    low: float,
    high: float,
) -> str:
    if len(points) < 2:
        return ""
    values = [float(point["value"]) for point in points]
    if high == low:
        high += 1
        low -= 1
    step = w / max(len(points) - 1, 1)
    coords = []
    for index, value in enumerate(values):
        px = x + index * step
        py = _value_to_y(value, low, high, y, h)
        coords.append(f"{px:.1f},{py:.1f}")
    return " ".join(coords)


def _value_bounds(variable: dict[str, Any]) -> tuple[float, float]:
    values = [float(point["value"]) for point in variable["series"]]
    values.extend(float(threshold["value"]) for threshold in variable["thresholds"])
    values.append(float(variable["latest"]))
    low = min(values)
    high = max(values)
    if low == high:
        low -= 1
        high += 1
    pad = max((high - low) * 0.12, 0.01)
    return low - pad, high + pad


def _value_to_y(value: float, low: float, high: float, y: float, h: float) -> float:
    return y + h - ((value - low) / (high - low)) * h


def render_reference_table(
    svg: list[str],
    variables: list[dict[str, Any]],
    *,
    x: float,
    y: float,
    width: float,
) -> float:
    """Render a compact reference table for the macro / regime mini-panel."""

    row_h = 26
    header_h = 30
    table_h = header_h + row_h * (len(variables) + 1)
    svg.extend(
        [
            f'<text class="tag" x="{x}" y="{y - 10}">reference table</text>',
            f'<rect x="{x}" y="{y}" width="{width}" height="{table_h}" rx="7" fill="#ffffff" stroke="#d8dee4"/>',
            f'<rect x="{x}" y="{y}" width="{width}" height="{header_h}" rx="7" fill="#f6f8fa" stroke="#d8dee4"/>',
        ]
    )

    columns = [
        ("indicator", x + 16),
        ("latest", x + 150),
        ("delta", x + 258),
        ("key thresholds", x + 372),
        ("read", x + 820),
    ]
    for label, col_x in columns:
        svg.append(f'<text class="tag" x="{col_x}" y="{y + 20}">{_svg_escape(label)}</text>')

    for index, variable in enumerate(variables, start=1):
        row_y = y + header_h + index * row_h
        if index % 2 == 0:
            svg.append(
                f'<rect x="{x}" y="{row_y - row_h + 3}" width="{width}" height="{row_h}" fill="#fbfcfd"/>'
            )
        unit = str(variable.get("unit") or "")
        cells = [
            (variable["name"], x + 16, 42),
            (_format_value(float(variable["latest"]), unit), x + 150, 36),
            (_delta_label(variable["series"], unit).replace("delta ", ""), x + 258, 36),
            (_threshold_summary(variable), x + 372, 64),
            (f'{variable["status"]}: {variable["interpretation"]}', x + 820, 44),
        ]
        for value, col_x, max_chars in cells:
            svg.append(
                f'<text class="muted" x="{col_x}" y="{row_y}">{_svg_escape(_clip(str(value), max_chars))}</text>'
            )

    return y + table_h


def render_svg(payload: dict[str, Any]) -> str:
    variables = normalize_variables(payload)
    title = str(payload.get("title") or "Macro / Regime Mini-Panel")
    subtitle = str(payload.get("subtitle") or "display-first visual artifact")
    strategy_posture = str(payload.get("strategy_posture") or payload.get("regime") or "watch")
    summary = str(payload.get("summary") or "Use threshold and delta context before changing risk.")
    source = str(payload.get("source") or "provided")
    as_of = str(payload.get("as_of") or payload.get("data_as_of") or "")
    notes = payload.get("notes") or []

    width = 1200
    cols = 2
    card_w = 548
    card_h = 184
    gap_x = 28
    gap_y = 24
    left = 36
    top = 132
    rows = (len(variables) + cols - 1) // cols
    cards_bottom = top + rows * card_h + max(rows - 1, 0) * gap_y
    table_h = 30 + 26 * (len(variables) + 1)
    height = max(520, cards_bottom + table_h + 162)
    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_svg_escape(title)}">',
        "<style>",
        ".title{font:700 22px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".subtitle{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".label{font:600 14px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".muted{font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".value{font:700 19px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".tag{font:700 12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".axis{font:10px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#6e7781}",
        "</style>",
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'<text class="title" x="36" y="42">{_svg_escape(title)}</text>',
        f'<text class="subtitle" x="36" y="66">{_svg_escape(subtitle)}</text>',
    ]
    meta = f"source: {source}"
    if as_of:
        meta = f"{meta} | as of: {as_of}"
    svg.append(f'<text class="muted" x="36" y="86">{_svg_escape(meta)}</text>')
    svg.extend(
        [
            '<text class="tag" x="36" y="112">strategy posture</text>',
            f'<rect x="154" y="96" width="178" height="25" rx="12" fill="#fff8c5" stroke="#d4a72c"/>',
            f'<text class="tag" x="170" y="113">{_svg_escape(strategy_posture)}</text>',
            f'<text class="muted" x="358" y="113">{_svg_escape(summary)}</text>',
        ]
    )

    for index, variable in enumerate(variables):
        row = index // cols
        col = index % cols
        x = left + col * (card_w + gap_x)
        y = top + row * (card_h + gap_y)
        color = _status_color(variable["status"])
        unit = variable["unit"]
        value_label = _format_value(float(variable["latest"]), unit)
        delta = _delta_label(variable["series"], unit)
        plot_x = x + 20
        plot_y = y + 72
        plot_w = 294
        plot_h = 70
        low, high = _value_bounds(variable)
        svg.extend(
            [
                f'<rect x="{x}" y="{y}" width="{card_w}" height="{card_h}" rx="7" fill="#fbfcfd" stroke="#d8dee4"/>',
                f'<circle cx="{x + 22}" cy="{y + 26}" r="7" fill="{color}"/>',
                f'<text class="label" x="{x + 40}" y="{y + 25}">{_svg_escape(variable["name"])}</text>',
                f'<text class="muted" x="{x + 40}" y="{y + 47}">{_svg_escape(variable["label"])}</text>',
                f'<text class="value" x="{x + 332}" y="{y + 30}">{_svg_escape(value_label)}</text>',
                f'<text class="muted" x="{x + 332}" y="{y + 52}">{_svg_escape(delta)} | {_svg_escape(variable["status"])}</text>',
                f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="#ffffff" stroke="#d8dee4"/>',
            ]
        )

        for guide in (0.25, 0.5, 0.75):
            gy = plot_y + plot_h * guide
            svg.append(
                f'<line x1="{plot_x}" y1="{gy:.1f}" x2="{plot_x + plot_w}" y2="{gy:.1f}" stroke="#eaeef2"/>'
            )

        for threshold in variable["thresholds"]:
            ty = _value_to_y(float(threshold["value"]), low, high, plot_y, plot_h)
            threshold_color = _threshold_color(threshold["kind"])
            label = f'threshold {threshold["label"]}'
            svg.extend(
                [
                    f'<line x1="{plot_x}" y1="{ty:.1f}" x2="{plot_x + plot_w}" y2="{ty:.1f}" stroke="{threshold_color}" stroke-width="1.4" stroke-dasharray="5 4"/>',
                    f'<text class="axis" x="{plot_x + 6}" y="{max(plot_y + 11, ty - 4):.1f}" style="fill:{threshold_color}">{_svg_escape(label)}</text>',
                ]
            )

        points = _sparkline(variable["series"], plot_x, plot_y, plot_w, plot_h, low, high)
        if points:
            svg.append(
                f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.6"/>'
            )
            latest_x = plot_x + plot_w
            latest_y = _value_to_y(float(variable["series"][-1]["value"]), low, high, plot_y, plot_h)
            svg.append(f'<circle cx="{latest_x:.1f}" cy="{latest_y:.1f}" r="4.2" fill="{color}"/>')

        first_time = variable["series"][0]["time"] if variable["series"] else ""
        last_time = variable["series"][-1]["time"] if variable["series"] else ""
        svg.extend(
            [
                f'<text class="axis" x="{plot_x}" y="{plot_y + plot_h + 16}">{_svg_escape(first_time)}</text>',
                f'<text class="axis" x="{plot_x + plot_w - 58}" y="{plot_y + plot_h + 16}">{_svg_escape(last_time)}</text>',
                f'<text class="axis" x="{plot_x + plot_w + 8}" y="{plot_y + 10}">{_svg_escape(_format_value(high, unit))}</text>',
                f'<text class="axis" x="{plot_x + plot_w + 8}" y="{plot_y + plot_h}">{_svg_escape(_format_value(low, unit))}</text>',
            ]
        )

        info_x = x + 332
        svg.append(f'<text class="tag" x="{info_x}" y="{y + 82}">impact path</text>')
        read_text = variable["impact_path"] or variable["interpretation"]
        for line_index, line in enumerate(_wrap_text(read_text, 29, 3)):
            svg.append(
                f'<text class="muted" x="{info_x}" y="{y + 104 + line_index * 18}">{_svg_escape(line)}</text>'
            )

    table_bottom = render_reference_table(
        svg,
        variables,
        x=36,
        y=cards_bottom + 34,
        width=1128,
    )
    note_y = table_bottom + 28
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
