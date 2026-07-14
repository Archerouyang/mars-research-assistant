# 周末首次启动：空 formal runtime

- exact prompt: `周末首次启动，先看看下周`
- deterministic scope: status-only、无网络、无 broker/private data。

## 运行状态检查

| item | status | effect |
| --- | --- | --- |
| runtime_origin | environment | runtime 路径来自 `TRADING_RESEARCH_RUNTIME_DIR`；保留确定性来源值 |
| formal runtime | missing | 环境变量选择的 private runtime 目录不存在；未创建目录 |
| startup_status | uninitialized | 启动完整度未初始化；与 formal runtime 可用性保持独立 |

## 可用研究摘要

- 公开来源研究仍可用，但本确定性合同不提供当前市场读数，也不声称完成实时核验。
- 本轮只给下周研究框架和待核验变量，不读取保存计划，不生成 setup。
- 先提供可用摘要，再请求授权或初始化选择；摘要不是个性化交易建议。

## 摘要后缺失确认

- broker read-only：选择 Longbridge、IBKR、两者或暂不启用；此处只记录偏好，不读取账户。
- setup key：确认完整 `ticker + trade_horizon + instrument`；确认 setup key 不等于授权写入。
- runtime：选择 `dry-run` 或初始化 private runtime；实际初始化必须获得独立明确授权 runtime 写入。

## 安全边界

- 本轮不写 runtime，也不创建 private runtime 目录。
- 不读取 broker 或 private account data。
- 不生成 setup、买卖指令或订单动作。
