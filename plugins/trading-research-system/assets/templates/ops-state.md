# Daily Ops State

This private runtime file tracks the user's current Daily Ops flow. It belongs
under `{runtime_dir}/ops-state.md`, not in the public plugin repo.

## State

- current_stage:
- next_recommended_action:
- blocked_reason:
- last_deep_update:
- last_quick_update:
- last_intraday_scan:
- last_post_market_review:
- last_position_daily_report:
- last_research_monitor:

## Pending Confirmations

- pending_confirmations:

## Active Setups

- active_setups:

| ticker | trade_horizon | instrument | setup_id | status | next_check |
| --- | --- | --- | --- | --- | --- |

## Notes

- Keep this compact.
- Do not store raw broker exports.
- Do not store paywalled report text.
- Objective broker facts should come from authorized read-only broker sources
  when needed.
