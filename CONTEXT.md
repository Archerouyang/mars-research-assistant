# Trading Research System

这个上下文定义交易投研系统的领域语言。系统用于把市场信息转化为可验证、可复盘、可更新的 Active Market Plan、setup pool、broker-live 持仓日报、复盘上下文和交易系统可视化。

## Language

**DailyTrades**:
The public project, repository, and distribution brand for Trading Research System.
_Avoid_: plugin name, private runtime

**Trading Research System**:
The user-facing trading research product delivered as one portable Agent Skill.
_Avoid_: Codex plugin, Claude plugin

**Agent Skill package**:
The single self-contained `trading-research-system` package installed across compatible coding agents; it includes every public workflow resource required to run without partial focused-skill selection.
_Avoid_: partial skill set, native plugin

**Command-first distribution**:
The installation model in which one `npx skills` command detects the coding agent and installs the portable Agent Skill.
_Avoid_: marketplace-first distribution, per-agent install paths

**交易投研系统**:
一套从信息收集到交易复盘的研究与决策支持系统。它服务于主动交易，不是自动下单系统，也不是保证收益的荐股系统。
_Avoid_: 自动交易系统, 荐股系统

**投研流水线**:
交易投研系统的核心流程：信息收集、信息处理、交易想法形成、信息验证、K 线 setup 分析、交易计划、broker-live 持仓/成交读取、复盘上下文采集和可视化统计。每个阶段都应产出可追踪的输入、判断和结论。
_Avoid_: 聊天流程, 临时分析

**技能集架构**:
Trading Research System 对外是一个自包含 Agent Skill，内部通过路由和 focused workflows 分担 Active Market Plan 更新、setup 扫描、交易复盘、宏观/标的研究、组合风险和统计复盘。
_Avoid_: 多个可被部分安装的公开 skills, 多个互不相干的 plugin

**Daily Ops Orchestrator**:
Trading Research System 的主动日程引导层。它位于单一 `trading-research-system` Skill 的路由入口，在内部 focused workflows 之前工作：先判断当前是周度 deep update、盘前 quick update、盘中 trigger monitor、盘后 review、研报摄取、持仓风险检查还是交易复盘，再告诉用户下一步应该做什么、为什么、缺少哪些确认，以及确认后会调用哪个 workflow。Daily Ops Orchestrator 不产生独立交易信号，也不替代内部 workflows。
_Avoid_: 新的荐股模块, 让用户手动 call out 每个步骤

**Daily Ops State**:
Daily Ops Orchestrator 的私有运行状态，默认保存在 `{runtime_dir}/ops-state.md`。它记录当前日程阶段、上次 deep/quick/scan/review 时间、待确认事项、active setup 摘要、blocked reason 和 next recommended action。它是日程状态，不是交易日志、broker 原始记录或研报仓库。
_Avoid_: 用聊天记录当状态, 把私有状态写进 public repo

**主动日程引导**:
agent 主动根据时间、runtime health、Active Market Plan、Trading Profile、KVN 状态、broker 授权状态和用户请求判断下一步，而不是要求用户记住并逐个调用 weekly、daily、KVN、setup、risk、review 等模块。主动日程引导的输出必须包含当前阶段、读取状态、缺失确认、建议下一步和确认后动作。
_Avoid_: 模块菜单, 用户自己编排日程

**交易周期确认**:
每个标的或 setup 进入具体触发分析前必须确认的使用意图。标准分组是 `ticker + trade_horizon + instrument`，例如 `QQQ + long-term holding + ETF`、`QQQ + 0DTE + option`、`MU + medium-term swing + equity`、`TSM + LEAP + call`。交易周期决定大周期分析时间框架、触发时间框架、风险边界和输出重点。若交易周期未知，系统只能输出观察问题，不能生成具体 entry/exit trigger。
_Avoid_: 只按 ticker 分组, 所有工具共用时间框架

**Active Market Plan**:
当前有效市场计划，是系统的 living state。它保存在 `{runtime_dir}/market-plan.md`，可以被覆盖更新，始终代表当前操作视图。周末、盘前、盘中和交易后都不是新建一套流程，而是对同一个 Active Market Plan 做不同深度的更新。
_Avoid_: 一次性周报, 每天从零开始

**市场计划更新轨迹**:
Active Market Plan 的 append-only 审计记录，保存在 `{runtime_dir}/updates/YYYY-MM-DD.md`。它记录本次更新类型、哪些市场变量变了、哪些 setup 状态或点位变了、依据是什么、下一步看什么。
_Avoid_: 覆盖后无历史, 聊天记录当日志

**Setup Pool**:
Active Market Plan 中的核心计划池。最小计划单元是 setup，而不是标的或交易工具。Setup 需要带 `theme_id`、`symbol`、`instrument_type`、分析时间框架、触发时间框架、状态、触发区域、失效条件和风险预算。同一市场机会如果有多个交易工具执行方式，应拆成多个 setup，并共享同一个 `theme_id` 或 `market_context_id`。
_Avoid_: 股票清单, 一个想法塞多个工具

**信息收集**:
收集会影响交易决策的原始信息，包括宏观政策、利率、债券收益率、研报、公司数据、价格行为、量化因子、异常期权信号和组合持仓。信息收集本身不等于交易结论。
_Avoid_: 新闻流, 噪音收集

**研报发现**:
由 agent 主动寻找公开、授权或用户可访问的研报、研究文章、公司材料、财报电话会和反方观点，并按信源优先级、时效性、相关性和对计划的潜在影响排序。研报发现不能绕过付费墙，也不能把不可访问来源当作已读取来源。
_Avoid_: 付费墙绕过, 只找确认偏误材料, 研报标题清单

**研报摄取**:
把用户提供的 PDF、链接、摘录、截图或文本，或研报发现阶段找到的可访问内容，压缩成可校验的 `Research Report Digest`、`Claim Ledger`、`Verification Queue` 和 `Trade Plan Preparation Impact`。研报摄取的目标不是长摘要，而是提炼 thesis/counter-thesis、关键假设、证据质量、过期数据、反方证据和下一步校验。
_Avoid_: 长篇摘要, 原文摘抄, 未校验观点直接入计划

**Claim Ledger**:
研报摄取中的关键 claim 台账。它只记录会改变交易计划、候选池、置信度或风险判断的重要 claim，并标记 `fact`、`estimate`、`opinion` 或 `assumption`，同时记录需要用哪个 S0/S1/S2/S3 信源校验。
_Avoid_: 每句话都记录, 不区分事实和观点

