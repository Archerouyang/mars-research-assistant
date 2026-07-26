# Mars Skills 开发说明

## 原则

- 每个 Skill 只完成一种交付；Ask Mars 只建议，不自动执行其他 Skill。
- 优先让模型在职责边界内判断研究方式；仓库测试只约束可观察的边界、来源标注、
  数据缺口、隐私和确认写入。
- 所有研究默认只读、无状态。未经用户确认，Drive 写入不会发生。
- 不访问账户、持仓、订单或交易执行能力；不在代码、测试、文档或日志中保存用户凭据。

## 环境

开发与验证使用 `uv`：

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

## 验证

唯一的组合级验收入口是：

```bash
bash scripts/verify-mars-skills.sh
```

它只读取仓库内的 fixture，并在临时目录验证独立安装副本；不调用市场数据、新闻、
Google Drive、浏览器、经纪商或任何需要凭据的服务。

每个新增 Skill 应提供自己的验收场景。验证器会自动发现这些场景，因此新增 Skill
不应复制或修改旧的验证链。

## 人工验收

涉及 Macro Board 的改动，除离线 fixture 外，应生成一份代表性自包含 Board 并在
in-app browser 中进行一次人工视觉验收。不要使用截图矩阵或像素比对取代用户判断。

## 提交前检查

- 运行组合级验收入口与相关的 focused test。
- 确认不引入私有绝对路径、凭据、外部服务调用或交易写操作。
- 确认 Skill 的交付没有越过其职责边界。
