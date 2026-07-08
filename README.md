# Dailytrades / Trading Research System

这是一个给 Codex 使用的 AI-native 交易研究 plugin。它帮助使用者把宏观、政策、利率、研报、盘面、持仓和 broker-live 数据压缩成可执行、可复盘、可更新的交易研究笔记。

它不是自动交易系统，不下单，不保证收益，也不会绕过付费研报或 broker 权限。

## 核心闭环

```text
研报 / 宏观 / 政策 / 利率 / 盘面
-> Active Market Plan
-> 盘前和盘中 setup 追踪
-> broker-live 持仓日报和复盘上下文
-> 风险暴露、setup 表现和系统优化
```

这个项目的重点不是生成长报告，而是让 agent 读得多、校验得严、展示得少，只把会改变计划、风险、setup 状态或下一步决策的信息告诉使用者。

## 快速开始

在 Codex 里直接说你要完成的交易研究任务。普通使用者不需要记住
focused skill 名称；agent 会根据任务自动选择内部工作流。

```text
帮我做下周交易计划，先看宏观、利率、政策、新闻和当前持仓影响。
```

```text
盘前更新一下今天需要盯的 setup，告诉我哪些接近触发。
```

```text
现在检查今天计划里的 QQQ 和 MU setup，哪些接近触发，哪些失效？
```

```text
读这篇 NVDA 研报，提炼 thesis 和 counter-thesis，并告诉我是否影响 Active Market Plan。
```

```text
生成今天的持仓日报，只告诉我风险暴露和需要决策的事项。
```

```text
这笔 QQQ 0DTE 已经结束了，帮我做出场复盘和系统标签。
```

## 主要能力

| 能力 | 用户任务 | 输出 |
| --- | --- | --- |
| 周度深度计划 | “帮我做下周交易计划” | 上周复盘、宏观/政策/利率/新闻展望、重点事件、持仓影响、setup 候选 |
| 每日盘面追踪 | “盘前更新一下” / “盘中看一下变化” | 当天变化、关键点位、setup 状态、风险变化、下一步检查 |
| 盘中 setup 扫描 | “检查今天计划里的 setup” | `candidate` / `active` / `approaching` / `triggered` / `invalidated` / `needs_review` |
| 研报摄取 | “读这篇研报，看是否影响计划” | `Research Report Digest`、`Claim Ledger`、`Verification Queue`、计划影响 |
| 宏观和标的研究 | “筛一下受益于利率下行的股票” | 宏观、金融条件、政策事件、行业强弱、个股 thesis 校验 |
| 持仓日报 | “生成今天的持仓日报” | broker-live 持仓摘要、暴露可视化、风险提示、今日决策事项 |
| 交易复盘 | “我刚下单了，带我复盘” / “这笔交易结束了” | 基于 broker-live 成交事实的入场/出场复盘上下文、错误标签、经验沉淀 |
| 组合风险 | “这笔加仓会不会让组合太集中” | 持仓集中度、方向暴露、工具风险、新交易对组合的影响 |
| 交易统计 | “看一下我的 setup 表现和胜率” | 胜率、R 倍数、expectancy、setup 表现、系统优化线索 |

## 高级入口

`trading-research` 是概念上的总入口。`weekly-trading-plan`、
`daily-market-tracking`、`intraday-setup-scan`、`research-report-intake`、
`trade-review`、`portfolio-risk` 等 focused skills 是 agent 内部工作流、
开发测试边界和高级调试入口，不是普通使用者默认要记的命令菜单。

## 本地记录

本地 runtime 是详细工作记忆和 source of truth。默认位置：

```text
~/Documents/dailytrades-runtime/
```

常见结构：

```text
market-plan.md
trading-profile.md
updates/YYYY-MM-DD.md
daily/YYYY-MM-DD/
charts/
```

### Runtime bootstrap

首次使用前可以先用空模板初始化私有 runtime。这个命令只写本地模板文件，
No live broker reads，不读取真实账户、不调用真实 market data、不创建真实
Codex automations。

```bash
uv run python plugins/trading-research-system/scripts/bootstrap_runtime.py --dry-run
uv run python plugins/trading-research-system/scripts/bootstrap_runtime.py --date 2026-07-06
```

### Broker snapshot ingest

当 Longbridge / IBKR 只读导出或 connector adapter 已经产生本地 CSV 后，
用 `broker_snapshot_ingest.py` 归一成标准 `portfolio_snapshot.csv`。这个命令
只读取用户授权的 read-only broker export；No live broker reads，不访问券商账户、
不调用行情、不创建或修改订单。

```bash
uv run python plugins/trading-research-system/scripts/broker_snapshot_ingest.py \
  --input IBKR:/path/to/ibkr-positions.csv \
  --input Longbridge:/path/to/longbridge-positions.csv \
  --output ~/Documents/dailytrades-runtime/daily/2026-07-06/portfolio_snapshot.csv \
  --as-of 2026-07-06T20:00:00Z
```

