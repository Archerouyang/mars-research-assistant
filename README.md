# Dailytrades / Trading Research System

这是一个给 Codex 使用的 AI-native 交易研究 plugin。它帮助使用者把宏观、政策、利率、研报、盘面、持仓和实际交易记录压缩成可执行、可复盘、可更新的交易研究笔记。

它不是自动交易系统，不下单，不保证收益，也不会绕过付费研报或 broker 权限。

## 核心闭环

```text
研报 / 宏观 / 政策 / 利率 / 盘面
-> Active Market Plan
-> 盘前和盘中 setup 追踪
-> 实际交易记录和复盘
-> 胜率、R 倍数、setup 表现和系统优化
```

这个项目的重点不是生成长报告，而是让 agent 读得多、校验得严、展示得少，只把会改变计划、风险、setup 状态或下一步决策的信息告诉使用者。

## 快速开始

在 Codex 里优先从总入口开始：

```text
$trading-research
```

常用入口：

```text
$weekly-trading-plan 帮我做下周交易计划，先从宏观、利率、政策、新闻和当前持仓影响开始。
```

```text
$research-report-intake 阅读这份研报，提炼 thesis、counter-thesis、Claim Ledger 和对 Active Market Plan 的影响。
```

```text
$daily-market-tracking 根据当前 market-plan.md，更新今天盘前/盘中需要关注的 setup 和风险变化。
```

```text
$intraday-setup-scan 检查当前 Active Market Plan 里的 setup，告诉我哪些接近触发、哪些失效、哪些需要我注意。
```

```text
$trade-review 根据最新成交记录，带我完成入场后复盘或出场后复盘。
```

## 主要能力

| 能力 | 入口 | 输出 |
| --- | --- | --- |
| 周度深度计划 | `$weekly-trading-plan` | 上周复盘、宏观/政策/利率/新闻展望、重点事件、持仓影响、setup 候选 |
| 每日盘面追踪 | `$daily-market-tracking` | 当天变化、关键点位、setup 状态、风险变化、下一步检查 |
| 盘中 setup 扫描 | `$intraday-setup-scan` | `candidate` / `active` / `approaching` / `triggered` / `invalidated` / `needs_review` |
| 研报摄取 | `$research-report-intake` | `Research Report Digest`、`Claim Ledger`、`Verification Queue`、计划影响 |
| 宏观和标的研究 | `$macro-equity-research` | 宏观、金融条件、政策事件、行业强弱、个股 thesis 校验 |
| 交易复盘 | `$trade-review` | 下单后入场复盘、出场后结果复盘、错误标签、经验沉淀 |
| 组合风险 | `$portfolio-risk` | 持仓集中度、方向暴露、工具风险、新交易对组合的影响 |
| 交易统计 | `$trading-stats` | 胜率、R 倍数、expectancy、setup 表现、系统优化线索 |

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

Google Sheets 后续只作为单向镜像和查看层，不作为 canonical source。详细记录、复盘、计划变化和 agent working memory 以本地 runtime 为准。

## 数据和连接边界

- Broker 数据只读，用于持仓、成交、订单状态、风险和复盘。
- IBKR、Longbridge 和手动 CSV 都应先映射到 canonical local files，再进入核心分析。
- Google Drive 可以作为研报、表格或记录来源，但不替代本地 runtime。
- Google Sheets 是 compact mirror，不做双向同步。
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
| 已可用 | focused skills、Active Market Plan 契约、Trade Plan Preparation 契约、研报摄取契约、本地 daily 模板、风险/统计基础脚本、chart artifact |
| 开发中 | fixture package、盘中 scan script、两阶段 trade review 写入本地 CSV |
| 后续 | Google Sheets 单向同步、自动化 prompts、动量量化模型、异常期权数据源 |

## 更多文档

- [Plugin README](plugins/trading-research-system/README.md): plugin 包内详细说明、脚本和模板。
- [Roadmap](docs/ROADMAP.md): 产品边界、执行方法、当前进度和任务拆分。
- [Development Plan](docs/DEVELOPMENT_PLAN.md): 当前开发优先级和每日开发规划。
- [Project Log](docs/PROJECT_LOG.md): GitHub trajectory 和重要变更记录。
- [Context](CONTEXT.md): 领域语言和术语定义。
