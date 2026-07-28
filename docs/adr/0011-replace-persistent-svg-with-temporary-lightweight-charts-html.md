# ADR 0011：用临时 Lightweight Charts HTML 取代持久 SVG

状态：已接受

取代：ADR 0002 中的三文件持久工件布局，以及 ADR 0007 的 SVG 渲染决定。两份旧 ADR
继续作为历史记录保留；其证据一致性、离线验收和无绘图库运行时依赖原则仍然有效。

## 背景

静态 SVG 能稳定重放证据，但交互和视觉体验不足。技术面分析仍需要可审计的 Markdown 与
JSON，同时希望使用 TradingView Lightweight Charts 展示 K 线、成交量、均线和关键位。
图表只服务于当前调用，不应成为长期归档格式，也不能引入 CDN、Node/npm 运行时或隐藏状态。

## 决定

合格分析只向调用方提供的新 `output_dir` 原子写入：

```text
analysis.md
evidence.json
```

两份持久工件共享 `evidence_id`。每次合格调用另外在操作系统临时目录创建唯一的
`chart.html`，并返回绝对路径以及 `generated`、`open_attempted`、`open_confirmed`
状态。默认请求系统浏览器打开；无法确认时仍返回路径和限制说明。失败关闭只写
`analysis.md`，不生成 HTML 或 evidence JSON。

临时结果声明 24 小时有效期；每次后续生成前尽力清理系统临时目录中超过 24 小时的同前缀
目录。这样既给浏览器足够时间读取单文件 HTML，也不建立隐藏的长期缓存或后台清理任务。

HTML 内嵌 vendored `lightweight-charts@5.2.0` standalone production 构建和从同一
`evidence.json` 投影出的最近 120 根 K 线、成交量、预计算 SMA20/50/200 与关键位。
JavaScript 只负责展示，不重新计算技术指标或关键位。页面保留 TradingView attribution，
不引用 CDN，不在打开时请求资源，不使用 `localStorage`、遥测、固定全局目录或 Skill
安装目录。

## 后果

- `analysis.md` 和 `evidence.json` 继续适合作为稳定、可审计的长期交付；
- 临时 HTML 可以提供 Lightweight Charts 的缩放、十字线和图例体验；
- HTML 路径的生命周期由操作系统临时目录管理，调用方不得把它当成持久工件；
- 用户研究调用只报告图表路径和浏览器打开请求状态，不执行或要求用户完成浏览器验收；
- 交互、响应式布局、控制台和网络行为的浏览器集成验收留在开发与发布流程；
- 旧 `chart.svg`、纯 Python SVG 渲染器及其兼容或 fallback 路径全部移除。
