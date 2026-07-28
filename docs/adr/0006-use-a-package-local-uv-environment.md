# 使用组合包内的 uv 虚拟环境

Mars Research Assistant 的 Python 行情环境只属于技术面分析 Skill。该 Skill 在每次取数前
调用自身的幂等环境门：从组合包根 `uv.lock` 解析依赖，在包内维护 `.venv`，缺少 Python
3.12 时由 uv 安装受管解释器，再执行 `uv sync --locked` 并验证 yfinance。其他五个 Skill
不触发 uv，也不依赖该环境。

完整包安装器复用同一环境门，以保证 Git 仓库安装和技术面分析首次调用具有同一依赖契约。
安装不污染用户项目或全局 Python；缺少 uv、依赖同步失败或环境验证失败都会使整个原子
安装失败，且不回退到 pip。受管升级在 `uv.lock` 未变化时复用环境。只复制 Markdown 或
单个子目录却缺少根锁文件时必须停止，并引导安装完整包，不能临时拼装未锁定环境。
