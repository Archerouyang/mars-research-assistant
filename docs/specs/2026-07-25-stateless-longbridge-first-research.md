# 无状态 Longbridge 优先研究重构

状态：已确认，待拆分实施。

## Problem Statement

火星投研助手目前仍把一次研究请求绑定到 private runtime、Daily Ops、持仓读取、旧券商路径、持久化工件、manifest、Gallery 与跨轮计划。这使一个本应可直接使用的研究 Skill 需要大量无关环境，输出链路又长又脆弱。

使用者需要的是可靠、快速、可解释的一次性研究：先获得宏观事件与完整的 Macro Regime Board，或直接研究一个标的的基本面、行业和公司事件；仅在询问趋势、点位、入场、减仓或交易计划时才获得 Price Action Board。Longbridge 应在用户明确启用且授权有效时提供优先的结构化数据，但没有 Longbridge 账号或权限的用户也必须获得完整可用的便携路径。

## Solution

将火星投研助手重构为无状态的一次性研究 Skill。每次运行只采集当前请求所需的数据，返回中文 Markdown 和当前请求所需的一个自包含 HTML Board；不读取或写入 runtime、缓存、计划、历史、账户或工件注册表。

所有路径汇聚到 `stateless_research_run` 这一主验收 seam：它接收研究意图和本次数据源选择，完成字段获取、批量懒回退、时间与语义校验、完整性门槛、Markdown 和可选 Board 交付。它不依赖 gateway、持久化状态或 ArtifactPacket。

## User Stories

1. 作为交易研究者，我希望安装后即可运行一次研究，而不必创建 runtime、计划或本地数据库，以便快速获得当前结论。
2. 作为首次使用者，我希望 Skill 只读检查 Longbridge CLI 的授权状态，以便知道更完整的数据路径是否可用而不暴露账户资料。
3. 作为 Longbridge 用户，我希望即使授权有效仍由我决定本次是否使用 Longbridge，以便数据源选择始终是显式的。
4. 作为未使用 Longbridge 的用户，我希望直接获得 yfinance 加 Web Search 的便携研究路径，以便不因账号或 CLI 缺失而被阻塞。
5. 作为使用 Longbridge 的用户，我希望 Longbridge 对语义等价的结构化字段优先，以便获得更稳定、快速的数据体验。
6. 作为研究者，我希望只有缺失或校验失败的字段才触发备用来源，以便避免重复请求和不必要的延迟。
7. 作为研究者，我希望每个数值和事件都有 `source` 与 `as_of`，以便识别数据来源和时间。
8. 作为宏观用户，我希望先得到未来七天和最近二十四小时重大事件的 Markdown 简报，以便理解随后状态判断的事件上下文。
9. 作为宏观用户，我希望 Macro Regime Board 仅在所有冻结字段完整且时间口径有效时生成，以便不会把缺口伪装成完整状态。
10. 作为宏观用户，我希望 Board 显示 2Y、10Y、30Y、VIX、VIX3M、DXY、WTI、黄金、HYG/LQD 和 NDX/RUT，以便快速判断利率、波动、美元、商品、信用与风格。
11. 作为宏观用户，我希望 NDX/RUT 与 HYG/LQD 均显示最近三十个共同交易日折线，以便查看相对强弱而非只看单日变化。
12. 作为标的研究者，我希望点名标的时只研究公司基本面、行业和公司事件，以便避免无关宏观、持仓或对标公司工作拖慢结论。
13. 作为标的研究者，我希望 Fundamentals 视图展示最近五季、最近三完整财年和当前估值，以便将趋势、资产负债与估值放在同一研究中。
14. 作为标的研究者，我希望 Industry 与 Events & Catalysts 只展示有明确经营传导的近三十日事实和未来九十日已知事件，以便不被新闻标题流淹没。
15. 作为标的研究者，我希望经济上不适用的字段显示 `N/A`、无事件显示 `none_found`、来源缺失显示 `data_gap`，以便正确理解不确定性。
16. 作为交易者，我希望只有明确询问走势、点位、入场、减仓或交易计划时才生成 Price Action Board，以便基本面研究不被技术面强制阻塞。
17. 作为交易者，我希望 Price Action 只使用一条来源一致的 120 个已完成交易日的复权日线序列，以便 EMA20、EMA50、ATR14、关键位和情景可以复核。
18. 作为交易者，我希望新上市或历史不足 120 个完成交易日的标的不生成 Price Action Board，以便不把不足样本包装为技术结论。
19. 作为使用者，我希望 Board 保留现有视觉语言但以单一自包含 HTML 直接交付，以便无需 manifest、Gallery 或宿主页面即可查看。
20. 作为贡献者，我希望 README 用 `uv` 和固定版本的 `requirements.txt` 给出唯一 Python 环境安装路径，以便环境可复现且不污染全局 Python。
21. 作为贡献者，我希望 Longbridge CLI 的安装与 OAuth 登录保持可选且显式同意，以便 Python 环境和券商 CLI 之间没有隐式耦合。
22. 作为维护者，我希望旧 runtime、持仓、IBKR、自动化、ArtifactPacket、Gallery、交易统计和旧 fixtures 被彻底删除，以便没有不可达的兼容代码继续影响设计或安装体积。

