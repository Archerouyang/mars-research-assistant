# Debug Plan

This document is the public source of truth for reproducible defects,
regressions, and acceptance failures. It tracks observed behavior, verification,
and closure criteria; it is not a feature roadmap or a technical-debt backlog.

Do not include private runtime contents, broker/account data, credentials, or
internal prompts. Record only the smallest public-safe reproduction and the
observable expected versus actual behavior.

## Boundaries

| Work type | Record here | Do not record here |
| --- | --- | --- |
| New capability, integration, or approved refactor | `docs/DEVELOPMENT_PLAN.md` | Defect triage details |
| Observed defect, regression, or failed acceptance | This document | Unproven architecture diagnosis |
| Cross-cutting design cost or repeated root cause | `docs/TECHNICAL_DEBT.md` | One-off defect fixes |
| Hard-to-reverse approved architectural decision | `docs/adr/` | Implementation task tracking |

## Debug Lifecycle

1. Record the smallest reproducible symptom, severity, affected contract, and
   expected/actual behavior.
2. Reproduce in an isolated task branch or worktree when feasible. Classify the
   result as reproducible, not reproducible, blocked, or duplicate.
3. Diagnose before fixing. A symptom becomes technical debt only when the root
   cause is cross-cutting, recurring, or materially raises future change cost.
4. Implement the smallest scoped correction and add the relevant regression
   check, contract test, or fresh-chat acceptance evidence.
5. Mark the item `closed` only after the stated exit evidence passes. Move a
   recurring systemic cause to the technical-debt register with a pointer.

## Status And Severity

- Status: `reported`, `reproducing`, `in_progress`, `blocked`, `verified`,
  `closed`, `duplicate`, or `deferred`.
- Severity: `P0` safety, data-boundary, or decision-correctness failure;
  `P1` core workflow regression; `P2` degraded clarity, ergonomics, or
  non-blocking behavior; `P3` minor defect.
- A `P0` supersedes feature work. A `P1` is scheduled before the affected
  workflow receives new capability. `P2` and `P3` are triaged in the weekly
  review unless they share a root cause with a higher-severity item.

## Active Debug Board