**Verification Queue**:
研报摄取后的校验队列。它列出采用研报观点前必须核验的 filings、IR、transcript、官方宏观数据、当前市场数据、估值数据、反方研究或事件日历。未完成 P0 校验的研报观点不能直接推动 setup。
_Avoid_: 看完即采用, 只校验支持证据

**Trade Plan Preparation Impact**:
研报摄取对交易计划准备的映射结果。它说明研报观点是支持、压制、阻止还是仅观察某个主题/标的进入 `Industry/Sector Strength`、`Company Thesis Check` 或 `Cross-Section Candidate Pool`。它不能直接替代大周期环境、价格结构、触发区域、失效条件和风险预算。
_Avoid_: 研报=交易信号, thesis 直接升级 setup

**第一阶段数据源**:
交易投研系统 MVP 阶段优先使用的数据来源，包括用户维护或导出的 CSV、可通过 web search 核验的公开来源、Longbridge macrodata、IBKR 行情数据、read-only broker source、用户提供的研报链接或摘录，以及后续可购买的期权数据 API。第一阶段不要求所有数据全自动接入。
_Avoid_: 全自动数据湖, 不可核验来源

**Broker Source**:
提供只读账户、持仓、成交或订单状态数据的券商来源，例如 IBKR connector、Longbridge skill/plugin 或手动 CSV。Broker Source 是可插拔 adapter，不是 Trading Research System 的核心逻辑。默认使用 broker-live 读取，不要求把逐笔交易事实长期保存成本地记录。
_Avoid_: 单一券商绑定, 券商即系统

**券商只读来源设置**:
Daily Ops 首次启动或 runtime health 显示 broker source 为 `missing` / `unauthorized` 时触发的只读券商来源访谈。它应询问用户是否启用 Longbridge read-only、IBKR read-only、两者都启用，或暂不启用并以 manual CSV / no broker facts 继续。本步骤只配置读取意图和偏好，不读取账户、不安装软件、不写入 public repo，也不允许任何 broker write action。
_Avoid_: 安装 plugin 等于授权 broker, 默认读取账户, 混淆 read-only 和下单权限

**Read-only Broker Adapter**:
把 broker 原始数据转换成标准运行时视图的适配层。它只能读取 positions、executions/trades、orders/status 或授权行情，不能创建、修改、取消真实订单，也不能调仓或平仓。适配层可以为一次分析返回内存数据、临时文件或派生快照，但不应要求长期保存券商逐笔事实。
_Avoid_: 自动下单插件, 账户控制层

**Longbridge Broker Source**:
Longbridge 作为可选 broker source，第一阶段提供 positions、executions/trades 和 orders/status 的 read-only 数据。若环境没有 Longbridge skill/plugin/terminal，应先询问用户是否安装或启用；可提示用户自行使用 `brew install --cask longbridge/tap/longbridge-terminal`。
_Avoid_: 内置 Longbridge 依赖, 自动安装

**Longbridge Macrodata Source**:
Longbridge skill/plugin 中的 `macrodata` 能力，用于多指标宏观数据查询，包括利率/收益率、经济指标、通胀、就业、流动性、信用、外汇、商品和金融条件相关数据。它是宏观数据获取源，不是 broker account source；可作为 `Macro Regime` 和 `Financial Conditions` 的 S1 数据输入，但政策原文、官方讲话、法规状态和经济数据最终发布时间仍应优先用 S0 官方来源确认。
_Avoid_: 把宏观数据源当账户权限, 用聚合数据替代官方政策事实

**Longbridge Skill Adapter**:
把 Longbridge skill/plugin/terminal 的只读能力接入 Trading Research 标准运行时视图的适配层。它拆成三个 capability：`longbridge_broker_skill` 用于 Codex-native skill/plugin 暴露的 positions、executions/trades、orders/status 等 broker facts；`longbridge_terminal_cli` 用于用户已安装且授权的 Longbridge Terminal CLI 只读 portfolio/position JSON；`longbridge_macrodata` 用于宏观和金融条件数值。Daily Ops 启动时应显示 `source_capability_health`，区分当前 chat 未暴露 skill capability、terminal CLI 是否可用、macrodata 是否可用、未授权、缺失、过期和可用状态。
_Avoid_: 把 Longbridge skill 当普通 connector 泛称, 混淆 broker facts 和 macrodata, 当前 chat 未暴露能力时说 Longbridge 不存在

**Longbridge Terminal CLI Adapter**:
消费用户已授权的 `longbridge portfolio --format json` 等只读 CLI 输出，并通过 `longbridge_cli_adapter.py` 转换成标准 `portfolio_snapshot.csv` 的本地适配层。该 adapter 只处理已保存 JSON，不主动运行 CLI、不读取 live broker、不调用行情、不创建/修改/取消/提交订单。
_Avoid_: 把 CLI adapter 当下单层, 把本机安装等同于 macrodata 可用, 把用户真实持仓 fixture 化进 public repo

**Macro Data Source Contract**:
宏观和金融条件分析的来源选择契约。若 Longbridge macrodata 可用，它是宏观数值和金融条件的优先 S1 来源；IBKR 行情数据用于价格、OHLCV、盘中 tape 和市场传导确认；官方来源 fallback 用于 S0 政策事实、经济数据发布时间、官方讲话、法规状态，以及 Longbridge macrodata 不可用时的官方宏观数值回退。Daily Ops / weekly / macro-equity 输出不能只说“宏观重要”，必须列出 `宏观数据来源状态` 和 `实际宏观指标读数`，否则要标记为降级分析。
_Avoid_: 没有实际宏观数值却声称完成宏观分析, 用 IBKR 行情替代 broad macrodata, 用新闻替代官方宏观数据

**Source Routing Boundary**:
按 source purpose 和 claim type 选择信源的硬边界。Longbridge broker source 可用于只读账户/持仓/成交事实，Longbridge macrodata 可用于宏观数值和金融条件，但 news source、政策事实、行业新闻和研报观点必须按 S0/S1/S2/S3 分层选择。选择 Longbridge 做股票数据或券商数据 does not make Longbridge the default source for news，也不能让宏观/政策/行业/新闻分析只使用 Longbridge。
_Avoid_: 一个 connector 变成所有证据来源, 行情源替代新闻源, macrodata 替代官方政策事实

