#!/usr/bin/env python3
"""Generate display-first price-action visual artifacts from normalized OHLCV JSON.

Default output is a transient SVG for chat display. Optional HTML is still
available for TradingView lightweight-charts inspection. Durable manifest saves
are opt-in only.
"""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any

from visual_artifacts import (
    default_display_output,
    manifest_record_from_args,
    save_manifest,
    slugify,
    write_text_artifact,
)


LIGHTWEIGHT_CHARTS_VERSION = "5.2.0"
LIGHTWEIGHT_CHARTS_URL = (
    "https://unpkg.com/lightweight-charts@"
    f"{LIGHTWEIGHT_CHARTS_VERSION}/dist/lightweight-charts.standalone.production.js"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a display-first price-action visual artifact."
    )
    parser.add_argument("input_json", help="Normalized OHLCV JSON input")
    parser.add_argument("--output", "-o", help="Optional output HTML path")
    parser.add_argument(
        "--display-output",
        help="Output SVG path for transient chat display; defaults to .scratch/visual-artifacts",
    )
    parser.add_argument(
        "--title",
        default=None,
        help="Override chart title; defaults to input title or symbol",
    )
    parser.add_argument("--artifact-id", default=None, help="Stable artifact identifier")
    parser.add_argument("--linked-context", default="", help="Setup, plan, or note this artifact supports")
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


