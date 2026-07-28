# Mars Research Assistant

**交易者自己的研究 Harness。**

Mars Research Assistant 把你的 AI Agent 变成一套可控的个人交易研究工作台：接住模糊问题，
选择合适的研究能力，在步骤之间传递上下文，并把结论、证据和图表交还给你。

它不是自动交易机器人，也不是替你做决定的黑盒。你决定研究什么、采用哪些证据、是否继续
下一步，以及要不要归档。Skill 负责把重复的研究流程组织起来。

- **为交易者而生**：默认围绕美股、USD 和 `America/New_York` 展开，也可以明确切换市场。
- **由你掌控**：六个独立 Skill 可以组合使用，也可以只调用其中一个。
- **证据优先**：研究标记来源、`as_of`、数据缺口；技术面结论与 evidence JSON 使用同一证据。
- **本地优先**：不读取券商账户、不下单、不运行后台监控；Drive 写入必须单独确认。

## 60 秒开始

### 1. 一条命令安装

在 macOS、Linux 或 WSL 终端运行：

```bash
curl -LsSf https://raw.githubusercontent.com/archerthegoat/mars-research-assistant/master/scripts/install-from-github.sh | bash
```

安装脚本只复制发布白名单中的根 Skill、六个子 Skill、脚本和锁文件，默认安装到
`~/.codex/skills/mars-research-assistant`。如果电脑还没有 [uv](https://docs.astral.sh/uv/)，
它会先调用 uv 官方安装器；随后由 uv 准备隔离的 Python 3.12 和 yfinance 环境。不会使用
pip，也不会把依赖装进你的项目或全局 Python。

> 想安装到其他位置？在命令前设置
> `MARS_SKILL_TARGET=/your/agent/skills/mars-research-assistant`。

### 2. 直接开始

在新的 Agent 会话中输入：

```text
/ask mars
```

Ask Mars 会主动给出今天的研究起点和可直接回复的下一步。你也可以直接说：

```text
开始今天的交易研究
```

未指定市场时，Harness 默认先做美股市场快照和未来 7 个日历日的催化剂简报；不会因为你
身处其他时区而擅自切换到 A 股或港股。

## 你的研究 Harness

Harness 的作用不是把六个工具堆在一起，而是让每一步保持清晰边界：

| 你想解决的问题 | 使用的 Skill | 交付 |
| --- | --- | --- |
| “我今天应该先研究什么？” | **Ask Mars** | 最小研究流程、第一步、默认假设和快捷选项 |
| “现在的市场环境如何？” | **市场快照** | 利率、通胀、风险偏好、美元与大宗商品快照 |
| “接下来有哪些重要事件？” | **市场催化剂简报** | 已定事件、发展中风险及未来传导路径 |
| “这家公司值得继续研究吗？” | **标的研究** | 发行人身份、基本面、行业与公司事件证据 |
| “趋势、关键位和条件路径是什么？” | **技术面分析** | Markdown、evidence JSON 与临时交互图表 |
| “把完成的研究整理起来” | **Drive 写入** | 经确认后初始化或归档到交易研究中心 |

典型流程是先理解市场，再研究标的，最后由你决定是否归档。没有上游上下文时，每个子 Skill
仍能独立工作，不会假装已经取得不存在的证据。

## 技术面分析

只需说：

```text
我想看 GOOGL 的 1D 技术面分析
```

技术面分析会用 yfinance 下载一次已完成日线快照，生成中文摘要、可审计的 `evidence.json`
和临时 Lightweight Charts HTML。图表支持缩放、平移、十字光标和悬停，但不会在后台刷新
行情，也不会连接实时交易服务。

![GOOGL 技术面分析摘要与 Lightweight Charts 交互图表](assets/technical-analysis-showcase.png)

<p align="center"><em>真实体验截图：左侧为研究摘要与条件路径，右侧为同一证据集生成的交互图表。画面中的数据仅代表生成时点，不构成投资建议。</em></p>

第一次运行技术面分析时，Skill 会自动让 uv 准备 Python 3.12、包内 `.venv` 和锁定版本的
yfinance。后续运行复用同一环境，不污染你的项目或全局 Python。数据不满足质量门时只说明
数据缺口，不生成趋势、关键位或图表。

离线演示工件位于 [`examples/technical-analysis-demo/`](examples/technical-analysis-demo/)。

## 默认行为与安全边界

- 未指定市场时默认美股；明确指定港股、A 股或其他市场时，以你的输入为准。
- 用户位置与系统时区只影响时间展示，不能决定研究市场。
- 技术面分析只使用 yfinance 作为内置 OHLCV 来源（非官方、best-effort），没有隐藏回退来源。
- 研究能力只读取公开信息；不会读取券商账户、持仓、订单或 API key。
- 所有输出都是研究材料和条件情景，不是交易指令。
- Drive 初始化和归档分别确认；一次确认不会授权后续写入。
- 不创建每日任务、后台监控、隐式缓存或遥测。

## 从仓库安装或参与开发

如果你希望检查源码、定制 Skill，或使用支持原子升级和定制保护的受管安装器：

```bash
git clone https://github.com/archerthegoat/mars-research-assistant.git
cd mars-research-assistant
bash scripts/install-mars-skill.sh \
  --target ~/.codex/skills/mars-research-assistant
```

安装器会在目标目录旁准备完整候选包，通过锁定依赖和离线结构校验后再整体替换旧安装。
锁文件未变时复用环境；发现用户定制时默认停止，不回退到 pip。

通用 `npx skills add` 能发现根 Skill，但目前不会遵循本项目的发布白名单。为避免把测试和
开发文档一起复制到用户环境，普通用户请使用上方的一键安装命令。

开发验证：

```bash
uv sync --locked
bash scripts/verify-mars-skills.sh
```

离线验收只使用 fixture 和临时目录，不请求真实市场数据、读取账户或写入 Drive。真实
yfinance 契约测试只在发布验收时运行一次，不创建定时任务。

<details>
<summary>RED Skill 上传包</summary>

根 `SKILL.md` 是 RED 的 Markdown 入口。需要上传完整包时生成过滤后的确定性 ZIP 和独立
哈希清单：

```bash
python3 scripts/build_red_upload_bundle.py \
  --output /tmp/mars-research-assistant-red.zip
```

上传包不包含 `.git`、`.venv`、测试、开发文档、凭据或本地开发配置。

</details>
