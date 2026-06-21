# 阶段六十九：本地控制台状态分组与筛选体验层

Stage69 是本地控制台状态分组与筛选体验层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。它基于 Stage68 本地控制台刷新与导航增强层，增加 status / severity / stage 分组、warning 与 blocking reason 筛选、只读搜索、卡片折叠/展开、分组计数 badge、筛选 empty state、forbidden route 安全占位和 Stage70 报告详情钻取与导出计划。

## 安全边界

- Stage69 不等于实盘授权。
- Stage69 只提供本地静态页面筛选体验。
- Stage69 不提供下单按钮。
- Stage69 不提供账户/持仓/订单/成交查询入口。
- Stage69 不调用 xttrader。
- Stage69 不真实下单。
- Stage69 不查询资金/持仓/订单/成交。
- Stage69 不真实发送通知。
- Stage69 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- READY_FOR_LOCAL_CONSOLE_GROUPING_REVIEW 只表示本地控制台状态分组与筛选体验层材料可供人工复核，不代表实盘授权。

## 只读体验

- status 分组：PASS / WARN / FAIL / SKIPPED / UNAVAILABLE。
- severity 分组：INFO / WARN / CRITICAL。
- stage 分组：Stage55-68。
- warning / blocking reason 筛选只作用于本地前端状态。
- searchReadOnly 只搜索本地 bundle，不发送网络请求。
- toggleCardCollapse 只切换卡片本地折叠状态。
- clearFilters 只清除本地筛选状态。
- forbidden hash route 显示“该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知功能。”。

## 安全分类

安全横幅、static safety、docs、generated reports 中的“不调用 xttrader”等安全说明归类为 INFO/WARN；真实可执行 JS/Python/route action 中的 xttrader、XtQuantTrader、下单、账户查询、真实通知、危险按钮或 forbidden route action 归类为 CRITICAL。xtdata / xtquant.xtdata 不应被误判为 CRITICAL。

## 下一阶段

Stage70 是本地控制台报告详情钻取与导出层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单，不真实发送通知，不绕过 Risk Gate / Human Approval。
