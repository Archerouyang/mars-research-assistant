# Mars Guided Research Flow Spec

Status: approved for ticketing.

## Problem Statement

Mars Daily Ops accumulated a rigid portfolio-risk phase between macro research
and named-instrument work. It conflates broker market-data access with account
holdings access, produces risk calculations the user no longer wants, and can
block a direct request for company, technical, or Price Action research.

## Solution

Mars becomes a guided, not mandatory, research flow:

1. an unscoped start checks Longbridge and IBKR source capability, then
   automatically delivers the canonical Macro Board or one Data Acquisition
   Blocker;
2. Macro fields prefer the configured read-only broker's eligible market/macro
   records, with exact public primary sources as field-level fallback;
3. after Macro, Mars asks whether to read and display the default broker's
   holdings, but does not read them without a per-request user confirmation;
4. Holdings Display is a compact factual view, not a Portfolio Risk Panel;
5. a user can name an instrument at any time and immediately receive the full
   research bundle without completing Holdings Display;
6. named-instrument research defaults to industry events, fundamentals,
   technical analysis, and the accepted 4H PA standalone Board.

## User Stories

1. As a trader, I want an unscoped Daily Ops start to check the available
   Longbridge and IBKR connections before using market data, so that the Macro
   Board uses the best available verified source path.
2. As a trader, I want every Macro field to prefer an eligible broker
   market/macro record and fall back to an exact public primary source, so that
   a missing public page does not discard valid broker data.
3. As a trader, I want a Macro Board to refuse delivery when any required field
   lacks identity, native path, unit, timestamp, or the required close/reference
   period, so that a polished artifact never hides a material data gap.
4. As a trader, I want Macro research to avoid accounts, positions, balances,
   and orders, so that market-data access does not imply account-data access.
5. As a trader, I want Mars to ask before reading holdings, so that I choose
   when private account information enters the conversation.
6. As a trader, I want Holdings Display to show broker, symbol, quantity, last
   price, market value, cost, unrealized P&L, cash, and retrieval time, so that
   I can inspect the current account facts without a risk-model overlay.
7. As a trader, I want unavailable holdings fields to be labelled unavailable,
   so that incomplete responses are not silently reconstructed.
8. As a trader, I do not want concentration, leverage-adjustment, stress,
   scenario loss, or risk-scoring output in Holdings Display, so that this
   workflow stays simple and factual.
9. As a trader, I want Macro completion to offer a next action instead of
   forcing Holdings Display, so that I retain control of the research sequence.
10. As a trader, I want a named ticker to bypass any unselected holdings step,
    so that a direct research request is never blocked by a default workflow.
11. As a trader, I want a named ticker to receive industry events, fundamentals,
    technical analysis, and 4H PA by default, so that I do not have to request
    every analytical layer separately.
12. As a trader, I want the existing accepted 4H PA standalone Board to remain
    the technical visual, so that the Skill does not create another visual
    surface or change accepted presentation behavior.
13. As a trader, I want the industry and fundamental interpretation delivered as
    concise Markdown beside the PA Board, so that sources and counter-theses
    remain readable and auditable.
14. As a trader, I want no order creation, modification, cancellation, or
    implied approval anywhere in this flow, so that research remains decision
    support only.

## Implementation Decisions

- `daily_ops_routing` is the single high-level behavioral seam. It changes from
  a mandatory Portfolio Risk state machine to a guided router with capability,
  Macro, optional Holdings Display, and explicit named-instrument routes.
- Capability discovery remains side-effect-free. It detects Longbridge and
  host-visible IBKR support without reading accounts, holdings, balances,
  orders, credentials, or raw provider payloads.
- Macro Preflight owns field-level source precedence. Broker records are
  admitted only with their source identity, native field identity/path, unit,
  timestamp, and required market-close or official-reference basis. Direct
  public sources are fallback only for uncovered fields.
- The router must not require a public payload for a field that a valid broker
  record already supplies. It must still validate common completed-market dates
  across the final normalized field set.
- Holdings Display has its own small factual input/output contract. It consumes
  a per-request authorized default-broker snapshot and exposes only the eight
  user-approved columns plus a retrieval timestamp. It does not invoke the
  Portfolio Risk adapter, risk aggregation, stress model, or a Portfolio Board.
- No automatic holdings read follows Macro delivery. Mars asks whether to show
  holdings and offers direct named-instrument research as an equally valid next
  action.
- A direct instrument request remains focused. Its default bundle combines
  industry-event and fundamental Markdown with the accepted 4H PA standalone
  Board. It may be narrowed only by an explicit user request.
- Delete the Mars-only portfolio-risk implementation after its replacement
  paths pass; no supported caller may remain.

## Testing Decisions

- Test the public behavior through `daily_ops_routing`, not private helpers.
- Assert an unscoped start reaches capability check then canonical Macro Board
  or one blocker; it must not auto-read holdings or auto-run PA.
- Assert Macro accepts valid broker-covered market fields even when the matching
  public fallback payload is absent, and returns the exact field blocker when
  neither path is valid.
- Assert Holdings Display requires explicit per-request consent, calls a
  display-only path, and has no risk, stress, concentration, or broker-order
  actions.
- Assert a named ticker bypasses Holdings Display and selects the complete
  research bundle, including the frozen PA Board contract.
- Reuse existing Macro Preflight, routing, capability, ResearchResult, and PA
  standalone Board selftests; add only focused behavior cases to those seams.

## Out of Scope

- Portfolio Risk Panels, concentration metrics, leverage-adjusted exposure,
  stress scenarios, risk scores, and portfolio-based trade recommendations.
- Broker order, execution, or account mutation capabilities.
- A new all-in-one company/instrument Board.
- A new public data vendor, proxy series, or incomplete Macro Board.
- Removing portfolio-risk code that still has a non-Mars compatibility caller.

## Further Notes

- The configured default broker is a source preference, not permission to read
  holdings. Holdings require fresh user consent every time.
- Macro market data and holdings are distinct data categories even when they
  come from the same broker connection.
- The Skill remains private and decision-support-only.
- Once the guided replacement paths pass, remove Mars-only Portfolio Risk
  routes, templates, tests, references, and visual-adapter calls that no longer
  have a supported caller.