**Broker-Live Data View**:
券商只读数据在一次分析运行中的标准视图，包括当前持仓、账户风险、成交、订单状态和可授权行情。核心分析消费这个标准视图，而不是直接依赖 IBKR、Longbridge 或其它券商的原始结构。该视图可以按需生成可视化或摘要快照，但逐笔券商事实默认不作为本地 source of truth 持久化。
_Avoid_: 直接读各券商私有结构, 本地交易明细作为唯一事实来源

**IBKR 行情数据**:
通过 Interactive Brokers 提供的行情、历史价格和账户数据。它是优先行情来源，但不负责替代研报校验、宏观来源核验或交易系统统计。
_Avoid_: 唯一事实来源

**期权数据 API**:
用于异常期权信号分析的外部付费或授权数据源。它提供成交、未平仓、隐含波动率、偏度和大单等线索，但需要与价格行为、事件和流动性共同验证。
_Avoid_: 期权内幕来源

**动量排行数据集**:
构建 KVN 动量榜所需的价格、成交量、波动率、相对强弱、S&P500 基准分布、赛道/主题分组和历史入榜状态数据集合。第一阶段优先使用授权行情或可导出的 OHLCV 数据；研报和新闻不作为 KVN 原始分数的数据源，而是在榜单之后用于 thesis 校验。
_Avoid_: 黑箱数据

**信息处理**:
把原始信息过滤、归类、去噪、标准化，并转化为可比较的市场变量、标的特征或风险信号。
_Avoid_: 摘要, 复制粘贴

**交易想法**:
一个尚未验证完成的潜在交易机会，包含标的、方向、逻辑、催化剂、风险和待验证假设。交易想法不是交易计划。
_Avoid_: 信号, 荐股

**Trading Profile**:
使用者私有的交易档案，记录交易目标、允许工具、时间框架、策略姿态阈值、主动交易池、ETF 组合、防御/宏观配置规则、拥挤度模型和人工覆盖规则。public plugin 只提供模板和读取规则，不把某个使用者的具体主题、品种、权重或时间框架硬编码为默认行为。
_Avoid_: 插件默认策略, 公开仓位配置

**核心 ETF 底仓**:
用户长期持有的宽基或主题 ETF 仓位，用于承担长期市场 beta 或核心主题暴露。核心 ETF 底仓默认少操作，主要讨论加仓、TP/再平衡、暂停加仓并复核，不按普通短线 setup 处理止损。
_Avoid_: 短线交易仓, 每个波动都调仓

**长期 ETF 组合**:
使用者长期持有和动态平衡的 ETF 组合。它可包含宽基/科技 beta ETF、主题 ETF，以及用于对冲、防御平衡或宏观配置的 ETF。具体 ETF、权重、加仓/再平衡规则由 Trading Profile 配置。长期 ETF 组合默认不做频繁交易；系统应区分核心持有、计划内加仓、TP/再平衡、防御增强和暂停加仓复核。
_Avoid_: ETF 日内交易池, ETF 全部同一种处理

**防御再平衡 ETF**:
长期 ETF 组合中用于风险环境恶化时再平衡的防御表达，例如医药、消费、公用事业或其它 profile 指定的防御 ETF。它们通常不是默认持续加仓对象，而是在 Risk Budget Score 下降、市场结构恶化、波动率上升、信用压力扩张或高 beta 暴露过度集中时用于降低组合波动和主题集中风险。
_Avoid_: 防御 ETF 永久高配, 风险好转仍机械加仓

**黄金主动配置 ETF**:
Trading Profile 可选择启用的黄金 ETF 表达。黄金 ETF 不只作为风险恶化时的防御资产，也可在利率宽松、实际利率下行、美元走弱、政策/财政不确定性或流动性环境改善但股票拥挤度偏高时作为宏观配置候选。是否启用黄金、使用哪些 ETF 和触发阈值都属于 profile 配置。
_Avoid_: 黄金只等于避险, 黄金和股票同一套触发规则

**宏观配置 Setup**:
由宏观环境、金融条件和组合配置需求驱动的 setup 类型，不以单票动量或行业 thesis 为主要来源。使用者可在 Trading Profile 中定义黄金、债券、外汇、商品或其它宏观配置表达。宏观配置 setup 需要同时评估实际利率、名义利率、美元、财政/政策不确定性、流动性环境、价格结构和组合对冲作用。
_Avoid_: 股票趋势 setup, 单纯避险买入

**主动个股中期交易**:
在核心 ETF 底仓之外，基于横截面动量、行业因子、宏观/金融条件、流动性和个股 thesis 形成的主动股票交易。它偏中期和长期投资倾向，不是高频短线，也不是纯粹长期买入后不管。
_Avoid_: 随机炒股, 纯日内交易, 永久持有

**主动交易池**:
主动个股中期交易使用的候选池集合，由 Trading Profile 配置。常见池包括动量池、大盘流动性龙头池、以及使用者指定的主题核心池。策略姿态评分决定每个池更适合趋势介入、均值回归介入、观察还是降风险，而不是决定是否只看某一个池。
_Avoid_: 单一股票池, 所有候选同优先级

**动量池**:
以 KVN Momentum Leaderboard 和其它横截面动量因子发现的新强势候选池。趋势策略时用于寻找强势新机会；均值回归策略时用于寻找前期强势股的高质量回踩或 reclaim，而不是盲目追高。
_Avoid_: 动量榜=买入名单

**大盘流动性龙头池**:
由大型指数权重股、流动性龙头或 profile 指定的大盘核心标的组成的候选/确认池。它既用于判断指数与流动性偏好，也可在好位置表达正股、LEAP 或其它低频交易。MAG7 是该池的一种常见配置，而不是插件默认必须使用的固定池。
_Avoid_: 大盘龙头永远无风险, 只做指数确认不交易

**主题核心池**:
使用者在 Trading Profile 中指定的主动集中研究/交易主题池。它可以是半导体、AI 硬件、存储、软件、消费、能源或其它主题。主题核心池可享有最高研究优先级，但仍需通过策略姿态评分、Crowding Score、个股 thesis、价格结构和组合风险过滤。
_Avoid_: 热门主题无条件集中, 只看叙事

