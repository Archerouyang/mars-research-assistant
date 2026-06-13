# Plugin-first interface

We will build the Trading Research System as a Codex plugin and CLI-like workflow first, and defer a standalone frontend. The system's primary user is an agent working through Codex, so the highest-value interface is a plugin with skills, scripts, templates, data schemas, research notes, and automation-ready workflows; chart pages can be generated as artifacts when needed instead of maintained as a permanent dashboard.

**Considered Options**

- Plugin/CLI first, with generated notes, CSV outputs, and chart artifacts.
- Standalone frontend or dashboard first.

**Consequences**

- The project prioritizes agent-usable workflows, structured inputs, reproducible analysis, and trade journal statistics before UI polish.
- Frontend work is deferred until repeated manual review pain justifies a persistent dashboard.
- Charting is still allowed as generated artifacts, especially for price action review and multi-timeframe setup analysis.
