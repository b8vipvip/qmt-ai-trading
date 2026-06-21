# Stage70 本地控制台报告详情钻取与导出层

Stage70 是本地控制台报告详情钻取与导出层，属于 Stage61-75：API Gateway / 本地控制台 / UI 产品化路线。它基于 Stage69 本地控制台状态分组与筛选体验层，增加报告详情钻取、单报告预览、复制摘要、导出本地 Markdown/JSON 快照、错误报告定位、人工复核包入口、report detail route map、export manifest、copy/export safety report、forbidden export route 安全占位和 Stage71 人工复核工作台计划。

## 安全边界

- Stage70 不等于实盘授权。
- Stage70 只提供本地静态页面报告钻取与复核快照导出。
- Stage70 不提供下单按钮。
- Stage70 不提供账户/持仓/订单/成交查询入口。
- Stage70 不调用 xttrader。
- Stage70 不真实下单。
- Stage70 不查询资金/持仓/订单/成交。
- Stage70 不真实发送通知。
- Stage70 不自动 approve，不绕过 Risk Gate，不绕过 Human Approval。
- READY_FOR_LOCAL_CONSOLE_DRILLDOWN_REVIEW 只表示本地控制台报告详情钻取与导出层材料可供人工复核，不是实盘授权。

## 只读能力

1. 报告详情钻取：通过 report_detail_index 提供本地报告 ID、标题、状态、severity、source_path 和摘要。
2. 单报告预览：在静态前端中渲染只读预览，不请求交易、账户、审批或通知接口。
3. 复制摘要：copySummaryReadOnly 只复制摘要文本，不发送网络请求。
4. 导出 Markdown 快照：只生成本地 Markdown 复核快照，包含 read_only=True、dry_run_only=True、no_trade_authorization=True。
5. 导出 JSON 快照：只生成本地结构化 JSON 复核快照，明确不是交易授权。
6. 错误报告定位：只返回本地 source_path，辅助人工定位报告。
7. 人工复核包入口：提供 Stage71 只读人工复核工作台入口，不自动 approve。
8. forbidden hash route：交易、账户、审批、通知等路由显示安全占位。

## 导出安全

导出只允许 Markdown/JSON 静态快照，不导出 `.env`、token、key、secret、credential，不导出 `market_data/`、`reports/`、`logs/`、`validation_logs/` 原始目录，不允许路径穿越，不允许绝对路径。

## Stage69 遗留 WARN 分类

Stage70 延续 Stage69 前端安全分类：安全横幅、静态安全说明、docs、generated reports 中出现“不调用 xttrader”等安全说明可归类为 INFO/WARN；app.js、preview server、executable Python 或 route action 中出现真实交易、账户查询、通知、审批绕过动作必须 CRITICAL。

## Stage71 预告

下一阶段 Stage71 是本地控制台人工复核工作台层，仍不得直接实盘，不调用 xttrader，不查询真实账户，不下单，不真实发送通知，不绕过 Risk Gate / Human Approval。
