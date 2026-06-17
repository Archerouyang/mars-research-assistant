---
name: research-report-intake
description: Find, intake, summarize, and verify equity or macro research reports, including public/authorized report discovery, user-provided PDF/link/text digestion, Seeking Alpha-style article distillation, claim ledger creation, verification queue creation, and Trade Plan Preparation impact notes. Use when the user asks Codex to find reports, read a report, summarize a PDF, extract a thesis, compare analyst views, validate report claims, or feed research reports into an Active Market Plan.
---

# Research Report Intake

Use this skill to turn research reports into decision-useful inputs. It should read deeply, show only the compressed result, and feed `macro-equity-research`, `weekly-trading-plan`, or the Active Market Plan when needed.

This is decision support, not investment advice. Separate facts, author opinion, assumptions, thesis, counter-thesis, verification status, and risk.

## Workflow

1. Read `../trading-research/references/research-report-intake.md`.
2. Use `Report Discovery` when the user asks to find research:
   - search only public, authorized, or user-accessible sources;
   - prefer primary company materials, filings, transcripts, and reputable research portals before opinion sites;
   - Do not bypass paywalls, scrape restricted content, or imply access that is not available.
3. Use `User-Provided Report Intake` when the user provides a PDF, link, excerpt, screenshot, or text:
   - identify source, date, author, target, stance, rating/price target if present, and report horizon;
   - extract thesis, counter-thesis, key assumptions, evidence, catalysts, valuation logic, and risks;
   - mark every important claim as fact, estimate, opinion, or assumption.
4. Create a `Claim Ledger`:
   - claim;
   - source location when available;
   - type: fact / estimate / opinion / assumption;
   - evidence used by the author;
   - primary/current source needed for verification;
   - current verification status.
5. Create a `Verification Queue`:
   - claims that must be checked against filings, investor relations, transcripts, official macro data, market data, or better current sources;
   - disconfirming evidence to search for;
   - stale data or missing assumptions.
6. Produce `Trade Plan Preparation Impact`:
   - whether the report affects `Industry/Sector Strength` or `Company Thesis Check`;
   - whether it supports, pressures, or blocks a Cross-Section Candidate Pool entry;
   - what must happen before the idea can become a `candidate setup`.
7. If the user needs a full audit, provide source-by-source details. Otherwise keep the user-facing note concise.

## Output

Use Chinese Markdown with:

- `结论`
- `Research Report Digest`
- `Claim Ledger`
- `Verification Queue`
- `Trade Plan Preparation Impact`
- `需要追问用户 / 需要补充来源`

Do not quote long copyrighted passages. Short excerpts are allowed only when necessary for evidence, and should stay minimal.
