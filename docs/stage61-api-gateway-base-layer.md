# 阶段六十一：API Gateway 基础层

Stage61 是 API Gateway 基础层，正式进入 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。

## 安全边界

- Stage61 不等于实盘授权。
- Stage61 只提供本地只读 API。
- Stage61 默认绑定 `127.0.0.1`，非 localhost host 必须 WARN 或拒绝。
- Stage61 不提供下单接口。
- Stage61 不提供账户/持仓/订单/成交查询接口。
- Stage61 不调用 `xttrader`，不导入 `XtQuantTrader`。
- Stage61 不真实下单。
- Stage61 不查询资金/持仓/订单/成交。
- Stage61 不真实发送通知。
- Stage61 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_API_GATEWAY_REVIEW` 只表示 API Gateway 基础层材料可供人工复核，不代表实盘授权。

## 只读 API 能力

- 健康检查。
- 项目阶段状态查询。
- roadmap / architecture 摘要查询。
- Stage55-60 报告读取。
- latest validation log 摘要读取。
- manifest / hash 查询。
- dry-run pipeline report 查询。
- scheduler / register preview 查询。
- safety boundary 查询。
- API capability 查询。

## 禁止 API 能力

Stage61 不暴露下单、撤单、账户、持仓、订单、成交、自动审批、真实通知、live execute 或任何绕过 Risk Gate / Human Approval 的接口。禁止路由会返回 `ok=false`、`read_only=true`、`dry_run_only=true`、`no_trade_authorization=true`，并在 `blocking_reasons` 中包含 `forbidden route`。

## 下一阶段预告

Stage62 是本地控制台报告读取层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单。Stage62 基于 Stage61 API Gateway 展示阶段报告列表、报告详情、manifest、validation log 摘要、dry-run pipeline 状态和安全边界。
