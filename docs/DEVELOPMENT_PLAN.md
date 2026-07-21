# Development Plan

This document is the public source of truth for Dailytrades feature,
integration, and approved architecture-optimization planning, daily task
selection, and progress. It is used by the weekday development brief and
end-of-day progress review automations.

Do not include private trade records, credentials, account details, unpublished research excerpts, or internal agent prompts. Keep this focused on project execution.

## Plan Boundaries

- Use this document for new product capability, integration work, and an
  architecture-optimization task that has met a technical-debt trigger.
- Use `docs/DEBUG_PLAN.md` for reproducible defects, regressions, acceptance
  failures, their evidence, and closure criteria.
- Use `docs/TECHNICAL_DEBT.md` for accepted or evidence-backed systemic cost,
  scoring, and architecture-optimization triggers.
- Do not convert a debug symptom into a feature task or an architecture rewrite
  before diagnosis establishes the appropriate scope.

## Current Development Phase

Phase: local trading research workflow MVP.

Goal: make the plugin usable for the core trading research loop before adding heavier external integrations: maintain an overwriteable Active Market Plan, append update notes, scan setup-level plans, read broker facts live when authorized, generate position daily reports, capture review context, and compute risk/statistics snapshots.

## Planning North Star

Daily development planning should prioritize product capability, not process work.

The current product sequence is:

1. AI-native synthesis contract: agent reads broadly and returns concise decision-useful notes, not raw research dumps;
2. accepted plugin design contract: natural-language task UX, router contract, runtime write boundary, broker source configuration, KVN snapshot boundary, and chart artifact boundary;
3. README and plugin docs aligned to natural-language task UX instead of user-facing focused-skill menus;
4. router intent fixtures and a router contract verifier;
5. runtime health contract and script for available/missing/stale/unauthorized state;
6. Active Market Plan schema, trading profile, update trail, and local report/review artifacts;
7. KVN model planning: define the future model module boundary, output contract, factor groups, universe rules, validation plan, and daily-job handoff without implementing the model inside this plugin;
8. KVN momentum leaderboard: import/read upstream or user-provided snapshots into SQLite, while the workflow displays Top10 and ticker lookups;
9. trade plan preparation: macro, financial conditions, policy/event risk, KVN snapshot, industry strength, and company thesis checks produce input reads and a Cross-Section Candidate Pool before setup rows are created;
10. research report intake: `research-report-intake` finds public/authorized reports, digests user-provided PDFs/links/text, creates a claim ledger, and maps verified report impact into Trade Plan Preparation;
11. fixture data covering KVN leaderboard snapshots, `market-plan.md`, private-style `trading-profile.md` fixture, append-only update notes, event previews, Trade Plan Preparation, setup pool, broker-live runtime views, position daily report output, and two-stage review context;
12. Daily Ops Orchestrator: active process guidance backed by `ops-state.md`, runtime health, Active Market Plan, Trading Profile, and `ticker + trade_horizon + instrument` confirmations;
13. premarket/intraday market parsing, level updates, and dynamic tracking against the Active Market Plan;
14. setup-scoped intraday scan;
15. broker-live position daily report automation and visualization snapshots;
16. post-order review to capture user context from read-only broker facts;
17. post-exit review to capture results, lessons, and optional statistics snapshots;
18. broker-agnostic portfolio reconciliation and risk view;
19. basic stats and system review;
20. automation setup checklist: confirm the Daily Ops thread, timezone, cadence, `runtime_dir`, allowed sources, runtime write policy, read-only broker permissions, and paywall boundaries through `automation-setup-checklist.md`;
21. user-confirmed Active Market Plan automations;
22. Source Routing Boundary: scope broker/account facts, market data, Longbridge macrodata, official policy facts, news, and research by source purpose so selecting Longbridge for one purpose does not become the default source for news;
23. scheduled macro/industry/news research monitor: after a weekly plan defines P0/P1 focus variables, run user-confirmed recurring searches over public/authorized sources and return only decision-useful deltas, research leads, verification queue, and Active Market Plan impact;
24. Content & Visualization Artifact System MVP: display-first visual artifacts for price action and macro/regime context, with optional durable saves only after confirmation;
25. persistent Macro Regime workspace: keep one stable private entry point for the current weekly panel, update it as events resolve, and retain immutable snapshots for later review;
26. OHLCV-backed chart artifacts;
27. option-flow anomaly research.

Development workflow, TDD, CI, worktree policy, and Claude/Codex handoff rules are support rails. They should be mentioned when relevant, but should not become the recommended main task unless they are directly blocking a product capability.

## Daily Development Loop

Weekday morning brief:

1. Inspect `docs/DEVELOPMENT_PLAN.md`, `docs/DEBUG_PLAN.md`,
   `docs/TECHNICAL_DEBT.md`, `docs/ROADMAP.md`, `docs/PROJECT_LOG.md`,
   `CONTEXT.md`, and current git status.
2. Report current development tasks with priority.
3. Recommend one product-capability main task for today.
4. Check whether an active P0/P1 debug item or a technical-debt architecture
   trigger changes the task order. A P0 supersedes feature work; a triggered
   architecture task is planned before further feature work in that subsystem.
5. Ask the user how to arrange the day:
   - available time;
   - chosen main task;
   - optional secondary task;
   - definition of done;
   - expected verification;
   - whether Claude Code should be assigned work;
   - whether progress should update this document, public roadmap/log, or both.

End-of-day progress review:

1. Ask what was planned, completed, verified, committed, pushed, blocked, or deferred.
2. Update the appropriate development, debug, and technical-debt records after
   confirmation.
3. Update `docs/PROJECT_LOG.md` only when the change affects public project
   trajectory.
4. Do not invent progress.

## Priority Rules

Use these priority levels:

- `P0`: needed to make the plugin workflow coherent, safe, or usable.
- `P1`: needed for the local MVP workflow.
- `P2`: needed for analysis depth or automation, but not a blocker for local MVP.
- `P3`: later optimization or expansion.

Use these statuses:

- `planned`
- `ready`
- `in_progress`
- `blocked`
- `review`
- `done`
- `deferred`

