# Stage71 本地控制台人工复核工作台层

Stage71 是本地控制台人工复核工作台层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。Stage71 基于 Stage70 本地控制台报告详情钻取与导出层，只提供本地静态人工复核材料、复核清单、review notes 模板、本地确认项、复核包目录索引、复核状态占位、复核结论草稿、review safety report 和 Stage72 UI 验收汇总层计划。

## 安全边界

- Stage71 不等于实盘授权。
- Stage71 只提供本地静态人工复核材料。
- Stage71 不提供下单按钮。
- Stage71 不提供账户/持仓/订单/成交查询入口。
- Stage71 不调用 xttrader。
- Stage71 不真实下单。
- Stage71 不查询资金/持仓/订单/成交。
- Stage71 不真实发送通知。
- Stage71 不自动 approve。
- review notes / checklist / local confirmations 都不是审批授权。
- READY_FOR_LOCAL_CONSOLE_REVIEW_WORKBENCH_REVIEW 只表示本地控制台人工复核工作台层材料可供人工复核。

## 只读能力

1. 人工复核工作台页面。
2. review checklist。
3. 只读 review notes template。
4. local confirmation checklist。
5. review package index。
6. PENDING_REVIEW / REVIEWED / NEEDS_FIX 状态占位。
7. 复核结论草稿。
8. manual review manifest。
9. review safety report。
10. Stage72 UI 验收汇总层计划。

## Forbidden hash route

交易、账户、审批、通知和自动批准相关 hash route 显示只读错误占位：该路由被安全边界禁止；本地控制台不提供交易/账户/审批/通知/自动批准功能。

## 下一阶段

Stage72 是本地控制台 UI 验收汇总层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单，不绕过 Risk Gate / Human Approval，不自动 approve。
