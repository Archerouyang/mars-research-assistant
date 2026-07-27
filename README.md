# Mars Skills 1.0

面向中文交易研究的独立 Skill 集合。每个 Skill 只交付一种明确结果：研究、建议或经确认后的归档；
不读取账户、不执行交易，也不把多个研究任务混成一次自动操作。

## 快速开始

在仓库根目录一次安装全部六个 Skills：

```bash
bash scripts/install-mars-skill.sh --target /path/to/agent-skills
```

安装器只提供这一种完整安装方式。它会先检查六个源目录与全部目标冲突；任一同名 Skill 已存在时，
会停止且不会覆盖或部分安装。

安装后可以先询问 Ask Mars，例如：

> 下周美股有哪些值得关注的宏观和地缘政治催化剂？之后我想研究 GOOGL 的日线价格结构。

## 包含的 Skills

| Skill | 交付 | 不会做什么 |
| --- | --- | --- |
| Ask Mars | 推荐最小 Skill 序列、第一步与所需输入 | 不自动研究或写入 |
| 市场催化剂简报 | 已定事件与持续风险的市场催化剂简报 | 不生成交易指令 |
| 市场快照 | 带来源、时间与数据缺口的市场状态摘要 | 不替代事件日历或技术分析 |
| 标的研究 | 基于 SEC 与发行人 IR 的基本面、行业和公司事件研究 | 不自动加入宏观或技术判断 |
| Price Action | 价格结构、关键位、情景与失效条件 | 不访问账户、不下单 |
| Drive 写入 | 先展示归档提议，确认后写入交易研究中心 | 未确认时绝不写入 |

## 数据与安全边界

- Price Action 只使用 yfinance 的非官方、best-effort OHLCV；不需要 API key，也没有其他数据源或回退路径。
- 日线结论要求带时区、复权 OHLCV、成交量与合适时间范围；少于 319 根日线时不绘制完整 SMA200 图，也不输出技术结论。
- 所有研究都应标记来源、`as_of` 与数据缺口。数据不足时，只报告状态与缺口。
- 不要把任何凭据放入仓库、Skill 目录、fixture、文档或日志。

## 开发与验证

开发环境使用 `uv`：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
bash scripts/verify-mars-skills.sh
```

这是唯一的离线发布验收入口：它验证六个 Skill 的发现与完整安装、fixture 场景、
来源/时间/缺口标注、确认写入边界，以及凭据、私有路径和退役能力的公共表面门禁。它只使用本地
fixture 和临时目录；不会请求市场数据、读取账户或写入 Drive。
