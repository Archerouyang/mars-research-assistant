# Automation: Alpha Weekly Shadow

每次唤醒先运行 `schedule-plan`，只有 jobs 包含 `weekly` 才继续。使用
`runs.sqlite` 和 `run-acquire --job-kind weekly` 获取唯一 lease。

1. 确认 daily price panel、universe、成熟标签和 Factor Registry 可读。
2. 运行 `train-challenger`。LightGBM 必须接收 `target_end_date`，训练行满足
   `target_end_date < validation_start`；使用固定 seed、时间切分和 shadow role。
3. 模型使用原生 LightGBM model + audit manifest 持久化到私有
   `{quant_runtime}/models/challenger/<session-date>/`。
4. challenger 只写 shadow artifact 和运行摘要，不改变 production Alpha Rank，
   不公开未校准概率，不自动 promotion。
5. 写入 sanitized outbox event，然后 `run-complete`。失败时保留旧 challenger，
   用短错误分类完成 failed run。

任何 promotion 至少需要 20 个 shadow trading days、deterministic gates、immutable
governance report 和 GPT-5.6 Sol `approved` review；Sol 不可用时必须阻断。
