# 通过 npx skills 分发 Skill 运行包

Mars Research Assistant 的唯一公开安装入口定为 `npx skills add archerthegoat/mars-research-assistant --skill mars-research-assistant --agent codex --global --copy`。仓库将向该入口提供仅包含运行期文件的 Skill 运行包，替代 curl 下载并执行自定义安装器；技术面分析的 Python 与 yfinance 环境继续在首次实际调用时按需初始化。

## Considered Options

- 保留 curl 安装器：能预先完成 uv 环境配置，但要求用户执行管道下载的 shell 脚本，并把安装、依赖准备和升级机制耦合在一起。
- 发布自定义 npm CLI：可以复刻受管安装器，却新增 npm 包、发布流程和第二套安装语义。
- 使用 `npx skills add`：与 Agent Skills 生态一致，免除 curl 和额外 npm 包；为保持轻量，必须避免把完整源码仓库作为安装内容。

## Consequences

公开安装不再预建 Python 环境，也不承诺自定义安装器的原子升级和完整性标记。默认安装到 Codex 的全局 Skill 目录，运行包必须保持自包含，根 Skill 与子 Skill 的相对引用不得依赖测试或开发文档。
