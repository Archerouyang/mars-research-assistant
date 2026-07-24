# Automation: Alpha Daily Publish

在美股收盘并等待数据落地后运行。量化仓库由安装时确认的
`{quant_repo}` 指定，Python 命令统一使用 `uv run`。

1. 运行 `cd {quant_repo} && uv run dailytrades-quant schedule-plan --now <UTC ISO>
   --format json`。
   只有返回 `daily` 才继续；交易所休市、尚未过 close delay 或重复唤醒时结束。
2. 使用 `{quant_runtime}/runs.sqlite`、`job_kind=daily`、session date 和 config
   hash 调用 `run-acquire`。返回 `null` 时结束，不重复执行。
3. 运行 `provider-probe --format json`。调整后 OHLCV 等 required capability
   不可用时失败关闭；current-universe fallback 不能冒充 PIT 历史 universe。
4. 运行 `refresh-prices`，输入 `{quant_runtime}/inputs/universe.csv`，输出
   `{quant_runtime}/data/prices.parquet`，额外读取 SPY 与配置的行业/主题 ETF。
5. 运行 `train-champion`，只使用已成熟的 20D 标签，模型写入私有
   `{quant_runtime}/models/champion.json`。
6. 运行 `publish-daily`：Parquet 写入 quant runtime，规范化 SQLite 写入
   `{skill_runtime}/alpha/leaderboard.sqlite`。不得写 public repo。
7. 成功后把 allowlisted 摘要写入 `{quant_runtime}/outbox.sqlite`：session、
   status、row count、model run id、report path、fingerprint。不得包含 API key、
   broker account、positions、holdings、executions 或原始数据。
8. 调用 `run-complete --status success`。任何失败都使用短错误分类完成为
   `failed` 并写失败 audit event；通知失败不得回滚已发布 Alpha。

禁止 broker/order create、submit、modify、cancel。默认只输出精炼中文运行摘要。
