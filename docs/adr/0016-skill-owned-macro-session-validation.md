---
status: accepted
---

# Validate Macro sessions inside the Skill

Macro providers supply each ratio as a same-source, inseparable pair of source-labelled constituent 1D observation series; a missing leg makes the entire pair eligible for lazy fallback rather than permitting cross-source stitching. The stateless Skill receives a caller-supplied, timezone-aware research reference time and an XNYS session calendar, derives the HYG/LQD and NDX/RUT intersections, and validates the last completed session before rendering a Board. This rejects the tempting but unauditable alternative of trusting a provider's precomputed ratio and `completed` flag, keeping Longbridge and yfinance interchangeable without weakening the frozen Macro semantics.
