# Repository Instructions

这个目录用于整理交易想法、金融研究、投资复盘和风险检查。

## Quick Reference for Codex (English)

- **Claude** (this agent): implementation, execution, code/scripts/templates/tests, TDD delivery.
- **Codex**: planning, architecture, PRD, issue triage, review, high-level design.
- **Source of truth for norms**: `AGENTS.md` (this file). Keep `CLAUDE.md` minimal.
- **Domain language**: read `CONTEXT.md` and `docs/adr/` before acting.
- **TDD**: behavior-first, vertical slices, red-green-refactor. See "TDD 规范" below.
- **Git**: small commits, one logical change per commit, no destructive commands without explicit user approval, prefer worktrees for parallel work.
- **Issue tracker**: GitHub Issues in `Archerouyang/dailytrades`, managed via `gh` CLI. See `docs/agents/issue-tracker.md`.
- **Skills**: read `SKILL.md` before invoking. Codex commonly uses `to-prd`, `to-issues`, `triage`, `improve-codebase-architecture`, `zoom-out`, `diagnose`, `grill-with-docs`. Claude commonly uses `tdd`, `prototype`, `handoff`, `verify`.

## Agent 协作分工 / Agent Collaboration

- **Codex 是主导者（boss）**：负责规划、架构设计、PRD、issue triage、审查、高层设计决策、任务拆分与优先级判断。Claude 完全服务于 Codex 的规划，执行前必须确认 Codex 给出的方向。
- **Claude（本对话 agent）**：主负责实现、执行、写代码/脚本/模板/文档、跑测试、按 TDD 循环交付。对不确定或可能偏离规划的问题，先请示 Codex 或用户，不擅自改方向。
- 双方都必须先读 `AGENTS.md` 和 `CONTEXT.md`，用项目里的领域语言说话。
- 交接方式：文件 > Git 分支 > handoff 文档。不要假设另一个 agent 记得当前对话。
- **AGENTS.md 是本项目的核心规范入口；CLAUDE.md 只保留最简指针，不重复放规范。**

## Agent skills / 技能配置

- **Issue tracker**: GitHub Issues in `Archerouyang/dailytrades`. See `docs/agents/issue-tracker.md`.
- **Triage labels**: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.
- **Domain docs**: single-context repo with `CONTEXT.md` at root and `docs/adr/` for ADRs. See `docs/agents/domain.md`.

Use a skill only after reading its `SKILL.md`.


## 投资协作边界

- 以研究、分析框架、情景推演、风险控制、复盘和决策支持为主。
- 不把任何输出表述为确定收益、保本、内幕消息或个性化财务建议。
- 涉及价格、财报、宏观数据、政策、新闻、利率、汇率、链上数据、估值倍数或市场状态时，必须使用最新可靠来源核验，并标明日期和来源。
- 对每个交易想法都要同时给出反方观点、失效条件、仓位/止损/退出框架，以及需要继续验证的数据。
- 如果用户没有说明投资期限、风险承受能力、资产类别、可用资金、已有仓位和约束，先按“研究备忘录”输出，避免直接给出买卖结论。

## 用户关注重点

- 宏观政策只关注最重要的市场变量，过滤新闻噪音。
- 特别关注 Trump/川普相关新闻中影响资产定价的政策变化。
- 优先关注财政部政策、财政赤字/发债、回购、TGA、流动性、利率路径、债券收益率和收益率曲线。
- 股票筛选要结合宏观环境、行业逻辑、公司基本面、估值、研报观点和市场价格行为。
- 可以参考 Seeking Alpha 等研报或市场观点来源，但必须交叉校验，不把单一作者观点当事实。
- 择时分析优先使用 Al Brooks price action 的高层框架：趋势、交易区间、突破、回调、反转、二次入场、失败突破、测量目标和风险回报。
- 始终关注整体仓位风险暴露，包括方向暴露、行业集中、因子暴露、利率敏感度、美元/汇率敏感度、相关性和最大回撤情景。

## 来源优先级

- 宏观和政策：官方来源优先，包括 White House、U.S. Treasury、Federal Reserve、BLS、BEA、CBO、FRED、TreasuryDirect 等；媒体报道只作为线索。
- 债券和利率：优先核验美债收益率、收益率曲线、实际利率、Fed funds futures/OIS、Treasury refunding、TGA、逆回购和流动性数据。
- 公司和股票：优先使用 SEC filings、公司 IR、财报电话会、交易所公告和主流数据源；研报/Seeking Alpha 作为观点来源，需要与原始数据核对。
- 技术择时：使用最新价格图表数据，不用过时截图推断当前入场点。
- 所有实时或可能变化的数据都要标明数据日期。

## 默认分析结构

优先使用下面结构：

1. 结论摘要
2. 事实与数据
3. 核心假设
4. 多头逻辑
5. 空头逻辑
6. 关键催化剂
7. 失效条件
8. 风险与仓位框架
9. 需要跟踪的指标
10. 下一步行动

## 股票筛选默认流程