| ID | Severity | Status | Observed behavior | Exit evidence | Owner |
| --- | --- | --- | --- | --- | --- |
| DBG-20260711-01 | P1 | closed | New Daily Ops chats do not make the private-runtime binding and startup state unambiguous. | Fresh-chat startup reports the resolved runtime scope and its state without exposing private content. | `debug1` |
| DBG-20260711-02 | P1 | closed | Partially available IBKR source data can be labelled as unauthorized rather than partial/degraded. | Source-health output preserves the distinct capability state and the relevant contract/self-test passes. | `debug1` |
| DBG-20260711-03 | P2 | closed | A medium-horizon price-action request with authorized OHLCV may not surface its visual artifact until explicitly requested. | The visual-trigger policy is exercised by a fresh-chat regression case and renders the expected chart state. | `debug1` |
| DBG-20260711-04 | P1 | closed | Separate IBKR NAV and Longbridge detail can be presented as confirmed combined exposure. | Portfolio output distinguishes coverage and prevents unsupported aggregate exposure claims. | `debug1` |
| DBG-20260711-05 | P2 | closed | Trading horizon and instrument confirmations are requested too late in the Daily Ops flow. | The required decision context is requested before dependent plan/setup reasoning. | `debug1` |
| DBG-20260711-06 | P2 | closed | The first weekly-plan response is overly status-oriented and does not foreground the actionable weekly plan. | Fresh-chat acceptance shows an ordered weekly plan with status details kept secondary. | `debug1` |
| DBG-20260719-01 | P1 | closed | The 0.2.0 candidate emits a 1.2 MB iframe-wrapped canonical Board instead of the compact native Codex inline chart the user approved in prior Daily Ops work. | ResearchResult emits a direct native fragment with no iframe or standalone document, remains below 100 KB on the reference fixture, and the user accepted the four-view Macro structure on 2026-07-19. | `codex/skill-v2-0.2.0` |
| DBG-20260719-02 | P1 | closed | The native Macro candidate uses single-value bars across unrelated units, so NDX/RUT, VXN, DXY, and rates do not show direction; scenarios are not visibly linked to current conditions or next-week events. | The accepted fragment uses selectable time series, causal event linkage, asset-preference impact, and comparison-row scenarios; the user froze this structure on 2026-07-19. | `codex/skill-v2-0.2.0` |
| DBG-20260719-03 | P0 | closed | A public synthetic Macro fixture is rendered with current-looking timestamps and values but no visible fixture disclosure; its NDX/RUT and VXN series can therefore be mistaken for verified live market data. | Public fixtures are visibly labelled as demo-only and never support a live/verified claim; the accepted live artifact uses aligned one-month NDX/RUT, VXN, exact DXY, rates, credit, and oil series with provenance, and the user froze the working data workflow on 2026-07-19. | `codex/skill-v2-0.2.0` |
| DBG-20260719-04 | P1 | closed | Portfolio Risk still uses the old generic bar-chart shell, so the first viewport does not clearly connect cash buffer, gross/delta exposure, look-through concentration, leverage amplification, source coverage, and stress loss. | The accepted chat-inline panel presents a decision-dense portfolio summary, comparable concentration views, visible leverage and exclusions, underlying fundamentals, and dedicated stress impact; the user froze the structure on 2026-07-20. | `codex/skill-v2-0.2.0` |
| DBG-20260720-01 | P1 | closed | Adding client-rendered fundamentals expanded the Portfolio Risk inline script to about 22 KB and the Codex chat `document.write` path failed with `Invalid or unexpected token`. | Fundamentals cards and Forward P/E SVGs are pre-rendered, the remaining client script stays below 12 KB, a `document.write` reproduction loads without console errors, and 680px/480px checks show no horizontal overflow or text overlap. | `codex/skill-v2-0.2.0` |
| DBG-20260720-02 | P2 | closed | Portfolio Risk overview hard-codes four concentration rows, so a leveraged holding such as KORU can be present in detail views but absent from the overview. | The overview shows up to six ranked look-through underlyings, the current Longbridge artifact includes EWY for KORU, and the fifth-underlying regression assertion passes. | `codex/skill-v2-0.2.0` |
| DBG-20260720-03 | P1 | closed | Portfolio fundamentals share one collection timestamp even when the Longbridge summary endpoint lags the latest quarterly statement; TSM therefore showed Q1 after Q2 was available. | Latest-quarter statement fields override stale summaries, each metric displays its own period or observation date, short-interest values fail closed after 45 days, and IV30 names its Cboe delayed source. | `codex/skill-v2-0.2.0` |
| DBG-20260720-04 | P1 | closed | Portfolio Risk labels a standalone FINRA short-interest ratio without distinguishing it from the much larger daily short-sale volume ratio, making a technically correct value look wrong and leaving IV30 without pricing context. | The panel names both measures precisely, shows Longbridge daily short-volume and Put/Call trends, preserves freshness-gated open short interest, and explains Cboe IV30 relative to Longbridge-price-derived HV20 and the implied 30-day range. | `codex/skill-v2-0.2.0` |
| DBG-20260720-05 | P1 | closed | Portfolio Risk renders stress scenarios through the generic exposure table, so the headers do not explain scenario loss, NAV impact, assumptions, or whether the result is a forecast. | Stress has a dedicated comparison view with scenario, estimated loss, NAV impact, calculation assumption, and an explicit non-forecast explanation. | `codex/skill-v2-0.2.0` |
| DBG-20260720-06 | P1 | closed | Fundamental volatility bars and metric cards rely on host theme variables without component fallbacks, so fills and borders can disappear in chat or standalone rendering. | Volatility bars, metric cards, and chart strokes retain visible contrast when host theme variables are absent, while preserving host colors when available. | `codex/skill-v2-0.2.0` |

## Review 2026-07-11

Review decision: `changes_requested`.

- Implementation baseline: `b752b78`; old UAT behavior reference:
  `dev@a19a5ed`. The review excluded concurrent Alpha, README, and planning
  changes.
- P1: `position_daily_report.py` accepts `not_confirmed` with no
  `--excluded-source`, then aggregates the two-broker fixture and labels it
  `已确认来源资产`. `DBG-20260711-04` remains open.
- P1: `price_action_rollforward.py` renders deep PA levels before enforcing the
  complete `ticker + trade_horizon + instrument` key; position reassessment can
  also trigger a board with an empty horizon. `DBG-20260711-05` remains open.
- P1: the weekend-first-start fixture promises a reduced-scope research summary
  instead of containing one, and omits the action that follows confirmation.
  `DBG-20260711-06` remains open.
