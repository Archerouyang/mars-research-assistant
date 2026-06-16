# Expected Weekly Outlook Shape: 2026-06-15 to 2026-06-19

This fixture defines the minimum acceptable user-facing shape for a weekly macro / policy / news outlook. It is not a live market call.

## 结论

- 本周核心不是猜方向，而是控制新增风险，等待 FOMC/SEP、10Y/4.5%、油价/伊朗/霍尔木兹三条线确认。
- 当前长期 ETF 持仓只讨论加仓、TP/再平衡、暂停加仓并复核，不讨论普通交易止损。

## 本周真正重要的 3 个变量

| 优先级 | 变量 | 为什么重要 | 影响的持仓/计划 | 用户动作 |
| --- | --- | --- | --- | --- |
| P0 | FOMC/SEP 与发布会 | 直接改变利率预期、长端收益率和成长股估值 | QQQ、SOXX、VOO、post-FOMC 新增计划、TLT/IWM 类候选 | 事件前降低新增风险，事件后再评估是否继续盯 |
| P0 | 10Y 是否围绕 4.5% 上破或回落 | 影响 duration growth、半导体、LEAP 和 TLT/IWM 相对吸引力 | QQQ、SOXX、DRAM、LEAP、TLT/IWM 类计划 | 10Y 上破则暂停加仓并复核；回落才考虑新增风险 |
| P1 | 伊朗/霍尔木兹/油价 | 通过 inflation、VIX、oil 和 growth multiple 传导 | QQQ、SOXX、VOO、新增 0DTE 风险 | 只处理已验证消息，不因标题噪音改计划 |

## 信源优先级

| 等级 | 当前使用方式 | 可以影响什么 | 限制 |
| --- | --- | --- | --- |
| S0 official / primary | Fed、Treasury、White House、BLS/BEA、NYSE/Fed calendars | FOMC/SEP、官方讲话、宏观数据、Juneteenth 休市事实 | 可直接进入事件表 |
| S1 market data / broker / calendar | 10Y、VIX、QQQ/SOXX/VOO/DRAM 价格结构、IBKR 行情 | 判断 rates、oil、volatility、sector 传导是否已经被市场确认 | 必须和价格反应一起看 |
| S2 reputable financial media | Reuters/AP/Bloomberg/WSJ/FT 等对伊朗、霍尔木兹、tariffs、Treasury/fiscal 的报道 | 作为政策和地缘事件线索 | 改变风险预算前需要 S0/S1 确认 |
| S3 research / opinion | Seeking Alpha、卖方研报、独立研究 | 个股 thesis、反方证据、动量主题解释 | 不能单独证明政策事实 |
| S4 social / rumor / unsourced commentary | 社媒、论坛、未署名截图 | 默认忽略 | 除非被 S0/S1/S2 确认 |

## 宏观/利率

- 10Y/4.5% 是本周利率主线；上破并维持会压制 QQQ、SOXX、DRAM、LEAP 和高 beta 动量风险。
- FOMC/SEP 后如果 10Y 回落、VIX 不扩张，才允许从平衡姿态向高 beta 动量靠近。

## 政策/新闻

- 特朗普/白宫相关内容只保留 tariffs、Treasury/fiscal、Fed independence、energy、sector regulation 这些能传导到资产定价的政策线。
- 伊朗/霍尔木兹和 oil 只在被 S0/S2 信源确认并传导到 VIX、inflation 或 growth multiple 后影响计划。

## 交易计划准备

### Input Reads

