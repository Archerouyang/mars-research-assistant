# Mars Skills

一个由独立、中文交易研究 Skills 组成的集合。每个 Skill 只完成一种交付；Ask Mars
只帮助判断下一步，不会代替用户自动研究或写入。

当前可用：

- **Ask Mars**：推荐应使用的 Skill、执行顺序、第一步与最少输入。
- **市场催化剂简报**：交付区分已定事件与发展中风险的中文 Markdown 简报。
- **市场快照**：交付带来源、时间与可见数据缺口的中文 Markdown 市场快照。
- **标的研究**：交付基于 SEC/发行人 IR 一手证据的单标的基本面、行业与公司事件研究。
- **Price Action**：仅在 OHLCV 合格时交付价格结构、关键位、情景与失效条件研究。
- **Drive 写入**：先提议归档位置与操作，只有明确确认后才将已完成研究写入交易研究中心。

后续 Skill 将按同一套离线验收入口独立加入，不把数据源、可视化或 Drive 写入变成
所有研究的前置条件。

## 安装

安装器只交付完整的六个 Mars Skills：

```bash
bash scripts/install-mars-skill.sh --target /path/to/agent-skills
```

脚本会在写入前验证全部源目录和目标冲突；若任一同名 Skill 已存在，会停止而不覆盖或部分安装。

安装命令只会写入明确给出的目标目录，且不会覆盖同名 Skill。开发环境使用 `uv`：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

## 可选本地 FMP

免费基础能力不需要 API key。Price Action 在没有用户提供合格 OHLCV 时，会先询问是否使用
本地私密配置的 FMP；用户未配置或明确不使用 FMP 时，才使用 yfinance。若用户已选择 FMP
但它不可用、未授权、限流或数据不合格，Skill 会说明原因并询问是否切换 yfinance，不会静默
降级。yfinance 必须标为非官方 best-effort，且仍须通过与 FMP 相同的 OHLCV 质量检查；合格
日线输入会交付同一份 Markdown 中的静态 SVG，数据不合格则只交付状态和缺口。

本仓库不保存、读取或要求任何 FMP 凭据。不要将凭据放入仓库、Skill 目录、fixture、文档或日志。

## 验证

```bash
bash scripts/verify-mars-skills.sh
```

这是唯一的离线发布验收入口：它检查六个 Skill 的发现与独立安装、fixture 场景、来源/时间/缺口
标注、确认写入边界，以及凭据、私有路径和退役能力的公共表面门禁。该命令只使用本地 fixture
和临时目录；不会请求市场数据、读取账户、写入 Drive 或需要任何凭据。
