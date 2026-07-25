# 火星投研助手

一个开箱即用的无状态研究 Skill：针对当前问题交付中文 Markdown，以及至多一个自包含 HTML Board。它不会创建 runtime、计划、缓存或历史记录，也不会读取账户、持仓或订单。

支持三种研究：

- **Macro Regime**：先给未来七天和过去 24 小时的重大事件简报；仅在完整字段可得时给 Macro Board。
- **Instrument Research**：公司基本面、行业与公司事件；不默认附带宏观、对标公司或技术图。
- **Price Action**：仅在明确问趋势、点位、入场、减仓或交易计划时，使用 120 根完成日线输出。

## 安装

安装 Skill：

```bash
npx skills@latest add Archerouyang/mars-research-assistant --skill mars-research-assistant -g
```

若需要在仓库中运行脚本，唯一受支持的 Python 环境是 `uv`：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

`requirements.txt` 由 `uv pip compile` 生成并精确锁定。不要使用全局 `pip install`。

Longbridge CLI 是可选的独立二进制，不在 Python 依赖中。Skill 会先只读检查其授权状态；即使授权有效，也会在每次研究前询问是否使用。没有账号、CLI 或授权时，自动使用 Portable Profile（yfinance + Web Search 与原始来源）。仅在你明确同意时，才按 [Longbridge 官方文档](https://longbridgeapp.github.io/openapi/zh-CN/) 安装并登录 CLI。

## 示例

```text
下周宏观要注意什么？
分析 NVDA 的基本面、行业和公司催化
给 TSLA 做日线趋势、关键位和入场情景
```

## 数据与安全

- Longbridge 优先用于语义等价的结构化市场、公司、财务、日历和新闻发现字段；缺口才按批次回退。
- Web Search 只发现候选来源；重大事件须带受限 `evidence_kind` 与已确认的一手来源，才可进入 Brief 与 Board。
- 每个字段保留来源与时间；不以代理值掩盖缺口。
- 不下单，不读取账户、持仓、订单、凭据或 token。

开发验证：

```bash
bash scripts/verify-skill.sh
```

MIT License。
