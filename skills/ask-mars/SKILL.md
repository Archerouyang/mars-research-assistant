---
name: ask-mars
description: 根据当前交易研究问题，建议应使用的 Mars Skill、执行顺序、第一步与最少输入。不会自动执行研究。
disable-model-invocation: true
---

# Ask Mars

## 能力合同

同目录的 `capability.json` 定义 Ask Mars 的公开能力边界与验收场景；本说明和该合同
共同约束交付行为。

```mars-skill-policy
{"delivery":"recommendation","forbidden_effects":["research","market_data","drive_write"]}
```

先判断用户真正需要的研究交付，再建议最小的一组 Mars Skills。可以推荐一个下一步，
也可以为复合问题给出有序执行序列。

每次回答包含：

- 建议使用的 Skill 与原因；
- 当前应先做的第一步；
- 用户还需要提供的最少信息；
- 如果问题包含后续步骤，说明它们何时有必要。

不要自动执行任何被建议的 Skill。不要自行搜索、获取市场数据、生成研究交付、写入
Google Drive、读取账户或执行交易。用户确认并显式调用相应 Skill 后，才由那个
独立 Skill 处理研究或写入。

对“下周事件 + 某标的研究”这类复合请求，给出可理解的顺序，例如先做市场催化剂
简报，再做标的研究；不要把它们合并成一次自动执行。
