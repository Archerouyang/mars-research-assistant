# 将技术面分析交付为三文件工件包

技术面分析以一个工件包交付：`analysis.md` 负责理由分析，`chart.svg` 负责图表可视化，
`evidence.json` 保存标准化 OHLCV、确定性派生结果和 provenance 以供审计重放；三者共享
同一个 evidence_id。我们放弃把原始 SVG 内嵌在单个 Markdown 文件中的方案，以换取跨
GitHub、Codex 和常见 Markdown 阅读器更稳定的展示、独立验收、README 示例复用和图文一致性
验证。renderer 必须接收调用方提供的工件目录，先在临时目录生成并验证三个文件，再原子
落盘；它不得把用户研究写进组合 Skill 安装目录或固定全局路径。
