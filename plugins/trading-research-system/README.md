# Trading Research System Plugin

This plugin packages a trading research workflow for Codex.

It is designed for research, screening, risk review, and decision support. It does not provide guaranteed returns, personalized financial advice, or trading instructions that ignore user constraints.

## Capabilities

- Macro and policy filtering focused on market-moving variables.
- Trump policy, Treasury policy, rates, yields, and liquidity monitoring.
- Equity screening with thesis verification against primary sources.
- Seeking Alpha and similar research-note synthesis when accessible or provided by the user.
- High-level Al Brooks price action timing framework.
- Portfolio risk exposure checks.

## Skill

Invoke the bundled skill with:

```text
$trading-research
```

Example prompts:

```text
$trading-research Analyze NVDA using my workflow: macro, research-note validation, price action, and portfolio risk.
```

```text
$trading-research Screen US stocks that benefit from lower long-end yields. My current holdings are...
```

## Data Boundaries

For current policy, market prices, rates, yields, financial statements, or news, Codex must verify against current sources. Paywalled sources such as Seeking Alpha can only be analyzed from publicly accessible content or user-provided excerpts.
