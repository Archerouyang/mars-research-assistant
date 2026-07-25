# Macro Board Interactive Acceptance

## Result

- Status: accepted through direct manual inspection of a generated synthetic
  `research-brief.html` in the local application browser.
- Scope: the initial `趋势` view with `NDX/RUT` selected; `当前状态` and its
  factor-only selector; `下周事件`; and `情景`.
- The visual fixture remains synthetic and explicitly labelled as non-market
  data. It is not evidence of a live provider result.

## Confirmed boundaries

- The Board is one-shot and self-contained: no runtime, cache, manifest,
  Gallery, account, holding, position, order, or broker-state surface exists.
- The visible copy distinguishes frozen observations, conditional scenarios,
  and macro-factor sensitivity from holdings or trade instructions.
- The Chinese system-font stack, compact market strip, evidence rail, tabs,
  chart, and selected-control states are accepted for the current visual
  contract.

## Repeatable checks

- The fixture writer creates only a caller-owned `research-brief.html` and
  rejects an existing output file.
- The Macro selftest covers four panels, both trend controls, the exposure
  selector, event evidence/source timing, fixture disclosure, and the
  no-holdings boundary.
- Future visual changes require a newly generated temporary synthetic Board and
  fresh manual inspection; no machine-local path or screenshot is committed as
  acceptance evidence.

final result: accepted