**核心池持久性规则**:
Trading Profile 可以配置某些主题核心池不因短期动量榜缺席、KVN 排名下降或短期价格回撤而自动降权。对这类核心池，动量信号只用于提高关注优先级、提示趋势强度或辅助选择趋势/均值回归介入方式；核心池降级应由 thesis 恶化、长期结构破坏、流动性恶化、拥挤风险过高、组合风险超限或使用者明确移出触发。
_Avoid_: KVN 不在榜就移除核心池, 短期回撤等于 thesis 失效

**主动池复核频率**:
Trading Profile 中定义的主动池检查节奏。常见规则是 Core Names 每周深度复核一次、日常只报告重要变化；Watch Names 只在有催化、KVN/动量信号或价格接近关键区域时复核；Momentum Additions 入榜当天快速复核、连续入榜再深入；Dormant 默认不看，除非重新出现动量、催化、thesis 改善或价格结构修复。
_Avoid_: 每天全量长报告, Dormant 标的持续占用注意力

**核心池人工升级规则**:
Trading Profile 可以规定 Watch Names 或 Momentum Additions 不能由系统自动升级为 Core Names。系统可以根据 thesis 可持续性、行业位置、流动性、价格结构、复核次数和风险可管理性提示“建议用户考虑升级”，但最终 Core Names 变更必须由使用者明确确认。
_Avoid_: 模型自动升级核心池, 一次强势就变 Core

**多池标的规则**:
同一个标的可以同时属于多个主动交易池，并根据本次 setup thesis 选择工具表达。例如同一标的既可以作为主题核心池标的，也可以作为大盘流动性龙头池标的。工具选择应先看本次 thesis 来源：行业/主题主线 thesis 使用主题核心池表达规则；大盘流动性或大型龙头 thesis 使用大盘流动性龙头池表达规则。若多个 thesis 同时成立，系统应列出不同表达的风险差异，而不是自动替用户选择。
_Avoid_: 一个 ticker 只能属于一个池, ticker 固定工具表达

**池级工具表达规则**:
Trading Profile 中按主动交易池配置的工具偏好。一个使用者 profile 可以配置主题核心池默认正股，只有使用者主动声明时才评估 LEAP；大盘流动性龙头池可以主动提示 LEAP 机会，但必须要求高质量位置、合理 IV、足够期限和事件风险确认。工具表达规则不应写死在 public plugin 中。
_Avoid_: 所有池共用工具, 插件主动建议用户未启用的工具

**策略姿态分流**:
把量化策略姿态评分应用到不同主动交易池和长期 ETF 组合上的过程。趋势环境通常优先动量和主题核心池强势 setup；均值回归环境通常优先主题核心池、大盘流动性龙头池和 ETF 的高质量回踩/reclaim；防御环境优先长期 ETF 组合的对冲、防御增强和风险复核。使用者可以在 Trading Profile 或对话中声明覆盖默认分流，但系统应记录人工覆盖理由。
_Avoid_: 一个策略套所有标的

**策略姿态判定**:
用宏观金融数据、利率/收益率、流动性、市场结构、波动率和横截面因子判断当前更适合趋势策略、均值回归策略、平衡观察还是防御降风险。策略姿态判定决定候选池如何过滤和 setup 如何升级，不直接等于买卖指令。
_Avoid_: 单指标开关, 主观感觉切换策略

**量化策略姿态评分**:
策略姿态判定的标准输出，由 `Risk Budget Score`、`Trend Fit Score` 和 `Mean Reversion Fit Score` 三个 0-100 分数组成。`Risk Budget Score` 决定当前能否增加风险和风险预算大小；`Trend Fit Score` 判断强动量、突破、顺势 setup 的适配度；`Mean Reversion Fit Score` 判断回踩、超跌反弹、区间下沿和核心 ETF 加仓的适配度。
_Avoid_: 只写看多看空, 无阈值策略建议

**Risk Budget Score**:
量化策略姿态评分中的市场风险预算分，用来判断当前市场是否允许加风险。它应综合市场结构、NDX/RUT 比值、板块 ETF 轮动、机构偏好、利率/美元压力、流动性/信用条件、波动率和当前组合热度/事件风险，而不是只看单个指数涨跌。
_Avoid_: 仓位建议, 自动调仓

**Trend Fit Score**:
量化策略姿态评分中的趋势适配分，用来判断趋势跟随、强动量、突破回踩、行业龙头和弹性个股策略是否应该优先。它需要同时参考大盘趋势、NDX/RUT 比值、行业 ETF 相对强弱、横截面动量、行业广度、价格结构和跟随性。
_Avoid_: 追高信号, 单票强就是趋势环境

**Mean Reversion Fit Score**:
量化策略姿态评分中的均值回归适配分，用来判断回踩买入、强票支撑反弹、核心 ETF 加仓、区间下沿反转和过度悲观后的反弹是否应该优先。它需要确认大周期没有明显破坏，且短期过热/超跌/波动回落条件成立。
_Avoid_: 接飞刀, 下跌就抄底

**机构偏好代理指标**:
用指数比值、相对表现和板块 ETF 轮动观察机构资金当前偏好。v1 核心观察包括 NDX ÷ RUT、SMH 或 SOXX ÷ SPY、XLK ÷ SPY、HYG ÷ LQD，以及 TLT 或 IEF 趋势。NDX ÷ RUT 上行通常表示资金更偏大盘成长/流动性龙头，下降通常表示小盘扩散或成长抱团降温；必须和半导体、科技、信用风险偏好和利率压力共同确认。
_Avoid_: 主观猜资金, 单一板块涨跌

**标的拥挤程度指标**:
衡量单个标的或主题是否已经被过度交易、过度追捧或风险回报变差的指标集合。v1 应优先关注权重数据、资金流驱动因子、对冲基金在相关行业的净暴露，以及主题对 S&P500 权重/收益贡献的集中度；再结合价格相对 20/50/200 EMA 的延伸、ATR/波动率分位、成交/换手、KVN 入榜热度和期权 IV/偏度/成交/OI 拥挤。标的拥挤程度用于降权、等待回踩、缩小仓位或提高触发严格度，不等于直接做空。
_Avoid_: 热门就空, 涨多了就卖

**Crowding Score**:
标的拥挤程度指标的标准评分，0-100。Crowding Score 先按主题/行业级别判断，再下钻到单票级别。高分表示该主题、行业或标的可能已经被资金、指数权重、期权仓位或叙事过度拥挤，新增交易需要更高质量位置、更小仓位或等待回踩。Crowding Score 是风险修正项，不是独立买卖信号。
_Avoid_: 拥挤=立刻卖出, 拥挤=做空信号

