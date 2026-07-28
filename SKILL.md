---
name: mars-research-assistant
description: 火星投研组合 Skill 的根入口。识别研究意图，选择并编排包内六个可独立调用的 Skill，显式传递证据上下文，并披露公开网络、本地写入、uv 受管安装及经确认的 Google Drive 写入边界。
---

# 火星投研助手

这是完整组合包的根 Skill，也是 RED Skill 上传入口。它不取代六个子 Skill：根入口负责理解
组合请求、选择最小能力集合、安排可并行步骤并显式传递上下文；用户也可以直接调用任一子
Skill，子 Skill 不得假设根入口或前置步骤已经运行。

## 权限与降级

- 研究能力会读取公开网络；技术面分析的唯一内置行情源是 yfinance（非官方、best-effort）。
- 受管安装器会在目标包内写入文件，并执行 `uv sync --locked` 创建包内 `.venv`。
- 研究工件只写入用户指定目录；不读取券商账户、持仓或订单，不交易，不读取 API key，
  不运行后台任务、每日检测、隐式缓存或遥测。
- Google Drive 写入是可选能力。只有用户对当前初始化或归档提议单独明确确认后才可写入；
  两种确认互不授权。
- 权限或数据不足时，明确失败或降级，不切换隐藏来源，也不扩大权限。

如果上传平台只保留本 Markdown，当前入口只能帮助用户识别能力和给出受管安装指引；不得
声称 `scripts/`、`.venv` 或六个子 Skill 已经可用。完整能力需从
`https://github.com/archerthegoat/mars-research-assistant` 获取仓库后运行：

```bash
git clone https://github.com/archerthegoat/mars-research-assistant.git
cd mars-research-assistant
bash scripts/install-mars-skill.sh \
  --target /path/to/agent-skills/mars-research-assistant
```

不支持以 pip、手工复制或第三方下载器冒充受管安装。

## 六个可直接调用的 Skill

- Ask Mars：`skills/ask-mars/SKILL.md`
- 市场催化剂简报：`skills/market-catalysts-brief/SKILL.md`
- 市场快照：`skills/market-snapshot/SKILL.md`
- 标的研究：`skills/instrument-research/SKILL.md`
- 技术面分析：`skills/technical-analysis/SKILL.md`
- Drive 写入：`skills/drive-writeback/SKILL.md`

## 编排规则

1. 先识别用户最终要交付的结果，只选择必要子 Skill。Ask Mars 只给建议，不自动研究。
2. 彼此独立且用户已提供输入的研究可以并行；有证据依赖的步骤必须等待上游完成。
3. 跨步骤只传递显式工件或结构化摘要，并携带来源、`as_of`、时区和数据状态。缺少上游
   上下文时，子 Skill 仍应独立完成自己的边界，不能猜测。
4. 市场背景传给技术面分析时只解释共振或冲突，不改变技术证据、关键位或证据标识。
5. Drive 写入永远是最后的独立提议；初始化成功后不自动归档，归档成功也不授权初始化。
