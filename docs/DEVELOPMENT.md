# Development Workflow

This document defines the public development workflow for the DailyTrades portable Skill repository.

It is a project workflow document, not an internal agent prompt. Do not include private trade records, credentials, account details, unpublished research excerpts, or broker-specific secrets.

## Portable Skill Distribution

Run the narrow distribution contract without network access:

```bash
uv run python scripts/verify_portable_distribution_contract.py
```

Run the actual `npx skills` discovery and install smoke in isolated temporary
agent homes. The script defaults to the current checkout and accepts a GitHub
source as its optional first argument after changes are published:

```bash
bash scripts/smoke-portable-skill-install.sh
bash scripts/smoke-portable-skill-install.sh Archerouyang/dailytrades
```

The smoke sets temporary `HOME`, `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, and
`XDG_CONFIG_HOME`, compares both installed copies with the canonical public
Skill, scans for private configuration and absolute user paths, and removes the
temporary directory on exit.

Visual acceptance is manual. Generate one representative inline HTML artifact,
open it in the Codex in-app browser, and give the user the artifact early. Do
not replace user judgment with screenshot matrices or pixel-diff gates.

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

## Sol Ultra Review Pipeline

When Codex is GPT-5.6 Sol Ultra, review defaults to the smallest agent topology:

1. Sol uses a few read-only commands to pin the implementation baseline,
   originating spec, task-owned tracked/untracked files, commit list, and concise
   verification evidence.
2. For a formal `review` skill run, spawn exactly two explicit GPT-5.6 Terra
   agents for the required Standards and Spec axes. Do not add Luna by default.
3. Sol receives only structured findings, reads the cited code hotspots, reruns
   the smallest useful verification, and makes the final
   `accept / changes_requested / reject` decision.

Use Luna before Terra only when mechanical preparation is itself substantial:
large source sets, ambiguous file ownership across branches/worktrees, or a
scope that cannot be recovered cheaply with a small number of read-only Git and
thread queries. Luna does not make quality decisions.

Review subagents must use `fork_context: false`. Their input must not include an
entire development/debug conversation or an unbounded repository diff. Each
review output should stay under roughly 400 words and include only:

- severity and confidence;
- file and line;
- violated standard or spec requirement;
- minimal reproduction or failure path;
- missing verification evidence.

Close review agents after aggregation. Keep the full diff and verbose test logs
in the worker task or temporary artifacts; do not copy them into the Sol
coordinator context.

Outside a formal review, use zero subagents for normal documentation, planning,
status checks, narrow fixes, and direct verification. Use one bounded subagent
only when it provides real parallelism or protects substantial Sol context;
additional agents require independent, non-overlapping work.

Sol directly reviews the full critical path when any of these applies:

- P0 safety, trading-decision correctness, private-data, credential, or order
  boundary risk;
- architecture optimization trigger or hard-to-reverse cross-module contract;
- reviewer disagreement, unexplained test/backtest behavior, or low confidence;
- model promotion/rollback or another decision explicitly reserved for Sol;
- explicit user request for direct Sol review.

For low-risk routine changes that do not require formal review, Sol may inspect
and verify directly without spawning an agent. For formal review, passing
deterministic tests plus clean Terra axes is sufficient for Sol to perform a
targeted sample rather than rereading the full diff. Worker self-review remains
evidence, not final approval.

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

## Test Policy

Use one focused self-test when repo-owned deterministic behavior changes:

- schema and privacy validation;
- deterministic ResearchResult delivery;
- chart payload preparation;
- high-risk safety boundaries.

TDD is not required for:

- `CONTEXT.md`;
- `docs/ROADMAP.md`;
- `docs/PROJECT_LOG.md`;
- `docs/DEVELOPMENT_PLAN.md`;
- ADRs;
- skill references;
- prompt/template prose.

Do not add workflow matrices, browser screenshot suites, duplicate contract
tests, or a self-test for another test. Prefer a narrow red-green loop for the
changed invariant, then deliver one real artifact for human acceptance.

## Test Scope

Tests should cover only repo-owned behavior.

The default gate is intentionally small: compile, portable Skill distribution,
ResearchResult delivery, ArtifactPacket compatibility, and Skill structure.
It does not launch Chrome or export artifacts. Run broader checks only when a
concrete risk or release boundary requires them.

External connectors are outside this repo's test scope. In particular, do not test live IBKR behavior here:

- no IBKR connection tests;
- no live account reads;
- no live market-data subscription tests;
- no order creation, modification, deletion, or submission tests.

If the repo later adds a pure transformation layer for external connector data, test only the transformation with fixture input. Example: fixture OHLCV JSON to normalized chart data. The connector itself remains outside repo CI.

## Python Environment

Use `uv` for all repo Python verification and script smoke checks. Do not rely
on global Python packages, user site-packages, or ad-hoc `pip install` state.

Standard local verification:

```bash
bash scripts/verify-skill.sh
```

The script compiles the canonical Skill and runs its focused distribution and
delivery checks through `uv run`. It sets `UV_CACHE_DIR`, `UV_PROJECT_ENVIRONMENT`, and
`UV_PYTHON_INSTALL_DIR` under `.scratch/` so Codex sandbox runs do not write to
global cache directories. It prefers the Codex bundled Python 3.12 when
available; otherwise it falls back to `python3.12` or `python3`.

## Product smoke

Use `docs/MVP_RUNBOOK.md` for the 0.2.0 smoke. It runs the narrow verification
gate, generates one ResearchResult delivery, and stops for user acceptance of
the actual inline HTML. It does not exercise private runtime state, brokers,
automations, or obsolete KVN databases.

For individual scripts, use:

```bash
uv run python skills/trading-research-system/scripts/<script>.py
```

## CI Policy

Lightweight CI is useful once the first repo-owned test harness exists.

Initial CI should check:

- Python syntax for Skill scripts;
- unit tests against fixtures;
- script smoke tests against fixture CSV files;
- basic Skill file-structure sanity;
- portable distribution validation through `scripts/verify-skill.sh`;
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
- Skill structure remains valid when public Skill files changed;
- Python checks are run through `uv` or the reason for skipping `uv` is stated;
- public/private repo boundary is preserved;
- `docs/PROJECT_LOG.md` is updated when the change affects project trajectory;
- no live external service behavior is required to prove the change.
## Inline Panel PNG Export

Keep the chat-inline Panel as the canonical interactive artifact. PNG export is
opt-in only: run it only after the user explicitly asks for a downloadable
image. Export that accepted HTML fragment on demand:

```bash
node scripts/export_inline_png.mjs \
  --input /absolute/path/to/panel.html \
  --output /absolute/path/to/panel.png
```

The exporter measures the rendered document and captures the complete content,
not a fixed browser viewport. Do not auto-save, batch-export, or update README
as a side effect of generating an inline Panel. Use `--public` for an explicitly
requested README or other public asset; it fails closed on common private-data
sentinels. Public images may use synthetic fixtures or dated public market data
after explicit user approval and privacy review. They must never contain
account, broker, private-runtime, or private-portfolio information. Do not add
hosting or a static frontend for this path.