| 模块 | read | supports | pressures | blocks | evidence | next_check |
| --- | --- | --- | --- | --- | --- | --- |
| Macro Regime | 事件压缩周，默认平衡，等待 FOMC/SEP 和油价风险确认 | 核心 ETF 保持计划内，不因单日数据重置 | 高 beta 动量、LEAP、半导体追高 | FOMC 前新增大风险 | FOMC/SEP、零售销售、oil/霍尔木兹 | FOMC 后看 10Y/VIX/QQQ 接受情况 |
| Financial Conditions | 10Y/4.5% 是关键金融条件阈值 | 10Y 回落支持 QQQ/SOXX/DRAM 候选 | 10Y 上破压制 growth multiple 和 duration | 10Y 上破并维持时阻止新增高 beta | 10Y、VIX、USD | 4H/1D/1W 是否仍是上涨或转震荡 |
| Policy/Event Risk | Fed、Treasury/fiscal、tariffs、Fed independence 和 energy 是本周政策线 | 政策落地后可恢复计划准备 | 标题噪音和未验证讲话 | 未验证政策标题不能进 setup pool | Fed calendar、White House/Treasury、S2 news | 只保留能传导到 rates、oil、volatility 的事件 |
| Industry/Sector Strength | 半导体和 megacap leadership 需要 FOMC 后确认 | SOXX/DRAM 若承接强可进入截面候选池 | sell-the-news、breadth 不扩散 | 行业相对强度失效时不转 setup | SOXX/QQQ 相对表现、breadth | 财报后 gap hold 和相对强弱 |
| Company Thesis Check | 个股 thesis 只能作为候选，需 primary/current 验证 | 指数权重科技、AI 链、强现金流大盘股 | 估值压缩、guidance 风险 | thesis 未验证或财报前 gap risk 太大 | 公司 IR/财报、Seeking Alpha 仅作观点输入 | thesis/counter-thesis 完成后再找 price structure |

### 截面候选池 / Cross-Section Candidate Pool

| rank | symbol/theme | drivers | supported_by | pressured_by | blocked_by | price_structure / risk_context | setup_readiness | next_check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | QQQ 核心 ETF / 0DTE 执行候选 | 核心趋势仍在，FOMC 后可能恢复 risk-on | Macro Regime、Financial Conditions | 10Y 上破、VIX 扩张 | FOMC 前不追高 | QQQ 有关键区域，0DTE 有短周期和事件风险 | 需要 4H/1D/1W 维持上涨或高位震荡，1H 以下只做执行观察；可转 candidate setup | FOMC 后看 724-726 接受或 715-711 reclaim |
| 2 | SOXX / DRAM 半导体主题 | AI/半导体 leadership 可能延续 | Industry/Sector Strength、Company Thesis Check | 利率上行、财报 sell-the-news | 相对强度失效不进 Setup Pool | 需要 SOXX 相对 QQQ 承接，半导体 beta 集中 | 4H/1D/1W 必须确认非下跌，price structure 清楚后才转 candidate setup | 看 SOXX 相对 QQQ 是否扩散 |
| 3 | TLT/IWM 类利率反应候选 | 若 10Y 回落可能受益 | Financial Conditions | 热数据、鹰派 FOMC | 10Y 维持 4.5% 上方 | 利率方向未确认，仍是事件驱动候选 | 暂留截面候选池，不是 candidate setup | 等 FOMC/SEP 后重新评估 |

## 对当前持仓的总体影响

| 持仓 | 影响 | 本周动作 | 暂停/复核条件 |
| --- | --- | --- | --- |
| QQQ | 对 FOMC、10Y、VIX 最敏感 | 等回踩/收复确认，小批量；不追第一根突破 | 10Y 上破并维持 4.5% 上方，或 VIX 扩张 |
| VOO | 宽基核心，受整体风险预算影响 | 基本不动，只在极端回撤或再平衡时处理 | 风险资产全面失败突破 |
| DRAM | 主题仓，受半导体动量和利率影响 | 等动量榜和主题强度确认 | 半导体失去相对强度 |
| SOXX | 半导体 beta 较集中 | 有空间但不能在事件前追高 | 10Y 上破、FOMC 鹰派或半导体失败突破 |

## 策略姿态建议

