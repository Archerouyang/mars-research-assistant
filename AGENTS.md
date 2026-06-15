# Project Agent Instructions

This repository is the public-facing plugin repo for the Daily Trades / Trading
Research System. Keep it focused on reusable plugin assets and user-readable
project documentation.

## Scope

- Plugin source lives under `plugins/`.
- Project docs live under `docs/`, `CONTEXT.md`, and top-level user-readable
  markdown files.
- Do not commit private trading records, broker exports, runtime market plans,
  screenshots, generated chart artifacts, credentials, or personal account data.
- Runtime trading data belongs outside the plugin repo, or in ignored local
  paths such as `data/` while the runtime directory is being finalized.

## Development Workflow

- Use `dev` as the default development branch.
- Keep changes small and reviewable.
- Use git for plugin/documentation changes and preserve unrelated user work.
- Prefer TDD for code paths, scripts, and data transformations where behavior
  can be tested cheaply.
- For plugin packaging or cache updates, use the existing project scripts and
  documented workflow before inventing a new path.

## Skill Routing

- For plugin development work, prefer the Matt Pocock engineering skill set:
  `to-issues`, `to-prd`, `triage`, `tdd`, `review`, `diagnose`,
  `improve-codebase-architecture`, `zoom-out`, and related setup skills.
- Use those engineering skills for planning, issue creation, implementation
  slicing, TDD, code review, diagnosis, and architecture work.
- Do not use the Trading Research System skills as development-process
  authority while editing this plugin. Those skills are the product being built.
- Use Trading Research System skills only to run or verify trading-research
  behavior, fixture outputs, and user-facing Daily Ops workflows.
- State which skills are being used in working updates when the task depends on
  them, especially when switching between development work and product-behavior
  verification.

## Plugin Work

- Trading workflow behavior should live in the Trading Research System skills,
  references, templates, or scripts, not in this instruction file.
- Keep AI-native output concise: read and verify more than is shown to the user.
  Put detailed working memory in runtime notes, not public plugin docs.

## Claude Code Collaboration

- Codex coordinates the task and performs final review.
- Claude Code may be used as an implementation subagent for scoped code or docs
  tasks.
- Ask Claude Code to self-check its changes before Codex reviews them.
- Do not let subagents push, reset, clean, or perform destructive git operations.

## Trading Safety Boundary

- The plugin is decision support only.
- It may read broker data through authorized connectors and prepare plans,
  scans, reviews, and risk notes.
- It must not create, submit, or imply approval of real orders.
