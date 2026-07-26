# Mars Skills

一个由独立、中文交易研究 Skills 组成的集合。每个 Skill 只完成一种交付；Ask Mars
只帮助判断下一步，不会代替用户自动研究或写入。

当前可用：

- **Ask Mars**：推荐应使用的 Skill、执行顺序、第一步与最少输入。
- **市场催化剂简报**：交付区分已定事件与发展中风险的中文 Markdown 简报。
- **市场快照**：交付带来源、时间与可见数据缺口的中文 Markdown 市场快照。
- **标的研究**：交付基于 SEC/发行人 IR 一手证据的单标的基本面、行业与公司事件研究。

后续 Skill 将按同一套离线验收入口独立加入，不把数据源、可视化或 Drive 写入变成
所有研究的前置条件。

## 安装

在本地仓库中安装 Ask Mars：

```bash
bash scripts/install-mars-skill.sh --skill ask-mars --target /path/to/agent-skills
```

安装其他研究 Skill 时，将 `ask-mars` 替换为对应 id，例如
`market-catalysts-brief`、`market-snapshot` 或 `instrument-research`。每个 Skill 都可单独安装。

安装命令只会写入明确给出的目标目录，且不会覆盖同名 Skill。开发环境使用 `uv`：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

## 验证

```bash
bash scripts/verify-mars-skills.sh
```

该命令只使用本地 fixture 和临时目录；不会请求市场数据、读取账户、写入 Drive 或
需要任何凭据。
