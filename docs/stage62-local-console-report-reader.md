# 阶段六十二：本地控制台报告读取层

Stage62 是本地控制台报告读取层，正式处于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。本阶段基于 Stage61 API Gateway 基础层，只提供本地只读报告读取、控制台视图路由索引、阶段报告列表、validation log latest 摘要、manifest/hash 摘要、dry-run pipeline 状态摘要、scheduler/register preview 摘要和 safety boundary 展示。

## 安全边界

- Stage62 不等于实盘授权。
- Stage62 只提供本地只读报告读取能力。
- Stage62 不提供下单接口。
- Stage62 不提供账户/持仓/订单/成交查询接口。
- Stage62 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage62 不真实下单。
- Stage62 不查询资金/持仓/订单/成交。
- Stage62 不真实发送通知。
- Stage62 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_REVIEW` 只表示本地控制台报告读取层材料可供人工复核，不代表实盘授权。

## 只读控制台视图

- `/dashboard`
- `/reports`
- `/reports/stage61` 到 `/reports/stage55`
- `/manifest`
- `/validation/latest`
- `/safety`
- `/api-capabilities`
- `/scheduler-preview`

## 禁止视图和动作

禁止 `/order`、`/orders`、`/trade`、`/execute`、`/approve`、`/live`、`/notify`、`/account`、`/positions`、`/assets`。本地控制台不能绕过 Risk Gate，不能绕过 Human Approval，不能直接访问 QMT，不能自动 approve。

## 下一阶段

Stage63 是本地控制台报告详情页与过滤层，增加报告详情页、阶段筛选、状态筛选、warning/blocking reason 过滤、manifest 文件详情和 validation log 摘要详情。Stage63 仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。
