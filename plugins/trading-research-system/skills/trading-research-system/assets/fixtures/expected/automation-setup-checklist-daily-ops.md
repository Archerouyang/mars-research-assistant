# Automation Setup Summary

Daily Ops automation setup is not complete yet. The intended workflow is clear:
use the fixed trading operations chat, `~/Documents/dailytrades-runtime`, and
Chinese concise notes to run weekly/daily Active Market Plan prompts, focused
macro/industry monitoring, intraday prepared-setup checks, position daily
reports, and post-market cleanup.

Do not create real Codex automations yet.

## Confirmed Configuration

| Field | Confirmed Value |
| --- | --- |
| timezone | Asia/Shanghai, pending user reconfirmation |
| runtime_dir | `~/Documents/dailytrades-runtime` |
| enabled automations | weekly deep update; weekday premarket quick update; intraday trigger monitor; post-market review; position daily report; macro/industry/news research monitor |
| allowed sources | public web search; official/primary sources; Longbridge macrodata when installed and authorized; IBKR connector read-only when authorized; Longbridge broker read-only when authorized; user-provided Seeking Alpha artifacts |
| runtime write policy | draft proposed updates first; ask before writing runtime files |
| broker policy | read-only broker access only |

## Missing Decisions

- Confirm the exact Daily Ops thread id/name.
- Confirm exact cadence for each automation.
- Confirm US-market calendar handling for holidays and event-window exceptions.
- Confirm whether Longbridge, IBKR, both, manual CSV, or no broker data should
  be used on the first real run.
- Confirm whether runtime writes can happen after each explicit approval or
  should stay draft-only every time.

## Draft Automation Plan

| Automation | Cadence | Reads | Proposed Writes |
| --- | --- | --- | --- |
| weekly deep update | weekend or user-confirmed reset window | runtime health; market-plan; trading-profile; prior updates; public/authorized sources | proposed `market-plan.md` rewrite and update note draft |
| weekday premarket quick update | weekday premarket | runtime health; current Active Market Plan; latest macro/rates/policy/news deltas | proposed update note and setup status changes |
| intraday trigger monitor | market hours only when active setups exist | prepared setups and authorized price/chart facts | no direct writes unless user asks |
| post-market review | after US close or local morning | setup statuses; broker read-only facts when authorized | proposed review queue and update note |
| position daily report | after US close or local morning | Longbridge/IBKR read-only broker facts or manual snapshot | proposed private position report |
| macro/industry/news research monitor | user-confirmed cadence around P0/P1 events | public/authorized sources; Longbridge macrodata; user-provided Seeking Alpha leads | proposed research delta note and verification queue |

## Safety Boundaries

- no broker write actions;
- no order placement, modification, cancellation, closing, or approval;
- no paywall bypass;
- inaccessible Seeking Alpha or other reports become research leads only;
- no raw broker export saved by default;
- no private runtime or broker data written to the public plugin repo.

## Next Action

Ask the user to confirm the missing decisions. After all confirmations are
present, ask whether to create the real Codex automations.
