# Daily Ops Orchestrator Input Fixture

User prompt:

```text
开始今天的交易研究
```

Available state:

- runtime health: available
- runtime_dir: `/private/tmp/mars-research-assistant-uat-runtime-9a24200`
- runtime_origin: explicit_argument
- formal runtime: available
- startup_status: ready
- startup_reason: not provided by runtime_health.py
- current_mode: dry-run
- `ops-state.md`: missing
- `market-plan.md`: available
- `trading-profile.md`: available
- `daily/YYYY-MM-DD/`: available
- KVN snapshot: missing
- macro-panel.json: missing; authorized/current macro values: missing; no actual macro values
- portfolio_snapshot.csv: available; status only; no private rows read
- source_capability_health:
  - Longbridge broker skill: needs_review; capability status not confirmed; authorization is not inferred
  - Longbridge Terminal CLI: needs_review; capability status not confirmed; authorization is not inferred
  - Longbridge macrodata: needs_review; capability status not confirmed; authorization is not inferred
  - Official source fallback: missing; capability output missing
  - IBKR connector: needs_review; capability status not confirmed; authorization is not inferred
  - Manual snapshot: missing; capability output missing
- broker_source_health: Longbridge needs_review; IBKR needs_review; Manual snapshot missing; no broker facts were read
- portfolio_reconciliation: unavailable; excluded sources longbridge and ibkr
- current context: weekday premarket
- existing watch context: QQQ、MU、TSM、GLW，交易周期未知

Constraints:

- Do not write runtime.
- Do not read broker.
- Do not create real automation.
- Do not web search in this fixture.
