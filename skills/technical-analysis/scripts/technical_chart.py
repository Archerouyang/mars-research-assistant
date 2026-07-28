"""Render and deliver the temporary, offline Lightweight Charts view."""

from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Any
import webbrowser


LIGHTWEIGHT_CHARTS_VERSION = "5.2.0"
LIGHTWEIGHT_CHARTS_DIRECTORY = (
    Path(__file__).resolve().parents[1]
    / "vendor"
    / "lightweight-charts"
    / LIGHTWEIGHT_CHARTS_VERSION
)
LIGHTWEIGHT_CHARTS_SCRIPT = (
    LIGHTWEIGHT_CHARTS_DIRECTORY
    / "lightweight-charts.standalone.production.js"
)
TEMPORARY_CHART_MAX_AGE_SECONDS = 24 * 60 * 60
TEMPORARY_CHART_MARKER_NAME = ".mars-technical-chart.json"
TEMPORARY_CHART_MARKER = {
    "schema_version": 1,
    "owner": "mars-skills/technical-analysis",
    "kind": "temporary-lightweight-chart",
}


def _safe_inline_json(value: object) -> str:
    return (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )


def _chart_payload(evidence: dict[str, Any]) -> dict[str, Any]:
    bars = evidence["ohlcv"]
    visible_count = int(evidence["visible_bars"])
    first_visible_index = max(0, len(bars) - visible_count)
    visible = bars[first_visible_index:]
    candles = [
        {
            "time": str(bar["timestamp"])[:10],
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
        }
        for bar in visible
    ]
    volume = [
        {
            "time": str(bar["timestamp"])[:10],
            "value": bar["volume"],
            "color": (
                "rgba(38, 166, 154, 0.45)"
                if float(bar["close"]) >= float(bar["open"])
                else "rgba(239, 83, 80, 0.45)"
            ),
        }
        for bar in visible
    ]
    moving_averages: dict[str, list[dict[str, Any]]] = {}
    for window_text, values in evidence["indicators"]["sma"].items():
        moving_averages[f"sma-{window_text}"] = [
            {
                "time": str(bars[index]["timestamp"])[:10],
                "value": value,
            }
            for index, value in enumerate(
                values[first_visible_index:],
                first_visible_index,
            )
            if value is not None
        ]
    return {
        "metadata": {
            "symbol": evidence["symbol"],
            "evidence_id": evidence["evidence_id"],
            "source": evidence["source"]["label"],
            "timezone": evidence["timezone"],
            "as_of": evidence["as_of"],
            "adjustment": evidence["adjustment"],
            "bars_used": evidence["bars_used"],
            "visible_bars": len(visible),
            "current_price": evidence["indicators"]["latest"]["close"],
            "library": f"TradingView Lightweight Charts {LIGHTWEIGHT_CHARTS_VERSION}",
        },
        "candles": candles,
        "volume": volume,
        "moving_averages": moving_averages,
        "key_levels": evidence["key_levels"],
    }


