# Automation: Alpha Gmail Audit Dispatcher

这是 outbox sender，不运行模型，也不改变 Alpha release。

1. 在 `/Users/archer/Documents/dailytrades-quant` 使用 `uv run
   dailytrades-quant outbox-next --db {quant_runtime}/outbox.sqlite --format json`。
2. 返回 `null` 时结束。否则只使用 event 中的 `subject`、`body` 和 allowlisted
   metadata，通过已授权 Gmail connector 发给用户确认的收件地址。
3. 邮件正文不得补充 API key、token、broker account、positions、holdings、
   executions、完整 universe、原始 market data 或私有交易记录。
4. Gmail 返回 message id 后运行 `outbox-mark-sent`。timeout/5xx 使用
   `outbox-mark-failed` 的临时失败；权限、地址或策略错误使用 permanent failure。
5. 使用 event id 保证幂等。发送失败不回滚 Alpha、模型或治理报告。

用户-facing 邮件只包含：job kind、session date、success/failed、row count、model
run id、report path/fingerprint、promotion blockers 和下一步需要用户决定的事项。
