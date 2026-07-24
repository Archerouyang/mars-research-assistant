# Automation: Alpha Gmail Audit Dispatcher

这是 outbox sender，不运行模型，也不改变 Alpha release。

1. 先在公开 Skill 运行 `python3 scripts/alpha_notification_adapter.py next
   --db {quant_runtime}/outbox.sqlite`。适配器以 SQLite `mode=ro` 重新验证 kind 和
   allowlisted metadata，完全忽略 producer 写入的 subject/body，再从固定字段重建
   outbound subject/body；不得直接信任 `outbox-next` 原始输出。
2. 返回 `null` 时结束。否则只使用验证后 event 中的 `subject`、`body` 和
   allowlisted metadata，通过已授权 Gmail connector 发给用户确认的收件地址。
3. 邮件正文不得补充 API key、token、broker account、positions、holdings、
   executions、完整 universe、原始 market data 或私有交易记录。
4. Gmail 返回 message id 后运行 `outbox-mark-sent`。timeout/5xx 使用
   `outbox-mark-failed` 的临时失败；权限、地址或策略错误使用 permanent failure。
5. 使用 event id 保证幂等。发送失败不回滚 Alpha、模型或治理报告。
6. 适配器校验失败时必须 fail closed：不发送、不 mark-sent，只记录清洗后的
   错误类别并请求人工检查 outbox producer。

用户-facing 邮件只包含：job kind、session date、success/failed、row count、model
run id、report path/fingerprint、promotion blockers 和下一步需要用户决定的事项。
