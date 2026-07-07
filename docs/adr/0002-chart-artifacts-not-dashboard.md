# Chart artifacts, not a dashboard

The Trading Research System will generate display-first chart artifacts on demand instead of maintaining a permanent charting frontend. For price action review, the plugin may generate transient chat images, local HTML pages, or Markdown report sections showing K lines, 20 EMA, 50 EMA, multi-timeframe structure, and setup annotations.

The default user-facing renderer is a transient SVG that can be shown directly in chat. The optional local chart artifact renderer uses TradingView `lightweight-charts` in a generated HTML file. This keeps the chart interaction familiar while avoiding a persistent frontend application.

Durable storage is an optional durable save, not the default. The agent should ask before saving visual artifacts into runtime records or manifests; otherwise chart output should remain transient under ignored paths such as `.scratch/visual-artifacts/`.

**Considered Options**

- Generate local chart artifacts from IBKR or other authorized market data.
- Generate local HTML chart artifacts with TradingView `lightweight-charts`.
- Generate transient chat-first SVG artifacts for price action and macro/regime context.
- Embed TradingView widgets when useful.
- Build and maintain a standalone chart dashboard.

**Consequences**

- Charting stays aligned with the plugin-first architecture.
- The system can still support Al Brooks-style setup analysis without taking on frontend product scope.
- The agent can show concise annotated charts in the conversation while keeping full source notes in local records.
- Macro/rates/regime snapshots can be displayed as small decision panels without becoming a dashboard.
- A persistent dashboard remains deferred until repeated manual review needs justify it.
