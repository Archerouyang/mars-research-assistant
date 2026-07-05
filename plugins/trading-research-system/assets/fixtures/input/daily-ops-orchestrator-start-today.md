# Daily Ops Orchestrator Input Fixture

User prompt:

```text
开始今天交易流程。先帮我判断现在应该做什么。我现在关注 QQQ、MU、TSM、GLW，但这些标的的交易周期未知。
```

Available state:

- runtime health: available
- `ops-state.md`: missing
- `market-plan.md`: available
- `trading-profile.md`: available
- KVN snapshot: stale
- broker source: unauthorized
- current context: weekday premarket

Constraints:

- Do not write runtime.
- Do not read broker.
- Do not create real automation.
- Do not web search in this fixture.