- P2: runtime-health tests do not cover `startup_status=ready/uninitialized` or
  reconciliation `confirmed/unavailable`. `DBG-20260711-01` remains open until
  branch coverage and fresh-chat evidence exist.
- `DBG-20260711-02` is locally verified. `DBG-20260711-03` remains open pending
  fresh-chat visual evidence. No item is `closed` until accepted changes are
  re-pinned into the UAT worktree and the relevant fresh-chat checks pass.

### Follow-up Review 2026-07-11

Review decision: `changes_requested` after the first correction round.

- Closed from the prior review: the weekend fixture now contains a concrete
  deterministic reduced-scope summary and post-confirmation action; runtime
  tests now cover startup `ready/uninitialized` and reconciliation
  `confirmed/unavailable`.
- P1: `daily-ops-orchestrator.md` does not require the first-start broker setup
  interview when the default broker state is `needs_review`. `DBG-20260711-06`
  remains open.
- P1: malformed exclusion metadata such as
  `IBKR:partial_data(NAV-only` is accepted because the parser discards the
  unmatched annotation. `DBG-20260711-04` remains open.
- P1: `price_action_rollforward.py` loads/parses OHLCV before checking the
  complete setup key, so malformed input raises before watch-only guidance can
  be returned. `DBG-20260711-05` remains open.
- Parent verification reran `bash scripts/verify-plugin.sh` and
  `bash scripts/verify-mvp.sh`; both exited 0. These findings are semantic gaps
  not covered by the current green suite.

### Second Correction Review 2026-07-11

Review decision: `changes_requested`.

- Closed from the preceding review: every first start now includes the
  `needs_review` broker setup interview; unbalanced exclusion annotations are
  rejected; the setup-key check now precedes OHLCV file parsing when a path is
  supplied.
- P1: exact exclusion grammar still strips leading/trailing whitespace and
  accepts whitespace-only annotations such as `Longbridge:partial_data(   )`.
  `DBG-20260711-04` remains open.
- P1: `--ohlcv-json` is still an argparse-required option. When the setup key is
  incomplete and no OHLCV argument is supplied, argparse exits before the
  watch-only gate. `DBG-20260711-05` remains open.
- P2: later-turn `needs_review` behavior is inconsistent: the router requests a
  verification/retry without repeating authorization setup, while the template
  and reference re-enter broker setup. `DBG-20260711-06` remains open until one
  canonical behavior is selected and tested.
- Parent verification again reran `bash scripts/verify-plugin.sh` and
  `bash scripts/verify-mvp.sh`; both exited 0. Sol reproduced both P1 paths.

### Third Correction Review 2026-07-11

Review decision: `changes_requested`.

- Closed from the preceding review: exact exclusion grammar now rejects raw
  surrounding whitespace and whitespace-only annotations; incomplete setup
  keys can return watch-only without `--ohlcv-json`; later-turn
  `needs_review` no longer repeats broker authorization setup.
- P1: `position_daily_report.py` still accepts a two-broker snapshot with
  `portfolio_reconciliation=unavailable`, exits 0, and renders a combined
  `总资产`. Sol reproduced the current fixture total of `$85,060`.
  `DBG-20260711-04` remains open until this path fails closed and has a
  regression test.
- P2: the Daily Ops template labels `partial / uninitialized` as formal-runtime
  states even though they are `startup_status` values. `DBG-20260711-01`
  remains open for a bounded naming/contract correction and fresh UAT.
- P2: the PA CLI help says `--ticker` defaults to the JSON symbol although the
  explicit setup-key gate intentionally requires ticker before reading JSON.
  `DBG-20260711-05` remains open until help and contract agree.
- P2: regression contracts do not cover malformed exclusion grammar in the
  `unavailable` mode or assert the first-start `needs_review` rule across the
  router, reference, and template. `DBG-20260711-04` and
  `DBG-20260711-06` remain open.
- Two explicit Terra reviewers checked Standards and Spec; Sol inspected and
  reproduced the cited paths. `bash scripts/verify-plugin.sh` and
  `bash scripts/verify-mvp.sh` both exited 0, so the green suites are not yet
  sufficient release or UAT evidence.

### Fourth Correction Review 2026-07-11

Review decision: `changes_requested`.

- Closed from the preceding review: the explicit ticker help, first-start
  cross-document contract, template `startup_status` label, and the known
  IBKR/Longbridge `unavailable` aggregate path are corrected.
