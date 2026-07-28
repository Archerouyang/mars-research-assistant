---
name: instrument-research
description: 针对用户指定的单一股票或其他可识别标的，生成中文 Markdown 基本面、行业与公司事件研究。需要核对发行人身份并优先使用 SEC 披露和发行人 IR；不用于宏观判断、市场快照或技术面分析。
---

# 标的研究

同目录的 `capability.json` 定义本 Skill 的公开交付边界与离线验收场景。

```mars-skill-policy
{"delivery":"markdown_research","forbidden_effects":["macro_analysis","technical_analysis","account_access","broker_write","drive_write","persistent_state"]}
```

只研究一个明确的标的。先确认 ticker、交易所和发行人身份；对适用的美国发行人，优先使用
SEC EDGAR 披露；对业绩、指引、产品或公司事件，优先使用发行人 IR。非美国发行人使用
其监管披露与发行人 IR，并说明 SEC 资料不适用。

默认交付中文 Markdown，并清楚区分：

- **事实与证据**：发行人身份与每项公司事实都附来源链接和 `as_of`；不要将聚合报价、
  新闻摘要或二手数据库伪装成公司事实。
- **基本面、行业背景、公司事件**：只写已取得证据支持且与该标的有关的内容。
- **推断**：明确标为推断，写明依据与后续验证条件；不要把推断写成事实或投资建议。
- **数据缺口**：发行人身份、披露、时效或证据不足时说明范围与所需资料。若身份无法确认，
  停在该处，不生成公司基本面。

不要自动加入宏观、市场快照、价格结构、关键位、仓位、订单或交易指令。不要访问账户、
持仓或订单，不写入 Drive，也不持久化研究状态。
