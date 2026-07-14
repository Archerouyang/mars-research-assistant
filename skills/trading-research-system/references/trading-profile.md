# Trading Profile

Use this reference when translating market setups into strategy posture, candidate pools, instrument choices, timeframe rules, crowding adjustments, and risk framing.

The Trading Research System should not assume every user expresses the same market idea with the same product. A setup should be evaluated against the user's trading profile before it becomes an `active` setup or a trade review baseline.

## File Boundary

Use:

```text
{runtime_dir}/trading-profile.md
```

This is private user data and should not be committed to the public plugin repository. The public plugin only ships `assets/templates/trading-profile.md`.

Default `runtime_dir` is `~/Documents/dailytrades-runtime`. If `{runtime_dir}/trading-profile.md` is unavailable, ask the user for the relevant preferences instead of inventing them.

## What Belongs Here

Include:

- trading objective;
- preferred holding periods;
- strategy posture scoring rules and thresholds;
- active trading pools;
- long-term ETF groups;
- macro allocation rules;
- crowding model inputs, weights, and actions;
- allowed and avoided instruments;
- timeframe rules by instrument or setup type;
- instrument preference rules;
- setup-to-instrument translation rules;
- personal avoid rules;
- sizing/risk guardrails;
- review tags the user wants to track.

Do not require account names. The profile describes trading style and instrument preference, not account allocation.

## Setup Translation

When a market opportunity appears, translate it into one or more setup-level plans:

1. Identify the market context and setup type.
2. Apply the user's strategy posture scoring and pool rules.
3. Check whether the opportunity belongs to a profile-defined pool.
4. Apply crowding adjustments when the profile defines them.
5. Check whether the setup matches the user's preferred instruments.
6. If the same opportunity can be expressed with multiple tools, create separate setups that share `theme_id`.
7. Assign analysis and trigger timeframes from the profile's timeframe rules.
8. Mark the setup `candidate` until the user confirms it belongs in the active plan.

## Example Rules

A user may prefer:

- ETF-only expressions for one category of trades;
- a private theme core pool;
- a large-cap liquidity leaders pool;
- strategy posture scores such as Risk Budget, Trend Fit, and Mean Reversion Fit;
- a crowding model for theme-level and ticker-level congestion;
- common stock for high-momentum or high-elasticity single names;
- common stock, 2x ETF expression, or LEAP call add-ons for large-cap names with lower elasticity;
- macro allocation setups for assets such as gold, bonds, commodities, or FX;
- stricter trigger confirmation for 0DTE options;
- slower confirmation and wider context for LEAP calls.

These are examples, not defaults. Use the user's local profile when available.

## Deep And Quick Updates

During `deep_update`, use the trading profile to:

- calculate or interpret strategy posture score thresholds;
- decide which profile-defined pools should be active;
- decide which candidate setups are worth expressing;
- choose the first instrument expression for each setup;
- split one market theme into multiple instrument-specific setups when needed;
- avoid setups that violate personal avoid rules.

During `quick_update` or `trigger_update`, use the trading profile to:

- check whether the selected instrument still fits the changed market context;
- flag when a setup should change expression rather than simply update levels;
- add `needs_review` when current conditions conflict with the profile.

## Output Rules

When profile rules matter, mention:

- preferred expression;
- active pool or rejected pool;
- strategy posture score or manual override that mattered;
- crowding adjustment that mattered;
- rejected expression;
- reason for instrument choice;
- timeframe implied by the instrument;
- risk or avoid rule triggered.

Do not expose private account details in public docs or generated project logs.
