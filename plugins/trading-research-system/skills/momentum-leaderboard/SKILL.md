---
name: momentum-leaderboard
description: Read imported KVN Momentum Leaderboard snapshots, display Top10, query tickers, summarize Top10 changes, and feed research-priority candidates into Trade Plan Preparation. Use when the user asks for KVN, momentum leaderboard, Top10, ticker lookup, strongest momentum names, or KVN changes.
---

# Momentum Leaderboard

Use this skill for KVN Momentum Leaderboard tasks.

This is decision support, not a buy list. KVN is research priority only, not a
trade signal by itself. This skill consumes imported snapshots; it does not construct the quantitative model, choose vendors, backtest factors, or infer
orders.

## Workflow

1. Read `../trading-research/references/runtime-health.md` before relying on
   private runtime state. If the KVN store is missing or stale, say so and ask
   whether to import a snapshot or continue without KVN.
2. Read `../trading-research/references/momentum-leaderboard.md` for the
   snapshot schema, Top10 definition, and output rules.
3. Use `../../scripts/kvn_leaderboard.py` for observable behavior:
   - `show`: default Top10 display.
   - `query`: look up any imported ticker, including non-Top10 names.
   - `changes`: compare current Top10 with the previous imported snapshot.
   - `import`: only after the user confirms the source file, date, and
     destination.
4. When the user asks for trade ideas from KVN, do not promote names directly
   into setup rows. Feed names into Trade Plan Preparation and the
   Cross-Section Candidate Pool with the required macro/financial,
   industry/company, price-structure, and portfolio-risk gates.

## Commands

Check runtime state:

```bash
python3 ../../scripts/runtime_health.py --format json
```

Display Top10:

```bash
python3 ../../scripts/kvn_leaderboard.py show --top 10
```

Query a ticker:

```bash
python3 ../../scripts/kvn_leaderboard.py query SOXX
```

Show Top10 changes:

```bash
python3 ../../scripts/kvn_leaderboard.py changes
```

Import a confirmed snapshot:

```bash
python3 ../../scripts/kvn_leaderboard.py import /path/to/kvn.csv --source user
```

## Output

Use concise Chinese Markdown:

- `结论`: latest KVN read or missing-state decision.
- `Top10`: default leaderboard when requested.
- `变化`: new, dropped, and continued Top10 names when previous snapshots exist.
- `Ticker 查询`: include rank, KVN score, KVN P, S&P500 membership, current Top10
  status, and Top10 memory.
- `进入交易计划准备的候选`: only when the user asks for idea generation.
- `下一步`: import snapshot, verify thesis, check price structure, or feed into
  Trade Plan Preparation.

Always state: KVN is research priority only, not a buy list.
