# Portable Skill Distribution And README Plan

Status: implemented

## Objective

Distribute Mars Research Assistant through one portable Agent Skill and present
it with a concise bilingual README. Installation must never copy or imply
synchronization of private trading state.

## Product Boundary

- **Mars Research Assistant** is the project and repository brand.
- **Mars Research Assistant** is the user-facing product.
- **`mars-research-assistant`** is the single distributed Agent Skill.
- `skills/mars-research-assistant/` is the only package and behavior source.
- Native wrappers and marketplace manifests are not planned or shipped.

## Installation

The first-screen installation command is:

```bash
npx skills@latest add Archerouyang/mars-research-assistant --skill mars-research-assistant -g
```

The installer owns coding-agent detection and target-directory adaptation. The
repository must expose exactly one self-contained Skill; users cannot install a
partial workflow set.

## First Run And Private State

The first prompt is `Start today's trading research.` or `开始今日交易研究`.
Without a private runtime, the Skill enters blank first-run setup. Installation
and first run do not copy, infer, or synchronize watchlists, profiles,
positions, plans, credentials, connector grants, or research history.

## README Contract

`README.md` is the single Chinese product entrypoint and keeps:

1. product purpose and Bayesian decision-support model;
2. one installation command;
3. first-use prompt;
4. user-selected, privacy-reviewed public-market examples;
5. workflow and capability summary;
6. Public Skill / Private Runtime boundary;
7. troubleshooting and detailed documentation links.

## Verification

The minimum release evidence is:

1. `bash scripts/verify-skill.sh`;
2. `bash scripts/smoke-portable-skill-install.sh` in isolated homes;
3. `git diff --check`;
4. explicit human acceptance for user-facing inline artifacts;
5. no private runtime, broker, account, credential, cache, or database state in
   the distributed Skill.

## Out Of Scope

- Native Codex or Claude wrappers and marketplace manifests;
- synchronization of private runtime or user preferences;
- persistent frontend or hosted dashboard;
- live broker or account reads for README examples;
- order creation, modification, cancellation, or submission.
