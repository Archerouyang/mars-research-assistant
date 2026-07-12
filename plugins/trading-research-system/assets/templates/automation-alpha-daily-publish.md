# Automation: Alpha Daily Publish

在美股收盘并等待数据落地后运行。量化仓库由安装时确认的
`{quant_repo}` 指定，Python 命令统一使用 `uv run`。

1. 运行 `cd {quant_repo} && uv run dailytrades-quant schedule-plan --now <UTC ISO>
   --format json`。
   只有返回 `daily` 才继续；交易所休市、尚未过 close delay 或重复唤醒时结束。
2. 使用 `{quant_runtime}/runs.sqlite`、`job_kind=daily`、session date 和 config
   hash 调用 `run-acquire`。返回 `null` 时结束，不重复执行。
3. 运行 `provider-probe --format json`，再运行
   `security-master-check --data {quant_runtime}/inputs/security-master.parquet
   --manifest {quant_runtime}/inputs/security-master.manifest.json
   --require-training-ready`。任一 required capability、PIT、delisting、symbol
   history、指纹或 future-leakage gate 不通过时失败关闭。
4. 读取 `{quant_runtime}/production-activation.json`；必须是 `approved`，且
   provider probe、future leakage、pilot run、rollback pointer 和 universe
   fingerprint 全部匹配，并记录四类证据 artifact 的 SHA-256。否则不得写插件运行库。
5. 生成本次 dependency manifest，并运行 `dependency-plan --db
   {quant_runtime}/dependencies.sqlite --manifest <manifest>`。只复用返回为
   `reusable` 的节点；model、rule、schema 或图结构变化时必须全量重算。
6. 运行 `refresh-prices`，输入已验证 universe，输出
   `{quant_runtime}/data/prices.parquet`，额外读取 SPY 与配置的行业/主题 ETF。
7. 验证本次因子输入全部存在并且 knowledge cutoff 合法：
   `{quant_runtime}/data/fundamentals.parquet`、
   `{quant_runtime}/data/industry-mapping.parquet`、
   `{quant_runtime}/data/macro-factors.parquet`、
   `{quant_runtime}/registries/factors.sqlite`。不得用当前行业分类、最新财报值或
   修订后宏观值回填历史日期。
8. 运行 `train-champion`，显式传入 `--fundamentals`、`--industry-mapping`、
   `--macro-factors`、`--factor-registry`；只使用逐日 PIT universe 和已成熟的
   20D 标签，模型写入私有 `{quant_runtime}/models/champion.json`。模型 artifact
   必须绑定 factor contract hash。
9. 运行 `publish-daily --activation-manifest
   {quant_runtime}/production-activation.json`：Parquet 写入 quant runtime，
   并再次显式传入四类因子参数。规范化 SQLite 写入
   `{plugin_runtime}/alpha/leaderboard.sqlite`。每行必须含可重建预测的模型基线、
   因子归因和主因子；不得写 public repo。
10. 发布成功后先调用 `run-complete --status success`；发布失败则完成为
   `failed`，不得推进依赖基线。
11. 仅对已在 `{quant_runtime}/runs.sqlite` 标记为 `success` 的同一 run id
   运行 `dependency-record --run-ledger {quant_runtime}/runs.sqlite
   --execution-fingerprint <published artifact sha256>`，把本次 manifest 写入
   `{quant_runtime}/dependencies.sqlite`。失败运行不得推进 latest-success 状态。
12. 成功后把 allowlisted 摘要写入 `{quant_runtime}/outbox.sqlite`：session、
   status、row count、model run id、report path、fingerprint。不得包含 API key、
   broker account、positions、holdings、executions 或原始数据。
    通知失败不得回滚已发布 Alpha。

禁止 broker/order create、submit、modify、cancel。默认只输出精炼中文运行摘要。
