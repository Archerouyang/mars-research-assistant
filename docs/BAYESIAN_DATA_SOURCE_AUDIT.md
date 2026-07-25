# Bayesian-First 数据源审计：IBKR、Longbridge 与 FMP

审计日期：2026-07-17

范围：核对官方 API 文档、官方产品页、官方协议与官方 FAQ，并对已有 FMP、IBKR 和 Longbridge 接入做最小只读 market/reference probe。未读取或回显任何密钥，未调用账户、持仓、订单或交易接口，未改动 Quant 代码或 runtime 数据。FMP probe 期间 `uv` 因旧 `.venv` 的 Python 链接已失效而自动重建了被 Git 忽略的本地开发环境；Quant Git 工作树仍然干净。

## 结论先行

当前三类可用入口可以支持一部分行情采集，但**没有任何一家已经被官方资料证明能单独满足 Bayesian 第一版的完整 P0 历史数据链**。

- **FMP 是最接近首轮有条件试采的主候选**：有历史 EOD、批量 EOD、历史市值、公司 profile、symbol change、美国退市公司、拆股、分红、SPY 行情以及交易所假日/时段接口。不过其官方 FAQ 明确说退市公司历史价只覆盖部分美国公司，部分 symbol 会缺失；公开文档也没有给出全市场 security master 的 `valid_from`、`valid_to`、市场数据 `available_at`、ticker 重用隔离或退市终值保证。因此它只能进入 entitlement 与 golden-case 验证，不能直接标记为 PIT-approved。
- **Longbridge 适合作为第二行情源和近年交叉核验源，不适合作为全市场 PIT 主链**：美国日线官方范围为 2010-06-01 至今，支持无复权/前复权、OHLCV 和 turnover，并新增了公司行动接口；但历史 K 线每月只允许查询 100–3,000 个唯一 symbol（取决于账户档位），官方 security list 还明确是会变化的当前列表，未文档化稳定 security ID、ticker lineage、历史有效期或 `available_at`。交易日接口只支持最近一年。
- **IBKR 不可作为历史全市场主源**：它有 `conId`、合约类型、历史 OHLCV、拆股/分红复权类型和历史 schedule，但官方文档明确列出“不再交易的证券”没有历史数据，证券换交易所后换所前数据也经常不可用；历史数据还会因后续调整、压缩和过滤而在不同请求时点出现差异。这与无生存者偏差、可复现 PIT 面板的核心要求冲突。
- **XNYS 2010+ 规范日历仍需独立、版本固定的权威来源**。三家接口都可提供部分时段/假日/交易日信息，但 Longbridge 只有最近一年，IBKR 是合约 schedule，FMP 的公开假日文档没有证明 2010+ 完整历史与修订版本；它们都不能直接替代一个冻结并哈希的 XNYS calendar artifact。
- **标签审计表、数据 manifest、原始响应 hash、缺失率/覆盖率报告必须由本项目构建**。三家均没有直接提供满足项目 schema 的 `target_end_date`、`label_matured`、stock/SPY matching return、source fingerprint 或不可变数据集 hash。

> **API key presence != entitlement/PIT proof。** 本机存在 FMP key、Longbridge/IBKR 可登录或能成功请求少量当前数据，只能证明某种凭据存在；它不证明相应套餐有 2010+ 历史深度、全市场/退市覆盖、批量权限、再分发授权，也不证明数据具有 point-in-time 或 `available_at` 语义。

因此，当前状态应保持为：`setup_gap.source_contract_unverified`。下一步是只读 entitlement probe 与供应商书面确认，不是开始全量下载或训练。

## 当前接入实测（2026-07-17）

### FMP entitlement probe

Quant 仓库的 `.env` 中已配置非空 `FMP_API_KEY`（本轮只检查存在性，未输出值）。通过现有 `uv run dailytrades-quant provider-probe --format json` 实测：

