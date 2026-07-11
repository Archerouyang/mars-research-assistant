# 周末首次启动

## 当前日程阶段

- stage: `weekly_deep_update（周末首次启动）`
- reason: 周末、`startup_status=partial`；按“先摘要，后授权/初始化”提供降级研究价值。

## 读取状态

| item | status | effect |
| --- | --- | --- |
| runtime_origin | default | formal runtime 使用默认私有路径，不是 UAT repo 或 fixture 路径 |
| startup_status | partial | 可以做公开来源研究，不能声称已读取完整 Active Market Plan |
| formal runtime | available | runtime directory 已存在于默认私有路径 |
| Longbridge | needs_review | 不推断 unauthorized，本轮不会读取 broker |
| IBKR | needs_review | 不推断 unauthorized，本轮不会读取 broker |
| public-source fixture | available | 仅用于本次确定性 reduced-scope 示例 |

## 可用研究摘要

- 利率：10Y 4.45%，仍低于 `4.50% pressure line`；若突破该线，高 beta/久期资产的研究优先级下调。
- 波动：VIX 18.2，低于 `VIX 20` 压力阈值；当前未显示压力确认，但需等待下周事件后的实际读数。
- 事件：`P0 CPI release` 是下周首要验证点；结果公布前只建立情景，不预判方向。
- 主题：QQQ/SOXX 仅作为 watch-only 主题；在 setup key 完整前不生成点位或交易触发。
- 本摘要只建立研究优先级，不是买卖指令。

## 降级范围

- formal runtime 为 `available`，但 `startup_status=partial`；`market-plan.md` 与当日日程包仍缺失，没有把 repo fixture 当成 Active Market Plan。
- broker source 为 `needs_review`；不会读取 broker，也不假设账户暴露。
- 缺少 `ticker + trade_horizon + instrument` 时只给 watch-only 摘要，不开始深度标的/setup 研究。
- CPI、10Y、VIX 是确定性 fixture 示例，不代表 fresh-chat 已完成实时市场核验。

## 缺失确认

- broker read-only：Longbridge / IBKR / 两者 / 暂不启用。
- setup key：`ticker + trade_horizon + instrument`。
- runtime：仅看 dry-run 初始化方案，或确认实际初始化。

## 券商只读来源设置

| source | status | 本轮选择 |
| --- | --- | --- |
| Longbridge | needs_review | Longbridge read-only / 两者都启用 / 暂不启用 |
| IBKR | needs_review | IBKR read-only / 两者都启用 / 暂不启用 |

是否启用只读 broker 数据？选项：Longbridge read-only / IBKR read-only / 两者都启用 / 暂不启用。

## 建议下一步

默认建议: 先确认 setup key，再做宏观/标的深研和周度计划草稿。

## 下一步指引

- 你只需要回复：`QQQ + medium-term swing + ETF；broker 暂不启用；runtime 仅 dry-run。`
- 这是默认低权限路径；不会写 runtime，也不会读取 broker。

## 确认后我会执行

确认后先执行宏观/标的深研，再生成周度 Active Market Plan 草稿；只有用户另行确认才写 runtime。

## 安全边界

- 本轮不会写 runtime。
- 不会读取 broker 私有账户数据。
- 不会创建、修改、取消或提交订单。
