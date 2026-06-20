# 阶段六十八：本地控制台刷新与导航增强层

Stage68 属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage68 基于 Stage67 本地只读预览服务层，新增本地静态控制台刷新按钮、hash route 导航、bundle reload、latest updated 显示、loading / error / empty state 占位、前端安全分类和 Stage69 状态分组与筛选体验计划。

## 安全边界

- Stage68 是本地控制台刷新与导航增强层。
- Stage68 进入 Stage61-75 UI 产品化路线。
- Stage68 不等于实盘授权。
- Stage68 只提供本地静态页面刷新与导航增强。
- Stage68 不提供下单按钮。
- Stage68 不提供账户/持仓/订单/成交查询入口。
- Stage68 不调用 `xttrader`。
- Stage68 不真实下单。
- Stage68 不查询资金/持仓/订单/成交。
- Stage68 不真实发送通知。
- Stage68 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- `READY_FOR_LOCAL_CONSOLE_REFRESH_REVIEW` 只表示本地控制台刷新与导航增强层材料可供人工复核，不代表实盘授权。

## 只读能力

- `#/dashboard`、`#/reports`、`#/filters`、`#/manifest`、`#/validation`、`#/scheduler`、`#/safety`、`#/api`、`#/next` 均为只读 hash route。
- 空 hash 默认进入 `#/dashboard`。
- 禁止 `#/order`、`#/orders`、`#/trade`、`#/execute`、`#/approve`、`#/live`、`#/notify`、`#/account`、`#/positions`、`#/assets`。
- 用户手动输入 forbidden hash route 时，只显示只读错误占位：该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知功能。
- 刷新按钮只重新读取本地相对 JSON：`data_bundle.json`、`binding_manifest.json`、`data_source_map.json`、`static_data_safety.json`。

## 前端安全分类

安全横幅、docs、generated reports、static data bundle 中的“不调用 xttrader”等历史说明归类为 INFO/WARN；真实可执行 JS / Python / route action 中的交易、账户、审批、通知、`xttrader` / `XtQuantTrader` / 下单 / 查询账户 / 真实通知动作归类为 CRITICAL。

## 下一阶段

Stage69 是本地控制台状态分组与筛选体验层，仍不得直接实盘，不调用 `xttrader`，不查询真实账户，不下单，不真实发送通知。