- P1: the new `unavailable` guard counts only IBKR and Longbridge. A snapshot
  containing IBKR plus a manual or future third-party broker label can still
  render a combined total. `DBG-20260711-04` remains open until every distinct
  non-empty broker label participates in the fail-closed check and the test
  matrix includes a manual-source case.
- P1: both weekend fixtures and their verifier still encode
  `formal runtime=partial`. In this fixture the runtime directory exists, so
  the canonical pair is `formal runtime=available` and
  `startup_status=partial`. `DBG-20260711-01` remains open until fixture and
  contract agree.
- The two weekend fixtures are currently untracked and must be included in the
  eventual controlled integration; this is an integration requirement, not a
  request for the debug worker to commit.
- The PA Scenario Board write path remains in scope under
  `DBG-20260711-03`; a reviewer suggestion to remove it as scope creep was not
  accepted.
- Two explicit Terra reviewers checked Standards and Spec. Sol reran
  `verify-plugin`, `verify-mvp`, compileall, and `git diff --check`; all passed,
  but the two semantic P1 findings still block local review acceptance and UAT.

### Final Local Review 2026-07-11

Review decision: `pass` for local implementation; formal UAT remains pending.

- The broker-agnostic `unavailable` guard now counts every distinct non-empty
  normalized broker label. Sol verified that IBKR plus ManualBroker fails
  closed and a single arbitrary broker remains renderable.
- Weekend input, expected output, and contract now use
  `formal runtime=available` with `startup_status=partial`; the verifier rejects
  the obsolete `formal runtime=partial` forms.
- The previously accepted exclusion grammar, setup-key/OHLCV ordering,
  first-start/later-turn broker routing, explicit ticker help, and PA visual
  behavior remain intact.
- Final Standards and Spec reviews both returned PASS. Sol reran
  `bash scripts/verify-plugin.sh`, `bash scripts/verify-mvp.sh`, compileall,
  `git diff --check`, and the cited broker/taxonomy boundary reproductions; all
  passed.
- All six debug items are `verified`, not `closed`. The reviewed scope and both
  weekend fixtures were integrated to `dev` in `2766c70`; closure still
  requires UAT workspace re-pin, plugin refresh, and the relevant fresh-chat
  acceptance prompts.

### Release Closure Review 2026-07-14

Review decision: `pass`; all six debug items are `closed`.

- Final behavior candidate: `19ca4ae`; detached UAT workspace:
  `/Users/archer/Documents/交易想法-1-0-uat`; installed plugin:
  `0.1.0+codex.20260714041242`.
- Exact rolling-PA Prompt 5 passed in fresh session
  `019f5ca4-eec7-7661-96c9-91162d81460a` for the unresolved-key watch-only
  branch. A separate authorized synthetic-OHLCV positive case passed in
  `019f5ca9-27f0-78a3-97db-e370344e92ff` with a visible PA Scenario Board,
  timeframe-owned levels, proportional actions, and no broker read or write.
- Exact Prompt 7 initially failed because the response omitted explicit
  `runtime_origin` / `startup_status` and the optional dry-run/initialization
  choice. Later deterministic checks also produced false confidence because
  the exact guard existed only in the router while the model directly activated
  `weekly-trading-plan`, and because two proposed command paths were not valid
  from the actual repo cwd.
- The final Prompt 7 run, session
  `019f5ed4-9994-7832-bcef-82f6681a34fd`, executed the repo-root runtime-health
  command successfully on its first attempt. It reported
  `runtime_origin=environment`, `formal runtime=missing`,
  `startup_status=uninitialized`, and `current_mode=dry-run`; then gave a
  public-source summary before requesting broker read-only preference, the full
  setup key, and dry-run or initialization choice with separate write
  authorization.
- The final UAT runtime path remained absent. No private runtime content,
  broker/account data, credentials, setup instruction, order action, or runtime
  write entered the repository or the acceptance response.
- Standards and Spec were reviewed independently after each accepted correction;
  Sol reran the cited focused checks and retained fresh-chat UAT as a separate
  release gate rather than treating fixture output as model evidence.

## Weekly Debug Review

At the weekly planning review, close verified items, update blocked/deferred
items with their next evidence, and evaluate whether the open board meets a
technical-debt trigger. The review must not relabel an unresolved symptom as an
architecture problem without diagnosis evidence.
