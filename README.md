# Mars Skills

面向中文交易研究的独立 Skill 集合。每个 Skill 只交付一种明确结果：研究、建议或经确认后的归档；
不读取账户、不执行交易，也不把多个研究任务混成一次自动操作。

未指定目标市场时默认进行美股投研，采用 USD、`America/New_York` 和 NYSE/Nasdaq
语境；用户位置与系统时区不会改变目标市场。用户明确指定其他市场时以用户输入为准。

## 快速开始

先安装 [uv](https://docs.astral.sh/uv/)。使用通用 Skills CLI 时，必须选择根组合 Skill，
让六个子 Skill、脚本和锁文件作为一个目录安装：

```bash
DISABLE_TELEMETRY=1 npx skills add archerthegoat/mars-research-assistant \
  --skill mars-research-assistant \
  --agent codex \
  --global \
  --copy \
  --yes
```

通用 CLI 负责复制 Skill，不执行仓库脚本。首次调用技术面分析时，该 Skill 会先运行自己的
幂等环境门，自动让 uv 准备 Python 3.12、包内 `.venv` 和锁定的 yfinance；其他五个 Skill
不触发 uv。不要只安装 `technical-analysis` 子目录，因为它需要根锁文件。

从 Git 仓库拉取时，可在仓库根目录立即完成同一环境准备和受管安装：

```bash
bash scripts/install-mars-skill.sh \
  --target /path/to/agent-skills/mars-research-assistant
```

仓库安装器是支持原子升级与定制保护的完整包受管入口。它先在目标目录旁构建完整候选包，再调用技术面
分析 Skill 自带的环境门：缺少 Python 3.12 时由 uv 安装受管解释器，并按锁文件创建包内
`.venv`。通过离线自检后才整体替换目标；失败不会破坏旧安装。锁文件未变的升级会复用
已有环境。已定制的受管安装默认停止，确认愿意覆盖后才使用 `--force`。不回退到 pip，
也不污染用户项目或全局 Python。

安装后可从根 `SKILL.md` 组合调用，也可直接调用任一子 Skill。可以先询问 Ask Mars：

> 下周美股有哪些值得关注的宏观和地缘政治催化剂？之后对 GOOGL 做日线技术面分析。

## 包含的 Skills

| Skill | 交付 | 不会做什么 |
| --- | --- | --- |
| Ask Mars | 推荐最小 Skill 序列、第一步与所需输入 | 不自动研究或写入 |
| 市场催化剂简报 | 已定事件与持续风险的市场催化剂简报 | 不生成交易指令 |
| 市场快照 | 带来源、时间与数据缺口的市场状态摘要 | 不替代事件日历或技术面分析 |
| 标的研究 | 基于 SEC 与发行人 IR 的基本面、行业和公司事件研究 | 不自动加入宏观或技术判断 |
| 技术面分析 | Markdown 分析、evidence JSON 与临时交互图表 | 不访问账户、不下单 |
| Drive 写入 | 幂等初始化交易研究中心，或归档已完成研究 | 初始化和归档分别确认，未确认时绝不写入 |

## 技术面分析示例

> 以下为确定性合成 `DEMO` fixture 生成的离线示例，非当前市场数据。真实 yfinance
> 截图与完整摘要将在集成验收任务中更新。

对应的 Markdown 摘要：

```markdown
# 技术面分析：DEMO

证据标识：`sha256:c4721a503676168daebe905ab56c9e006b8fd71812eacd3dc6e560ba07a53292`

## 当前结论
当前技术结构为**多头**，当前优先情景：**多头**。价格位于三组均线上方，且均线次序
由短到长依次走高；最近阻力在 230.43，距现价 1.15%，应以已完成日线是否突破或失守
关键位作为下一步验证。

## 趋势、位置与确认
- **趋势**：最新收盘 227.82，较 SMA20 高 1.97%，较 SMA50 高 3.79%，较 SMA200 高 14.52%。
- **动量**：20/60/120 根收益分别为 5.38% / 10.52% / 17.8%；距 120 日高点回撤 1.13%。
- **参与度**：最新量为 20 日均量的 1.04 倍。
- **波动**：ATR14 占收盘价 2.2%；距最近支撑 214.27 为 5.95%，距最近阻力 230.43 为 1.15%。
```

持久示例工件位于 [`examples/technical-analysis-demo/`](examples/technical-analysis-demo/)。
`analysis.md` 与 `evidence.json` 共享同一个 `evidence_id`。每次合格运行还会生成临时
`chart.html`，用包内 TradingView Lightweight Charts 可视化同一证据集，并在标准输出
返回路径与浏览器打开状态；临时图表不写入持久工件目录。它展示一次下载后内嵌的固定
行情快照，缩放、平移、十字光标和悬停都只发生在本地，不会动态刷新行情。

## RED Skill 上传

根 `SKILL.md` 是 RED 的 Markdown 入口。如果平台只保留 Markdown，它只做能力发现和受管
GitHub 安装引导，不会假装脚本或环境已经安装。需要上传完整包时生成过滤后的确定性 ZIP
和独立哈希清单：

```bash
python3 scripts/build_red_upload_bundle.py \
  --output /tmp/mars-research-assistant-red.zip
```

包中不包含 `.git`、`.venv`、测试、开发文档、示例研究、凭据或本地开发配置。

## 数据与安全边界

- 技术面分析只使用 yfinance 的非官方、best-effort OHLCV；不需要 API key，也没有其他数据源或回退路径。
- 日线结论要求带时区、复权 OHLCV、正成交量与合适覆盖范围；少于 319 根已完成日线时整体失败关闭。
- 第一次取数不合格时最多进行一次 yfinance 同源扩大窗口重试，不插值、不合成、不切换来源。
- 所有研究都标记来源、`as_of` 与数据缺口；不把任何凭据放入仓库、Skill、fixture、文档或日志。
- Drive 写入每次从 My Drive 精确解析交易研究中心，只补缺项且不缓存 Drive ID；重复根目录由
  用户选择，不移动、覆盖、重命名或删除已有内容。

## 开发与验证

使用锁定的 `uv` 环境：

```bash
uv sync --locked
bash scripts/verify-mars-skills.sh
```

离线验收只使用 fixture 与临时目录，不请求市场数据、读取账户或写入 Drive。

发布前只运行一次真实 yfinance 契约测试，不创建每日任务：

```bash
uv run python scripts/run_yfinance_contract_test.py \
  --symbol SPY \
  --output-dir /tmp/mars-yfinance-release-check
```