## Implementation Decisions

- `stateless_research_run` 是唯一主行为与主验收 seam。它同步完成一次请求；运行结果只在内存或调用者提供的临时目录存在。
- 数据源预检只读取 Longbridge CLI 是否存在及授权是否有效，绝不读取或展示账户、持仓、订单、凭据或 token。授权有效后仍需本次用户选择才能使用 Longbridge；未授权时可询问是否安装并登录 CLI，绝不静默安装或登录。
- Longbridge Profile 优先使用 Longbridge 的结构化报价、历史日线、公司、财务报表、业务分部、估值、日历和新闻发现能力。Portable Profile 使用 yfinance 的等价结构化字段，并使用 Web Search 发现候选事件与原始资料。
- 回退采用批量懒回退：主源按数据集请求并校验，只有缺失或校验失败字段才访问 yfinance 或官方来源；不得为交叉比较并行重复抓取。语义、单位和时间等价后，字段可混合来源，但每项必须显示实际来源和时间。
- Web Search 是发现层。会改变宏观、行业或公司结论的事件，必须以原始公告、监管披露、官方日历或公司 IR 页面取证。聚合新闻不能单独构成重大事实证据。
- 市场字段和三十日折线截至最近一个已完成的美国交易日。财政部收益率保留最新官方发布日期而不伪造为同日。基本面保留报告期末和披露日，事件保留发生或发布时间，Price Action 排除未完成日线。
- Macro Event Brief 覆盖未来七日的央行决议、CPI/PCE/PPI、就业、GDP、PMI、重大财政或关税政策、长期美债拍卖，以及最近二十四小时内明确影响 Macro v1 字段的已发生重大事件。Macro Regime Board 仅纳入最改变判断的三至五项事件。
- Macro v1 字段固定为美国财政部 2Y/10Y/30Y，VIX 与 VIX3M 原始读数，DXY，WTI，COMEX 黄金，HYG/LQD 和 NDX/RUT。WTI、黄金、DXY 分别固定为 `CL=F`、`GC=F`、`DX-Y.NYB` 的语义；HYG/LQD、NDX/RUT、VIX/VIX3M 使用 Longbridge 的相同已完成日线，缺口回退 yfinance。利率只使用美国财政部同一发布日期的官方曲线。
- Macro Regime Board 只有全部冻结字段取得且通过时间校验才生成。缺少任何必需字段时交付 Macro Event Brief 和明确的字段缺口，而不是空卡片、代理值或半成品 Board。
- Instrument Research Board 固定为 Overview、Fundamentals、Industry、Events & Catalysts 四个视图。它不包含 OHLCV、价格形态、流动性、技术指标、setup、持仓、同业表或同业事件。
- Instrument Fundamentals 固定为身份、交易所、币种、行业、业务分部、最近五季与三完整财年的收入、同比、毛利率、营业利润率、净利率、稀释 EPS、经营现金流、资本开支、FCF、现金、总债务、净现金/债务，以及当前市值、Trailing/Forward P/E、P/S、P/B、EV/EBITDA。
- Instrument Industry 固定为价值链位置、产品市场、需求、供给/产能/库存/定价、周期位置、竞争结构和监管风险，以及近三十日发生与未来九十日已知且具有收入、利润率、资本开支或风险传导的行业事件。
- Instrument Events & Catalysts 固定为近三十日与未来九十日的财报/指引/经营数据、产品、客户或供应商、合同、资本开支、融资、回购、分红、并购、监管、诉讼、管理层、申报、投资者日与已确认催化剂。每项包含时间、事实状态、来源、预期证据、财务传导和失效条件。
- Instrument Research Board 只在公司身份不唯一或完全没有可用财务报表时阻塞。其它字段按 `N/A`、`none_found` 或 `data_gap` 明确交付并降低置信度。
- Price Action Board 只在用户明确需要技术时生成。它使用 120 根完成日线、前复权 OHLCV、EMA20、EMA50、ATR14、关键支撑/阻力、区域、当前结构、牛/基准/熊情景和失效条件。Longbridge 使用前复权日线，缺口回退 yfinance 自动复权日线；OHLCV 和全部派生指标不可跨来源混用。
- Board 直接渲染为单个自包含 HTML。保留 Macro Regime、Instrument Research、Price Action 的视觉风格，移除 ArtifactPacket、ResearchResult、manifest、内容哈希、Gallery、PNG 导出和持久化工件协议。
- Python 依赖由 `uv pip compile` 生成完整、精确版本固定的 `requirements.txt`；README 以 `uv` 隔离环境作为唯一受支持安装方式。Longbridge CLI 不属于 Python 依赖树。
- 删除所有 runtime、Daily Ops、自动化、账户与持仓、IBKR、旧 Longbridge gateway、KVN/Alpha、交易复盘、旧工件管线、旧 source contract、旧模板、旧 fixtures、旧 staging Gallery 与旧产品截图。历史 ADR 保留但标注为被当前无状态决策取代，且不再被使用者文档引用。

