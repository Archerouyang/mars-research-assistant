#!/usr/bin/env python3
"""Generate a local lightweight-charts HTML artifact from normalized OHLCV JSON."""

from __future__ import annotations

import argparse
import json
from html import escape
from pathlib import Path
from typing import Any


LIGHTWEIGHT_CHARTS_VERSION = "5.2.0"
LIGHTWEIGHT_CHARTS_URL = (
    "https://unpkg.com/lightweight-charts@"
    f"{LIGHTWEIGHT_CHARTS_VERSION}/dist/lightweight-charts.standalone.production.js"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a local TradingView lightweight-charts HTML artifact."
    )
    parser.add_argument("input_json", help="Normalized OHLCV JSON input")
    parser.add_argument("--output", "-o", required=True, help="Output HTML path")
    parser.add_argument(
        "--title",
        default=None,
        help="Override chart title; defaults to input title or symbol",
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
        "candles": candles,
        "volume": volume_points(candles),
        "ema20": payload.get("ema20") or ema_points(candles, 20),
        "ema50": payload.get("ema50") or ema_points(candles, 50),
        "levels": normalize_levels(payload),
        "notes": payload.get("notes") or [],
        "source": str(payload.get("source") or ""),
    }


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
    payload = build_chart_payload(load_payload(Path(args.input_json)), args.title)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(payload), encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