def normalize_candles(payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw = payload.get("candles") or payload.get("ohlcv") or payload.get("data")
    if not isinstance(raw, list) or not raw:
        raise SystemExit("input JSON must include non-empty candles, ohlcv, or data list")

    candles: list[dict[str, Any]] = []
    for index, row in enumerate(raw, start=1):
        if not isinstance(row, dict):
            raise SystemExit(f"candle {index} must be an object")
        try:
            candle = {
                "time": str(row["time"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
            }
        except KeyError as exc:
            raise SystemExit(f"candle {index} missing field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"candle {index} has invalid numeric fields") from exc
        if row.get("volume") not in (None, ""):
            try:
                candle["volume"] = float(row["volume"])
            except (TypeError, ValueError) as exc:
                raise SystemExit(f"candle {index} has invalid volume") from exc
        candles.append(candle)
    return candles


def ema_points(candles: list[dict[str, Any]], period: int) -> list[dict[str, Any]]:
    if len(candles) < period:
        return []
    closes = [float(candle["close"]) for candle in candles]
    seed = sum(closes[:period]) / period
    multiplier = 2 / (period + 1)
    ema = seed
    points = [{"time": candles[period - 1]["time"], "value": round(ema, 4)}]
    for index in range(period, len(candles)):
        ema = closes[index] * multiplier + ema * (1 - multiplier)
        points.append({"time": candles[index]["time"], "value": round(ema, 4)})
    return points


def normalize_levels(payload: dict[str, Any]) -> list[dict[str, Any]]:
    levels = payload.get("levels") or []
    if not isinstance(levels, list):
        raise SystemExit("levels must be a list when provided")
    normalized = []
    for index, level in enumerate(levels, start=1):
        if not isinstance(level, dict):
            raise SystemExit(f"level {index} must be an object")
        try:
            price = float(level["price"])
        except KeyError as exc:
            raise SystemExit(f"level {index} missing price") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"level {index} has invalid price") from exc
        normalized.append(
            {
                "price": price,
                "label": str(level.get("label") or level.get("name") or price),
                "kind": str(level.get("kind") or "level"),
                "color": str(level.get("color") or color_for_kind(str(level.get("kind") or ""))),
            }
        )
    return normalized


def normalize_zones(payload: dict[str, Any]) -> list[dict[str, Any]]:
    zones = payload.get("zones") or []
    if not isinstance(zones, list):
        raise SystemExit("zones must be a list when provided")
    normalized = []
    for index, zone in enumerate(zones, start=1):
        if not isinstance(zone, dict):
            raise SystemExit(f"zone {index} must be an object")
        try:
            low = float(zone["low"])
            high = float(zone["high"])
        except KeyError as exc:
            raise SystemExit(f"zone {index} missing field: {exc.args[0]}") from exc
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"zone {index} has invalid numeric fields") from exc
        if low > high:
            low, high = high, low
        kind = str(zone.get("kind") or "zone")
        normalized.append(
            {
                "low": low,
                "high": high,
                "label": str(zone.get("label") or kind),
                "kind": kind,
                "color": str(zone.get("color") or color_for_kind(kind)),
            }
        )
    return normalized


def color_for_kind(kind: str) -> str:
    lowered = kind.lower()
    if lowered in {"add", "trigger", "support"}:
        return "#1a7f37"
    if lowered in {"profit", "rebalance", "target"}:
        return "#6f42c1"
    if lowered in {"invalid", "invalidation", "review", "risk"}:
        return "#d1242f"
    return "#57606a"


def volume_points(candles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points = []
    for candle in candles:
        if "volume" not in candle:
            continue
        up = float(candle["close"]) >= float(candle["open"])
        points.append(
            {
                "time": candle["time"],
                "value": float(candle["volume"]),
                "color": "rgba(26, 127, 55, 0.35)" if up else "rgba(207, 34, 46, 0.35)",
            }
        )
    return points


def build_chart_payload(payload: dict[str, Any], title_override: str | None) -> dict[str, Any]:
    candles = normalize_candles(payload)
    title = title_override or str(payload.get("title") or payload.get("symbol") or "Chart Artifact")
    return {
        "title": title,
        "subtitle": str(payload.get("subtitle") or ""),
        "symbol": str(payload.get("symbol") or ""),
        "setup_status": str(payload.get("setup_status") or ""),
        "data_as_of": str(payload.get("data_as_of") or payload.get("as_of") or ""),
        "candles": candles,
        "volume": volume_points(candles),
        "ema20": payload.get("ema20") or ema_points(candles, 20),
        "ema50": payload.get("ema50") or ema_points(candles, 50),
        "levels": normalize_levels(payload),
        "zones": normalize_zones(payload),
        "notes": payload.get("notes") or [],
        "source": str(payload.get("source") or ""),
    }


def _svg_escape(value: Any) -> str:
    return escape(str(value), quote=True)


def _polyline(points: list[tuple[float, float]]) -> str:
    if not points:
        return ""
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def render_svg(chart_payload: dict[str, Any]) -> str:
    """Render a static display-first SVG with trigger zone and TP/rebalance annotations."""

    candles = chart_payload["candles"]
    levels = chart_payload.get("levels") or []
    zones = chart_payload.get("zones") or []
    ema20 = chart_payload.get("ema20") or []
    ema50 = chart_payload.get("ema50") or []

    values: list[float] = []
    for candle in candles:
        values.extend([float(candle["high"]), float(candle["low"])])
    values.extend(float(level["price"]) for level in levels)
    for zone in zones:
        values.extend([float(zone["low"]), float(zone["high"])])
    for point in [*ema20, *ema50]:
        if isinstance(point, dict) and point.get("value") not in (None, ""):
            values.append(float(point["value"]))

    min_price = min(values)
    max_price = max(values)
    pad = max((max_price - min_price) * 0.08, 1)
    min_price -= pad
    max_price += pad

    width = 1200
    height = 720
    plot_x = 78
    plot_y = 108
    plot_w = 850
    plot_h = 455
    side_x = 962
    side_w = 190
    n = len(candles)
    step = plot_w / max(n - 1, 1)
    candle_w = max(min(step * 0.58, 12), 3)

    def x_for_index(index: int) -> float:
        return plot_x + index * step

    def y_for_price(price: float) -> float:
        scale = (price - min_price) / (max_price - min_price)
        return plot_y + plot_h - scale * plot_h

    time_to_index = {str(candle["time"]): index for index, candle in enumerate(candles)}

    svg: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{_svg_escape(chart_payload["title"])}">',
        "<style>",
        ".label{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".muted{font:12px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".small{font:11px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        ".title{font:700 22px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#24292f}",
        ".subtitle{font:13px -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;fill:#57606a}",
        "</style>",
        '<rect width="1200" height="720" fill="#ffffff"/>',
        f'<text class="title" x="36" y="42">{_svg_escape(chart_payload["title"])}</text>',
    ]

    subtitle = chart_payload.get("subtitle") or "display-first visual artifact"
    svg.append(f'<text class="subtitle" x="36" y="66">{_svg_escape(subtitle)}</text>')
    status = chart_payload.get("setup_status")
    if status:
        svg.append(
            f'<text class="muted" x="36" y="86">setup status: {_svg_escape(status)}</text>'
        )

    svg.extend(
        [
            f'<rect x="{plot_x}" y="{plot_y}" width="{plot_w}" height="{plot_h}" fill="#fbfcfd" stroke="#d8dee4"/>',
            f'<line x1="{plot_x}" y1="{plot_y + plot_h * 0.25:.1f}" x2="{plot_x + plot_w}" y2="{plot_y + plot_h * 0.25:.1f}" stroke="#eaeef2"/>',
            f'<line x1="{plot_x}" y1="{plot_y + plot_h * 0.50:.1f}" x2="{plot_x + plot_w}" y2="{plot_y + plot_h * 0.50:.1f}" stroke="#eaeef2"/>',
            f'<line x1="{plot_x}" y1="{plot_y + plot_h * 0.75:.1f}" x2="{plot_x + plot_w}" y2="{plot_y + plot_h * 0.75:.1f}" stroke="#eaeef2"/>',
        ]
    )

    for zone in zones:
        y_high = y_for_price(float(zone["high"]))
        y_low = y_for_price(float(zone["low"]))
        color = _svg_escape(zone["color"])
        label = _svg_escape(zone["label"])
        svg.append(
            f'<rect x="{plot_x}" y="{y_high:.1f}" width="{plot_w}" height="{max(y_low - y_high, 2):.1f}" fill="{color}" opacity="0.12"/>'
        )
        svg.append(
            f'<text class="small" x="{plot_x + 8}" y="{max(y_high - 5, plot_y + 12):.1f}" fill="{color}">{label}</text>'
        )

    for index, candle in enumerate(candles):
        x = x_for_index(index)
        open_y = y_for_price(float(candle["open"]))
        close_y = y_for_price(float(candle["close"]))
        high_y = y_for_price(float(candle["high"]))
        low_y = y_for_price(float(candle["low"]))
        up = float(candle["close"]) >= float(candle["open"])
        color = "#1a7f37" if up else "#cf222e"
        rect_y = min(open_y, close_y)
        rect_h = max(abs(open_y - close_y), 2)
        svg.append(f'<line x1="{x:.1f}" y1="{high_y:.1f}" x2="{x:.1f}" y2="{low_y:.1f}" stroke="{color}" stroke-width="1.4"/>')
        svg.append(
            f'<rect x="{x - candle_w / 2:.1f}" y="{rect_y:.1f}" width="{candle_w:.1f}" height="{rect_h:.1f}" fill="{color}" opacity="0.88"/>'
        )

    def ema_path(points: list[dict[str, Any]]) -> list[tuple[float, float]]:
        result = []
        for point in points:
            index = time_to_index.get(str(point.get("time")))
            if index is None:
                continue
            result.append((x_for_index(index), y_for_price(float(point["value"]))))
        return result

    svg.append(
        f'<polyline points="{_polyline(ema_path(ema20))}" fill="none" stroke="#0969da" stroke-width="2.2"/>'
    )
    svg.append(
        f'<polyline points="{_polyline(ema_path(ema50))}" fill="none" stroke="#fb8500" stroke-width="2.2"/>'
    )
    svg.append('<text class="small" x="80" y="590" fill="#0969da">EMA 20</text>')
    svg.append('<text class="small" x="142" y="590" fill="#fb8500">EMA 50</text>')

    for level in levels:
        y = y_for_price(float(level["price"]))
        color = _svg_escape(level["color"])
        label = _svg_escape(level["label"])
        svg.append(
            f'<line x1="{plot_x}" y1="{y:.1f}" x2="{plot_x + plot_w}" y2="{y:.1f}" stroke="{color}" stroke-width="1.8" stroke-dasharray="6 5"/>'
        )
        svg.append(
            f'<text class="small" x="{plot_x + plot_w + 8}" y="{y + 4:.1f}" fill="{color}">{label}</text>'
        )

    latest = candles[-1]
    svg.extend(
        [
            f'<rect x="{side_x}" y="{plot_y}" width="{side_w}" height="{plot_h}" rx="6" fill="#ffffff" stroke="#d8dee4"/>',
            f'<text class="label" x="{side_x + 16}" y="{plot_y + 28}">Decision panel</text>',
            f'<text class="muted" x="{side_x + 16}" y="{plot_y + 55}">last close: {latest["close"]:.2f}</text>',
            f'<text class="muted" x="{side_x + 16}" y="{plot_y + 76}">source: {_svg_escape(chart_payload.get("source") or "provided")}</text>',
        ]
    )
    if chart_payload.get("data_as_of"):
        svg.append(
            f'<text class="muted" x="{side_x + 16}" y="{plot_y + 97}">as of: {_svg_escape(chart_payload["data_as_of"])}</text>'
        )

    note_y = plot_y + 130
    svg.append(f'<text class="label" x="{side_x + 16}" y="{note_y}">Notes</text>')
    for offset, note in enumerate(chart_payload.get("notes") or [], start=1):
        clipped = str(note)
        if len(clipped) > 62:
            clipped = clipped[:59] + "..."
        svg.append(
            f'<text class="small" x="{side_x + 16}" y="{note_y + offset * 22}">{_svg_escape(clipped)}</text>'
        )

    first_time = candles[0]["time"]
    last_time = candles[-1]["time"]
    svg.append(f'<text class="small" x="{plot_x}" y="{plot_y + plot_h + 30}">{_svg_escape(first_time)}</text>')
    svg.append(
        f'<text class="small" x="{plot_x + plot_w - 86}" y="{plot_y + plot_h + 30}">{_svg_escape(last_time)}</text>'
    )
    svg.append(
        '<text class="small" x="36" y="682">Display-first chart artifact. Use authorized OHLCV or fixture data only; no live broker reads or live market data calls.</text>'
    )
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def render_html(chart_payload: dict[str, Any]) -> str:
    data_json = json.dumps(chart_payload, ensure_ascii=False)
    title = escape(str(chart_payload["title"]))
    subtitle = escape(str(chart_payload.get("subtitle") or ""))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <script src="{LIGHTWEIGHT_CHARTS_URL}"></script>
  <style>
    :root {{
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #ffffff;
      color: #1f2328;
    }}
    body {{
      margin: 0;
      padding: 24px;
      background: #ffffff;
    }}
    header {{
      margin-bottom: 14px;
    }}
    h1 {{
      margin: 0;
      font-size: 20px;
      line-height: 1.25;
    }}
    .subtitle {{
      margin-top: 4px;
      color: #57606a;
      font-size: 13px;
    }}
    #chart {{
      width: 100%;
      height: 620px;
      border: 1px solid #d8dee4;
    }}
    .notes {{
      margin-top: 12px;
      padding-left: 18px;
      color: #57606a;
      font-size: 13px;
    }}
    footer {{
      margin-top: 14px;
      color: #57606a;
      font-size: 12px;
    }}
    footer a {{
      color: #0969da;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <div class="subtitle">{subtitle}</div>
  </header>
  <div id="chart"></div>
  <ul class="notes" id="notes"></ul>
  <footer>
    Chart rendering powered by
    <a href="https://www.tradingview.com/" rel="noreferrer">TradingView</a>
    Lightweight Charts™.
  </footer>
  <script>
    const payload = {data_json};
    const chartElement = document.getElementById('chart');
    const chart = LightweightCharts.createChart(chartElement, {{
      layout: {{ background: {{ color: '#ffffff' }}, textColor: '#1f2328' }},
      grid: {{
        vertLines: {{ color: '#f0f2f4' }},
        horzLines: {{ color: '#f0f2f4' }},
      }},
      rightPriceScale: {{ borderVisible: false }},
      timeScale: {{ borderVisible: false, timeVisible: false }},
      crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
    }});

    const candleSeries = chart.addSeries(LightweightCharts.CandlestickSeries, {{
      upColor: '#1a7f37',
      downColor: '#cf222e',
      borderUpColor: '#1a7f37',
      borderDownColor: '#cf222e',
      wickUpColor: '#1a7f37',
      wickDownColor: '#cf222e',
    }});
    candleSeries.setData(payload.candles);

    if (payload.volume && payload.volume.length > 0) {{
      const volumeSeries = chart.addSeries(LightweightCharts.HistogramSeries, {{
        priceFormat: {{ type: 'volume' }},
        priceScaleId: '',
        lastValueVisible: false,
        priceLineVisible: false,
      }});
      volumeSeries.setData(payload.volume);
      chart.priceScale('').applyOptions({{
        scaleMargins: {{ top: 0.8, bottom: 0 }},
      }});
    }}

    if (payload.ema20 && payload.ema20.length > 0) {{
      const ema20 = chart.addSeries(LightweightCharts.LineSeries, {{
        color: '#0969da',
        lineWidth: 2,
        title: 'EMA 20',
      }});
      ema20.setData(payload.ema20);
    }}

    if (payload.ema50 && payload.ema50.length > 0) {{
      const ema50 = chart.addSeries(LightweightCharts.LineSeries, {{
        color: '#fb8500',
        lineWidth: 2,
        title: 'EMA 50',
      }});
      ema50.setData(payload.ema50);
    }}

    for (const level of payload.levels || []) {{
      candleSeries.createPriceLine({{
        price: level.price,
        color: level.color || '#57606a',
        lineWidth: 2,
        lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: level.label || String(level.price),
      }});
    }}

    const notes = document.getElementById('notes');
    for (const note of payload.notes || []) {{
      const item = document.createElement('li');
      item.textContent = note;
      notes.appendChild(item);
    }}

    chart.timeScale().fitContent();
    window.addEventListener('resize', () => {{
      chart.applyOptions({{ width: chartElement.clientWidth }});
    }});
  </script>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    raw_payload = load_payload(Path(args.input_json))
    payload = build_chart_payload(raw_payload, args.title)
    artifact_id = args.artifact_id or slugify(str(payload.get("symbol") or payload["title"]))
    repo_root = Path(__file__).resolve().parents[3]
    display_output = (
        Path(args.display_output)
        if args.display_output
        else default_display_output(repo_root, artifact_id)
    )

    write_text_artifact(display_output, render_svg(payload))
    print(f"display {display_output}")

    html_output = Path(args.output) if args.output else None
    if html_output is not None:
        write_text_artifact(html_output, render_html(payload))
        print(f"html {html_output}")

    if args.save_manifest:
        if not args.manifest:
            raise SystemExit("--save-manifest requires --manifest")
        manifest_path = Path(args.manifest)
        record = manifest_record_from_args(
            artifact_id=artifact_id,
            artifact_type="price_action",
            mode="saved",
            linked_context=args.linked_context,
            data_source=args.data_source or str(payload.get("source") or "provided"),
            data_as_of=args.data_as_of or str(payload.get("data_as_of") or ""),
            image_path=display_output,
            html_path=html_output,
            decision_summary=args.decision_summary,
        )
        save_manifest(manifest_path, record)
        print(f"manifest {manifest_path}")


if __name__ == "__main__":
    main()