| 姿态 | 采用条件 | 当前判断 | 对持仓/新增风险的含义 |
| --- | --- | --- | --- |
| 防御 | 10Y 上破并维持 4.5% 上方、VIX 扩张、油价/霍尔木兹风险被 S0/S2+S1 确认、FOMC 明显鹰派 | 不是默认，但必须准备切换 | 暂停 QQQ/SOXX/DRAM 加仓，0DTE 只做极小风险或跳过 |
| 平衡 | 事件前缺少方向确认，核心持仓趋势未破，利率和 VIX 没有失控 | 本周默认姿态 | 保留 QQQ/VOO/DRAM/SOXX 核心仓，只做小批量高质量加仓和计划内 TP/再平衡 |
| 高 beta 动量 | FOMC 后 10Y 回落、VIX 不扩张、QQQ/SOXX 接受关键位上方、动量榜扩散 | 事件后才允许升级 | 才考虑增加 SOXX/DRAM/强动量票/2x ETF 或更主动的 QQQ 0DTE setup |

## 当周重点财报

具体 ticker 不在 fixture 固化；实际运行必须用 S0/S1 财报日历确认。本节只保留会影响当前持仓、指数/行业 beta、动量主题或计划中 setup 的财报。

| 优先级 | 时间 | 标的/主题 | 信源优先级 | 为什么重要 | 影响的持仓/计划 | 财报后确认 | 策略姿态含义 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0/P1 | 本周盘前/盘后 ET | QQQ/VOO 指数权重科技股 | S0 公司 IR/交易所日历 + S1 盘后反应 | 可能影响 megacap leadership、growth multiple 和指数 gap risk | QQQ、VOO、QQQ 0DTE、新增科技 beta | guidance、盘后缺口是否守住、次日 breadth | 好结果且利率配合才支持高 beta 动量；否则维持平衡 |
| P1 | 本周盘前/盘后 ET | 半导体 / AI 链核心财报 | S0 公司 IR/交易所日历 + S1 SOXX/个股反应 | 验证 SOXX、DRAM、AI capex 和半导体相对强弱 | SOXX、DRAM、强动量票、2x ETF | 是否带动 SOXX 相对强度扩散 | 失败或 sell-the-news 提高防御权重；强承接才考虑高 beta 动量 |
| P2 | 本周盘前/盘后 ET | 消费、银行、能源代表性财报 | S0 公司 IR/交易所日历 + S2 财经媒体摘要 | 只作为增长、信用、油价和 sector rotation 背景 | VOO、IWM 类计划、能源/周期观察 | 是否改变 breadth 或 sector leadership | 默认不改变姿态，除非传导到 rates、oil、volatility |

## 事件重要性排序

| 优先级 | 时间 | 事件 | 为什么重要 | 信源优先级 | 传导路径 | 影响的持仓/计划 | 需要观察的确认 | 策略姿态含义 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | Mon ET | Empire State、工业产出、NAHB | FOMC 前的增长/制造业/住房预热 | S0 数据 + S1 10Y/VIX | rates / 10Y / sector | QQQ、VOO、IWM 类计划 | 数据是否推高长端收益率 | 只影响平衡/防御切换，不因单项数据进入高 beta 动量 |
| P1 | Tue ET | 进口/出口价格、住房开工、营建许可 | 进口价格影响通胀，住房影响利率敏感资产 | S0 数据 + S1 yields | inflation / 10Y / housing / growth | QQQ、SOXX、TLT/IWM 类计划 | 进口价格是否改变通胀预期 | 事件前保持平衡，热数据提高防御权重 |
| P0 | Wed 08:30 ET | 零售销售 | 消费强弱会影响 Fed 路径和收益率 | S0 数据 + S1 10Y/USD | rates / USD / earnings | QQQ、VOO、消费相关、新增计划 | 强数据是否推高 10Y | 热数据下暂停追高，维持平衡或转防御 |
| P0 | Wed 14:00 / 14:30 ET | FOMC 声明、SEP、发布会 | 全周最大政策和利率事件 | S0 Fed + S1 yields/VIX/QQQ | Fed / 2Y / 10Y / USD / volatility | QQQ、SOXX、DRAM、VOO、TLT/IWM、0DTE | 点阵图、发布会语气、10Y/VIX 反应 | 决定事件后继续平衡、转防御，还是允许高 beta 动量 |
| P1 | Thu ET | 初请失业金、Philadelphia Fed | 验证 FOMC 后软着陆/放缓叙事 | S0 数据 + S1 index/breadth | labor / growth / rates | IWM、QQQ、VOO、周期/小盘 | 劳动力是否降温但不崩 | 若数据温和且市场承接好，可从平衡向高 beta 动量靠近 |
| P2 | Fri | Juneteenth 休市 | 流动性和期权反应压缩到周一至周四 | S0 exchange calendar | liquidity / options | 0DTE、短周期计划 | 周四尾盘是否失真 | 不改变姿态，只提醒不要过度解读周四尾盘 |

