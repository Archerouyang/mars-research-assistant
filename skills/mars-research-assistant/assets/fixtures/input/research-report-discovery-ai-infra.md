# Report Discovery Fixture: AI Infrastructure Research

This is a synthetic prompt fixture for testing report discovery behavior. It
does not include copyrighted report text.

## User Request

Find useful research sources for AI infrastructure beneficiaries, especially
optical networking, power infrastructure, and AI hardware suppliers. I may have
Seeking Alpha access, but do not bypass any paywall. Tell me which sources are
worth reading, which claims could affect the Active Market Plan, and which
sources are inaccessible unless I provide authorized content.

## Candidate Source States

| title | source_type | source_priority | date | target | stance | access_status |
| --- | --- | --- | --- | --- | --- | --- |
| Example GLW investor presentation | company IR | S0 official / primary | 2026-06-18 | GLW | factual | public |
| Example AI networking earnings transcript | transcript | S0 official / primary | 2026-06-19 | AI networking suppliers | factual | public |
| Example market data relative strength snapshot | market data | S1 market data / broker / macrodata / calendar | 2026-06-20 | GLW/LITE/CRDO | neutral | authorized |
| Example Seeking Alpha bullish article | Seeking Alpha | S3 research / opinion | 2026-06-20 | GLW | bullish | inaccessible |
| Example unsourced social thread | social media | S4 social / rumor | 2026-06-20 | optical theme | bullish | public |

## Required Discovery Behavior

- Prefer public S0/S1 sources for company facts and current market confirmation.
- Mark inaccessible S3 sources as useful leads only, not read content.
- Ask the user to provide authorized text or access before summarizing
  inaccessible research.
- Ignore S4 rumor unless confirmed by stronger sources.
- Output what each source could change in Trade Plan Preparation.