**Flow-Driven Factor**:
用资金流、被动/主动配置、ETF 创建赎回、行业/主题净流入、机构持仓变化和衍生品流量衡量某个主题或标的上涨是否主要由资金流驱动的因子。它用于判断趋势的可持续性和拥挤风险，不能单独证明基本面改善。
_Avoid_: 资金流=基本面, 短期流入=无风险趋势

**行业净暴露**:
机构或对冲基金在某个行业的净多/净空暴露，例如半导体净暴露。它用于判断行业交易是否拥挤、是否还有增量买盘、以及回撤时是否存在集中减仓风险。若数据来自滞后披露或第三方估算，必须标注时效性和置信度。
_Avoid_: 估算暴露当实时事实

**指数权重贡献**:
某个行业、主题或少数龙头对 S&P500 等指数权重、收益和估值变化的贡献。半导体占 S&P500 权重和收益贡献过高时，可能说明指数上涨依赖单一主题，风险预算和新增高 beta 仓位需要更谨慎。
_Avoid_: 指数涨=市场全面健康

**拥挤度主题列表**:
Crowding Score 优先覆盖 Trading Profile 中配置的活跃主题群。主题列表用于决定哪些主题先进入拥挤度、flow、指数权重贡献和行业净暴露分析，不代表其它行业永远不分析。半导体、AI 硬件、存储、AI 应用/软件和 MAG7 可以作为一个使用者 profile 的示例配置，而不是 public plugin 的固定默认。
_Avoid_: 全行业平均覆盖, 永久固定主题

**主线交易池**:
横截面筛选中的优先交易主题池，由 Trading Profile 配置，用于主动寻找中期趋势机会、回踩机会和高质量 setup。主线交易池中的标的仍需经过策略姿态评分、Crowding Score、个股 thesis、价格结构和组合风险过滤。
_Avoid_: 无条件买主线, 热门主题即交易计划

**确认/对照池**:
横截面筛选中的市场确认主题池，由 Trading Profile 配置，用于判断资金是否从主线扩散到相邻主题、是否继续抱团大盘流动性龙头、或是否发生主题轮动。确认/对照池不默认直接产生交易候选，除非其动量、thesis、价格结构和风险预算也满足主线交易池同等标准。
_Avoid_: 所有主题同等交易, 对照信号直接下单

**周度市场复盘与下周交易计划**:
Active Market Plan 的 `deep_update`。它通常发生在周末或周初，用于复盘上周交易，分析当前盘面、宏观、利率、政策、新闻和重大事件，预览未来事件风险，重建动量强弱榜单，并刷新 setup pool。它不是另一套 workflow。
_Avoid_: 泛泛周报, 每周另起炉灶

**每日盘面追踪**:
Active Market Plan 的 `quick_update` 或轻量 `trigger_update`。交易日内或盘前/盘中把当前市场状态与 `market-plan.md` 对照，快速更新盘面、宏观、政策、新闻、事件预览、动量榜单、setup 状态和关键点位。每日盘面追踪可以发掘机会，但机会必须落回已有主题或新建 `candidate` setup。
_Avoid_: 随机盘中扫股, 新闻驱动追单

**信息验证**:
用原始来源、交叉来源、当前市场数据和反方证据检查交易想法的关键事实和假设。
_Avoid_: 确认偏误, 找支持材料

**交易计划准备**:
信息验证之后、预备交易计划之前的正式阶段。它先把宏观、金融条件、政策事件、行业强弱、个股 thesis/counter-thesis 和组合风险压缩成截面候选池，再从截面候选池中寻找具备价格结构的 `candidate setup`。交易计划准备写入 Active Market Plan 的 `market_context`、`theme`、`candidate setup`、`evidence_needed`、`invalidation` 和 `next_check`。交易计划准备默认只产出 `candidate` 或 `active` setup，不直接产出 `approaching` 或 `triggered`。
_Avoid_: 宏观报告, 直接交易信号

**截面候选池**:
交易计划准备中的中间产物。它通过宏观/金融条件、政策事件、行业/个股投研、相对强弱、流动性和组合风险等因子筛出值得继续找 setup 的标的或主题。截面候选池写入 Active Market Plan 的 `Trade Plan Preparation` 区块下的 `Cross-Section Candidate Pool`，位置在宏观/利率/政策/新闻之后、事件预览和主题/setup 之前。截面候选池不是 Setup Pool；只有当标的在大周期环境、价格结构、触发区域、失效条件和风险预算上足够清楚时，才转化为 `candidate setup`。
_Avoid_: 买入名单, setup pool, 直接交易计划

**交易计划准备输入层**:
交易计划准备 v1 的固定输入模块，包括 `Macro Regime`、`Financial Conditions`、`Policy/Event Risk`、`Industry/Sector Strength`、`Company Thesis Check` 和已计算的 `KVN Momentum Leaderboard`。这些模块共同决定哪些主题或标的进入截面候选池。KVN 榜单是独立分析能力；交易计划准备只消费它的最新结果和变化摘要，不在同一步临时全量重算。
_Avoid_: 原始新闻列表, 未分层研究摘要, 混入未建模动量排名

**计划准备输入结论**:
交易计划准备输入层中每个模块的统一输出形状。每个模块都应输出 `read`、`supports`、`pressures`、`blocks`、`evidence` 和 `next_check`，用来说明它如何影响截面候选池。计划准备输入结论不是长报告；它只回答哪些主题/标的被支持、被压制、被阻止进入 setup pool，以及下一步需要验证什么。
_Avoid_: 五篇独立报告, 新闻摘要, 不可执行观点

**动量候选池**:
基于独立 KVN 量化动量模型生成的候选池。它由每日脚本计算并写入本地 SQLite 数据库，默认只向用户展示 Top10，但全 universe 可查询。动量候选池是研究优先级和截面候选源，不是 setup pool，也不是买入名单；进入交易计划前仍需经过宏观/利率环境、行业/个股深研、价格结构和组合风险过滤。
_Avoid_: 手工动量榜, 买入名单, 未验证排名

**大周期环境判定**:
交易计划准备中的第一步。先用 4H、1D、1W 判断市场环境是上涨、震荡还是下跌，再决定交易偏见、允许的策略和哪些 setup 值得进入候选池。
_Avoid_: 小周期先行, 触发信号替代市场环境