## 宏观/政策/新闻时间线

| 时间 | 事件 | 优先级 | 计划影响 |
| --- | --- | --- | --- |
| Mon/Tue ET | 制造业、进口价格、住房数据 | P1 | 更新利率压力，不单独改变持仓 |
| Wed 08:30 ET | 零售销售 | P0 | 决定 FOMC 前是否继续冻结新增风险 |
| Wed 14:00 / 14:30 ET | FOMC/SEP/发布会 | P0 | 决定平衡、防御、高 beta 动量的切换 |
| Thu ET | 初请失业金、Philadelphia Fed | P1 | 验证 FOMC 后的市场承接和 breadth |
| Fri | Juneteenth 休市 | P2 | 提醒周四流动性和期权反应可能失真 |

## 下周事件预览

- 已知 P0/P1 事件直接进入事件表；其他财报、Fed/Treasury 日程、期权到期、政策期限、休市安排只在影响持仓或策略姿态时保留。

## 特朗普/白宫公开讲话与政策风险

- 只保留会影响 tariffs、Treasury/fiscal、Fed independence、energy、sector regulation 的内容。
- 公开讲话如果不能传导到 rates、USD、oil、sector 或 volatility，就视为噪音。
- 与 Fed independence、关税、财政赤字、能源供给相关的表态应进入 P0/P1 观察清单。

## 对现有持仓计划的影响

| 持仓 | 加仓影响 | TP/再平衡影响 | 暂停/复核触发 |
| --- | --- | --- | --- |
| QQQ | 只在回踩/收复确认和 VIX/10Y 配合时小批量 | 前高或高潮延伸后才考虑小幅 TP/再平衡 | 10Y 上破并维持 4.5% 上方，或 VIX 扩张 |
| VOO | 以核心持有为主，不因单日宏观数据加减 | 只在组合过度集中或再平衡需要时处理 | 宽基风险资产全面失败突破 |
| DRAM | 等半导体动量和财报/主题确认 | 主题过热或相对强度失效时复核 | 半导体失去相对强度 |
| SOXX | 事件前不追高，等 FOMC 后 rates/VIX/price action 确认 | 强延伸后考虑再平衡 | FOMC 鹰派、10Y 上破或半导体失败突破 |

## 对新增持仓计划的影响

| Plan / product | Risk allowed now? | Event confirmation needed | Crowding risk |
| --- | --- | --- | --- |
| QQQ 0DTE | 只允许 tiny risk，且必须等 5m/15m 确认 | VIX 不扩张，QQQ 不在中间震荡区 | 短周期 QQQ beta |
| ETF / 2x ETF | FOMC 前谨慎，事件后再判断 | 10Y 不能上破并维持 4.5% 上方 | 杠杆 beta |
| LEAP | 等利率路径确认 | FOMC/SEP 不能明显鹰派 | rate-sensitive duration |

## 组合风险

- 科技 beta：QQQ、SOXX、DRAM 方向高度相关。
- 半导体：SOXX + DRAM 主题暴露需要动量确认，不适合在利率事件前追高。
- 利率敏感：QQQ、SOXX、LEAP、TLT/IWM 类计划都受 10Y 冲击。
- 短周期/0DTE：只作为盘中执行，不应替代周度计划判断。

## 需要用户决策的事项

1. FOMC 前是否冻结新增 ETF/2x/LEAP 风险。
2. 若 QQQ 到加仓区，是否只允许小批量并要求 VIX/10Y 同向确认。
3. 是否把油价/伊朗/霍尔木兹列为本周 P1 风险监控，而不是盘中追标题。
