# Development Workflow

This document defines the public development workflow for the Dailytrades plugin repository.

It is a project workflow document, not an internal agent prompt. Do not include private trade records, credentials, account details, unpublished research excerpts, or broker-specific secrets.

## Branch Model

Use the lightweight branch model documented in `docs/ROADMAP.md`:

```text
codex/<task> -> dev -> master
```

- `master`: reviewed stable baseline, not a release/version signal.
- `dev`: integration branch for reviewed work.
- `codex/<task>`: task branches for implementation, documentation, experiments, or Claude Code worker tasks.

Claude Code should work on task branches or isolated worktrees. Codex reviews task output before merge or promotion.

## Agent Collaboration

Default mode is Codex-managed Claude Code execution:

1. Codex writes the task packet.
2. Claude Code implements the task.
3. Claude Code self-reviews before returning.
4. Codex reviews the diff, runs checks, and decides whether to accept, revise, or reject.
5. Codex owns final commits, pushes, and project trajectory updates.

Claude Code must not push branches, define product boundaries, create broker orders, or call live external services as part of this plugin workflow.

When a task uses a repo skill, plugin skill, connector, or Claude Code worker, Codex must label it in the user-facing progress update. Use concise labels such as:

- `使用 skills: trading-research-system:trading-research, google-drive:google-sheets`
- `使用 Claude Code: yes, isolated worktree, task=<short task>`
- `使用 Claude Code: no, reason=<small edit/read-only/connector-only>`

If an obvious skill is not used, state the reason briefly. Do not imply Claude Code was used unless the `claude` CLI, a Claude Code worktree session, or an explicitly delegated Claude Code worker actually ran.

## Worktree Policy

Use the current worktree for:

- documentation-only edits;
- small reference updates;
- narrow script fixes;
- read-only analysis.

Use a separate worktree for:

- medium or large implementations;
- Claude Code worker tasks;
- experiments or prototypes;
- schema changes;
- sync logic;
- chart artifact generation;
- any task that may create temporary data or generated artifacts.

If the current worktree has uncommitted user/Codex changes, prefer a separate worktree before starting Claude Code.

## TDD Policy

Use TDD for repo-owned behavior logic:

- intraday scan state machine;
- CSV parsing and schema validation;
- trade statistics;
- portfolio/risk calculations;
- watchlist scoring;
- Google Sheets row mapping;
- chart artifact data preparation;
- future pure data transformation modules.

TDD is not required for:

- `CONTEXT.md`;
- `docs/ROADMAP.md`;
- `docs/PROJECT_LOG.md`;
- `docs/DEVELOPMENT_PLAN.md`;
- ADRs;
- skill references;
- prompt/template prose.

For TDD tasks:

1. Add or update fixture inputs.
2. Add the expected output or assertion.
3. Run the failing test, or explain why the test harness does not exist yet.
4. Implement the smallest useful change.
5. Run tests and relevant smoke checks.
6. Return a self-review.

## Test Scope

Tests should cover only repo-owned behavior.

Required test coverage as modules are added:

- happy path;
- missing or invalid required fields;
- edge cases for status transitions or calculations;
- fixture-based smoke tests for scripts;
- no live external service calls.

External connectors are outside this repo's test scope. In particular, do not test live IBKR behavior here:

- no IBKR connection tests;
- no live account reads;
- no live market-data subscription tests;
- no order creation, modification, deletion, or submission tests.

If the repo later adds a pure transformation layer for external connector data, test only the transformation with fixture input. Example: fixture OHLCV JSON to normalized chart data. The connector itself remains outside repo CI.

## CI Policy

Lightweight CI is useful once the first repo-owned test harness exists.

Initial CI should check:

- Python syntax for plugin scripts;
- unit tests against fixtures;
- script smoke tests against fixture CSV files;
- basic plugin file-structure sanity;
- no tests require live IBKR, Google Drive, Gmail, Calendar, or other external services.

CI should not:

- publish releases;
- create release tags;
- update plugin cachebusters;
- call live broker services;
- call live Google services;
- require secrets;
- place, modify, delete, or submit orders.

Until CI exists, Codex must run the relevant local checks before accepting task work.

## Claude Code Self-Review

Claude Code must return this self-review for implementation tasks:

```text
## Claude Self Review

Files changed:
Tests run:
Expected failures:
Known risks:
Boundary check:
- No broker write action:
- No live external service call:
- No private/dev-only file added to public repo:
- No unrelated formatting churn:
```

## Acceptance Gate

Codex can accept a task only when:

- changed behavior is covered by fixture-based checks when practical;
- relevant scripts or docs were inspected;
- plugin structure remains valid when plugin files changed;
- public/private repo boundary is preserved;
- `docs/PROJECT_LOG.md` is updated when the change affects project trajectory;
- no live external service behavior is required to prove the change.
