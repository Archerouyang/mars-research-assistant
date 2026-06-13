# Chart artifacts, not a dashboard

The Trading Research System will generate chart artifacts on demand instead of maintaining a permanent charting frontend. For price action review, the plugin may generate local HTML pages, images, or Markdown report sections showing K lines, 20 EMA, 50 EMA, multi-timeframe structure, and setup annotations.

**Considered Options**

- Generate local chart artifacts from IBKR or other authorized market data.
- Embed TradingView widgets when useful.
- Build and maintain a standalone chart dashboard.

**Consequences**

- Charting stays aligned with the plugin-first architecture.
- The system can still support Al Brooks-style setup analysis without taking on frontend product scope.
- A persistent dashboard remains deferred until repeated manual review needs justify it.
