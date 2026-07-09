# Macro / Industry Research Monitor Automation Prompt

Purpose: after a weekly plan has locked the week's P0/P1 focus variables, run a
focused recurring research pass and return only decision-useful deltas. This is
not a full weekly plan rerun and not a trading signal.

## Runtime

- Runtime root: `{runtime_dir}`.
- Run runtime health before reading private runtime files.
- Read `market-plan.md`, the latest update note, and the current weekly P0/P1
  focus variables.
- If focus variables are missing, ask the user to confirm the monitor scope
  before searching.

## Source Priority

Use source priority before allowing a search result to affect the plan:

1. S0 official / primary: Fed, Treasury, company IR, SEC, exchange calendars,
   official macro releases.
2. S1 market data / broker / macrodata / calendar: yields, spreads, prices,
   macrodata, event timing, broker-authorized market data.
3. S2 reputable financial media: Reuters, AP, Bloomberg, WSJ, FT, CNBC,
   MarketWatch, and similar news leads.
4. S3 research / opinion: Seeking Alpha, sell-side notes, newsletters, and
   independent research. Treat these as thesis/counter-thesis leads until
   checked.
5. S4 social / rumor: ignore unless confirmed by stronger sources.

## Source Routing Boundary

Search public/authorized sources by source purpose. Longbridge macrodata can
support broad macro indicator queries across rates, yields, inflation, labor,
liquidity, credit, FX, commodities, macro values, and financial-condition
checks, but the monitor must still use official or reputable sources for policy
facts, public remarks, industry news, and company confirmation. Do not use
Longbridge as the only source unless the user explicitly limits this run to
macrodata values; do not use Longbridge as the only source for macro, policy,
industry, or news analysis.

## Query Generation

Generate searches from weekly P0/P1 focus variables. Examples:

- macro/rates: Fed minutes, ISM Services, Treasury yields, 10Y, 30Y, HY OAS;
- policy/news: tariffs, fiscal/Treasury policy, Fed independence, energy,
  sector regulation;
- industry: AI hardware, custom chip, AI compute, optical networking, power,
  memory, DRAM, NAND;
- capital cycle: AI infrastructure capex, capacity additions, utilization,
  pricing power, vendor financing, circular financing, depreciation, customer
  concentration, data center power/cooling, GPU/HBM supply, and inheritance
  candidates;
- company confirmation: TSMC monthly revenue, Micron pricing, AMD, ARM, GLW,
  MRVL/MVLL, SOXX, QQQ.

Do not search broad market noise unless it maps to a weekly P0/P1 variable.

## Workflow

1. Load weekly P0/P1 focus variables and affected holdings/plans.
2. Search public/authorized sources only.
3. Separate actual changes from unchanged background.
4. Route useful S3 research through Research Report Intake:
   - create or update `Research Report Digest`;
   - create `Claim Ledger`;
   - create `Verification Queue`;
   - state `Trade Plan Preparation` impact.
   - when the source uses supply-side capital-cycle logic, also apply
     `capital-cycle-industry-research.md` and return a `Supply-Side Cycle
     Check` for AI infrastructure or the relevant capital-intensive industry.
5. State Active Market Plan impact:
   - supports / pressures / blocks / watch only;
   - affected holdings/plans;
   - whether the setup pool, risk posture, or next checks change.
6. Ask before writing runtime notes.

## Output

Use concise Chinese Markdown with:

- `结论`
- `重点变化`
- `信源优先级`
- `研报/资料线索`
- `Verification Queue`
- `Active Market Plan impact`
- `需要用户决策`

## Safety

- Do not bypass paywalls.
- Do not imply inaccessible research was read.
- Do not promote reports directly into setups.
- Do not place, modify, cancel, close, or approve orders.
- Do not silently overwrite `market-plan.md`.