## Active Task Board

| Priority | Status | Task | Why It Matters | Next Action |
| --- | --- | --- | --- | --- |
| P0 | done | Deepen the four 0.3.0 architecture modules | Centralizes Broker-Live product knowledge, isolates purpose-specific chat visuals, gives Private Runtime one layout owner, and narrows the Artifact Packet facade without redesigning accepted outputs. | Focused module checks, the 0.3.0 Skill gate, and final Standards/Spec review pass. Remote `dev` integration remains user-approved only. |
| P0 | done | Refactor Trading Research System around one stable delivery contract (#72) | Replaces prompt-heavy behavior ownership with `Validated ResearchResult -> DeliveryPacket`, preserves purpose-specific inline visuals, and removes obsolete code, caches, database compatibility paths, fixtures, and redundant prose tests for version 0.2.0. | User accepted the frozen output structures and authorized integration to remote `dev` on 2026-07-20. Minimal release gates, isolated install, and final Standards/Spec review passed; public `master` cutover remains separate. |
| P2 | done | Accepted inline Panel PNG export | Opt-in only: exports the full accepted chat-inline HTML fragment as an on-demand PNG by measuring rendered content height; no automatic save, static frontend, or hosting. | Run only after explicit user selection. Keep private exports local; a separately requested README example may use reviewed public-market data but must contain no broker, private runtime, account, or private portfolio information. |
| P1 | done | Re-scope retained read-only commands | Prevents supported runtime, broker, macro, PA, and Alpha adapters from becoming unreachable leftovers. | Progressive references now name the retained runtime, broker, macro, OHLCV, and Alpha helpers; future additions require an active caller or compatibility obligation. |
| P1 | done | Redesign Portfolio Risk chat-inline panel | The old generic bar shell hid the relationship between capital, look-through concentration, product leverage, source coverage, exclusions, scenario loss, and underlying fundamentals. | Structure accepted and frozen by the user on 2026-07-20. Preserve the summary, primary-risk line, ordered views, look-through fundamentals, dedicated stress meaning, and source/exclusion disclosures defined in `references/portfolio-research.md`; structural changes require renewed acceptance. |
| P1 | ready | Add persistent weekly Macro Regime workspace (#73) | Makes the weekly macro panel easy to find again, refresh after each important event, and compare with the pre-event view instead of leaving the useful interactive artifact inside chat or a disposable temp directory. | Implement issue #73 through one stable private `latest` entry point, canonical immutable snapshots, event lifecycle and posterior comparison, without a second renderer, public exposure, or broker reads for macro-only updates. |
| P1 | completed | Add the default weekly research cadence | Daily Ops lacked a compact weekday priority, so fresh sessions could start with the wrong scope. | Monday builds the market framework and weekly watchlist; Tuesday-Friday update information, ideas, and plans; Saturday reviews markets and trades and prepares next week's watchlist. The cadence remains overridable by the user's current request. |
| P1 | completed | Establish Bayesian decision-support philosophy | The system should help the user update beliefs and choose risk-bounded actions, not imply that research can predict the next market move. | Treat thesis and regime as priors, separate observations from interpretation, express posterior confidence and conditional scenarios, and name the next evidence that would change the decision. Do not force numerical probabilities without calibration. |
| P2 | deferred | Public visual cutover | Keeps accepted chat-inline artifacts separate from the paused public Board/gallery release. | Proceed only after explicit 0.2.0 release-candidate approval. |
| P2 | planned | Research option-flow data vendor | Needed before implementing abnormal options signal analysis. | Define minimum anomaly schema and candidate vendor requirements. |

## Historical 0.1.x Architecture Records

The sections below are preserved as implementation history. Their commands,
versions, fixtures, and compatibility modules are not current 0.2.0 release
instructions. Use the active task table, ADR 0009, `docs/ROADMAP.md`, and
`docs/MVP_RUNBOOK.md` for current work.

### Architecture Optimization: High-Risk Behavior Contract Matrices

Status: complete on `codex/behavior-contract-matrix` from `dev@7ab4ab0`.

Trigger and target invariant:

- `TD-20260711-03` satisfies Architecture Optimization Trigger 3 after the same
  shallow behavior-contract cause produced repeated corrective patches while
  aggregate suites remained green;
- one repo-level deep test Module must own common scenario execution and
  observable assertions for the affected workflows;
- the Module is development harness only, tests the canonical
  `skills/trading-research-system/` behavior source, and is not distributed in
  the public Agent Skill;
- migrated behavior must be tested through existing CLI and document surfaces;
  no public Trading Research System behavior changes are in scope.

Approved slices:

1. `portfolio_reconciliation` status by broker-source composition;
2. `startup_status` by router, reference, template, fixture, and direct
   activation surface;
3. complete setup key by OHLCV input, validation ordering, and forbidden side
   effects.

The shared Interface is limited to command, cwd, temporary filesystem, exit
code, stdout/stderr, forbidden text, file creation/change, and validation
precedence. Workflow-specific semantic assertions remain with their workflow.
Each case has a stable ID; behavior mismatches aggregate within a scenario
family, while harness corruption fails immediately. Migration is
replace-not-layer: delete superseded bespoke setup and assertions rather than
running old and new paths together.

Acceptance:

- all three slices use the shared Interface and preserve workflow-specific
  behavior;
- focused Matrix and workflow selftests pass;
- `bash scripts/verify-plugin-compile.sh`, `bash scripts/verify-plugin.sh`, and
  `bash scripts/verify-mvp.sh` pass;
- canonical Skill and generated wrapper remain drift-free;
- `TD-20260711-03` is removed only after formal review confirms the exit
  criteria; no ADR is required unless the public contract changes.

Completion evidence:

- the shared harness and three focused family modules replace the migrated
  bespoke reconciliation and setup-key subprocess cases;
- startup surface cases bind each surface contract to a concrete
  ready/partial/uninitialized fixture, and all harness inputs are preflighted
  before any case executes;
- `bash scripts/verify-plugin-compile.sh`, `bash scripts/verify-plugin.sh`, and
  `bash scripts/verify-mvp.sh` pass after the final review fixes;
- final Standards and Spec reviews report no findings.

### Conditional Architecture Optimization: Artifact Packet Internal Board Seam

Status: complete after post-Macro deletion-test revalidation on
`codex/behavior-contract-matrix`. The integrated `dev@7ab4ab0` implementation
still mixed two payload policies and renderers into the shared packet core, so
the approved private Board seam remained justified.

Proceed only when the integrated baseline still shows all of the following:

- Instrument and Macro payload policy is coupled inside the shared Artifact
  Packet implementation;
- shared identity, privacy, hash, diagnostic, size, and immutable-write tests
  are duplicated across Board paths;
- deleting a private Board seam would spread that complexity back across both
  Board implementations.

If confirmed, preserve the Artifact Packet external Interface, CLI, stable
error codes, canonical JSON/HTML/manifest bytes, and ADR 0008. Keep shared
invariants in a deep core; use an explicit static internal registry for the two
known Board adapters; keep payload schema, evidence/freshness policy, and
renderer selection inside each adapter. Modify only canonical
`skills/trading-research-system/` behavior, generate Native Plugin wrappers via
`scripts/sync_native_plugin.py`, and replace duplicated shared tests with one
core conformance matrix plus Board-specific semantic tests.

Completion evidence:

- `artifact_packet.py` is now the stable public facade, while
  `artifact_packet_core.py` owns shared packet validation, canonical JSON,
  privacy, diagnostics, size limits, HTML safety, manifests, and immutable
  writes; neither contains Instrument or Macro payload/renderer policy;
- `artifact_packet_instrument_adapter.py` and
  `artifact_packet_macro_adapter.py` own their Board-specific schema,
  evidence/freshness rules, and renderer selection;
- `artifact_packet_board_adapters.py` is an explicit static registry keyed by
  `(board_id, payload major)` with no dynamic discovery;
- the shared conformance test pins exact JSON/HTML/manifest SHA-256 bytes for
  both complete public fixtures, while existing Instrument and Macro tests
  retain Board-specific semantic coverage;
- canonical Skill changes were projected only through
  `scripts/sync_native_plugin.py`; compile, plugin, MVP, Instrument browser
  (12 checks), and Macro browser (15 checks) gates pass;
- the external Artifact Packet contract and ADR 0008 are unchanged.

## Canonical Instrument Research Board

Status: implementation complete and under review in PR #66.

Bounded scope:

- four views: Overview, Price & Setup, Industry & Peers, and Catalysts & Flows;
- industry, fundamentals, catalysts, and market/instrument data remain required
  evidence gates, while flows remain supporting-only;
- complete, partial, stale, and source_error snapshots are synthetic,
  deterministic, privacy-safe, and rendered through the canonical artifact
  packet seam;
- Price Action owns timing and setup evidence only and cannot make an incomplete
  cross-module research gate ready;
- Issue #38 annotation work, private runtime state, README Gallery switching,
  and the public SVG cutover remain outside this ticket.

Local acceptance:

```bash
bash scripts/verify-plugin-compile.sh
bash scripts/verify-plugin.sh
```

Focused browser acceptance uses the repository-locked Playwright dependency,
a freshly generated synthetic HTML artifact, and a caller-supplied local Chrome
or Chromium executable. The exact command is maintained in
`skills/trading-research-system/references/artifact-packet-contract.md`.
Repository-wide mandatory browser, privacy, and distribution gating remains a
separate deliverable under Issue #58.

## Cross-device Git-backed Plugin Distribution

Status: local implementation complete; remote clean-install UAT pending after
the accepted change reaches `master`.

Scope for this tracer bullet:

- make `.agents/plugins/marketplace.json` the only repository distribution
  source for `trading-research-system`;
- keep `plugins/trading-research-system/.codex-plugin/plugin.json` as the single
  source of truth for the published version;
- reject marketplace source/name/display metadata drift, invalid manifest
  versions, nested marketplace copies, package paths outside the public
  allowlist, and structured README install-contract drift;
- document installation without implying that Codex account login synchronizes
  plugins, connector grants, credentials, or private runtime data.

Public/private product boundary:

- the public plugin may package only generic skills, references, scripts, blank
  templates, explicitly synthetic sanitized fixtures, and generic contracts;
- private user state includes stock pools/watchlists, `trading-profile.md`,
  Active Market Plans, setups, positions, executions, reviews, broker data,
  runtime files, account/connector authorization, personal risk parameters, and
  research history;
- marketplace add, plugin install, and upgrade must never copy, package, commit,
  restore, or imply synchronization of private user state;
- every user initializes a blank local runtime independently; the repository
  does not supply a personal profile, plan, default watchlist, or preferred
  ticker list;
- any future preference-sync capability is separate, private, explicitly
  opt-in, and outside this public plugin distribution task.

Local acceptance gate:

- `python3 scripts/verify_plugin_distribution_selftest.py` passes;
- `bash scripts/verify-plugin-compile.sh` compiles every plugin script while
  directing bytecode to `.scratch/plugin-compile-cache`; do not use bare
  `python3 -m compileall -q plugins/trading-research-system/scripts` as a gate,
  because bare `compileall` writes `__pycache__` into the public package;
- `bash scripts/verify-plugin.sh` and `bash scripts/verify-mvp.sh` pass;
- `git diff --check` passes;
- an isolated Codex home smoke resolves the root marketplace, lists version
  `0.1.1`, and installs the plugin into that temporary home without writing
  global Codex configuration;
- the distribution contract enforces top-level Python-only scripts,
  `SKILL.md`/Markdown-only skill trees, explicit fixture/template asset shapes,
  rejection of symlinks and generated/cache artifacts, header-only CSV runtime
  templates, and structured Markdown install/boundary sections.

Reproducible local marketplace resolution and install smoke:

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
ISOLATED_ROOT="$(mktemp -d /tmp/dailytrades-marketplace-review.XXXXXX)"
mkdir -p "$ISOLATED_ROOT/home" "$ISOLATED_ROOT/codex" \
  "$ISOLATED_ROOT/config" "$ISOLATED_ROOT/cache"
export HOME="$ISOLATED_ROOT/home"
export CODEX_HOME="$ISOLATED_ROOT/codex"
export XDG_CONFIG_HOME="$ISOLATED_ROOT/config"
export XDG_CACHE_HOME="$ISOLATED_ROOT/cache"
export PYTHONDONTWRITEBYTECODE=1
codex plugin marketplace add "$REPO_ROOT" --json
codex plugin marketplace list --json
codex plugin list --marketplace dailytrades --available --json
codex plugin add trading-research-system@dailytrades --json
codex plugin list --marketplace dailytrades --json
```

The 2026-07-14 review rerun resolved `dailytrades`, exposed
`trading-research-system` version `0.1.1` from the repository source, and
installed it under the temporary `CODEX_HOME`; the real home, global
marketplace, plugin cache, credentials, and private runtime were not used.
This is local-equivalent evidence only. It does not prove GitHub `master`
fetching, desktop Plugins behavior, process restart, or a fresh task loading
the installed version.

Coordinator follow-up after integration and publication:

1. On a clean device or isolated Codex home, add
   `Archerouyang/dailytrades@master` as a marketplace.
2. Install `trading-research-system` from Codex `/plugins` or desktop Plugins.
3. Open a new task and confirm the installed version and expected skills load.
4. Confirm no account-login step is presented as plugin, connector, credential,
   or private-runtime synchronization.

These remote GitHub and restart/new-task checks remain pending and must not be
marked passed until the coordinator runs them after integration to `master`.

## Today

Date: 2026-07-20

- Main task: implement the approved 0.3.0 architecture-deepening spec.
- Current stage: all four bounded workstreams are integrated; the minimal 0.3.0
  Skill gate and final Standards/Spec review pass.
- Next task: present the local candidate for user acceptance before any remote
  `dev` integration.
- Definition of done: all four modules meet the spec, accepted inline outputs
  remain stable, obsolete compatibility paths are removed, focused verification
  and final Standards/Spec review pass, and no public cutover occurs without
  explicit approval.

## Progress Log

### 2026-07-20

- Completed the approved 0.3.0 architecture-deepening spec: canonical
  Broker-Live product knowledge, four purpose-specific chat visual adapters,
  one Private Runtime owner, and a narrowed Artifact Packet facade.
- Initial review found and closed signed-exposure defects for explicit zero,
  short leveraged ETFs, and short inverse ETFs. Fragile full-inline SHA checks
  were removed in favor of semantic structure, interaction, safety, and size
  checks consistent with manual visual acceptance.
- The focused module tests, portable Skill gate, generated-state scan,
  `git diff --check`, and final Standards/Spec review pass. Nothing was pushed.
- User removed Native Plugin distribution from the current product plan. The
  repository now ships only `skills/trading-research-system/`; wrapper copies,
  repository marketplaces, sync code, and wrapper-only validation are deleted.
- User accepted the 0.2.0 frozen Macro, Price Action, and Portfolio panel
  structures and authorized integration to remote `dev`.
- README positioning now states the Bayesian decision-support model explicitly:
  priors are updated with observations, scenarios stay conditional, and the
  system identifies the next evidence that would change the current action.
- The user-selected Macro and NVDA Price Action PNG exports are embedded as
  reviewed public-market examples; they contain no broker, runtime, account,
  or private portfolio data.
- The minimal Skill gate, isolated portable install,
  cleanup scan, ResearchResult regression suite, and final Standards/Spec
  review passed for the 0.2.0 candidate.

### 2026-07-19

- User acceptance froze the 0.2.0 PA inline template after the NVDA real-chat
  prototype. The accepted structure is decision hierarchy -> continuous metric
  strip -> Chinese trigger/path/action scenarios -> dominant PA chart ->
  current-price-anchored level ladder -> proportional staged plan -> company and
  direct supply-chain events -> compact data-method disclosure. Macro liquidity
  events remain owned by the Macro panel. Structural or interaction changes
  require renewed real-chat acceptance.
- User acceptance froze the working Macro research and Longbridge CLI workflow
  for 0.2.0. The release contract is now capability check -> `macrodata`
  discovery/history -> supported Longbridge market history -> purpose-specific
  Treasury/Cboe/exact-DXY completion -> one-month session alignment ->
  `ResearchResult -> DeliveryPacket` -> compact native inline. Changes to this
  sequence or its source/safety boundaries require renewed user acceptance.
- Manual acceptance feedback for #72 requires the native macro inline fragment
  to localize visible transmission states and scenario descriptions in Chinese.
  The stable macro observation set now includes 2Y/10Y/30Y rates, CPI and PPI,
  NDX/RUT, and VXN, while retaining decision-relevant USD, credit, commodity,
  and liquidity context. Acceptance remains user-owned in the real chat surface.
- Follow-up acceptance rejected cross-unit single-value bars. Macro inline now
  needs time-series direction for NDX/RUT, VXN, DXY, and rates, plus an explicit
  causal chain from current state through next-week event outcomes to scenario
  and plan consequences.

### 2026-07-14

- Added the local Git-backed distribution contract for the repository-root
  marketplace, manifest-owned versioning, README installation flow, and
  nested-marketplace drift prevention. Remote clean-install UAT remains a
  coordinator gate after the change is integrated and published to `master`.
- Hardened the review fix with a strict recursive public package allowlist,
  structured Markdown contracts, first-screen install and upgrade guidance,
  two Mermaid diagrams, and an isolated temporary-`CODEX_HOME` CLI install.
  GitHub/ref resolution and restart/new-task UAT remain coordinator-owned.
- Replaced the polluting bare-`compileall` acceptance step with
  `scripts/verify-plugin-compile.sh`, which sends bytecode to the ignored
  `.scratch/plugin-compile-cache` before the distribution verifier confirms the
  public package remains clean.
- Closed all six 2026-07-11 behavior debug items after dual-axis review and
  targeted fresh-chat UAT.
- Verified both Prompt 5 branches: unresolved setup keys stay watch-only, while
  an authorized synthetic-OHLCV positive case renders the visible PA Scenario
  Board without broker reads or writes.
- Diagnosed Prompt 7 beyond fixture checks: the exact request directly activated
  `weekly-trading-plan`, bypassing a router-only guard. Added direct-entry
  assembly coverage and a repo-cwd subprocess check for the status command.
- Final Prompt 7 session `019f5ed4-9994-7832-bcef-82f6681a34fd` passed with an
  absent environment-selected runtime and no private read or write.
- Recorded the remaining contract-depth and behavior-ownership costs in
  `docs/TECHNICAL_DEBT.md`; broad feature work in this subsystem follows the
  bounded architecture-optimization task.

### 2026-07-11

- Integrated the final dual-axis-reviewed non-quant behavior correction to
  `dev` as `2766c70`, including both weekend fixtures.
- Integrated the UAT, planning-record, and Sol Ultra review rules as `7d91010`.
- Resolved two runtime-health conflicts by preserving the non-quant `dev`
  surface while keeping startup checks separate from broker capability checks.
- Verified the integrated worktree with the plugin validator, fixture-backed
  MVP smoke, compileall, and diff checks. Formal UAT remains pending.

### 2026-07-09

- Completed: wrote the user-confirmed monitor-only setup rows to the private
  2026-07-09 runtime with `prepare_setup_rows.py`. The runtime now has 5
  scanner-ready rows: DRAM/SOXX/TSMX/GLW as `needs_review` and MAG7 basket as
  `candidate`.
- Completed: reran fresh-chat acceptance prompt 3 in thread
  `019f4705-cc23-72a0-94e0-3adec7a42df5` against installed plugin
  `0.1.0+codex.20260709083506`. Result: `PASS`; it read plan/update trail,
  macro-panel, and watchlist state, ran `intraday_scan.py` read-only, reported
  no `active`, `approaching`, or `triggered` setups, and did not call brokers or
  write repo/runtime files.
- Completed: local 1.0 fresh-chat acceptance is now 6 PASS, 0 PARTIAL, 0 FAIL.
  Final `dev` gates passed; promotion from `dev` to `master` remains a
  separate user-confirmed step.
- Completed: added and ran the private 2026-07-09 daily runtime package
  preparation flow. Today's runtime now has header-only `trade-plans.csv`,
  `intraday-watchlist.csv`, `portfolio_snapshot.csv`, `ops-state.md`, and update
  containers outside the public repo.
- Completed: polished the empty intraday scan output so a header-only watchlist
  reports `没有已准备的 setup 行` and does not claim `approaching` or `triggered`
  signals.
- Completed: refreshed the plugin cachebuster to
  `0.1.0+codex.20260709022827`, pushed `dev`, synced the personal plugin source,
  and reinstalled `trading-research-system@personal`.
- Completed: added the IBKR connector adapter. `ibkr_connector_adapter.py` maps
  saved read-only IBKR positions/balances JSON into standard
  `portfolio_snapshot.csv`, with synthetic fixtures and contract checks.
- Completed: forward-smoked the IBKR read-only connector path privately:
  positions/balances/allocation tools were read-only callable, saved JSON was
  normalized through `ibkr_connector_adapter.py`, and `position_daily_report.py`
  rendered from the standard view. Temporary private files were deleted.
- Completed: reran fresh-chat acceptance prompt 3. Result remains `PARTIAL`
  because today's plan/watchlist files are header-only, `macro-panel.json` is
  missing, and broker/macrodata sources were unauthorized in that fresh chat.
- Completed: fixed packaged contract path resolution so installed plugin
  verifiers can use the project checkout from cwd for repo docs while keeping
  plugin files rooted in the installed cache.
- Completed: added Macro panel runtime preparation. `prepare_macro_panel.py`
  writes the standard dated `macro-panel.json` from saved macrodata JSON,
  preserves existing panels by default, and gives missing-input guidance instead
  of inventing macro values.
- Completed: tightened macro panel source labeling. Official fallback JSON now
  uses `--source-capability official_source_fallback`, preserving item-level
  sources instead of being mislabeled as Longbridge macrodata.
- Completed: added `official_source_fallback` to runtime health source
  capabilities and forward-smoked today's private runtime macro panel from
  Treasury/FRED fallback data. Runtime health now reports `macro_panel`
  available and `official_source_fallback=available`.
- Completed: made Gold an optional macro confirmation input. Missing Gold is
  disclosed via `missing_optional_indicators`, but does not degrade the panel
  when all required posture inputs are present.
- Completed: refreshed and reinstalled the personal plugin to
  `0.1.0+codex.20260709062046`, regenerated today's private macro panel, and
  reran a fresh-chat #1/#3 combined acceptance. The rerun passed behavior
  acceptance: macro panel is available/non-degraded via official fallback, and
  header-only setup CSVs correctly produce no approaching/triggered claims.
- Completed: added Setup row preparation. `prepare_setup_rows.py` consumes
  user-confirmed setup JSON and fills scanner-ready `trade-plans.csv` and
  `intraday-watchlist.csv`, while preserving populated files by default and
  refusing to parse free-form trade ideas.
- Completed: refreshed the plugin cachebuster to
  `0.1.0+codex.20260709052038`, synced the personal plugin source, reinstalled
  `trading-research-system@personal`, and verified the installed-cache
  `prepare_macro_panel` contract.
- Verification: daily runtime package selftest/contract, IBKR connector adapter
  selftest/contract, `scripts/verify-plugin.sh`, `scripts/verify-mvp.sh`,
  compileall, `git diff --check`, installed-cache 1.0/IBKR contract checks, and
  macro-panel preparation selftest/contract, runtime-health selftest/contract,
  and official fallback runtime smoke pass.
- Next: forward-test setup-row population against the private 2026-07-09
  runtime after the user confirms today's setup list, then continue with live
  Longbridge macrodata visibility, Longbridge read-only forward test, PA
  market-data inputs, and snapshot repair.

### 2026-07-08

- Completed: merged the 1.0 Acceptance Plan and Visual Trigger Policy into
  `dev`, refreshed the installed plugin cache, and reran the local gates.
- Completed: ran the six fresh-chat acceptance prompts. Results: Daily Ops
  startup PASS, weekly plan PASS, daily/intraday setup scan PARTIAL, position
  daily PASS, rolling PA PARTIAL, two-stage trade review PASS.
- Recorded: added `docs/1.0_ACCEPTANCE_RESULTS.md` with non-private evidence
  and P0 gaps for daily runtime package creation, macro-panel generation,
  authorized read-only broker adapters, PA market-data inputs, and snapshot
  repair.
- Next: choose the first blocker to close. The most workflow-critical slice is
  daily runtime package creation, because it is what turns the intraday setup
  scan from mirror-only into a formal scan.

### 2026-07-07

- Completed: hardened the 1.0 RC release surface. External quantitative momentum modules are now hidden from the default README, router, focused skill list, and daily tracking template. The internal compatibility scripts and planning docs remain for user-provided snapshots, but the plugin no longer exposes model construction or a standalone leaderboard workflow by default.
- Completed: added the Price Action rollforward contract. PA updates must now compare with prior analysis, state `主分析时间框架` and `辅助时间框架`, bind levels to support/resistance and timeframe, include cost/buy-record context, use proportional sizing instead of exact share counts by default, and map levels to the week's macro/news/events.
- Verification: release surface contract, PA rollforward contract, core contract suite, plugin verify, MVP smoke, compileall, and `git diff --check` pass locally.
- Completed: implemented the Content & Visualization Artifact System MVP. This adds display-first visual artifacts for price action and macro/regime context, with transient chat SVG output by default and optional durable manifest save only after explicit confirmation.
- Scope: `chart_artifact.py`, `macro_regime_artifact.py`, shared visual helpers, fixture data, output template rules, ADR, roadmap, project log, and contract-suite checks.
- Next: review the PR, then decide whether the next visualization slice should be richer price charts, confirmed runtime save integration, or content-output polishing.
- Completed: hardened fresh-chat Daily Ops startup health after the `交易研究2` forward test. `runtime_health.py` now emits `current_mode` and per-source `broker_source_health`; Daily Ops startup output must include `运行状态检查`, `券商来源健康`, `当前模式`, formal `runtime_dir`, and the repo-fixture boundary before analysis.
- Verification: runtime health selftest, runtime health contract, and Daily Ops Orchestrator contract pass locally.
- Completed: added the Macro Data Source Contract. Daily, weekly, and macro-equity workflows now have to report `宏观数据来源状态` and `实际宏观指标读数`; Longbridge macrodata is the preferred S1 macro-values source, IBKR market data is limited to price/OHLCV transmission, and official source fallback covers S0 facts and fallback values.
- Verification: `verify_macro_data_source_contract.py` added to the core suite.
- Completed: defined the Longbridge Skill Adapter contract. Runtime health now reports `source_capability_health` so Daily Ops can distinguish Longbridge broker skill, Longbridge macrodata, IBKR connector, and manual snapshot readiness before analysis.
- Verification: `verify_longbridge_skill_adapter_contract.py` added to the core suite.

### 2026-07-06

- Completed: deepened the Contract Suite module. Added `contract_suite.py`, `verify_contract_suite.py`, `verify_contract_suite_selftest.py`, and `verify_contract_suite_contract.py`; migrated core verifier path resolution to `PluginPaths`; `scripts/verify-plugin.sh` now delegates core checks to `verify_contract_suite.py core`.
- Completed: deepened the Runtime State module. Added `runtime_state.py`, `verify_runtime_state_selftest.py`, and `verify_runtime_state_contract.py`; migrated bootstrap, daily initialization, runtime health, KVN default storage, review context, trade-record compatibility, legacy import, and append-review scripts to the shared runtime path/write seam.
- Completed: added Runtime bootstrap for private runtime initialization. `bootstrap_runtime.py` creates blank `market-plan.md`, `trading-profile.md`, `ops-state.md`, config, runtime directories, update note, and an optional dated daily folder; it supports `--dry-run`, `--overwrite`, and `--no-daily`.
- Completed: added Broker snapshot ingest. `broker_snapshot_ingest.py` maps user-approved read-only broker export CSVs from IBKR/Longbridge-style inputs into standard `portfolio_snapshot.csv` rows for position daily reports, without live broker reads or order actions.
- Completed: added Longbridge Terminal CLI adapter. `longbridge_cli_adapter.py` maps saved `longbridge portfolio --format json` output into the standard `portfolio_snapshot.csv` view, exposes `longbridge_terminal_cli` as a runtime health capability, and keeps live broker reads/order actions outside the adapter step.
- Completed: added the Fixture-backed local MVP smoke path. `scripts/verify-mvp.sh` runs `scripts/verify-plugin.sh`, fixture runtime health, KVN import/show/query/changes, intraday scan, position daily report, and the MVP smoke contract without live broker reads, real Codex automations, or live market data.
- Completed: added `docs/MVP_RUNBOOK.md` to define the Local MVP boundary, smoke output location, new-chat validation prompt, and next steps after MVP.
- Next: refresh the installed plugin cache, validate the smoke output, and open a PR for review.

### 2026-07-05

- Completed: defined the KVN Model module planning contract in `docs/KVN_MODEL_PLAN.md` and `docs/adr/0006-kvn-model-module-boundary.md`. The future model owns universe, data ingestion, factor computation, validation, versioning, and daily snapshots; the plugin only consumes standardized outputs.
- Completed: added the first `position_daily_report.py` slice. It renders a concise Chinese position daily report from the standard `portfolio_snapshot.csv` fixture, keeps broker reads out of the script, and locks output with `verify_position_daily_report_selftest.py`.
- Completed: added `automation-position-daily-report.md` and wired the automation contract to the standard runtime snapshot -> `position_daily_report.py` path. The prompt asks before runtime writes and forbids broker write actions.
- Completed: forward-tested `research-report-intake` with safe realistic fixtures: one user-provided AI infrastructure report artifact and one public-source discovery/access-boundary prompt. The contract now locks source priority, inaccessible S3 handling, Claim Ledger, Verification Queue, and Trade Plan Preparation impact without storing real paywalled report text.
- Completed: re-scoped trade review around a default review-context artifact path. Added `write_trade_review_context.py`, self-test, and contract verifier so post-order/post-exit reviews can append `reviews.md` without creating `trades.csv`.
- Completed: added Active Plan automation prompt templates for deep update, quick update, intraday trigger monitor, post-market review, and position daily report. Added `verify_active_plan_automation_contract.py`; actual Codex automations still require user-confirmed cadence and data-source permissions.
- Completed: added the first Plan-scoped intraday scan script. `intraday_scan.py` renders `intraday-watchlist.csv` into a priority-ordered Chinese setup status note, and `verify_intraday_scan_selftest.py` locks the fixture behavior.
- Completed: added scheduled macro/industry/news research monitor prompt and fixture coverage. The monitor starts from weekly P0/P1 focus variables such as Fed minutes, yields, TSMC monthly revenue, AI hardware news, and DRAM pricing; it searches public/authorized sources on a confirmed cadence, produces concise deltas and report leads, and feeds `Research Report Intake` / `Trade Plan Preparation` without becoming a full-plan rerun or automated trading signal.
- Completed: added the Automation setup checklist contract. `automation-setup-checklist.md` now defines the setup interview for Daily Ops thread, timezone, cadence, `runtime_dir`, allowed sources, runtime write policy, read-only broker access, and paywall boundaries before creating real Codex automations.
- Completed: added the Daily Ops Orchestrator contract. `daily-ops-orchestrator.md` and `ops-state.md` define proactive stage detection, next recommended action, missing confirmations, and ticker-level `ticker + trade_horizon + instrument` grouping before focused workflow routing.
- Completed: extended Trade Plan Preparation from five input reads to six by adding `KVN Momentum Leaderboard` as an imported snapshot input.
- Completed: updated weekly planning, macro/equity research, Active Market Plan, output templates, and market/weekly templates so KVN feeds the Cross-Section Candidate Pool but cannot become a buy list or direct setup.
- Completed: added `trade-plan-preparation-with-kvn-2026-06-24.md` fixture showing SNDK/CRDO/GLW/SOXX style KVN candidates, thesis/risk gates, and promotion requirements for `candidate setup`.
- Completed: added the focused `momentum-leaderboard` skill wrapper around `kvn_leaderboard.py` and updated the router to use it for KVN import/show/query/change tasks.
- Completed: added the Active Market Plan fixture package under `assets/fixtures/runtime/active-market-plan-2026-06-24/`, covering plan state, trading profile, update note, setup pool, intraday watchlist, broker-live fixture views, position daily report, review context, and expected intraday scan output.
- Completed: hardened daily tracking KVN source discipline after local validation showed a `KVN-like` rebuild risk. `daily-market-tracking` now must report missing/stale KVN and ask whether to import or continue without KVN; it must not rebuild or relabel public market data as KVN.
- Completed: tightened KVN leaderboard semantics. KVN rows are ticker-only, preserve script-computed order from the scheduled/upstream model output, and must not be re-ranked, re-scored, or replaced with sector/theme/narrative buckets by the agent.
- Next: define the position daily report contract/script or implement the first `intraday_scan.py` against the fixture package.

### 2026-07-04

- Completed: accepted the plugin design contract in `docs/PLUGIN_DESIGN.md`.
- Decisions: default UX is natural-language tasks; focused skills are internal/power-user tools; trading-judgment runtime writes are draft-only; trading-operation automations default to draft mode; broker facts are read live from authorized sources; derived broker summaries may be saved privately; v1 broker sources are Longbridge skill/plugin and IBKR connector; KVN model construction is outside plugin scope; chart artifacts are on-demand with opt-in auto-generation for high-priority setup/review contexts.
- Next: implement the development queue from the design: README UX alignment, router intent fixtures, router verifier, runtime health contract/script, then KVN snapshot import/storage.
- Completed: aligned root/plugin README around natural-language task prompts and moved focused skill names into advanced/internal wording.
- Completed: added router intent fixtures for weekly plan, premarket update, intraday setup scan, research report intake, post-order review, post-exit review, position daily report, and portfolio risk.
- Completed: added `verify_router_contract.py` as a local acceptance gate for router fixture shape, allowed workflows, required output labels, and AI-native prompt wording.
- Completed: added a private-safe runtime health contract and script that reports runtime availability, stale state, and broker authorization status without copying private runtime content into the public repo.
- Completed: added runtime health selftest and contract verifier coverage, and wired the router/automation docs to run the health check before runtime-dependent work.
- Completed: added `kvn_leaderboard.py` for importing externally generated KVN snapshots into SQLite, showing Top10, querying any ticker, and summarizing Top10 changes.
- Completed: added KVN fixture snapshots, expected Top10 output, selftest, contract verifier, and router fixture coverage for natural-language KVN lookup.
- Next: update Trade Plan Preparation fixtures so macro/financial/policy reads and imported KVN candidates can feed the Cross-Section Candidate Pool.

### 2026-07-03

- Planned: use `grill-with-docs` to re-evaluate plugin scope and development priorities against current docs.
- Decision: the record module is useful but hard to perfect upfront; near-term development should prioritize analysis, especially the KVN momentum leaderboard, macro/rates regime filtering, and industry/company research flow.
- Decision: objective broker facts should be read live from Longbridge/IBKR when authorized; Google Sheets and local `trades.csv` should not be treated as the main trade-record layer.
- Decision: add a scheduled position daily report capability that summarizes broker-live holdings, risk exposure, notable changes, and visualization-ready snapshots without placing or implying orders.
- Decision: `momentum-leaderboard` should be a focused skill backed by KVN snapshot import/storage in `{runtime_dir}/momentum/kvn.sqlite`, not a sub-section of `macro-equity-research`; the quantitative model itself stays outside plugin scope.
- Decision: default user-facing KVN output is Top10 with screenshot-like fields, while all liquid universe symbols remain queryable from local storage.
- Next: implement the `momentum-leaderboard` contract, fixture, verifier, and storage schema; then define the broker-live position daily report fixture and automation prompt.

### 2026-06-18

- Completed: added a shared `contract_verifier.py` module for product contract checks.
- Completed: converted weekly outlook, Trade Plan Preparation, and research report intake verifier scripts into thin adapters over the shared verifier.
- Completed: added exact CSV header validation for the research report log template.
- Completed: added `record_schemas.py` as the canonical local CSV schema registry and wired `init_daily.py` to it.
- Completed: added record template verification for headers and row widths, which caught and fixed a misaligned `trades.csv` sample row.
- Completed: added the Actual trade record module with `trade_records.py` and `update_trade_record.py` for post-order row creation and post-exit row completion.
- Completed: wired `$trade-review` documentation to use the update script after user confirmation.
- Completed: fixed legacy `active` Sheet import by adding an explicit `--allow-unknown-execution-fields` mode for older rows missing `quantity`, `fees`, or `risk_amount`.
- Completed: added `import_legacy_active_csv.py` to migrate legacy `active` tab CSV exports into canonical local `trades.csv` and append-only `reviews.md`.
- Verification: shared verifier self-test plus all existing contract checks pass locally.
- Next: import a broader legacy active CSV export into the private runtime, inspect the stats output, then use the same schema path for one-way Google Sheets sync.

### 2026-06-17

- Completed: defined the `research-report-intake` capability as the first-class path for report discovery and user-provided report digestion.
- Completed: added `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact` as the required shape before report views can affect macro/equity research or setup promotion.
- Verification: added and ran the report-intake contract verifier; kept weekly outlook and Trade Plan Preparation contract checks passing.
- Next: forward-test on a user-provided research report and a public-source discovery prompt, then add report-digestion fixtures.

### 2026-06-16

- Planned: prioritize Trade Plan Preparation over `intraday_scan.py`.
- Decision: v1 inputs are `Macro Regime`, `Financial Conditions`, `Policy/Event Risk`, `Industry/Sector Strength`, and `Company Thesis Check`.
- Decision: quantitative momentum candidate pool is a separate TODO and should not be treated as a v1 input until its data, factors, ranking, and validation are defined.
- Decision: Active Market Plan needs a `Trade Plan Preparation` section with `Input Reads` and `Cross-Section Candidate Pool` before setup rows are promoted.
- Decision: research reports need a dedicated `research-report-intake` path before macro/equity research consumes them. Report discovery is limited to public/authorized sources, user-provided reports are reduced to `Research Report Digest`, `Claim Ledger`, `Verification Queue`, and `Trade Plan Preparation Impact`, and paywall bypass remains out of scope.

### 2026-06-14

- Planned: create a dedicated development planning/progress document and align weekday automations to it.
- Completed: created `docs/DEVELOPMENT_PLAN.md`, registered it in `docs/ROADMAP.md`, and updated both weekday development automations to use it as the progress source of truth.
- Completed: added `docs/DEVELOPMENT.md` as the lightweight development workflow, TDD, CI, worktree, and Codex/Claude handoff standard. Clarified that live IBKR connector behavior is outside this repo's test scope.
- Verification: read both automation configs after update; confirmed they reference `docs/DEVELOPMENT_PLAN.md`; plugin validation passed after development workflow review.
- Blockers: none.
- Decision: confirmed the user's hard need is a weekly market review and next-week plan package, daily premarket/intraday tracking with level updates, opportunity discovery within the plan/watchlist, and two-stage trade review based on actual trade facts.
- Completed: added weekly review and daily market tracking templates to the plugin and aligned review references around post-order and post-exit stages.
- Completed: split the plugin into a lightweight `trading-research` router plus focused skills for weekly market review/planning, daily tracking, intraday scan, trade review, macro/equity research, portfolio risk, and trading stats.
- Decision: confirmed fixture data as the next product-capability implementation slice before `intraday_scan.py`.
- Decision: refined the workflow around one overwriteable Active Market Plan plus append-only update notes. Weekly and daily work are update depths, not separate workflows. Setup is the smallest planning unit, and broker sources are read-only adapters mapped into canonical daily CSV.
- Decision: added a trading profile layer for style and instrument preferences without storing account allocation in the public repo.
- Next: forward-test focused skill routing, then define the fixture package using `market-plan.md`, `trading-profile.md`, update notes, setup pool, and canonical broker CSV, implement `intraday_scan.py`, and connect post-order/post-exit review CSV writing.
- Completed: defined the basic plugin content plan across router/focused skills, shared references, templates, scripts, fixture package, priorities, and deferred scope.
- Completed: initialized the 2026-06-15 to 2026-06-19 Active Market Plan outlook and append-only update note using current event/calendar and market sources.
- Decision: clarified the plugin is AI-native: agents should read, verify, compare, and synthesize broadly, but return concise decision notes rather than long source dumps.
- Next: convert the new market plan into fixture package files for daily records, expected intraday scan output, and review-writing tests.

## Automation Contract

Automations should use this document as the development progress source of truth:

- `dailytrades-weekday-development-brief`: weekday morning brief and daily task-planning interaction.
- `dailytrades-end-of-day-progress-review`: weekday end-of-day progress review and update prompt.

The morning automation should recommend one main product-capability task for the day, ask for available time, chosen task, optional secondary task, definition of done, expected verification, whether Claude Code should be assigned work, and which docs should be updated after completion.

Automation outputs should be concise Chinese Markdown notes. They should ask before editing files and should not touch broker write actions, private trade data, or live external services.

Trading-operation reminders and assistant prompts are separate from development automations. They belong in the fixed `交易研究 Daily Ops` chat and should use `runtime_dir` as the private working-memory root. Default `runtime_dir` is `~/Documents/dailytrades-runtime`, with `TRADING_RESEARCH_RUNTIME_DIR` or script-level `--runtime-dir` overrides.

Trading prompts should read `{runtime_dir}/market-plan.md` as current state, `{runtime_dir}/trading-profile.md` as private trading style input when available, and `{runtime_dir}/updates/YYYY-MM-DD.md` as the append-only trail. They may prompt for deep updates, quick updates, intraday trigger checks, post-market reviews, position daily reports, and read-only broker reconciliation, but should ask before editing files and should never call broker write actions. They are not automated trading systems. Google Sheets is no longer a trade-record layer.