**市场环境策略映射**:
大周期环境判定后的策略约束。上涨环境优先顺势做多，包括回踩做多、突破回踩、强势股/ETF、LEAP、2x 产品和 ETF 加仓候选；震荡环境避免追高杀跌，优先区间边界、失败突破反向、降低仓位和确认后的 0DTE 边界交易；下跌环境以防御为先，减少新增多头，做多只允许反弹或超短线，空头/put 只能在大周期背景和风险控制允许时进入候选。
_Avoid_: 不分环境套同一策略, 低周期信号决定整体偏见

**小周期执行观察**:
在大周期环境判定之后使用 1H 及以下时间框架观察入场区域、信号 K、二次入场、失败突破和风险回报。小周期只能用于执行观察和触发确认，不能单独推翻大周期交易偏见。
_Avoid_: 1H 以下直接定方向, 低周期噪音

**K 线 Setup 分析**:
基于 price action、20 EMA、50 EMA、200 EMA 和多时间框架判断交易想法是否具备可执行的入场、止损和退出结构。Setup 分析决定“是否有可交易形态”，不替代基本面或宏观验证。
_Avoid_: 技术指标信号, 图形迷信

**Price Action**:
使用 Al Brooks 风格的高层价格行为语言描述趋势、交易区间、突破、失败突破、回调、二次入场、反转和测量目标。Price Action 不提供确定性预测。
_Avoid_: 必胜形态, 神奇指标

**择时技术体系**:
Trading Profile 中配置的技术择时框架。一个常见配置是 Price Action 和 20/50/200 EMA。系统不应把 RSI、MACD、布林带等额外技术指标硬编码为默认；若使用者主动要求，可以作为补充观察，但不能替代 profile 指定的主择时框架和多时间框架背景。
_Avoid_: 指标堆叠, 低周期指标信号

**动量强弱排行榜**:
基于量化因子筛选出的相对强弱标的列表，用于优先发现主动交易候选标的。当前规范化形态是 `KVN Momentum Leaderboard`：按 `KVN 分数` 降序排序，默认显示 Top10，保留 `Rank vs S&P500`、`KVN P`、`当前是否 S&P500` 和 Top10 入榜记忆字段。排行榜是研究优先级，不是直接买卖指令。
_Avoid_: 买入名单, 黑箱排名

**KVN Momentum Leaderboard**:
每天由本地脚本或上游脚本计算的 ticker 级动量排行榜。主显示字段贴近学习对象：`Rank vs S&P500`、`Ticker`、`KVN 分数`、`KVN P`、`当前是否 S&P500`、`连续入选Top10天数`、`近20日入选Top10次数` 和 `上次入选Top10时间`。skill 调用时直接读取最新数据库结果，而不是临时抓取并全量计算。Agent 只能读取、查询和解释脚本结果，不能重新排序、重新打分，不能把行业、主题、资产类别或叙事桶写成 KVN row。
_Avoid_: 临时聊天榜单, 每次手算, 全量表格轰炸

**KVN 分数**:
KVN 动量榜的主排序分数。它参考 SPMO 式风险调整动量思想，但服务于日更交易候选筛选：个股价格动量、成交量/波动质量和赛道邻域动量共同决定分数。`KVN 分数` 是相对强弱排序，不是收益预测概率。
_Avoid_: 预测收益率, 买入信号

**KVN P**:
当前 `KVN 分数` 相对该标的过去 60 个交易日 KVN 分数分布的时间序列百分位。`KVN P` 辅助判断分数是否处在该标的近期高位，但不替代 `KVN 分数` 排序。
_Avoid_: 横截面排名, 胜率概率

**Rank vs S&P500**:
把任意通过流动性过滤的股票放入 S&P500 动量分布中比较得到的相对排名。非 S&P500 标的也可以有 `Rank vs S&P500`，因此该字段不是“当前是否 S&P500”的同义词。
_Avoid_: 全 universe 排名, 指数成分状态

**赛道邻域动量**:
KVN 中的 `N`。它表示标的所在交易主题、行业、peer group 或相关 ETF/篮子的整体动量和广度，例如 AI infrastructure、Memory/Storage、Semicap Equipment、Foundry、MAG7 Platform、Power/Grid/Nuclear 等。赛道邻域动量是量化/半量化分组信号，不是主观叙事。
_Avoid_: Narrative, 新闻热度, 手工故事

**Top10 入榜记忆**:
KVN 动量榜记录标的是否连续出现在每日 Top10、近 20 个交易日入选 Top10 的次数，以及今天之前上一次入选 Top10 的日期。它用于区分稳定龙头、反复回榜和首次进入榜单的标的。
_Avoid_: 全 universe 出现时间, 今天日期冒充上次入榜

**多因子 Alpha 榜**:
由独立 Alpha Lab 在每个有效交易日生成的 ticker 级截面排行榜。它以动量为核心，同时允许经过验证的量价、波动、流动性、行业/主题 ETF、市场环境和 point-in-time 基本面因子进入模型。全量合格股票可查询，默认展示 Top10，Top20 进入研究候选池，Top5 进入优先深挖。排行榜只提高研究优先级，不直接生成交易 setup 或订单。`KVN Momentum Leaderboard` 是旧兼容名称，不是新模型的权威术语。
_Avoid_: KVN 复刻, 买入名单, Agent 临时重排

**Alpha Score**:
多因子 Alpha 榜的正式排序分数。1.0 的 Bayesian champion 使用未来 20 个交易日相对 SPY 超额收益的后验预期与预测不确定性构造风险调整分数；LightGBM challenger 独立生成后台截面排名。模型、因子、数据和训练窗口必须有版本，Agent 只能读取和解释已生成分数。
_Avoid_: 主观打分, 未校准胜率, 新闻热度排名

**历史分位**:
当前 Alpha Score 相对同一标的自身滚动历史分布的 percentile。它描述当前分数是否处于该标的历史高位，不是横截面排名，也不是未来跑赢概率。
_Avoid_: Alpha Rank, P(20D 超额收益 > 0), 胜率

**Alpha 轨迹状态**:
不改变原始 Alpha Rank 的派生状态，用于描述标的进入、上升、持续留存或滑出候选池的路径。标准状态为 `new`、`strengthening`、`persistent` 和 `fading`。交易研究优先读取当前 Top5，并保留 Top20 中持续性强或排名快速改善的标的。
_Avoid_: 二次重排, 主观升降级, 单日排名等于趋势