| Endpoint 能力 | HTTP | 实测状态 | 对 Bayesian P0 的含义 |
|---|---:|---|---|
| `daily_adjusted_ohlcv` | 200 | `available` | 可进入小样本历史深度与复权对账；尚未证明 2010+ 和退市覆盖。 |
| `delisted_companies` | 200 | `available` | 可取退市列表，但不等于退市 OHLCV、并购现金/破产终值完整。 |
| `stock_list` | 402 | `plan_restricted` | 当前套餐不能依靠该接口生成基础 universe，且 current list 本身也不是 PIT master。 |
| `symbol_changes` | 402 | `plan_restricted` | ticker lineage 的必要输入当前不可用。 |
| `historical_sp500_constituents` | 402 | `plan_restricted` | 不能用当前权限验证历史指数成分；该接口即使可用也不替代全市场 PIT universe。 |
| `etf_holdings` | 402 | `plan_restricted` | 不阻塞五因子 v1；但阶段二行业/主题映射不能依赖当前权限。 |
| income/balance/cashflow/as-reported/report dates | 200 | `available` | 属第三阶段候选，不应继续被现有 probe 标为 Bayesian v1 `required`。 |
| `analyst_estimates` | 400 | `degraded` | 不在 v1 范围；不影响 P0 判定。 |

目前的 `DEFAULT_ENDPOINTS` 仍把四类基本面接口标为 `required`，而把 security-master/PIT 相关接口标为 optional。这与已冻结的 Bayesian-first 优先级相反，应在下一张 bounded 开发票中修正；本轮不修代码。

### IBKR market-data probe

当前 IBKR 连接可解析美国 SPY（ARCA）合约，并返回 2021-07-19 至 2026-07-17 的 1,254 根日线 OHLCV，同一请求包含 20 条 `CashDividends` 公司行动。这证明当前会话可做 active-security/SPY 行情对账；当前 Codex IBKR 连接器的该请求最长期限为五年，且仍然没有消除 IBKR 官方所述的死证券、换所前历史和历史重处理缺口。

### Longbridge market-data probe

Longbridge CLI 已安装，`longbridge check --format json` 显示 token 有效且 CN/global OpenAPI 连通。只读 K-line probe 成功返回：

- 最近 5 根 SPY 前复权日线，包含 OHLCV 和 turnover；
- 2010-06-01 至 2010-06-10 的 8 根 SPY 前复权日线，证明当前 token 可读到文档所述的 2010-06-01 起点；这段历史数据的 `turnover` 全部为 `0`，因此历史资格筛选不能盲目依赖 Longbridge turnover，需用一致价量口径推导 20 日成交额并做 golden-case 对账。

上述实测仍只证明单一 active symbol 的访问能力，没有验证每月唯一 symbol 配额、退市 symbol 可读性、公司行动完整性或 PIT identity contract。

## 判定口径

- `supported`：官方资料明确覆盖该项的全部最低要求。
- `partial`：明确覆盖一部分，但仍缺关键字段、历史范围、完整性、PIT 语义或合同证明。
- `unsupported`：官方资料明确说明缺失/不可用，或明确限制与要求冲突。
- `unknown`：官方公开资料没有足够信息；不能把“文档没写”推断为“肯定支持”。

这里的 PIT 至少要求：历史截面成员不从今天的列表回填；身份和 ticker 关系有有效期；每条资格字段有当时可用时间；后续修订不会无痕覆盖；退市/并购终值进入收益链；原始数据可按来源与 hash 重放。

## P0 must-have 矩阵

