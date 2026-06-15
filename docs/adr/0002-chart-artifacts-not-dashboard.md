# Chart artifacts, not a dashboard

The Trading Research System will generate chart artifacts on demand instead of maintaining a permanent charting frontend. For price action review, the plugin may generate local HTML pages, images, or Markdown report sections showing K lines, 20 EMA, 50 EMA, multi-timeframe structure, and setup annotations.

The default local chart artifact renderer uses TradingView `lightweight-charts` in a generated HTML file. This keeps the chart interaction familiar while avoiding a persistent frontend application.

**Considered Options**

- Generate local chart artifacts from IBKR or other authorized market data.
- Generate local HTML chart artifacts with TradingView `lightweight-charts`.
- Embed TradingView widgets when useful.
- Build and maintain a standalone chart dashboard.

**Consequences**

- Charting stays aligned with the plugin-first architecture.
- The system can still support Al Brooks-style setup analysis without taking on frontend product scope.
- The agent can show concise annotated charts in the conversation while keeping full source notes in local records.
- A persistent dashboard remains deferred until repeated manual review needs justify it.
