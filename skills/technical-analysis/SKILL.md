---
name: technical-analysis
description: 针对单一标的生成基于已完成日线的中文技术面分析，持久交付 Markdown 与 evidence JSON，并用临时 Lightweight Charts HTML 展示同一证据。官方唯一内置 OHLCV 来源为 yfinance；坏数据整体失败关闭。
---

# 技术面分析

## 能力合同

同目录的 `capability.json` 定义公开交付、数据质量门和离线验收场景。

```mars-skill-policy
{"delivery":"technical_evidence_package","forbidden_effects":["fundamentals","industry_analysis","account_access","broker_write","drive_write","persistent_state","provider_fallback"]}
```

只分析一个明确标的的 `1D` 已完成日线。调用方必须提供独立、尚不存在的 `output_dir`。
合格时在临时目录完成并校验两份持久内容，再原子落盘：

```text
analysis.md
evidence.json
```

两份工件共享同一个 `evidence_id`。`analysis.md` 只解释 `evidence.json` 已有的数字；
不得新增关键位、指标或价格。每次合格调用还会在操作系统临时目录生成一个
`chart.html`，使用包内固定版本的 TradingView Lightweight Charts 展示同一证据集最近
120 根已完成 K 线、成交量、SMA20/50/200 与最多两个支撑、两个阻力。该 HTML 不属于
持久工件包，不写入安装目录，也不保存浏览器或研究状态。后续调用会尽力清理同一系统临时
目录下超过 24 小时的旧图表，返回结果同时声明 `expires_after_seconds=86400`。

在包含完整包的受管安装中，通过包内脚本执行：

```bash
uv run python scripts/run_yfinance_analysis.py \
  --symbol SYMBOL \
  --output-dir /caller/provided/new-directory
```

脚本默认请求系统浏览器打开临时 HTML，并始终在标准输出返回临时路径以及
`generated`、`open_attempted`、`open_confirmed` 状态。无法确认打开时仍返回可手动打开
的路径和限制说明。自动化测试可传 `--no-open`，但仍会生成真实 HTML。

不要绕开包内脚本另写临时下载逻辑；脚本负责唯一数据源、质量门、单次重试、原子落盘与
临时图表生成。

## 数据源与质量门

官方唯一内置 OHLCV 来源是 yfinance。每次输出都将它标为非官方、best-effort；不读取、
探测、保存或输出任何 API key，也不尝试其他 Provider。用户可以在自己的 fork 中修改，
但不属于官方兼容范围。

第一次取数不合格时，只允许用 yfinance 扩大历史窗口重试一次。可以安全剔除一根位于
末尾的未完成日线；不得插值、合成、调换顺序或切换来源。

在输出任何技术结论前，必须同时满足：

- 时间框架为 `1D`，时间戳带时区且严格递增；
- 复权口径明确为 adjusted；
- 每根都包含有限的 OHLCV、正成交量和一致的价格边界；
- 声明覆盖范围由实际 bars 覆盖；
- 剔除未完成日线后至少有 319 根。

任一门槛在唯一一次重试后仍失败，只原子交付含“数据状态”和“数据缺口”的
`analysis.md`。不生成临时 HTML、evidence JSON、趋势、关键位、情景或失效条件。

## 确定性证据

SMA20/50/200、ATR14、趋势分类和关键位全部由脚本确定性计算。关键位来自已确认
swing high / swing low，按固定 `0.5 × ATR14` 聚类，并依次按触碰次数、最近确认时间、
距最新收盘价排序。每侧最多两个；没有合格摆动位时使用明确标记的 120 日高低点 fallback。

每条关键位必须携带：

- `method`
- `lookback`
- `anchor_dates`
- `touches`
- `price`

图表使用包内 vendored 的 TradingView Lightweight Charts 5.2.0 standalone 构建；
运行时不访问 CDN、不要求 Node/npm，也不在 JavaScript 中重新计算分析指标。生成的单文件
HTML 内嵌库与证据视图数据，包含 `evidence_id`、来源、时区、as_of、复权口径、
bars_used、TradingView attribution 和完整关键位 provenance。

## 可选市场背景

市场快照背景是非阻塞输入。与当前组合任务同批产生时直接有效；外部背景按目标市场时区
默认 24 小时有效。缺失、失败、无效或过期时，明确说明“仅基于技术面证据”并继续交付。

背景只能解释与技术证据的共振或冲突，不能改变 `evidence_id`、图表数据、指标或关键位。
即使用户跳过前置宏观步骤，也要完整阐述多头、震荡、空头的条件和各自失效条件。

## 边界

不加入基本面、行业分析、账户、仓位、订单、交易执行或 Drive 写入。不创建固定全局目录，
不向 Skill 安装目录写入，不使用 `localStorage`，不持久化图表或研究状态，不在打开图表时
发起网络请求。本交付不是实时行情或交易建议。

仓库内的离线公开验收入口是 `scripts/render_technical_analysis_fixture.py`，它直接执行同一
包内 runtime，并用 `--no-open` 抑制 GUI 副作用。真实 yfinance 入口仅在发布集成验收时联网
运行。
