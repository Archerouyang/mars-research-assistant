---
name: instrument-research
description: 为单一、身份可唯一核验的上市公司生成轻量中文个股快览，包含公开关键数据、近 30 天直接相关公司新闻和明确缺口。Use when the user asks for a company or ticker overview, recent company developments, or a quick stock research snapshot; not for valuation, deep modelling, macro, or technical analysis.
---

# 个股快览

同目录的 `capability.json` 定义交付与验收边界。

```mars-skill-policy
{"delivery":"local_markdown_equity_snapshot","forbidden_effects":["valuation","technical_analysis","macro_analysis","account_access","broker_write","drive_write","persistent_state"]}
```

只处理一家公司。先核验公司名称、ticker、交易所和发行人身份；不带市场后缀的 ticker 可先
按美股候选核验，但不能确认或存在同名歧义时，要求用户澄清并且不创建工件。用户明确的市场
覆盖默认美股语境；用户所在地和系统时区不得选择市场。

## 工作流

1. 从监管披露、交易所和发行人 IR 确认身份和最新财务事实。价格、规模和估值锚使用可公开
   核验的报价来源；每项都标明 `as_of`。搜索结果摘要不是证据。
2. 只收集最近 30 天内与该公司直接相关的 3–5 条公告或新闻。优先公司公告；必要时使用可信
   媒体原文，并说明它不是一手公告。
3. 默认在活动工作目录的 `mars-research/` 创建唯一的
   `YYYY-MM-DD-SYMBOL-quick-look[-NN].md`；用户显式指定其他本地目录时使用该目录。绝不覆盖
   已有文件或写入安装目录。聊天中只简要说明已生成的本地工件和关键缺口；文字正文以 Markdown
   源稿为准。

工件按以下顺序交付：发行人身份；一组关键公开数据（价格、规模或估值锚、最新财务摘要）；
最近 30 天公司相关公告或新闻；来源与时间戳；数据缺口。事实与推断必须区分，所有缺失数据
如实记录。不得加入估值、技术面、宏观观点、买卖、仓位或交易指令。
