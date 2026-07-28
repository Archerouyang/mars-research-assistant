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

只分析一个明确标的的 `1D` 已完成日线。未指定市场时，不带市场后缀的 symbol 默认按美国
上市标的解释；明确的交易所或 yfinance 市场后缀覆盖默认值。不得根据用户位置或系统时区
改写 symbol。调用方必须提供独立、尚不存在的 `output_dir`。
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

## 运行前环境门

只有本技术面分析 Skill 需要 Python 行情环境；其他五个 Skill 不得因此运行 uv。每次执行
前，先从当前 Skill 目录运行幂等环境门：

```bash
bash scripts/ensure_yfinance_environment.sh
```

环境门要求安装的是完整 Mars Skill 包，并从包根 `pyproject.toml` 与 `uv.lock` 读取唯一
依赖契约。它只使用 uv：优先复用可用的 Python 3.12 与包根 `.venv`；缺少 3.12 时让 uv
安装受管解释器；随后执行锁定同步并验证 yfinance 版本。锁与环境均已满足时仍可安全重复
运行，不使用 pip，不写入用户项目或全局 Python。

若当前平台只复制了本 `SKILL.md` 或技术面子目录，缺少完整包的锁文件与脚本，必须停止并
提示用户安装完整仓库包，不得临时拼装未锁定环境。

环境就绪后，通过包内 Python 执行：

```bash
../../.venv/bin/python scripts/analyze_with_yfinance.py \
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

下列归一化指标必须先写入 `evidence.json`，Markdown 和 HTML 只能解释或显示同一份数字：

- 最新收盘相对 SMA20/50/200 的百分比距离；
- 固定回看 5 根已完成日线的 SMA20/50/200 方向和变化幅度；
- 20/60/120 根已完成日线收益；
- ATR14 占最新收盘价比例、最新成交量相对 20 日均量倍数；
- 距 120 日高点回撤，以及距最近支撑和阻力的百分比距离。

摘要先给出一个确定性的当前结论与优先情景，再解释趋势、位置、参与度和波动是确认还是
冲突。不得输出概率、评分或伪置信度。多头、震荡、空头三种情景都必须分别说明支持条件、
有利表现、不利表现、触发条件和失效条件；即使没有市场背景也必须独立成立。

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

它是一次性行情快照：Python 完成一次下载与计算后，HTML 只对已内嵌的固定数据提供本地
缩放、平移、十字光标和悬停，不轮询、不刷新行情，也不连接实时数据服务。

真实浏览器验收还必须确认缩放、平移、十字光标、OHLCV/SMA 悬停、桌面与窄屏布局；
颜色不能是区分当前价、均线、支撑、阻力和成交量的唯一方式。打开时不得发起 fetch、
XHR、WebSocket、CDN、遥测或其他外部请求，不得使用浏览器持久状态。HTML 字符串检查
不能替代真实浏览器和人眼视觉评审；浏览器不可用时必须明确记录限制。

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
套一次性分析逻辑，并用 `--no-open` 抑制 GUI 副作用。真实 yfinance 数据适配器仅在发布集成
验收时联网运行一次。
