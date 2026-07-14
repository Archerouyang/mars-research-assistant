# 持仓日报 - 2026-06-24

Source: broker-live fixture
Read time: 2026-06-24T20:00:00Z
Coverage: 2 broker/account source(s): IBKR:SIM-IBKR, Longbridge:SIM-LB
Data status: fixture
Snapshot saved: fixture

## 结论

- 总资产 $85,060；已投资 82.4%；现金 17.6%。
- 最大主题 `tech_beta` 为 42.6%；最大单一持仓 `QQQ` 为 42.6%。
- 产品暴露：etf_common 43.7%, sector_etf 24.5%, stock_common 14.2%；杠杆/单股 ETF 1.1%。
- 未实现盈亏合计 $2,860；本报告只提示复核项，不生成任何订单动作。

## 需要用户决策

| 优先级 | 持仓/主题 | 问题 | 可选动作 | 需要确认 |
| --- | --- | --- | --- | --- |
| P1 | tech_beta | 主题集中度 42.6% | 维持 / 暂停新增同主题 / 降低相关风险 | 是否仍允许新增同主题 setup |
| P1 | QQQ | 单一持仓权重 42.6% | 继续持有 / TP再平衡复核 / 暂停加仓 | Active Market Plan 对该持仓的动作 |
| P2 | cash | 现金 17.6% | 保留 / 等待计划内 setup / 补充风险缓冲 | 今日是否有计划内新增风险 |
| P2 | 杠杆/单股 ETF | 暴露 1.1% (TSMX 0.8%, MVLL 0.2%) | 维持 / 暂停新增 / 降低路径风险 | 是否允许继续叠加杠杆或隔夜风险 |

## 风险变化

| 风险 | 当前状态 | 变化 | 影响 | 需要观察 |
| --- | --- | --- | --- | --- |
| 集中度 | `tech_beta` 42.6% / `QQQ` 42.6% | 来自当前 snapshot | 限制新增同向风险 | Active Market Plan risk budget |
| 产品结构 | etf_common 43.7%, sector_etf 24.5%, stock_common 14.2% | 来自当前 snapshot | 区分核心 ETF、行业 ETF、个股和杠杆产品 | instrument-specific risk budget |
| 杠杆/单股 ETF | TSMX 0.8%, MVLL 0.2% | 来自当前 snapshot | 路径依赖、波动衰减和隔夜风险需单独复核 | holding period / event risk |
| Broker exposure | IBKR:SIM-IBKR 67.1%, Longbridge:SIM-LB 32.9% | 来自当前 snapshot | 防止漏读账户导致仓位判断失真 | broker authorization and stale data |
| 现金 | 17.6% | 来自当前 snapshot | 决定是否有新增仓位空间 | buying power / planned adds |
| Broker coverage | 2 broker/account source(s): IBKR:SIM-IBKR, Longbridge:SIM-LB | fixture | 缺失来源会降低置信度 | authorization and stale data |
| 期权 | no option positions in snapshot | - | 无 0DTE/LEAP 仓位字段 | broker orders/executions if needed |

## 持仓影响

| 持仓 | 定位 | 当前影响 | Active Market Plan 动作 | 备注 |
| --- | --- | --- | --- | --- |
| QQQ | tech_beta / etf_common | weight 42.6%; uPnL $1,250 | 继续持有；新增同主题风险前先复核 | core ETF fixture |
| SOXX | semiconductor / sector_etf | weight 24.5%; uPnL $1,200 | 继续观察；按 setup/计划复核 | semiconductor fixture |
| CRDO | ai-infra-momentum / stock_common | weight 14.2%; uPnL $300 | 继续观察；按 setup/计划复核 | synthetic broker-live fixture |
| TSMX | ai-hardware-leverage / etf_common | weight 0.8%; uPnL $100 | 继续观察；新增或隔夜前复核路径风险 | leveraged ETF fixture; 2x TSM exposure |
| MVLL | ai-hardware-leverage / etf_common | weight 0.2%; uPnL $10 | 继续观察；新增或隔夜前复核路径风险 | leveraged ETF fixture; 2x MRVL exposure |

## 可视化

- Allocation by symbol: QQQ 42.6%, SOXX 24.5%, CRDO 14.2%, TSMX 0.8%, MVLL 0.2%
- Theme / sector exposure: tech_beta 42.6%, semiconductor 24.5%, ai-infra-momentum 14.2%, ai-hardware-leverage 1.1%
- Instrument exposure: etf_common 43.7%, sector_etf 24.5%, stock_common 14.2%
- Broker / account exposure: IBKR:SIM-IBKR 67.1%, Longbridge:SIM-LB 32.9%
- Leveraged / path-risk exposure: TSMX 0.8%, MVLL 0.2%
- PnL contribution: total unrealized $2,860
- Risk heatmap: top theme `tech_beta` and top symbol `QQQ` need review before adding correlated exposure.

## 数据缺口

- This report uses the provided standard portfolio snapshot; it does not verify live broker authorization by itself.
- Account-level margin, buying power, option Greeks, and current orders may require broker-live reads.
- Values may be delayed, fixture, or user-provided according to the data status above.
