# 滚动盘面确认

## 运行状态

- 当前状态：待复核（内部限定：watch-only）

## 当前范围

- setup key: DRAM、SOXX、QQQ 均缺少 `trade_horizon + instrument`
- Active Plan: formal runtime 不可用；repo fixture 未读取、未借用
- concrete PA output: blocked，等待逐 ticker 确认完整 setup key

## Watch-only 摘要

- DRAM：仍是未确认的 watch ticker；不主张结构、方向或风险角色。
- SOXX：仍是未确认的 watch ticker；不主张结构、方向或风险角色。
- QQQ：仍是未确认的 watch ticker；不主张结构、方向或风险角色。

## 可执行下一步

- 初始化今日运行包：仅在用户明确授权 runtime 写入后执行。
- 生成盘中观察清单：先确认 DRAM、SOXX、QQQ 各自完整 setup key，并在用户明确授权 runtime 写入后再生成。

## 聚焦确认问题

请分别确认 DRAM、SOXX、QQQ 各自的 `trade_horizon` 和 `instrument` 是什么？