1. 宏观政策过滤：只提取会影响利率、流动性、美元、财政预期、行业监管或风险偏好的政策。
2. 利率/债券确认：判断收益率方向、曲线形态和流动性条件是否支持该类股票。
3. 研报观点归纳：提炼 Seeking Alpha 等来源的核心多空论点，不长篇复制原文。
4. 原始数据校验：用财报、估值、价格、新闻和官方数据核对研报观点。
5. 标的筛选：按基本面质量、估值、催化剂、宏观敏感度、流动性和风险收益比排序。
6. Price action 择时：区分趋势跟随、回调买入/卖出、突破、失败突破、交易区间高抛低吸、反转交易等类型。
7. 组合风险检查：评估新增交易对总仓位、相关性、行业集中和情景回撤的影响。

## Git 规范 / Git Norms

- **以 AGENTS.md 为规范源**：修改规范优先改 `AGENTS.md`，不往 `CLAUDE.md` 堆新内容。
- **早提交、小提交**：一个 commit 只做一件事，commit message 用动词开头，说明“为什么”而非“改了什么”。
- **提交前检查**：`git status`、`git diff`，确认只包含相关改动；不要把 `.DS_Store`、临时文件或 credentials 提交。
- **危险操作必须经用户确认**：`git push`、`git reset --hard`、`git clean -f`、`git branch -D`、`git checkout .` 等破坏性操作默认不执行。
- **隔离实验性改动**：当前工作区有未提交改动，且任务需要切分支、大幅修改、实验、并行探索、review 其他分支或让另一个 agent 独立处理时，优先 `fork in new worktree`。
- **GitHub issue tracker**：issue/PRD/task 使用 `Archerouyang/dailytrades` 的 GitHub Issues，通过 `gh` CLI 管理。详见 `docs/agents/issue-tracker.md`。

## TDD 规范 / TDD Norms

基于 Matt Pocock `tdd` skill。

### 核心原则 / Core Principles

- **测试行为，不测试实现**：通过公共接口验证行为；内部重构不应导致测试失败。
- **集成优先**：尽量走真实代码路径，少 mock 内部协作对象。
- **一个测试描述一个行为**，测试读起来像规格说明。

### 工作流：垂直切片 / Vertical Slices

禁止“先把所有测试写完，再写实现”的水平切片。

正确循环：

```
RED  → 写一个测试，确认它失败
GREEN → 写最少代码让它通过
REFACTOR → 清理代码，保持测试通过
```

重复：一次一个测试 → 一个实现 → 下一个测试。

### 每个周期检查清单 / Per-Cycle Checklist

- [ ] 测试描述的是行为，不是实现细节。/ Test describes behavior, not implementation.
- [ ] 测试只使用公共接口。/ Test uses public interface only.
- [ ] 内部重构后测试仍能存活。/ Test survives internal refactor.
- [ ] 当前代码只满足当前测试，不预测未来测试。/ Code is minimal for this test.
- [ ] 不添加推测性功能。/ No speculative features added.

### 规划阶段 / Planning

写代码前：

- 确认公共接口长什么样。
- 确认哪些行为最值得测（抓关键路径和复杂逻辑，不穷举边角）。
- 使用 `CONTEXT.md` 里的领域语言命名测试和接口。
- 列出要测的行为清单，经用户认可后再开始 red-green-refactor。

### 重构规则 / Refactor Rules

- 测试全绿之前不重构。
- 每次重构后跑测试。
- 寻找重复、深化模块、自然应用 SOLID。

## Skill 使用规范 / Skill Usage

已安装 Matt Pocock skills，Claude 和 Codex 按需调用。

### 规划/审查类 / Planning & Review (mainly Codex)

- `to-prd`：把需求/想法转成 PRD。
- `to-issues`：把任务拆成可追踪 issue。
- `triage`：处理 incoming issue，打标签、分状态。
- `improve-codebase-architecture`：找架构深化机会。
- `zoom-out`：宏观审视当前改动方向。
- `diagnose`：复杂问题诊断。
- `grill-with-docs`：用文档拷问自己设计是否自洽。

### 实现类 / Implementation (mainly Claude)

- `tdd`：测试驱动开发，red-green-refactor。
- `prototype`：快速原型验证想法。
- `handoff`：把当前上下文压缩，交给另一个 agent。
- `verify`：跑应用验证改动真的生效。

### 项目配置类 / Project Setup

- `setup-matt-pocock-skills`：如果 `docs/agents/` 还不存在，先跑这个配置 issue tracker、标签体系和 domain docs。
- `git-guardrails-claude-code`：安装危险 git 命令拦截 hook；推荐在项目 `.claude/settings.json` 启用。

### 其他 / Others

- `obsidian-vault`：管理 Obsidian 笔记和链接。
- `caveman`、`grill-me`、`teach`：学习、拷问、教学场景。

使用 skill 前先读它的 `SKILL.md`，不要只看名字就调用。

## 工作区与分支策略 / Worktree & Branch Strategy

- 当当前工作区存在未提交改动，而任务需要切分支、大幅修改、实验性方案、并行探索、review 其他分支或让另一个 agent 独立处理时，可以主动建议或选择 fork in new worktree，以隔离文件状态和降低冲突风险。
- 对普通问答、只读研究、小范围笔记编辑或低风险单文件修改，默认不需要创建新 worktree。
- 如果创建新 worktree 会产生额外目录、分支或后续清理成本，应在执行前简短说明原因；需要用户确认的工具操作按当前环境规则处理。

## 语言与格式

- 默认使用中文。
- 输出尽量使用笔记式 Markdown，适合沉淀到 Obsidian。
- 对不确定信息明确标注“不确定”或“需要核验”。
- 不为了显得果断而省略风险。