**分析运行快照**:
一次成功分析在指定数据截止时间、标的/范围、分析类型、主时间框架、策略周期、模型版本和输入版本下的完整结构化结果。每次增量更新仍保存完整快照，使未来运行不依赖聊天记录或拼接多份 delta 才能恢复上下文。
_Avoid_: Chat 作为事实库, 只保存最新文字, 无版本覆盖

**分析增量**:
当前分析运行与同一稳定键的上次成功快照之间的结构化差异。差异状态为 `unchanged`、`updated`、`invalidated` 或 `added`。默认用户输出只展示变化、原因、计划影响和下一次检查，但模型或规则版本变化时必须全量重算。
_Avoid_: 全量重复报告, 不说明变化原因, 跨时间框架误对齐

**模型概率边界**:
数字概率只允许来自可回测、样本外验证并记录模型版本的输出。1.0 可展示 Bayesian champion 的 `P(20D 超额收益 > 0)`，但必须标记 `Experimental` 和不确定性。宏观、新闻、Al Brooks Price Action、EMA、支撑压力和 Agent 综合判断只能给结构状态、条件、证据强弱与明确行动结论，不能伪装成数字概率。
_Avoid_: 主观上涨概率, 把历史分位当胜率, 未校准 LightGBM predict_proba

**异常期权信号**:
期权市场中显著偏离常态的成交、未平仓、隐含波动率、偏度或大单行为。异常期权信号是线索，需要与价格、基本面、事件和流动性校验。
_Avoid_: 期权内幕信号, 无风险信号

**预备交易计划**:
在下单前形成的可执行 setup 计划，包含标的、方向、交易工具、分析时间框架、触发时间框架、入场触发、止损、目标、仓位、失效条件和组合风险影响。
_Avoid_: 想法, 临时下单理由

**盘面分析时间框架**:
用于判断市场结构、趋势、交易区间、关键支撑阻力和多时间框架背景的时间框架。它可以高于实际触发时间框架。
_Avoid_: 入场时间框架

**交易触发时间框架**:
用于判断具体入场、失效、止损和执行信号的时间框架。它必须在预备交易计划中明确，方便盘中 Setup 扫描执行。
_Avoid_: 背景时间框架

**交易工具类型**:
预备交易计划使用的交易工具类别，包括 LEAP call/put、2x 杠杆产品、ETF、0DTE QQQ 期权等。交易工具类型影响时间框架、仓位、止损方式、风险暴露和复盘统计。
_Avoid_: 标的一概而论

**工具时间框架规则**:
交易工具类型决定默认盘面分析时间框架和交易触发时间框架。用户可以覆盖默认值，但系统应先按工具时间框架规则生成预备交易计划和盘中 Setup 扫描配置。
_Avoid_: 所有产品共用一个时间框架

**默认工具时间框架表**:
Trading Profile 中配置的工具时间框架规则。public plugin 只提供可编辑模板和示例，不把某个使用者的时间框架设为所有人的默认。一个中期主动交易 profile 示例可以是：长期 ETF 核心仓使用 1W/1D 分析、4H/1D 触发；宏观配置 setup 使用 1W/1D 分析、1D/4H 触发；主动个股中期交易使用 1W/1D/4H 分析、4H/1H 触发；LEAP call 使用 1W/1D 分析、1D/4H 触发；2x ETF 使用 1D/4H 分析、4H/1H 触发；0DTE QQQ 使用 1D/4H/1H 背景、15m/5m 触发。
_Avoid_: 日内信号触发长期配置, 低周期决定宏观配置

**实际交易记录**:
真实发生的交易事实记录，包括入场、出场、时间、价格、仓位、盈亏、执行偏差和当时依据。可用 broker 成交记录作为事实来源，但入场理由、信号 K、信心和经验必须通过交互式追问补全。
_Avoid_: 事后解释, 记忆中的交易

**券商成交事实**:
来自 IBKR、Longbridge 或其它 broker source 的真实成交、订单或账户记录，例如标的、方向、数量、价格、手续费、时间和盈亏。它用于减少手工录入错误，但不能替代用户对盘面背景、入场理由和执行质量的复盘。
_Avoid_: 自动复盘结论, 经纪商即完整日志

**持仓日报**:
交易运营 automation 的一种，定时从授权 broker source 只读读取当前持仓、账户风险、现金/保证金、未实现盈亏、集中度和工具暴露，并生成简洁中文摘要和可视化快照。持仓日报参考 Longbridge 类持仓提醒体验，但在本 plugin 中保持 broker-agnostic，优先使用 Longbridge 或 IBKR 的只读来源，不创建或修改订单。
_Avoid_: 自动调仓, 账户日报流水账, 手工交易表

**持仓日报快照**:
持仓日报生成的派生展示产物，例如权重条形图、主题/行业暴露图、PnL 贡献图、期权到期风险提示和需要用户决策的事项。快照可以保存到 runtime 作为复盘材料，但不能包含不必要的逐笔成交明细或账户凭证。
_Avoid_: 原始券商导出, 私密账户备份

**交互式交易复盘采集**:
一种一问一答的复盘填写流程，用于把实际交易补全成结构化记录和可读复盘。它会追问入场理由、盘面背景、信号 K、辅助信号、信心、执行偏差、离场质量、错误标签和经验。
_Avoid_: 自由聊天复盘, 只记录盈亏

**下单后交易记录**:
交易刚下单或刚成交后进行的第一阶段复盘上下文采集。重点是锁定当时事实和入场依据：交易来自哪个计划、看到什么盘面背景、什么信号 K、触发时间框架、信心、止损、目标、仓位和风险。客观成交事实默认从 broker-live source 读取；本地只保存用户确认后的复盘摘要或可视化快照。
_Avoid_: 等交易结束后再回忆入场理由

**结束后交易复盘**:
交易平仓或失效后进行的第二阶段复盘。重点是出场理由、执行偏差、盈亏、R 倍数、是否遵守计划、错误标签、经验和下次规则。客观结果优先从 broker-live source 读取；本地只保存结构化复盘摘要、图表或统计快照。
_Avoid_: 把盈亏当成唯一质量判断

**复盘追问序列**:
交互式交易复盘采集使用的问题顺序。每个问题都应服务于写入 `trades.csv` 或 `reviews.md`，不能为了聊天而追问。
_Avoid_: 随机追问

