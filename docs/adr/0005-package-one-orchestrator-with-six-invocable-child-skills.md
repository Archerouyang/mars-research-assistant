# 用 RED Skill 根入口包装六个可调用子 Skill

Mars Research Assistant 只作为一个受管包下载和升级。为满足 RED Skill 上传入口要求，仓库根
`SKILL.md` 同时作为分发入口和完整安装后的执行编排器，负责权限披露、意图识别、并行编排和
显式上下文传递；包内六个子 Skill 各自保留 `SKILL.md` 和独立交付边界，仍可被用户直接调用。
这不是 Matt Pocock 仓库的根 Skill 模式：如果上传平台只保留 Markdown，根入口只能引导 GitHub
受管安装，不能宣称依赖脚本已可运行。我们接受七个可发现入口，以获得 RED Skill 兼容、组合
体验、单包安装和子能力可组合性；直接调用子 Skill 时不得假设顶层已经提供上下文。
