[English](README.md) | [简体中文](README.zh-CN.md)

# DailyTrades：交易投研系统

一个 AI-native、基于贝叶斯理念的决策支持 Skill，把市场、宏观、政策、公司、Price Action 和组合证据压缩成可持续更新的决策流程。它不试图预测下一步行情，而是用新证据更新先验、比较条件情景，并明确什么后续观察会改变当前判断。

版本：`0.3.0`

## 30 秒安装

安装完整的 portable Agent Skill。安装器会检测支持的 coding agent 并适配目标目录。

```bash
npx skills@latest add Archerouyang/dailytrades --skill trading-research-system -g
```

## 首次使用

新开一个任务并发送：

```text
开始今日交易研究
```

同一个 Skill 会先检查 runtime health；如果不存在 private runtime，就自动进入空白首次设置，确认本地 runtime 位置，并询问是否启用可选的授权只读数据源。它不会恢复或推断观察清单、交易偏好、持仓、计划、凭据、connector 授权或研究历史。

## 已验收输出示例

以下图片是用户选择性导出的已验收 chat-inline 面板 PNG。数据来自有明确日期的公开市场快照，不包含券商账户、private runtime 或私人持仓信息；它们是研究快照，不是实时行情或交易指令。

### 宏观环境面板

![展示收益率曲线、通胀、风险广度和一个月趋势分析的宏观环境面板](docs/assets/readme/macro-regime-live-2026-07-19.png)

宏观面板把当前流动性环境与长短端利率、通胀、NDX/RUT 市场广度、波动率、美元、信用、油价及下一阶段重点事件联系起来。

### NVDA 4H Price Action 面板

![包含情景、关键位、分段建仓和公司事件的 NVDA 4H Price Action 面板](docs/assets/readme/nvda-4h-pa-entry-plan.png)

Price Action 面板把观察与行动分开，同时展示周期与数据来源、当前结构、条件路径、关键位、失效条件、分段执行和股票自身事件。

交互式 chat-inline HTML 仍是主要视觉产物；只有用户明确选择导出时才保存 PNG。TradingView attribution 和 Apache-2.0 许可见[第三方声明](THIRD_PARTY_NOTICES.md)。

## 工作流

```mermaid
flowchart TB
  GOAL(["自然语言研究目标"])

  subgraph PUBLIC["PUBLIC SKILL · 研究循环"]
    direction TB
    subgraph DISCOVER["01 · 建立研究判断"]
      direction LR
      ROUTE{"识别任务"} --> RESEARCH["研究<br/>宏观 · 个股 · 研报"]
      RESEARCH --> VERIFY["校验<br/>观点 · 信源"]
    end
    subgraph OPERATE["02 · 执行市场计划"]
      direction LR
      PLAN(["Active Market Plan"]) --> TRACK["追踪<br/>setup · 点位"]
      TRACK --> REVIEW["复核<br/>风险 · 交易"]
    end
    VERIFY --> PLAN
    REVIEW -. "沉淀经验" .-> PLAN
  end

  subgraph PRIVATE["PRIVATE RUNTIME · 用户所有"]
    direction LR
    RUNTIME[("偏好 · 观察清单 · 持仓 · 历史")]
  end

  GOAL --> ROUTE
  PRIVATE -. "仅提供本地上下文" .-> ROUTE
  REVIEW --> RESULT(["决策摘要 · 下一检查点"])

  classDef terminal fill:#1f2328,stroke:#1f2328,color:#ffffff,stroke-width:1.5px
  classDef gate fill:#fff8c5,stroke:#9a6700,color:#1f2328,stroke-width:1.5px
  classDef step fill:#ffffff,stroke:#57606a,color:#1f2328,stroke-width:1.5px
  classDef plan fill:#dafbe1,stroke:#1a7f37,color:#1f2328,stroke-width:2px
  classDef runtime fill:#f6f8fa,stroke:#8c959f,color:#57606a,stroke-width:1.5px
  class GOAL,RESULT terminal
  class ROUTE gate
  class RESEARCH,VERIFY,TRACK,REVIEW step
  class PLAN plan
  class RUNTIME runtime
  style PUBLIC fill:#f6f8fa,stroke:#d0d7de,stroke-width:1.5px
  style DISCOVER fill:#ffffff,stroke:#d8dee4,stroke-width:1px
  style OPERATE fill:#ffffff,stroke:#d8dee4,stroke-width:1px
  style PRIVATE fill:#ffffff,stroke:#8c959f,stroke-width:1.5px,stroke-dasharray:5 5
```

