# Automation: Alpha Monthly Governance

每次唤醒先运行 `schedule-plan`，只有 jobs 包含 `monthly` 才继续。使用
`run-acquire --job-kind monthly` 防止重复与并发。

1. 运行 `evaluate-bayesian` 生成 purged walk-forward 样本外预测。
2. 运行 `governance-report`，必须包含 Rank IC、ICIR、Top5/Top10/Top20 excess
   return、top-minus-bottom spread、turnover、estimated transaction cost、max
   drawdown、tail loss、Brier score 和 regime stability。
3. `governance-report` 必须读取与训练相同的 `--universe` 和
   `--universe-manifest`，从内容绑定的 manifest 派生 `data_scope`、
   `point_in_time_status`、knowledge cutoff 和 universe fingerprint；不得由
   prompt 或调用者手工声明。若只有 current-universe fallback 或缺少
   delisting/symbol history，阻断 promotion；不把 survivorship-biased 结果
   描述为 full-universe validation。
4. 报告写入私有 immutable report directory。同 report id 内容变化必须失败。
5. 默认 `sol_review=pending`。只有确定性门禁通过后才升级到 GPT-5.6 Sol；
   未获得 `approved` 不得调用 model registry promotion。
6. Model Registry promotion 必须同时比较 champion/challenger 的 Rank IC、
   ICIR、Precision@5、Top5/10/20 return、top-bottom spread、turnover、transaction
   cost、max drawdown、tail loss、Brier score 和逐 regime Rank IC。任一缺失、
   非有限或退化都 fail closed；月报本身不能绕过该相对门禁。
   PromotionEvidence 还必须绑定 immutable report fingerprint、rollback
   artifact path 和 rollback artifact fingerprint；Model Registry 必须重新读取
   两个本地文件并计算 SHA-256，不能只接受格式正确的字符串。
7. 将 allowlisted 报告摘要写入 outbox，并完成 run lease。通知失败不回滚报告。

此任务只做研究治理，不读取 broker 私有仓位，不创建任何订单。