## Testing Decisions

- 以 `stateless_research_run` 的外部行为为主测试层。测试注入受控的 Longbridge CLI、yfinance、财政部与事件取证响应；不依赖真实账号、实时网络、系统时钟或已有 runtime。
- 每项成功路径断言 Markdown、字段来源、时间、完整性状态和恰当的一个自包含 HTML Board；失败路径断言具体数据缺口或 blocker，而非内部异常。
- 测试 Longbridge 授权预检只暴露可用性布尔结果；测试授权有效但未经用户选择时不使用 Longbridge；测试拒绝或缺失授权后进入 Portable Profile。
- 测试批量懒回退仅请求缺失字段，且不为比较而重复请求完整字段。
- Macro 测试覆盖精确字段标识、共同完成交易日、财政部独立发布日期、三十日共同交易日折线、事件窗口、无代理替代和完整性门槛。
- Instrument 测试覆盖五季/三年字段映射、`N/A`/`none_found`/`data_gap` 区分、身份和财报阻塞条件、事件一手来源要求，以及没有默认 PA 的行为。
- Price Action 测试覆盖 120 个已完成日线门槛、单来源序列、复权模式、EMA20/EMA50/ATR14、排除未完成日线与历史不足时不生成 Board。
- Board 测试覆盖自包含性、离线打开、稳定视觉结构、必需视图、无 manifest/Gallery 依赖以及不出现持仓、订单、runtime 或旧 Price & Setup/Peers 内容。
- 安装测试从干净的 `uv` 虚拟环境按 README 和 `requirements.txt` 执行；测试确认 Longbridge CLI 仍是可选外部依赖。
- 清理测试从打包文件清单与文本引用两侧断言旧 runtime、broker、artifact、自动化和交易生命周期术语没有活动入口或用户文档引用。

## Out of Scope

- 订单创建、修改、取消、提交、执行建议或账户读取。
- 持仓展示、组合风险、Daily Ops、计划、复盘、自动化、KVN/Alpha、历史工作区、缓存和后台任务。
- 对标公司、同业估值、同业事件、默认技术分析、4H 或其它多周期 Price Action。
- VIX/VIX3M 比值、银行准备金、TGA、ON RRP、NDX/RUT 短窗卡片、z-score、价格代理与跨源交叉检查。
- 数据供应商之间的价格交叉核验、支付级别自动升级、静默安装或登录 Longbridge CLI。
- 历史 ADR 的删除或改写；它们只作为已被取代的决策记录保留。

## Further Notes

- 此规格取代当前 IBKR-only、持久化 Macro workspace、Daily Ops、ArtifactPacket 和 Gallery 的活动方向；对应的开放 issue 将在 ticket 化时标记为 superseded 或关闭。
- 供应商命令、字段、覆盖范围、请求批次与回退规则应在独立的字段级数据源契约中维护，以便在不改变 Board 语义的前提下验证供应商变更。
- 不需要 prototype：状态模型、字段集合、视觉范围和删除边界均已通过对话确认；风险应由 seam 注入测试覆盖。