**本地日分区记录**:
按交易日期在本地保存观察清单、预备交易计划、复盘摘要、持仓日报快照和图表产物。Active Market Plan 当前状态在 `{runtime_dir}/market-plan.md`，每日变化轨迹在 `{runtime_dir}/updates/YYYY-MM-DD.md`，日分区记录在 `{runtime_dir}/daily/YYYY-MM-DD/`。默认 `runtime_dir` 是 `~/Documents/dailytrades-runtime`。本地日分区记录不应成为 broker 逐笔交易事实的长期 source of truth。
_Avoid_: 临时聊天记录, 未归档输出

**盘中分析**:
基于当天预备交易计划，在交易时段内同步观察多个标的和多个时间框架图表，持续更新价格行为、触发条件、失效条件和风险暴露。盘中分析用于辅助执行，不等同于自动交易。
_Avoid_: 自动交易, 盯盘聊天

**盘中 Setup 扫描**:
盘中分析中的核心能力，用于在 Active Market Plan 的 setup pool 中同步检查当前盘面是否出现计划内信号或合适的 K 线 setup。它帮助用户同时兼顾多个 setup，但不主动创造没有计划依据的新交易。
_Avoid_: 全市场扫股, 自动下单信号

**盘中扫描状态**:
盘中 Setup 扫描对每个 setup 输出的状态，包括 `candidate`、`active`、`approaching`、`triggered`、`invalidated`、`needs_review` 和 `completed`。这些状态用于提醒用户关注计划进展，不等同于买卖指令。
_Avoid_: buy, sell, 自动交易信号

**Triggered 状态**:
盘中扫描状态之一，表示 setup 关键价位已经到达或突破，并且执行时间框架出现计划内 K 线 setup 确认。`triggered` 只代表需要人工决策和 execution check，不等于可以下单。单纯触及价格只能算 `approaching`，不能算 `triggered`。
_Avoid_: 触价即买入

**触发确认规则**:
判断盘中计划是否进入 `triggered` 的默认规则。它要求价格到达计划关键区域，执行时间框架出现计划内 setup，信号 K 至少达到中等质量，不明显逆着更高时间框架背景，并且触发后仍满足最低风险回报。
_Avoid_: 单一价格提醒, 无背景信号

**工具触发严格度**:
不同交易工具类型对应不同的触发确认严格度。0DTE QQQ/SPY 期权最严格，2x/3x 杠杆 ETF 次之，普通 ETF/股票 swing 居中，LEAP call/put 更重视日线和周线背景，允许较慢确认。工具触发严格度可以覆盖默认规则，但不能取消失效条件和风险控制。
_Avoid_: 所有产品共用同一触发标准

**Invalidated 状态**:
盘中扫描状态中优先级最高的状态，表示原预备交易计划的失效条件已经触发。计划一旦进入 `invalidated`，后续即使出现新的入场形态，也不能自动恢复为 `triggered`，需要人工复核或新建计划。
_Avoid_: 失效后继续硬做

**Approaching 状态**:
盘中扫描状态之一，表示价格或结构正在接近预备交易计划中的关键区域，但尚未出现执行时间框架的 K 线 setup 确认。`approaching` 的敏感度应按交易工具类型调整。
_Avoid_: 接近就入场

**Needs Review 状态**:
盘中扫描状态之一，表示系统无法给出清晰计划内状态，需要用户人工复核。典型触发包括行情缺失或延迟、多时间框架冲突、预备交易计划字段不完整、计划外重大新闻或宏观事件、接近或触发时组合风险超限，以及计划失效后又出现新的强形态。`needs_review` 是人工复核提醒，不是交易信号。
_Avoid_: 模糊信号, 系统硬判

**盘中注意力优先级**:
盘中 Setup 扫描对多个 setup 排序的规则。状态优先级从高到低为 `invalidated`、`triggered`、`needs_review`、`approaching`、`active`、`candidate`、`completed`；同一状态内按交易工具紧急度排序，通常为 0DTE 期权、短周期期权、杠杆 ETF、普通 swing、LEAP。注意力优先级用于安排用户先看什么，不代表交易建议强弱。
_Avoid_: 交易推荐排名, 自动下单优先级

**盘中监控列表**:
当天需要同步观察的标的、时间框架、关键价位、入场触发、止损、目标和备注。它来自预备交易计划，是盘中分析的输入。
_Avoid_: 普通观察清单

**Google Sheets 同步**:
可选展示层，用于同步精炼摘要、持仓日报快照索引或非敏感统计结果。Google Sheets 不再承担交易记录维护职责，也不保存逐笔 broker facts；如后续启用，只能是用户确认后的只读摘要镜像。
_Avoid_: 唯一数据源, 双向同步, 手动交易记录表

**交易复盘**:
对实际交易记录进行结构化评估，区分判断质量、执行质量、运气、仓位和系统问题。
_Avoid_: 自责, 炫耀盈亏

**胜率验证**:
用交易记录统计交易系统在特定 setup、标的类型、市场环境和执行规则下的表现。胜率验证需要同时看盈亏比、回撤、样本量和一致性。
_Avoid_: 单看胜率, 事后挑样本

**R 倍数**:
以每笔交易的计划风险为单位衡量结果的统计口径。R 倍数用于比较不同仓位和不同产品的交易质量，不能只用盈亏金额替代。
_Avoid_: 只看 PnL

**最小可统计单元**:
交易日志中的一行记录，代表一笔可独立计算风险、盈亏和复盘标签的交易或成交。分批成交应拆行，并用同一个 trade_id 关联。
_Avoid_: 一个单元格放多个价格

**结构化复盘字段**:
从原始复盘文本中拆出的 setup、入场、出场、错误标签和经验字段。它保留复盘可读性，同时支持统计错误频率和系统优化。
_Avoid_: 只有长文本复盘

**Plugin-first 系统**:
优先把交易投研系统实现为 Codex 可直接调用的插件和技能，而不是先建设独立前端应用。这样 agent 可以直接使用工作流、脚本、模板和外部工具，不需要用户自己配置模型层。
_Avoid_: 前端优先系统, 独立 SaaS

**图表产物**:
由插件或 Codex 按需生成的临时图表页面、图片或报告片段，用于 K 线 setup、多时间框架和均线结构分析。图表产物不是长期维护的前端应用。
_Avoid_: Dashboard, 常驻前端