用户只需用自然语言描述研究目标，Skill 会自主选择内部 workflow；新用户不需要记住 focused workflow 名称。

## 能力与数据来源

| 能力 | Skill 输出 | 信源规则 |
| --- | --- | --- |
| 周度与每日市场研究 | Active Market Plan 变化、事件优先级和下一步 | 校验当前事实，只展示影响决策的变化 |
| 宏观、利率与政策 | 市场环境、传导路径和受影响计划 | 官方一手信源优先；授权 macrodata 提供指标值 |
| 个股与研报研究 | thesis、counter-thesis、Claim Ledger、Verification Queue | 只使用公开、已授权或用户提供的内容，不绕过付费墙 |
| Price Action | 明确时间框架、趋势/震荡环境、点位和 setup 条件 | 使用授权 OHLCV；canonical 图表使用 TradingView Lightweight Charts |
| Alpha Lab 输入 | 用于研究排序的已发布 champion 排名、历史变化和不确定性 | 只读私有 store；保留模型排名，不可用时安全降级 |
| 组合风险 | 集中度、产品、主题、券商暴露和重大风险旗标 | 授权只读 broker facts 或用户明确提供的数据 |
| 交易复盘 | 下单后与平仓后的背景、错误和经验 | 只读成交事实加用户确认 |

私有 Alpha Lab 可用时，Skill 只把已发布的 champion 排名作为研究优先级输入，不会在 agent 内训练或重排模型。Alpha 契约与自动化细节见 [Alpha Lab 计划](docs/ALPHA_LAB_PLAN.md)。

本系统只提供决策支持，不保证收益，不替代受监管的投资建议，也不会把单个数据点直接转成交易指令。

## Public Skill / Private Runtime

| Public Skill | Private Runtime |
| --- | --- |
| 一个可安装的 `trading-research-system` 包，包含 workflow、references、scripts、空白模板和合成 fixtures | 用户自己的交易偏好、观察清单、持仓、Active Market Plan、setup、复盘、凭据和 connector 授权 |
| 可以公开发布和升级 | 始终位于公开仓库和分发包之外 |
| 不内置个人默认值 | 只有用户明确授权本地写入后才创建 |

安装和升级绝不会复制、推断、同步或恢复 private state。券商和行情集成是可选能力，必须单独授权且只读。**No order actions：**Skill 永远不会创建、修改、取消或提交真实订单。

## 故障排查与详细文档

| 现象 | 检查 |
| --- | --- |
| 找不到 Skill | 确认仓库可访问，并检查安装输出是否只列出 `trading-research-system`。 |
| 新任务没有个人数据 | 这是预期行为；首次运行保持空白，直到用户明确初始化 private runtime。 |
| 券商或宏观数据不可用 | 单独授权对应的可选只读来源；安装 Skill 不会授予 connector 权限。 |
| 无法导出选中的 inline panel | 用户选择性 PNG 导出需要 Chrome/Chromium；chat-inline HTML 仍是主产物。 |

详细文档：[Skill 契约](skills/trading-research-system/SKILL.md)、
[交付契约](docs/adr/0009-research-result-delivery-contract.md)、
[0.3.0 module ownership](docs/adr/0010-deep-module-ownership-for-0.3.0.md)、
[MVP Runbook](docs/MVP_RUNBOOK.md) 和
[分发计划](docs/DISTRIBUTION_AND_README_PLAN.md)。

DailyTrades 使用 MIT License；第三方组件保留各自许可证。
