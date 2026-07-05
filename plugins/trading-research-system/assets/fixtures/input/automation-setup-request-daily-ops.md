# Automation Setup Request

The user wants to enable Daily Ops automations for the Trading Research System.

Known preferences:

- Daily Ops thread: fixed trading operations chat, name likely `交易研究 Daily Ops`.
- Runtime directory: `~/Documents/dailytrades-runtime`.
- Timezone: Asia/Shanghai unless the user overrides it.
- Enabled automations requested:
  - weekly deep update;
  - weekday premarket quick update;
  - intraday trigger monitor when active setups exist;
  - post-market review;
  - position daily report;
  - macro/industry/news research monitor after weekly P0/P1 variables are set.
- Source preferences:
  - public web search and official sources for macro, policy, rates, earnings,
    and company confirmation;
  - Longbridge macrodata for macro/financial-conditions data when installed and
    authorized;
  - IBKR connector for read-only broker facts when authorized;
  - Longbridge broker source for read-only broker facts when authorized;
  - user-provided Seeking Alpha reports, excerpts, PDFs, screenshots, or links;
  - no paywall bypass.
- Broker boundary: read-only; no order creation, modification, cancellation,
  closing, or approval.
- Runtime write preference: draft proposed updates first; ask before writing
  `market-plan.md`, update notes, position reports, or review context.

Need confirmation:

- exact Daily Ops thread id/name;
- exact cadence and market-calendar handling;
- whether Longbridge and IBKR are authorized for the first real run;
- whether runtime writes should be allowed after confirmation or always remain
  draft-only.

