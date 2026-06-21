# Stage78：AI 接口配置、模型发现与压力测试层

Stage78 新增 AI Provider 配置中心：用户可在前端配置 OpenAI-compatible / OpenAI Official / Custom Compatible 的 Base URL 与 API Key，后端仅在本地会话中使用密钥调用模型列表接口。

- 后端按 `/v1/models` 优先、`/models` fallback 的顺序发现模型，并返回前端展示。
- 前端支持模型多选，展示 `model_id`、`owned_by`、`created`、状态与能力推断。
- 后端对选中模型串行执行 1000 / 3000 / 5000 字压力测试，每个模型每种长度仅 1 次，最多 15 个请求。
- 测试 prompt 只验证中文摘要、结构化 JSON 与理解能力，不输出投资建议，不生成交易指令。
- 测试报告返回前端，包含成功/失败、响应时间、输出长度、错误类型、推荐用途与综合评分。
- API Key 不提交、不落日志、不写前端 localStorage，报告只显示 masked key。
- 本阶段只服务 TradingAgents Agent 能力配置，不接交易；AI Agent 仍只做分析、解释、评分和建议。
- QMT Gateway 仍是最终交易执行终端；所有实盘前必须经过 Risk Gate；Stage78 不调用 xttrader、不真实下单、不查账户。
- Stage79 进入因子研究工作台与选股评分可视化层。
- 所有实盘仍然关闭。