### Longbridge Terminal CLI adapter

如果本机已经安装并授权 Longbridge Terminal CLI，可以先由用户/agent 在只读边界
下生成 portfolio JSON，再用 `longbridge_cli_adapter.py` 转成标准
`portfolio_snapshot.csv`。这个 adapter 只消费已保存 JSON；契约短语是
`No live broker reads`，不运行 CLI、不调用行情、不创建或修改订单。

```bash
longbridge portfolio --format json > /tmp/longbridge-portfolio.json

uv run python plugins/trading-research-system/scripts/longbridge_cli_adapter.py \
  --portfolio-json /tmp/longbridge-portfolio.json \
  --output ~/Documents/dailytrades-runtime/daily/2026-07-06/portfolio_snapshot.csv \
  --as-of 2026-07-06T20:00:00Z
```

Google Sheets 不再作为交易记录层。后续如果启用，只同步非敏感摘要、持仓日报索引或可视化结果，不保存逐笔 broker facts。

`trading-profile.md` 是私有策略配置层，用来记录使用者自己的策略评分、主动交易池、ETF 组合、交易工具、时间框架、拥挤度模型和风控偏好。public plugin 只提供模板，不内置某个使用者的具体交易模型。

## 数据和连接边界

- Broker 数据只读，用于持仓、成交、订单状态、风险和复盘。
- 安装后首次交易研究日程或初始化 runtime 时询问启用哪些 broker 来源；v1 正式支持 Longbridge skill/plugin/Terminal CLI 和 IBKR connector。手动 CSV 只作为单次运行或 fixture 的降级 fallback。
- 券商只读来源设置只确认 read-only 来源偏好，不自动读取账户、不自动安装软件、不写 public repo，也不允许任何下单/改单/撤单动作。
- Longbridge `macrodata` 可作为宏观数据和金融条件读取源；政策事实和官方讲话仍需优先用 S0 官方来源确认。
- Google Drive 可以作为研报、表格或记录来源，但不替代本地 runtime。
- Google Sheets 是可选摘要展示层，不做双向同步，也不维护交易记录。
- 研报只能来自公开、授权或用户提供内容；不可访问内容只能标记为 inaccessible。

## 安全边界

这个 plugin 只做研究和决策支持：

- 不创建、提交、修改或取消真实订单；
- 不提供保证收益或确定性买卖结论；
- 不绕过付费墙、账户权限或数据授权；
- 不把研报观点直接升级为交易 setup；
- 不把短周期信号当作完整交易计划；
- 不提供税务、法律或受监管投资建议。

## 当前状态

| 状态 | 内容 |
| --- | --- |
| 已可用 | AI-native 设计契约、router intent fixtures/verifier、runtime health 脚本/契约、Runtime bootstrap、Active Market Plan fixture package、内部 focused skills、Active Market Plan 契约、Trade Plan Preparation 契约、研报摄取契约、本地 daily 模板、风险/统计基础脚本、chart artifact |
| 可选内部输入 | 外部量化动量快照消费层；默认不开放模型构建、排名生成或公开入口 |
| 开发中 | broker-live adapter live read、盘中 scan data adapter |
| 后续 | Codex 持仓日报 automation、异常期权数据源、可视化快照 |

## 开发验证

项目 Python 验证统一使用 `uv`。不要依赖全局 `python3` 是否已经安装
`PyYAML` 或其它开发依赖。

```bash
brew install uv
bash scripts/verify-plugin.sh
```

`scripts/verify-plugin.sh` 会把 `uv` cache、venv 和 managed Python 放到
`.scratch/` 下，并运行 plugin validator 与关键合同检查。

### Local MVP

Fixture-backed local MVP smoke:

```bash
bash scripts/verify-mvp.sh
```

See [MVP Runbook](docs/MVP_RUNBOOK.md). This check does not perform live
broker reads, real Codex automations, or live market data calls.

## 更多文档

- [Plugin README](plugins/trading-research-system/README.md): plugin 包内详细说明、脚本和模板。
- [MVP Runbook](docs/MVP_RUNBOOK.md): fixture-backed local MVP smoke 和新对话验证边界。
- [Plugin Design](docs/PLUGIN_DESIGN.md): 已接受的 AI-native UX、runtime、broker、chart 和开发队列设计。
- [Roadmap](docs/ROADMAP.md): 产品边界、执行方法、当前进度和任务拆分。
- [Development Plan](docs/DEVELOPMENT_PLAN.md): 当前开发优先级和每日开发规划。
- [Project Log](docs/PROJECT_LOG.md): GitHub trajectory 和重要变更记录。
- [Context](CONTEXT.md): 领域语言和术语定义。
