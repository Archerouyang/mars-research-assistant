---
name: deep-equity-research
description: 为单一、身份可唯一核验的上市公司生成九章中文深度基本面研究，含财报质量检查和数据齐备时可复算的三情景 DCF／反向 DCF。Use when the user explicitly requests deep research, valuation, earnings review, an investment memo, competitive analysis, or modelling; not for a quick company snapshot or direct trading advice.
---

# 深度个股研究

同目录的 `capability.json` 定义交付、估值输入和离线验收边界。

```mars-skill-policy
{"delivery":"local_markdown_deep_equity_research","forbidden_effects":["trade_recommendation","position_sizing","technical_analysis","account_access","broker_write","drive_write","persistent_state"]}
```

只处理一家公司。开始取数前核验公司名称、ticker、交易所和发行人；不能唯一对应时要求澄清，
不创建工件。事实优先使用监管披露、交易所和发行人 IR；价格、规模和估值锚使用可公开核验
报价并标注 `as_of`；搜索摘要不是证据。冲突、无法取得的资料和推断均须明确标记。

## 工作流

1. 在活动工作目录的 `mars-research/` 创建唯一的
   `YYYY-MM-DD-SYMBOL-deep-research[-NN].md`；绝不覆盖既有文件，也不写入安装目录。
2. 交付固定九章：研究范围与核心判断；公司与商业模式；行业与竞争格局；管理层、治理与
   资本配置；财务表现与质量核查；预期差、催化剂与关键跟踪项；估值；风险、反方论点与可
   证伪条件；来源、时间戳、假设与数据缺口。
3. 财报质量至少核查：收入、利润、经营现金流趋势的一致性；现金转换与应计质量；应收账款
   与递延收入相对收入的异常变化；股本稀释或 SBC、审计意见和治理红旗。每项都需要来源，
   缺失则记录缺口；不输出 A–D 等级或默认使用 Beneish M-Score。
4. 只有来源可追溯 JSON 同时具有价格、股本、净债务、WACC、永续增长率及三情景 FCF 路径时，
   才运行包内 `scripts/render_deep_equity_research.py` 计算 DCF。缺少任一输入则保留估值章，
   写明数据缺口，不用模型记忆补数。反向 DCF 仅在额外输入齐备时运行。

结论、预期差、估值范围和风险必须可审计，却不得变成买入、卖出、持仓比例、下单或其他交易
动作。Markdown 是默认源稿；仅在用户要求或图表、对比确实显著改善理解时另生成 PDF/PPT。
