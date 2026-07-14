# Command-First Distribution And README Plan

Status: approved for implementation

Baseline: `dev@4e90f33`

## Objective

Make Trading Research System installable through one Agent Skills command,
present it to newcomers with a concise bilingual README and reproducible
synthetic visuals, and retain Codex and Claude native plugins as optional
managed wrappers. Public installation must never copy or imply synchronization
of private trading state.

## Canonical Product Language

- **DailyTrades** is the project, repository, and distribution brand.
- **Trading Research System** is the user-facing product.
- **`trading-research-system`** is the single portable Agent Skill and the
  primary technical form of the product.
- **Native plugin** means an optional Codex or Claude wrapper that packages the
  same public capability for managed installation and upgrades.

## Confirmed Requirements

### Command-First Installation

The first-screen installation command is:

```bash
npx skills@latest add Archerouyang/dailytrades --skill trading-research-system -g
```

The installer owns coding-agent detection and target-directory adaptation. Do
not show separate Codex, Claude Code, Cursor, or OpenCode commands as the main
path. Codex and Claude native plugin instructions remain a secondary option.
Submission to the public OpenAI Plugins Directory is deferred and is not a 1.0
acceptance gate.

The repository must expose exactly one portable, self-contained skill named
`trading-research-system`. Focused workflows may remain internal, but a user
must not be able to install a partial set that omits required references,
scripts, or assets. There must be one canonical behavior source: relocation or
a deterministic generated bundle is acceptable, but manually maintained
duplicate behavior is not.

### First Run And Private State

After installation, the first user prompt is:

```text
Start today's trading research.
```

The Chinese equivalent is `开始今日交易研究`. If no runtime exists, the Skill
enters blank first-run setup and confirms the private runtime location and
optional authorized read-only sources. Installation and first run must not
copy, infer, or synchronize watchlists, trading profiles, positions, plans,
credentials, connector grants, or research history.

### README Information Architecture

`README.md` is the default English page. `README.zh-CN.md` is the complete
Chinese version. Both begin with a visible language switch and keep structured
installation, first-run, version, safety, and native-plugin facts consistent.

The root README order is:

1. product name and one-sentence value;
2. one 30-second installation command;
3. first-use prompt;
4. synthetic output gallery;
5. product workflow tree;
6. capability and source summary;
7. Public Skill / Private Runtime boundary;
8. optional Codex and Claude native plugin installation;
9. troubleshooting and links to detailed docs.

Detailed script commands, development verification, and maintainer material
move to the plugin README or existing development documents. The root README
must not read like a script inventory or internal module catalog.

### Visual Gallery

All committed README visuals use explicitly labeled synthetic fixture data and
must be reproducible from repository scripts.

1. A Mermaid top-down tree shows research inputs, Active Market Plan, intraday
   tracking, portfolio risk, review, and the Public Skill / Private Runtime
   boundary.
2. The existing macro regime renderer produces the Macro Regime Panel.
3. TradingView Lightweight Charts v5.2.0 is the canonical K-line renderer. It
   produces interactive HTML; a browser renders that same HTML into the static
   README image. Keep the current handcrafted SVG only as a no-browser fallback,
   not as the README representation of the component.
4. Add a Position Risk Visual renderer using horizontal and stacked bars for
   concentration, instrument/product, theme, and broker exposure plus material
   risk flags.

Use a light financial-research style: white background, black/gray text,
green/red only for state, and yellow for attention. Preserve TradingView's
required attribution, Apache-2.0 notice, and link. Do not use real user charts,
broker screenshots, account data, or decorative generated imagery.

### License

Change the project and published package metadata from `UNLICENSED` to MIT.
Keep trading-safety and no-order-action language separate from the software
license. Preserve third-party notices for bundled or linked chart components.

### Development Journal

Create a native Google Sheet at `My Drive/DailyTrades/DailyTrades 开发日志`.
It starts on 2026-07-14 without historical backfill and uses four columns:
`日期`, `今日完成`, `涉及模块`, and `当前状态`. The coordinator appends one row
at the end of a development day using only reviewed results. The Sheet must not
contain private trading data, credentials, detailed debug traces, or internal
prompts.

## Out Of Scope

- Public OpenAI Plugins Directory submission or review.
- Synchronization of private runtime or user preferences.
- A persistent frontend or hosted dashboard.
- Replacing the existing macro visualization system.
- Formal behavior certification for every coding agent supported by the
  installer.
- Live market, broker, or account reads for README examples.

## Work Packages

### WP1: Portable Distribution

Owner surface: portable skill layout, Codex/Claude manifests, license,
distribution verifiers, and install smoke fixtures. Do not rewrite root README
content or visual renderers.

Deliverables:

- one self-contained `trading-research-system` Agent Skill discoverable by the
  documented `npx skills` command;
- optional Codex and Claude native plugin wrappers over the same public behavior;
- MIT license and required package metadata;
- drift checks that prevent partial or manually duplicated packages;
- isolated discovery/install smoke with no writes to the real agent homes.

### WP2: README And Visual Evidence

Owner surface: `README.md`, `README.zh-CN.md`, README-only assets, existing
visual renderers, a new Position Risk Visual renderer, synthetic visual
fixtures, and visual/documentation verification. Do not redesign package
discovery or native plugin manifests.

Deliverables:

- newcomer-first bilingual README pair;
- reproducible Macro Regime, Lightweight Charts PA, and Position Risk images;
- Mermaid workflow tree;
- TradingView attribution and third-party notice compliance;
- README consistency and visual-generation contract checks.

## Acceptance Gates

1. The documented `npx skills` command discovers and installs exactly one
   self-contained `trading-research-system` skill in isolated test homes.
2. Codex and Claude native wrappers resolve the same public capability without
   copying private state.
3. First-run fixtures enter blank setup and never imply account or preference
   synchronization.
4. English and Chinese READMEs expose the same install command, first prompt,
   package version, safety boundary, and optional native-plugin facts.
5. All three output images regenerate from sanitized fixtures; the PA image is
   captured from Lightweight Charts v5.2.0 HTML and includes attribution.
6. The Position Risk Visual renderer has focused selftests and handles empty,
   partial, and representative synthetic exposure inputs without inventing data.
7. `bash scripts/verify-plugin.sh`, `bash scripts/verify-mvp.sh`, focused new
   contracts, `git diff --check`, and generated-artifact scans pass.
8. The Google Sheet exists in the approved Drive folder and its initial row
   contains only reviewed, non-private development outcomes.

## Review And Integration

Codex reviews WP1 and WP2 separately against this plan using Standards and Spec
axes. A worker self-check is not acceptance. Integrate into `dev` only after
focused checks and independent review pass; re-pin the non-quant UAT worktree
before treating later acceptance as release evidence.
