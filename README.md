# 火星投研助手

把宏观、行业事件、公司基本面与价格行为，收束成可复核的研究判断。

它不预测下一根 K 线，也不替你下单。它做的是把证据、反方观点、失效条件和下一步验证点放在同一条研究链上，让交易判断可以持续更新。

## 安装

```bash
npx skills@latest add Archerouyang/mars-research-assistant --skill mars-research-assistant -g
```

新开任务后直接说：

```text
开始今日交易研究
```

## 你会得到什么

**宏观先行，但不拿半成品凑数。**

系统先检查 Longbridge 与 IBKR 的可用能力，再逐字段获取宏观数据。每个字段优先使用合格的券商市场/宏观数据；没有精确字段时才回退到公开一手来源。只要关键字段不完整，就返回明确的数据获取阻塞，而不是用 ETF、新闻或猜测代替。

**持仓只在你同意后读取。**

持仓展示只给出券商、标的、数量、最新价格、市值、成本、未实现盈亏、现金与读取时间。它不会暗中读取账户，不会把缺失字段补成推测，也不会自动生成组合建议。

**点名标的，直接进入研究。**

例如：`分析 NVDA`、`做 TSM 的 4H PA`。默认会给出行业事件、基本面、催化、估值、反方风险，以及冻结样式的 4H Price Action Board；不会要求你先走完持仓或默认流程。

![NVDA 4H Price Action 示例](docs/assets/readme/nvda-4h-pa-entry-plan.png)

## 工作方式

```text
开始今日交易研究
        ↓
券商能力检查 → Macro Board 或数据获取阻塞
        ↓
展示默认券商持仓 / 直接研究指定标的
        ↓
按新证据更新判断，而不是把一次观点当结论
```

所有图表使用可独立打开的 standalone Board。市场字段采用最近共同完成收盘，不把盘中、盘前和不同日期的数据混成一张宏观图。

## 明确边界

- 只做研究与决策支持，不创建、修改、取消或提交真实订单。
- 券商账户读取必须单独获得同意；安装 Skill 不等于授权账户。
- 不把私人持仓、凭证、运行时数据或原始券商响应写入公开仓库。
- 不把预测、目标价、情景或模型输出说成确定结果。

## 开发与验证

```bash
bash scripts/verify-skill.sh
```

核心行为说明见 [Skill 契约](skills/mars-research-assistant/SKILL.md)，字段与交互边界见 [火星投研助手 1.0 规格](docs/MARS_RESEARCH_ASSISTANT_1_0_SPEC.md)。

MIT License。第三方组件保留各自许可证，详见 [第三方声明](THIRD_PARTY_NOTICES.md)。
