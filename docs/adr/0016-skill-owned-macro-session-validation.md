---
status: accepted
---

# Validate Macro sessions inside the Skill

Macro providers supply each ratio as a same-source, inseparable pair of source-labelled constituent 1D observation series; a missing leg makes the entire pair eligible for lazy fallback rather than permitting cross-source stitching. The stateless Skill receives a caller-supplied, timezone-aware research reference time, an XNYS session calendar, and a primary-event-source registry that binds the event title, category, timezone-aware time, permitted evidence kind, and exact original URL. It derives the HYG/LQD and NDX/RUT intersections, validates the last completed session, and requires the registry before rendering a Board. This rejects the tempting but unauditable alternatives of trusting a provider's precomputed ratio and `completed` flag, or accepting a claimed primary event solely from an `https` URL, keeping Longbridge and yfinance interchangeable without weakening the frozen Macro semantics.