def chart_html(evidence: dict[str, Any]) -> str:
    library = LIGHTWEIGHT_CHARTS_SCRIPT.read_text(encoding="utf-8")
    payload = _safe_inline_json(_chart_payload(evidence))
    title = escape(f"{evidence['symbol']} · 技术面分析", quote=True)
    identity = escape(str(evidence["evidence_id"]), quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    html, body {{ max-width: 100%; overflow-x: hidden; }}
    body {{ margin: 0; background: #0b0e11; color: #d1d4dc; }}
    main {{ min-width: 0; min-height: 100vh; padding: 20px; display: grid; grid-template-rows: auto auto minmax(520px, 1fr) auto; gap: 14px; }}
    header, footer, #chart-legend {{ display: flex; flex-wrap: wrap; gap: 8px 16px; }}
    header, footer {{ justify-content: space-between; }}
    h1 {{ margin: 0; color: #f0f3fa; font-size: 20px; }}
    .meta, footer, #chart-legend {{ color: #787b86; font-size: 12px; overflow-wrap: anywhere; }}
    .legend-item {{ display: inline-flex; align-items: center; gap: 6px; white-space: nowrap; }}
    .legend-swatch {{ width: 16px; height: 3px; border-radius: 2px; background: var(--swatch); }}
    .legend-swatch.solid {{ height: 0; border-top: 3px solid var(--swatch); background: transparent; }}
    .legend-swatch.dashed {{ height: 0; border-top: 2px dashed var(--swatch); background: transparent; }}
    .legend-swatch.dotted {{ height: 0; border-top: 3px dotted var(--swatch); background: transparent; }}
    .chart-shell {{ min-width: 0; min-height: 520px; position: relative; border: 1px solid #2a2e39; border-radius: 8px; overflow: hidden; }}
    #chart {{ width: 100%; height: 100%; min-height: 520px; }}
    #crosshair-tooltip {{ position: absolute; z-index: 4; top: 12px; left: 12px; max-width: calc(100% - 24px); padding: 8px 10px; border: 1px solid #363a45; border-radius: 6px; background: rgba(11,14,17,.88); color: #d1d4dc; font: 12px/1.5 ui-monospace, monospace; pointer-events: none; }}
    a {{ color: #2962ff; }}
    @media (max-width: 640px) {{
      main {{ padding: 10px; grid-template-rows: auto auto minmax(420px, 1fr) auto; }}
      h1 {{ font-size: 17px; }}
      .chart-shell, #chart {{ min-height: 420px; }}
      #crosshair-tooltip {{ top: 8px; left: 8px; max-width: calc(100% - 16px); font-size: 10px; }}
    }}
  </style>
</head>
<body>
  <main data-evidence-id="{identity}">
    <header><h1 id="title"></h1><div class="meta" id="provenance"></div></header>
    <div id="chart-legend" aria-label="图表图例">
      <span class="legend-item"><span class="legend-swatch" style="--swatch:#f0f3fa"></span>当前价</span>
      <span class="legend-item"><span class="legend-swatch solid" style="--swatch:#2962ff"></span>SMA20（实线）</span>
      <span class="legend-item"><span class="legend-swatch dashed" style="--swatch:#ab47bc"></span>SMA50（虚线）</span>
      <span class="legend-item"><span class="legend-swatch dotted" style="--swatch:#ff9800"></span>SMA200（点线）</span>
      <span class="legend-item"><span class="legend-swatch dashed" style="--swatch:#26a69a"></span>支撑关键位</span>
      <span class="legend-item"><span class="legend-swatch dashed" style="--swatch:#ef5350"></span>阻力关键位</span>
      <span class="legend-item"><span class="legend-swatch" style="--swatch:#787b86"></span>成交量</span>
    </div>
    <section class="chart-shell">
      <div id="crosshair-tooltip" aria-live="polite">移动十字光标查看 OHLCV、成交量与均线</div>
      <div id="chart" role="img" aria-label="{title} K 线、成交量、均线、当前价与关键位"></div>
    </section>
    <footer>
      <span id="identity"></span>
      <span>Powered by <a href="https://www.tradingview.com/" target="_blank" rel="noopener noreferrer">TradingView Lightweight Charts™</a> {LIGHTWEIGHT_CHARTS_VERSION}</span>
    </footer>
  </main>
  <script>{library}</script>
  <script>
    const chartEvidence = {payload};
    const metadata = chartEvidence.metadata;
    document.getElementById('title').textContent = `${{metadata.symbol}} · 技术面分析`;
    document.getElementById('provenance').textContent =
      `${{metadata.source}} · ${{metadata.timezone}} · as_of ${{metadata.as_of}} · ${{metadata.adjustment}} · ${{metadata.bars_used}} bars`;
    document.getElementById('identity').textContent = metadata.evidence_id;

    const container = document.getElementById('chart');
    const chart = LightweightCharts.createChart(container, {{
      width: container.clientWidth,
      height: container.clientHeight,
      layout: {{ background: {{ color: '#0b0e11' }}, textColor: '#d1d4dc' }},
      grid: {{ vertLines: {{ color: '#1f232d' }}, horzLines: {{ color: '#1f232d' }} }},
      rightPriceScale: {{ borderColor: '#2a2e39' }},
      timeScale: {{ borderColor: '#2a2e39', timeVisible: false }},
      crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
      handleScroll: {{ mouseWheel: true, pressedMouseMove: true, horzTouchDrag: true, vertTouchDrag: false }},
      handleScale: {{ axisPressedMouseMove: true, mouseWheel: true, pinch: true }}
    }});
    const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
      upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
      wickUpColor: '#26a69a', wickDownColor: '#ef5350'
    }});
    candles.setData(chartEvidence.candles);
    candles.createPriceLine({{
      price: metadata.current_price, color: '#f0f3fa', lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true,
      title: `当前价 ${{metadata.current_price}}`
    }});
    const volume = chart.addSeries(LightweightCharts.HistogramSeries, {{
      priceFormat: {{ type: 'volume' }}, priceScaleId: 'volume'
    }});
    chart.priceScale('volume').applyOptions({{ scaleMargins: {{ top: .82, bottom: 0 }} }});
    volume.setData(chartEvidence.volume);

    const smaColors = {{ 'sma-20': '#2962ff', 'sma-50': '#ab47bc', 'sma-200': '#ff9800' }};
    const smaLineStyles = {{
      'sma-20': LightweightCharts.LineStyle.Solid,
      'sma-50': LightweightCharts.LineStyle.Dashed,
      'sma-200': LightweightCharts.LineStyle.Dotted
    }};
    const smaSeries = {{}};
    for (const [name, points] of Object.entries(chartEvidence.moving_averages)) {{
      const line = chart.addSeries(LightweightCharts.LineSeries, {{
        color: smaColors[name], lineStyle: smaLineStyles[name], lineWidth: 2,
        title: name.toUpperCase(), priceLineVisible: false, lastValueVisible: true
      }});
      line.setData(points);
      smaSeries[name] = line;
    }}
    for (const level of chartEvidence.key_levels) {{
      candles.createPriceLine({{
        price: level.price,
        color: level.side === 'support' ? '#26a69a' : '#ef5350',
        lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed,
        axisLabelVisible: true,
        title: `${{level.side === 'support' ? '支撑' : '阻力'}} · ${{level.touches}} 次确认`
      }});
    }}
    const tooltip = document.getElementById('crosshair-tooltip');
    const number = value => Number.isFinite(value) ? value.toFixed(2) : '—';
    chart.subscribeCrosshairMove(param => {{
      const candle = param.seriesData.get(candles);
      if (!param.time || !candle) {{
        tooltip.textContent = '移动十字光标查看 OHLCV、成交量与均线';
        return;
      }}
      const volumePoint = param.seriesData.get(volume);
      const values = Object.entries(smaSeries).map(([name, series]) => {{
        const point = param.seriesData.get(series);
        return `${{name.toUpperCase()}} ${{number(point?.value)}}`;
      }});
      tooltip.textContent = [
        String(param.time), `O ${{number(candle.open)}}`, `H ${{number(candle.high)}}`,
        `L ${{number(candle.low)}}`, `C ${{number(candle.close)}}`,
        `成交量 ${{volumePoint?.value ?? '—'}}`, ...values
      ].join(' · ');
    }});
    chart.timeScale().fitContent();
    new ResizeObserver(entries => {{
      const box = entries[0].contentRect;
      chart.resize(box.width, box.height);
    }}).observe(container);
  </script>
</body>
</html>
"""


def _cleanup_expired_charts() -> None:
    temporary_root = Path(tempfile.gettempdir())
    cutoff = time.time() - TEMPORARY_CHART_MAX_AGE_SECONDS
    for candidate in temporary_root.glob("mars-technical-chart-*"):
        try:
            candidate_stat = candidate.stat()
            if candidate.is_symlink() or not candidate.is_dir():
                continue
            if hasattr(os, "getuid") and candidate_stat.st_uid != os.getuid():
                continue
            if candidate_stat.st_mtime >= cutoff:
                continue
            marker = candidate / TEMPORARY_CHART_MARKER_NAME
            chart = candidate / "chart.html"
            if marker.is_symlink() or chart.is_symlink():
                continue
            if not marker.is_file() or not chart.is_file():
                continue
            if {path.name for path in candidate.iterdir()} != {
                TEMPORARY_CHART_MARKER_NAME,
                "chart.html",
            }:
                continue
            if json.loads(marker.read_text(encoding="utf-8")) != TEMPORARY_CHART_MARKER:
                continue
            shutil.rmtree(candidate)
        except (json.JSONDecodeError, OSError):
            continue


def temporary_chart(html: str) -> Path:
    _cleanup_expired_charts()
    directory = Path(tempfile.mkdtemp(prefix="mars-technical-chart-"))
    chart_path = directory / "chart.html"
    try:
        chart_path.write_text(html, encoding="utf-8", newline="\n")
        (directory / TEMPORARY_CHART_MARKER_NAME).write_text(
            json.dumps(TEMPORARY_CHART_MARKER, ensure_ascii=False, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    except Exception:
        shutil.rmtree(directory, ignore_errors=True)
        raise
    return chart_path


def visualization_result(
    chart_path: Path | None,
    *,
    open_chart: bool,
) -> dict[str, Any]:
    if chart_path is None:
        return {
            "kind": "temporary_html",
            "path": None,
            "generated": False,
            "open_attempted": False,
            "open_confirmed": False,
            "limitation": "visualization withheld because evidence did not qualify",
            "expires_after_seconds": None,
        }
    open_attempted = False
    open_confirmed = False
    limitation: str | None = None
    if open_chart:
        open_attempted = True
        try:
            configured_browser = os.environ.get("BROWSER")
            browser = (
                webbrowser.get(configured_browser)
                if configured_browser
                else webbrowser
            )
            open_confirmed = bool(browser.open(chart_path.as_uri()))
            if not open_confirmed:
                limitation = "browser did not confirm accepting the open request"
        except Exception as error:  # browser/desktop integration boundary
            limitation = f"browser open failed: {type(error).__name__}"
    return {
        "kind": "temporary_html",
        "path": str(chart_path.resolve()),
        "generated": True,
        "open_attempted": open_attempted,
        "open_confirmed": open_confirmed,
        "limitation": limitation,
        "expires_after_seconds": TEMPORARY_CHART_MAX_AGE_SECONDS,
    }