| P0 数据层 | IBKR | Longbridge OpenAPI | FMP | 审计结论 |
|---|---|---|---|---|
| 历史 PIT security master：稳定 ID、上市/退市、ticker lineage、有效期、`available_at` | `unsupported` | `unknown` | `partial` | IBKR `conId` 可标识当前/可解析合约，但官方明确无“不再交易证券”的历史数据，换交易所前历史也常缺。Longbridge 公开接口以 `ticker.region` 为键，只有会变化的当前 security list/static info/当前 trade status，未见完整 lineage 与有效期。FMP 有 CIK/ISIN/CUSIP、IPO/active profile、symbol change 和 US delisted list，但未形成全市场 canonical security interval，也无 market-data `available_at`。 |
| 历史资格：价格、20 日成交额、市值/替代、上市历史、证券类型 | `partial` | `partial` | `partial` | 三家都能提供历史价格；20 日成交额可由价量推导，Longbridge 还直接返回 turnover。IBKR API 的 market-cap fundamental tags 已被[官方 changelog](https://www.interactivebrokers.com/campus/ibkr-api-page/web-api-changelog/)标为弃用；Longbridge static shares/status 是当前快照；FMP 明确有历史市值与 profile IPO/type，但 profile/active 信息不是历史 as-of interval。 |
| 完整 OHLCV 与明确复权政策 | `partial` | `partial` | `partial` | IBKR `TRADES` 拆股复权但不含分红，`ADJUSTED_LAST` 同时含拆股和分红；但死证券与换所历史缺失、volume 被过滤且历史会重处理。Longbridge 有 actual/forward-adjust、OHLCV/turnover，美国日线从 2010-06-01 起；官方没有解释前复权对现金分红/特殊行动的完整算法。FMP 有 full、non-split-adjusted、dividend-adjusted 三类 EOD 和 EOD bulk，但 full endpoint 的完整 adjustment contract、历史修订/冻结规则仍需确认。 |
| 拆股、分红、停牌、并购、退市终值 | `unsupported` | `partial` | `partial` | IBKR 调整价可覆盖拆股/分红效果，但“不再交易证券无历史数据”使退市收益链不可闭合。Longbridge 文档化了 suspension/delisted/code moved 状态和 corporate-actions（split/merger/spin-off/rights）及 dividend dates，但没有终值、ticker lineage、事件 `available_at` 和完整覆盖承诺。FMP 有 splits/dividends/M&A/symbol change/delist，但官方 FAQ 承认退市历史价只覆盖部分标的，也未承诺现金并购/破产清算 terminal return。 |
| SPY 与 XNYS calendar | `partial` | `partial` | `partial` | 三家理论上都能取 SPY 行情。IBKR 有 `SCHEDULE` 和 contract trading hours，但不是冻结的全市场历史日历；Longbridge US trading-days 只有最近一年；FMP 有 exchange market hours 与 holidays-by-exchange，但公开页未证明 2010+ 历史、半日和修订版本完整性。 |
| 标签审计表 | `partial` | `partial` | `partial` | 可提供 stock/SPY 输入；`target_end_date`、matching-session 20D returns、`label_matured`、terminal treatment 和 source fingerprints 都需项目侧生成。三家都没有现成的项目标签审计表。 |
| 授权、as-of/available-at、覆盖率、缺失率、调整政策、不可变 hash | `partial` | `partial` | `partial` | 三家都存在授权/套餐/频率或带宽边界；都没有直接交付本项目需要的 manifest 与不可变 hash。IBKR 明确会在不同请求时点返回不同历史；Longbridge/FMP 市场数据公开 schema 未给 `available_at`。这些字段必须在采集层自行记录，并把未知项 fail closed。 |

## 供应商逐项证据

### 1. Interactive Brokers（IBKR）

**可用能力**

- Contract 对象提供 `conId`、symbol、security type、exchange/primary exchange、currency；Contract Details 还可返回 ISIN、stock type、trading/liquid hours 等当前描述。这可用于当前合约解析和交叉 ID，但官方文档没有把它定义为一套带历史有效期的 security master。[IBKR TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- 历史 bar 支持 OHLCV。`TRADES` 对拆股复权但不对分红复权；`ADJUSTED_LAST` 对拆股与分红都复权；`SCHEDULE` 返回历史交易 schedule 而不返回 OHLCV。[IBKR TWS API historical market data](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- `reqHeadTimestamp` 可查某合约/数据类型在 IBKR 历史库中的最早可用时间，但这只是“数据最早可取时间”，不是上市日或 PIT `available_at`。[IBKR TWS API documentation](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)

**致命限制与合同风险**

- 官方“Unavailable Historical Data”明确包括“data for securities which are no longer trading”；证券迁移到新交易所后，迁移前历史也经常不可用。这直接破坏退市覆盖和 symbol/exchange 连续性。[IBKR TWS API historical limitations](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- 历史交易数据会过滤偏离 NBBO 的某些 trade types，历史 volume 可能低于实时未过滤数据；官方还说明历史数据默认会调整、压缩和过滤，因此不同请求时点可能出现差异。若没有项目侧原始快照与 hash，研究不可重放。[IBKR TWS API historical limitations](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- 小 bar 有 60 requests / 10 minutes 等 pacing 限制；IBKR 也明确表示自己不是专业历史数据供应商，并建议需求不满足时使用专门 provider。[IBKR TWS API historical limitations](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- API market data 要求逐用户订阅、Market Data API Acknowledgement，并受交易所/专业用户分类影响；有账户不等于有 API market-data entitlement。[IBKR API market data subscriptions](https://www.interactivebrokers.com/campus/ibkr-api-page/market-data-subscriptions/)
- IBKR/GFIS 的 API acknowledgement 明确限制向第三方发布、传播或再分发市场数据，除非事先获得许可；因此研究结果对外展示/分发必须单独走许可审查。[IBKR market data API acknowledgement](https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3089)

**角色建议**：只作为 active-security 行情/调整价/交易 schedule 的交叉核验源，或少量 SPY/当前 universe sanity check；禁止承担历史 PIT universe、退市链或全市场主面板。

### 2. Longbridge OpenAPI

**可用能力**

- Historical Candlesticks 按 `ticker.region`、日期或 offset 返回 open/high/low/close/volume/turnover/timestamp；美国股票日/周/月/年 K 线的官方范围是 2010-06-01 至今。单次最多 1,000 bars，endpoint 限速 60 次/30 秒。[Longbridge Historical Candlesticks](https://open.longbridge.com/docs/quote/pull/history-candlestick)
- K 线 adjustment enum 只有 `Actual` 与 `Adjust forward`。它证明可选择不复权/前复权，但官方 enum 没有披露分红、特殊分红、spin-off、rights、合并换股等调整公式。[Longbridge quote object definitions](https://open.longbridge.com/docs/quote/objects)
- Static Info 返回当前 symbol、exchange、currency、board、total/circulating shares 等；当前 quote/quote push 还可返回 trade status。状态 enum 包含 suspension、delisted、code moved、split-stock halt 等，可用于当前状态检测。[Longbridge Static Info](https://open.longbridge.com/docs/quote/pull/static)；[Longbridge quote object definitions](https://open.longbridge.com/docs/quote/objects)
- 新增的 corporate-actions endpoint 声称可取 split、merger、spin-off、rights issue 历史；dividend detail 提供 ex/record/payment dates。它们为事件对账提供了候选输入，但响应以 symbol 为主，公开 schema 没有稳定 security ID、公告/接收 `available_at` 或终值字段。[Longbridge Corporate Actions](https://open.longbridge.com/docs/fundamental/fundamental/corporate-actions)；[Longbridge Dividend Detail](https://open.longbridge.com/docs/fundamental/fundamental/dividend-detail)

**致命限制与未知项**

- 历史 K 线实行每月唯一 symbol 配额：按账户档位只有 100、400、600、1,000、2,000 或最多 3,000 个 symbol。即使最高档，仍不能假定足以覆盖完整美国股票历史截面；实际 entitlement 必须现场读取但不得输出凭据。[Longbridge K-line quota](https://open.longbridge.com/docs/cli/market-data/kline)
- Security List 官方说明“列表会随着 eligibility 更新而变化，应重新查询而不是依赖缓存”。这正是 current-universe endpoint，而不是历史 PIT universe。[Longbridge Security List](https://open.longbridge.com/docs/cli/market-data/security-list)
- Market Trading Days 明确限制单次区间不超过一个月，并且只支持最近一年；它无法提供 2010+ XNYS 研究日历。[Longbridge Market Trading Days](https://open.longbridge.com/docs/quote/pull/trade-day)
- OpenAPI quote permissions 与 App/PC/Web 权限分离，需要独立激活/购买；能登录 Longbridge 或 App 有实时行情不证明 OpenAPI 历史 K 线配额与权限。[Longbridge Quote API overview](https://open.longbridge.com/docs/quote/overview)；[Longbridge pricing](https://open.longbridge.com/pricing)
- 本轮在官方公开 OpenAPI 文档中未找到 market-data redistribution、长期存储、派生数据发布的完整授权条款，也未找到 PIT/`available_at` 承诺。结论必须是 `unknown`，上线/公开分发前需 Longbridge 书面确认。

**角色建议**：作为 2010-06-01 之后 active/current symbol 的第二 OHLCV 源、turnover 核验源和公司行动对账源；在唯一 symbol 配额、死证券可访问性、前复权算法和许可得到实测/书面确认前，禁止当全市场主源。

### 3. Financial Modeling Prep（FMP）

**可用能力**

- Stable API 有 full EOD OHLCV、EOD bulk、明确的 non-split-adjusted endpoint，以及 dividend-adjusted endpoint；另有逐 symbol splits 与 dividends。因此可以同时保存原始价、拆股事件和含分红调整价，建立 adjustment reconciliation。[FMP full EOD](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full)；[FMP unadjusted EOD](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-non-split-adjusted)；[FMP dividend-adjusted EOD](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-dividend-adjusted)；[FMP splits](https://site.financialmodelingprep.com/developer/docs/stable/splits-company)；[FMP dividends](https://site.financialmodelingprep.com/developer/docs/historical-stock-dividends-api/)
- Company Profile 提供 CIK、ISIN、CUSIP、IPO date、当前 active 状态、当前 price/market cap 等；另有历史 market-cap endpoint。[FMP Company Profile](https://site.financialmodelingprep.com/developer/docs/stable/profile-symbol)；[FMP Historical Market Cap](https://site.financialmodelingprep.com/developer/docs/historical-market-cap-company-information)
- Stable API 有 symbol-change 与美国 delisted-companies 列表，可用于生成候选 identity edges 和 list/delist events；有 S&P 500 历史 additions/removals，但这只覆盖特定指数变更，不能代替全市场 PIT universe。[FMP Symbol Changes](https://site.financialmodelingprep.com/developer/docs/stable/symbol-changes-list)；[FMP Delisted Companies](https://site.financialmodelingprep.com/developer/docs/delisted-companies-api)；[FMP Historical S&P 500](https://site.financialmodelingprep.com/developer/docs/stable/historical-sp-500)
- FMP 提供 exchange market hours 与 holidays-by-exchange，可作为日历对账输入；SPY 可走股票 EOD endpoint。[FMP Exchange Market Hours](https://site.financialmodelingprep.com/developer/docs/stable/exchange-market-hours)；[FMP Holidays by Exchange](https://site.financialmodelingprep.com/developer/docs/stable/holidays-by-exchange)

**致命限制与合同风险**

- FMP 官方 FAQ 明确：只为“部分美国退市公司”提供历史价格，某些退市 symbol 因上游限制不可用；当 ticker 被新公司重新采用或彻底退休时，历史数据可能有限或不再可用。这意味着 delisted list 的存在不等于退市 OHLCV/terminal return 完整。[FMP official FAQ](https://site.financialmodelingprep.com/contact)
- 公开 schema 没有把 CIK/ISIN/CUSIP + symbol change + delisted list 组合成稳定的 security-level 历史 interval，也没有给市场数据 `available_at`、修订序号或不可变版本。必须实测 ticker reuse、share class、merger successor 和 delisting cash/zero terminal cases。
- 旧版曾有名为 “Survivorship Bias Free EOD” 的 legacy endpoint，但官方页面现在明确标为 Legacy；FMP FAQ 还说明 Legacy API 对新用户和免费用户已停止支持。不能因为旧页面存在就假定当前 key 有权限，更不能把它当 stable PIT contract。[FMP legacy survivorship-bias endpoint](https://site.financialmodelingprep.com/developer/docs/survivorship-bias-api)；[FMP official FAQ](https://site.financialmodelingprep.com/contact)
- 套餐决定历史深度与批量权限：官方 pricing 显示 Basic/Starter 为 5 年，Premium/Ultimate 为 30+ 年，Ultimate 才明确列出 full historical access 与 bulk/batch delivery；另有 calls/minute 与 rolling 30-day bandwidth 限额。一个可用 key 不证明有 2010+、bulk 或全部 endpoint entitlement。[FMP pricing](https://site.financialmodelingprep.com/pricing-plans)
- FMP pricing 明确：展示或再分发 FMP 数据需要单独 Data Display and Licensing Agreement。仓库、报告或对外产品不能默认携带原始 FMP 数据。[FMP pricing and licensing](https://site.financialmodelingprep.com/pricing-plans)

**角色建议**：进入“有条件主候选”验证。只有在 entitlement、delisted golden set、identity interval、adjustment reconciliation、market-cap as-of、calendar depth 和许可全部通过后，才可承担首轮 pilot；即使通过，PIT master 与 terminal-return policy 仍可能需要第二供应商或项目自建补齐。

## 对五因子与标签的直接影响

| 模型字段 | 可从三家构造吗 | 仍需冻结的口径 |
|---|---|---|
| `return_20d`、`return_60d` | 可以从一致复权口径的 daily close 构造 | 使用 price-return 还是 total-return；分红、拆股、symbol change、停牌空窗和终值如何处理；不能混用 provider 默认调整价。 |
| `volume_ratio_5_20` | 可以从 volume 构造，Longbridge 另有 turnover | IBKR volume 有过滤且可按 shares/lots 配置；拆股前后 volume 是否反向调整；缺失 session 是零还是 NA。 |
| `realized_volatility_20d` | 可以从冻结的 daily return 构造 | return 定义必须与标签一致；停牌/退市不得用前值静默填充。 |
| `ema_distance_50d` | 可以从冻结的 adjusted close 构造 | 复权历史一旦重算会改变整条 EMA；必须 pin raw payload、adjustment version 与 hash。 |
| 未来 20 交易日相对 SPY 超额收益 | 可以构造，但当前尚未 production-ready | XNYS session 对齐、SPY 同源复权、`target_end_date`、label maturity、股票中途退市/并购终值和不可交易空窗。 |

技术上约 332 个交易日只够跑通首次验证，不改变供应商验收标准。正式研究仍应要求 raw history 从 2010 年开始、2016 年起 walk-forward、2024 年起 untouched OOS。Longbridge 的 US 日线从 2010-06-01 开始，因此连“2010 全年”也需明确接受缺口或由另一来源补齐。

## 开发前必须完成的只读验收

### A. 书面合同/entitlement 问题

向每家供应商取得可保存的答复，至少覆盖：

1. 当前账户的具体套餐、US equity 历史起点、全市场与 delisted symbol 权限、批量/带宽/频率上限；
2. stable identifier 的生命周期、ticker reuse、share class、exchange move、merger successor 如何表达；
3. split/dividend/special dividend/spin-off/rights/merger cash 的调整算法和生效时间；
4. suspension、bankruptcy、acquisition delisting 和 liquidation 的最后可交易价/现金终值是否提供；
5. market-cap/shares/security status 的历史 `as_of` 与 `available_at` 是否存在，后续修订如何版本化；
6. 原始数据长期存储、内部研究、派生结果、图表展示与再分发的授权范围。

任何没有明确答复的项都保持 `unknown`，不得由“API 调通”升级为 `supported`。

### B. 不泄密的 golden-case probe

只调用公开 market/reference endpoints，不调用 account/order endpoints；日志禁止出现 key、token、完整授权 header 或账户号。至少检查：

- 普通长期上市股：完整 2010+/2016+/2024+ 日线、volume 与 adjustment 稳定性；
- 多次拆股与现金分红标的：raw / split-adjusted / dividend-adjusted returns 能否与事件表对账；
- ticker rename、exchange move、双 share class：稳定身份是否连续且不会错误合并；
- 停牌后恢复、现金并购退市、破产退市：最后交易日、缺失 bars、successor/cash/zero terminal 是否可重建；
- 同一历史区间隔日重取：payload 是否变化，若变化能否识别 revision；
- SPY 与 XNYS 半日/假日：session 数、maturity date 与 20-session window 是否一致。

### C. pass/fail 门槛

只有同时满足以下条件，才进入 adapter/manifest 开发：

- 不从 current stock list 回填历史 universe；
- 每个历史 row 可映射到项目 `security_id` 与有效 ticker interval；
- 退市 golden cases 的 terminal return 可解释且可重放；
- raw payload 保存 fetch timestamp、endpoint/version、非敏感 request parameters、entitlement label、provider as-of/available-at（若有）、coverage/missingness 与 SHA-256；
- SPY 与股票使用同一 session/adjustment contract；
- 供应商许可允许预定的内部存储和输出范围；
- 任何不完整覆盖被显式标为 `PARTIAL`，不会静默进入 Bayesian 训练。

## 推荐执行顺序

1. **先验 FMP entitlement，不下载全量数据。** 读取 dashboard 中的 plan/endpoint entitlement 与带宽状态，做最小只读探针；不得打印 key。
2. **并行验证 Longbridge 真实 symbol 配额与死证券行为。** 若账户档位低于研究 universe 或 delisted symbol 不可取，固定为 cross-check source。
3. **把 IBKR 固定为非主源。** 只验证 active-security/SPY/adjustment 对账，不再尝试用它补历史退市链。
4. **单独批准 XNYS calendar source 与 terminal-return policy。** 在这两项冻结前，不实现 label maturity 或正式 walk-forward。
5. **通过 golden-case 后再写 bounded spec/tickets。** 第一张实现票应是 raw immutable landing + source manifest，不是 Bayesian 拟合或大规模 backfill。

## 官方来源索引

### IBKR

- [TWS API documentation: contracts, historical data, adjustment types, schedule and limitations](https://ibkrcampus.com/campus/ibkr-api-page/twsapi-doc/)
- [IBKR API market-data subscriptions and compliance](https://www.interactivebrokers.com/campus/ibkr-api-page/market-data-subscriptions/)
- [IBKR/GFIS Market Data API Acknowledgement](https://gdcdyn.interactivebrokers.com/Universal/servlet/Registration_v2.formSampleView?formdb=3089)

### Longbridge

- [Historical Candlesticks](https://open.longbridge.com/docs/quote/pull/history-candlestick)
- [Quote object definitions](https://open.longbridge.com/docs/quote/objects)
- [Static Info](https://open.longbridge.com/docs/quote/pull/static)
- [Security List](https://open.longbridge.com/docs/cli/market-data/security-list)
- [Market Trading Days](https://open.longbridge.com/docs/quote/pull/trade-day)
- [Corporate Actions](https://open.longbridge.com/docs/fundamental/fundamental/corporate-actions)
- [Dividend Detail](https://open.longbridge.com/docs/fundamental/fundamental/dividend-detail)
- [Quote permissions](https://open.longbridge.com/docs/quote/overview)
- [K-line quota](https://open.longbridge.com/docs/cli/market-data/kline)
- [Pricing](https://open.longbridge.com/pricing)

### FMP

- [Stable API index](https://site.financialmodelingprep.com/developer/docs/stable)
- [Full EOD OHLCV](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-full)
- [Unadjusted EOD](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-non-split-adjusted)
- [Dividend-adjusted EOD](https://site.financialmodelingprep.com/developer/docs/stable/historical-price-eod-dividend-adjusted)
- [Historical Market Cap](https://site.financialmodelingprep.com/developer/docs/historical-market-cap-company-information)
- [Company Profile](https://site.financialmodelingprep.com/developer/docs/stable/profile-symbol)
- [Symbol Changes](https://site.financialmodelingprep.com/developer/docs/stable/symbol-changes-list)
- [Delisted Companies](https://site.financialmodelingprep.com/developer/docs/delisted-companies-api)
- [Official FAQ, including delisted-history and legacy-access limits](https://site.financialmodelingprep.com/contact)
- [Exchange Market Hours](https://site.financialmodelingprep.com/developer/docs/stable/exchange-market-hours)
- [Holidays by Exchange](https://site.financialmodelingprep.com/developer/docs/stable/holidays-by-exchange)
- [Pricing, history depth, rate/bandwidth and display/redistribution licensing](https://site.financialmodelingprep.com/pricing-plans)
- [Terms of Service](https://site.financialmodelingprep.com/developer/docs/terms-of-service)
