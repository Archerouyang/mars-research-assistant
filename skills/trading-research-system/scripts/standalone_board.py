#!/usr/bin/env python3
"""Build the only supported visual delivery: a self-contained Board packet."""

from __future__ import annotations

from html import escape
from typing import Any, Mapping

from artifact_packet import ArtifactPacket, canonical_json_bytes, sha256_hex
from board_visual import BoardVisualError, render_board_visual


SCHEMA_VERSION = "1.0"
MAX_STANDALONE_HTML_BYTES = 4 * 1024 * 1024


def build_standalone_board(
    visual: Mapping[str, Any] | None,
    privacy: str,
) -> ArtifactPacket | None:
    """Return deterministic snapshot, standalone HTML, and manifest bytes."""

    if visual is None:
        return None
    fragment = render_board_visual(visual, privacy)
    if fragment is None:
        return None
    adapter = str(visual.get("adapter") or "board")
    snapshot = canonical_json_bytes(
        {
            "artifact_kind": "standalone_board",
            "privacy": privacy,
            "schema_version": SCHEMA_VERSION,
            "visual": visual,
        }
    )
    html = _document(adapter, fragment)
    if len(html) > MAX_STANDALONE_HTML_BYTES:
        raise BoardVisualError("standalone_board_size_invalid")
    manifest = canonical_json_bytes(
        {
            "artifact_kind": "standalone_board",
            "canonical_html": "research-brief.html",
            "canonical_json": "snapshot.canonical.json",
            "canonical_json_sha256": sha256_hex(snapshot),
            "html_sha256": sha256_hex(html),
            "manifest_version": SCHEMA_VERSION,
            "privacy": privacy,
            "schema_version": SCHEMA_VERSION,
            "visual_adapter": adapter,
        }
    )
    return ArtifactPacket(canonical_json=snapshot, html=html, manifest=manifest)


def _document(adapter: str, fragment: bytes) -> bytes:
    title = f"DailyTrades {adapter.replace('_', ' ').title()} Board"
    body = fragment.decode("utf-8")
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'">
  <title>{escape(title)}</title>
  <style>
    :root{{--background:#f7f8fa;--foreground:#17202a;--card:#fff;--card-foreground:#17202a;--muted:#eef1f4;--muted-foreground:#66717d;--border:#dce2e8;--primary:#1769aa;--primary-foreground:#fff;--destructive:#b43b32;--warning:#9a6700;--dt-warning:#9a6700;--viz-series-1:#1769aa;--viz-series-2:#9a6700;--viz-series-3:#6f42c1;--viz-series-4:#2f855a;color-scheme:light;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
    *{{box-sizing:border-box}}
    body{{margin:0;background:var(--background);color:var(--foreground);font-size:14px;line-height:1.5}}
    main{{width:min(1180px,100%);margin:0 auto;padding:18px}}
    button,input,select,textarea{{font:inherit}}
    .dt-board{{padding:18px;background:var(--card);border:1px solid var(--border);border-radius:8px;box-shadow:0 1px 2px rgba(23,32,42,.05)}}
    .viz-row{{display:flex;align-items:center;flex-wrap:wrap}}
    .viz-grid{{display:grid;gap:10px}}
    .viz-stat,.card{{display:block;padding:12px;background:var(--card);color:var(--card-foreground);border:1px solid var(--border);border-radius:6px}}
    .viz-stat-value{{font-size:18px;font-weight:650;font-variant-numeric:tabular-nums}}
    .viz-controls{{display:flex;flex-wrap:wrap;gap:6px}}
    .btn{{appearance:none;border:1px solid var(--border);border-radius:6px;background:var(--card);color:var(--foreground);padding:7px 10px;cursor:pointer}}
    .btn:hover{{border-color:var(--primary)}}
    .btn:focus-visible{{outline:3px solid rgba(23,105,170,.25);outline-offset:2px}}
    .btn-primary,.btn[aria-pressed="true"]{{background:var(--primary);border-color:var(--primary);color:var(--primary-foreground)}}
    .text-small{{font-size:12px}}
    .text-muted{{color:var(--muted-foreground)}}
    .viz-badge{{display:inline-flex;align-items:center;padding:3px 7px;border-radius:999px;background:var(--muted);color:var(--muted-foreground);font-size:11px;font-weight:600}}
    h1,h2,h3,p{{overflow-wrap:anywhere}}
    svg{{max-width:100%}}
    @media(max-width:640px){{main{{padding:8px}}.dt-board{{padding:12px}}}}
  </style>
</head>
<body>
  <main>{body}</main>
</body>
</html>
"""
    return html.encode("utf-8")
