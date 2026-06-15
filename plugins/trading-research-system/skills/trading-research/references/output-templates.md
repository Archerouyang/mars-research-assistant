# Output Templates

Use concise Chinese Markdown unless the user asks otherwise.

## AI-Native Output Contract

The agent should read and verify much more than it shows. User-facing output is a synthesis layer, not a research dump.

Default rules:

- start with the answer or current state;
- keep only facts that change the plan, setup status, risk, or confidence;
- collapse repetitive headlines into one changed variable;
- prefer a compact chart or annotated visual when price structure, levels, volatility, or multi-timeframe context are easier to inspect visually;
- cite or name sources only where evidence quality matters;
- move raw detail into local notes or appendices only when needed;
- ask follow-up questions only when missing information blocks the next decision.

Chart rules:

- use TradingView links or screenshots when the user provides them or when an authenticated browser session makes that practical;
- otherwise generate local TradingView `lightweight-charts` HTML artifacts from authorized OHLCV data;
- when the chat benefits from inline visuals, show a screenshot or exported image of the generated artifact, while keeping the HTML as the richer local artifact;
- keep chart annotations limited to decision-useful levels such as 20 EMA, 50 EMA, trigger zone, invalidation, profit-taking/rebalance zone, VIX confirmation, and setup status;
- avoid chart dumps with every indicator. If the chart needs more than a few annotations, put the full version in local notes and show the user the simplified version.

For market-hour outputs, prefer:

```markdown
## 结论
-

## 变化
-

## Setup 状态
| setup_id | 状态 | 为什么 | 下一步 |
| --- | --- | --- | --- |

## 风险/失效
-
```

For weekly macro / policy / news outlooks, avoid plain event-calendar output. Use:

```markdown
## 结论
-

## 本周真正重要的 3 个变量
| 优先级 | 变量 | 为什么重要 | 影响的持仓/计划 | 用户动作 |
| --- | --- | --- | --- | --- |
| P0/P1/P2 |  |  |  |  |

## 信源优先级
| 等级 | 当前使用方式 | 可以影响什么 | 限制 |
| --- | --- | --- | --- |
| S0 official / primary |  | 政策事实、经济数据、交易所日历、公司事实 |  |
| S1 market data / broker / calendar |  | 价格、收益率、VIX、事件时间、市场传导 |  |
| S2 reputable financial media |  | 新闻线索和政策解读 | 需要 S0/S1 确认后才改变风险预算 |
| S3 research / opinion |  | 研报观点、反方论证、个股 thesis | 不能单独证明政策或宏观事实 |
| S4 social / rumor / unsourced commentary |  | 默认忽略 | 除非被更高等级信源确认 |

## 宏观/利率
- 只写会改变风险预算、策略姿态、持仓加仓/TP/暂停复核的利率和流动性变量。

## 政策/新闻
- 只写会通过 rates、USD、oil、sector、volatility、liquidity 或 earnings 传导到计划的政策/新闻。

## 对当前持仓的总体影响
| 持仓 | 影响 | 本周动作 | 暂停/复核条件 |
| --- | --- | --- | --- |
| QQQ/VOO/DRAM/SOXX |  | 加仓 / TP再平衡 / 暂停加仓 |  |

## 策略姿态建议
| 姿态 | 采用条件 | 当前判断 | 对持仓/新增风险的含义 |
| --- | --- | --- | --- |
| 防御 |  |  |  |
| 平衡 |  |  |  |
| 高 beta 动量 |  |  |  |

先给出组合层面的姿态判断，再说明具体观察清单和 setup。不要把“交易含义”写成孤立的买卖建议。

## 当周重点财报
| 优先级 | 时间 | 标的/主题 | 信源优先级 | 为什么重要 | 影响的持仓/计划 | 财报后确认 | 策略姿态含义 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P0/P1/P2 | 日期 + 盘前/盘后/ET |  | S0/S1/S2 | 指数权重 / sector leadership / watchlist setup / gap risk | QQQ/VOO/DRAM/SOXX/新增计划 | guidance / gap hold / breadth / relative strength | 防御 / 平衡 / 高 beta 动量 |

只列会影响当前持仓、指数/行业 beta、动量主题或计划中 setup 的财报。不要输出完整财报日历。

## 事件重要性排序
| 优先级 | 时间 | 事件 | 为什么重要 | 信源优先级 | 传导路径 | 影响的持仓/计划 | 需要观察的确认 | 策略姿态含义 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P0/P1/P2 | 日期 + 美东时间 |  |  | S0/S1/S2/S3/S4 | rates / 10Y / USD / oil / sector / volatility |  |  | 防御 / 平衡 / 高 beta 动量 |

## 宏观/政策/新闻时间线
-

## 下周事件预览
- 用于补充还没有进入 P0/P1/P2 表格、但需要提前准备的数据、Fed/Treasury、财报、期权到期、政策期限或休市安排。

## 特朗普/白宫公开讲话与政策风险
- 只保留会影响 tariffs、Treasury/fiscal、Fed independence、energy、sector regulation 的内容。
- 其他讲话或媒体噪音不进入交易计划，除非传导到 rates、USD、oil、sector 或 volatility。

## 对现有持仓计划的影响
- 长期 ETF 只讨论加仓、TP/再平衡、暂停加仓并复核；不写普通交易止损。

## 对新增持仓计划的影响
- 说明是否允许新增风险，还是必须等待事件确认。

## 组合风险
- 科技 beta：
- 半导体：
- 利率敏感：
- 短周期/0DTE：

## 需要用户决策的事项
1.
```

Weekly user-facing text should not use unexplained internal status jumps. If an internal status is necessary, explain it in Chinese immediately.

## Research Memo

```markdown
# 交易研究备忘录：{target}

## 结论摘要
- 判断：
- 置信度：
- 不应贸然行动的理由：

## 宏观政策与利率环境
- 核心信号：
- 噪音过滤：
- 传导路径：

## 事实与数据
| 项目 | 数据/事实 | 日期 | 来源 |
|---|---:|---|---|

## 多头逻辑
-

## 空头逻辑
-

## 研报观点与校验
| 来源 | 观点 | 可验证事实 | 反方证据 | 结论 |
|---|---|---|---|---|

## Price Action 择时
- 市场状态：
- 交易类型：
- 入场触发：
- 失效/止损：
- 目标：

## 组合风险
-

## 下一步
1.
2.
3.
```

## Stock Screen

```markdown
# 股票筛选：{theme}

## 筛选结论
| 排名 | 标的 | 逻辑 | 宏观适配 | 估值 | 催化剂 | 风险 | 择时条件 |
|---:|---|---|---|---|---|---|---|

## 入选理由
-

## 剔除/降级理由
-

## 组合风险提示
-
```

## Portfolio Risk

```markdown
# 组合风险体检

## 总体判断
-

## 风险暴露
| 暴露 | 问题 | 相关仓位 | 严重度 | 处理方式 |
|---|---|---|---|---|

## 情景压力
| 情景 | 可能影响 | 受影响仓位 | 应对 |
|---|---|---|---|

## 优先动作
1.
2.
3.
```
