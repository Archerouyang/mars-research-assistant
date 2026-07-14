# Chart artifacts, not a dashboard

The Trading Research System will generate display-first chart artifacts on demand instead of maintaining a permanent charting frontend. For price action review, the plugin may generate transient chat images, local HTML pages, or Markdown report sections showing K lines, 20 EMA, 50 EMA, multi-timeframe structure, and setup annotations.

The canonical price-action renderer is TradingView Lightweight Charts v5.2.0
interactive HTML. A browser captures the transient static image from that same
HTML for chat or documentation. The handcrafted SVG is retained only as a
no-browser fallback. Macro and position-risk panels may remain purpose-built
SVGs because they are not K-line renderers. This keeps chart interaction
familiar while avoiding a persistent frontend application.

Durable storage is an optional durable save, not the default. The agent should ask before saving visual artifacts into runtime records or manifests; otherwise chart output should remain transient under ignored paths such as `.scratch/visual-artifacts/`.

**Considered Options**

- Generate local chart artifacts from IBKR or other authorized market data.
- Generate local HTML chart artifacts with TradingView `lightweight-charts` and capture transient chat images from them.
- Retain handcrafted price-action SVG only as a no-browser fallback; use purpose-built SVG for macro/regime and position risk.
- Embed TradingView widgets when useful.
- Build and maintain a standalone chart dashboard.

**Consequences**

- Charting stays aligned with the plugin-first architecture.
- The system can still support Al Brooks-style setup analysis without taking on frontend product scope.
- The agent can show concise annotated charts in the conversation while keeping full source notes in local records.
- Macro/rates/regime snapshots can be displayed as small decision panels without becoming a dashboard.
- A persistent dashboard remains deferred until repeated manual review needs justify it.
